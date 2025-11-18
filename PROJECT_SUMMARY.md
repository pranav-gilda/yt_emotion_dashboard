# Project Summary: AI Model Validation for Peace Research

**Last Updated:** November 18, 2024  
**Status:** ✅ Complete - All 5 Dimensions Analyzed and Validated

---

## 🎯 Project Goal

Validate AI models against human-coded gold standard scores across 5 dimensions of peace journalism to determine which models best replicate human judgment.

---

## ✅ Current Status: COMPLETE

### Completed ✅
- ✅ Human score extraction from Excel gold standard (52 videos, 3 evaluators)
- ✅ Video ID extraction from hyperlinks (robust matching)
- ✅ Transcript fetching (Word doc + history folder, yt-dlp disabled)
- ✅ 6 model implementations (4 LLM + 2 RoBERTa)
- ✅ Score normalization to 1-5 scale (consistent across all models)
- ✅ Statistical comparison framework (correlations, MAE, RMSE)
- ✅ Visualization generation (scatter plots, heatmaps)
- ✅ Team report generation (publication-ready)
- ✅ MLflow tracking (experiment tracking and reproducibility)
- ✅ Inter-rater reliability analysis (human vs. human agreement)

### Results Summary
- **Total Videos in Gold Standard:** 52
- **Videos with Transcripts:** 49
- **Total Model Comparisons:** 22 (4 LLM × 5 dimensions + 2 RoBERTa × 1 dimension)
- **Best Overall Model:** Google Gemini 2.5 Flash (No Context)
- **Strongest Correlation:** 0.773 (Prevention vs. Promotion)
- **Average Correlation:** 0.516 (SD: 0.193)
- **Human Inter-Rater Reliability:** 0.727-0.947 (excellent agreement)

---

## 📊 Key Findings

### Best Models by Dimension

| Dimension | Best Model | Pearson r | MAE | N | Interpretation |
|-----------|------------|-----------|-----|---|----------------|
| **Prevention vs. Promotion** | Gemini (No Context) | **0.773** | 0.775 | 34 | Excellent correlation |
| **Creativity vs. Order** | Gemini (No Context) | **0.751** | 0.933 | 30 | Strong correlation |
| **Compassion vs. Contempt** | Gemini (No Context) | **0.722** | 0.670 | 45 | Strong correlation |
| **News vs. Opinion** | Gemini (No Context) | **0.716** | 0.703 | 32 | Strong correlation |
| **Nuance vs. Oversimplification** | Gemini (No Context) | **0.449** | 1.145 | 35 | Moderate correlation |

**Critical Finding:** **Gemini (No Context) is the best model for ALL 5 dimensions.**

### Human Inter-Rater Reliability

**Excellent Agreement Validates Gold Standard Quality:**

| Dimension | Avg. Correlation | Agreement Within 1pt |
|-----------|------------------|---------------------|
| News/Opinion | **0.947** | 100% |
| Compassion/Contempt | **0.940** | 100% |
| Order/Creativity | **0.935** | 100% |
| Nuance | **0.879** | 94.4% |
| Prevention/Promotion | **0.727** | 93.3% |

### Missing Data Analysis

| Dimension | Available | Missing | Missing % |
|-----------|-----------|---------|-----------|
| Compassion/Contempt | 47 | 5 | 9.6% |
| Nuance | 37 | 15 | 28.9% |
| Order/Creativity | 32 | 20 | 38.5% |
| Prevention/Promotion | 35 | 17 | 32.7% |
| News/Opinion | 34 | 18 | 34.6% |

**Handling:** Pairwise deletion (exclude missing from analysis)

---

## 🔧 Technical Details

### Models Implemented
1. **OpenAI GPT-4o** (with/without RoBERTa context)
2. **Google Gemini 2.5 Flash** (with/without RoBERTa context) ⭐ **BEST**
3. **RoBERTa Plain** (emotion-based)
4. **RoBERTa Valence** (weighted scoring)

### Data Pipeline
1. Extract human scores from `gold_standard.xlsx`
2. Extract YouTube IDs from Excel hyperlinks
3. Fetch transcripts from `transcripts/Transcripts.docx` or `transcripts/history/`
4. Run all 6 models on each video transcript
5. Normalize scores to 1-5 scale
6. Compare against human gold standard
7. Generate statistical reports and visualizations
8. Track in MLflow for reproducibility

### Key Files
- `validate_against_human.py` - Human score extraction and validation
- `run_models_on_gold_standard.py` - Model execution (with MLflow tracking)
- `compare_models_to_human.py` - Statistical comparison
- `generate_team_report.py` - Report generation
- `llm_analyzer.py` - LLM API integration (OpenAI + Gemini)
- `compare_runs_consistency.py` - Run consistency analysis

---

## 📁 Output Locations

- **Human Scores:** `validation_results/human_scores_cleaned.csv`
- **Model Scores:** `model_scores_gold_standard/run_1/model_scores_*.csv`
- **Comparisons:** `model_comparison_results/model_vs_human_metrics_*.csv`
- **Reports:** `team_report/team_report_20251117_204008.md` ⭐ **USE THIS ONE**
- **Visualizations:** `model_comparison_results/plots/` and `plots/heatmaps/`

---

## 🔍 Key Insights

### 1. Gemini Outperforms OpenAI
- **Average advantage:** r = +0.232 across all dimensions
- **Cost-effective:** Lower API costs
- **Simpler:** Works best without RoBERTa context

### 2. RoBERTa Context Not Beneficial
- Gemini: r = 0.682 (no context) vs. 0.645 (with context)
- OpenAI: r = 0.450 (no context) vs. 0.420 (with context)
- **Implication:** Simple prompts more effective

### 3. Strong Performance for 4/5 Dimensions
- Prevention/Promotion: r = 0.773
- Creativity/Order: r = 0.751
- Compassion/Contempt: r = 0.722
- News/Opinion: r = 0.716
- Nuance: r = 0.449 (most challenging)

### 4. Human Agreement Validates Gold Standard
- Inter-rater correlations: 0.727-0.947
- 100% agreement within 1 point for 3 dimensions
- High-quality gold standard for validation

---

## 🚀 Next Steps

1. ✅ All 5 dimensions analyzed and validated
2. ✅ Column mapping fixed (contempt_compassion_score ↔ compassion_contempt)
3. ✅ Comprehensive reports generated
4. ✅ MLflow tracking implemented
5. 📄 Prepare publication tables (see `COMPREHENSIVE_RESULTS_REPORT.md`)
6. 📊 Create presentation slides from results
7. 📖 Write methodology section for paper
8. 🔄 Run 2 for consistency check (optional)

---

## 📝 Important Notes

- **All scores normalized to 1-5 scale** for consistency
- **Rate limiting (1.5s)** prevents API throttling
- **Missing transcripts handled gracefully** (3 videos excluded)
- **Column name mapping:** `contempt_compassion_score` (human) ↔ `compassion_contempt` (model)
- **Transcript sources:** Priority: history folder → .docx → skip yt-dlp
- **MLflow tracking:** All runs logged for reproducibility

---

## 📚 Documentation

- **Comprehensive Report:** `COMPREHENSIVE_RESULTS_REPORT.md` ⭐ **START HERE**
- **Quick Start:** `README.md`
- **MLflow Guide:** `MLFLOW_TRACKING_GUIDE.md`
- **Team Report:** `team_report/team_report_20251117_204008.md`

---

**For detailed methodology and full results, see:** `COMPREHENSIVE_RESULTS_REPORT.md`
