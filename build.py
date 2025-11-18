import yt_dlp
import pandas as pd
import logging
import json
import os
import time
from datetime import datetime

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# A diverse list of channels categorized by their content type.
CHANNELS_TO_SCRAPE = {
    "Political Commentary (Left)": ["https://www.youtube.com/@TheDailyShow", "https://www.youtube.com/@LastWeekTonight"],
    "Political Commentary (Right)": ["https://www.youtube.com/@DailyWirePlus", "https://www.youtube.com/@MattWalsh"],
    "News & Journalism": ["https://www.youtube.com/@Reuters", "https://www.youtube.com/@johnnyharris", "https://www.youtube.com/@Wendoverproductions", "https://www.youtube.com/@Vox"],
    "Educational": ["https://www.youtube.com/@kurzgesagt", "https://www.youtube.com/@Veritasium", "https://www.youtube.com/@SmarterEveryDay", "https://www.youtube.com/@CrashCourse"],
    "Tech & Business": ["https://www.youtube.com/@MKBHD", "https://www.youtube.com/@CNBCTelevision"],
    "Science & Nature": ["https://www.youtube.com/@nasa", "https://www.youtube.com/@NatGeo"],
    "Documentary": ["https://www.youtube.com/@VICE"]
}

VIDEOS_TO_SELECT_PER_CHANNEL = 10
POOL_SIZE_PER_CHANNEL = 50
MIN_VIDEO_DURATION_SECONDS = 120
MAX_VIDEO_DURATION_SECONDS = 1800
MIN_VIEWS = 50000
SORT_VIDEOS_BY = 'view_count'
OUTPUT_CSV_PATH = "transcript_corpus_v2.csv"

def fetch_transcript(video_url: str) -> str | None:
    video_id = video_url.split("v=")[-1]
    temp_filename_base = f'subtitles_temp_{video_id}'
    
    ydl_opts = {
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en-US', 'en'],
        'subtitlesformat': 'json3',
        'skip_download': True,
        'quiet': True,
        'outtmpl': temp_filename_base,
        'format': 'bestaudio/best',
        'noplaylist': True,
        'ignore_errors': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        subtitle_data = None
        for lang_code in ['en-US', 'en']:
            json3_path = f'{temp_filename_base}.{lang_code}.json3'
            if os.path.exists(json3_path):
                with open(json3_path, 'r', encoding='utf-8') as f:
                    subtitle_data = json.load(f)
                break
        
        if not subtitle_data:
            logging.warning(f"No usable JSON3 English subtitle file found for {video_url}.")
            return None

        transcript = " ".join([event['segs'][0]['utf8'] for event in subtitle_data.get('events', []) if 'segs' in event and event['segs']])
        return transcript.replace('\n', ' ').strip()
    except Exception as e:
        logging.warning(f"Could not process transcript for {video_url}: {e}")
        return None
    finally:
        for lang_code in ['en-US', 'en']:
            for ext in ['.json3', '.vtt']:
                filepath_to_clean = f'{temp_filename_base}.{lang_code}{ext}'
                if os.path.exists(filepath_to_clean):
                    os.remove(filepath_to_clean)


def build_corpus():
    processed_channels = set()
    all_videos_data = []
    if os.path.exists(OUTPUT_CSV_PATH):
        logging.info(f"Resuming from existing file: '{OUTPUT_CSV_PATH}'")
        df_existing = pd.read_csv(OUTPUT_CSV_PATH)
        processed_channels = set(df_existing['channel'].unique())
        all_videos_data = df_existing.to_dict('records')
        logging.info(f"Already processed {len(processed_channels)} channels.")

    with yt_dlp.YoutubeDL({'quiet': True, 'ignore_errors': True}) as ydl:
        for category, channel_urls in CHANNELS_TO_SCRAPE.items():
            for channel_url in channel_urls:
                try:
                    channel_meta = ydl.extract_info(channel_url, download=False, process=False)
                    channel_name = channel_meta.get('uploader')
                    if channel_name in processed_channels:
                        logging.info(f"Channel '{channel_name}' already processed. Skipping.")
                        continue
                    
                    logging.info(f"Processing Channel: {channel_url} (Name: {channel_name})")
                    # STAGE 1: Get a flat list of video entries (lightweight)
                    playlist_dict = ydl.extract_info(f"{channel_url}/videos", download=False, extra_info={'playlistend': POOL_SIZE_PER_CHANNEL}, process=False)
                    
                    if not playlist_dict or 'entries' not in playlist_dict:
                        logging.warning(f"  - No video entries found for {channel_url}. Skipping.")
                        continue
                    
                    # STAGE 2: Process each video individually to isolate errors
                    filtered_pool = []
                    for video_entry in playlist_dict['entries']:
                        try:
                            video_id = video_entry.get('id')
                            video_url = f"https://www.youtube.com/watch?v={video_id}"
                            
                            # Get detailed metadata for this single video
                            video_meta = ydl.extract_info(video_url, download=False)

                            title, duration, view_count, live_status = video_meta.get('title'), video_meta.get('duration'), video_meta.get('view_count'), video_meta.get('live_status')
                            
                            if live_status in ['is_live', 'is_upcoming']: continue
                            if not (duration and MIN_VIDEO_DURATION_SECONDS <= duration <= MAX_VIDEO_DURATION_SECONDS): continue
                            if not (view_count and view_count >= MIN_VIEWS): continue
                            
                            filtered_pool.append(video_meta)
                        except Exception as e:
                            logging.warning(f"  - Skipping video {video_entry.get('id')} due to metadata fetch error: {e}")
                            continue

                    filtered_pool.sort(key=lambda x: x.get(SORT_VIDEOS_BY, 0), reverse=True)
                    selected_videos = filtered_pool[:VIDEOS_TO_SELECT_PER_CHANNEL]
                    logging.info(f"  - Filtered to {len(selected_videos)} videos to process.")

                    for video_meta in selected_videos:
                        video_id = video_meta.get('id')
                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                        logging.info(f"  - SELECTING '{video_meta.get('title')}'")
                        transcript = fetch_transcript(video_url)
                        
                        if transcript:
                            all_videos_data.append({
                                "video_id": video_id, "title": video_meta.get('title'), "channel": video_meta.get('channel'),
                                "category": category, "upload_date": video_meta.get('upload_date'),
                                "duration_seconds": video_meta.get('duration'), "view_count": video_meta.get('view_count'),
                                "like_count": video_meta.get('like_count'), "full_transcript": transcript
                            })
                        else:
                            logging.warning(f"  - SKIPPED video due to missing transcript.")
                except Exception as e:
                    logging.error(f"  - FATAL error processing channel {channel_url}. Skipping. Error: {e}")
                
                time.sleep(2)

    df = pd.DataFrame(all_videos_data)
    df.to_csv(OUTPUT_CSV_PATH, index=False, encoding='utf-8')
    logging.info("="*50 + "\nCorpus Building Complete!")
    print(df.groupby('category')['video_id'].count())
    logging.info("="*50)

if __name__ == "__main__":
    build_corpus()

