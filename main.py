import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from config import OUTPUT_DIR
from utils import create_directory
from transcript_downloader import download_transcript, get_transcript
from video_details import get_video_details
from history_extractor import extract_history
import boto3
import models
import logging
import io
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logging.info(f"🧠 main.py is loading models from: {models.__file__}")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

# Initialize S3 client
s3 = boto3.client('s3')
BUCKET_NAME = "yt-user-history-bucket"

class UsernameRequest(BaseModel):
    username: Optional[str] = None

@app.post("/users/history")
async def store_user_history(request: UsernameRequest):
    """Extracts user history, analyzes emotions, and stores an enriched Excel in S3."""
    try:
        # Use provided username or a default
        username = request.username if request.username else "default_user"
        logging.info(f"Processing history for user: {username}")

        # 1. Extract history data locally
        history_df = extract_history()

        logging.info(f"Extracted history with {len(history_df)} entries.") # Log count of entries
        logging.info(f"Columns in extracted history: {history_df.columns.tolist()}") # Log columns

        # 2. Process history and get emotion analysis
        processed_videos_data = []
        category_dir = os.path.join(OUTPUT_DIR, "history")
        create_directory(category_dir)

        logging.info("Starting video processing loop...") # Log before loop
        if history_df.empty:
            logging.warning("History DataFrame is empty. Skipping video processing loop.")

        for index, row in history_df.iterrows():
            # Log row index and some data to see if the loop is running and what's being processed
            video_url = row.get('video_url')
            video_title = row.get('video_title')
            logging.info(f"Processing row {index}: URL={video_url}, Title={video_title}")

            video = {
                "browser": row.get("browser"),
                "date_watched": row.get("date_watched"), # Corrected column name
                "video_title": video_title,              # Corrected variable usage
                "url": video_url                         # Corrected variable usage
            }
            if not video.get("url"): 
                logging.warning(f"Skipping row {index} due to missing URL after checking 'video_url' column.")
                continue # Skip rows without URL

            logging.info(f"Calling process_video for URL: {video.get('url')}") # Log before calling process_video

            # The process_video function itself will have logging inside now as well
            video_details = process_video(video["url"], category_dir)

            emotion_analysis = None
            if video_details["transcript"] != "NA":
                 try:
                    logging.info(f"Analyzing emotions for transcript from {video.get('url')}") # Log before analysis
                    emotion_analysis = models.analyse_transcript(video_details["transcript"], "roberta_go_emotions")
                    logging.info(f"Emotion analysis complete for {video.get('url')}. Result: {list(emotion_analysis.keys())}") # Log analysis success
                 except Exception as e:
                     logging.error(f"Error analyzing transcript for {video.get('video_title')}: {e}", exc_info=True)
                     emotion_analysis = None # Ensure it's None on error

            # Process emotion analysis into a flattened DataFrame row
            if emotion_analysis:
                # Use models.to_dataframe to flatten the analysis result
                emotion_df = models.to_dataframe(emotion_analysis)

                # Rename average_scores columns to just emotion names
                renamed_emotion_data = {}
                for col in emotion_df.columns:
                    if col.startswith("average_scores."):
                        # Remove the 'average_scores.' prefix
                        new_col_name = col.replace("average_scores.", "")
                        renamed_emotion_data[new_col_name] = emotion_df.iloc[0][col]
                    else:
                        # Keep other columns (dominant emotions) as they are
                        renamed_emotion_data[col] = emotion_df.iloc[0][col]

                # Combine original video data with renamed and flattened emotion data
                processed_video_data = {
                    "browser": video["browser"],
                    "date_watched": video["date_watched"],
                    "video_title": video["video_title"],
                    "url": video["url"],
                    "transcript": video_details["transcript"],
                    "seconds_watched": video_details["seconds_watched"],
                    "category_watched": video_details["category_watched"],
                    **renamed_emotion_data # Merge the renamed emotion data
                }
            else:
                # If no emotion analysis, just include original video data and NA for emotion fields
                processed_video_data = {
                    "browser": video["browser"],
                    "date_watched": video["date_watched"],
                    "video_title": video["video_title"],
                    "url": video["url"],
                    "transcript": video_details["transcript"],
                    "seconds_watched": video_details["seconds_watched"],
                    "category_watched": video_details["category_watched"],
                    # No emotion data to add if analysis failed or no transcript
                }

            processed_videos_data.append(processed_video_data)

        logging.info(f"Finished video processing loop. Collected {len(processed_videos_data)} processed video data entries.") # Log after loop

        # 3. Create and save enriched Excel to S3
        if processed_videos_data:
            logging.info("Creating styled Excel from processed video data.") # Log before Excel creation
            # Create DataFrame from the list of dictionaries
            combined_df = pd.DataFrame(processed_videos_data)

            # Ensure all ALL_EMOTIONS columns and dominant emotion columns are present (now using simple names),
            # filling missing values with 0 for scores and None for labels if a video had no transcript/analysis.
            expected_emotion_cols = list(models.ALL_EMOTIONS) + \
                                    ["dominant_emotion", "dominant_emotion_score", "dominant_attitude_emotion", "dominant_attitude_score"]
            for col in expected_emotion_cols:
                if col not in combined_df.columns:
                     if "score" in col or col in models.ALL_EMOTIONS: # Emotion scores and dominant scores
                          combined_df[col] = 0 # Fill missing scores with 0
                     else:
                          combined_df[col] = None # Fill missing labels with None

            # --- Define the desired column order (using simple names) ---
            original_cols = ["unique_id", "browser", "date_watched", "video_title", "url", "transcript", "seconds_watched", "category_watched"]
            dominant_cols = ["dominant_emotion", "dominant_emotion_score", "dominant_attitude_emotion", "dominant_attitude_score"]

            # Emotion score columns based on user's desired order (using simple names)
            respect_cols = list(models.RESPECT) # Use list to maintain potential order if set matters
            contempt_cols = list(models.CONTEMPT)
            neutral_col = ["neutral"] if "neutral" in combined_df.columns else []

            # Get all simple emotion name columns that are not in respect, contempt, or neutral
            all_simple_emotion_cols = [col for col in combined_df.columns if col in models.ALL_EMOTIONS]
            specific_emotion_cols_set = set(respect_cols + contempt_cols + neutral_col)
            remaining_emotion_cols = sorted([col for col in all_simple_emotion_cols if col not in specific_emotion_cols_set])

            # Combine and reindex DataFrame in the specified order
            # Ensure only columns that actually exist in the df are included in ordered_cols before reindexing
            ordered_cols = [col for col in original_cols + respect_cols + contempt_cols + neutral_col + remaining_emotion_cols + dominant_cols if col in combined_df.columns]


            # Select and reorder columns, dropping any unexpected ones and adding missing expected ones (filled with defaults above)
            combined_df = combined_df[ordered_cols]

            # Add a unique ID for each row after sorting
            combined_df['unique_id'] = range(len(combined_df))

            # Use the new function from models.py to create styled Excel bytes
            excel_bytes_io = models.create_styled_excel_bytes(combined_df)
            logging.info("Excel bytes object created.") # Log after Excel creation

            # Upload to S3
            s3_key = f"{username}/history_emotions.xlsx"
            logging.info(f"Attempting to upload enriched history Excel to S3: {s3_key}") # Log before S3 upload
            s3.put_object(
                Bucket=BUCKET_NAME,
                Key=s3_key,
                Body=excel_bytes_io.getvalue()
            )
            logging.info(f"Enriched history Excel saved to S3: {s3_key}")

        else:
            logging.warning("No processed video data collected. Skipping Excel creation and S3 upload.")

        return {"status": "success", "message": "History processed and enriched Excel stored in S3"}

    except Exception as e:
        logging.error(f"Error in /users/history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

class VideoData(BaseModel):
    browser: str
    date_watched: str
    video_title: str
    url: str
    transcript: Optional[str]
    seconds_watched: int
    category_watched: str

def process_video(url: str, category_dir: str) -> Dict:
    """Processes a single video URL, downloads transcript, gets details, and returns results."""
    logging.info(f"Inside process_video for URL: {url}") # Log at start of process_video

    transcript_downloaded = download_transcript(url, category_dir) # This now saves locally
    
    # Get the transcript content from the local file after attempting download
    transcript_content = get_transcript(url, category_dir) # This reads from the local file

    try:
        seconds_watched, category_watched = get_video_details(url) # Replace with actual implementation
    except Exception as e:
        logging.error(f"Error getting video details for {url}: {e}")
        seconds_watched = 0
        category_watched = "NA"

    return {
        "transcript": transcript_content, # Return the content read from the local file
        "seconds_watched": seconds_watched,
        "category_watched": category_watched
    }

@app.get("/run_models")
def run_models(transcript: str, 
               model_name: str = "roberta_go_emotions", # Set default model_name
               file_name: Optional[str] = None):
    """
    Return clean JSON.  
    If `file_name` is given, a styled Excel is also written to results/<file_name>.xlsx
    """
    try:
        if model_name not in {"go_emotions", "roberta_go_emotions"}:
            raise HTTPException(status_code=400, detail="Model not recognized.")
        result = models.run_go_emotions(transcript, model_name, file_name)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download_excel")
def download_excel(username: str = "default_user"):
    """
    Fetches the enriched history Excel from S3 for a given user (or default) and streams it back.
    """
    try:
        logging.info(f"Attempting to fetch enriched history Excel for user: {username} from S3")

        s3_key = f"{username}/history_emotions.xlsx"

        # Fetch the Excel file from S3
        response = s3.get_object(
            Bucket=BUCKET_NAME,
            Key=s3_key
        )

        # Read the content from the S3 response body
        excel_content = response['Body']

        # Define headers for the response to indicate it's an Excel file download
        headers = {
            "Content-Disposition": f'attachment; filename="{username}_history_emotions.xlsx"'
        }

        logging.info(f"Successfully fetched and streaming enriched history Excel from S3: {s3_key}")

        # Return the S3 object body as a StreamingResponse
        return StreamingResponse(excel_content,
                                 media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                 headers=headers)

    except s3.exceptions.NoSuchKey:
        logging.warning(f"Enriched history Excel not found for user: {username} at {s3_key}")
        raise HTTPException(status_code=404, detail="User history not found. Please run the POST /users/history endpoint first.")
    except Exception as e:
        logging.error(f"Error in GET /download_excel for user {username}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

class VideoRequest(BaseModel):
    url: str

@app.post("/process_video")
async def process_video_endpoint(request: VideoRequest):
    try:
        url = request.url
        video_dir = os.path.join(OUTPUT_DIR, "temp_videos")
        create_directory(video_dir)

        # 1. Download and get transcript
        download_transcript(url, video_dir)
        transcript = get_transcript(url, video_dir)
        if not transcript or transcript == "NA":
            raise HTTPException(status_code=404, detail="No transcript available for this video.")

        # 2. Run emotion model
        result = models.run_go_emotions(transcript, "roberta_go_emotions")
        average_scores = result.get("average_scores", {})

        # Define emotion categories
        respect_emotions = ['approval', 'caring', 'admiration']
        contempt_emotions = ['disapproval', 'disgust', 'annoyance']
        neutral_emotions = ['confusion', 'curiosity', 'desire', 'realization', 'surprise', 'neutral']
        positive_emotions = ['amusement', 'excitement', 'joy', 'love', 'optimism', 'pride', 'relief', 'gratitude']
        negative_emotions = ['anger', 'disappointment', 'embarrassment', 'fear', 'grief', 'nervousness', 'remorse', 'sadness']

        # Calculate aggregate scores
        def agg(emolist):
            vals = [average_scores.get(e, 0) for e in emolist]
            return sum(vals) / len(vals) if vals else 0

        agg_scores = {
            'respect': agg(respect_emotions),
            'contempt': agg(contempt_emotions),
            'neutral': agg(neutral_emotions),
            'positive': agg(positive_emotions),
            'negative': agg(negative_emotions),
        }

        # Prepare per-emotion scores grouped by category
        def emotion_scores(emolist):
            return [{
                'label': e.capitalize(),
                'score': round(average_scores.get(e, 0), 4)
            } for e in emolist]

        grouped = {
            'respect': emotion_scores(respect_emotions),
            'contempt': emotion_scores(contempt_emotions),
            'neutral': emotion_scores(neutral_emotions),
            'positive': emotion_scores(positive_emotions),
            'negative': emotion_scores(negative_emotions),
        }

        return {
            'dominant_emotion': result.get('dominant_emotion'),
            'dominant_emotion_score': result.get('dominant_emotion_score'),
            'dominant_attitude_emotion': result.get('dominant_attitude_emotion'),
            'dominant_attitude_score': result.get('dominant_attitude_score'),
            'aggregate_scores': agg_scores,
            'emotions': grouped
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in /process_video: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
