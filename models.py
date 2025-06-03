# import nltk
# nltk.data.path.append("C:/Users/HOME/nltk_data")  # Add your preferred path
# nltk.download('punkt', download_dir='C:/Users/HOME/nltk_data')
from collections import defaultdict
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
# from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktParameters
import re
import pandas as pd
from functools import lru_cache
import io

# ────────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ────────────────────────────────────────────────────────────────────────────────
RESPECT = {"admiration", "approval", "caring"}
CONTEMPT = {"annoyance", "disapproval", "disgust"}
ALL_EMOTIONS = sorted(
    list(RESPECT | CONTEMPT | {        # keep key ones first
        "neutral", "joy", "sadness", "anger", "fear", "surprise", "optimism",
        "gratitude", "curiosity", "confusion", "excitement", "embarrassment",
        "love", "desire", "remorse", "relief", "grief", "nervousness", "pride",
        "amusement", "disappointment", "realization"
    })
)

# ────────────────────────────────────────────────────────────────────────────────
# UTILITIES
# ────────────────────────────────────────────────────────────────────────────────
_SIMPLE_SPLIT = re.compile(r'(?<=[.!?])\s+').split
def split_into_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SIMPLE_SPLIT(text.strip().replace("\n", " ")) if s.strip()]

@lru_cache  # keeps it in memory across calls
def _get_classifier(model_type: str):
    if model_type == "roberta_go_emotions":
        model_name = "SamLowe/roberta-base-go_emotions"
    elif model_type == "go_emotions":
        model_name = "monologg/bert-base-cased-goemotions-original"
    else:
        raise ValueError("model_type must be 'go_emotions' or 'roberta_go_emotions'")
    clf = pipeline("text-classification", model=model_name, top_k=None)
    return clf

# ────────────────────────────────────────────────────────────────────────────────
# CORE LOGIC
# ────────────────────────────────────────────────────────────────────────────────
def analyse_transcript(transcript: str, model_type: str) -> dict:
    clf = _get_classifier(model_type)
    scores, counts = defaultdict(float), defaultdict(int)

    for sent in split_into_sentences(transcript):
        for emo in clf(sent[:500])[0]:
            scores[emo["label"]] += emo["score"]
            counts[emo["label"]] += 1

    avg = {l: scores[l] / counts[l] for l in scores}
    dominant = max(avg, key=avg.get)

    comb = {**{k: avg[k] for k in RESPECT if k in avg},
            **{k: avg[k] for k in CONTEMPT if k in avg}}
    dom_att = max(comb, key=comb.get) if comb else None

    return {
        "average_scores": avg,
        "dominant_emotion": dominant,
        "dominant_emotion_score": avg[dominant],
        "dominant_attitude_emotion": dom_att,
        "dominant_attitude_score": comb.get(dom_att, 0)
    }

def to_dataframe(emotion_result: dict) -> pd.DataFrame:
    """One-row DataFrame with 28 emotion columns."""
    row = {emo: emotion_result["average_scores"].get(emo, 0) for emo in ALL_EMOTIONS}
    row.update({
        "dominant_emotion": emotion_result["dominant_emotion"],
        "dominant_emotion_score": emotion_result["dominant_emotion_score"],
        "dominant_attitude_emotion": emotion_result["dominant_attitude_emotion"],
        "dominant_attitude_score": emotion_result["dominant_attitude_score"],
    })
    return pd.DataFrame([row])

def save_styled_excel(df: pd.DataFrame, save_path: str):
    import os, xlsxwriter
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with pd.ExcelWriter(save_path, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Emotions")
        wb, ws = writer.book, writer.sheets["Emotions"]

        yellow = wb.add_format({'bold': True, 'bg_color': '#FFFACD'})
        red    = wb.add_format({'bold': True, 'bg_color': '#FFD4D4'})

        for idx, col in enumerate(df.columns, 0):  # 0-based here
            if col in RESPECT:
                ws.set_column(idx, idx, 14, yellow)
            elif col in CONTEMPT:
                ws.set_column(idx, idx, 14, red)
            else:
                ws.set_column(idx, idx, 14)

# Add the new function to create styled Excel in bytes
def create_styled_excel_bytes(df: pd.DataFrame) -> io.BytesIO:
    """Creates a styled Excel file in memory and returns it as a BytesIO object."""
    import io, xlsxwriter

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Emotions")
        wb, ws = writer.book, writer.sheets["Emotions"]

        yellow = wb.add_format({'bold': True, 'bg_color': '#FFFACD'})
        red    = wb.add_format({'bold': True, 'bg_color': '#FFD4D4'})
        bold_format = wb.add_format({'bold': True})

        # Apply column styling based on emotion names in models.RESPECT/CONTEMPT for score columns
        header_map = {col: idx for idx, col in enumerate(df.columns)}

        for emo in ALL_EMOTIONS:
            col_name = emo
            if col_name in header_map:
                col_idx = header_map[col_name]
                if emo in RESPECT:
                    ws.set_column(col_idx, col_idx, 14, yellow)
                elif emo in CONTEMPT:
                    ws.set_column(col_idx, col_idx, 14, red)
                else:
                    ws.set_column(col_idx, col_idx, 14)

        # Apply styling to dominant columns (bolding and conditional coloring)
        dominant_cols = ["dominant_emotion", "dominant_emotion_score", "dominant_attitude_emotion", "dominant_attitude_score"]
        for col in dominant_cols:
            if col in header_map:
                col_idx = header_map[col]
                ws.set_column(col_idx, col_idx, 18, bold_format) # Apply bold format

                # Apply conditional formatting for background color based on dominant emotion
                if col in ["dominant_emotion", "dominant_attitude_emotion"]:
                    # Define formats for conditional formatting (yellow for RESPECT, red for CONTEMPT)
                    cf_yellow = wb.add_format({'bg_color': '#FFFACD'})
                    cf_red = wb.add_format({'bg_color': '#FFD4D4'})

                    # Apply conditional formatting rule: if cell value is in RESPECT, format yellow
                    ws.conditional_format(1, col_idx, len(df), col_idx,  # Apply to data rows
                        {'type': 'text', 'criteria': 'containing', 'value': ', '.join(list(RESPECT)), 'format': cf_yellow})

                    # Apply conditional formatting rule: if cell value is in CONTEMPT, format red
                    ws.conditional_format(1, col_idx, len(df), col_idx,  # Apply to data rows
                        {'type': 'text', 'criteria': 'containing', 'value': ', '.join(list(CONTEMPT)), 'format': cf_red})


    output.seek(0)
    return output

# one-shot wrapper ----------------------------------------------------------------
def run_go_emotions(transcript: str, model_type: str,
                    file_name: str | None = None) -> dict:
    res = analyse_transcript(transcript, model_type)
    if file_name:
        if not file_name.endswith(".xlsx"):
            file_name += ".xlsx"
        save_styled_excel(to_dataframe(res), f"results/{file_name}")
    return res


if __name__ == "__main__":
    run_go_emotions()
