import os
import logging
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from youtube_transcript_api._errors import NoTranscriptFound # Import specific error for better handling
from utils import get_video_id, create_directory

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def download_transcript(video_url, output_folder):
    """Downloads and saves the transcript of a YouTube video.
    Uses basic functionality compatible with youtube-transcript-api<=1.0.3.
    Only fetches manual English transcripts if available.
    """
    try:
        logging.info(f"Attempting to fetch transcript for: {video_url}")

        video_id = get_video_id(video_url)
        if not video_id:
            logging.error(f"Failed to extract video ID from: {video_url}")
            return False

        # Using functionality compatible with older versions (<=1.0.3)
        # This primarily attempts to fetch manual English transcripts.
        logging.info(f"Attempting to get manual English transcript for video ID: {video_id} (using youtube-transcript-api<=1.0.3 compatible call).")

        try:
            # Removed languages and continue_after_error for compatibility
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)

            logging.info(f"Received transcript_list for {video_id} with {len(transcript_list)} entries.") # Log number of entries

            if not transcript_list:
                 # This case might be less likely with old version's behavior,
                 # as NoTranscriptFound is typically raised instead of returning an empty list.
                 logging.warning(f"Received empty transcript list for {video_url}.")
                 return False

            logging.info(f"Successfully fetched transcript data for {video_url}. Proceeding to format manually.") # Log success before manual formatting

            # Manually format transcript by joining text entries
            formatted_transcript = " ".join([entry['text'] for entry in transcript_list])

            logging.info(f"Successfully formatted transcript manually for {video_url}.") # Log after manual formatting

            # Ensure output folder exists
            create_directory(output_folder)

            # Save transcript
            output_file = os.path.join(output_folder, f"{video_id}.txt")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(formatted_transcript)

            logging.info(f"Transcript successfully saved to: {output_file}")
            return True

        except NoTranscriptFound:
             logging.warning(f"No English transcripts (manual or auto-generated) available for {video_url}.")
             return False # No transcript found in desired language
        except Exception as e:
            logging.error(f"An error occurred while fetching/processing transcript for {video_url}: {e}", exc_info=True) # Keep exc_info=True for traceback
            return False # Indicate failure

    except Exception as e:
        # Catch any potential errors from get_video_id or initial steps
        logging.error(f"An unexpected error occurred during transcript download for {video_url}: {e}")
        return False

def get_transcript(url, output_folder):
    """Reads a saved transcript file."""
    video_id = get_video_id(url)
    if not video_id:
         logging.error(f"Could not extract video ID to get transcript file for: {url}")
         return "NA"

    output_file = os.path.join(output_folder, f"{video_id}.txt")

    if not os.path.exists(output_file):
        logging.warning(f"Transcript file not found for {url}: {output_file}")
        return "NA"

    try:
        with open(output_file, "r", encoding="utf-8") as file:
            file_contents = file.read()
        logging.info(f"Successfully read transcript from file for {url}.")
        return file_contents
    except Exception as e:
        logging.error(f"Error reading transcript file {output_file} for {url}: {e}")
        return "NA"
    