"""
Parse Transcripts.docx and extract transcripts matched to video titles.
"""
import os
import re
import logging
from typing import Dict, Optional

try:
    from docx import Document
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False
    logging.warning("python-docx not installed. Cannot parse .docx files.")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TRANSCRIPTS_DOCX_PATH = "transcripts/Transcripts.docx"

def normalize_title(title: str) -> str:
    """Normalize title for matching (lowercase, remove special chars)."""
    normalized = re.sub(r'[^\w\s]', '', title.lower())
    normalized = re.sub(r'\s+', '_', normalized.strip())
    return normalized[:50]  # Take first 50 chars

def extract_youtube_id_from_text(text: str) -> Optional[str]:
    """Extract YouTube ID from text (could be in URL or standalone)."""
    import re
    # Try URL patterns
    url_patterns = [
        r'youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'youtu\.be/([a-zA-Z0-9_-]{11})',
        r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        r'youtube\.com/v/([a-zA-Z0-9_-]{11})',
    ]
    for pattern in url_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    # Try standalone 11-char ID
    standalone_match = re.search(r'\b([a-zA-Z0-9_-]{11})\b', text)
    if standalone_match:
        return standalone_match.group(1)
    return None

def parse_transcripts_docx() -> Dict[str, str]:
    """
    Parse Transcripts.docx and return a dictionary mapping normalized titles/IDs to transcripts.
    
    Returns:
        Dict mapping (normalized_title or youtube_id) -> full_transcript_text
        Multiple keys per transcript (by title AND by YouTube ID if found)
    """
    if not HAS_DOCX:
        logging.warning("python-docx not available. Skipping .docx parsing.")
        return {}
    
    if not os.path.exists(TRANSCRIPTS_DOCX_PATH):
        logging.warning(f"Transcripts.docx not found at {TRANSCRIPTS_DOCX_PATH}")
        return {}
    
    logging.info(f"Parsing {TRANSCRIPTS_DOCX_PATH}...")
    
    try:
        doc = Document(TRANSCRIPTS_DOCX_PATH)
        transcripts = {}
        current_title = None
        current_transcript = []
        
        for para in doc.paragraphs:
            text = para.text.strip()
            
            if not text:
                continue
            
            # Check if this looks like a title (short, might be hyperlink, or formatted differently)
            # Titles are often followed by transcript content
            # Look for patterns: hyperlinks, bold text, or short lines that could be titles
            
            # If line is short and looks like a title, start new entry
            if len(text) < 100 and (text.count(' ') < 10):
                # Save previous transcript if exists
                if current_title and current_transcript:
                    transcript_text = ' '.join(current_transcript)
                    if len(transcript_text) > 50:  # Only save if substantial content
                        # Map by normalized title
                        normalized = normalize_title(current_title)
                        transcripts[normalized] = transcript_text
                        
                        # Also try to extract YouTube ID from title and map by that too
                        youtube_id = extract_youtube_id_from_text(current_title)
                        if youtube_id:
                            # Map by YouTube ID (as-is and cleaned)
                            transcripts[youtube_id] = transcript_text
                            if youtube_id.startswith('-') or youtube_id.startswith('_'):
                                transcripts[youtube_id[1:]] = transcript_text
                        
                        logging.debug(f"  Extracted transcript for: {current_title[:50]}")
                
                # Start new entry
                current_title = text
                current_transcript = []
            else:
                # This is transcript content
                if current_title:
                    current_transcript.append(text)
                else:
                    # No title yet, might be at start of doc
                    # Try to extract title from first substantial line
                    if len(text) < 100:
                        current_title = text
                        current_transcript = []
        
        # Save last transcript
        if current_title and current_transcript:
            transcript_text = ' '.join(current_transcript)
            if len(transcript_text) > 50:
                normalized = normalize_title(current_title)
                transcripts[normalized] = transcript_text
                
                # Also map by YouTube ID if found
                youtube_id = extract_youtube_id_from_text(current_title)
                if youtube_id:
                    transcripts[youtube_id] = transcript_text
                    if youtube_id.startswith('-') or youtube_id.startswith('_'):
                        transcripts[youtube_id[1:]] = transcript_text
        
        logging.info(f"  Extracted {len(set(transcripts.values()))} unique transcripts from .docx")
        logging.info(f"  Created {len(transcripts)} mapping keys (by title and YouTube ID)")
        return transcripts
        
    except Exception as e:
        logging.error(f"Error parsing Transcripts.docx: {e}")
        return {}

if __name__ == "__main__":
    transcripts = parse_transcripts_docx()
    print(f"\nExtracted {len(transcripts)} transcripts")
    print("\nSample titles:")
    for i, title in enumerate(list(transcripts.keys())[:5]):
        print(f"  {i+1}. {title}")

