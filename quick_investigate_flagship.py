"""
Quick investigation script for flagship results - no pandas required for basic checks.
"""

import json
import os
from pathlib import Path

def quick_investigation():
    """Quick investigation without pandas."""
    
    print(f"\n{'='*80}")
    print(f"QUICK FLAGSHIP RESULTS INVESTIGATION")
    print(f"{'='*80}\n")
    
    # Find latest files
    flagship_dir = "model_scores_gold_standard/flagship_run"
    
    csv_files = sorted([f for f in os.listdir(flagship_dir) if f.startswith("flagship_scores_") and f.endswith(".csv")])
    json_files = sorted([f for f in os.listdir(flagship_dir) if f.startswith("flagship_scores_detailed_") and f.endswith(".json")])
    
    if not csv_files:
        print("[ERROR] No flagship CSV files found!")
        return
    
    latest_csv = csv_files[-1]
    latest_json = json_files[-1] if json_files else None
    
    print(f"[FILE] Latest CSV: {latest_csv}")
    if latest_json:
        print(f"[FILE] Latest JSON: {latest_json}")
    
    # Read CSV header and count lines
    csv_path = os.path.join(flagship_dir, latest_csv)
    with open(csv_path, 'r', encoding='utf-8') as f:
        header = f.readline().strip()
        lines = f.readlines()
    
    print(f"\n[CSV] Summary:")
    print(f"   Total videos: {len(lines)}")
    print(f"   Columns: {len(header.split(','))}")
    print(f"   Header: {header[:100]}...")
    
    # Read JSON if available
    if latest_json:
        json_path = os.path.join(flagship_dir, latest_json)
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"\n[JSON] Summary:")
        print(f"   Total videos: {len(data)}")
        
        if len(data) > 0:
            first_video = data[0]
            print(f"\n   Sample video (first):")
            print(f"      Video ID: {first_video.get('video_id', 'N/A')}")
            print(f"      Methods: {list(first_video.get('methods', {}).keys())}")
            
            # Check OpenAI flagship
            if 'openai_flagship' in first_video.get('methods', {}):
                scores = first_video['methods']['openai_flagship'].get('scores', {})
                print(f"      OpenAI Flagship scores: {scores}")
            
            # Check Gemini flagship
            if 'gemini_flagship' in first_video.get('methods', {}):
                scores = first_video['methods']['gemini_flagship'].get('scores', {})
                print(f"      Gemini Flagship scores: {scores}")
    
    # Check missing transcripts
    missing_files = [f for f in os.listdir(flagship_dir) if f.startswith("missing_transcripts_")]
    if missing_files:
        latest_missing = sorted(missing_files)[-1]
        missing_path = os.path.join(flagship_dir, latest_missing)
        with open(missing_path, 'r') as f:
            missing = f.read().strip().split('\n')
        print(f"\n[WARNING] Missing Transcripts: {len(missing)} videos")
        if len(missing) <= 10:
            print(f"   IDs: {', '.join(missing)}")
        else:
            print(f"   First 10 IDs: {', '.join(missing[:10])}...")
    
    print(f"\n{'='*80}")
    print(f"NEXT STEPS:")
    print(f"{'='*80}")
    print(f"1. Open CSV in Excel: {csv_path}")
    print(f"2. View MLflow: Run 'mlflow ui' and check 'Flagship Models Validation'")
    print(f"3. Compare to human: Run 'python compare_models_to_human.py'")
    print(f"4. Read detailed JSON: {json_path if latest_json else 'N/A'}")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    quick_investigation()

