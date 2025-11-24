"""Verify that extracted transcripts match CSV video IDs."""

import os
import csv

# Read CSV video IDs
csv_ids = set()
with open('validation_results/human_scores_cleaned.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        vid = row['video_id'].strip()
        yid = row.get('youtube_id', '').strip()
        if vid and vid != '#NAME?':
            csv_ids.add(vid)
        if yid and yid != '#NAME?' and yid != 'nan':
            csv_ids.add(yid)

# Get history files
history_files = {f.replace('.txt', '') for f in os.listdir('transcripts/history') if f.endswith('.txt')}

# Check matches
matches = csv_ids & history_files
missing = csv_ids - history_files

print(f"{'='*80}")
print(f"TRANSCRIPT MAPPING VERIFICATION")
print(f"{'='*80}")
print(f"CSV video IDs: {len(csv_ids)}")
print(f"Transcript files in history/: {len(history_files)}")
print(f"Matches: {len(matches)}")
print(f"Missing: {len(missing)}")
print(f"\nMatch rate: {len(matches)/len(csv_ids)*100:.1f}%")

if missing:
    print(f"\nMissing IDs (first 10):")
    for vid in list(missing)[:10]:
        print(f"  - {vid}")

if matches:
    print(f"\nSample matches (first 5):")
    for vid in list(matches)[:5]:
        print(f"  + {vid}")

print(f"\n{'='*80}")
if len(matches) >= len(csv_ids) * 0.9:
    print("[SUCCESS] Mapping looks good! Most transcripts are available.")
else:
    print("[WARNING] Some transcripts are missing. Check previous run JSON files.")
print(f"{'='*80}")

