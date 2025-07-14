# YouTube Emotion Analyzer & Transcript Parser 🚦

A full-stack solution for analyzing YouTube video emotions using a Chrome extension and FastAPI backend. Visualize respect/contempt and all 28 GoEmotions with a modern speedometer UI and detailed modal.

---

## Features
- 🧠 **FastAPI backend**: Processes YouTube video transcripts, runs RoBERTa-GoEmotions, and returns per-emotion and aggregate scores (Respect, Contempt, Positive, Negative, Neutral).
- 🌐 **Chrome extension**: Auto-detects YouTube videos, overlays a speedometer UI, and provides a "Learn More" modal with all emotion scores and categories.
- 🎨 **Modern UI/UX**: Clean, color-coded, and demo-ready overlay and modal. Refresh and info buttons, dominant emotion/attitude display, and responsive design.
- 📊 **Excel export**: Download enriched emotion history as Excel (via backend endpoint).
- 🔒 **Configurable**: Uses environment variables and S3 for storage (if configured).

---

## Installation & Usage

### 1. Backend (FastAPI)
```sh
pip install -r requirements.txt
python main.py
```
- The API runs on `http://localhost:8080` by default.

### 2. Chrome Extension
- Load the `extension/` folder as an unpacked extension in Chrome.
- The overlay will auto-appear on YouTube video pages.
- Click the refresh icon (top-left) to re-analyze, or "Learn More" for emotion details.

---

## Emotion Categories
- **Respect**: Admiration, Approval, Caring
- **Contempt**: Disapproval, Disgust, Annoyance
- **Positive**: Amusement, Excitement, Joy, Love, Optimism, Pride, Relief, Gratitude
- **Neutral**: Confusion, Curiosity, Desire, Realization, Surprise, Neutral
- **Negative**: Anger, Disappointment, Embarrassment, Fear, Grief, Nervousness, Remorse, Sadness


For questions or demo instructions, see the code comments or contact the author.
