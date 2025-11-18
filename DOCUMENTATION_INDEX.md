# Documentation Index

**Quick Navigation Guide for Peace Research AI Validation Project**

---

## ⭐ Start Here: Main Reports

### 1. **COMPREHENSIVE_RESULTS_REPORT.md** ⭐ **PRIMARY REPORT**
   - **Purpose:** Complete, publication-ready results report
   - **Contents:**
     - Human gold standard dataset analysis (52 videos, 3 evaluators)
     - Missing data handling and inter-rater reliability
     - Model performance across all 5 dimensions
     - Gemini vs OpenAI comparison (Gemini superior)
     - Previous corpus analysis vs current gold standard
     - Publication-ready tables and insights
   - **Use For:** Team meetings, paper submissions, presentations

### 2. **PROJECT_SUMMARY.md**
   - **Purpose:** Quick project overview and status
   - **Contents:** Current status, key findings, technical details, next steps
   - **Use For:** Quick reference, project status updates

### 3. **FINAL_RESULTS_SUMMARY.md**
   - **Purpose:** Executive summary of final results
   - **Contents:** Best models, key findings, recommendations
   - **Use For:** Quick results overview

---

## 📚 Detailed Documentation

### Results and Analysis

- **COMPREHENSIVE_RESULTS_REPORT.md** - Complete results (see above)
- **team_report/team_report_20251117_204008.md** - Detailed team report
- **model_comparison_results/** - Statistical metrics and visualizations

### Technical Documentation

- **IMPLEMENTATION_NOTES.md** - Lessons learned, improvements, best practices
- **MLFLOW_TRACKING_GUIDE.md** - MLflow experiment tracking guide
- **README.md** - Quick start guide and project overview

### Historical Context

- **MODEL_COMPARISON_SUMMARY.md** - Previous corpus analysis (Nov 7, without gold standard)
- **SYSTEM_OVERVIEW.md** - System architecture overview
- **ANALYSIS_MECHANISMS_EXPLAINED.md** - Technical deep-dive on analysis methods

---

## 🎯 Quick Reference by Use Case

### For Team Meetings / Presentations
1. **COMPREHENSIVE_RESULTS_REPORT.md** - Main report
2. **FINAL_RESULTS_SUMMARY.md** - Executive summary
3. **model_comparison_results/plots/** - Visualizations

### For Paper Writing
1. **COMPREHENSIVE_RESULTS_REPORT.md** - Publication-ready tables
2. **validation_results/inter_rater_reliability.csv** - Human agreement metrics
3. **model_comparison_results/model_vs_human_metrics_*.csv** - Statistical metrics

### For Understanding the System
1. **README.md** - Quick start
2. **SYSTEM_OVERVIEW.md** - Architecture
3. **ANALYSIS_MECHANISMS_EXPLAINED.md** - Method details

### For Running Experiments
1. **README.md** - Setup and usage
2. **MLFLOW_TRACKING_GUIDE.md** - Experiment tracking
3. **IMPLEMENTATION_NOTES.md** - Best practices

### For Understanding Results
1. **COMPREHENSIVE_RESULTS_REPORT.md** - Complete analysis
2. **PROJECT_SUMMARY.md** - Key findings
3. **IMPLEMENTATION_NOTES.md** - What we learned

---

## 📊 Key Findings Summary

### Best Model
- **Google Gemini 2.5 Flash (No Context)**
- Average correlation: r = 0.682
- Strong correlations (r > 0.7) for 4/5 dimensions

### Human Gold Standard
- **52 videos** evaluated by 3 human coders
- **Excellent inter-rater reliability:** r = 0.727-0.947
- **Missing data:** 9.6%-38.5% per dimension

### Model Performance
- **49 videos** with complete model scores
- **22 comparisons** (4 LLM × 5 dimensions + 2 RoBERTa × 1 dimension)
- **Best dimension:** Prevention/Promotion (r = 0.773)
- **Most challenging:** Nuance (r = 0.449)

### Gemini vs OpenAI
- **Gemini outperforms OpenAI** by r = +0.232 on average
- **Works best without RoBERTa context**
- **Cost-effective** compared to GPT-4o

---

## 🔍 Dataset Distinctions

### 1. Human Gold Standard Dataset
- **Source:** `gold_standard.xlsx`
- **Size:** 52 videos
- **Evaluators:** 3 human coders (EA, JPA, MMM)
- **Purpose:** Validation benchmark
- **Analysis:** Inter-rater reliability, missing data patterns

### 2. Model Validation Dataset
- **Source:** Videos from gold standard with transcripts
- **Size:** 49 videos (3 missing transcripts)
- **Models:** 6 models (4 LLM + 2 RoBERTa)
- **Purpose:** Model performance evaluation
- **Analysis:** Correlations, MAE, RMSE

### 3. Previous Transcript Corpus (Historical)
- **Source:** `transcript_corpus_v2.csv`
- **Date:** November 7, 2024
- **Models:** 4 methods (2 RoBERTa + 2 OpenAI LLM)
- **Purpose:** Initial model comparison (no gold standard)
- **Analysis:** Model-to-model comparison only

---

## 📁 File Locations

### Results
- **Human Scores:** `validation_results/`
- **Model Scores:** `model_scores_gold_standard/run_1/`
- **Comparisons:** `model_comparison_results/`
- **Reports:** `team_report/`

### Documentation
- **Main Reports:** Root directory (`*.md`)
- **Technical Guides:** Root directory (`*_GUIDE.md`, `*_NOTES.md`)

---

## 🚀 Quick Navigation

| Need | Go To |
|------|-------|
| Complete results | `COMPREHENSIVE_RESULTS_REPORT.md` |
| Quick overview | `PROJECT_SUMMARY.md` |
| Setup instructions | `README.md` |
| Technical details | `IMPLEMENTATION_NOTES.md` |
| Experiment tracking | `MLFLOW_TRACKING_GUIDE.md` |
| Previous analysis | `MODEL_COMPARISON_SUMMARY.md` |

---

**Last Updated:** November 18, 2024

