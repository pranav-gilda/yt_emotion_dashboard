import os
import logging
from youtube_transcript_api._api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from youtube_transcript_api._errors import NoTranscriptFound, RequestBlocked
from utils import get_video_id, create_directory

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def download_transcript(video_url, output_folder):
    """Downloads and saves the transcript of a YouTube video."""
    try:
        logging.info(f"Attempting to fetch transcript for: {video_url}")

        video_id = get_video_id(video_url)
        if not video_id:
            logging.error(f"Failed to extract video ID from: {video_url}")
            return False

        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)

            logging.info(f"Received transcript_list for {video_id} with {len(transcript_list)} entries.")

            if not transcript_list:
                logging.warning(f"Received empty transcript list for {video_url}.")
                return False

            logging.info(f"Successfully fetched transcript data for {video_url}. Proceeding to format manually.")

            formatted_transcript = " ".join([entry['text'] for entry in transcript_list])

            logging.info(f"Successfully formatted transcript manually for {video_url}.")

            create_directory(output_folder)

            output_file = os.path.join(output_folder, f"{video_id}.txt")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(formatted_transcript)

            logging.info(f"Transcript successfully saved to: {output_file}")
            return True

        except NoTranscriptFound:
            logging.warning(f"No English transcripts (manual or auto-generated) available for {video_url}.")
            return False
        except RequestBlocked as e:
            # This will catch the specific error confirming an IP block.
            logging.error(f"Request was blocked by YouTube for video {video_url}. This might be a persistent IP block. Error: {e}")
            return False
        except Exception as e:
            logging.error(f"An error occurred while fetching/processing transcript for {video_url}: {e}", exc_info=True)
            return False

    except Exception as e:
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
