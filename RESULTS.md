# Results Summary: AI Model Validation for Peace Research

**Last Updated:** November 18, 2024  
**Status:** ✅ Complete - All 5 Dimensions Analyzed and Validated

---

## 🎯 Project Overview

This project validates AI models against human-coded gold standard scores across 5 dimensions of peace journalism to determine which models best replicate human judgment.

**Best Overall Model:** **Google Gemini 2.5 Flash (No Context)** - Best performing model for ALL 5 dimensions!

---

## ✅ Completed Work

- ✅ Human score extraction from Excel gold standard (52 videos, 3 evaluators)
- ✅ Video ID extraction from hyperlinks (robust matching)
- ✅ Transcript fetching (Word doc + history folder)
- ✅ 6 model implementations (4 LLM + 2 RoBERTa)
- ✅ Score normalization to 1-5 scale (consistent across all models)
- ✅ Statistical comparison framework (correlations, MAE, RMSE)
- ✅ Visualization generation (scatter plots, heatmaps)
- ✅ Team report generation (publication-ready)
- ✅ MLflow tracking (experiment tracking and reproducibility)
- ✅ Inter-rater reliability analysis (human vs. human agreement)

---

## 🏆 Key Findings

### Best Models by Dimension

| Dimension | Best Model | Pearson r | MAE | N | Interpretation |
|-----------|------------|-----------|-----|---|----------------|
| **Prevention vs. Promotion** | Gemini (No Context) | **0.773** | 0.775 | 34 | Excellent correlation |
| **Creativity vs. Order** | Gemini (No Context) | **0.751** | 0.933 | 30 | Strong correlation |
| **Compassion vs. Contempt** | Gemini (No Context) | **0.722** | 0.670 | 45 | Strong correlation |
| **News vs. Opinion** | Gemini (No Context) | **0.716** | 0.703 | 32 | Strong correlation |
| **Nuance vs. Oversimplification** | Gemini (No Context) | **0.449** | 1.145 | 35 | Moderate correlation |

**Critical Finding:** **Gemini (No Context) is the best model for ALL 5 dimensions.**

### Overall Performance Statistics

- **Total Videos in Gold Standard:** 52
- **Videos with Transcripts:** 49
- **Total Model Comparisons:** 22 (4 LLM × 5 dimensions + 2 RoBERTa × 1 dimension)
- **Average Pearson Correlation:** 0.516 (SD: 0.193)
- **Range of Correlations:** 0.126 to 0.773
- **Average MAE:** 0.863 (SD: 0.183)

### Human Inter-Rater Reliability

**Excellent Agreement Validates Gold Standard Quality:**

| Dimension | Avg. Correlation | Agreement Within 1pt |
|-----------|------------------|---------------------|
| News/Opinion | **0.947** | 100% |
| Compassion/Contempt | **0.940** | 100% |
| Order/Creativity | **0.935** | 100% |
| Nuance | **0.879** | 94.4% |
| Prevention/Promotion | **0.727** | 93.3% |

---

## 💡 Key Insights

1. **Gemini Outperforms OpenAI** - Average advantage of r = +0.232 across all dimensions, more cost-effective
2. **RoBERTa Context Not Beneficial** - Simple prompts without RoBERTa context work better
3. **Strong Performance for 4/5 Dimensions** - Strong correlations (r > 0.7) for all dimensions except Nuance
4. **Human Agreement Validates Gold Standard** - Inter-rater correlations of 0.727-0.947 demonstrate high-quality gold standard

---

## 📁 Output Files

### Reports
- `team_report/team_report_*.md` - Detailed team reports
- `COMPREHENSIVE_RESULTS_REPORT.md` - ⭐ **Complete detailed report**

### Data Files
- `validation_results/human_scores_cleaned.csv` - Aggregated human scores
- `model_scores_gold_standard/run_*/model_scores_*.csv` - Model scores
- `model_comparison_results/model_vs_human_metrics_*.csv` - Statistical metrics
- `model_comparison_results/comparison_summary_*.json` - Best methods summary

### Visualizations
- `model_comparison_results/plots/*.png` - Scatter plots and heatmaps

---

## 🎯 Recommendations

**Primary Model:** Google Gemini 2.5 Flash (No Context)
- Best overall performance across all dimensions
- Cost-effective (compared to GPT-4o)
- No additional preprocessing needed

**Key Finding to Highlight:**
- Gemini achieves strong correlations (r > 0.7) for 4 out of 5 dimensions
- Prevention/Promotion dimension shows highest agreement with human coders (r=0.773)

---

## 📚 Detailed Documentation

For comprehensive methodology and full results, see:
- **`COMPREHENSIVE_RESULTS_REPORT.md`** - ⭐ **Start here for complete analysis**
- **`DATASET_ANALYSIS_COMPARISON.md`** - ⭐ **Understand the difference between transcript corpus analysis vs. gold standard validation**
- **`README.md`** - Quick start guide and project documentation
- **`IMPLEMENTATION_NOTES.md`** - Technical details and lessons learned
- **`MLFLOW_TRACKING_GUIDE.md`** - Experiment tracking guide

---

**For historical context:** See `MODEL_COMPARISON_SUMMARY.md` for the previous transcript corpus analysis (Nov 7, 2024) without gold standard validation.

**To understand both phases:** See `DATASET_ANALYSIS_COMPARISON.md` for a detailed comparison between the transcript corpus analysis (Phase 1) and gold standard validation (Phase 2).

