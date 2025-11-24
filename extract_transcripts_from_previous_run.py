"""
Extract transcripts from previous successful run JSON files and save them to transcripts/history/
This ensures we can reuse transcripts without calling yt-dlp again.
"""

import json
import os
from pathlib import Path
import glob

def extract_and_save_transcripts(json_path: str, output_dir: str = "transcripts/history"):
    """Extract transcripts from previous run JSON and save to transcripts/history/"""
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n{'='*80}")
    print(f"Extracting transcripts from: {json_path}")
    print(f"{'='*80}")
    
    if not os.path.exists(json_path):
        print(f"[WARNING] File not found: {json_path}")
        return 0
    
    with open(json_path, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    saved_count = 0
    skipped_count = 0
    
    for video_result in results:
        video_id = video_result.get('video_id')
        youtube_id = video_result.get('youtube_id')
        
        # Try to get transcript from roberta_valence raw_result
        transcript = None
        methods = video_result.get('methods', {})
        roberta_valence = methods.get('roberta_valence', {})
        raw_result = roberta_valence.get('raw_result', {})
        if 'transcript' in raw_result:
            transcript = raw_result['transcript']
        
        if not transcript or len(transcript) < 50:
            skipped_count += 1
            continue
        
        # Determine which ID to use for filename
        # Priority: youtube_id > video_id
        save_id = None
        if youtube_id and youtube_id != 'nan' and str(youtube_id).strip():
            save_id = str(youtube_id).strip()
        elif video_id:
            save_id = str(video_id).strip()
        
        if not save_id:
            skipped_count += 1
            continue
        
        # Save transcript
        output_file = os.path.join(output_dir, f"{save_id}.txt")
        
        # Check if file already exists (don't overwrite)
        if os.path.exists(output_file):
            print(f"  [SKIP] Skipping {save_id} (already exists)")
            skipped_count += 1
            continue
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(transcript)
            saved_count += 1
            print(f"  [OK] Saved transcript for {save_id} ({len(transcript)} chars)")
        except Exception as e:
            print(f"  [ERROR] Error saving {save_id}: {e}")
            skipped_count += 1
    
    print(f"\n{'='*80}")
    print(f"[SUCCESS] Saved {saved_count} transcripts to {output_dir}/")
    if skipped_count > 0:
        print(f"[INFO] Skipped {skipped_count} videos (no transcript or already exists)")
    print(f"{'='*80}\n")
    
    return saved_count

if __name__ == "__main__":
    total_saved = 0
    
    # Extract from run_1
    json_path_1 = "model_scores_gold_standard/run_1/model_scores_detailed_20251117_184222.json"
    if os.path.exists(json_path_1):
        total_saved += extract_and_save_transcripts(json_path_1)
    
    # Also try run_2 if it exists
    json_path_2 = "model_scores_gold_standard/run_2/model_scores_detailed_20251118_101719.json"
    if os.path.exists(json_path_2):
        total_saved += extract_and_save_transcripts(json_path_2)
    
    # Check for any other JSON files in run directories
    for run_dir in glob.glob("model_scores_gold_standard/run_*/"):
        json_files = glob.glob(os.path.join(run_dir, "model_scores_detailed_*.json"))
        for json_file in json_files:
            if json_file not in [json_path_1, json_path_2]:
                total_saved += extract_and_save_transcripts(json_file)
    
    print(f"\n[SUCCESS] Total transcripts extracted: {total_saved}")
    print(f"[INFO] Transcripts saved to: transcripts/history/")
    print(f"\n[READY] Ready for future runs! The script will now find these transcripts automatically.")

