"""
Run all 6 models on gold standard videos and compare with human scores.

Models:
1. OpenAI without RoBERTa (all 5 dimensions)
2. OpenAI with RoBERTa (all 5 dimensions)
3. Gemini without RoBERTa (all 5 dimensions)
4. Gemini with RoBERTa (all 5 dimensions)
5. RoBERTa Plain (compassion/contempt only)
6. RoBERTa Valence (compassion/contempt only)
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
from models import run_go_emotions, RESPECT, CONTEMPT
from scale import run_valence_analysis
from llm_analyzer import analyze_transcript_with_llm
from build import fetch_transcript
from parse_transcripts_docx import parse_transcripts_docx, normalize_title

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
MLFLOW_EXPERIMENT_NAME = "Gold Standard Model Validation"

# Transcript cache to avoid re-reading
TRANSCRIPT_CACHE = {}

# ============================================================================
# TRANSCRIPT FETCHING
# ============================================================================

def get_transcript_for_video(video_id: str, youtube_id: Optional[str], 
                              docx_transcripts: Dict[str, str]) -> Optional[str]:
    """
    Get transcript for a video, trying multiple sources:
    1. From transcripts/history/{youtube_id}.txt (fastest, skip yt-dlp)
    2. From transcripts/history/{video_id}.txt (if video_id is YouTube ID)
    3. From Transcripts.docx (matched by normalized title or video_id)
    4. Skip yt-dlp to avoid hitting YouTube servers
    """
    # Get candidate IDs to try (youtube_id and video_id, both as-is and cleaned)
    candidate_ids = []
    
    # Add youtube_id if available (handle NaN, None, empty string)
    if youtube_id is not None:
        try:
            if pd.notna(youtube_id):
                youtube_id_str = str(youtube_id).strip()
                if youtube_id_str and len(youtube_id_str) > 0:
                    candidate_ids.append(youtube_id_str)
                    # Also try without leading dash/underscore
                    if youtube_id_str.startswith('-') or youtube_id_str.startswith('_'):
                        candidate_ids.append(youtube_id_str[1:])
        except:
            pass
    
    # Add video_id
    if video_id:
        video_id_str = str(video_id).strip()
        if video_id_str and video_id_str not in candidate_ids:
            candidate_ids.append(video_id_str)
        # Also try without leading dash/underscore
        if video_id_str and (video_id_str.startswith('-') or video_id_str.startswith('_')):
            cleaned = video_id_str[1:]
            if cleaned not in candidate_ids:
                candidate_ids.append(cleaned)
    
    # Check cache first (use first candidate as cache key)
    cache_key = candidate_ids[0] if candidate_ids else video_id
    if cache_key in TRANSCRIPT_CACHE:
        logging.info(f"  Using cached transcript for {video_id[:30]}")
        return TRANSCRIPT_CACHE[cache_key]
    
    # Try transcripts/history folder with all candidate IDs
    for candidate_id in candidate_ids:
        transcript_file = os.path.join("transcripts", "history", f"{candidate_id}.txt")
        if os.path.exists(transcript_file):
            logging.info(f"  Found transcript file: {transcript_file}")
            try:
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    transcript = f.read().strip()
                if len(transcript) > 50:  # Only return if substantial content
                    TRANSCRIPT_CACHE[cache_key] = transcript
                    return transcript
            except Exception as e:
                logging.warning(f"  Error reading transcript file: {e}")
    
    # Try .docx with all candidate IDs (both direct and normalized)
    for candidate_id in candidate_ids:
        # Try direct match first (in case .docx has YouTube ID as key)
        if candidate_id in docx_transcripts:
            logging.info(f"  Found transcript in .docx (direct match) for {candidate_id[:30]}")
            transcript = docx_transcripts[candidate_id]
            if len(transcript) > 50:
                TRANSCRIPT_CACHE[cache_key] = transcript
                return transcript
        
        # Try normalized match
        normalized_candidate = normalize_title(candidate_id)
        if normalized_candidate in docx_transcripts:
            logging.info(f"  Found transcript in .docx (normalized) for {candidate_id[:30]}")
            transcript = docx_transcripts[normalized_candidate]
            if len(transcript) > 50:
                TRANSCRIPT_CACHE[cache_key] = transcript
                return transcript
    
    # Also try with original video_id (in case it's a title, not an ID)
    if video_id not in candidate_ids:
        # Try direct match
        if video_id in docx_transcripts:
            logging.info(f"  Found transcript in .docx (direct video_id) for {video_id[:30]}")
            transcript = docx_transcripts[video_id]
            if len(transcript) > 50:
                TRANSCRIPT_CACHE[cache_key] = transcript
                return transcript
        
        # Try normalized
        normalized_video_id = normalize_title(video_id)
        if normalized_video_id not in [normalize_title(cid) for cid in candidate_ids]:
            if normalized_video_id in docx_transcripts:
                logging.info(f"  Found transcript in .docx (normalized video_id) for {video_id[:30]}")
                transcript = docx_transcripts[normalized_video_id]
                if len(transcript) > 50:
                    TRANSCRIPT_CACHE[cache_key] = transcript
                    return transcript
    
    logging.warning(f"  Could not get transcript for {video_id} (youtube_id: {youtube_id}) (skipping yt-dlp)")
    return None

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

def normalize_roberta_plain_to_1_5(roberta_result: Dict) -> Optional[float]:
    """
    Normalize RoBERTa plain (respect/contempt) to 1-5 scale.
    Currently outputs 0-5, so add 1 to get 1-5.
    """
    avg_scores = roberta_result.get("average_scores", {})
    
    respect_scores = [avg_scores.get(emo, 0) for emo in RESPECT]
    contempt_scores = [avg_scores.get(emo, 0) for emo in CONTEMPT]
    
    avg_respect = sum(respect_scores) / len(respect_scores) if respect_scores else 0
    avg_contempt = sum(contempt_scores) / len(contempt_scores) if contempt_scores else 0
    
    net_score = avg_respect - avg_contempt  # ranges from -1 to +1
    score_0_5 = 2.5 + (net_score * 2.5)  # map to 0-5
    score_1_5 = score_0_5 + 1  # map to 1-5
    
    return round(max(1, min(5, score_1_5)), 4)

def normalize_roberta_valence_to_1_5(valence_result: Dict) -> Optional[float]:
    """
    Normalize RoBERTa valence to 1-5 scale.
    Already outputs 1-5, so just clamp.
    """
    score = valence_result.get("human_rater_score_1_to_5")
    if score is None:
        return None
    return round(max(1, min(5, float(score))), 4)

# ============================================================================
# MODEL RUNNERS
# ============================================================================

def run_openai_without_roberta(transcript: str) -> Dict[str, Any]:
    """Run OpenAI LLM without RoBERTa context (all 5 dimensions)."""
    try:
        result = analyze_transcript_with_llm(transcript, "openai", "v5_all_dimensions")
        
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
            'method': 'openai_no_roberta',
            'scores': scores,
            'raw_result': result,
            'error': None
        }
    except Exception as e:
        logging.error(f"  Error in OpenAI (no RoBERTa): {e}")
        return {
            'method': 'openai_no_roberta',
            'scores': {},
            'raw_result': None,
            'error': str(e)
        }

def run_openai_with_roberta(transcript: str) -> Dict[str, Any]:
    """Run OpenAI LLM with RoBERTa context (all 5 dimensions)."""
    try:
        result = analyze_transcript_with_llm(transcript, "openai", "v5_all_dimensions_context")
        
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
            'method': 'openai_with_roberta',
            'scores': scores,
            'raw_result': result,
            'error': None
        }
    except Exception as e:
        logging.error(f"  Error in OpenAI (with RoBERTa): {e}")
        return {
            'method': 'openai_with_roberta',
            'scores': {},
            'raw_result': None,
            'error': str(e)
        }

def run_gemini_without_roberta(transcript: str) -> Dict[str, Any]:
    """Run Gemini LLM without RoBERTa context (all 5 dimensions)."""
    try:
        result = analyze_transcript_with_llm(transcript, "gemini", "v5_all_dimensions")
        
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
            'method': 'gemini_no_roberta',
            'scores': scores,
            'raw_result': result,
            'error': None
        }
    except Exception as e:
        logging.error(f"  Error in Gemini (no RoBERTa): {e}")
        return {
            'method': 'gemini_no_roberta',
            'scores': {},
            'raw_result': None,
            'error': str(e)
        }

def run_gemini_with_roberta(transcript: str) -> Dict[str, Any]:
    """Run Gemini LLM with RoBERTa context (all 5 dimensions)."""
    try:
        result = analyze_transcript_with_llm(transcript, "gemini", "v5_all_dimensions_context")
        
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
            'method': 'gemini_with_roberta',
            'scores': scores,
            'raw_result': result,
            'error': None
        }
    except Exception as e:
        logging.error(f"  Error in Gemini (with RoBERTa): {e}")
        return {
            'method': 'gemini_with_roberta',
            'scores': {},
            'raw_result': None,
            'error': str(e)
        }

def run_roberta_plain(transcript: str) -> Dict[str, Any]:
    """Run RoBERTa plain (compassion/contempt only)."""
    try:
        result = run_go_emotions(transcript, "roberta_go_emotions")
        score = normalize_roberta_plain_to_1_5(result)
        
        # Extract top 3 emotions
        avg_scores = result.get("average_scores", {})
        top_emotions = sorted(avg_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        top_emotions_list = [{"emotion": emo, "score": round(score_val, 4)} 
                            for emo, score_val in top_emotions]
        
        return {
            'method': 'roberta_plain',
            'scores': {'compassion_contempt': score},
            'raw_result': result,
            'top_3_emotions': top_emotions_list,
            'error': None
        }
    except Exception as e:
        logging.error(f"  Error in RoBERTa Plain: {e}")
        return {
            'method': 'roberta_plain',
            'scores': {},
            'raw_result': None,
            'top_3_emotions': [],
            'error': str(e)
        }

def run_roberta_valence(transcript: str) -> Dict[str, Any]:
    """Run RoBERTa valence (compassion/contempt only)."""
    try:
        result = run_valence_analysis(transcript, "roberta_go_emotions")
        score = normalize_roberta_valence_to_1_5(result)
        
        # Extract top 3 emotions from RoBERTa result
        avg_scores = result.get("roberta_average_scores", {})
        top_emotions = sorted(avg_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        top_emotions_list = [{"emotion": emo, "score": round(score_val, 4)} 
                            for emo, score_val in top_emotions]
        
        return {
            'method': 'roberta_valence',
            'scores': {'compassion_contempt': score},
            'raw_result': result,
            'top_3_emotions': top_emotions_list,
            'error': None
        }
    except Exception as e:
        logging.error(f"  Error in RoBERTa Valence: {e}")
        return {
            'method': 'roberta_valence',
            'scores': {},
            'raw_result': None,
            'top_3_emotions': [],
            'error': str(e)
        }

# ============================================================================
# MAIN PIPELINE
# ============================================================================

def run_all_models_on_gold_standard(run_number: int = 1):
    """Run all 6 models on gold standard videos."""
    logging.info("="*80)
    logging.info(f"RUNNING MODELS ON GOLD STANDARD VIDEOS - RUN #{run_number}")
    logging.info("="*80)
    
    # Set up MLflow tracking
    if HAS_MLFLOW:
        mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
        run_name = f"gold_standard_run_{run_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        mlflow_run = mlflow.start_run(run_name=run_name)
        mlflow.log_param("run_number", run_number)
        mlflow.log_param("timestamp", datetime.now().isoformat())
    else:
        mlflow_run = None
    
    # Create run-specific output directory
    run_output_dir = os.path.join(OUTPUT_DIR, f"run_{run_number}")
    os.makedirs(run_output_dir, exist_ok=True)
    
    # Load gold standard
    logging.info(f"\nLoading gold standard from: {GOLD_STANDARD_PATH}")
    gold_df = pd.read_csv(GOLD_STANDARD_PATH)
    logging.info(f"Loaded {len(gold_df)} videos from gold standard")
    
    if HAS_MLFLOW:
        mlflow.log_param("total_videos", len(gold_df))
    
    # Load transcripts from .docx
    logging.info("\nLoading transcripts from Transcripts.docx...")
    docx_transcripts = parse_transcripts_docx()
    logging.info(f"Found {len(docx_transcripts)} transcripts in .docx")
    
    if HAS_MLFLOW:
        mlflow.log_param("docx_transcripts_count", len(docx_transcripts))
    
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
        
        # Run all 6 models
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
        
        # 1. OpenAI without RoBERTa
        logging.info("  Running OpenAI (no RoBERTa)...")
        video_results['methods']['openai_no_roberta'] = run_openai_without_roberta(transcript)
        
        # 2. OpenAI with RoBERTa
        logging.info("  Running OpenAI (with RoBERTa)...")
        video_results['methods']['openai_with_roberta'] = run_openai_with_roberta(transcript)
        
        # 3. Gemini without RoBERTa
        logging.info("  Running Gemini (no RoBERTa)...")
        video_results['methods']['gemini_no_roberta'] = run_gemini_without_roberta(transcript)
        
        # 4. Gemini with RoBERTa
        logging.info("  Running Gemini (with RoBERTa)...")
        video_results['methods']['gemini_with_roberta'] = run_gemini_with_roberta(transcript)
        
        # 5. RoBERTa Plain
        logging.info("  Running RoBERTa Plain...")
        video_results['methods']['roberta_plain'] = run_roberta_plain(transcript)
        
        # 6. RoBERTa Valence
        logging.info("  Running RoBERTa Valence...")
        video_results['methods']['roberta_valence'] = run_roberta_valence(transcript)
        
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
    json_path = os.path.join(run_output_dir, f"model_scores_detailed_{timestamp}.json")
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
    csv_path = os.path.join(run_output_dir, f"model_scores_{timestamp}.csv")
    df_scores.to_csv(csv_path, index=False)
    logging.info(f"✓ Model scores CSV saved to: {csv_path}")
    
    if HAS_MLFLOW:
        mlflow.log_artifact(csv_path, "model_scores")
    
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
        for method in ['openai_no_roberta', 'openai_with_roberta', 'gemini_no_roberta', 
                      'gemini_with_roberta', 'roberta_plain', 'roberta_valence']:
            method_cols = [c for c in df_scores.columns if c.startswith(f"{method}_")]
            if method_cols:
                success_count = df_scores[method_cols[0]].notna().sum()
                mlflow.log_metric(f"{method}_success_rate", success_count / len(df_scores))
    
    logging.info(f"\n✅ Completed! Processed {len(all_results)} videos")
    logging.info(f"   Results saved to: {run_output_dir}/")
    
    if HAS_MLFLOW:
        mlflow.end_run()
        logging.info(f"   MLflow run logged: {run_name}")
    
    return all_results, df_scores

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run models on gold standard videos')
    parser.add_argument('--run-number', type=int, default=1, 
                       help='Run number (1 for first run, 2 for second run, etc.)')
    parser.add_argument('--compassion-only', action='store_true',
                       help='Only analyze compassion_contempt dimension (still calls all 5 for consistency)')
    
    args = parser.parse_args()
    
    try:
        results, scores_df = run_all_models_on_gold_standard(run_number=args.run_number)
        print(f"\n{'='*80}")
        print(f"SUCCESS! Processed {len(results)} videos (Run #{args.run_number})")
        print(f"{'='*80}")
        if HAS_MLFLOW:
            print(f"   MLflow tracking: Enabled")
            print(f"   View results: mlflow ui")
    except Exception as e:
        logging.error(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        raise

