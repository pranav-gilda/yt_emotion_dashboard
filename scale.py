# This script contains the new valence modeling logic.
# It imports the "Researcher" agent from models.py and applies
# the "Teacher" agent's mathematical transformation.

import pandas as pd
from models import run_go_emotions, ALL_EMOTIONS

# 1. The Valence "Contract" / Rubric
# As defined in our discussion, mapping each emotion to a valence score.
EMOTION_VALENCE_MAP = {
    # Highly Positive (+1.0)
    "joy": 1.0,
    "love": 1.0,
    "admiration": 1.0,
    "gratitude": 1.0,
    "pride": 1.0,
    "excitement": 1.0,
    
    # Mildly Positive (+0.5)
    "approval": 0.5,
    "caring": 0.5,
    "optimism": 0.5,
    "relief": 0.5,
    "amusement": 0.5,
    "curiosity": 0.5,
    
    # Neutral (0.0)
    "neutral": 0.0,
    "realization": 0.0,
    "surprise": 0.0,
    "confusion": 0.0,
    
    # Mildly Negative (-0.5)
    "annoyance": -0.5,
    "disapproval": -0.5,
    "disappointment": -0.5,
    "nervousness": -0.5,
    "remorse": -0.5,
    "desire": -0.5,
    
    # Highly Negative (-1.0)
    "anger": -1.0,
    "disgust": -1.0,
    "fear": -1.0,
    "sadness": -1.0,
    "grief": -1.0,
    "embarrassment": -1.0,
}

# Ensure all 28 emotions from models.py are in our map
def validate_map():
    for emo in ALL_EMOTIONS:
        if emo not in EMOTION_VALENCE_MAP:
            print(f"WARNING: Emotion '{emo}' from models.py is not in the valence map. It will be ignored.")
validate_map()


def calculate_weighted_valence_score(average_scores: dict) -> float:
    """
    Calculates the weighted valence score on a -100 to +100 scale.
    
    Formula: Score = Σ [ (probability * 100) * valence ]
    """
    valence_score_100 = 0.0
    for emotion, probability in average_scores.items():
        # Get the valence for this emotion, defaulting to 0 if not in map
        valence = EMOTION_VALENCE_MAP.get(emotion, 0.0)
        
        # Add to the total score
        # (e.g., 0.6 probability * 100) * +1.0 valence = +60
        # (e.g., 0.3 probability * 100) * -0.5 valence = -15
        valence_score_100 += (probability * 100) * valence
        
    return valence_score_100

def scale_to_human_rater_score(valence_score_100: float) -> float:
    """
    Maps the -100 to +100 score onto the 1-5 human rater scale.
    
    Formula: f(x) = 3 + (x / 50)
    """
    # Clamp the score to the expected [-100, 100] range just in case
    clamped_score = max(-100.0, min(100.0, valence_score_100))
    
    scaled_score = 3.0 + (clamped_score / 50.0)
    
    return scaled_score

def run_valence_analysis(transcript: str, model_type: str = "roberta_go_emotions") -> dict:
    """
    Runs the full analysis pipeline:
    1. Get emotion probabilities from RoBERTa
    2. Calculate the -100 to +100 weighted score
    3. Map to the 1-5 human rater score
    """
    # 1. Run the "Researcher" agent
    roberta_result = run_go_emotions(transcript, model_type)
    average_scores = roberta_result.get("average_scores", {})
    
    # 2. Calculate the weighted score
    valence_score_100 = calculate_weighted_valence_score(average_scores)
    
    # 3. Map to the final 1-5 scale
    human_rater_score_1_to_5 = scale_to_human_rater_score(valence_score_100)
    
    return {
        "transcript": transcript,
        "valence_score_100": round(valence_score_100, 4),
        "human_rater_score_1_to_5": round(human_rater_score_1_to_5, 4),
        "roberta_dominant_emotion": roberta_result.get("dominant_emotion"),
        "roberta_average_scores": average_scores
    }

if __name__ == "__main__":
    # Example for testing this script directly
    test_transcript = (
        "This is amazing! I am so grateful for all the hard work and admiration I have for this team. "
        "I feel a lot of joy. However, that other person makes me angry and I feel a lot of disgust."
    )
    
    analysis = run_valence_analysis(test_transcript)
    
    print("--- Valence Analysis Test ---")
    print(f"Transcript: {test_transcript[:50]}...")
    print(f"Valence Score (-100 to +100): {analysis['valence_score_100']}")
    print(f"Scaled Score (1 to 5): {analysis['human_rater_score_1_to_5']}")
    print(f"Dominant Emotion: {analysis['roberta_dominant_emotion']}")
    print("--- Top 5 Average Scores ---")
    top_5 = sorted(analysis['roberta_average_scores'].items(), key=lambda item: item[1], reverse=True)[:5]
    for emo, score in top_5:
        print(f"- {emo}: {score*100:.2f}%")
