document.addEventListener('DOMContentLoaded', function() {
    // --- State Variables ---
    let lastAnalysisData = null;
    let originalTranscript = '';
    let robertaThumbRating = null;
    let llmThumbRating = null;
    let currentModel = '';

    // --- Element References ---
    const allViews = document.querySelectorAll('.view');
    const initialView = document.getElementById('initial-view');
    const robertaResultsView = document.getElementById('roberta-results-view');
    const llmResultsView = document.getElementById('llm-results-view');
    const robertaDetailsView = document.getElementById('roberta-details-view');
    const errorEl = document.getElementById('error');
    
    // Buttons
    const analyzeRobertaBtn = document.getElementById('analyze-roberta-btn');
    const analyzeLlmBtn = document.getElementById('analyze-llm-btn');
    const robertaAnalyzeAnother = document.getElementById('roberta-analyze-another');
    const robertaLearnMore = document.getElementById('roberta-learn-more');
    const robertaFeedbackSubmit = document.getElementById('roberta-feedback-submit');
    const llmAnalyzeAnother = document.getElementById('llm-analyze-another');
    const llmFeedbackSubmit = document.getElementById('llm-feedback-submit');
    
    // Roberta Feedback
    const robertaThumbUp = document.getElementById('roberta-thumb-up');
    const robertaThumbDown = document.getElementById('roberta-thumb-down');
    const robertaEmotionSelect = document.getElementById('roberta-emotion-select');
    const robertaFeedbackComment = document.getElementById('roberta-feedback-comment');
    
    // LLM Feedback
    const llmThumbUp = document.getElementById('llm-thumb-up');
    const llmThumbDown = document.getElementById('llm-thumb-down');
    const llmFeedbackComment = document.getElementById('llm-feedback-comment');

    // --- Event Listeners ---
    analyzeRobertaBtn.addEventListener('click', () => handleAnalysisRequest('roberta'));
    analyzeLlmBtn.addEventListener('click', () => handleAnalysisRequest('llm'));

    robertaAnalyzeAnother.addEventListener('click', showInitialView);
    llmAnalyzeAnother.addEventListener('click', showInitialView);
    robertaLearnMore.addEventListener('click', () => showView('roberta-details-view'));

    robertaThumbUp.addEventListener('click', () => setThumbRating('roberta', 'up'));
    robertaThumbDown.addEventListener('click', () => setThumbRating('roberta', 'down'));
    robertaFeedbackSubmit.addEventListener('click', handleFeedbackSubmit);
    
    llmThumbUp.addEventListener('click', () => setThumbRating('llm', 'up'));
    llmThumbDown.addEventListener('click', () => setThumbRating('llm', 'down'));
    llmFeedbackSubmit.addEventListener('click', handleFeedbackSubmit);

    // --- View Switching ---
    function showView(viewId) {
        allViews.forEach(v => v.style.display = 'none');
        document.getElementById(viewId).style.display = 'block';
    }
    function showInitialView() { showView('initial-view'); hideError(); }

    // --- Core Logic ---
    async function handleAnalysisRequest(modelType) {
        currentModel = modelType;
        const btn = modelType === 'roberta' ? analyzeRobertaBtn : analyzeLlmBtn;
        btn.disabled = true;
        btn.textContent = 'Importing Transcript...';
        hideError();

        try {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            if (!tab) throw new Error("Could not find active tab.");
            const response = await chrome.tabs.sendMessage(tab.id, { type: 'SCRAPE_TRANSCRIPT' });

            if (response && response.success) {
                originalTranscript = response.transcript;
                await sendTranscriptToBackend(response.transcript, modelType);
            } else {
                throw new Error(response.error || "Failed to get transcript.");
            }
        } catch (error) {
            showError(error.message);
        } finally {
            btn.disabled = false;
            btn.textContent = modelType === 'roberta' ? 'Analyze with GoEmotions' : 'Analyze with Peacefulness LLM';
        }
    }

    async function sendTranscriptToBackend(transcript, modelType) {
        const endpoint = modelType === 'roberta' ? '/run_roberta_model' : '/analyze_with_llm';
        const btn = modelType === 'roberta' ? analyzeRobertaBtn : analyzeLlmBtn;
        btn.textContent = 'Analyzing...';

        try {
            const response = await fetch(`http://localhost:8080${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ transcript })
            });
            if (!response.ok) throw new Error((await response.json()).detail || 'Backend error.');
            lastAnalysisData = await response.json();
            
            if (modelType === 'roberta') {
                updateRobertaUI(lastAnalysisData);
                showView('roberta-results-view');
            } else {
                updateLlmUI(lastAnalysisData);
                showView('llm-results-view');
            }
        } catch (error) {
            showError(error.message);
        }
    }

    async function handleFeedbackSubmit() {
        const rating = currentModel === 'roberta' ? robertaThumbRating : llmThumbRating;
        const comment = currentModel === 'roberta' ? robertaFeedbackComment.value.trim() : llmFeedbackComment.value.trim();
        const user_emotion = currentModel === 'roberta' ? robertaEmotionSelect.value : 'N/A';
        const btn = currentModel === 'roberta' ? robertaFeedbackSubmit : llmFeedbackSubmit;

        const payload = { model_type: currentModel, original_transcript: originalTranscript, model_analysis: lastAnalysisData, user_feedback: { rating, comment, user_emotion } };

        btn.disabled = true;
        btn.textContent = 'Submitting...';
        try {
            const response = await fetch('http://localhost:8080/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (!response.ok) throw new Error('Failed to submit feedback.');
            btn.textContent = 'Thank You!';
        } catch (err) {
            btn.textContent = 'Submission Failed';
            setTimeout(() => { btn.disabled = false; btn.textContent = 'Submit Feedback'; }, 2000);
        }
    }

    // --- UI Update Functions ---
    function setThumbRating(model, rating) {
        if (model === 'roberta') {
            robertaThumbRating = rating;
            robertaThumbUp.classList.toggle('selected', rating === 'up');
            robertaThumbDown.classList.toggle('selected', rating === 'down');
        } else {
            llmThumbRating = rating;
            llmThumbUp.classList.toggle('selected', rating === 'up');
            llmThumbDown.classList.toggle('selected', rating === 'down');
        }
    }
    
    function updateRobertaUI(data) {
        const { respect, contempt } = data.aggregate_scores;
        // The new scale is more sensitive, from -20 to +20.
        const SCALE_MIN = -20, SCALE_MAX = 20;
        let combinedScore = Math.max(SCALE_MIN, Math.min(SCALE_MAX, respect - contempt));
        
        const angle = 180 - ((combinedScore - SCALE_MIN) / (SCALE_MAX - SCALE_MIN)) * 180;
        const r = 70, cx = 110, cy = 100;
        const rad = (angle * Math.PI) / 180;
        const x2 = cx + r * Math.cos(rad);
        const y2 = cy - r * Math.sin(rad);
        document.getElementById('gaugeNeedle').setAttribute('x2', x2);
        document.getElementById('gaugeNeedle').setAttribute('y2', y2);
        document.getElementById('respectValue').innerHTML = `<b>${respect.toFixed(1)}%</b>`;
        document.getElementById('contemptValue').innerHTML = `<b>${contempt.toFixed(1)}%</b>`;
        
        populateEmotionDropdown(data, robertaEmotionSelect);
        renderRobertaDetails(data);
    }

    function updateLlmUI(data) {
        const listEl = document.getElementById('llm-dimension-list');
        listEl.innerHTML = '';
        const labels = {
            nuance: ['Oversimplification', 'Nuance'],
            creativity_vs_order: ['Order', 'Creativity'],
            safety_vs_threat: ['Threat', 'Safety'],
            compassion_vs_contempt: ['Contempt', 'Compassion'],
            reporting_vs_opinion: ['Opinion', 'Reporting']
        };
        for (const key in data) {
            const item = data[key];
            const score = item.score;
            const percentage = (Math.abs(score) / 5) * 50;
            const color = score >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';
            const leftPos = score >= 0 ? '50%' : `${50 - percentage}%`;

            const element = document.createElement('div');
            element.className = 'dimension-item';
            element.innerHTML = `
                <div class="dimension-header">
                    <span class="dimension-label">${key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                    <span class="dimension-score" style="background-color: ${color};">${score > 0 ? '+' : ''}${score}</span>
                </div>
                <div class="score-bar-container">
                    <div class="score-bar-center-line"></div>
                    <div class="score-bar" style="width: ${percentage}%; left: ${leftPos}; background-color: ${color};"></div>
                </div>
                <div class="bar-labels"><span>${labels[key][0]}</span><span>${labels[key][1]}</span></div>
                <div class="dimension-rationale">${item.rationale}</div>
            `;
            listEl.appendChild(element);
        }
    }
    
    function populateEmotionDropdown(data, selectElement) {
        selectElement.innerHTML = '<option value="">-- Select an emotion --</option>';
        let allEmotions = [];
        if (data.dominant_emotion) {
            allEmotions.push(data.dominant_emotion.charAt(0).toUpperCase() + data.dominant_emotion.slice(1));
        }
        for (const category in data.emotions) {
            allEmotions.push(...data.emotions[category].map(e => e.label));
        }
        const uniqueEmotions = [...new Set(allEmotions)];
        uniqueEmotions.sort().forEach(emotion => {
            const option = document.createElement('option');
            option.value = emotion.toLowerCase();
            option.textContent = emotion;
            selectElement.appendChild(option);
        });
    }

    function renderRobertaDetails(data) {
        const colors = { Respect: '#4caf50', Contempt: '#ff4d4f', Positive: '#2196f3', Negative: '#9c27b0', Neutral: '#ffd700' };
        let detailsHTML = `<h2>Detailed Scores</h2>`;
        
        function renderCategory(title, emotions, aggregateScore) {
            if (!emotions || emotions.length === 0) return '';
            
            let categoryHTML = `
                <div class="modal-cat-header" style="color:${colors[title]}; display: flex; justify-content: space-between; align-items: center;">
                    <span>${title}</span>
                    <span style="font-weight: bold; font-size: 0.9em;">Total: ${aggregateScore.toFixed(1)}%</span>
                </div>
                <div class="emotions-list">`;
            
            emotions.forEach(e => {
                categoryHTML += `<div class="emotion-item"><span>${e.label}</span><span style="color:${colors[title]}; font-weight:bold;">${e.score.toFixed(1)}%</span></div>`;
            });
            
            return categoryHTML + `</div>`;
        }

        detailsHTML += `<div class="emotion-item"><span>Dominant Emotion</span><span style="font-weight:bold;">${data.dominant_emotion.charAt(0).toUpperCase() + data.dominant_emotion.slice(1)}</span></div>`;
        detailsHTML += `<div class="emotion-item"><span>Neutral Score</span><span style="font-weight:bold;">${data.neutral_score.toFixed(1)}%</span></div>`;
        
        detailsHTML += renderCategory('Respect', data.emotions.respect, data.aggregate_scores.respect);
        detailsHTML += renderCategory('Contempt', data.emotions.contempt, data.aggregate_scores.contempt);
        detailsHTML += renderCategory('Positive', data.emotions.positive, data.aggregate_scores.positive);
        detailsHTML += renderCategory('Negative', data.emotions.negative, data.aggregate_scores.negative);
        
        detailsHTML += `<div class="button-group" style="margin-top: 15px;"><button id="detailsBackBtn">Back to Results</button></div>`;
        
        robertaDetailsView.innerHTML = detailsHTML;
        document.getElementById('detailsBackBtn').addEventListener('click', () => showView('roberta-results-view'));
    }

    function showError(msg) { errorEl.style.display = 'block'; errorEl.textContent = msg; }
    function hideError() { errorEl.style.display = 'none'; errorEl.textContent = ''; }
});
