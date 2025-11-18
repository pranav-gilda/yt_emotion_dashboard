
# Quick Start Guide: Model Comparison & Validation

This guide will walk you through testing all 4 analysis methods and validating them against human scores.

---

## 📋 Prerequisites

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up API keys** (for LLM methods):
   Create a `.env` file with:
   ```
   OPENAI_API_KEY=your_key_here
   GEMINI_API_KEY=your_key_here
   ```

3. **Prepare transcript corpus**:
   - Already done! `transcript_corpus_v2.csv` contains your transcripts
   - Or build a new one: `python build.py`

---

## 🚀 Step 1: Run Comparison on All Methods

### Quick Test (2 samples)
```bash
python compare_all_models.py --quick-test
```

This will:
- ✅ Test on 2 transcripts (fast, good for testing)
- ✅ Run all 4 methods
- ✅ Generate comparison files

### Analyze Specific Videos
```bash
python compare_all_models.py --video-ids _GXNJ3V9lzg DK9TkLPJY6w k8j3N7dEwzY
```

### Analyze Random Sample (10 videos)
```bash
python compare_all_models.py --num-samples 10
```

### Analyze ALL Transcripts (⚠️ Expensive - LLM API costs!)
```bash
python compare_all_models.py
```

**⚠️ Cost Warning**: Running LLM analysis on all transcripts can be expensive!
- OpenAI GPT-4: ~$0.03 per transcript
- 50 transcripts = ~$1.50
- Use `--num-samples` to control costs

---

## 📊 Step 2: Review Comparison Results

After running `compare_all_models.py`, check the `comparison_results/` folder:

### Files Generated

1. **`score_comparison_TIMESTAMP.xlsx`** ⭐ START HERE
   - Color-coded scores (red = low peace, green = high peace)
   - Easy to see which methods agree/disagree
   - Open in Excel/LibreOffice

2. **`score_comparison_TIMESTAMP.csv`**
   - Same data in CSV format
   - For programmatic analysis

3. **`detailed_comparison_TIMESTAMP.json`**
   - Full raw results from each method
   - Includes rationales, emotions, etc.

### What to Look For

**High Agreement** (all methods give similar scores):
- Transcript is clear-cut (very positive or very negative)
- Methods are working well

**Low Agreement** (methods disagree):
- Transcript is nuanced/complex
- May need human coding to determine ground truth
- Interesting cases for analysis!

**Example**: 
| Video ID | Title   | RoBERTa Plain | Valence | LLM V1 | LLM V3 |
|----------|---------|---------------|---------|--------|--------|
| ABC123   | News    |      2.3      |   2.5   |   2.4  |   2.6  | ← Good agreement
| XYZ789   | Opinion |      1.2      |   3.8   |   4.1  |   3.5  | ← Poor agreement, needs human review

---

## 👤 Step 3: Add Human Ground Truth (Optional but Recommended)

### 3.1 Create Human Scores File

Create `human_scores.csv` with this format:

```csv
video_id,human_score_0_5,coder_id,notes,confidence
_GXNJ3V9lzg,2.3,coder1,Neutral tone with slight negativity,high
DK9TkLPJY6w,4.2,coder1,Mostly positive framing,high
k8j3N7dEwzY,1.8,coder1,Divisive language,medium
```

**Required columns**:
- `video_id`: Must match IDs in `transcript_corpus_v2.csv`
- `human_score_0_5`: Score from 0-5 (0=very negative/contemptuous, 5=very positive/compassionate)

**Optional columns**:
- `coder_id`: For tracking multiple coders
- `notes`: Why this score?
- `confidence`: high/medium/low

### 3.2 Coding Guidelines (Suggested)

**0-5 Scale for Peacefulness/Compassion:**

- **5.0**: Highly compassionate, inclusive, respectful language. Multiple perspectives presented fairly.
- **4.0**: Mostly positive, some empathy shown, generally constructive.
- **3.0**: Neutral, balanced reporting without strong emotional framing.
- **2.0**: Somewhat divisive or dismissive, but not overtly contemptuous.
- **1.0**: Clearly contemptuous, dehumanizing language toward outgroups.
- **0.0**: Extremely divisive, hateful, or violent rhetoric.

**Tips**:
- Watch out for sarcasm (may appear positive but is actually negative)
- Consider both explicit words AND implicit framing
- Code independently then compare with other coders

---

## 🔬 Step 4: Validate Against Human Scores

Once you have `human_scores.csv`, run validation:

```bash
python validate_against_human.py
```

This will:
1. ✅ Compare each method to human scores
2. ✅ Calculate MAE (lower = better)
3. ✅ Calculate correlation (higher = better)
4. ✅ Generate scatter plots and error distributions
5. ✅ Identify which method best matches humans

### Output Files

Check `validation_results/` folder:

1. **`validation_metrics.csv`** - Summary table
   - MAE, RMSE, correlation for each method
   - Sorted by performance (best first)

2. **`scatter_comparison.png`** - Visual comparison
   - Shows how each method correlates with human scores
   - Regression lines and perfect agreement line

3. **`error_distribution.png`** - Error analysis
   - Shows bias (systematically too high/low?)
   - Helps identify which method is most calibrated

4. **`bland_altman.png`** - Agreement analysis
   - Clinical-style agreement plots
   - Shows if agreement varies by score range

### Interpreting Results

**Good Method:**
- ✅ MAE < 0.5 (predictions within ±0.5 of human)
- ✅ Pearson r > 0.7 (strong correlation)
- ✅ Within 1pt agreement > 80%
- ✅ Low bias (close to 0)

**Example Output**:
```
🏆 BEST PERFORMING METHOD: LLM_V3_FINAL_openai
   - Mean Absolute Error: 0.32
   - Pearson Correlation: 0.87
   - Within 1 point: 95.23%
```

---

## 📈 Step 5: Analyze Results

### Questions to Answer

1. **Which method is most accurate?**
   - Look at MAE in validation results
   - Check correlation coefficients

2. **Which method is best for my use case?**
   - High accuracy needed → Use best-performing method
   - Large dataset needed → Use RoBERTa (fast, cheap)
   - Need explanations → Use LLM methods

3. **Do methods agree more on certain content types?**
   - Filter by `category` column
   - Compare scores across "Political Commentary" vs "Educational"
   - May reveal domain-specific strengths

4. **Are there systematic biases?**
   - Check "bias" metric in validation
   - Positive bias = method scores too high
   - Negative bias = method scores too low

### Example Analysis

```python
import pandas as pd

# Load comparison results
df = pd.read_csv('comparison_results/score_comparison_TIMESTAMP.csv')

# Compare by category
by_category = df.groupby('category')[['RoBERTa_Plain_score', 
                                       'LLM_V3_FINAL_openai_score']].mean()
print(by_category)

# Find high-disagreement cases
df['disagreement'] = abs(df['RoBERTa_Plain_score'] - df['LLM_V3_FINAL_openai_score'])
high_disagreement = df.nlargest(10, 'disagreement')[['video_id', 'title', 
                                                       'RoBERTa_Plain_score', 
                                                       'LLM_V3_FINAL_openai_score']]
print(high_disagreement)
```

---

## 🛠️ Troubleshooting

### "No module named 'openai'"
```bash
pip install -r requirements.txt
```

### "OPENAI_API_KEY not set"
Create `.env` file with your API key.

### "No matching video_ids found"
Check that video IDs in `human_scores.csv` match those in comparison results.

### "Rate limit exceeded" (OpenAI)
- Add delays: Modify `compare_all_models.py` to add `time.sleep(1)` between calls
- Use fewer samples: `--num-samples 5`
- Use cheaper model: Edit `llm_analyzer.py` to use `gpt-3.5-turbo`

### Memory issues with large datasets
- Process in batches
- Run RoBERTa separately from LLM methods
- Use `--num-samples` to limit size

---

## 💡 Tips & Best Practices

### For Testing
1. **Start small**: Use `--quick-test` first
2. **Check one video in detail**: Look at JSON results to understand outputs
3. **Test with known examples**: Create a mini eval set with obvious positive/negative cases

### For Human Coding
1. **Multiple coders**: Have 2-3 people code same videos, check agreement
2. **Code in batches**: Don't code all at once (fatigue affects scores)
3. **Random order**: Don't code videos in category order (bias)
4. **Blind coding**: Don't see automated scores before coding

### For Production
1. **Choose one method**: Based on validation results and constraints (cost, speed, accuracy)
2. **Document version**: Log which prompt version, model version used
3. **Monitor drift**: Periodically re-validate as content changes
4. **Ensemble if needed**: Combine methods with weighted average

---

## 📚 Next Steps

1. ✅ Run comparison on small sample
2. ✅ Review results in Excel
3. ✅ Code 20-30 videos manually
4. ✅ Run validation
5. ✅ Choose best method for your needs
6. ✅ Scale up to full dataset

For detailed technical explanations, see:
- `ANALYSIS_MECHANISMS_EXPLAINED.md` - How each method works
- `compare_all_models.py` - Source code with comments
- `validate_against_human.py` - Validation methodology

---

## 🆘 Need Help?

**Common Questions:**
- "Which method should I use?" → Run validation first!
- "Is LLM worth the cost?" → Depends on your accuracy needs
- "Can I use without API keys?" → Yes, RoBERTa methods are free
- "How do I cite this?" → See `ANALYSIS_MECHANISMS_EXPLAINED.md`

---

*Last Updated: 2025-11-07*

