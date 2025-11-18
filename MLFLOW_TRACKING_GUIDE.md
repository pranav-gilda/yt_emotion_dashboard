# MLflow Tracking Guide

## Overview

All model runs are now tracked in MLflow for easy comparison, reproducibility, and analysis.

## Quick Start

### Run 2 (Compassion/Contempt Only)

```bash
# Run second pass (will analyze all 5 dimensions but you can focus on compassion_contempt)
python run_models_on_gold_standard.py --run-number 2
```

This will:
- ✅ Skip yt-dlp (uses `transcripts/history/` first, then `.docx`)
- ✅ Cache transcripts to avoid re-reading
- ✅ Track everything in MLflow
- ✅ Save to `model_scores_gold_standard/run_2/`
- ✅ Capture top 3 emotions from RoBERTa
- ✅ Include transcript metadata (length, word count, sentence count)

### Compare Run Consistency

After run 2 completes, compare consistency for compassion_contempt:

```bash
python compare_runs_consistency.py
```

This will:
- Compare run 1 vs run 2 for compassion_contempt dimension
- Calculate Pearson correlation, MAE, exact agreement
- Save results to `run_consistency_analysis/`
- Track in MLflow

### View MLflow Results

```bash
mlflow ui
```

Then open http://localhost:5000 in your browser to see:
- All runs with parameters and metrics
- Artifacts (CSV files, JSON results)
- Comparison between runs
- Experiment tracking

## What's Tracked in MLflow

### Parameters
- `run_number`: Which run (1, 2, etc.)
- `total_videos`: Number of videos processed
- `docx_transcripts_count`: Transcripts found in .docx
- `timestamp`: When the run was executed

### Metrics
- `videos_processed`: Successfully processed videos
- `videos_missing_transcripts`: Videos without transcripts
- `avg_transcript_length`: Average transcript length
- `avg_word_count`: Average word count
- `{method}_success_rate`: Success rate per method

### Artifacts
- `model_scores/`: CSV file with all scores
- `detailed_results/`: JSON with full results including top emotions

## File Structure

```
model_scores_gold_standard/
├── run_1/                    # First run (4 dimensions)
│   ├── model_scores_*.csv
│   ├── model_scores_detailed_*.json
│   └── missing_transcripts_*.txt
└── run_2/                    # Second run (compassion_contempt focus)
    ├── model_scores_*.csv
    ├── model_scores_detailed_*.json
    └── missing_transcripts_*.txt

run_consistency_analysis/
├── run_consistency_*.csv     # Detailed consistency metrics
└── consistency_summary_*.json # Summary statistics
```

## Key Features

### 1. Transcript Optimization
- **Priority 1:** `transcripts/history/{youtube_id}.txt` (fastest, no API)
- **Priority 2:** `transcripts/Transcripts.docx` (parsed)
- **Priority 3:** Skip yt-dlp (to avoid hitting YouTube servers)
- **Caching:** Transcripts are cached in memory to avoid re-reading

### 2. Top 3 Emotions
RoBERTa methods now capture top 3 emotions:
```json
{
  "top_3_emotions": [
    {"emotion": "admiration", "score": 0.1234},
    {"emotion": "caring", "score": 0.0987},
    {"emotion": "disgust", "score": 0.0765}
  ]
}
```

### 3. Transcript Metadata
Each video now includes:
- `transcript_length`: Character count
- `transcript_word_count`: Word count
- `transcript_sentence_count`: Sentence count

### 4. Run-Specific Folders
Each run saves to its own folder for easy comparison:
- `run_1/`: First run
- `run_2/`: Second run
- Future runs: `run_3/`, `run_4/`, etc.

## Consistency Analysis

The consistency script compares:
- **Pearson correlation** between runs
- **MAE and RMSE** (error metrics)
- **Exact agreement** percentage
- **Agreement within 0.5** and **within 1.0**

Results help identify:
- Which models are most stable
- Which models have high variance between runs
- Overall reliability of predictions

## Next Steps

1. **Run 2:** Execute `python run_models_on_gold_standard.py --run-number 2`
2. **Compare:** Run `python compare_runs_consistency.py`
3. **Analyze:** Use MLflow UI to explore results
4. **Report:** Generate final report with all 5 dimensions complete

---

**Note:** All runs are tracked in MLflow experiment: `Gold Standard Model Validation`

