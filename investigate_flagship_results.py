"""
Investigate flagship model results - quick analysis and comparison.
"""

import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
from datetime import datetime

def load_latest_flagship_results():
    """Load the most recent flagship run results."""
    flagship_dir = "model_scores_gold_standard/flagship_run"
    
    # Find latest CSV
    csv_files = sorted([f for f in os.listdir(flagship_dir) if f.startswith("flagship_scores_") and f.endswith(".csv")])
    if not csv_files:
        raise FileNotFoundError("No flagship scores CSV found!")
    
    latest_csv = os.path.join(flagship_dir, csv_files[-1])
    latest_json = latest_csv.replace(".csv", "_detailed.json")
    
    print(f"📊 Loading latest flagship results:")
    print(f"   CSV: {latest_csv}")
    print(f"   JSON: {latest_json}")
    
    df = pd.read_csv(latest_csv)
    
    if os.path.exists(latest_json):
        with open(latest_json, 'r', encoding='utf-8') as f:
            detailed = json.load(f)
    else:
        detailed = None
    
    return df, detailed, latest_csv, latest_json

def summarize_flagship_results(df):
    """Print summary statistics for flagship models."""
    print(f"\n{'='*80}")
    print(f"FLAGSHIP MODEL RESULTS SUMMARY")
    print(f"{'='*80}")
    
    print(f"\n📈 Dataset Overview:")
    print(f"   Total videos processed: {len(df)}")
    print(f"   Videos with OpenAI scores: {df['openai_flagship_opinion_news'].notna().sum()}")
    print(f"   Videos with Gemini scores: {df['gemini_flagship_opinion_news'].notna().sum()}")
    
    # Score statistics per dimension
    dimensions = ['opinion_news', 'nuance', 'order_creativity', 'prevention_promotion', 'compassion_contempt']
    
    print(f"\n📊 Score Statistics by Dimension:")
    print(f"\n{'Dimension':<25} {'OpenAI Mean':<15} {'OpenAI Std':<15} {'Gemini Mean':<15} {'Gemini Std':<15}")
    print(f"{'-'*80}")
    
    for dim in dimensions:
        openai_col = f"openai_flagship_{dim}"
        gemini_col = f"gemini_flagship_{dim}"
        
        if openai_col in df.columns:
            openai_mean = df[openai_col].mean()
            openai_std = df[openai_col].std()
        else:
            openai_mean = openai_std = np.nan
        
        if gemini_col in df.columns:
            gemini_mean = df[gemini_col].mean()
            gemini_std = df[gemini_col].std()
        else:
            gemini_mean = gemini_std = np.nan
        
        print(f"{dim:<25} {openai_mean:>10.2f}     {openai_std:>10.2f}     {gemini_mean:>10.2f}     {gemini_std:>10.2f}")
    
    # Model agreement
    print(f"\n🤝 Model Agreement (Correlation):")
    print(f"{'Dimension':<25} {'Pearson r':<15} {'Mean Diff':<15}")
    print(f"{'-'*55}")
    
    for dim in dimensions:
        openai_col = f"openai_flagship_{dim}"
        gemini_col = f"gemini_flagship_{dim}"
        
        if openai_col in df.columns and gemini_col in df.columns:
            both_valid = df[[openai_col, gemini_col]].dropna()
            if len(both_valid) > 1:
                corr = both_valid[openai_col].corr(both_valid[gemini_col])
                mean_diff = (both_valid[openai_col] - both_valid[gemini_col]).abs().mean()
                print(f"{dim:<25} {corr:>10.3f}     {mean_diff:>10.3f}")
            else:
                print(f"{dim:<25} {'N/A':<15} {'N/A':<15}")
        else:
            print(f"{dim:<25} {'N/A':<15} {'N/A':<15}")

def compare_to_human_scores(df):
    """Compare flagship models to human gold standard."""
    print(f"\n{'='*80}")
    print(f"COMPARISON TO HUMAN GOLD STANDARD")
    print(f"{'='*80}")
    
    # Load human scores
    human_path = "validation_results/human_scores_cleaned.csv"
    if not os.path.exists(human_path):
        print(f"⚠ Human scores not found at {human_path}")
        return None
    
    human_df = pd.read_csv(human_path)
    
    # Merge
    merged = df.merge(human_df, on='video_id', how='inner', suffixes=('_flagship', '_human'))
    print(f"\n📊 Merged {len(merged)} videos (common to both datasets)")
    
    if len(merged) == 0:
        print("⚠ No common videos found!")
        return None
    
    # Dimension mapping
    dim_mapping = {
        'opinion_news': 'news_opinion_score',
        'nuance': 'nuance_score',
        'order_creativity': 'order_creativity_score',
        'prevention_promotion': 'prevention_promotion_score',
        'compassion_contempt': 'contempt_compassion_score'
    }
    
    print(f"\n📈 Correlation with Human Scores:")
    print(f"\n{'Model':<20} {'Dimension':<25} {'Pearson r':<12} {'MAE':<12} {'N':<8}")
    print(f"{'-'*80}")
    
    results = []
    
    for model_prefix in ['openai_flagship', 'gemini_flagship']:
        for dim, human_col in dim_mapping.items():
            model_col = f"{model_prefix}_{dim}"
            
            if model_col not in merged.columns or human_col not in merged.columns:
                continue
            
            # Get valid pairs
            valid = merged[[model_col, human_col]].dropna()
            if len(valid) < 2:
                continue
            
            y_true = valid[human_col].values
            y_pred = valid[model_col].values
            
            # Calculate metrics
            corr = np.corrcoef(y_true, y_pred)[0, 1]
            mae = np.mean(np.abs(y_true - y_pred))
            
            print(f"{model_prefix:<20} {dim:<25} {corr:>10.3f}     {mae:>10.3f}     {len(valid):>5d}")
            
            results.append({
                'model': model_prefix,
                'dimension': dim,
                'pearson_r': corr,
                'mae': mae,
                'n': len(valid)
            })
    
    return pd.DataFrame(results)

def compare_to_previous_runs(df):
    """Compare flagship models to previous run results."""
    print(f"\n{'='*80}")
    print(f"COMPARISON TO PREVIOUS RUNS")
    print(f"{'='*80}")
    
    # Find previous run files
    run_dirs = [d for d in os.listdir("model_scores_gold_standard") if d.startswith("run_")]
    if not run_dirs:
        print("⚠ No previous runs found")
        return None
    
    # Load latest previous run
    latest_run = sorted(run_dirs)[-1]
    run_path = f"model_scores_gold_standard/{latest_run}"
    
    csv_files = sorted([f for f in os.listdir(run_path) if f.startswith("model_scores_") and f.endswith(".csv")])
    if not csv_files:
        print(f"⚠ No CSV files found in {run_path}")
        return None
    
    prev_csv = os.path.join(run_path, csv_files[-1])
    prev_df = pd.read_csv(prev_csv)
    
    print(f"\n📊 Comparing to: {prev_csv}")
    print(f"   Flagship videos: {len(df)}")
    print(f"   Previous run videos: {len(prev_df)}")
    
    # Merge on video_id
    merged = df.merge(prev_df, on='video_id', how='inner', suffixes=('_flagship', '_prev'))
    print(f"   Common videos: {len(merged)}")
    
    if len(merged) == 0:
        print("⚠ No common videos found!")
        return None
    
    # Compare flagship OpenAI to previous OpenAI
    print(f"\n📈 Flagship vs Previous Run (OpenAI):")
    print(f"{'Dimension':<25} {'Flagship Mean':<15} {'Prev Mean':<15} {'Diff':<15}")
    print(f"{'-'*70}")
    
    dimensions = ['opinion_news', 'nuance', 'order_creativity', 'prevention_promotion', 'compassion_contempt']
    
    for dim in dimensions:
        flagship_col = f"openai_flagship_{dim}"
        prev_col = f"openai_{dim}"
        
        if flagship_col in merged.columns and prev_col in merged.columns:
            flagship_mean = merged[flagship_col].mean()
            prev_mean = merged[prev_col].mean()
            diff = flagship_mean - prev_mean
            print(f"{dim:<25} {flagship_mean:>12.2f}     {prev_mean:>12.2f}     {diff:>12.2f}")
    
    # Compare flagship Gemini to previous Gemini
    print(f"\n📈 Flagship vs Previous Run (Gemini):")
    print(f"{'Dimension':<25} {'Flagship Mean':<15} {'Prev Mean':<15} {'Diff':<15}")
    print(f"{'-'*70}")
    
    for dim in dimensions:
        flagship_col = f"gemini_flagship_{dim}"
        prev_col = f"gemini_{dim}"
        
        if flagship_col in merged.columns and prev_col in merged.columns:
            flagship_mean = merged[flagship_col].mean()
            prev_mean = merged[prev_col].mean()
            diff = flagship_mean - prev_mean
            print(f"{dim:<25} {flagship_mean:>12.2f}     {prev_mean:>12.2f}     {diff:>12.2f}")

def main():
    """Main investigation function."""
    print(f"\n{'='*80}")
    print(f"FLAGSHIP MODEL RESULTS INVESTIGATION")
    print(f"{'='*80}")
    
    # Load results
    df, detailed, csv_path, json_path = load_latest_flagship_results()
    
    # 1. Summary statistics
    summarize_flagship_results(df)
    
    # 2. Compare to human scores
    human_comparison = compare_to_human_scores(df)
    
    # 3. Compare to previous runs
    compare_to_previous_runs(df)
    
    # 4. Save comparison results
    if human_comparison is not None and len(human_comparison) > 0:
        output_path = "model_scores_gold_standard/flagship_run/flagship_vs_human_comparison.csv"
        human_comparison.to_csv(output_path, index=False)
        print(f"\n✅ Saved human comparison to: {output_path}")
    
    print(f"\n{'='*80}")
    print(f"INVESTIGATION COMPLETE")
    print(f"{'='*80}")
    print(f"\n📁 Files to explore:")
    print(f"   CSV: {csv_path}")
    print(f"   JSON: {json_path}")
    print(f"\n💡 Next steps:")
    print(f"   1. View detailed results: Open {json_path}")
    print(f"   2. Compare to human: Run compare_models_to_human.py with flagship scores")
    print(f"   3. View MLflow: Run 'mlflow ui' and check 'Flagship Models Validation' experiment")
    print(f"   4. Generate visualizations: Use compare_models_to_human.py")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()

