# Dataset Analysis Comparison: Transcript Corpus vs. Gold Standard Validation

> **Purpose:** This document clearly distinguishes between the two major analysis phases of this project, explaining their differences in dataset, methodology, findings, and implementation.

---

## 📋 Overview: Two Analysis Phases

This project has **two distinct analysis phases**:

1. **Phase 1: Transcript Corpus Analysis** (Nov 7, 2024)
   - Model-to-model comparison without human validation
   - Diverse YouTube channels corpus
   - Established baseline framework

2. **Phase 2: Gold Standard Validation** (Nov 17-18, 2024)
   - Model-to-human comparison with human-coded scores
   - Curated gold standard dataset
   - Validated model performance

---

## 🔄 Phase 1: Transcript Corpus Analysis

### 🎯 Purpose & Goals

**Primary Goal:** Establish a baseline comparison framework for different analysis methods without requiring human-validated ground truth.

**Objectives:**
- Compare 4 different analysis methods on the same transcripts
- Normalize all scores to a comparable scale (0-5)
- Generate visual comparisons to identify method differences
- Establish which methods show similar/different patterns
- Build the framework for future validation

### 📊 Dataset: Transcript Corpus (`transcript_corpus_v2.csv`)

**Source:** `build.py` - Automated YouTube channel scraping

**Dataset Characteristics:**
- **Collection Method:** Automated scraping from diverse YouTube channels
- **Channel Categories:**
  - Political Commentary (Left): The Daily Show, Last Week Tonight
  - Political Commentary (Right): Daily Wire Plus, Matt Walsh
  - News & Journalism: Reuters, Johnny Harris, Wendover Productions, Vox
  - Educational: Kurzgesagt, Veritasium, Smarter Every Day, Crash Course
  - Tech & Business: MKBHD, CNBC Television
  - Science & Nature: NASA, National Geographic
  - Documentary: VICE

**Selection Criteria:**
- 10 videos per channel (from pool of 50 most viewed)
- Duration: 120-1800 seconds (2-30 minutes)
- Minimum views: 50,000
- Sorted by view count (most popular first)
- Only videos with available transcripts

**Final Dataset:**
- **Total Videos:** 49+ transcripts
- **Format:** CSV with columns: `video_id`, `title`, `channel`, `category`, `upload_date`, `duration_seconds`, `view_count`, `like_count`, `full_transcript`
- **No Human Scores:** Pure transcript data only

### 🤖 Models Analyzed (4 Methods)

1. **RoBERTa Plain** (`models.py`)
   - Emotion detection using RoBERTa-base model
   - Focus: Respect vs. Contempt emotions
   - Output: Averaged respect/contempt scores
   - Scale: Normalized to 0-5

2. **RoBERTa Valence** (`scale.py`)
   - Same RoBERTa model + valence weighting
   - Emotion-to-valence mapping (joy=+1.0, anger=-1.0, etc.)
   - Output: Weighted valence score
   - Scale: 1-5 (shifted to 0-5 for comparison)

3. **LLM V1** (`llm_analyzer.py`)
   - OpenAI GPT-4o with plain prompt
   - All 5 peace journalism dimensions
   - Output: Scores on -5 to +5 scale per dimension
   - Scale: Normalized to 0-5

4. **LLM V3_FINAL** (`llm_analyzer.py`)
   - OpenAI GPT-4o with RoBERTa context
   - Hybrid approach: RoBERTa emotions + LLM reasoning
   - Output: Scores on 0-100 scale per dimension
   - Scale: Normalized to 0-5

**Provider:** OpenAI only (no Gemini yet)

### 📝 Implementation Scripts

**Main Script:** `compare_all_models.py`

**Process:**
1. Load `transcript_corpus_v2.csv`
2. Run all 4 methods on each transcript
3. Normalize all scores to 0-5 scale
4. Generate comparison files:
   - `score_comparison_TIMESTAMP.xlsx` (color-coded Excel)
   - `score_comparison_TIMESTAMP.csv` (raw data)
   - `detailed_comparison_TIMESTAMP.json` (full results with rationales)

**Output Location:** `comparison_results/`

### 🔍 Key Findings

1. **LLM Methods Outperformed RoBERTa**
   - LLM methods showed more nuanced understanding
   - RoBERTa methods were faster but less sophisticated

2. **V3_FINAL Showed Promise**
   - Hybrid approach (RoBERTa + LLM) performed well
   - Emotion context helped LLM reasoning

3. **Model Agreement Patterns**
   - Some transcripts: High agreement across all methods
   - Other transcripts: Significant disagreement (interesting cases)
   - Disagreement often indicated nuanced/complex content

4. **No Validation Yet**
   - Could not determine which method was "correct"
   - No ground truth to compare against
   - Framework established for future validation

### 📊 Output Files

- `comparison_results/score_comparison_*.xlsx` - Color-coded comparison
- `comparison_results/score_comparison_*.csv` - Raw scores
- `comparison_results/detailed_comparison_*.json` - Full results

**Note:** These outputs are model-to-model comparisons only, not validated against human judgment.

---

## ✅ Phase 2: Gold Standard Validation

### 🎯 Purpose & Goals

**Primary Goal:** Validate AI models against human-coded gold standard scores to determine which models best replicate human judgment across 5 dimensions of peace journalism.

**Objectives:**
- Extract and clean human-coded scores from Excel
- Run all 6 models on gold standard videos
- Compare model outputs to human scores statistically
- Identify best-performing models per dimension
- Generate publication-ready reports

### 📊 Dataset: Human Gold Standard (`gold_standard.xlsx`)

**Source:** Manually coded by research team

**Dataset Characteristics:**
- **Collection Method:** Manual human coding by 3 evaluators
- **Total Videos:** 52 unique videos
- **Evaluators:** 3 human coders (EA, JPA, MMM)
- **Evaluation Structure:** Each video evaluated by all 3 raters (3 rows per video)

**Coding Dimensions (1-5 scale):**
1. **Nuance** (1-5): Oversimplification vs. Highly nuanced/contextualized
2. **Order/Creativity** (1-5): Order/control vs. Creativity/innovation
3. **Prevention/Promotion** (1-5): Prevention focus vs. Promotion focus
4. **Contempt/Compassion** (1-5): Contemptuous vs. Compassionate toward outgroups
5. **Opinion/News** (1-5): Opinion-based vs. Fact-based news reporting

**Missing Data:**
- Compassion/Contempt: 47 available, 5 missing (9.6%)
- Nuance: 37 available, 15 missing (28.9%)
- Order/Creativity: 32 available, 20 missing (38.5%)
- Prevention/Promotion: 35 available, 17 missing (32.7%)
- News/Opinion: 34 available, 18 missing (34.6%)

**Handling:** Pairwise deletion (exclude missing from analysis)

**Inter-Rater Reliability (Human Agreement):**
- News/Opinion: **r = 0.947** (excellent)
- Compassion/Contempt: **r = 0.940** (excellent)
- Order/Creativity: **r = 0.935** (excellent)
- Nuance: **r = 0.879** (excellent)
- Prevention/Promotion: **r = 0.727** (good)

**Video IDs:** Extracted from Excel hyperlinks (robust matching)

**Transcripts:** Fetched from:
1. Primary: `transcripts/Transcripts.docx` (Word document)
2. Secondary: `transcripts/history/` folder (50 transcript files)
3. Fallback: yt-dlp (disabled to avoid server load)

**Final Dataset:** 49 videos with complete transcripts (3 missing transcripts)

### 🤖 Models Analyzed (6 Methods)

#### LLM Models (All 5 Dimensions)

1. **OpenAI GPT-4o (No Context)**
   - Provider: OpenAI
   - Model: GPT-4o
   - Prompt: V5 All Dimensions (1-5 scale) - **Improved prompts**
   - Context: Transcript only, no emotion scores

2. **OpenAI GPT-4o (With RoBERTa)**
   - Provider: OpenAI
   - Model: GPT-4o
   - Prompt: V5 All Dimensions with RoBERTa Context
   - Context: Transcript + RoBERTa emotion profile

3. **Google Gemini 2.5 Flash (No Context)** ⭐ **BEST OVERALL**
   - Provider: Google
   - Model: Gemini 2.5 Flash
   - Prompt: V5 All Dimensions (1-5 scale)
   - Context: Transcript only, no emotion scores

4. **Google Gemini 2.5 Flash (With RoBERTa)**
   - Provider: Google
   - Model: Gemini 2.5 Flash
   - Prompt: V5 All Dimensions with RoBERTa Context
   - Context: Transcript + RoBERTa emotion profile

#### RoBERTa Models (Compassion/Contempt Only)

5. **RoBERTa Plain**
   - Emotion detection for respect/contempt
   - Output: Normalized to 1-5 scale

6. **RoBERTa Valence**
   - Valence-weighted emotion scores
   - Output: Normalized to 1-5 scale

**Key Differences from Phase 1:**
- ✅ Added Gemini provider (proved superior)
- ✅ Improved prompts (V5 vs. V1/V3)
- ✅ All 5 dimensions (not just compassion/contempt)
- ✅ Better normalization (1-5 matches human scale)

### 📝 Implementation Scripts

**Pipeline (3-step process):**

1. **`validate_against_human.py`**
   - Loads `gold_standard.xlsx`
   - Extracts video IDs from hyperlinks
   - Cleans and aggregates human scores (3 evaluators → average)
   - Calculates inter-rater reliability
   - Output: `validation_results/human_scores_cleaned.csv`

2. **`run_models_on_gold_standard.py`**
   - Loads `validation_results/human_scores_cleaned.csv`
   - Fetches transcripts (Word doc → history folder → skip yt-dlp)
   - Runs all 6 models on each video
   - MLflow tracking for reproducibility
   - Output: `model_scores_gold_standard/run_*/model_scores_*.csv`

3. **`compare_models_to_human.py`**
   - Loads human scores + model scores
   - Calculates statistical metrics:
     - Pearson correlation (r)
     - Spearman correlation (ρ)
     - Mean Absolute Error (MAE)
     - Root Mean Squared Error (RMSE)
   - Generates visualizations (scatter plots, heatmaps)
   - Output: `model_comparison_results/`

**Output Locations:**
- Human scores: `validation_results/`
- Model scores: `model_scores_gold_standard/`
- Comparisons: `model_comparison_results/`

### 🔍 Key Findings

1. **Gemini Outperforms OpenAI** ⭐
   - Average correlation advantage: **+0.232** across all dimensions
   - Best model for ALL 5 dimensions: **Google Gemini 2.5 Flash (No Context)**
   - Cost-effective compared to GPT-4o

2. **Best Performance by Dimension:**
   - Prevention/Promotion: **r = 0.773** (excellent)
   - Creativity/Order: **r = 0.751** (strong)
   - Compassion/Contempt: **r = 0.722** (strong)
   - News/Opinion: **r = 0.716** (strong)
   - Nuance: **r = 0.449** (moderate - most challenging)

3. **RoBERTa Context Not Beneficial**
   - Gemini: r = 0.682 (no context) vs. 0.645 (with context)
   - OpenAI: r = 0.450 (no context) vs. 0.420 (with context)
   - **Implication:** Simple prompts more effective

4. **Human Agreement Validates Gold Standard**
   - Inter-rater correlations: 0.727-0.947 (excellent)
   - 100% agreement within 1 point for 3 dimensions
   - High-quality gold standard for validation

5. **Model Performance Summary:**
   - Average correlation: **r = 0.516** (SD: 0.193)
   - 4 out of 5 dimensions show strong correlations (r > 0.7)
   - Nuance dimension remains most challenging

### 📊 Output Files

**Human Score Extraction:**
- `validation_results/human_scores_cleaned.csv` - Aggregated human scores
- `validation_results/human_metrics_summary.csv` - Summary statistics
- `validation_results/inter_rater_reliability.csv` - Human agreement metrics
- `validation_results/missing_data_report.csv` - Missing data analysis

**Model Scores:**
- `model_scores_gold_standard/run_*/model_scores_*.csv` - All model scores
- `model_scores_gold_standard/run_*/model_scores_detailed_*.json` - Detailed results

**Comparison Results:**
- `model_comparison_results/model_vs_human_metrics_*.csv` - Statistical metrics
- `model_comparison_results/comparison_summary_*.json` - Best methods per dimension
- `model_comparison_results/plots/*.png` - Scatter plots and heatmaps

**Reports:**
- `team_report/team_report_*.md` - Detailed reports
- `COMPREHENSIVE_RESULTS_REPORT.md` - Complete analysis
- `RESULTS.md` - Quick summary

---

## 🔄 Key Differences Summary

### Dataset Differences

| Aspect | Phase 1: Transcript Corpus | Phase 2: Gold Standard |
|--------|---------------------------|------------------------|
| **Source** | Automated scraping (`build.py`) | Manual human coding |
| **Size** | 49+ videos | 52 videos (49 with transcripts) |
| **Selection** | Diverse channels, popular videos | Curated research videos |
| **Human Scores** | ❌ None | ✅ Yes (3 evaluators) |
| **Purpose** | Baseline model comparison | Model validation |

### Model Differences

| Aspect | Phase 1: Transcript Corpus | Phase 2: Gold Standard |
|--------|---------------------------|------------------------|
| **Number of Models** | 4 methods | 6 methods |
| **Providers** | OpenAI only | OpenAI + Google Gemini |
| **Prompt Versions** | V1, V3_FINAL (older) | V5 (improved) |
| **Dimensions** | Primarily Compassion/Contempt | All 5 dimensions |
| **Scale** | 0-5 normalization | 1-5 (matches human) |

### Implementation Differences

| Aspect | Phase 1: Transcript Corpus | Phase 2: Gold Standard |
|--------|---------------------------|------------------------|
| **Main Script** | `compare_all_models.py` | `run_models_on_gold_standard.py` |
| **Input** | `transcript_corpus_v2.csv` | `gold_standard.xlsx` |
| **Output** | Model-to-model comparison | Model-to-human comparison |
| **Validation** | ❌ No ground truth | ✅ Statistical validation |
| **Metrics** | Agreement patterns | Correlations, MAE, RMSE |
| **Tracking** | None | MLflow tracking |

### Findings Differences

| Aspect | Phase 1: Transcript Corpus | Phase 2: Gold Standard |
|--------|---------------------------|------------------------|
| **Main Finding** | LLM > RoBERTa, V3_FINAL promising | Gemini > OpenAI, No Context > With Context |
| **Validation** | Framework established | Models validated against humans |
| **Best Model** | V3_FINAL (hybrid) | Gemini 2.5 Flash (No Context) |
| **Confidence** | Low (no ground truth) | High (validated against humans) |

---

## 📚 Related Documentation

### Phase 1 Documentation
- **`MODEL_COMPARISON_SUMMARY.md`** - Historical summary of transcript corpus analysis
- **`compare_all_models.py`** - Main script for Phase 1

### Phase 2 Documentation
- **`COMPREHENSIVE_RESULTS_REPORT.md`** - ⭐ Complete detailed results
- **`RESULTS.md`** - Quick results summary
- **`validate_against_human.py`** - Human score extraction
- **`run_models_on_gold_standard.py`** - Model execution
- **`compare_models_to_human.py`** - Statistical comparison

### General Documentation
- **`README.md`** - Project overview and quick start
- **`IMPLEMENTATION_NOTES.md`** - Technical details and lessons learned
- **`ANALYSIS_MECHANISMS_EXPLAINED.md`** - How each model works

---

## 🎯 Why Both Phases Matter

### Phase 1 Value
- ✅ Established the comparison framework
- ✅ Identified promising approaches (LLM > RoBERTa)
- ✅ Created baseline for future work
- ✅ Demonstrated feasibility without human coding

### Phase 2 Value
- ✅ Validated models against human judgment
- ✅ Identified best-performing models (Gemini)
- ✅ Confirmed model effectiveness across dimensions
- ✅ Generated publication-ready results

### Together
- **Phase 1** informed **Phase 2** (framework → validation)
- **Phase 2** validated **Phase 1** findings (LLM superiority confirmed)
- Both phases essential for complete research pipeline

---

## 🚀 Usage Guide

### To Run Phase 1 Analysis:
```bash
# Build corpus (if needed)
python build.py

# Compare all models
python compare_all_models.py
```

### To Run Phase 2 Analysis:
```bash
# Step 1: Extract human scores
python validate_against_human.py

# Step 2: Run models on gold standard
python run_models_on_gold_standard.py

# Step 3: Compare models to human scores
python compare_models_to_human.py

# Step 4: Generate team report
python generate_team_report.py
```

---

**Last Updated:** November 21, 2024

