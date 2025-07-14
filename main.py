import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import boto3
import models
import logging
import io
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import openpyxl

load_dotenv()

logging.basicConfig(level=logging.INFO)
logging.info(f"🧠 main.py is loading models from: {models.__file__}")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

class TranscriptRequest(BaseModel):
    transcript: str
    model_name: str = "roberta_go_emotions"

class FeedbackPayload(BaseModel):
    original_transcript: str
    model_analysis: Dict[str, Any]
    user_feedback: Dict[str, Any]

FEEDBACK_FILE_PATH = "feedback_log.xlsx"

@app.post("/feedback")
async def receive_feedback(payload: FeedbackPayload):
    """
    Receives feedback from the extension and appends it as a new row in an Excel file.
    """
    try:
        # Flatten the data into a single dictionary for the new row
        new_feedback_row = {
            "timestamp": datetime.now().isoformat(),
            "user_rating": payload.user_feedback.get('rating'),
            "user_dominant_emotion": payload.user_feedback.get('user_emotion'),
            "user_comment": payload.user_feedback.get('comment'),
            "model_dominant_emotion": payload.model_analysis.get('dominant_emotion'),
            "model_dominant_score": payload.model_analysis.get('dominant_emotion_score'),
            "model_respect_score": payload.model_analysis.get('aggregate_scores', {}).get('respect'),
            "model_contempt_score": payload.model_analysis.get('aggregate_scores', {}).get('contempt'),
            "original_transcript": payload.original_transcript
        }
        
        # Check if the feedback file exists to either load it or create a new one
        if os.path.exists(FEEDBACK_FILE_PATH):
            df = pd.read_excel(FEEDBACK_FILE_PATH)
            # Use pd.concat to append the new row
            new_row_df = pd.DataFrame([new_feedback_row])
            df = pd.concat([df, new_row_df], ignore_index=True)
        else:
            df = pd.DataFrame([new_feedback_row])
            
        # Save the updated DataFrame back to the Excel file
        df.to_excel(FEEDBACK_FILE_PATH, index=False)
        
        logging.info(f"Feedback successfully saved to {FEEDBACK_FILE_PATH}")
        
        return {"status": "success", "message": "Feedback received. Thank you!"}
    except Exception as e:
        logging.error(f"Error processing feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error processing feedback.")


@app.post("/run_models")
def run_models(request: TranscriptRequest):
    """
    Receives raw transcript text, runs emotion analysis, and returns a
    structured JSON response compatible with the extension's UI.
    """
    try:
        if request.model_name not in {"go_emotions", "roberta_go_emotions"}:
            raise HTTPException(status_code=400, detail="Model not recognized.")
        
        result = models.run_go_emotions(request.transcript, request.model_name)
        average_scores = result.get("average_scores", {})

        # Separate the neutral score from the other aggregate calculations
        neutral_score = average_scores.get('neutral', 0)

        respect_emotions = ['approval', 'caring', 'admiration']
        contempt_emotions = ['disapproval', 'disgust', 'annoyance']
        positive_emotions = ['amusement', 'excitement', 'joy', 'love', 'optimism', 'pride', 'relief', 'gratitude']
        negative_emotions = ['anger', 'disappointment', 'embarrassment', 'fear', 'grief', 'nervousness', 'remorse', 'sadness']
        
        # Note: The 'neutral_emotions' list is now only used for the detailed breakdown
        neutral_emotions_list = ['confusion', 'curiosity', 'desire', 'realization', 'surprise']


        def agg(emolist):
            vals = [average_scores.get(e, 0) for e in emolist]
            return sum(vals) / len(vals) if vals else 0

        agg_scores = {
            'respect': agg(respect_emotions),
            'contempt': agg(contempt_emotions),
            'positive': agg(positive_emotions),
            'negative': agg(negative_emotions),
        }

        def emotion_scores(emolist):
            return [{'label': e.capitalize(), 'score': round(average_scores.get(e, 0), 4)} for e in emolist]

        grouped = {
            'respect': emotion_scores(respect_emotions),
            'contempt': emotion_scores(contempt_emotions),
            'positive': emotion_scores(positive_emotions),
            'negative': emotion_scores(negative_emotions),
            'neutral_breakdown': emotion_scores(neutral_emotions_list), # For details view
        }

        return {
            'dominant_emotion': result.get('dominant_emotion'),
            'dominant_emotion_score': result.get('dominant_emotion_score'),
            'dominant_attitude_emotion': result.get('dominant_attitude_emotion'),
            'dominant_attitude_score': result.get('dominant_attitude_score'),
            'aggregate_scores': agg_scores,
            'neutral_score': neutral_score, # Add the separate neutral score
            'emotions': grouped
        }

    except Exception as e:
        logging.error(f"Error in /run_models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
