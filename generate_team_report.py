"""
Generate comprehensive team meeting report from all model comparison results.
Formats data for presentation and paper publication.
"""

import pandas as pd
import numpy as np
import json
import os
import logging
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Input directories
MODEL_SCORES_DIR = "model_scores_gold_standard"
COMPARISON_RESULTS_DIR = "model_comparison_results"
VALIDATION_RESULTS_DIR = "validation_results"
OUTPUT_DIR = "team_report"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Dimension names for display
DIMENSION_DISPLAY_NAMES = {
    'opinion_news': 'News vs. Opinion',
    'nuance': 'Nuance vs. Oversimplification',
    'order_creativity': 'Creativity vs. Order',
    'prevention_promotion': 'Prevention vs. Promotion',
    'compassion_contempt': 'Compassion vs. Contempt'
}

METHOD_DISPLAY_NAMES = {
    'openai_no_roberta': 'OpenAI GPT-4o (No Context)',
    'openai_with_roberta': 'OpenAI GPT-4o (With RoBERTa)',
    'openai_flagship': 'OpenAI GPT-5.1 (Flagship)',
    'gemini_no_roberta': 'Google Gemini 2.5 Flash (No Context)',
    'gemini_with_roberta': 'Google Gemini 2.5 Flash (With RoBERTa)',
    'gemini_flagship': 'Google Gemini 3 Pro Preview (Flagship) ⭐',
    'roberta_plain': 'RoBERTa Plain (Emotion-based)',
    'roberta_valence': 'RoBERTa Valence (Weighted)'
}

# ============================================================================
# LOAD DATA
# ============================================================================

def load_latest_files():
    """Load the most recent comparison results."""
    # Find latest comparison summary
    summary_files = [f for f in os.listdir(COMPARISON_RESULTS_DIR) 
                     if f.startswith('comparison_summary_') and f.endswith('.json')]
    if not summary_files:
        raise FileNotFoundError("No comparison summary found")
    
    summary_files.sort(reverse=True)
    latest_summary = os.path.join(COMPARISON_RESULTS_DIR, summary_files[0])
    
    # Find latest metrics CSV
    metrics_files = [f for f in os.listdir(COMPARISON_RESULTS_DIR)
                     if f.startswith('model_vs_human_metrics_') and f.endswith('.csv')]
    metrics_files.sort(reverse=True)
    latest_metrics = os.path.join(COMPARISON_RESULTS_DIR, metrics_files[0])
    
    # Find latest merged data
    merged_files = [f for f in os.listdir(COMPARISON_RESULTS_DIR)
                    if f.startswith('merged_human_model_scores_') and f.endswith('.csv')]
    merged_files.sort(reverse=True)
    latest_merged = os.path.join(COMPARISON_RESULTS_DIR, merged_files[0])
    
    logging.info(f"Loading latest results:")
    logging.info(f"  Summary: {latest_summary}")
    logging.info(f"  Metrics: {latest_metrics}")
    logging.info(f"  Merged: {latest_merged}")
    
    with open(latest_summary, 'r') as f:
        summary = json.load(f)
    
    metrics_df = pd.read_csv(latest_metrics)
    merged_df = pd.read_csv(latest_merged)
    
    return summary, metrics_df, merged_df

def load_human_stats():
    """Load human score statistics."""
    human_scores_path = os.path.join(VALIDATION_RESULTS_DIR, "human_scores_cleaned.csv")
    if os.path.exists(human_scores_path):
        df = pd.read_csv(human_scores_path)
        return df
    return None

# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_executive_summary(summary: Dict, metrics_df: pd.DataFrame) -> str:
    """Generate executive summary section."""
    lines = []
    lines.append("# Executive Summary")
    lines.append("")
    lines.append(f"**Date:** {datetime.now().strftime('%B %d, %Y')}")
    lines.append(f"**Total Videos Analyzed:** {summary.get('total_videos', 'N/A')}")
    lines.append(f"**Total Model Comparisons:** {summary.get('total_comparisons', 'N/A')}")
    lines.append("")
    lines.append("## Key Findings")
    lines.append("")
    
    # Best methods per dimension
    best_methods = summary.get('best_method_per_dimension', {})
    if best_methods:
        lines.append("### Best Performing Models by Dimension")
        lines.append("")
        lines.append("| Dimension | Best Model | Pearson r | MAE |")
        lines.append("|-----------|------------|-----------|-----|")
        
        for dim, info in best_methods.items():
            dim_name = DIMENSION_DISPLAY_NAMES.get(dim, dim)
            method_name = METHOD_DISPLAY_NAMES.get(info['method'], info['method'])
            r = info.get('pearson_r', 0)
            mae = info.get('mae', 0)
            lines.append(f"| {dim_name} | {method_name} | {r:.3f} | {mae:.3f} |")
    
    lines.append("")
    lines.append("### Overall Performance Highlights")
    lines.append("")
    
    # Calculate overall stats
    all_pearson = metrics_df['pearson_r'].dropna()
    all_mae = metrics_df['mae'].dropna()
    
    if len(all_pearson) > 0:
        lines.append(f"- **Average Pearson Correlation:** {all_pearson.mean():.3f} (SD: {all_pearson.std():.3f})")
        lines.append(f"- **Range of Correlations:** {all_pearson.min():.3f} to {all_pearson.max():.3f}")
        lines.append(f"- **Average MAE:** {all_mae.mean():.3f} (SD: {all_mae.std():.3f})")
        lines.append(f"- **Strongest Correlation:** {all_pearson.max():.3f}")
        lines.append(f"- **Weakest Correlation:** {all_pearson.min():.3f}")
    
    return "\n".join(lines)

def generate_detailed_results(metrics_df: pd.DataFrame) -> str:
    """Generate detailed results section."""
    lines = []
    lines.append("# Detailed Results")
    lines.append("")
    
    # Group by dimension
    for dimension in metrics_df['dimension'].unique():
        dim_name = DIMENSION_DISPLAY_NAMES.get(dimension, dimension)
        lines.append(f"## {dim_name}")
        lines.append("")
        
        dim_metrics = metrics_df[metrics_df['dimension'] == dimension].copy()
        dim_metrics = dim_metrics.sort_values('pearson_r', ascending=False)
        
        lines.append("| Model | N | Pearson r | p-value | Spearman r | MAE | RMSE |")
        lines.append("|-------|---|-----------|--------|------------|-----|------|")
        
        for _, row in dim_metrics.iterrows():
            method_name = METHOD_DISPLAY_NAMES.get(row['method'], row['method'])
            n = int(row['n']) if not pd.isna(row['n']) else 0
            pearson_r = row['pearson_r'] if not pd.isna(row['pearson_r']) else 0
            pearson_p = row['pearson_p'] if not pd.isna(row['pearson_p']) else 1.0
            spearman_r = row['spearman_r'] if not pd.isna(row['spearman_r']) else 0
            mae = row['mae'] if not pd.isna(row['mae']) else 0
            rmse = row['rmse'] if not pd.isna(row['rmse']) else 0
            
            # Format p-value
            if pearson_p < 0.001:
                p_str = "< 0.001"
            else:
                p_str = f"{pearson_p:.3f}"
            
            lines.append(f"| {method_name} | {n} | {pearson_r:.3f} | {p_str} | {spearman_r:.3f} | {mae:.3f} | {rmse:.3f} |")
        
        lines.append("")
    
    return "\n".join(lines)

def generate_methodology_section() -> str:
    """Generate methodology section."""
    lines = []
    lines.append("# Methodology")
    lines.append("")
    lines.append("## Models Evaluated")
    lines.append("")
    
    for method_key, method_name in METHOD_DISPLAY_NAMES.items():
        lines.append(f"### {method_name}")
        lines.append("")
        if 'OpenAI' in method_name:
            lines.append("- **Provider:** OpenAI")
            lines.append("- **Model:** GPT-4o")
            if 'With RoBERTa' in method_name:
                lines.append("- **Context:** Enhanced with RoBERTa emotion scores")
            else:
                lines.append("- **Context:** Transcript only")
        elif 'Gemini' in method_name:
            lines.append("- **Provider:** Google")
            lines.append("- **Model:** Gemini 2.5 Flash")
            if 'With RoBERTa' in method_name:
                lines.append("- **Context:** Enhanced with RoBERTa emotion scores")
            else:
                lines.append("- **Context:** Transcript only")
        elif 'RoBERTa' in method_name:
            lines.append("- **Provider:** Hugging Face")
            lines.append("- **Model:** RoBERTa-base + GoEmotions")
            if 'Valence' in method_name:
                lines.append("- **Method:** Weighted valence scoring")
            else:
                lines.append("- **Method:** Emotion-based scoring")
        lines.append("")
    
    lines.append("## Dimensions Evaluated")
    lines.append("")
    for dim_key, dim_name in DIMENSION_DISPLAY_NAMES.items():
        lines.append(f"- **{dim_name}:** Score range 1-5")
    lines.append("")
    
    lines.append("## Evaluation Metrics")
    lines.append("")
    lines.append("- **Pearson Correlation (r):** Linear relationship strength")
    lines.append("- **Spearman Correlation (ρ):** Monotonic relationship strength")
    lines.append("- **Mean Absolute Error (MAE):** Average prediction error")
    lines.append("- **Root Mean Squared Error (RMSE):** Penalizes larger errors")
    lines.append("")
    
    return "\n".join(lines)

def generate_publication_table(metrics_df: pd.DataFrame) -> str:
    """Generate publication-ready table."""
    lines = []
    lines.append("# Publication-Ready Results Table")
    lines.append("")
    lines.append("## Table: Model Performance by Dimension")
    lines.append("")
    
    # Create comprehensive table
    all_dims = sorted(metrics_df['dimension'].unique())
    all_methods = sorted(metrics_df['method'].unique())
    
    lines.append("| Dimension | Model | N | r | p | ρ | MAE | RMSE |")
    lines.append("|-----------|-------|---|---|---|---|-----|------|")
    
    for dim in all_dims:
        dim_metrics = metrics_df[metrics_df['dimension'] == dim].copy()
        dim_metrics = dim_metrics.sort_values('pearson_r', ascending=False)
        
        for _, row in dim_metrics.iterrows():
            dim_name = DIMENSION_DISPLAY_NAMES.get(dim, dim)
            method_name = METHOD_DISPLAY_NAMES.get(row['method'], row['method'])
            n = int(row['n']) if not pd.isna(row['n']) else 0
            r = row['pearson_r'] if not pd.isna(row['pearson_r']) else 0
            p = row['pearson_p'] if not pd.isna(row['pearson_p']) else 1.0
            rho = row['spearman_r'] if not pd.isna(row['spearman_r']) else 0
            mae = row['mae'] if not pd.isna(row['mae']) else 0
            rmse = row['rmse'] if not pd.isna(row['rmse']) else 0
            
            # Format p-value
            if p < 0.001:
                p_str = "< .001"
            elif p < 0.01:
                p_str = f"{p:.3f}"
            else:
                p_str = f"{p:.2f}"
            
            lines.append(f"| {dim_name} | {method_name} | {n} | {r:.3f} | {p_str} | {rho:.3f} | {mae:.3f} | {rmse:.3f} |")
    
    return "\n".join(lines)

def generate_full_report():
    """Generate complete team report."""
    logging.info("="*80)
    logging.info("GENERATING TEAM REPORT")
    logging.info("="*80)
    
    # Load data
    summary, metrics_df, merged_df = load_latest_files()
    human_df = load_human_stats()
    
    # Generate sections
    report_sections = []
    
    report_sections.append("# Model Validation Report: AI Scoring vs. Human Gold Standard")
    report_sections.append("")
    report_sections.append(f"**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    report_sections.append("")
    
    report_sections.append(generate_executive_summary(summary, metrics_df))
    report_sections.append("")
    report_sections.append("---")
    report_sections.append("")
    report_sections.append(generate_methodology_section())
    report_sections.append("")
    report_sections.append("---")
    report_sections.append("")
    report_sections.append(generate_detailed_results(metrics_df))
    report_sections.append("")
    report_sections.append("---")
    report_sections.append("")
    report_sections.append(generate_publication_table(metrics_df))
    
    # Combine all sections
    full_report = "\n".join(report_sections)
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(OUTPUT_DIR, f"team_report_{timestamp}.md")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(full_report)
    
    logging.info(f"\n✓ Full report saved to: {report_path}")
    
    # Also save as HTML for easy viewing
    try:
        import markdown
        html = markdown.markdown(full_report, extensions=['tables', 'fenced_code'])
        html_path = os.path.join(OUTPUT_DIR, f"team_report_{timestamp}.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Model Validation Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; font-weight: bold; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        h3 {{ color: #7f8c8d; }}
    </style>
</head>
<body>
{html}
</body>
</html>""")
        logging.info(f"✓ HTML report saved to: {html_path}")
    except ImportError:
        logging.warning("markdown library not available. Skipping HTML export.")
    
    # Save summary statistics as JSON
    stats = {
        'generation_date': datetime.now().isoformat(),
        'total_videos': summary.get('total_videos'),
        'total_comparisons': summary.get('total_comparisons'),
        'best_methods': summary.get('best_method_per_dimension', {}),
        'overall_stats': {
            'mean_pearson_r': float(metrics_df['pearson_r'].mean()) if len(metrics_df) > 0 else None,
            'std_pearson_r': float(metrics_df['pearson_r'].std()) if len(metrics_df) > 0 else None,
            'mean_mae': float(metrics_df['mae'].mean()) if len(metrics_df) > 0 else None,
            'std_mae': float(metrics_df['mae'].std()) if len(metrics_df) > 0 else None,
        }
    }
    
    stats_path = os.path.join(OUTPUT_DIR, f"summary_stats_{timestamp}.json")
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logging.info(f"✓ Summary statistics saved to: {stats_path}")
    logging.info(f"\n✅ Report generation complete!")
    logging.info(f"   All files saved to: {OUTPUT_DIR}/")
    
    return report_path

if __name__ == "__main__":
    try:
        generate_full_report()
    except Exception as e:
        logging.error(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        raise

