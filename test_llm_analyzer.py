import os
import json
import logging
import mlflow
import llm_analyzer
from typing import List, Dict

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
MLFLOW_EXPERIMENT_NAME = "Peace Speech Dimension Analysis"
EVAL_SET_FILE = "eval_set.json"
MODELS_TO_TEST = ["openai", "gemini"]
PROMPT_VERSIONS_TO_TEST = ["v1", "v2"] # We will now test both versions

# --- Helper Functions ---

def load_eval_set(file_path: str) -> List[Dict]:
    """Loads the evaluation set from a JSON file."""
    if not os.path.exists(file_path):
        logging.error(f"Evaluation set file not found: {file_path}")
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def compare_results(expected: List[Dict], actual: List[Dict]) -> (int, int, float): # type: ignore
    """Compares expected vs actual results and calculates Mean Absolute Error."""
    total_metrics = 0
    errors = []
    
    expected_map = {item['dimension']: item for item in expected}

    if not actual:
        logging.warning("Actual result is empty or None. Cannot compare.")
        # Return a high error value if the model failed to produce output
        return len(expected), 0, float(len(expected) * 10) # Max possible error

    for actual_item in actual:
        dim = actual_item['dimension']
        if dim in expected_map:
            total_metrics += 1
            expected_item = expected_map[dim]
            
            try:
                # Ensure scores are integers before comparing
                expected_score = int(expected_item['score'])
                actual_score = int(actual_item['score'])
                
                diff = abs(expected_score - actual_score)
                if diff > 0:
                    logging.warning(
                        f"    - DEVIATION for '{dim}': Expected {expected_score}, Got {actual_score} (Difference: {diff})"
                    )
                    errors.append(diff)
                else:
                    logging.info(f"    - PERFECT Score for '{dim}': Expected {expected_score}, Got {actual_score}")
            
            except (ValueError, TypeError) as e:
                logging.error(f"    - TYPE ERROR for '{dim}': Could not convert scores to integers. Expected={expected_item.get('score')}, Got={actual_item.get('score')}. Error: {e}")
                errors.append(10) # Assign max error for non-integer scores

    mae = sum(errors) / total_metrics if total_metrics > 0 else 0.0
    return total_metrics, len(errors), mae


# --- Main Execution ---

if __name__ == "__main__":
    eval_set = load_eval_set(EVAL_SET_FILE)
    if not eval_set:
        exit()

    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
    
    logging.info(f"--- Starting evaluation with {len(eval_set)} test cases across {len(MODELS_TO_TEST)} models and {len(PROMPT_VERSIONS_TO_TEST)} prompt versions ---")

    for model_name in MODELS_TO_TEST:
        for prompt_version in PROMPT_VERSIONS_TO_TEST:
            with mlflow.start_run(run_name=f"{model_name}_{prompt_version}"):
                
                logging.info(f"\n{'='*50}\nEVALUATING MODEL: {model_name.upper()} | PROMPT: {prompt_version}\n{'='*50}")
                
                # Log parameters for this run
                mlflow.log_param("model_name", model_name)
                mlflow.log_param("prompt_version", prompt_version)
                
                total_mae = 0
                total_test_cases = 0

                for test_case in eval_set:
                    test_case_id = test_case['id']
                    logging.info(f"--- Running test case: {test_case_id} ---")

                    try:
                        analysis = llm_analyzer.analyze_transcript_with_llm(
                            transcript=test_case["transcript"],
                            model_name=model_name,
                            prompt_version=prompt_version
                        )
                        
                        _, _, mae = compare_results(test_case["expected_output"], analysis)
                        total_mae += mae
                        total_test_cases += 1

                    except Exception as e:
                        logging.error(f"Test case '{test_case_id}' failed with an exception: {e}")
                        # If a test case fails entirely, we can't calculate MAE for it.
                        # Depending on strictness, you might want to penalize this.
                        # For now, we just log it and move on.

                # Calculate and log the overall average MAE for this run
                if total_test_cases > 0:
                    overall_mae = total_mae / total_test_cases
                    logging.info(f"\n--- Evaluation complete for {model_name.upper()} with prompt {prompt_version} ---")
                    logging.info(f"Overall Mean Absolute Error (MAE): {overall_mae:.2f}")
                    mlflow.log_metric("overall_mae", overall_mae)
                else:
                    logging.warning(f"No test cases were successfully run for {model_name.upper()} with prompt {prompt_version}.")

    logging.info("\nAll evaluations complete. Run 'mlflow ui' in your terminal to see the results.")
