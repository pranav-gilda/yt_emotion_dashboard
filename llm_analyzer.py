import os
import openai
import google.generativeai as genai
import json
import logging
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()
# --- API Key Configuration ---
openai.api_key = os.getenv("OPENAI_API_KEY")
genai.configure(api_key=os.getenv("GEMINI_API_KEY")) # type: ignore

# This is the prompt your team developed. We can version this in the future.
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
Respond ONLY with a valid JSON object. Do not include any other text or explanations outside of the JSON. The JSON object must follow this structure:

{
  "nuance": { "score": <integer>, "rationale": "<string>" },
  "creativity_vs_order": { "score": <integer>, "rationale": "<string>" },
  "safety_vs_threat": { "score": <integer>, "rationale": "<string>" },
  "compassion_vs_contempt": { "score": <integer>, "rationale": "<string>" },
  "reporting_vs_opinion": { "score": <integer>, "rationale": "<string>" }
}
"""

def analyze_with_openai(transcript: str) -> Dict[str, Any]:
    """Sends the transcript to the OpenAI API."""
    if not openai.api_key:
        raise ValueError("OPENAI_API_KEY not set.")
    
    user_prompt = f"**Transcript to Analyze:**\n```\n{transcript}\n```"
    completion = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_V1},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(completion.choices[0].message.content)

def analyze_with_gemini(transcript: str) -> Dict[str, Any]:
    """Sends the transcript to the Google Gemini API."""
    if not os.getenv("GEMINI_API_KEY"):
        raise ValueError("GEMINI_API_KEY not set.")
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    full_prompt = f"{SYSTEM_PROMPT_V1}\n\n**Transcript to Analyze:**\n```\n{transcript}\n```"
    
    # Gemini requires the response_mime_type for JSON output
    response = model.generate_content(
        full_prompt,
        generation_config=genai.types.GenerationConfig(
            response_mime_type="application/json"
        )
    )
    return json.loads(response.text)

def analyze_transcript_with_llm(transcript: str, model_name: str) -> Dict[str, Any]:
    """
    Main function to route the analysis to the specified model.
    """
    logging.info(f"Sending transcript to {model_name.upper()} API for analysis...")
    try:
        if model_name == "openai":
            result = analyze_with_openai(transcript)
        elif model_name == "gemini":
            result = analyze_with_gemini(transcript)
        else:
            raise ValueError(f"Unknown model_name: {model_name}. Use 'openai' or 'gemini'.")
        
        logging.info(f"Successfully received and parsed analysis from {model_name.upper()}.")
        return result
        
    except json.JSONDecodeError:
        logging.error(f"Failed to decode JSON from {model_name.upper()} response.")
        raise ValueError("The model returned an invalid JSON response.")
    except Exception as e:
        logging.error(f"An unexpected error occurred with the {model_name.upper()} API: {e}")
        raise
