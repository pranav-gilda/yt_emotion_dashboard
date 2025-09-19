import logging
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import pipeline
from typing import Dict, Any

# --- Basic Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
app = FastAPI()

# --- CORS Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
class TranscriptRequest(BaseModel):
    transcript: str

class FeedbackPayload(BaseModel):
    original_transcript: str
    model_analysis: Dict[str, Any]
    user_feedback: Dict[str, Any]

# --- ML Model Loading ---
classifier = None

@app.on_event("startup")
async def startup_event():
    global classifier
    logging.info("Application startup...")
    try:
        logging.info("Loading RoBERTa model... (This should only happen once!)")
        classifier = pipeline(
            task="text-classification",
            model="SamLowe/roberta-base-go_emotions",
            top_k=None
        )
        logging.info("✅ RoBERTa model loaded successfully. Server is ready.")
    except Exception as e:
        logging.error(f"💥 Failed to load model during startup: {e}", exc_info=True)
        classifier = None

# --- API Endpoints ---
@app.post("/run_models")
async def run_models(request: TranscriptRequest):
    logging.info("Received new transcript for analysis.")
    if not classifier:
        raise HTTPException(status_code=503, detail="Model is not available or failed to load.")
    if not request.transcript:
        raise HTTPException(status_code=400, detail="Transcript cannot be empty.")

    try:
        cleaned_transcript = request.transcript.strip().replace("\n", " ")
        
        # --- THE DEFINITIVE FIX ---
        # We no longer manually split the string.
        # Instead, we pass the truncation argument directly to the pipeline.
        # This lets the tokenizer handle long text precisely and correctly.
        model_outputs = classifier(cleaned_transcript, truncation=True, max_length=512)
        # --- END FIX ---
        
        all_emotions_dict = {item['label']: item['score'] for item in model_outputs[0]}
        
        respect_list = ["admiration", "approval", "caring"]
        contempt_list = ["disapproval", "disgust", "annoyance"]
        positive_list = ["amusement", "excitement", "joy", "love", "optimism", "pride", "relief", "gratitude"]
        negative_list = ["anger", "disappointment", "embarrassment", "fear", "grief", "nervousness", "remorse", "sadness"]
        neutral_list = ["confusion", "curiosity", "desire", "realization", "surprise", "neutral"]

        def get_emotion_details(category_list):
            return sorted(
                [{'label': e, 'score': all_emotions_dict.get(e, 0)} for e in category_list if all_emotions_dict.get(e, 0) > 0.001],
                key=lambda x: x['score'],
                reverse=True
            )

        emotions_by_category = {
            "respect": get_emotion_details(respect_list),
            "contempt": get_emotion_details(contempt_list),
            "positive": get_emotion_details(positive_list),
            "negative": get_emotion_details(negative_list),
            "neutral_breakdown": get_emotion_details(neutral_list)
        }
        
        aggregate_scores = {
            cat: sum(e['score'] for e in emotions) for cat, emotions in emotions_by_category.items()
        }
        
        dominant_emotion = max(all_emotions_dict, key=all_emotions_dict.get) if all_emotions_dict else "neutral"
        
        final_output = {
            "aggregate_scores": aggregate_scores,
            "emotions": emotions_by_category,
            "dominant_emotion": dominant_emotion
        }
        
        logging.info("Analysis complete, returning results.")
        return final_output
    except Exception as e:
        logging.error(f"Error during model inference: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred during model processing.")

@app.post("/feedback")
async def receive_feedback(payload: FeedbackPayload):
    feedback_file = 'feedback_log.xlsx'
    try:
        feedback_data = {
            'timestamp': pd.Timestamp.now(),
            'user_rating': payload.user_feedback.get('rating', 'N/A'),
            'user_emotion': payload.user_feedback.get('user_emotion', 'N/A'),
            'user_comment': payload.user_feedback.get('comment', ''),
            'respect_score': payload.model_analysis.get('aggregate_scores', {}).get('respect', 0),
            'contempt_score': payload.model_analysis.get('aggregate_scores', {}).get('contempt', 0),
            'transcript': payload.original_transcript
        }
        
        new_feedback_df = pd.DataFrame([feedback_data])

        try:
            existing_df = pd.read_excel(feedback_file)
            combined_df = pd.concat([existing_df, new_feedback_df], ignore_index=True)
        except FileNotFoundError:
            combined_df = new_feedback_df

        combined_df.to_excel(feedback_file, index=False)
        
        return {"status": "success", "message": "Feedback received"}
    except Exception as e:
        logging.error(f"Failed to process feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save feedback.")