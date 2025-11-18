# Peace Research: AI Model Validation Framework

A comprehensive framework for validating AI models against human-coded gold standard scores across 5 dimensions of peace journalism.

## 🎯 Overview

This repository contains tools for:
- **Extracting and cleaning human-coded scores** from Excel gold standard files
- **Running 6 different AI models** (4 LLM + 2 RoBERTa) on video transcripts
- **Comparing model outputs** against human gold standard with statistical analysis
- **Generating publication-ready reports** for team meetings and papers

## 📊 Five Dimensions Evaluated

1. **News vs. Opinion** - Fact-based reporting (4-5) vs. Subjective analysis (1-2)
2. **Nuance vs. Oversimplification** - Multi-perspective (4-5) vs. Binary/simplistic (1-2)
3. **Creativity vs. Order** - Innovation/human-centered (4-5) vs. Control/authority (1-2)
4. **Prevention vs. Promotion** - Growth/aspiration (4-5) vs. Safety/security (1-2)
5. **Compassion vs. Contempt** - Inclusive/respectful (4-5) vs. Dehumanizing/divisive (1-2)

## 🤖 Models Evaluated

### LLM Models (All 5 Dimensions)
1. **OpenAI GPT-4o (No Context)** - Pure LLM reasoning
2. **OpenAI GPT-4o (With RoBERTa)** - LLM enhanced with emotion scores
3. **Google Gemini 2.5 Flash (No Context)** - Pure LLM reasoning
4. **Google Gemini 2.5 Flash (With RoBERTa)** - LLM enhanced with emotion scores

### RoBERTa Models (Compassion/Contempt Only)
5. **RoBERTa Plain** - Emotion-based scoring (respect vs. contempt)
6. **RoBERTa Valence** - Weighted valence scoring (1-5 scale)

## 🚀 Quick Start

### 1. Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables (.env file)
OPENAI_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
```

### 2. Extract Human Scores from Gold Standard

```bash
python validate_against_human.py
```

This will:
- Load `gold_standard.xlsx`
- Extract video IDs from hyperlinks
- Clean and aggregate human scores
- Generate validation reports in `validation_results/`

### 3. Run Models on Gold Standard Videos

```bash
python run_models_on_gold_standard.py
```

This will:
- Load videos from `validation_results/human_scores_cleaned.csv`
- Fetch transcripts (from `transcripts/Transcripts.docx` or via yt-dlp)
- Run all 6 models on each video
- Save results to `model_scores_gold_standard/`

**Note:** This may take a while due to API rate limiting (1.5s delay between calls).

### 4. Compare Models to Human Scores

```bash
python compare_models_to_human.py
```

This will:
- Calculate correlations (Pearson, Spearman)
- Compute error metrics (MAE, RMSE)
- Generate scatter plots and heatmaps
- Save comparison results to `model_comparison_results/`

### 5. Generate Team Report

```bash
python generate_team_report.py
```

This will:
- Compile all results into a comprehensive report
- Create publication-ready tables
- Generate HTML and Markdown outputs
- Save to `team_report/`

## 📁 Project Structure

```
.
├── gold_standard.xlsx              # Human-coded scores (input)
├── transcripts/
│   └── Transcripts.docx            # Video transcripts (optional)
├── validation_results/              # Human score extraction outputs
│   ├── human_scores_cleaned.csv
│   ├── human_metrics_summary.csv
│   └── ...
├── model_scores_gold_standard/     # Model scoring outputs
│   ├── model_scores_YYYYMMDD.csv
│   └── model_scores_detailed_YYYYMMDD.json
├── model_comparison_results/        # Comparison analysis
│   ├── model_vs_human_metrics_YYYYMMDD.csv
│   ├── comparison_summary_YYYYMMDD.json
│   └── plots/
└── team_report/                     # Final reports
    ├── team_report_YYYYMMDD.md
    └── team_report_YYYYMMDD.html
```

## 📊 Output Files

### Human Score Extraction
- `human_scores_cleaned.csv` - Aggregated human scores (gold standard, 52 videos)
- `human_metrics_summary.csv` - Summary statistics per dimension
- `inter_rater_reliability.csv` - Agreement between evaluators (excellent: r=0.727-0.947)
- `human_dimensions_correlation.csv` - Correlation matrix between dimensions
- `missing_data_report.csv` - Missing data analysis (9.6%-38.5% per dimension)

### Model Scores
- `model_scores_gold_standard/run_1/model_scores_YYYYMMDD.csv` - All model scores (49 videos, all 5 dimensions)
- `model_scores_gold_standard/run_1/model_scores_detailed_YYYYMMDD.json` - Detailed results with rationales

### Comparison Results
- `model_comparison_results/model_vs_human_metrics_YYYYMMDD.csv` - Statistical metrics (22 comparisons)
- `model_comparison_results/comparison_summary_YYYYMMDD.json` - Best methods per dimension
- `model_comparison_results/plots/` - Scatter plots for all method-dimension combinations
- `model_comparison_results/plots/heatmaps/` - Correlation heatmaps per dimension

### Team Report
- `team_report/team_report_20251117_204008.md` - ⭐ **Complete report (use this one)**
- `team_report/summary_stats_20251117_204008.json` - Summary statistics

### Comprehensive Documentation
- `COMPREHENSIVE_RESULTS_REPORT.md` - ⭐ **Publication-ready comprehensive report**
- `PROJECT_SUMMARY.md` - Project overview and status
- `IMPLEMENTATION_NOTES.md` - Lessons learned and improvements

## 🔧 Key Scripts

| Script | Purpose |
|--------|---------|
| `validate_against_human.py` | Extract and clean human scores from Excel |
| `run_models_on_gold_standard.py` | Run all 6 models on gold standard videos |
| `compare_models_to_human.py` | Statistical comparison and visualization |
| `generate_team_report.py` | Generate publication-ready reports |
| `llm_analyzer.py` | LLM API integration (OpenAI + Gemini) |
| `parse_transcripts_docx.py` | Extract transcripts from Word document |

## 📈 Evaluation Metrics

- **Pearson Correlation (r)**: Linear relationship strength
- **Spearman Correlation (ρ)**: Monotonic relationship strength  
- **Mean Absolute Error (MAE)**: Average prediction error
- **Root Mean Squared Error (RMSE)**: Penalizes larger errors

## 🏆 Key Results

**Best Overall Model:** Google Gemini 2.5 Flash (No Context)
- **Average Correlation:** r = 0.682 across all 5 dimensions
- **Strong Correlations (r > 0.7):** 4 out of 5 dimensions
- **Best Dimension:** Prevention/Promotion (r = 0.773)

**Human Inter-Rater Reliability:** Excellent agreement (r = 0.727-0.947)

**Total Analysis:**
- 52 videos in gold standard
- 49 videos with complete model scores
- 22 model comparisons (4 LLM × 5 dimensions + 2 RoBERTa × 1 dimension)

For detailed results, see: **`COMPREHENSIVE_RESULTS_REPORT.md`**

## 🎓 Research Use Cases

- **Model Validation**: Compare AI models against human coders
- **Method Selection**: Choose optimal model based on accuracy/cost tradeoffs
- **Inter-Rater Reliability**: Analyze agreement between human evaluators
- **Publication**: Generate tables and figures for papers

## 📝 Notes

- All scores are normalized to **1-5 scale** for comparison
- Rate limiting (1.5s delay) prevents API throttling
- Transcripts are fetched from `transcripts/history/` → `.docx` → skip yt-dlp
- Missing data handled with pairwise deletion (N varies by dimension: 29-47)
- MLflow tracking enabled for experiment reproducibility
- Run-specific folders (`run_1/`, `run_2/`) for easy comparison

## 🔗 Related Documentation

- **`COMPREHENSIVE_RESULTS_REPORT.md`** - ⭐ **Start here for complete results and insights**
- **`PROJECT_SUMMARY.md`** - Project overview and current status
- **`IMPLEMENTATION_NOTES.md`** - Lessons learned and technical improvements
- **`MLFLOW_TRACKING_GUIDE.md`** - MLflow experiment tracking guide
- See individual script docstrings for detailed function documentation
- Check `validation_results/data_quality_notes.json` for data quality issues
- Review `model_comparison_results/` for detailed analysis outputs

## 📧 Contact

For questions or issues, please refer to the research team.

---

**Last Updated:** November 2024
