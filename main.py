import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import pandas as pd
from datetime import datetime
import logging
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import openpyxl
import mlflow
import models 
from llm_analyzer import analyze_transcript_with_llm

load_dotenv()
logging.basicConfig(level=logging.INFO)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

class TranscriptRequest(BaseModel):
    transcript: str

class FeedbackPayload(BaseModel):
    model_type: str
    original_transcript: str
    model_analysis: Dict[str, Any]
    user_feedback: Dict[str, Any]

@app.post("/feedback")
async def receive_feedback(payload: FeedbackPayload):
    feedback_file_path = f"feedback_{payload.model_type}.xlsx"
    new_feedback_row = {
        "timestamp": datetime.now().isoformat(),
        "user_rating": payload.user_feedback.get('rating'),
        "user_dominant_emotion": payload.user_feedback.get('user_emotion'),
        "user_comment": payload.user_feedback.get('comment'),
        "model_analysis_json": str(payload.model_analysis),
        "original_transcript": payload.original_transcript
    }
    if os.path.exists(feedback_file_path):
        df = pd.read_excel(feedback_file_path, engine='openpyxl')
        new_row_df = pd.DataFrame([new_feedback_row])
        df = pd.concat([df, new_row_df], ignore_index=True)
    else:
        df = pd.DataFrame([new_feedback_row])
    df.to_excel(feedback_file_path, index=False, engine='xlsxwriter')
    logging.info(f"Feedback successfully saved to {feedback_file_path}")
    return {"status": "success", "message": "Feedback received!"}

@app.post("/run_roberta_model")
def run_roberta_model(request: TranscriptRequest):
    try:
        result = models.run_go_emotions(request.transcript, "roberta_go_emotions")
        average_scores = result.get("average_scores", {})
        
        # Convert all scores to percentages (0-100 scale)
        percent_scores = {key: value * 100 for key, value in average_scores.items()}
    
        neutral_score = percent_scores.get('neutral', 0)
        respect_emotions = ['approval', 'caring', 'admiration']
        contempt_emotions = ['disapproval', 'disgust', 'annoyance']
        positive_emotions = ['amusement', 'excitement', 'joy', 'love', 'optimism', 'pride', 'relief', 'gratitude']
        negative_emotions = ['anger', 'disappointment', 'embarrassment', 'fear', 'grief', 'nervousness', 'remorse', 'sadness']
        neutral_emotions_list = ['confusion', 'curiosity', 'desire', 'realization', 'surprise']
        
        # Change aggregation from average to SUM of percentages
        def agg(emolist):
            return sum([percent_scores.get(e, 0) for e in emolist])
        
        agg_scores = {'respect': agg(respect_emotions), 'contempt': agg(contempt_emotions), 'positive': agg(positive_emotions), 'negative': agg(negative_emotions)}
        
        def emotion_scores(emolist):
            return [{'label': e.capitalize(), 'score': percent_scores.get(e, 0)} for e in emolist]
            
        grouped = {'respect': emotion_scores(respect_emotions), 'contempt': emotion_scores(contempt_emotions), 'positive': emotion_scores(positive_emotions), 'negative': emotion_scores(negative_emotions), 'neutral_breakdown': emotion_scores(neutral_emotions_list)}
        
        return {
            'dominant_emotion': result.get('dominant_emotion'),
            'dominant_emotion_score': percent_scores.get(result.get('dominant_emotion'), 0),
            'aggregate_scores': agg_scores,
            'neutral_score': neutral_score,
            'emotions': grouped
        }
    except Exception as e:
        logging.error(f"Error in RoBERTa model endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze_with_llm")
async def analyze_with_llm_endpoint(request: TranscriptRequest):
    try:
        if not request.transcript:
            raise HTTPException(status_code=400, detail="Transcript cannot be empty.")
        analysis_result = analyze_transcript_with_llm(request.transcript, model_name="gemini")
        
        return analysis_result
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logging.error(f"Error in LLM analysis endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred during LLM analysis.")

# --- New Pydantic Model for MLflow Logging ---
class MLflowLogPayload(BaseModel):
    model_name: str
    prompt_version: str
    transcript: str
    analysis_output: Dict[str, Any]
    # You could add more context here later, like the YouTube video ID

@app.post("/log_llm_run")
async def log_llm_run_to_mlflow(payload: MLflowLogPayload):
    """
    Receives the results of a real-world analysis from the extension
    and logs the entire run to MLflow for later review.
    """
    try:
        with mlflow.start_run(run_name=f"LiveRun_{payload.model_name}"):
            # Log parameters
            mlflow.log_param("run_type", "live_extension")
            mlflow.log_param("model_name", payload.model_name)
            mlflow.log_param("prompt_version", payload.prompt_version)
            mlflow.log_param("transcript_length", len(payload.transcript))

            # Log the actual text inputs and outputs as artifacts
            mlflow.log_text(payload.transcript, "transcript.txt")
            mlflow.log_dict(payload.analysis_output, "analysis_output.json")

            # Log key output metrics for easy comparison in the UI
            for dimension, values in payload.analysis_output.items():
                if isinstance(values, dict) and 'score' in values:
                    mlflow.log_metric(f"score_{dimension}", values['score'])
        
        return {"status": "success", "message": "Run logged to MLflow."}
    except Exception as e:
        logging.error(f"Failed to log run to MLflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to log run to MLflow.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
