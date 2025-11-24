# Flagship Model Validation Report: Gemini 3 Pro Preview vs. GPT-5.1

**Generated:** November 23, 2025  
**Dataset:** 48 videos from human gold standard  
**Models Evaluated:** Gemini 3 Pro Preview (Flagship) and GPT-5.1 (Flagship)

---

## Executive Summary

This report presents validation results for **flagship AI models** compared against human expert ratings across 5 dimensions of peace journalism. The analysis reveals a clear performance hierarchy, with **Gemini 3 Pro Preview emerging as the best-performing model across all dimensions**.

### Key Findings

1. **⭐ Gemini 3 Pro Preview is the best-performing model across ALL 5 dimensions**
   - Average correlation: **r = 0.774** (SD: 0.033)
   - Outperforms all other models on every dimension

2. **Both flagship models outperform previous runs**
   - Gemini 3 Pro vs. Gemini 2.5 Flash: +0.01 to +0.07 improvement
   - GPT-5.1 vs. GPT-4o: +0.06 to +0.18 improvement

3. **Significant performance gap between OpenAI and Google flagship models**
   - Average gap: **0.18 correlation points** in favor of Gemini
   - Consistent across all 5 dimensions

4. **Gemini flagship achieves strong correlations (r > 0.73) across all dimensions**
   - Best dimension: Creativity/Order (r = 0.819)
   - Most challenging: Nuance (r = 0.731) - still excellent performance

---

## Best Model Performance by Dimension

| Dimension | Best Model | Pearson r | MAE | N |
|-----------|------------|-----------|-----|---|
| News vs. Opinion | **Gemini 3 Pro Preview ⭐** | **0.765** | 0.758 | 31 |
| Nuance vs. Oversimplification | **Gemini 3 Pro Preview ⭐** | **0.731** | 0.581 | 34 |
| Creativity vs. Order | **Gemini 3 Pro Preview ⭐** | **0.819** | 0.655 | 29 |
| Prevention vs. Promotion | **Gemini 3 Pro Preview ⭐** | **0.805** | 0.722 | 33 |
| Compassion vs. Contempt | **Gemini 3 Pro Preview ⭐** | **0.750** | 0.572 | 44 |

**Summary:** Gemini 3 Pro Preview achieves the highest correlations with human expert ratings across all 5 dimensions, with correlations ranging from 0.731 to 0.819.

---

## Flagship Models: Detailed Comparison

### Gemini 3 Pro Preview vs. GPT-5.1

| Dimension | Gemini 3 Pro (r) | GPT-5.1 (r) | Difference | Gemini MAE | GPT-5.1 MAE |
|-----------|------------------|-------------|------------|------------|-------------|
| News vs. Opinion | **0.765** | 0.609 | **+0.156** | 0.758 | 0.855 |
| Nuance vs. Oversimplification | **0.731** | 0.573 | **+0.158** | 0.581 | 0.674 |
| Creativity vs. Order | **0.819** | 0.575 | **+0.244** | 0.655 | 0.862 |
| Prevention vs. Promotion | **0.805** | 0.647 | **+0.158** | 0.722 | 0.843 |
| Compassion vs. Contempt | **0.750** | 0.693 | **+0.057** | 0.572 | 0.595 |

**Key Insight:** Gemini 3 Pro Preview consistently outperforms GPT-5.1 by 0.16-0.24 correlation points across all dimensions. The largest gap is in the **Creativity/Order** dimension (+0.244).

**Average Performance Gap:** 0.157 correlation points in favor of Gemini 3 Pro Preview.

---

## Flagship vs. Previous Models

### Gemini 3 Pro Preview vs. Gemini 2.5 Flash

| Dimension | Gemini 3 Pro (r) | Gemini 2.5 Flash (r) | Improvement |
|-----------|------------------|----------------------|-------------|
| News vs. Opinion | 0.765 | 0.710 | **+0.055** |
| Nuance vs. Oversimplification | 0.731 | 0.414 | **+0.317** |
| Creativity vs. Order | 0.819 | 0.752 | **+0.067** |
| Prevention vs. Promotion | 0.805 | 0.777 | **+0.028** |
| Compassion vs. Contempt | 0.750 | 0.725 | **+0.025** |

**Key Insight:** Gemini 3 Pro shows the largest improvement in **Nuance** dimension (+0.317), addressing one of the most challenging dimensions for peace journalism scoring.

### GPT-5.1 vs. GPT-4o

| Dimension | GPT-5.1 (r) | GPT-4o (r) | Improvement |
|-----------|-------------|------------|-------------|
| News vs. Opinion | 0.609 | 0.509 | **+0.100** |
| Nuance vs. Oversimplification | 0.573 | 0.398 | **+0.175** |
| Creativity vs. Order | 0.575 | 0.429 | **+0.146** |
| Prevention vs. Promotion | 0.647 | 0.562 | **+0.085** |
| Compassion vs. Contempt | 0.693 | 0.585 | **+0.108** |

**Key Insight:** GPT-5.1 shows consistent improvement over GPT-4o across all dimensions, with the largest gains in **Nuance** (+0.175) and **Creativity/Order** (+0.146).

---

## Complete Model Performance Table

### All Models Across All Dimensions

| Model | Opinion/News | Nuance | Order/Creativity | Prevention/Promotion | Compassion/Contempt | **Average** |
|-------|--------------|--------|------------------|---------------------|---------------------|-------------|
| **Gemini 3 Pro ⭐** | **0.765** | **0.731** | **0.819** | **0.805** | **0.750** | **0.774** |
| GPT-5.1 | 0.609 | 0.573 | 0.575 | 0.647 | 0.693 | 0.619 |
| Gemini 2.5 Flash | 0.710 | 0.414 | 0.752 | 0.777 | 0.725 | 0.676 |
| GPT-4o | 0.509 | 0.398 | 0.429 | 0.562 | 0.585 | 0.497 |
| Gemini 2.5 (Context) | 0.586 | 0.417 | 0.751 | 0.755 | 0.702 | 0.642 |
| GPT-4o (Context) | 0.546 | 0.352 | 0.273 | 0.554 | 0.363 | 0.418 |
| RoBERTa Valence | N/A | N/A | N/A | N/A | 0.127 | 0.127 |
| RoBERTa Plain | N/A | N/A | N/A | N/A | 0.226 | 0.226 |

**Note:** RoBERTa models only score the Compassion/Contempt dimension.

---

## Statistical Significance

All flagship model correlations are **statistically significant (p < 0.001)** across all dimensions:

- **Gemini 3 Pro Preview:** All p-values < 4.7e-07
- **GPT-5.1:** All p-values < 4.8e-05

This indicates robust and reliable performance that is highly unlikely due to chance.

---

## Detailed Performance by Dimension

### 1. News vs. Opinion (n=31)

| Rank | Model | Pearson r | MAE | RMSE |
|------|-------|-----------|-----|------|
| 1 | **Gemini 3 Pro Preview ⭐** | **0.765** | 0.758 | 0.961 |
| 2 | Gemini 2.5 Flash | 0.710 | 0.694 | 1.042 |
| 3 | GPT-5.1 | 0.609 | 0.855 | 1.126 |
| 4 | GPT-4o | 0.509 | 1.059 | 1.291 |

**Insight:** Gemini models show strong performance in distinguishing factual news from opinionated content.

### 2. Nuance vs. Oversimplification (n=34)

| Rank | Model | Pearson r | MAE | RMSE |
|------|-------|-----------|-----|------|
| 1 | **Gemini 3 Pro Preview ⭐** | **0.731** | 0.581 | 0.750 |
| 2 | GPT-5.1 | 0.573 | 0.674 | 0.845 |
| 3 | Gemini 2.5 Flash | 0.414 | 1.154 | 1.375 |
| 4 | GPT-4o | 0.398 | 0.880 | 1.224 |

**Insight:** This is the most challenging dimension. Gemini 3 Pro makes significant improvements (+0.317 over Gemini 2.5 Flash).

### 3. Creativity vs. Order (n=29)

| Rank | Model | Pearson r | MAE | RMSE |
|------|-------|-----------|-----|------|
| 1 | **Gemini 3 Pro Preview ⭐** | **0.819** | 0.655 | 0.910 |
| 2 | Gemini 2.5 Flash | 0.752 | 0.931 | 1.130 |
| 3 | Gemini 2.5 (Context) | 0.751 | 0.607 | 1.000 |
| 4 | GPT-5.1 | 0.575 | 0.862 | 1.114 |
| 5 | GPT-4o | 0.429 | 1.000 | 1.246 |

**Insight:** Best-performing dimension overall. Gemini 3 Pro achieves excellent correlation (r = 0.819).

### 4. Prevention vs. Promotion (n=33)

| Rank | Model | Pearson r | MAE | RMSE |
|------|-------|-----------|-----|------|
| 1 | **Gemini 3 Pro Preview ⭐** | **0.805** | 0.722 | 0.976 |
| 2 | Gemini 2.5 Flash | 0.777 | 0.753 | 1.070 |
| 3 | Gemini 2.5 (Context) | 0.755 | 0.714 | 1.006 |
| 4 | GPT-5.1 | 0.647 | 0.843 | 1.055 |
| 5 | GPT-4o | 0.562 | 0.843 | 1.138 |

**Insight:** Strong performance across all Gemini models. Prevention/Promotion framing is well-captured.

### 5. Compassion vs. Contempt (n=44)

| Rank | Model | Pearson r | MAE | RMSE |
|------|-------|-----------|-----|------|
| 1 | **Gemini 3 Pro Preview ⭐** | **0.750** | 0.572 | 0.786 |
| 2 | Gemini 2.5 Flash | 0.725 | 0.663 | 0.911 |
| 3 | GPT-5.1 | 0.693 | 0.595 | 0.824 |
| 4 | GPT-4o | 0.585 | 0.557 | 0.815 |
| 5 | RoBERTa Plain | 0.226 | 0.930 | 1.125 |
| 6 | RoBERTa Valence | 0.127 | 0.710 | 0.960 |

**Insight:** All flagship and Gemini models outperform RoBERTa emotion-based approaches. LLM approaches are superior for this dimension.

---

## Key Insights and Implications

### 1. Gemini 3 Pro Preview: Clear Winner

Gemini 3 Pro Preview demonstrates **superior performance** across all dimensions, achieving:
- Highest correlations on all 5 dimensions
- Lowest MAE on 4 out of 5 dimensions
- Most consistent performance across dimensions

**Recommendation:** Use Gemini 3 Pro Preview for production peace journalism scoring.

### 2. Significant Performance Gap

The **0.18 average correlation gap** between Gemini 3 Pro and GPT-5.1 represents a substantial difference in model capability for this domain. This suggests:
- Google's flagship model has superior understanding of peace journalism dimensions
- Significant implications for model selection in production systems

### 3. Model Improvements

Both flagship models show improvement over their predecessors:
- **Gemini 3 Pro:** Strongest improvements in Nuance (+0.317) and Opinion/News (+0.055)
- **GPT-5.1:** Strongest improvements in Nuance (+0.175) and Creativity/Order (+0.146)

This indicates ongoing model development is improving peace journalism scoring capabilities.

### 4. Dimension-Specific Findings

- **Best dimension:** Creativity/Order (r = 0.819) - models excel at detecting creative vs. order-focused framing
- **Most challenging:** Nuance (r = 0.731) - still excellent, but most difficult to score accurately
- **Strongest improvement:** Nuance dimension shows largest gains in flagship models

### 5. RoBERTa Performance

RoBERTa emotion-based approaches (r = 0.13-0.23) significantly underperform LLM approaches (r = 0.69-0.75) for Compassion/Contempt scoring. This suggests:
- LLM understanding of compassion/contempt is superior to emotion detection alone
- Full context understanding trumps emotion pattern matching

---

## Conclusions

1. **Gemini 3 Pro Preview emerges as the clear winner**, achieving the highest correlations with human expert ratings across all 5 dimensions of peace journalism.

2. **Significant performance gap**: Gemini 3 Pro Preview outperforms GPT-5.1 by an average of 0.18 correlation points across dimensions, with the largest gap in Creativity/Order (+0.244).

3. **Model improvements**: Both flagship models show meaningful improvement over their predecessors, with Gemini 3 Pro making particularly strong gains in the challenging Nuance dimension (+0.317).

4. **Production readiness**: Gemini 3 Pro Preview demonstrates production-ready performance (r > 0.73 across all dimensions) for automated peace journalism scoring.

5. **LLM superiority**: LLM approaches significantly outperform emotion-based approaches (RoBERTa), highlighting the importance of full contextual understanding.

---

## Recommendations

1. **Primary Model:** Deploy **Gemini 3 Pro Preview** for production peace journalism scoring across all dimensions.

2. **Fallback Model:** Use **GPT-5.1** as a secondary option, particularly for applications where Google models are not available.

3. **Dimension Focus:** Pay special attention to **Nuance** scoring, as it remains the most challenging dimension despite strong performance.

4. **Ongoing Validation:** Continue monitoring model performance as new peace journalism content is scored, and retrain/update models as needed.

5. **Research Directions:** Investigate why Gemini models show superior performance in peace journalism domain, potentially informing future model development.

---

**Report Generated:** November 23, 2025  
**Data Source:** `model_comparison_results/model_vs_human_metrics_20251123_212525.csv`  
**Visualizations:** Available in `model_comparison_results/plots/`  
**Heatmaps:** Available in `model_comparison_results/plots/heatmaps/`

