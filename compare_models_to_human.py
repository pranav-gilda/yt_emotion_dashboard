"""
Compare model scores against human gold standard scores.
Calculate correlations, MAE, RMSE, and create visualizations.
"""

import pandas as pd
import numpy as np
import logging
import os
import json
from typing import Dict, List, Tuple, Any
from datetime import datetime
from scipy.stats import pearsonr, spearmanr
from sklearn.metrics import mean_absolute_error, mean_squared_error

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    HAS_PLOTTING = True
except ImportError:
    HAS_PLOTTING = False
    logging.warning("matplotlib/seaborn not available. Skipping plots.")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

HUMAN_SCORES_PATH = "validation_results/human_scores_cleaned.csv"
MODEL_SCORES_DIR = "model_scores_gold_standard"
OUTPUT_DIR = "model_comparison_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Dimension mapping (human scores use different column names)
DIMENSION_MAPPING = {
    'opinion_news': 'opinion_news_score',
    'nuance': 'nuance_score',
    'order_creativity': 'order_creativity_score',
    'prevention_promotion': 'prevention_promotion_score',
    'compassion_contempt': 'contempt_compassion_score'  # Note: human scores use contempt_compassion_score
}

# All 5 dimensions
ALL_DIMENSIONS = list(DIMENSION_MAPPING.keys())

# Methods that score all 5 dimensions
LLM_METHODS = [
    'openai_no_roberta',
    'openai_with_roberta',
    'gemini_no_roberta',
    'gemini_with_roberta'
]

# Methods that only score compassion_contempt
ROBERTA_METHODS = [
    'roberta_plain',
    'roberta_valence'
]

# ============================================================================
# LOAD DATA
# ============================================================================

def load_latest_model_scores() -> pd.DataFrame:
    """Load the most recent model scores CSV."""
    if not os.path.exists(MODEL_SCORES_DIR):
        raise FileNotFoundError(f"Model scores directory not found: {MODEL_SCORES_DIR}")
    
    csv_files = [f for f in os.listdir(MODEL_SCORES_DIR) if f.startswith('model_scores_') and f.endswith('.csv')]
    if not csv_files:
        raise FileNotFoundError(f"No model scores CSV found in {MODEL_SCORES_DIR}")
    
    # Get most recent file
    csv_files.sort(reverse=True)
    latest_file = os.path.join(MODEL_SCORES_DIR, csv_files[0])
    
    logging.info(f"Loading model scores from: {latest_file}")
    df = pd.read_csv(latest_file)
    logging.info(f"  Loaded {len(df)} videos with model scores")
    
    return df

def load_human_scores() -> pd.DataFrame:
    """Load human gold standard scores."""
    logging.info(f"Loading human scores from: {HUMAN_SCORES_PATH}")
    df = pd.read_csv(HUMAN_SCORES_PATH)
    logging.info(f"  Loaded {len(df)} videos with human scores")
    return df

# ============================================================================
# METRICS CALCULATION
# ============================================================================

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calculate various metrics comparing predictions to ground truth."""
    # Remove NaN pairs
    mask = ~(np.isnan(y_true) | np.isnan(y_pred))
    y_true_clean = y_true[mask]
    y_pred_clean = y_pred[mask]
    
    if len(y_true_clean) < 2:
        return {
            'n': len(y_true_clean),
            'pearson_r': np.nan,
            'pearson_p': np.nan,
            'spearman_r': np.nan,
            'spearman_p': np.nan,
            'mae': np.nan,
            'mse': np.nan,
            'rmse': np.nan,
            'mean_true': np.nan,
            'mean_pred': np.nan,
            'std_true': np.nan,
            'std_pred': np.nan
        }
    
    # Pearson correlation
    pearson_r, pearson_p = pearsonr(y_true_clean, y_pred_clean)
    
    # Spearman correlation
    spearman_r, spearman_p = spearmanr(y_true_clean, y_pred_clean)
    
    # MAE, MSE, RMSE
    mae = mean_absolute_error(y_true_clean, y_pred_clean)
    mse = mean_squared_error(y_true_clean, y_pred_clean)
    rmse = np.sqrt(mse)
    
    return {
        'n': len(y_true_clean),
        'pearson_r': pearson_r,
        'pearson_p': pearson_p,
        'spearman_r': spearman_r,
        'spearman_p': spearman_p,
        'mae': mae,
        'mse': mse,
        'rmse': rmse,
        'mean_true': np.mean(y_true_clean),
        'mean_pred': np.mean(y_pred_clean),
        'std_true': np.std(y_true_clean),
        'std_pred': np.std(y_pred_clean)
    }

# ============================================================================
# COMPARISON ANALYSIS
# ============================================================================

def compare_all_models_to_human() -> Dict[str, Any]:
    """Compare all model scores to human gold standard."""
    logging.info("="*80)
    logging.info("COMPARING MODELS TO HUMAN GOLD STANDARD")
    logging.info("="*80)
    
    # Load data
    human_df = load_human_scores()
    model_df = load_latest_model_scores()
    
    # Merge on video_id
    merged_df = human_df.merge(model_df, on='video_id', how='inner', suffixes=('_human', '_model'))
    logging.info(f"\nMerged {len(merged_df)} videos (common to both datasets)")
    
    if len(merged_df) == 0:
        raise ValueError("No common videos found between human and model scores!")
    
    # Calculate metrics for each method-dimension combination
    all_metrics = []
    
    # For LLM methods (all 5 dimensions)
    for method in LLM_METHODS:
        for dimension in ALL_DIMENSIONS:
            human_col = DIMENSION_MAPPING[dimension]
            model_col = f"{method}_{dimension}"
            
            if human_col not in merged_df.columns:
                logging.warning(f"  Human column not found: {human_col}")
                continue
            if model_col not in merged_df.columns:
                logging.warning(f"  Model column not found: {model_col}")
                continue
            
            y_true = merged_df[human_col].values
            y_pred = merged_df[model_col].values
            
            metrics = calculate_metrics(y_true, y_pred)
            metrics['method'] = method
            metrics['dimension'] = dimension
            all_metrics.append(metrics)
            
            if metrics['n'] > 0:
                logging.info(f"  {method:25s} | {dimension:25s} | N={metrics['n']:3d} | "
                           f"Pearson r={metrics['pearson_r']:.3f} | MAE={metrics['mae']:.3f}")
    
    # For RoBERTa methods (compassion_contempt only)
    for method in ROBERTA_METHODS:
        dimension = 'compassion_contempt'
        human_col = DIMENSION_MAPPING[dimension]
        model_col = f"{method}_{dimension}"
        
        if human_col not in merged_df.columns:
            logging.warning(f"  Human column not found: {human_col}")
            continue
        if model_col not in merged_df.columns:
            logging.warning(f"  Model column not found: {model_col}")
            continue
        
        y_true = merged_df[human_col].values
        y_pred = merged_df[model_col].values
        
        metrics = calculate_metrics(y_true, y_pred)
        metrics['method'] = method
        metrics['dimension'] = dimension
        all_metrics.append(metrics)
        
        if metrics['n'] > 0:
            logging.info(f"  {method:25s} | {dimension:25s} | N={metrics['n']:3d} | "
                       f"Pearson r={metrics['pearson_r']:.3f} | MAE={metrics['mae']:.3f}")
    
    # Create metrics DataFrame
    metrics_df = pd.DataFrame(all_metrics)
    
    # Summary statistics
    summary = {
        'total_comparisons': len(metrics_df),
        'total_videos': len(merged_df),
        'metrics_by_method': {},
        'metrics_by_dimension': {},
        'best_method_per_dimension': {}
    }
    
    # Best method per dimension (by Pearson r)
    for dimension in ALL_DIMENSIONS:
        dim_metrics = metrics_df[metrics_df['dimension'] == dimension].copy()
        if len(dim_metrics) > 0:
            best_idx = dim_metrics['pearson_r'].idxmax()
            best_method = dim_metrics.loc[best_idx, 'method']
            best_r = dim_metrics.loc[best_idx, 'pearson_r']
            summary['best_method_per_dimension'][dimension] = {
                'method': best_method,
                'pearson_r': best_r,
                'mae': dim_metrics.loc[best_idx, 'mae']
            }
    
    return {
        'merged_df': merged_df,
        'metrics_df': metrics_df,
        'summary': summary
    }

# ============================================================================
# VISUALIZATIONS
# ============================================================================

def create_visualizations(merged_df: pd.DataFrame, metrics_df: pd.DataFrame):
    """Create scatter plots and correlation heatmaps."""
    if not HAS_PLOTTING:
        logging.warning("Skipping visualizations (matplotlib/seaborn not available)")
        return
    
    plots_dir = os.path.join(OUTPUT_DIR, 'plots')
    heatmaps_dir = os.path.join(plots_dir, 'heatmaps')
    os.makedirs(plots_dir, exist_ok=True)
    os.makedirs(heatmaps_dir, exist_ok=True)
    
    # 1. Scatter plots: Human vs Model for each method-dimension
    logging.info("\nCreating scatter plots...")
    
    for method in LLM_METHODS + ROBERTA_METHODS:
        # Determine which dimensions this method scores
        if method in LLM_METHODS:
            dimensions = ALL_DIMENSIONS
        else:
            dimensions = ['compassion_contempt']
        
        for dimension in dimensions:
            human_col = DIMENSION_MAPPING[dimension]
            model_col = f"{method}_{dimension}"
            
            if human_col not in merged_df.columns or model_col not in merged_df.columns:
                continue
            
            # Get metrics for this combination
            method_metrics = metrics_df[
                (metrics_df['method'] == method) & 
                (metrics_df['dimension'] == dimension)
            ]
            
            if len(method_metrics) == 0:
                continue
            
            metrics = method_metrics.iloc[0]
            
            # Create scatter plot
            plt.figure(figsize=(8, 6))
            
            y_true = merged_df[human_col].dropna()
            y_pred = merged_df[model_col].dropna()
            
            # Align indices
            common_idx = y_true.index.intersection(y_pred.index)
            y_true = y_true.loc[common_idx]
            y_pred = y_pred.loc[common_idx]
            
            plt.scatter(y_true, y_pred, alpha=0.6, s=50)
            
            # Add diagonal line (perfect agreement)
            min_val = min(y_true.min(), y_pred.min())
            max_val = max(y_true.max(), y_pred.max())
            plt.plot([min_val, max_val], [min_val, max_val], 'r--', alpha=0.5, label='Perfect Agreement')
            
            # Add metrics to title
            title = f"{method} vs Human: {dimension}\n"
            title += f"Pearson r={metrics['pearson_r']:.3f}, MAE={metrics['mae']:.3f}, N={int(metrics['n'])}"
            
            plt.xlabel('Human Score (1-5)', fontsize=12)
            plt.ylabel('Model Score (1-5)', fontsize=12)
            plt.title(title, fontsize=11)
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # Save
            safe_method = method.replace(' ', '_').replace('/', '_')
            safe_dim = dimension.replace(' ', '_').replace('/', '_')
            plot_path = os.path.join(plots_dir, f"{safe_method}_{safe_dim}_scatter.png")
            plt.savefig(plot_path, dpi=150, bbox_inches='tight')
            plt.close()
    
    # 2. Correlation heatmap: All methods vs Human (per dimension)
    logging.info("Creating correlation heatmaps...")
    
    for dimension in ALL_DIMENSIONS:
        human_col = DIMENSION_MAPPING[dimension]
        
        if human_col not in merged_df.columns:
            continue
        
        # Get all method columns for this dimension
        method_cols = []
        method_names = []
        
        for method in LLM_METHODS:
            model_col = f"{method}_{dimension}"
            if model_col in merged_df.columns:
                method_cols.append(model_col)
                method_names.append(method)
        
        # Add RoBERTa methods if this is compassion_contempt
        if dimension == 'compassion_contempt':
            for method in ROBERTA_METHODS:
                model_col = f"{method}_{dimension}"
                if model_col in merged_df.columns:
                    method_cols.append(model_col)
                    method_names.append(method)
        
        if len(method_cols) == 0:
            continue
        
        # Calculate correlation matrix
        corr_data = merged_df[[human_col] + method_cols].corr()
        
        # Create heatmap
        plt.figure(figsize=(10, 8))
        sns.heatmap(corr_data, annot=True, fmt='.3f', cmap='coolwarm', center=0,
                   square=True, linewidths=1, cbar_kws={"shrink": 0.8},
                   xticklabels=['Human'] + method_names,
                   yticklabels=['Human'] + method_names)
        plt.title(f'Correlation Matrix: {dimension}', fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        safe_dim = dimension.replace(' ', '_').replace('/', '_')
        heatmap_path = os.path.join(heatmaps_dir, f"{safe_dim}_correlation_heatmap.png")
        plt.savefig(heatmap_path, dpi=150, bbox_inches='tight')
        plt.close()
    
    logging.info(f"✓ Scatter plots saved to: {plots_dir}/")
    logging.info(f"✓ Heatmaps saved to: {heatmaps_dir}/")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main comparison pipeline."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Run comparison
    results = compare_all_models_to_human()
    
    # Save results
    # 1. Metrics CSV
    metrics_path = os.path.join(OUTPUT_DIR, f"model_vs_human_metrics_{timestamp}.csv")
    results['metrics_df'].to_csv(metrics_path, index=False)
    logging.info(f"\n✓ Metrics saved to: {metrics_path}")
    
    # 2. Summary JSON
    summary_path = os.path.join(OUTPUT_DIR, f"comparison_summary_{timestamp}.json")
    with open(summary_path, 'w') as f:
        json.dump(results['summary'], f, indent=2)
    logging.info(f"✓ Summary saved to: {summary_path}")
    
    # 3. Merged data CSV
    merged_path = os.path.join(OUTPUT_DIR, f"merged_human_model_scores_{timestamp}.csv")
    results['merged_df'].to_csv(merged_path, index=False)
    logging.info(f"✓ Merged data saved to: {merged_path}")
    
    # 4. Create visualizations
    create_visualizations(results['merged_df'], results['metrics_df'])
    
    # Print summary
    logging.info("\n" + "="*80)
    logging.info("COMPARISON SUMMARY")
    logging.info("="*80)
    logging.info(f"Total videos compared: {results['summary']['total_videos']}")
    logging.info(f"Total comparisons: {results['summary']['total_comparisons']}")
    logging.info("\nBest method per dimension (by Pearson r):")
    for dim, info in results['summary']['best_method_per_dimension'].items():
        logging.info(f"  {dim:25s}: {info['method']:25s} (r={info['pearson_r']:.3f}, MAE={info['mae']:.3f})")
    
    logging.info(f"\n✅ All results saved to: {OUTPUT_DIR}/")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        raise

