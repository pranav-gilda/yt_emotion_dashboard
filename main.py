import logging
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import pipeline
from typing import Dict

# --- Basic Setup ---
logging.basicConfig(level=logging.INFO)
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
    model_type: str
    transcript: str
    model_output: Dict
    user_rating: int
    user_emotion: str
    user_comment: str

# --- ML Model Loading ---
# This is a global variable that will hold the loaded model.
classifier = None

@app.on_event("startup")
async def startup_event():
    """Load the model on server startup."""
    global classifier
    try:
        logging.info("Loading RoBERTa model...")
        classifier = pipeline(
            task="text-classification",
            model="SamLowe/roberta-base-go_emotions",
            top_k=None
        )
        logging.info("RoBERTa model loaded successfully.")
    except Exception as e:
        logging.error(f"Failed to load model during startup: {e}", exc_info=True)
        # The app will continue to run, but endpoints will fail until the model is loaded.
        classifier = None

# --- API Endpoints ---
@app.post("/run_roberta_model")
async def run_roberta_model(request: TranscriptRequest):
    if not classifier:
        raise HTTPException(status_code=503, detail="Model is not available or failed to load.")
    if not request.transcript:
        raise HTTPException(status_code=400, detail="Transcript cannot be empty.")

    try:
        cleaned_transcript = request.transcript.strip().replace("\n", " ")
        model_outputs = classifier(cleaned_transcript)
        
        all_emotions = {item['label']: round(item['score'] * 100, 2) for item in model_outputs[0]}
        
        respect_emotions = ["admiration", "approval", "gratitude", "love", "optimism", "caring", "pride", "joy", "excitement", "relief"]
        contempt_emotions = ["anger", "annoyance", "disappointment", "disapproval", "disgust", "fear", "grief", "nervousness", "remorse", "sadness"]

        respect_total = sum(all_emotions.get(e, 0) for e in respect_emotions)
        contempt_total = sum(all_emotions.get(e, 0) for e in contempt_emotions)
        
        final_output = {
            "respect_total": round(respect_total, 2),
            "contempt_total": round(contempt_total, 2),
            "all_emotions": all_emotions
        }
        
        return final_output
    except Exception as e:
        logging.error(f"Error during model inference: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred during model processing.")

@app.post("/feedback")
async def receive_feedback(payload: FeedbackPayload):
    feedback_file = 'feedback_log.xlsx'
    try:
        # Flatten the model_output data for clean columns
        respect_score = payload.model_output.get('respect_total', 0)
        contempt_score = payload.model_output.get('contempt_total', 0)

        feedback_data = {
            'timestamp': pd.Timestamp.now(),
            'user_rating': 'up' if payload.user_rating == 1 else 'down',
            'user_emotion': payload.user_emotion,
            'user_comment': payload.user_comment,
            'respect_score': respect_score,
            'contempt_score': contempt_score,
            'transcript': payload.transcript
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

