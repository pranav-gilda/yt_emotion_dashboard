# 🔍 How to Investigate Flagship Model Results

## 📁 Files Generated

Your flagship run created these files in `model_scores_gold_standard/flagship_run/`:

- **`flagship_scores_20251123_162450.csv`** - All scores in tabular format
- **`flagship_scores_detailed_20251123_162450.json`** - Detailed results with rationales
- **`missing_transcripts_20251123_162450.txt`** - List of videos without transcripts

## 🔬 Quick Investigation Methods

### 1. **View CSV in Excel/Spreadsheet**

```bash
# Open the CSV file
model_scores_gold_standard/flagship_run/flagship_scores_20251123_162450.csv
```

**Columns to check:**
- `openai_flagship_*` - All 5 dimensions from GPT-5.1
- `gemini_flagship_*` - All 5 dimensions from Gemini 3 Pro Preview
- `transcript_length`, `transcript_word_count` - Transcript metadata

### 2. **Compare to Human Scores**

Use the existing comparison script (it should work with flagship scores):

```bash
python compare_models_to_human.py
```

This will:
- Load human gold standard from `validation_results/human_scores_cleaned.csv`
- Compare flagship models to human scores
- Calculate correlations, MAE, RMSE
- Generate scatter plots and heatmaps
- Save results to `model_comparison_results/`

**Note:** You may need to update `compare_models_to_human.py` to recognize `openai_flagship_*` and `gemini_flagship_*` columns.

### 3. **View MLflow Results**

```bash
mlflow ui
```

Then:
1. Open http://localhost:5000 in your browser
2. Find experiment: **"Flagship Models Validation"**
3. Click on the latest run
4. View:
   - Parameters (model names, video count)
   - Metrics (success rates, transcript stats)
   - Artifacts (CSV files, JSON files)

### 4. **Read JSON for Detailed Rationales**

The JSON file contains full model responses with rationales:

```python
import json

with open('model_scores_gold_standard/flagship_run/flagship_scores_detailed_20251123_162450.json', 'r') as f:
    results = json.load(f)

# View first video's results
first_video = results[0]
print(f"Video ID: {first_video['video_id']}")
print(f"OpenAI scores: {first_video['methods']['openai_flagship']['scores']}")
print(f"Gemini scores: {first_video['methods']['gemini_flagship']['scores']}")
```

### 5. **Quick Python Analysis** (if pandas available)

```python
import pandas as pd

# Load flagship results
df = pd.read_csv('model_scores_gold_standard/flagship_run/flagship_scores_20251123_162450.csv')

# Basic stats
print("OpenAI Flagship Stats:")
print(df[[c for c in df.columns if c.startswith('openai_flagship_')]].describe())

print("\nGemini Flagship Stats:")
print(df[[c for c in df.columns if c.startswith('gemini_flagship_')]].describe())

# Model agreement
for dim in ['opinion_news', 'nuance', 'order_creativity', 'prevention_promotion', 'compassion_contempt']:
    openai_col = f'openai_flagship_{dim}'
    gemini_col = f'gemini_flagship_{dim}'
    if openai_col in df.columns and gemini_col in df.columns:
        corr = df[openai_col].corr(df[gemini_col])
        print(f"{dim}: r = {corr:.3f}")
```

### 6. **Compare to Previous Runs**

Compare flagship models to your previous runs (run_1, run_2):

```python
import pandas as pd

# Load flagship
flagship = pd.read_csv('model_scores_gold_standard/flagship_run/flagship_scores_20251123_162450.csv')

# Load previous run
prev = pd.read_csv('model_scores_gold_standard/run_1/model_scores_20251117_184222.csv')

# Merge
merged = flagship.merge(prev, on='video_id', how='inner', suffixes=('_flagship', '_prev'))

# Compare OpenAI models
print("OpenAI Flagship vs OpenAI Previous:")
for dim in ['opinion_news', 'nuance', 'order_creativity', 'prevention_promotion', 'compassion_contempt']:
    flagship_col = f'openai_flagship_{dim}'
    prev_col = f'openai_{dim}'
    if flagship_col in merged.columns and prev_col in merged.columns:
        corr = merged[flagship_col].corr(merged[prev_col])
        print(f"  {dim}: r = {corr:.3f}")
```

## 📊 Key Questions to Answer

1. **How do flagship models compare to human scores?**
   - Run `compare_models_to_human.py` (may need updates)
   - Check correlations, MAE, RMSE

2. **Do flagship models agree with each other?**
   - Calculate correlation between OpenAI and Gemini scores
   - Check mean absolute differences

3. **How do flagship models compare to previous runs?**
   - Compare to `run_1` and `run_2` results
   - Are scores consistent? Different?

4. **Which model performs better?**
   - Compare OpenAI vs Gemini correlations with human scores
   - Check which has lower MAE/RMSE

5. **Are there any patterns in disagreements?**
   - Look at videos where models disagree most
   - Check transcript characteristics (length, word count)

## 🛠️ Next Steps

1. **Update `compare_models_to_human.py`** to include flagship models:
   - Add `'openai_flagship'` and `'gemini_flagship'` to method lists
   - Ensure dimension mapping works correctly

2. **Generate visualizations:**
   - Scatter plots: Flagship vs Human
   - Heatmaps: Correlation matrices
   - Comparison plots: Flagship vs Previous runs

3. **Create summary report:**
   - Best performing model per dimension
   - Comparison to previous runs
   - Key insights and recommendations

## 📝 Example Commands

```bash
# View CSV
cat model_scores_gold_standard/flagship_run/flagship_scores_20251123_162450.csv | head -20

# Count videos
wc -l model_scores_gold_standard/flagship_run/flagship_scores_20251123_162450.csv

# Check missing transcripts
cat model_scores_gold_standard/flagship_run/missing_transcripts_20251123_162450.txt

# Start MLflow UI
mlflow ui
```

## 🎯 Quick Wins

1. **Open CSV in Excel** - Quick visual inspection
2. **View MLflow UI** - See all metrics at a glance
3. **Read JSON** - Check model rationales for a few videos
4. **Compare means** - Simple average comparison between models

