# Pre-Push Verification Checklist

**Run these checks before pushing to public repository**

---

## ✅ Security Checks

### 1. Verify Sensitive Files Are Ignored

```bash
# These should all return the file paths (meaning they're ignored)
git check-ignore gold_standard.xlsx
git check-ignore transcripts/Transcripts.docx
git check-ignore model_scores_gold_standard/run_*/model_scores_detailed_*.json
git check-ignore mlruns/
```

**Expected:** All commands should return the file paths (confirming they're ignored)

### 2. Check for Hardcoded API Keys

```bash
# Search for potential secrets (should only find environment variable references)
grep -r "api_key\|API_KEY\|sk-" . --exclude-dir=.git --exclude="*.md" --exclude="*.txt" --exclude="*.csv"
```

**Expected:** Should only find `os.getenv("API_KEY")` patterns, NOT actual keys

### 3. Verify No Large Files

```bash
# Find files larger than 10MB
find . -type f -size +10M -not -path "./.git/*"
```

**Expected:** Should be empty or only show files that are intentionally included

---

## ✅ File Status Check

### Review What Will Be Committed

```bash
# See all changes
git status

# See what's staged
git diff --cached --name-only

# See what's untracked
git ls-files --others --excluded --exclude-standard
```

---

## ✅ Final Checklist

Before pushing:

- [x] `.gitignore` updated with sensitive data exclusions
- [ ] No hardcoded API keys in code (only `os.getenv()` references)
- [ ] `gold_standard.xlsx` is ignored
- [ ] Transcript files are ignored
- [ ] Large detailed JSON files are ignored
- [ ] MLflow database is ignored
- [ ] All documentation files are included
- [ ] Core Python scripts are included
- [ ] Summary results (CSV, plots) are included
- [ ] Detailed results (large JSON) are excluded

---

## 🚀 Ready to Push

Once all checks pass:

```bash
# Stage all changes
git add .

# Review what will be committed
git status

# Commit
git commit -m "Add comprehensive documentation and results for public repo"

# Push (when ready)
git push origin main
```

---

**Last Updated:** November 18, 2024

