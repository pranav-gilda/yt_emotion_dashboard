"""
Setup Verification Script

Run this script to verify that all components are properly installed and configured.
"""

import sys
import os

def print_header(text):
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80)

def print_status(check_name, status, message=""):
    icon = "✅" if status else "❌"
    print(f"{icon} {check_name:<40} {message}")

def check_imports():
    """Check if all required packages are installed."""
    print_header("Checking Package Installations")
    
    packages = {
        "pandas": "pandas",
        "numpy": "numpy",
        "transformers": "transformers (HuggingFace)",
        "torch": "torch (PyTorch)",
        "openai": "openai",
        "google.generativeai": "google-generativeai",
        "xlsxwriter": "xlsxwriter",
        "scipy": "scipy",
        "sklearn": "scikit-learn",
        "matplotlib": "matplotlib",
        "seaborn": "seaborn",
    }
    
    all_good = True
    for module, display_name in packages.items():
        try:
            __import__(module)
            print_status(display_name, True, "Installed")
        except ImportError:
            print_status(display_name, False, "NOT INSTALLED")
            all_good = False
    
    return all_good

def check_api_keys():
    """Check if API keys are configured."""
    print_header("Checking API Keys")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print_status("python-dotenv", False, "NOT INSTALLED (optional but recommended)")
    
    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    if openai_key:
        print_status("OPENAI_API_KEY", True, f"Found ({openai_key[:8]}...)")
    else:
        print_status("OPENAI_API_KEY", False, "Not set (required for LLM methods)")
    
    if gemini_key:
        print_status("GEMINI_API_KEY", True, f"Found ({gemini_key[:8]}...)")
    else:
        print_status("GEMINI_API_KEY", False, "Not set (optional, OpenAI can be used instead)")
    
    return bool(openai_key or gemini_key)

def check_files():
    """Check if required files exist."""
    print_header("Checking Required Files")
    
    files = {
        "models.py": "Core RoBERTa analysis",
        "scale.py": "Valence scaling",
        "llm_analyzer.py": "LLM analysis",
        "compare_all_models.py": "Main comparison script",
        "validate_against_human.py": "Validation script",
        "transcript_corpus_v2.csv": "Transcript data",
    }
    
    all_good = True
    for file, description in files.items():
        exists = os.path.exists(file)
        print_status(description, exists, file)
        if not exists:
            all_good = False
    
    return all_good

def check_transcript_data():
    """Check transcript corpus data."""
    print_header("Checking Transcript Corpus")
    
    corpus_file = "transcript_corpus_v2.csv"
    if not os.path.exists(corpus_file):
        print_status("Corpus file exists", False, "File not found")
        return False
    
    try:
        import pandas as pd
        df = pd.read_csv(corpus_file)
        
        print_status("Corpus loaded", True, f"{len(df)} transcripts")
        
        required_cols = ['video_id', 'title', 'full_transcript']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            print_status("Required columns", False, f"Missing: {missing_cols}")
            return False
        else:
            print_status("Required columns", True, "All present")
        
        # Check for actual transcript data
        empty_transcripts = df['full_transcript'].isna().sum()
        if empty_transcripts > 0:
            print_status("Transcript data", False, f"{empty_transcripts} empty transcripts")
        else:
            print_status("Transcript data", True, "All transcripts have data")
        
        return True
        
    except Exception as e:
        print_status("Corpus loading", False, f"Error: {e}")
        return False

def test_roberta():
    """Test RoBERTa analysis."""
    print_header("Testing RoBERTa Analysis")
    
    try:
        from models import run_go_emotions
        
        test_text = "I admire the caring and compassionate approach. This is wonderful!"
        
        print("Running test analysis...")
        result = run_go_emotions(test_text, "roberta_go_emotions")
        
        print_status("RoBERTa analysis", True, f"Dominant emotion: {result['dominant_emotion']}")
        
        # Check if it detected positive emotions
        avg_scores = result.get('average_scores', {})
        positive_emotions = ['admiration', 'caring', 'joy']
        detected = any(avg_scores.get(emo, 0) > 0.1 for emo in positive_emotions)
        
        if detected:
            print_status("Emotion detection", True, "Correctly detected positive emotions")
        else:
            print_status("Emotion detection", False, "May not be detecting emotions properly")
        
        return True
        
    except Exception as e:
        print_status("RoBERTa test", False, f"Error: {e}")
        return False

def test_valence():
    """Test valence scaling."""
    print_header("Testing Valence Scaling")
    
    try:
        from scale import run_valence_analysis
        
        test_text = "I love this amazing work. It brings me joy and gratitude."
        
        print("Running valence analysis...")
        result = run_valence_analysis(test_text, "roberta_go_emotions")
        
        score = result.get('human_rater_score_1_to_5', 0)
        print_status("Valence scaling", True, f"Score (1-5): {score:.2f}")
        
        # Should be positive (>3) for this text
        if score > 3:
            print_status("Score validation", True, "Correctly identified as positive")
        else:
            print_status("Score validation", False, f"Expected >3, got {score:.2f}")
        
        return True
        
    except Exception as e:
        print_status("Valence test", False, f"Error: {e}")
        return False

def test_directories():
    """Check if output directories will be created properly."""
    print_header("Checking Output Directories")
    
    dirs = ["comparison_results", "validation_results"]
    
    for dir_name in dirs:
        if os.path.exists(dir_name):
            print_status(f"{dir_name}/", True, "Exists")
        else:
            print_status(f"{dir_name}/", True, "Will be created when needed")
    
    return True

def main():
    """Run all checks."""
    print("\n" + "🔍 " + "="*76)
    print("  SETUP VERIFICATION SCRIPT")
    print("  Checking if everything is ready for model comparison...")
    print("="*80)
    
    checks = {
        "Package installations": check_imports(),
        "API keys": check_api_keys(),
        "Required files": check_files(),
        "Transcript data": check_transcript_data(),
        "Output directories": test_directories(),
        "RoBERTa analysis": test_roberta(),
        "Valence scaling": test_valence(),
    }
    
    # Summary
    print_header("SUMMARY")
    
    passed = sum(checks.values())
    total = len(checks)
    
    print(f"\nPassed: {passed}/{total} checks")
    
    if passed == total:
        print("\n🎉 " + "="*76)
        print("  ALL CHECKS PASSED!")
        print("  You're ready to run: python compare_all_models.py --quick-test")
        print("="*80 + "\n")
        return 0
    else:
        print("\n⚠️  " + "="*76)
        print("  SOME CHECKS FAILED")
        print("="*80)
        
        print("\n📋 Action Items:")
        
        if not checks["Package installations"]:
            print("  1. Install missing packages: pip install -r requirements.txt")
        
        if not checks["API keys"]:
            print("  2. Set up API keys in .env file (needed for LLM methods)")
            print("     - Get OpenAI key: https://platform.openai.com/api-keys")
            print("     - Get Gemini key: https://makersuite.google.com/app/apikey")
        
        if not checks["Required files"]:
            print("  3. Ensure all required Python files are present")
        
        if not checks["Transcript data"]:
            print("  4. Run: python build.py (to create transcript corpus)")
        
        print("\n  Note: You can still run RoBERTa methods (free) without API keys!")
        print("="*80 + "\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())

