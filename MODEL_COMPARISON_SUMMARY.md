# Model Comparison Framework - Historical Summary

> **⚠️ HISTORICAL DOCUMENT:** This document describes the **previous transcript corpus analysis** (Nov 7, 2024) without human gold standard validation.  
> 
> **For current results, see:**
> - **⭐ [`COMPREHENSIVE_RESULTS_REPORT.md`](COMPREHENSIVE_RESULTS_REPORT.md)** - Complete results with all 5 dimensions, Gemini vs OpenAI comparison, and human validation
> - **⭐ [`RESULTS.md`](RESULTS.md)** - Quick results summary

---

## 🎯 What I've Created For You

I've built a comprehensive testing and validation framework that allows you to:

1. **Compare 4 different analysis methods** on the same transcripts
2. **Normalize all scores to 0-5 scale** for fair comparison
3. **Generate visual comparisons** (Excel with color coding, charts, etc.)
4. **Validate against human ground truth** when available
5. **Identify the best method** for your specific use case

---

## 📊 The 4 Analysis Methods Explained Simply

### Method 1: RoBERTa Plain
- **What it does**: Counts emotions, calculates respect vs contempt
- **Pros**: Fast, free, deterministic
- **Cons**: Simple, doesn't understand context
- **Best for**: Large datasets, quick analysis, when you don't need deep understanding

### Method 2: RoBERTa Valence Scaled (scale.py)
- **What it does**: Weights emotions by "valence" (how positive/negative), maps to 1-5 scale
- **Pros**: More nuanced than plain RoBERTa, still fast and free
- **Cons**: Valence weights are subjective, still no context
- **Best for**: When you want more sophistication than plain RoBERTa but still need speed

### Method 3: LLM V1 (Plain Prompt)
- **What it does**: Sends transcript to GPT-4, scores 5 "peace dimensions"
- **Pros**: Deep contextual understanding, interpretable rationales
- **Cons**: Expensive, slow, non-deterministic
- **Best for**: When accuracy is critical and you have budget

### Method 4: LLM V3_FINAL (RoBERTa + LLM Combined)
- **What it does**: First runs RoBERTa emotions, then asks LLM to reason using those emotions
- **Pros**: Best accuracy, combines data + reasoning
- **Cons**: Most expensive, slowest
- **Best for**: Final validation, research publications, when you need the best

---

## 🗂️ Files I've Created

### Main Scripts

| File | Purpose | When to Use |
|------|---------|-------------|
|    `compare_all_models.py`   | Run all 4 methods on transcripts | **Use this first!** |
| `validate_against_human.py` | Compare methods to human scores | After you have human-coded data |

### Documentation

| File | What's Inside |
|------|---------------|
| `QUICK_START_GUIDE.md` | Step-by-step tutorial (⭐ **START HERE**) |
| `ANALYSIS_MECHANISMS_EXPLAINED.md` | Technical deep-dive on each method |
| `MODEL_COMPARISON_SUMMARY.md` | This file - high-level overview |

### Templates & Examples

| File | Purpose |
|------|---------|
| `human_scores_template.csv` | Template for adding your human scores |

---

## 🚀 How to Use This (Simple 3-Step Process)

### Step 1: Run Comparison (5 minutes)

```bash
# Quick test on 2 transcripts
python compare_all_models.py --quick-test
```

**Output**: Creates `comparison_results/score_comparison_TIMESTAMP.xlsx`

Open this Excel file to see:
- All 4 methods' scores side-by-side
- Color coding (red = negative, green = positive)
- Which videos have high agreement vs disagreement

### Step 2: Review Results (10 minutes)

Look for:
- ✅ **High agreement** = All methods give similar scores (good!)
- ⚠️ **Low agreement** = Methods disagree (interesting cases, may need human review)
- 📊 **Patterns** = Do certain methods always score higher/lower?

### Step 3: (Optional) Add Human Scores & Validate

1. Pick 20-30 videos to code yourself
2. Fill in `human_scores.csv` (use template)
3. Run: `python validate_against_human.py`
4. See which method matches humans best

---

## 📈 Understanding the Output

### Comparison Results (Step 1 Output)

**Excel File Structure:**
```
video_id | title | category | RoBERTa_Plain | RoBERTa_Valence | LLM_V1 | LLM_V3
---------|-------|----------|---------------|-----------------|--------|--------
ABC123   | News  | Journalism | 2.3        | 2.5            | 2.4    | 2.6
XYZ789   | Opinion| Political | 1.2        | 3.8            | 4.1    | 3.5  ← Disagreement!
```

**What to do with disagreements:**
1. Watch/read that video yourself
2. Decide which method seems right
3. Use that insight to choose your method

### Validation Results (Step 3 Output)

**Metrics Explained:**

- **MAE** (Mean Absolute Error): Average difference from human scores
  - 0.3 = Excellent ✅
  - 0.5 = Good ✅
  - 1.0 = Okay ⚠️
  - 2.0 = Poor ❌

- **Pearson r** (Correlation): How well method tracks with humans
  - 0.9+ = Excellent ✅
  - 0.7-0.9 = Good ✅
  - 0.5-0.7 = Okay ⚠️
  - <0.5 = Poor ❌

- **Within 1pt Agreement**: % of scores within ±1 point of human
  - 95%+ = Excellent ✅
  - 80%+ = Good ✅
  - 60%+ = Okay ⚠️
  - <60% = Poor ❌

---

## 💰 Cost Considerations

|      Method     | Cost per Transcript | 100 Transcripts | Notes |
|-----------------|---------------------|-----------------|-------|
|  RoBERTa Plain  |        $0           | $0 | Free! |
| RoBERTa Valence |        $0           | $0 | Free! |
| LLM V1 (OpenAI) |       ~$0.03        | ~$3 | GPT-4 pricing |
|  LLM V3_FINAL   |       ~$0.05        | ~$5 | RoBERTa + GPT-4 |

**Money-Saving Tips:**
1. Test on small sample first (use `--num-samples 10`)
2. Use RoBERTa methods for bulk analysis
3. Use LLM methods only for validation subset
4. Consider GPT-3.5 instead of GPT-4 (cheaper but less accurate)

---

## 🎓 Research Workflow Recommendation

Based on peace research best practices:

### Phase 1: Exploration (Free)
```bash
python compare_all_models.py --num-samples 20
```
- Use to understand your data
- Identify interesting cases
- See if methods agree

### Phase 2: Pilot Validation ($5-10)
```bash
python compare_all_models.py --num-samples 30  # Include LLM methods
```
- Code 30 transcripts yourself
- Run validation
- Choose best method

### Phase 3: Full Analysis (Cost depends on choice)
```bash
# Option A: Use best LLM method on all (expensive but accurate)
python compare_all_models.py

# Option B: Use free RoBERTa method on all (free but less accurate)
# Just run RoBERTa analysis separately

# Option C: Hybrid approach
# - RoBERTa on all transcripts (free)
# - LLM validation on random 10% sample (moderate cost)
```

### Phase 4: Publication
- Report all methods' results in appendix
- Use validation metrics to justify choice
- Make code/data available for replication

---

## 🔍 What Each Score Means (0-5 Scale)

All methods now output on same 0-5 scale where:

- **5** = Highly compassionate, inclusive, peaceful language
- **4** = Mostly positive, constructive
- **3** = Neutral, balanced
- **2** = Somewhat negative, divisive
- **1** = Clearly contemptuous, dismissive
- **0** = Extremely hostile, dehumanizing

**Example Interpretations:**

| Score | Example Language |
|-------|------------------|
|  4.5  | "Leaders from both parties came together to find common ground..." |
|  3.0  | "The bill passed with a vote of 52-48..." (factual, neutral) |
|  1.5  | "Idiotic politicians once again prove they have no idea what they're doing..." |

---

## ❓ FAQ

### Q: Which method should I use?
**A:** Run comparison first, then decide based on:
- Budget (RoBERTa = free, LLM = costs money)
- Accuracy needs (LLM = more accurate)
- Scale (RoBERTa = fast for 1000s of videos)

### Q: Do I need human scores?
**A:** Not required, but highly recommended for:
- Academic research (need validation)
- Production systems (need confidence)
- Understanding which method fits your domain

### Q: How many transcripts should I code?
**A:** 
- Minimum: 20 (basic validation)
- Good: 50 (reliable estimates)
- Best: 100+ (robust validation)

### Q: What if methods disagree?
**A:** This is actually useful information!
- High disagreement = complex/nuanced content
- Code these manually to understand why
- May reveal method strengths/weaknesses

### Q: Can I use this for non-English?
**A:** 
- RoBERTa: English only (model limitation)
- LLM: Yes! GPT-4 handles many languages
- Would need separate validation per language

### Q: How do I cite this work?
**A:** See `ANALYSIS_MECHANISMS_EXPLAINED.md` for proper citations of:
- RoBERTa model (HuggingFace)
- Go Emotions dataset (Google Research)
- Your own methodology

---

## 🛠️ Troubleshooting Quick Reference

| Problem | Solution |
|---------|----------|
| "Module not found" | `pip install -r requirements.txt` |
| "API key not set" | Create `.env` file with keys |
| "Out of memory" | Use `--num-samples` to limit size |
| "Rate limit exceeded" | Add delays or use fewer samples |
| "No validation data" | Check video_ids match between files |

---

## 📞 Next Steps

1. ✅ **Read this file** (you're here!)
2. ✅ **Try quick test**: `python compare_all_models.py --quick-test`
3. ✅ **Open Excel results** to see comparison
4. ✅ **Review** [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md) for detailed instructions
5. ✅ **Code some transcripts** and run validation
6. ✅ **Choose your method** based on results

---

## 🎉 What Makes This Framework Powerful

✅ **Unified Scale**: All methods normalized to 0-5 for fair comparison

✅ **Comprehensive**: Tests 4 fundamentally different approaches

✅ **Validated**: Can compare to human ground truth

✅ **Visual**: Excel color-coding and plots make patterns obvious

✅ **Reproducible**: All code documented and version controlled

✅ **Flexible**: Works with 2 transcripts or 2000

✅ **Research-Ready**: Generates publication-quality validation metrics

---

*Happy analyzing! 📊*

*Last Updated: 2025-11-07*

