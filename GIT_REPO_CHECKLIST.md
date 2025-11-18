# Git Repository Checklist: What to Push to Public Repo

**Purpose:** Guide for sharing code and results with team members while protecting sensitive data.

---

## ✅ INCLUDE (Push to Repo)

### 📝 Core Documentation
- ✅ `README.md` - Main project documentation
- ✅ `COMPREHENSIVE_RESULTS_REPORT.md` - Complete results report
- ✅ `PROJECT_SUMMARY.md` - Project overview
- ✅ `IMPLEMENTATION_NOTES.md` - Lessons learned
- ✅ `DOCUMENTATION_INDEX.md` - Navigation guide
- ✅ `FINAL_RESULTS_SUMMARY.md` - Executive summary
- ✅ `MLFLOW_TRACKING_GUIDE.md` - MLflow guide
- ✅ `MODEL_COMPARISON_SUMMARY.md` - Historical context
- ✅ `SYSTEM_OVERVIEW.md` - Architecture overview
- ✅ `ANALYSIS_MECHANISMS_EXPLAINED.md` - Technical deep-dive
- ✅ `QUICK_START_GUIDE.md` - Quick start guide
- ✅ `GIT_REPO_CHECKLIST.md` - This file

### 💻 Core Python Scripts
- ✅ `validate_against_human.py` - Human score extraction
- ✅ `run_models_on_gold_standard.py` - Model execution
- ✅ `compare_models_to_human.py` - Statistical comparison
- ✅ `generate_team_report.py` - Report generation
- ✅ `llm_analyzer.py` - LLM API integration
- ✅ `models.py` - RoBERTa models
- ✅ `scale.py` - Valence scaling
- ✅ `parse_transcripts_docx.py` - Transcript parsing
- ✅ `utils.py` - Utility functions
- ✅ `compare_all_models.py` - Historical comparison script
- ✅ `compare_runs_consistency.py` - Run consistency analysis
- ✅ `build.py` - Transcript fetching utilities
- ✅ `config.py` - Configuration (if no secrets)

### 📊 Results and Outputs (Summary Data Only)
- ✅ `validation_results/human_scores_cleaned.csv` - Aggregated human scores (anonymized)
- ✅ `validation_results/human_metrics_summary.csv` - Summary statistics
- ✅ `validation_results/inter_rater_reliability.csv` - Human agreement metrics
- ✅ `validation_results/missing_data_report.csv` - Missing data analysis
- ✅ `validation_results/data_quality_notes.json` - Data quality notes
- ✅ `validation_results/*.png` - Human score visualizations
- ✅ `model_comparison_results/comparison_summary_*.json` - Best methods summary
- ✅ `model_comparison_results/model_vs_human_metrics_*.csv` - Statistical metrics
- ✅ `model_comparison_results/plots/*.png` - Visualizations (scatter plots, heatmaps)
- ✅ `team_report/team_report_*.md` - Team reports
- ✅ `team_report/summary_stats_*.json` - Summary statistics
- ✅ `model_scores_gold_standard/run_*/model_scores_*.csv` - Summary model scores (CSV only, not detailed JSON)

### 📦 Configuration Files
- ✅ `requirements.txt` - Python dependencies
- ✅ `.gitignore` - Git ignore rules

### 📋 Templates and Examples
- ✅ `human_scores_template.csv` - Template for human scoring

### 📈 Sample Data (If Appropriate)
- ✅ `transcript_corpus_v2.csv` - Sample transcript corpus (if not sensitive)
- ✅ `transcript_corpus.csv` - Sample corpus (if not sensitive)

---

## ❌ EXCLUDE (Do NOT Push)

### 🔐 Sensitive Data
- ❌ `.env` files - API keys and secrets (already in .gitignore)
- ❌ `gold_standard.xlsx` - **Contains human evaluator names and potentially sensitive data**
  - **Alternative:** Create anonymized version or exclude
- ❌ `transcripts/Transcripts.docx` - **May contain copyrighted content**
  - **Alternative:** Include sample transcripts only, or exclude entirely
- ❌ `transcripts/history/*.txt` - Individual transcript files (large, potentially copyrighted)
- ❌ Any files with API keys, passwords, or personal information

### 💾 Large Files and Caches
- ❌ `mlruns/` - MLflow tracking database (can be large, regenerated)
- ❌ `__pycache__/` - Python bytecode (already in .gitignore)
- ❌ `*.pyc`, `*.pyo`, `*.pyd` - Compiled Python files (already in .gitignore)
- ❌ `subtitles/` - Temporary subtitle files (already in .gitignore)
- ❌ `results/` - Old results (already in .gitignore)
- ❌ `experiments/` - Experimental files (already in .gitignore)

### 🗂️ Detailed Model Outputs (Too Large)
- ❌ `model_scores_gold_standard/run_*/model_scores_detailed_*.json` - **Very large files with full rationales**
  - **Alternative:** Include only the CSV summaries, exclude detailed JSON
- ❌ `model_comparison_results/merged_human_model_scores_*.csv` - **Contains full individual scores**
  - **Alternative:** Include only summary metrics, not individual video scores

### 🛠️ Development Files
- ❌ `*.code-workspace` - VSCode workspace files (already in .gitignore)
- ❌ `.vscode/` - VSCode settings (already in .gitignore)
- ❌ `testenv/` - Virtual environment (already in .gitignore)
- ❌ `venv/` - Virtual environment (already in .gitignore)
- ❌ `test_*.py` - Test files (optional, can include if useful)
- ❌ `app.py` - Flask app (if contains test code only)

### 📱 Extension/Experimental Code
- ❌ `extension/` - Chrome extension (if not core to research)
- ❌ `experiments/` - Experimental code (already in .gitignore)
- ❌ `hist_*.py` - History extraction scripts (if not core)

### 📄 Office Files (Temporary)
- ❌ `~$*.xlsx` - Excel temporary files (now in .gitignore)
- ❌ `~$*.docx` - Word temporary files (now in .gitignore)
- ❌ `*.xlsx` in `comparison_results/` - Large Excel files (CSV is better)

---

## 🔄 RECOMMENDED: Create Anonymized/Sample Versions

### For `gold_standard.xlsx`:
Create `gold_standard_sample.xlsx` with:
- ✅ Sample of 5-10 videos (not all 52)
- ✅ Anonymized evaluator names (EA, JPA, MMM → Evaluator1, Evaluator2, Evaluator3)
- ✅ Remove any identifying information

### For Transcripts:
- ✅ Include 2-3 sample transcripts in `samples/transcripts/` folder
- ✅ Add note: "Full transcripts available upon request"

### For Model Scores:
- ✅ Include summary CSVs only
- ✅ Exclude detailed JSON with full rationales (too large)
- ✅ Add note: "Detailed results available upon request"

---

## 📝 Pre-Push Checklist

Before pushing to public repo:

- [ ] Review all files for API keys, passwords, personal info
- [ ] Remove or anonymize `gold_standard.xlsx` (or exclude)
- [ ] Exclude large detailed JSON files
- [ ] Exclude individual transcript files
- [ ] Update `.gitignore` with exclusions (✅ DONE)
- [ ] Test clone in fresh directory to verify nothing sensitive is included
- [ ] Add `LICENSE` file (if applicable)
- [ ] Add `CONTRIBUTING.md` (if team will contribute)
- [ ] Update `README.md` with setup instructions (without API keys)

---

## 🎯 Recommended Repository Structure

```
peace-research-ai-validation/
├── README.md                          # Main documentation
├── requirements.txt                   # Dependencies
├── .gitignore                         # Exclusions
├── LICENSE                            # License (if applicable)
│
├── docs/                              # Documentation
│   ├── COMPREHENSIVE_RESULTS_REPORT.md
│   ├── PROJECT_SUMMARY.md
│   ├── IMPLEMENTATION_NOTES.md
│   └── ...
│
├── src/                               # Core scripts
│   ├── validate_against_human.py
│   ├── run_models_on_gold_standard.py
│   ├── compare_models_to_human.py
│   ├── llm_analyzer.py
│   ├── models.py
│   └── ...
│
├── data/                              # Sample data
│   ├── samples/
│   │   └── transcripts/              # 2-3 sample transcripts
│   └── gold_standard_sample.xlsx     # Anonymized sample
│
├── results/                           # Summary results only
│   ├── validation_results/           # Human score summaries
│   ├── model_comparison_results/     # Metrics and plots
│   └── team_report/                  # Reports
│
└── templates/
    └── human_scores_template.csv
```

---

## 🔍 Security Review Commands

Before making repo public, run these commands:

```bash
# Search for API keys
grep -r "api_key" . --exclude-dir=.git --exclude="*.md" --exclude="*.txt"
grep -r "API_KEY" . --exclude-dir=.git --exclude="*.md" --exclude="*.txt"
grep -r "sk-" . --exclude-dir=.git --exclude="*.md" --exclude="*.txt"  # OpenAI keys

# Check for large files
find . -type f -size +10M -not -path "./.git/*"

# Review what will be committed
git status
git diff --cached  # If staging files
```

---

## 📧 For Team Members

**What they'll get:**
- ✅ All code to run the analysis
- ✅ Documentation and reports
- ✅ Summary statistics and visualizations
- ✅ Sample data to understand structure

**What they'll need:**
- 🔑 Their own API keys (OpenAI, Gemini)
- 📊 Access to full gold standard (if needed, share separately)
- 📝 Full transcripts (if needed, share separately)

**Setup instructions:**
1. Clone repo
2. Install dependencies: `pip install -r requirements.txt`
3. Set up `.env` file with their own API keys:
   ```
   OPENAI_API_KEY=their_key_here
   GEMINI_API_KEY=their_key_here
   ```
4. Run scripts as documented in README

---

## 🚀 Quick Commands

```bash
# Review what will be committed
git status

# Check for large files
find . -type f -size +5M -not -path "./.git/*"

# Check for potential secrets
grep -r "api_key\|API_KEY\|password\|secret" . --exclude-dir=.git --exclude="*.md" --exclude="*.txt"

# See what files are tracked/untracked
git ls-files
git ls-files --others --excluded --exclude-standard
```

---

**Last Updated:** November 18, 2024

