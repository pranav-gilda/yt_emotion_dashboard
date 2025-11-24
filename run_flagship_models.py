"""
Run flagship models on gold standard videos.

Models:
1. OpenAI Flagship (e.g., gpt-4o, gpt-5.1) - all 5 dimensions, no RoBERTa
2. Gemini 3 Pro Preview - all 5 dimensions, no RoBERTa
"""

import pandas as pd
import numpy as np
import logging
import json
import os
import time
import re
import argparse
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import analysis functions
from llm_analyzer import analyze_transcript_with_llm
from parse_transcripts_docx import parse_transcripts_docx, normalize_title

# Import transcript fetching from the working script (proven logic)
from run_models_on_gold_standard import get_transcript_for_video, TRANSCRIPT_CACHE

# MLflow tracking
try:
    import mlflow
    HAS_MLFLOW = True
except ImportError:
    HAS_MLFLOW = False
    logging.warning("MLflow not available. Tracking will be skipped.")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

GOLD_STANDARD_PATH = "validation_results/human_scores_cleaned.csv"
OUTPUT_DIR = "model_scores_gold_standard"
FLAGSHIP_RUN_DIR = "flagship_run"
MLFLOW_EXPERIMENT_NAME = "Flagship Models Validation"

# Flagship model names
OPENAI_FLAGSHIP_MODEL = "gpt-5.1"  # Can be overridden with "gpt-5" or other models
GEMINI_FLAGSHIP_MODEL = "models/gemini-3-pro-preview"  # Gemini 3 Pro Preview

# Transcript fetching is imported from run_models_on_gold_standard.py (proven working logic)
# This ensures both scripts use the exact same transcript matching logic

# ============================================================================
# SCORE NORMALIZATION (to 1-5 scale)
# ============================================================================

def normalize_llm_score_to_1_5(score: Any, dimension: str) -> Optional[float]:
    """
    Normalize LLM score to 1-5 scale.
    Handles various output formats from different prompts.
    """
    if score is None or (isinstance(score, float) and np.isnan(score)):
        return None
    
    try:
        score_float = float(score)
    except (ValueError, TypeError):
        return None
    
    # If already 1-5, return as is (clamped)
    if 1 <= score_float <= 5:
        return round(score_float, 4)
    
    # If -5 to +5, map to 1-5: (score + 5) / 2
    if -5 <= score_float <= 5:
        normalized = (score_float + 5) / 2
        return round(max(1, min(5, normalized)), 4)
    
    # If 0-100, map to 1-5: (score / 20) + 1
    if 0 <= score_float <= 100:
        normalized = (score_float / 20) + 1
        return round(max(1, min(5, normalized)), 4)
    
    # If 0-5, map to 1-5: score + 1
    if 0 <= score_float <= 5:
        normalized = score_float + 1
        return round(max(1, min(5, normalized)), 4)
    
    return None

# ============================================================================
# FLAGSHIP MODEL RUNNERS
# ============================================================================

def run_openai_flagship(transcript: str, model_name: str = OPENAI_FLAGSHIP_MODEL) -> Dict[str, Any]:
    """Run OpenAI Flagship LLM without RoBERTa context (all 5 dimensions)."""
    try:
        result = analyze_transcript_with_llm(
            transcript, 
            "openai", 
            "v5_all_dimensions",
            model_name=model_name
        )
        
        # Extract and normalize scores
        scores = {}
        dimension_mapping = {
            'opinion_news': 'opinion_news',
            'nuance': 'nuance',
            'order_creativity': 'order_creativity',
            'prevention_promotion': 'prevention_promotion',
            'compassion_contempt': 'compassion_contempt'
        }
        
        for dim_key, dim_name in dimension_mapping.items():
            dim_result = result.get(dim_key, {})
            if isinstance(dim_result, dict):
                raw_score = dim_result.get('score')
                scores[dim_name] = normalize_llm_score_to_1_5(raw_score, dim_name)
        
        return {
            'method': 'openai_flagship',
            'model_name': model_name,
            'scores': scores,
            'raw_result': result,
            'error': None
        }
    except Exception as e:
        logging.error(f"  Error in OpenAI Flagship ({model_name}): {e}")
        return {
            'method': 'openai_flagship',
            'model_name': model_name,
            'scores': {},
            'raw_result': None,
            'error': str(e)
        }

def run_gemini_flagship(transcript: str, model_name: str = GEMINI_FLAGSHIP_MODEL) -> Dict[str, Any]:
    """Run Gemini 3 Pro Preview LLM without RoBERTa context (all 5 dimensions)."""
    try:
        result = analyze_transcript_with_llm(
            transcript, 
            "gemini", 
            "v5_all_dimensions",
            model_name=model_name
        )
        
        # Extract and normalize scores
        scores = {}
        dimension_mapping = {
            'opinion_news': 'opinion_news',
            'nuance': 'nuance',
            'order_creativity': 'order_creativity',
            'prevention_promotion': 'prevention_promotion',
            'compassion_contempt': 'compassion_contempt'
        }
        
        for dim_key, dim_name in dimension_mapping.items():
            dim_result = result.get(dim_key, {})
            if isinstance(dim_result, dict):
                raw_score = dim_result.get('score')
                scores[dim_name] = normalize_llm_score_to_1_5(raw_score, dim_name)
        
        return {
            'method': 'gemini_flagship',
            'model_name': model_name,
            'scores': scores,
            'raw_result': result,
            'error': None
        }
    except Exception as e:
        logging.error(f"  Error in Gemini Flagship ({model_name}): {e}")
        return {
            'method': 'gemini_flagship',
            'model_name': model_name,
            'scores': {},
            'raw_result': None,
            'error': str(e)
        }

# ============================================================================
# MAIN PIPELINE
# ============================================================================

def run_flagship_models_on_gold_standard(
    openai_model: str = OPENAI_FLAGSHIP_MODEL,
    gemini_model: str = GEMINI_FLAGSHIP_MODEL
):
    """Run flagship models on gold standard videos."""
    logging.info("="*80)
    logging.info("RUNNING FLAGSHIP MODELS ON GOLD STANDARD VIDEOS")
    logging.info(f"OpenAI Model: {openai_model}")
    logging.info(f"Gemini Model: {gemini_model}")
    logging.info("="*80)
    
    # Set up MLflow tracking
    if HAS_MLFLOW:
        mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
        run_name = f"flagship_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        mlflow_run = mlflow.start_run(run_name=run_name)
        mlflow.log_param("openai_model", openai_model)
        mlflow.log_param("gemini_model", gemini_model)
        mlflow.log_param("prompt_version", "v5_all_dimensions")
        mlflow.log_param("timestamp", datetime.now().isoformat())
    else:
        mlflow_run = None
    
    # Create flagship run output directory
    run_output_dir = os.path.join(OUTPUT_DIR, FLAGSHIP_RUN_DIR)
    os.makedirs(run_output_dir, exist_ok=True)
    
    # Load gold standard
    logging.info(f"\nLoading gold standard from: {GOLD_STANDARD_PATH}")
    gold_df = pd.read_csv(GOLD_STANDARD_PATH)
    
    # Filter out invalid entries (Excel errors like #NAME?)
    initial_count = len(gold_df)
    gold_df = gold_df[gold_df['video_id'].astype(str).str.strip() != '#NAME?']
    gold_df = gold_df[gold_df['video_id'].notna()]
    gold_df = gold_df[gold_df['video_id'].astype(str).str.len() > 0]
    
    filtered_count = initial_count - len(gold_df)
    if filtered_count > 0:
        logging.info(f"Filtered out {filtered_count} invalid entries (e.g., #NAME?)")
    
    logging.info(f"Loaded {len(gold_df)} valid videos from gold standard")
    
    if HAS_MLFLOW:
        mlflow.log_param("total_videos", len(gold_df))
        mlflow.log_param("filtered_invalid", filtered_count)
    
    # Skip .docx loading - transcripts are in transcripts/history/ and previous run JSON files
    docx_transcripts = {}  # Not using .docx anymore - transcripts from JSON files
    logging.info("\nSkipping .docx loading - using transcripts from history/ and previous run JSON files")
    
    if HAS_MLFLOW:
        mlflow.log_param("docx_transcripts_count", 0)
        mlflow.log_param("transcript_source", "history_folder_and_json")
    
    # Process each video
    all_results = []
    missing_transcripts = []
    
    for idx, row in gold_df.iterrows():
        video_id = row['video_id']
        youtube_id = row.get('youtube_id')  # May be NaN
        
        logging.info(f"\n{'='*80}")
        logging.info(f"Processing video {idx+1}/{len(gold_df)}: {video_id[:50]}")
        logging.info(f"{'='*80}")
        
        # Get transcript (handle NaN youtube_id)
        youtube_id_clean = youtube_id if pd.notna(youtube_id) else None
        transcript = get_transcript_for_video(video_id, youtube_id_clean, docx_transcripts)
        
        if not transcript:
            logging.warning(f"  No transcript available for {video_id}")
            missing_transcripts.append(video_id)
            continue
        
        logging.info(f"  Transcript length: {len(transcript)} characters")
        
        # Run flagship models
        transcript_words = transcript.split()
        transcript_sentences = [s for s in transcript.split('.') if s.strip()]
        
        video_results = {
            'video_id': video_id,
            'youtube_id': youtube_id if pd.notna(youtube_id) else None,
            'transcript_length': len(transcript),
            'transcript_word_count': len(transcript_words),
            'transcript_sentence_count': len(transcript_sentences),
            'methods': {}
        }
        
        # 1. OpenAI Flagship
        logging.info(f"  Running OpenAI Flagship ({openai_model})...")
        video_results['methods']['openai_flagship'] = run_openai_flagship(transcript, openai_model)
        
        # 2. Gemini Flagship
        logging.info(f"  Running Gemini Flagship ({gemini_model})...")
        video_results['methods']['gemini_flagship'] = run_gemini_flagship(transcript, gemini_model)
        
        all_results.append(video_results)
        
        # Log summary
        logging.info("\n  --- Scores Summary (1-5 scale) ---")
        for method_key, method_result in video_results['methods'].items():
            if method_result.get('error'):
                logging.info(f"    {method_key:25s}: ERROR - {method_result['error'][:50]}")
            else:
                scores_str = ', '.join([f"{k}={v:.2f}" for k, v in method_result['scores'].items()])
                logging.info(f"    {method_key:25s}: {scores_str}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Save detailed JSON
    json_path = os.path.join(run_output_dir, f"flagship_scores_detailed_{timestamp}.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    logging.info(f"\n✓ Detailed results saved to: {json_path}")
    
    if HAS_MLFLOW:
        mlflow.log_artifact(json_path, "detailed_results")
    
    # 2. Create flattened CSV for easy comparison
    flattened_data = []
    for result in all_results:
        row = {
            'video_id': result['video_id'],
            'youtube_id': result.get('youtube_id'),
            'transcript_length': result['transcript_length'],
            'transcript_word_count': result.get('transcript_word_count'),
            'transcript_sentence_count': result.get('transcript_sentence_count')
        }
        
        # Add scores from each method
        for method_key, method_result in result['methods'].items():
            for dim, score in method_result.get('scores', {}).items():
                col_name = f"{method_key}_{dim}"
                row[col_name] = score
        
        flattened_data.append(row)
    
    df_scores = pd.DataFrame(flattened_data)
    csv_path = os.path.join(run_output_dir, f"flagship_scores_{timestamp}.csv")
    df_scores.to_csv(csv_path, index=False)
    logging.info(f"✓ Flagship scores CSV saved to: {csv_path}")
    
    if HAS_MLFLOW:
        mlflow.log_artifact(csv_path, "flagship_scores")
    
    # 3. Save missing transcripts list
    if missing_transcripts:
        missing_path = os.path.join(run_output_dir, f"missing_transcripts_{timestamp}.txt")
        with open(missing_path, 'w') as f:
            f.write('\n'.join(missing_transcripts))
        logging.info(f"⚠ {len(missing_transcripts)} videos missing transcripts (saved to {missing_path})")
    
    # 4. Log summary metrics to MLflow
    if HAS_MLFLOW:
        mlflow.log_metric("videos_processed", len(all_results))
        mlflow.log_metric("videos_missing_transcripts", len(missing_transcripts))
        mlflow.log_metric("avg_transcript_length", df_scores['transcript_length'].mean() if len(df_scores) > 0 else 0)
        mlflow.log_metric("avg_word_count", df_scores['transcript_word_count'].mean() if len(df_scores) > 0 else 0)
        
        # Log success rates per method
        for method in ['openai_flagship', 'gemini_flagship']:
            method_cols = [c for c in df_scores.columns if c.startswith(f"{method}_")]
            if method_cols:
                success_count = df_scores[method_cols[0]].notna().sum()
                mlflow.log_metric(f"{method}_success_rate", success_count / len(df_scores) if len(df_scores) > 0 else 0)
    
    logging.info(f"\n✅ Completed! Processed {len(all_results)} videos")
    logging.info(f"   Results saved to: {run_output_dir}/")
    
    if HAS_MLFLOW:
        mlflow.end_run()
        logging.info(f"   MLflow run logged: {run_name}")
    
    return all_results, df_scores

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run flagship models on gold standard videos')
    parser.add_argument('--openai-model', type=str, default=OPENAI_FLAGSHIP_MODEL,
                       help=f'OpenAI model name (default: {OPENAI_FLAGSHIP_MODEL})')
    parser.add_argument('--gemini-model', type=str, default=GEMINI_FLAGSHIP_MODEL,
                       help=f'Gemini model name (default: {GEMINI_FLAGSHIP_MODEL})')
    
    args = parser.parse_args()
    
    try:
        results, scores_df = run_flagship_models_on_gold_standard(
            openai_model=args.openai_model,
            gemini_model=args.gemini_model
        )
        print(f"\n{'='*80}")
        print(f"SUCCESS! Processed {len(results)} videos with flagship models")
        print(f"OpenAI Model: {args.openai_model}")
        print(f"Gemini Model: {args.gemini_model}")
        print(f"{'='*80}")
        if HAS_MLFLOW:
            print(f"   MLflow tracking: Enabled")
            print(f"   View results: mlflow ui")
    except Exception as e:
        logging.error(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        raise

