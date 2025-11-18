"""
Compare consistency between two runs of the same models.
Analyzes overlap, agreement, and stability of predictions.
"""

import pandas as pd
import numpy as np
import logging
import json
import os
from typing import Dict, List, Tuple
from datetime import datetime
from scipy.stats import pearsonr
from sklearn.metrics import mean_absolute_error

try:
    import mlflow
    HAS_MLFLOW = True
except ImportError:
    HAS_MLFLOW = False
    logging.warning("MLflow not available. Tracking will be skipped.")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

RUN1_DIR = "model_scores_gold_standard/run_1"
RUN2_DIR = "model_scores_gold_standard/run_2"
OUTPUT_DIR = "run_consistency_analysis"
MLFLOW_EXPERIMENT_NAME = "Run Consistency Analysis"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_latest_run_scores(run_dir: str) -> pd.DataFrame:
    """Load the most recent scores CSV from a run directory."""
    if not os.path.exists(run_dir):
        raise FileNotFoundError(f"Run directory not found: {run_dir}")
    
    csv_files = [f for f in os.listdir(run_dir) if f.startswith('model_scores_') and f.endswith('.csv')]
    if not csv_files:
        raise FileNotFoundError(f"No model scores found in {run_dir}")
    
    csv_files.sort(reverse=True)
    latest_file = os.path.join(run_dir, csv_files[0])
    
    logging.info(f"Loading: {latest_file}")
    return pd.read_csv(latest_file)

def compare_runs_consistency():
    """Compare consistency between two runs."""
    logging.info("="*80)
    logging.info("COMPARING RUN CONSISTENCY")
    logging.info("="*80)
    
    # Set up MLflow
    if HAS_MLFLOW:
        mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
        run_name = f"consistency_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        mlflow_run = mlflow.start_run(run_name=run_name)
        mlflow.log_param("run1_dir", RUN1_DIR)
        mlflow.log_param("run2_dir", RUN2_DIR)
    else:
        mlflow_run = None
    
    # Load both runs
    run1_df = load_latest_run_scores(RUN1_DIR)
    run2_df = load_latest_run_scores(RUN2_DIR)
    
    if HAS_MLFLOW:
        mlflow.log_param("run1_videos", len(run1_df))
        mlflow.log_param("run2_videos", len(run2_df))
    
    # Merge on video_id
    merged = run1_df.merge(run2_df, on='video_id', how='inner', suffixes=('_run1', '_run2'))
    logging.info(f"\nFound {len(merged)} common videos between runs")
    
    if len(merged) == 0:
        raise ValueError("No common videos found between runs!")
    
    if HAS_MLFLOW:
        mlflow.log_metric("common_videos", len(merged))
    
    # Find all score columns (compassion_contempt for both runs)
    run1_score_cols = [c for c in run1_df.columns if any(method in c for method in 
        ['openai_no_roberta', 'openai_with_roberta', 'gemini_no_roberta', 
         'gemini_with_roberta', 'roberta_plain', 'roberta_valence']) 
        and 'compassion_contempt' in c]
    
    consistency_results = []
    
    for col in run1_score_cols:
        if col not in run1_df.columns or col not in run2_df.columns:
            continue
        
        run1_col = f"{col}_run1"
        run2_col = f"{col}_run2"
        
        if run1_col not in merged.columns or run2_col not in merged.columns:
            continue
        
        # Get scores
        scores1 = merged[run1_col].dropna()
        scores2 = merged[run2_col].dropna()
        
        # Align indices
        common_idx = scores1.index.intersection(scores2.index)
        scores1 = scores1.loc[common_idx]
        scores2 = scores2.loc[common_idx]
        
        if len(scores1) < 2:
            continue
        
        # Calculate consistency metrics
        pearson_r, pearson_p = pearsonr(scores1, scores2)
        mae = mean_absolute_error(scores1, scores2)
        rmse = np.sqrt(np.mean((scores1 - scores2) ** 2))
        
        # Exact agreement
        exact_agreement = (scores1 == scores2).sum() / len(scores1)
        
        # Agreement within 0.5
        within_half = (np.abs(scores1 - scores2) <= 0.5).sum() / len(scores1)
        
        # Agreement within 1.0
        within_one = (np.abs(scores1 - scores2) <= 1.0).sum() / len(scores1)
        
        consistency_results.append({
            'method_dimension': col,
            'n_videos': len(scores1),
            'pearson_r': pearson_r,
            'pearson_p': pearson_p,
            'mae': mae,
            'rmse': rmse,
            'exact_agreement': exact_agreement,
            'agreement_within_0.5': within_half,
            'agreement_within_1.0': within_one,
            'mean_run1': scores1.mean(),
            'mean_run2': scores2.mean(),
            'std_run1': scores1.std(),
            'std_run2': scores2.std()
        })
        
        logging.info(f"\n{col}:")
        logging.info(f"  Pearson r: {pearson_r:.3f} (p={pearson_p:.4f})")
        logging.info(f"  MAE: {mae:.3f}, RMSE: {rmse:.3f}")
        logging.info(f"  Exact agreement: {exact_agreement:.1%}")
        logging.info(f"  Agreement within 0.5: {within_half:.1%}")
        logging.info(f"  Agreement within 1.0: {within_one:.1%}")
        
        # Log to MLflow
        if HAS_MLFLOW:
            safe_name = col.replace(' ', '_').replace('/', '_')
            mlflow.log_metric(f"{safe_name}_pearson_r", pearson_r)
            mlflow.log_metric(f"{safe_name}_mae", mae)
            mlflow.log_metric(f"{safe_name}_exact_agreement", exact_agreement)
    
    # Create results DataFrame
    consistency_df = pd.DataFrame(consistency_results)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(OUTPUT_DIR, f"run_consistency_{timestamp}.csv")
    consistency_df.to_csv(csv_path, index=False)
    logging.info(f"\n✓ Consistency results saved to: {csv_path}")
    
    if HAS_MLFLOW:
        mlflow.log_artifact(csv_path, "consistency_results")
    
    # Summary statistics
    summary = {
        'total_comparisons': len(consistency_df),
        'mean_pearson_r': float(consistency_df['pearson_r'].mean()) if len(consistency_df) > 0 else 0,
        'mean_mae': float(consistency_df['mae'].mean()) if len(consistency_df) > 0 else 0,
        'mean_exact_agreement': float(consistency_df['exact_agreement'].mean()) if len(consistency_df) > 0 else 0,
        'high_consistency': len(consistency_df[consistency_df['pearson_r'] > 0.9]) if len(consistency_df) > 0 else 0,
        'moderate_consistency': len(consistency_df[(consistency_df['pearson_r'] > 0.7) & (consistency_df['pearson_r'] <= 0.9)]) if len(consistency_df) > 0 else 0,
        'low_consistency': len(consistency_df[consistency_df['pearson_r'] <= 0.7]) if len(consistency_df) > 0 else 0
    }
    
    summary_path = os.path.join(OUTPUT_DIR, f"consistency_summary_{timestamp}.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logging.info(f"\n✓ Summary saved to: {summary_path}")
    logging.info(f"\nSummary:")
    logging.info(f"  Mean Pearson r: {summary['mean_pearson_r']:.3f}")
    logging.info(f"  Mean MAE: {summary['mean_mae']:.3f}")
    logging.info(f"  Mean exact agreement: {summary['mean_exact_agreement']:.1%}")
    logging.info(f"  High consistency (r>0.9): {summary['high_consistency']}")
    logging.info(f"  Moderate consistency (0.7<r≤0.9): {summary['moderate_consistency']}")
    logging.info(f"  Low consistency (r≤0.7): {summary['low_consistency']}")
    
    if HAS_MLFLOW:
        mlflow.log_metric("mean_pearson_r", summary['mean_pearson_r'])
        mlflow.log_metric("mean_mae", summary['mean_mae'])
        mlflow.log_metric("mean_exact_agreement", summary['mean_exact_agreement'])
        mlflow.log_metric("high_consistency_count", summary['high_consistency'])
        mlflow.log_artifact(summary_path, "summary")
        mlflow.end_run()
        logging.info(f"\n✓ MLflow run logged: {run_name}")
    
    return consistency_df, summary

if __name__ == "__main__":
    try:
        consistency_df, summary = compare_runs_consistency()
        print(f"\n{'='*80}")
        print(f"SUCCESS! Consistency analysis complete")
        print(f"{'='*80}")
    except Exception as e:
        logging.error(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        raise

