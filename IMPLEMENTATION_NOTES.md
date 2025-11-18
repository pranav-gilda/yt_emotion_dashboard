# Implementation Notes: Lessons Learned and Improvements

**Date:** November 18, 2024  
**Purpose:** Document key learnings, improvements, and best practices for future runs

---

## 🔍 Key Discoveries

### 1. Column Name Mismatch Issue

**Problem:** Human scores use `contempt_compassion_score`, but model outputs use `compassion_contempt`.

**Solution:** Added explicit mapping in `compare_models_to_human.py`:
```python
DIMENSION_MAPPING = {
    'compassion_contempt': 'contempt_compassion_score'  # Human scores use different naming
}
```

**Lesson:** Always verify column name consistency between data sources before comparison.

**Impact:** Initially missed compassion/contempt in first two comparison runs (18:44:42, 18:44:58). Fixed in third run (20:39:32).

---

### 2. Transcript Matching Challenges

**Problem:** Video IDs from CSV didn't match transcript filenames in `transcripts/history/`.

**Root Cause:**
- CSV video_ids: YouTube IDs like `-xSSoIOxP3E`
- Transcript files: May have different format or naming
- Zero overlap between CSV IDs and transcript filenames

**Solution Implemented:**
1. **Multiple candidate IDs:** Try both `youtube_id` and `video_id`, with/without leading dashes
2. **Enhanced .docx parser:** Extract YouTube IDs from titles and create dual mapping (by title AND by ID)
3. **Direct + normalized matching:** Try exact match first, then normalized match
4. **Priority order:** `transcripts/history/` → `.docx` → skip yt-dlp

**Code Location:** `run_models_on_gold_standard.py` - `get_transcript_for_video()`

**Lesson:** Robust matching requires multiple fallback strategies and flexible ID handling.

---

### 3. Gemini API Key Check Bug

**Problem:** Code checked `genai.api_key` which doesn't exist in the library.

**Error:** `module 'google.generativeai' has no attribute 'api_key'`

**Solution:** Changed to check environment variable directly:
```python
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not set in environment variables.")
```

**Lesson:** Always verify library API before using attributes. Check environment variables directly.

---

### 4. Transcript Caching (In-Memory Only)

**Current Implementation:**
- `TRANSCRIPT_CACHE = {}` - in-memory dictionary
- Resets on every script run
- Caches during single run execution

**Limitation:** Transcripts re-read on every new run.

**Future Improvement:** Could persist cache to disk (JSON/pickle) for cross-run caching.

**Current Workaround:** Use `transcripts/history/` folder for fast file-based access.

---

### 5. Missing Data Handling

**Approach:** Pairwise deletion (exclude missing from analysis)

**Impact:**
- Sample sizes vary by dimension (N = 29-47)
- Most complete: Compassion/Contempt (N = 47, 9.6% missing)
- Least complete: Order/Creativity (N = 32, 38.5% missing)

**Considerations:**
- Missing data is not random (varies by dimension)
- Could bias results if missingness correlates with score values
- Future: Consider imputation or complete-case analysis

---

## 🚀 Improvements Implemented

### 1. MLflow Tracking

**Added:** Full experiment tracking for all model runs

**Benefits:**
- Reproducibility: All parameters and metrics logged
- Comparison: Easy comparison between runs
- Artifacts: CSV and JSON files automatically saved
- History: Track evolution of results over time

**Implementation:**
- Experiment: "Gold Standard Model Validation"
- Parameters: run_number, total_videos, transcript counts
- Metrics: success rates, average transcript lengths, word counts
- Artifacts: model scores CSV, detailed JSON

**Usage:**
```bash
mlflow ui  # View all runs in web interface
```

---

### 2. Run-Specific Folders

**Structure:**
```
model_scores_gold_standard/
├── run_1/  # First run (complete, all 5 dimensions)
└── run_2/  # Second run (for consistency check)
```

**Benefits:**
- No overwrites: Each run saves to separate folder
- Easy comparison: Compare run_1 vs run_2
- Organization: Clear separation of different runs
- History: Keep all runs for analysis

---

### 3. Transcript Optimization

**Priority Order:**
1. `transcripts/history/{youtube_id}.txt` - Fastest, no API calls
2. `transcripts/Transcripts.docx` - Parsed, 459 transcripts
3. Skip yt-dlp - Avoid hitting YouTube servers

**Benefits:**
- **Speed:** Local files much faster than API calls
- **Reliability:** No dependency on YouTube API availability
- **Cost:** No API rate limits or costs
- **Caching:** File-based access is naturally cached by OS

**Implementation:** Enhanced matching logic tries multiple candidate IDs and formats.

---

### 4. Enhanced Metadata Capture

**Added Fields:**
- `transcript_length`: Character count
- `transcript_word_count`: Word count
- `transcript_sentence_count`: Sentence count
- `top_3_emotions`: For RoBERTa methods (from emotion scores)

**Benefits:**
- **Analysis:** Can investigate transcript length impact on performance
- **Quality Control:** Identify very short/long transcripts
- **Interpretability:** Top emotions provide context for RoBERTa scores

**Future Use:** Transcript length analysis to understand if longer transcripts improve model performance.

---

### 5. Top 3 Emotions Capture

**Added:** RoBERTa methods now extract and save top 3 emotions

**Format:**
```json
{
  "top_3_emotions": [
    {"emotion": "admiration", "score": 0.1234},
    {"emotion": "caring", "score": 0.0987},
    {"emotion": "disgust", "score": 0.0765}
  ]
}
```

**Benefits:**
- **Interpretability:** Understand what emotions drive RoBERTa scores
- **Analysis:** Can correlate top emotions with human scores
- **Debugging:** Identify cases where emotions don't align with scores

---

### 6. Heatmaps Organization

**Structure:**
```
model_comparison_results/plots/
├── scatter_plots/  # Individual method-dimension scatter plots
└── heatmaps/       # Correlation heatmaps per dimension
```

**Benefits:**
- **Organization:** Clear separation of plot types
- **Consistency:** Matches user's folder structure preference
- **Easy Access:** Quick location of specific visualizations

---

### 7. Robust Error Handling

**Improvements:**
- Graceful handling of missing transcripts
- Logging of failed model runs (continues with other models)
- NaN handling in pandas operations
- Type checking and validation

**Result:** Scripts complete successfully even with partial failures.

---

## 📊 Comparison: Previous vs. Current Analysis

### Previous Analysis (Transcript Corpus, Nov 7)

**Dataset:** `transcript_corpus_v2.csv`  
**Models:** 4 (2 RoBERTa + 2 OpenAI LLM)  
**Prompts:** V1, V3_FINAL (older)  
**Provider:** OpenAI only  
**Gold Standard:** None  
**Scale:** 0-5 normalization  

**Purpose:** Establish baseline, compare model methods

### Current Analysis (Gold Standard, Nov 17)

**Dataset:** 49 videos with human gold standard  
**Models:** 6 (2 RoBERTa + 4 LLM)  
**Prompts:** V5 All Dimensions (new, improved)  
**Providers:** OpenAI + Google Gemini  
**Gold Standard:** 52 videos, 3 evaluators  
**Scale:** 1-5 (matches human scale)  

**Purpose:** Validate models against human judgment

**Key Evolution:**
- ✅ Added Gemini (proved superior)
- ✅ Improved prompts (V5 vs. V1/V3)
- ✅ Human validation (not just model comparison)
- ✅ All 5 dimensions (not just compassion/contempt)
- ✅ Better normalization (1-5 matches human scale)

---

## 🎯 Best Practices Established

### 1. Always Verify Column Names
- Check human score column names
- Map to model output names explicitly
- Log mismatches for debugging

### 2. Use Multiple Transcript Sources
- Local files first (fastest)
- .docx parsing (flexible)
- Skip external APIs when possible

### 3. Track Everything in MLflow
- Parameters: run_number, model versions, prompt versions
- Metrics: success rates, correlations, errors
- Artifacts: CSV files, JSON results

### 4. Organize by Run Number
- Separate folders for each run
- Timestamped files for history
- Easy comparison between runs

### 5. Capture Rich Metadata
- Transcript characteristics (length, word count)
- Model outputs (scores, emotions, rationales)
- Processing metadata (timestamps, errors)

### 6. Robust Matching Logic
- Try multiple ID formats
- Direct and normalized matching
- Fallback strategies

---

## 🔮 Future Improvements

### 1. Persistent Transcript Cache
- Save cache to disk (JSON/pickle)
- Load on script start
- Update as new transcripts found

### 2. Transcript Length Analysis
- Correlate length with model performance
- Identify optimal transcript length
- Handle very short/long transcripts

### 3. Error Analysis
- Deep dive into high-error cases
- Identify patterns in failures
- Improve prompts based on errors

### 4. Missing Data Imputation
- Consider imputation methods
- Compare complete-case vs. imputed results
- Document imputation impact

### 5. Run Consistency Analysis
- Compare run_1 vs run_2
- Identify stable vs. variable models
- Document reliability metrics

---

## 📝 Code Quality Improvements

### 1. Type Hints
- Added type hints throughout
- Better IDE support
- Clearer function signatures

### 2. Error Messages
- Descriptive error messages
- Context in logging
- Actionable warnings

### 3. Documentation
- Comprehensive docstrings
- Clear function purposes
- Usage examples

### 4. Modularity
- Separate functions for each step
- Reusable components
- Easy to test and debug

---

## 🎓 Lessons for Future Research

1. **Start with column name verification** - Saves debugging time
2. **Use MLflow from the beginning** - Tracking is invaluable
3. **Organize by run number** - Prevents confusion and overwrites
4. **Capture rich metadata** - Enables deeper analysis later
5. **Robust matching logic** - Handle edge cases upfront
6. **Test with small sample first** - Catch issues early
7. **Document assumptions** - Makes debugging easier
8. **Version control prompts** - Track prompt evolution

---

**Last Updated:** November 18, 2024  
**Status:** Active Documentation

