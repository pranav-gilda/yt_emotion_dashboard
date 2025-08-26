import json
import logging
import mlflow
from llm_analyzer import analyze_transcript_with_llm, SYSTEM_PROMPT_V1
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

EVAL_SET_FILE = "eval_set.json"

def load_evaluation_set(file_path: str) -> List[Dict[str, Any]]:
    """Loads the evaluation set from a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Evaluation set file not found at: {file_path}")
        return []
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from the evaluation set file: {file_path}")
        return []

def run_evaluation(model_to_test: str, prompt_version: str):
    """
    Runs the LLM analyzer against the evaluation set and logs results to MLflow.
    """
    eval_set = load_evaluation_set(EVAL_SET_FILE)
    if not eval_set:
        return

    # --- MLflow Integration ---
    # Start an MLflow run. Everything inside this 'with' block will be logged.
    with mlflow.start_run(run_name=f"Eval_{model_to_test}_{prompt_version}"):
        
        # Log the parameters of this experiment
        mlflow.log_param("model_name", model_to_test)
        mlflow.log_param("prompt_version", prompt_version)
        mlflow.log_param("num_test_cases", len(eval_set))
        mlflow.log_text(SYSTEM_PROMPT_V1, "prompt.txt") # Save the actual prompt text

        total_absolute_error = 0
        total_dimensions = 0
        score_errors = {
            "nuance": 0, "creativity_vs_order": 0, "safety_vs_threat": 0,
            "compassion_vs_contempt": 0, "reporting_vs_opinion": 0
        }

        for test_case in eval_set:
            transcript = test_case.get("transcript")
            expected = test_case.get("expected_output")

            try:
                actual = analyze_transcript_with_llm(transcript, model_name=model_to_test)
                
                for dimension, expected_values in expected.items():
                    actual_values = actual.get(dimension, {})
                    expected_score = expected_values.get("score")
                    actual_score = actual_values.get("score")

                    if actual_score is not None and expected_score is not None:
                        error = abs(expected_score - actual_score)
                        score_errors[dimension] += error
                        total_absolute_error += error
                        total_dimensions += 1
            except Exception as e:
                logging.error(f"Test case failed with exception: {e}")

        # --- Log Metrics to MLflow ---
        # Calculate and log the overall Mean Absolute Error
        overall_mae = total_absolute_error / total_dimensions if total_dimensions > 0 else -1
        mlflow.log_metric("overall_mae", overall_mae)

        # Calculate and log the MAE for each individual dimension
        for dim, total_error in score_errors.items():
            mae_dim = total_error / len(eval_set) if eval_set else -1
            mlflow.log_metric(f"mae_{dim}", mae_dim)
            
        logging.info(f"--- Evaluation complete for {model_to_test} ---")
        logging.info(f"Overall MAE: {overall_mae:.2f}")

if __name__ == "__main__":
    # --- Your New Testing Workflow ---
    # Define the experiments you want to run
    models_to_evaluate = ["openai", "gemini"]
    prompt_version = "v1" # You can change this as you iterate on your prompt

    for model in models_to_evaluate:
        run_evaluation(model_to_test=model, prompt_version=prompt_version)
    
    print("\nAll evaluations complete. Run 'mlflow ui' in your terminal to see the results.")
