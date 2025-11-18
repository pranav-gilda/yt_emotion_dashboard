# Analysis Mechanisms Comparison Guide

This document explains the 4 different analysis mechanisms available in this codebase for scoring transcript "peacefulness" or sentiment.

---

## Overview of Methods

| Method | File | Input | Output Scale | Key Features |
|--------|------|-------|--------------|--------------|
| **RoBERTa Plain** | `models.py` | Transcript text | 0-5 (normalized) | 28 emotion probabilities, respect vs contempt |
| **RoBERTa Valence Scaled** | `scale.py` | Transcript text | 1-5 (maps to 0-5) | Weighted valence scoring with emotion mapping |
| **LLM V1** | `llm_analyzer.py` | Transcript text | -5 to +5 (maps to 0-5) | Pure LLM reasoning across 5 dimensions |
| **LLM V3_FINAL** | `llm_analyzer.py` | Transcript + RoBERTa | 0-100 (maps to 0-5) | Combined RoBERTa emotions + LLM reasoning |

---

## 1. RoBERTa Plain (Respect/Contempt Scoring)

### Location
`models.py` - function `run_go_emotions()`

### How It Works

1. **Emotion Detection**: Uses HuggingFace's `SamLowe/roberta-base-go_emotions` model to detect 28 emotions in the text
2. **Sentence-by-Sentence**: Splits transcript into sentences and analyzes each
3. **Averaging**: Calculates average probability for each emotion across all sentences
4. **Respect vs Contempt**: 
   - **Respect emotions**: admiration, approval, caring
   - **Contempt emotions**: annoyance, disapproval, disgust
5. **Net Score**: Average respect score minus average contempt score

### Output Format
```python
{
    "average_scores": {
        "admiration": 0.234,
        "anger": 0.045,
        # ... all 28 emotions
    },
    "dominant_emotion": "neutral",
    "dominant_emotion_score": 0.456,
    "dominant_attitude_emotion": "admiration",
    "dominant_attitude_score": 0.234
}
```

### Normalization to 0-5 Scale
```python
avg_respect = mean([admiration, approval, caring])
avg_contempt = mean([annoyance, disapproval, disgust])
net_score = avg_respect - avg_contempt  # ranges -1 to +1
score_0_5 = 2.5 + (net_score * 2.5)     # map to 0-5
```

### Strengths
- ✅ Fast and deterministic
- ✅ No API costs
- ✅ Provides granular emotion breakdown
- ✅ Transparent methodology

### Limitations
- ❌ Simplistic respect/contempt dichotomy
- ❌ Doesn't capture nuance or context
- ❌ Fixed to pre-trained emotion categories

---

## 2. RoBERTa Valence Scaled

### Location
`scale.py` - function `run_valence_analysis()`

### How It Works

1. **Uses RoBERTa**: Calls `run_go_emotions()` to get 28 emotion probabilities
2. **Valence Mapping**: Each emotion has a pre-defined valence weight:
   - **Highly Positive (+1.0)**: joy, love, admiration, gratitude, pride, excitement
   - **Mildly Positive (+0.5)**: approval, caring, optimism, relief, amusement, curiosity
   - **Neutral (0.0)**: neutral, realization, surprise, confusion
   - **Mildly Negative (-0.5)**: annoyance, disapproval, disappointment, nervousness, remorse, desire
   - **Highly Negative (-1.0)**: anger, disgust, fear, sadness, grief, embarrassment

3. **Weighted Score Calculation**:
   ```
   score_100 = Σ [(probability × 100) × valence]
   ```
   This produces a score from -100 to +100

4. **Map to Human Scale (1-5)**:
   ```
   score_1_5 = 3 + (score_100 / 50)
   ```
   Where 1 = very negative, 3 = neutral, 5 = very positive

### Output Format
```python
{
    "transcript": "...",
    "valence_score_100": 24.5,
    "human_rater_score_1_to_5": 3.49,
    "roberta_dominant_emotion": "joy",
    "roberta_average_scores": {...}
}
```

### Normalization to 0-5 Scale
```python
# Subtract 1 to shift from 1-5 to 0-5
score_0_5 = score_1_5 - 1
```

### Strengths
- ✅ More sophisticated than simple respect/contempt
- ✅ Weighted approach considers emotion intensity
- ✅ Fast and deterministic
- ✅ Scales well to large datasets

### Limitations
- ❌ Valence mapping is subjective (why is "desire" negative?)
- ❌ Still based on pre-trained categories
- ❌ No contextual understanding

---

## 3. LLM V1 (Plain Prompt)

### Location
`llm_analyzer.py` - `SYSTEM_PROMPT_V1` with `analyze_transcript_with_llm(prompt_version="v1")`

### How It Works

1. **Pure LLM Reasoning**: Sends transcript to GPT-4 or Gemini with no additional context
2. **5 Dimensions Scored**: Each on -5 (low peace) to +5 (high peace) scale:
   - **Nuance**: Multiple perspectives (+5) vs one-sided (-5)
   - **Creativity vs Order**: Human-centered (+5) vs control/authority (-5)
   - **Safety vs Threat**: Stability (+5) vs crisis/danger (-5)
   - **Compassion vs Contempt**: Inclusive (+5) vs dehumanizing (-5)
   - **Reporting vs Opinion**: Objective (+5) vs subjective (-5)
3. **JSON Response**: LLM provides score + rationale for each dimension

### Output Format
```python
{
    "nuance": {
        "score": 2,
        "rationale": "Text presents some context but leans toward one viewpoint"
    },
    "creativity_vs_order": {...},
    "safety_vs_threat": {...},
    "compassion_vs_contempt": {
        "score": -3,
        "rationale": "Language is divisive with contemptuous framing"
    },
    "reporting_vs_opinion": {...}
}
```

### Normalization to 0-5 Scale
We focus on the **compassion_vs_contempt** dimension:
```python
score_0_5 = (score + 5) / 2  # map from -5..+5 to 0..5
```

### Strengths
- ✅ Sophisticated contextual understanding
- ✅ Multi-dimensional analysis
- ✅ Provides interpretable rationales
- ✅ Can understand sarcasm, irony, implicit meaning

### Limitations
- ❌ Expensive (API costs)
- ❌ Slow (requires API calls)
- ❌ Non-deterministic (different results on same input)
- ❌ Requires API keys

---

## 4. LLM V3_FINAL (RoBERTa + LLM Combined)

### Location
`llm_analyzer.py` - `SYSTEM_PROMPT_V3_FINAL` with `analyze_transcript_with_llm(prompt_version="v3_final")`

### How It Works

1. **Two-Step Process**:
   - Step 1: Run RoBERTa emotion analysis (`run_go_emotions()`)
   - Step 2: Pass transcript + emotion profile to LLM
   
2. **Enhanced Prompt**: LLM receives:
   ```
   Transcript: [full text]
   
   Emotional Profile Context:
   {
     "admiration": 0.234,
     "anger": 0.045,
     ...
   }
   ```

3. **LLM Task**:
   - Identify top 3 non-neutral emotions
   - Score 4 dimensions (note: different scales than V1):
     - **Compassion vs Contempt**: 0-100 scale
     - **Creativity vs Order**: -5 to +5
     - **Safety vs Threat**: -5 to +5
     - **Reporting vs Opinion**: -5 to +5
   - Must reference emotion scores in rationales

### Output Format
```python
{
    "compassion_vs_contempt": {
        "score": 35,
        "rationale": "Low score due to strong presence of disapproval (0.23) and anger (0.15)..."
    },
    "creativity_vs_order": {...},
    "safety_vs_threat": {...},
    "reporting_vs_opinion": {...},
    "top_emotions": [
        {"emotion": "disapproval", "score": 0.23},
        {"emotion": "anger", "score": 0.15},
        {"emotion": "concern", "score": 0.12}
    ]
}
```

### Normalization to 0-5 Scale
```python
score_0_5 = compassion_score / 20  # map from 0..100 to 0..5
```

### Strengths
- ✅ **Best of both worlds**: Quantitative emotions + contextual reasoning
- ✅ LLM explicitly grounds reasoning in emotion data
- ✅ More consistent than pure LLM (emotion anchor)
- ✅ Provides transparency (top emotions listed)

### Limitations
- ❌ Most expensive (RoBERTa + LLM API)
- ❌ Slowest method
- ❌ Complexity in debugging (two-stage process)

---

## Comparison Matrix

| Aspect | RoBERTa Plain | RoBERTa Valence | LLM V1 | LLM V3_FINAL |
|--------|---------------|-----------------|---------|---------------|
| **Speed** | ⚡⚡⚡ | ⚡⚡⚡ | ⚡ | ⚡ |
| **Cost** | Free | Free | $$ | $$$ |
| **Determinism** | ✅ Yes | ✅ Yes | ❌ No | ❌ No |
| **Interpretability** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Context Awareness** | ⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Reproducibility** | ✅ 100% | ✅ 100% | ❌ ~80% | ❌ ~85% |
| **Offline Capable** | ✅ Yes | ✅ Yes | ❌ No | ❌ No |

---

## When to Use Each Method

### Use RoBERTa Plain when:
- You need **fast, free** analysis
- You want **deterministic** results
- You're analyzing **large datasets** (1000s of transcripts)
- You need to understand **emotion breakdown**
- Simple respect/contempt metric is sufficient

### Use RoBERTa Valence Scaled when:
- You want a more **nuanced** quantitative approach than plain RoBERTa
- You trust the predefined **valence mappings**
- You need **fast, scalable** analysis with better granularity
- You want results on a **1-5 human-like scale**

### Use LLM V1 when:
- You need **deep contextual** understanding
- You want **multi-dimensional** analysis
- You need **interpretable rationales**
- Budget allows for **API costs**
- Dataset is **small to medium** (<100 transcripts)

### Use LLM V3_FINAL when:
- You want **best accuracy**
- You need both **quantitative rigor** (emotions) and **qualitative insight** (LLM)
- You want LLM reasoning **grounded in data**
- You're doing **final validation** or **research publication**
- Budget allows for API costs

---

## Running Comparisons

### Quick Test (2 samples)
```bash
python compare_all_models.py --quick-test
```

### Analyze Specific Videos
```bash
python compare_all_models.py --video-ids _GXNJ3V9lzg DK9TkLPJY6w
```

### Analyze Random Sample
```bash
python compare_all_models.py --num-samples 10
```

### Analyze ALL Transcripts
```bash
python compare_all_models.py
```

### Output Files
All results are saved to `comparison_results/`:
- `detailed_comparison_TIMESTAMP.json` - Full raw results
- `score_comparison_TIMESTAMP.csv` - Score comparison table
- `score_comparison_TIMESTAMP.xlsx` - Formatted Excel with color scales

---

## Human Ground Truth Validation

Once you have human-coded scores, use `validate_against_human.py` to:
1. Load human scores
2. Compare against all 4 methods
3. Calculate MAE, correlation, and agreement
4. Identify which method best matches human judgment

See `validate_against_human.py` for details (to be created).

---

## Future Work

### Potential Improvements
1. **Ensemble Method**: Combine multiple methods with learned weights
2. **Fine-tuned RoBERTa**: Train on peace research specific corpus
3. **Prompt Engineering**: Optimize LLM prompts with few-shot examples
4. **Cost Optimization**: Use smaller/cheaper LLMs (GPT-3.5, Gemini Flash)
5. **Caching**: Cache RoBERTa results to avoid recomputation in V3

### Research Questions
- Which method correlates best with human coders?
- Does V3_FINAL justify its cost vs V1?
- Can we predict which method works best for which content type?
- What's the optimal ensemble weighting?

---

## Contact & Citations

If using these methods in research, please cite appropriately:
- RoBERTa model: [SamLowe/roberta-base-go_emotions](https://huggingface.co/SamLowe/roberta-base-go_emotions)
- Original Go Emotions: Demszky et al. (2020) - Google Research

---

*Last Updated: 2025-11-07*

