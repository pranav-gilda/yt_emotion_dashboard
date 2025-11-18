"""
Unified Testing Framework for All Analysis Mechanisms

This script tests and compares 4 different scoring approaches:
1. Plain RoBERTa emotion scores (averaged across respect/contempt)
2. Valence-scaled RoBERTa (mapped to 1-5 scale)
3. LLM V1 prompt (plain LLM without RoBERTa context)
4. LLM V3_FINAL (RoBERTa + LLM combined logic)

All scores are normalized to a 0-5 scale for comparison.
"""

import pandas as pd
import logging
import json
import os
from typing import Dict, List, Any
from datetime import datetime
import xlsxwriter

# Import the different analysis mechanisms
from models import run_go_emotions, RESPECT, CONTEMPT
from scale import run_valence_analysis
from llm_analyzer import analyze_transcript_with_llm, PROMPTS

# Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TRANSCRIPT_CORPUS_PATH = "transcript_corpus_v2.csv"
OUTPUT_DIR = "comparison_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================================
# SCORE NORMALIZATION FUNCTIONS
# ============================================================================

def normalize_roberta_respect_contempt(roberta_result: Dict) -> float:
    """
    Convert RoBERTa respect/contempt scores to 0-5 scale.
    
    Logic:
    - Calculate average respect score
    - Calculate average contempt score
    - Net score = respect - contempt (ranges from -1 to +1)
    - Map to 0-5: score_0_5 = 2.5 + (net_score * 2.5)
    """
    avg_scores = roberta_result.get("average_scores", {})
    
    respect_scores = [avg_scores.get(emo, 0) for emo in RESPECT]
    contempt_scores = [avg_scores.get(emo, 0) for emo in CONTEMPT]
    
    avg_respect = sum(respect_scores) / len(respect_scores) if respect_scores else 0
    avg_contempt = sum(contempt_scores) / len(contempt_scores) if contempt_scores else 0
    
    net_score = avg_respect - avg_contempt  # ranges from -1 to +1
    score_0_5 = 2.5 + (net_score * 2.5)  # map to 0-5
    
    return round(max(0, min(5, score_0_5)), 4)


def normalize_valence_score(valence_result: Dict) -> float:
    """
    The valence analysis already outputs a 1-5 scale.
    We just need to shift it to 0-5 (subtract 1 is not right, it's already 1-5).
    Actually, keep it as is since 1-5 is close enough to 0-5 for comparison.
    But to be consistent, we'll map 1-5 to 0-5: (score - 1) / 4 * 5
    
    Wait, let me reconsider: The scale.py gives 1-5 based on formula: 3 + (valence_100/50)
    So 1 = very negative, 5 = very positive, 3 = neutral
    To map to 0-5: We can just subtract 1, or keep as is.
    Let's keep as 1-5 but relabel as 0-5 by subtracting 1.
    """
    score_1_5 = valence_result.get("human_rater_score_1_to_5", 3.0)
    score_0_5 = score_1_5 - 1  # shift from 1-5 to 0-5
    return round(max(0, min(5, score_0_5)), 4)


def normalize_llm_v1_score(llm_result: Dict) -> float:
    """
    LLM V1 outputs scores on -5 to +5 scale for each dimension.
    We'll focus on 'compassion_vs_contempt' dimension.
    Map -5 to +5 to 0-5: score_0_5 = (score + 5) / 2
    """
    compassion_score = llm_result.get("compassion_vs_contempt", {}).get("score", 0)
    score_0_5 = (compassion_score + 5) / 2  # map from -5..+5 to 0..5
    return round(max(0, min(5, score_0_5)), 4)


def normalize_llm_v3_score(llm_result: Dict) -> float:
    """
    LLM V3_FINAL outputs 'compassion_vs_contempt' on 0-100 scale.
    Map 0-100 to 0-5: score_0_5 = score / 20
    """
    compassion_score = llm_result.get("compassion_vs_contempt", {}).get("score", 50)
    score_0_5 = compassion_score / 20  # map from 0..100 to 0..5
    return round(max(0, min(5, score_0_5)), 4)


# ============================================================================
# ANALYSIS RUNNERS
# ============================================================================

def run_roberta_plain(transcript: str) -> Dict[str, Any]:
    """Run plain RoBERTa analysis and return normalized score."""
    try:
        roberta_result = run_go_emotions(transcript, "roberta_go_emotions")
        normalized_score = normalize_roberta_respect_contempt(roberta_result)
        
        return {
            "method": "RoBERTa_Plain",
            "score_0_5": normalized_score,
            "raw_result": roberta_result,
            "dominant_emotion": roberta_result.get("dominant_emotion"),
            "dominant_attitude": roberta_result.get("dominant_attitude_emotion"),
            "error": None
        }
    except Exception as e:
        logging.error(f"RoBERTa Plain analysis failed: {e}")
        return {
            "method": "RoBERTa_Plain",
            "score_0_5": None,
            "raw_result": None,
            "error": str(e)
        }


def run_valence_scaled(transcript: str) -> Dict[str, Any]:
    """Run valence-scaled RoBERTa analysis and return normalized score."""
    try:
        valence_result = run_valence_analysis(transcript, "roberta_go_emotions")
        normalized_score = normalize_valence_score(valence_result)
        
        return {
            "method": "RoBERTa_Valence_Scaled",
            "score_0_5": normalized_score,
            "raw_result": valence_result,
            "valence_100": valence_result.get("valence_score_100"),
            "original_1_5": valence_result.get("human_rater_score_1_to_5"),
            "error": None
        }
    except Exception as e:
        logging.error(f"Valence Scaled analysis failed: {e}")
        return {
            "method": "RoBERTa_Valence_Scaled",
            "score_0_5": None,
            "raw_result": None,
            "error": str(e)
        }


def run_llm_v1(transcript: str, model_provider: str = "openai") -> Dict[str, Any]:
    """Run LLM V1 analysis (plain prompt) and return normalized score."""
    try:
        llm_result = analyze_transcript_with_llm(
            transcript=transcript,
            model_provider=model_provider,
            prompt_version="v1"
        )
        normalized_score = normalize_llm_v1_score(llm_result)
        
        return {
            "method": f"LLM_V1_{model_provider}",
            "score_0_5": normalized_score,
            "raw_result": llm_result,
            "all_dimensions": llm_result,
            "error": None
        }
    except Exception as e:
        logging.error(f"LLM V1 analysis failed: {e}")
        return {
            "method": f"LLM_V1_{model_provider}",
            "score_0_5": None,
            "raw_result": None,
            "error": str(e)
        }


def run_llm_v3(transcript: str, model_provider: str = "openai") -> Dict[str, Any]:
    """Run LLM V3_FINAL analysis (RoBERTa + LLM) and return normalized score."""
    try:
        llm_result = analyze_transcript_with_llm(
            transcript=transcript,
            model_provider=model_provider,
            prompt_version="v3_final"
        )
        normalized_score = normalize_llm_v3_score(llm_result)
        
        return {
            "method": f"LLM_V3_FINAL_{model_provider}",
            "score_0_5": normalized_score,
            "raw_result": llm_result,
            "all_dimensions": llm_result,
            "top_emotions": llm_result.get("top_emotions", []),
            "error": None
        }
    except Exception as e:
        logging.error(f"LLM V3_FINAL analysis failed: {e}")
        return {
            "method": f"LLM_V3_FINAL_{model_provider}",
            "score_0_5": None,
            "raw_result": None,
            "error": str(e)
        }


# ============================================================================
# MAIN COMPARISON PIPELINE
# ============================================================================

def analyze_single_transcript(transcript: str, video_id: str, title: str) -> Dict[str, Any]:
    """
    Run all 4 analysis methods on a single transcript.
    Returns a dictionary with all results.
    """
    logging.info(f"\n{'='*80}")
    logging.info(f"Analyzing: {title[:60]}... (ID: {video_id})")
    logging.info(f"{'='*80}")
    
    results = {
        "video_id": video_id,
        "title": title,
        "transcript_length": len(transcript),
        "methods": {}
    }
    
    # Method 1: Plain RoBERTa
    logging.info("Running RoBERTa Plain...")
    results["methods"]["roberta_plain"] = run_roberta_plain(transcript)
    
    # Method 2: Valence-scaled RoBERTa
    logging.info("Running RoBERTa Valence Scaled...")
    results["methods"]["roberta_valence"] = run_valence_scaled(transcript)
    
    # Method 3: LLM V1 (Plain prompt)
    logging.info("Running LLM V1 (OpenAI)...")
    results["methods"]["llm_v1"] = run_llm_v1(transcript, "openai")
    
    # Method 4: LLM V3_FINAL (RoBERTa + LLM)
    logging.info("Running LLM V3_FINAL (OpenAI)...")
    results["methods"]["llm_v3"] = run_llm_v3(transcript, "openai")
    
    # Print summary
    logging.info("\n--- RESULTS SUMMARY (0-5 scale) ---")
    for method_key, method_result in results["methods"].items():
        score = method_result.get("score_0_5", "ERROR")
        logging.info(f"  {method_result['method']:30s}: {score}")
    
    return results


def run_comparison_on_corpus(num_samples: int = None, sample_ids: List[str] = None):
    """
    Run all analysis methods on the transcript corpus.
    
    Args:
        num_samples: Number of random samples to analyze (if None, analyze all)
        sample_ids: Specific video IDs to analyze (if provided, overrides num_samples)
    """
    # Load corpus
    logging.info(f"Loading transcript corpus from: {TRANSCRIPT_CORPUS_PATH}")
    df = pd.read_csv(TRANSCRIPT_CORPUS_PATH)
    logging.info(f"Loaded {len(df)} transcripts")
    
    # Sample if requested
    if sample_ids:
        df = df[df['video_id'].isin(sample_ids)]
        logging.info(f"Filtered to {len(df)} specific video IDs")
    elif num_samples and num_samples < len(df):
        df = df.sample(n=num_samples, random_state=42)
        logging.info(f"Randomly sampled {num_samples} transcripts")
    
    # Run analysis on each transcript
    all_results = []
    for idx, row in df.iterrows():
        try:
            result = analyze_single_transcript(
                transcript=row['full_transcript'],
                video_id=row['video_id'],
                title=row['title']
            )
            result["category"] = row.get("category", "Unknown")
            result["channel"] = row.get("channel", "Unknown")
            all_results.append(result)
        except Exception as e:
            logging.error(f"Failed to analyze video {row['video_id']}: {e}")
            continue
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Save detailed JSON results
    json_path = os.path.join(OUTPUT_DIR, f"detailed_comparison_{timestamp}.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    logging.info(f"\nDetailed results saved to: {json_path}")
    
    # 2. Create comparison DataFrame and save as CSV
    comparison_data = []
    for result in all_results:
        row_data = {
            "video_id": result["video_id"],
            "title": result["title"][:60],
            "category": result.get("category", "Unknown"),
            "channel": result.get("channel", "Unknown"),
            "transcript_length": result["transcript_length"],
        }
        
        # Add scores from each method
        for method_key, method_result in result["methods"].items():
            row_data[f"{method_result['method']}_score"] = method_result.get("score_0_5")
            if method_result.get("error"):
                row_data[f"{method_result['method']}_error"] = method_result["error"]
        
        comparison_data.append(row_data)
    
    comparison_df = pd.DataFrame(comparison_data)
    csv_path = os.path.join(OUTPUT_DIR, f"score_comparison_{timestamp}.csv")
    comparison_df.to_csv(csv_path, index=False, encoding='utf-8')
    logging.info(f"Comparison CSV saved to: {csv_path}")
    
    # 3. Create Excel with formatting
    excel_path = os.path.join(OUTPUT_DIR, f"score_comparison_{timestamp}.xlsx")
    create_comparison_excel(comparison_df, excel_path)
    logging.info(f"Formatted Excel saved to: {excel_path}")
    
    # 4. Print summary statistics
    print_summary_statistics(comparison_df)
    
    return all_results, comparison_df


def create_comparison_excel(df: pd.DataFrame, output_path: str):
    """Create a nicely formatted Excel comparison file."""
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Scores', index=False)
        
        workbook = writer.book
        worksheet = writer.sheets['Scores']
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4F81BD',
            'font_color': 'white',
            'border': 1
        })
        
        score_format = workbook.add_format({
            'num_format': '0.00',
            'align': 'center'
        })
        
        # Format header row
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            
            # Adjust column width
            if 'score' in value.lower():
                worksheet.set_column(col_num, col_num, 15)
            elif 'title' in value.lower():
                worksheet.set_column(col_num, col_num, 40)
            else:
                worksheet.set_column(col_num, col_num, 12)
        
        # Apply score formatting and conditional formatting
        score_cols = [col for col in df.columns if 'score' in col.lower()]
        for col_name in score_cols:
            col_idx = df.columns.get_loc(col_name)
            
            # Apply number format
            worksheet.set_column(col_idx, col_idx, 15, score_format)
            
            # Add conditional formatting (color scale)
            worksheet.conditional_format(1, col_idx, len(df), col_idx, {
                'type': '3_color_scale',
                'min_color': "#F8696B",  # Red for low scores (0)
                'mid_color': "#FFEB84",  # Yellow for mid scores (2.5)
                'max_color': "#63BE7B"   # Green for high scores (5)
            })


def print_summary_statistics(df: pd.DataFrame):
    """Print summary statistics for all methods."""
    print("\n" + "="*80)
    print("SUMMARY STATISTICS (0-5 scale)")
    print("="*80)
    
    score_cols = [col for col in df.columns if 'score' in col.lower() and 'error' not in col.lower()]
    
    summary_data = []
    for col in score_cols:
        stats = df[col].describe()
        summary_data.append({
            "Method": col.replace("_score", ""),
            "Mean": f"{stats['mean']:.3f}",
            "Std": f"{stats['std']:.3f}",
            "Min": f"{stats['min']:.3f}",
            "Max": f"{stats['max']:.3f}",
            "Median": f"{stats['50%']:.3f}",
        })
    
    summary_df = pd.DataFrame(summary_data)
    print(summary_df.to_string(index=False))
    
    # Calculate correlations
    print("\n" + "="*80)
    print("CORRELATION MATRIX")
    print("="*80)
    correlation_matrix = df[score_cols].corr()
    print(correlation_matrix.to_string())
    print("\n")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Compare all analysis methods on transcript corpus")
    parser.add_argument("--num-samples", type=int, default=None, 
                       help="Number of random samples to analyze (default: all)")
    parser.add_argument("--video-ids", nargs="+", default=None,
                       help="Specific video IDs to analyze")
    parser.add_argument("--quick-test", action="store_true",
                       help="Run on just 2 samples for quick testing")
    
    args = parser.parse_args()
    
    if args.quick_test:
        num_samples = 2
        video_ids = None
    else:
        num_samples = args.num_samples
        video_ids = args.video_ids
    
    logging.info("="*80)
    logging.info("UNIFIED MODEL COMPARISON FRAMEWORK")
    logging.info("="*80)
    logging.info("This will compare:")
    logging.info("  1. RoBERTa Plain (respect/contempt averaging)")
    logging.info("  2. RoBERTa Valence Scaled (weighted valence mapping)")
    logging.info("  3. LLM V1 (plain prompt)")
    logging.info("  4. LLM V3_FINAL (RoBERTa + LLM combined)")
    logging.info("="*80 + "\n")
    
    results, comparison_df = run_comparison_on_corpus(
        num_samples=num_samples,
        sample_ids=video_ids
    )
    
    logging.info("\n" + "="*80)
    logging.info("COMPARISON COMPLETE!")
    logging.info(f"Analyzed {len(results)} transcripts")
    logging.info(f"Results saved to: {OUTPUT_DIR}/")
    logging.info("="*80)

