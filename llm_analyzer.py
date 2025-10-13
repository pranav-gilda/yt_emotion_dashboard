import os
import openai
import google.generativeai as genai
import json
import logging
from typing import Dict, Any
from dotenv import load_dotenv

# Import the RoBERTa function from your models file
from models import run_go_emotions

load_dotenv()
# --- API Key Configuration ---
openai.api_key = os.getenv("OPENAI_API_KEY")
genai.configure(api_key=os.getenv("GEMINI_API_KEY")) # type: ignore

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

# Prompt mapping for easy selection
PROMPTS = {
    "v1": SYSTEM_PROMPT_V1,
    "v1_context": SYSTEM_PROMPT_V1_WITH_CONTEXT,
    "v2_streamlined": SYSTEM_PROMPT_V2_STREAMLINED, # New default prompt
}

# --- Internal Helper for OpenAI ---
def _analyze_with_openai(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    """Internal function to call the OpenAI API."""
    if not openai.api_key:
        raise ValueError("OPENAI_API_KEY not set.")
    
    completion = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(completion.choices[0].message.content)

# --- Main Router Function (Corrected and Complete) ---
def analyze_transcript_with_llm(transcript: str, model_provider: str, prompt_version: str) -> Dict[str, Any]:
    """
    Main function to route the analysis to the specified model and prompt version.
    """
    logging.info(f"Routing request for provider: {model_provider.upper()}, prompt: {prompt_version.upper()}")
    
    prompt_to_use = PROMPTS.get(prompt_version)
    if not prompt_to_use:
        raise ValueError(f"Unknown prompt_version: {prompt_version}. Use 'v1', 'v1_context', or 'v2_streamlined'.")

    try:
        # Workflows that require RoBERTa pre-analysis
        if prompt_version in ['v1_context', 'v2_streamlined']:
            if model_provider != 'openai':
                raise ValueError("The context-aware prompts currently only support the 'openai' provider.")
            
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
            logging.info(f"{prompt_version.upper()} Workflow: Sending combined prompt to OpenAI...")
            return _analyze_with_openai(prompt_to_use, user_prompt_with_context)

        # Original "v1" workflow for backward compatibility and testing
        else:
            user_prompt = f"**Transcript to Analyze:**\n```\n{transcript}\n```"
            if model_provider == "openai":
                return _analyze_with_openai(prompt_to_use, user_prompt)
            elif model_provider == "gemini":
                full_prompt = f"{prompt_to_use}\n\n{user_prompt}"
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(response_mime_type="application/json")
                )
                return json.loads(response.text)
            else:
                raise ValueError(f"Unknown model_provider: {model_provider}.")
        
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON from {model_provider.upper()} response: {e}")
        raise ValueError("The model returned an invalid JSON response.")
    except Exception as e:
        logging.error(f"An unexpected error occurred with the {model_provider.upper()} API: {e}")
        raise

