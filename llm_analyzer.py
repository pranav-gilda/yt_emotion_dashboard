import os
import openai
import google.generativeai as genai
import json
import logging
import re
import time
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Import the RoBERTa function from your models file
from models import run_go_emotions

load_dotenv()
# --- API Key Configuration ---
openai.api_key = os.getenv("OPENAI_API_KEY", "")
genai.configure(api_key=os.getenv("GEMINI_API_KEY", "")) # type: ignore

# --- Original Prompt V1 ---
SYSTEM_PROMPT_V1 = """
You are a media analyst AI tasked with scoring a news story transcript across 5 dimensions of peacefulness.
**Instructions:**
Analyze the provided transcript and for each of the 5 dimensions below, provide a score from -5 (low peace) to +5 (high peace) and a brief, one-sentence rationale for your score.
**Dimensions:**
1.  **Nuance:** Does the text present multiple perspectives and context (+5), or is it overly simplistic and one-sided (-5)?
2.  **Creativity vs. Order:** Does the text emphasize human-centered stories and innovation (+5), or control, authority, and systems (-5)?
3.  **Safety vs. Threat:** Is the text framed around stability and resilience (+5), or crisis, danger, and threat (-5)?
4.  **Compassion vs. Contempt:** Is the language inclusive and respectful of outgroups (+5), or dehumanizing and divisive (-5)?
5.  **Reporting vs. Opinion:** Is the text highly fact-based and objective (+5), or highly subjective and persuasive (-5)?
**Output Format:**
Respond ONLY with a valid JSON object following this structure:
{
  "nuance": { "score": <integer>, "rationale": "<string>" },
  "creativity_vs_order": { "score": <integer>, "rationale": "<string>" },
  "safety_vs_threat": { "score": <integer>, "rationale": "<string>" },
  "compassion_vs_contempt": { "score": <integer>, "rationale": "<string>" },
  "reporting_vs_opinion": { "score": <integer>, "rationale": "<string>" }
}
"""

# --- V1 Prompt Augmented with RoBERTa Context ---
SYSTEM_PROMPT_V1_WITH_CONTEXT = """
You are a media analyst AI tasked with scoring a news story transcript across 5 dimensions of peacefulness.
**Instructions:**
Analyze the provided transcript. As additional context, you are also being given a quantitative emotional profile of the text from another AI model. Use **both the transcript and the emotional profile** to inform your scores. For each of the 5 dimensions, provide a score from -5 (low peace) to +5 (high peace) and a brief, one-sentence rationale.
**Dimensions:**
1.  **Nuance:** Does the text present multiple perspectives and context (+5), or is it overly simplistic and one-sided (-5)?
2.  **Creativity vs. Order:** Does the text emphasize human-centered stories and innovation (+5), or control, authority, and systems (-5)?
3.  **Safety vs. Threat:** Is the text framed around stability and resilience (+5), or crisis, danger, and threat (-5)?
4.  **Compassion vs. Contempt:** Is the language inclusive and respectful of outgroups (+5), or dehumanizing and divisive (-5)? (Hint: Use the emotional profile's `admiration`, `caring`, `disgust`, `disapproval` scores to help inform this).
5.  **Reporting vs. Opinion:** Is the text highly fact-based and objective (+5), or highly subjective and persuasive (-5)?
**Output Format:**
Respond ONLY with a valid JSON object following this structure:
{
  "nuance": { "score": <integer>, "rationale": "<string>" },
  "creativity_vs_order": { "score": <integer>, "rationale": "<string>" },
  "safety_vs_threat": { "score": <integer>, "rationale": "<string>" },
  "compassion_vs_contempt": { "score": <integer>, "rationale": "<string>" },
  "reporting_vs_opinion": { "score": <integer>, "rationale": "<string>" }
}
"""

# --- NEW: V2 Streamlined Prompt for Speedometer UI ---
SYSTEM_PROMPT_V2_STREAMLINED = """
You are a media analyst AI tasked with scoring a news story transcript.

**Instructions:**
Analyze the provided transcript and its quantitative emotional profile. Score the transcript on the following dimensions.

**Dimensions & Scoring:**

1.  **Compassion vs. Contempt (Score 0-100):** This is the primary metric. A score of 0 indicates extreme contempt, divisiveness, and dehumanizing language. A score of 100 indicates extreme compassion, respect, and inclusive language. A score of 50 is neutral. Use the emotional profile's `admiration`, `caring`, `disgust`, `disapproval` scores to help inform this.
2.  **Creativity vs. Order (Score -5 to +5):** Does the text emphasize human-centered stories and innovation (+5), or control, authority, and systems (-5)?
3.  **Safety vs. Threat (Score -5 to +5):** Is the text framed around stability and resilience (+5), or crisis, danger, and threat (-5)?
4.  **Reporting vs. Opinion (Score -5 to +5):** Is the text highly fact-based and objective (+5), or highly subjective and persuasive (-5)?

**Output Format:**
Respond ONLY with a valid JSON object following this structure:
{
  "compassion_vs_contempt": { "score": <integer>, "rationale": "<string>" },
  "creativity_vs_order": { "score": <integer>, "rationale": "<string>" },
  "safety_vs_threat": { "score": <integer>, "rationale": "<string>" },
  "reporting_vs_opinion": { "score": <integer>, "rationale": "<string>" }
}
"""

# --- NEW: V3 Final Prompt for Streamlined UI with Enhanced Reasoning ---
SYSTEM_PROMPT_V3_FINAL = """
You are a media analyst AI. Your task is to analyze a transcript and its emotional profile to create a final, user-facing analysis.

**Instructions:**
Analyze the provided transcript and its quantitative emotional profile from a RoBERTa model.

**Analysis Steps & Output:**

1.  **Identify Top Emotions:** From the provided "Emotional Profile Context", identify the top 3 non-neutral emotions with the highest scores.
2.  **Score Dimensions:** Score the transcript on the following dimensions.
3.  **Incorporate Emotions in Rationale:** For the "Compassion vs. Contempt" score, your rationale **must** explicitly reference the top emotions you identified. For example: "The score is low due to the strong presence of emotions like disapproval and anger, which points to a contemptuous tone."

**Dimensions & Scoring:**

1.  **Compassion vs. Contempt (Score 0-100):** 0 indicates extreme contempt, 100 indicates extreme compassion, 50 is neutral.
2.  **Creativity vs. Order (Score -5 to +5):** +5 for human-centered stories, -5 for control/authority.
3.  **Safety vs. Threat (Score -5 to +5):** +5 for stability/resilience, -5 for crisis/danger.
4.  **Reporting vs. Opinion (Score -5 to +5):** +5 for objectivity, -5 for subjectivity.

**Output Format:**
Respond ONLY with a valid JSON object. The "top_emotions" array must contain exactly three emotion objects.

{
  "compassion_vs_contempt": { "score": <integer>, "rationale": "<string>" },
  "creativity_vs_order": { "score": <integer>, "rationale": "<string>" },
  "safety_vs_threat": { "score": <integer>, "rationale": "<string>" },
  "reporting_vs_opinion": { "score": <integer>, "rationale": "<string>" },
  "top_emotions": [
      { "emotion": "<string>", "score": <float> },
      { "emotion": "<string>", "score": <float> },
      { "emotion": "<string>", "score": <float> }
  ]
}
"""

# --- NEW: V5 All Dimensions Prompt (1-5 scale, without RoBERTa) ---
SYSTEM_PROMPT_V5_ALL_DIMENSIONS = """
You are a media analyst AI tasked with scoring a video transcript across 5 dimensions.

**Instructions:**
Analyze the provided transcript and score it on each of the 5 dimensions below. Provide a score from 1-5 and a brief rationale for each dimension.

**Dimensions:**

1. **News - Opinion:** Score from 1-2 (highly subjective, persuasive and analytical - the "what does this mean?" angle offering judgements and personal reflections on topics) to 3 (neutral or irrelevant) to 4-5 (highly fact-based and objective - the "who, what, when, where, why, and how" of an event).

2. **Nuance - Oversimplification:** Score on a 5-point scale from 1-2 (overly simplistic, one-sided, or binary – with absence of qualifiers, conflicting views, caveats) to 3 (balanced simple and complex) to 4-5 (highly nuanced, contextualized, and multi-perspective – with presence of qualifiers, conflicting views, and caveats).

3. **Creativity - Order:** Score on a scale from 1-2 (emphasizing control, authority, bureaucratic systems, or law and order) to 3 (a balance of both order and creativity) to 4-5 (emphasizing creativity, innovation, culture, or human-centered stories). Justify your score based on the dominant themes and framing.

4. **Prevention - Promotion:** Score on a scale from 1-2 (strong prevention focus: language emphasizing safety, security, duty, or avoidance of loss) to 3 (neutral or irrelevant or both) to 4-5 (strong promotion focus: language emphasizing aspiration, growth, innovation, and future opportunity). Provide a rationale for your score.

5. **Compassion - Contempt:** Score on a scale from 1-2 (overly contemptuous, dehumanizing, or divisive toward outgroups) to 3 (neutral or irrelevant) to 4-5 (compassionate, inclusive, and respectful of outgroups or marginalized populations).

**Output Format:**
Respond ONLY with a valid JSON object following this structure:

{
  "opinion_news": { "score": <integer 1-5>, "rationale": "<string>" },
  "nuance": { "score": <integer 1-5>, "rationale": "<string>" },
  "order_creativity": { "score": <integer 1-5>, "rationale": "<string>" },
  "prevention_promotion": { "score": <integer 1-5>, "rationale": "<string>" },
  "compassion_contempt": { "score": <integer 1-5>, "rationale": "<string>" }
}
"""

# --- NEW: V5 All Dimensions Prompt with RoBERTa Context ---
SYSTEM_PROMPT_V5_ALL_DIMENSIONS_CONTEXT = """
You are a media analyst AI tasked with scoring a video transcript across 5 dimensions.

**Instructions:**
Analyze the provided transcript. As additional context, you are also being given a quantitative emotional profile of the text from a RoBERTa model. Use **both the transcript and the emotional profile** to inform your scores. For each dimension, provide a score from 1-5 and a brief rationale.

**Dimensions:**

1. **News - Opinion:** Score from 1-2 (highly subjective, persuasive and analytical - the "what does this mean?" angle offering judgements and personal reflections on topics) to 3 (neutral or irrelevant) to 4-5 (highly fact-based and objective - the "who, what, when, where, why, and how" of an event).

2. **Nuance - Oversimplification:** Score on a 5-point scale from 1-2 (overly simplistic, one-sided, or binary – with absence of qualifiers, conflicting views, caveats) to 3 (balanced simple and complex) to 4-5 (highly nuanced, contextualized, and multi-perspective – with presence of qualifiers, conflicting views, and caveats).

3. **Creativity - Order:** Score on a scale from 1-2 (emphasizing control, authority, bureaucratic systems, or law and order) to 3 (a balance of both order and creativity) to 4-5 (emphasizing creativity, innovation, culture, or human-centered stories). Justify your score based on the dominant themes and framing.

4. **Prevention - Promotion:** Score on a scale from 1-2 (strong prevention focus: language emphasizing safety, security, duty, or avoidance of loss) to 3 (neutral or irrelevant or both) to 4-5 (strong promotion focus: language emphasizing aspiration, growth, innovation, and future opportunity). Provide a rationale for your score.

5. **Compassion - Contempt:** Score on a scale from 1-2 (overly contemptuous, dehumanizing, or divisive toward outgroups) to 3 (neutral or irrelevant) to 4-5 (compassionate, inclusive, and respectful of outgroups or marginalized populations). (Hint: Use the emotional profile's `admiration`, `caring`, `disgust`, `disapproval` scores to help inform this).

**Output Format:**
Respond ONLY with a valid JSON object following this structure:

{
  "opinion_news": { "score": <integer 1-5>, "rationale": "<string>" },
  "nuance": { "score": <integer 1-5>, "rationale": "<string>" },
  "order_creativity": { "score": <integer 1-5>, "rationale": "<string>" },
  "prevention_promotion": { "score": <integer 1-5>, "rationale": "<string>" },
  "compassion_contempt": { "score": <integer 1-5>, "rationale": "<string>" }
}
"""

# Prompt mapping for easy selection
PROMPTS = {
    "v1": SYSTEM_PROMPT_V1,
    "v1_context": SYSTEM_PROMPT_V1_WITH_CONTEXT,
    "v2_streamlined": SYSTEM_PROMPT_V2_STREAMLINED,
    "v3_final": SYSTEM_PROMPT_V3_FINAL,
    "v5_all_dimensions": SYSTEM_PROMPT_V5_ALL_DIMENSIONS,
    "v5_all_dimensions_context": SYSTEM_PROMPT_V5_ALL_DIMENSIONS_CONTEXT,
}

# --- Internal Helper for OpenAI ---
def _analyze_with_openai(system_prompt: str, user_prompt: str, model_name: str = "gpt-4o") -> Dict[str, Any]:
    """Internal function to call the OpenAI API."""
    if not openai.api_key:
        raise ValueError("OPENAI_API_KEY not set.")
    
    completion = openai.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"}
    )
    content = completion.choices[0].message.content
    if not content:
        raise ValueError("OpenAI API returned empty response.")
    return json.loads(content)

# --- Internal Helper for Gemini ---
def _analyze_with_gemini(full_prompt: str, model_name: str = "models/gemini-2.5-flash") -> Dict[str, Any]:
    """Internal function to call the Gemini API."""
    # Check if API key is configured (it's set via genai.configure() in module init)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in environment variables.")
    
    model = genai.GenerativeModel(model_name)  # type: ignore
    
    # Gemini uses a single prompt (combine system + user)
    # Add explicit JSON instruction
    json_prompt = f"""{full_prompt}

IMPORTANT: Respond ONLY with valid JSON. Do not include any text before or after the JSON object."""
    
    response = model.generate_content(json_prompt)
    
    # Extract JSON from response
    response_text = response.text.strip()
    
    # Try to find JSON in response (in case there's extra text)
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        response_text = json_match.group(0)
    
    return json.loads(response_text)

# --- Main Router Function (Updated to handle V3) ---
def analyze_transcript_with_llm(transcript: str, model_provider: str, prompt_version: str, model_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Main function to route the analysis to the specified model and prompt version.
    
    Args:
        transcript: The transcript text to analyze
        model_provider: "openai" or "gemini"
        prompt_version: One of the PROMPTS keys (e.g., "v5_all_dimensions")
        model_name: Optional model name override (e.g., "gpt-4o", "models/gemini-3-pro-preview")
    """
    logging.info(f"Routing request for provider: {model_provider.upper()}, prompt: {prompt_version.upper()}, model: {model_name or 'default'}")
    
    prompt_to_use = PROMPTS.get(prompt_version)
    if not prompt_to_use:
        raise ValueError(f"Unknown prompt_version. Available: {list(PROMPTS.keys())}")

    try:
        # Rate limiting: add delay between API calls
        time.sleep(1.5)  # 1.5 second delay to avoid rate limits
        
        # Workflows that require RoBERTa pre-analysis
        if prompt_version in ['v1_context', 'v2_streamlined', 'v3_final', 'v5_all_dimensions_context']:
            logging.info(f"{prompt_version.upper()} Workflow: Running RoBERTa pre-analysis...")
            roberta_result = run_go_emotions(transcript, "roberta_go_emotions")
            roberta_scores = roberta_result.get("average_scores", {})
            roberta_scores_json = json.dumps({k: round(v, 4) for k, v in roberta_scores.items()}, indent=2)

            user_prompt_with_context = f"""
**Transcript to Analyze:**
```
{transcript}
```

**Emotional Profile Context:**
```json
{roberta_scores_json}
```
"""
            if model_provider == "openai":
                logging.info(f"{prompt_version.upper()} Workflow: Sending combined prompt to OpenAI...")
                openai_model = model_name if model_name else "gpt-4o"
                return _analyze_with_openai(prompt_to_use, user_prompt_with_context, model_name=openai_model)
            elif model_provider == "gemini":
                # Combine system and user prompts for Gemini
                combined_prompt = f"{prompt_to_use}\n\n{user_prompt_with_context}"
                logging.info(f"{prompt_version.upper()} Workflow: Sending combined prompt to Gemini...")
                gemini_model = model_name if model_name else "models/gemini-2.5-flash"
                return _analyze_with_gemini(combined_prompt, model_name=gemini_model)
            else:
                raise ValueError(f"Provider '{model_provider}' not supported for context-aware prompts.")

        # Workflows without RoBERTa context
        else:
            user_prompt = f"**Transcript to Analyze:**\n```\n{transcript}\n```"
            
            if model_provider == "openai":
                openai_model = model_name if model_name else "gpt-4o"
                return _analyze_with_openai(prompt_to_use, user_prompt, model_name=openai_model)
            elif model_provider == "gemini":
                # Combine system and user prompts for Gemini
                combined_prompt = f"{prompt_to_use}\n\n{user_prompt}"
                gemini_model = model_name if model_name else "models/gemini-2.5-flash"
                return _analyze_with_gemini(combined_prompt, model_name=gemini_model)
            else:
                raise ValueError(f"Provider '{model_provider}' not configured. Use 'openai' or 'gemini'.")
        
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON from {model_provider.upper()} response: {e}")
        raise ValueError("The model returned an invalid JSON response.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise


