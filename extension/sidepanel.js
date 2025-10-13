document.addEventListener('DOMContentLoaded', function() {
    // --- State Variables ---
    let lastAnalysisData = null;
    let originalTranscript = '';
    let llmThumbRating = null;

    // --- Element References ---
    const allViews = document.querySelectorAll('.view');
    const initialView = document.getElementById('initial-view');
    const resultsView = document.getElementById('results-view');
    const errorEl = document.getElementById('error');
    
    // Buttons
    const analyzeBtn = document.getElementById('analyze-btn');
    const analyzeAnotherBtn = document.getElementById('analyze-another');
    const llmFeedbackSubmit = document.getElementById('llm-feedback-submit');
    
    // LLM Feedback
    const llmThumbUp = document.getElementById('llm-thumb-up');
    const llmThumbDown = document.getElementById('llm-thumb-down');
    const llmFeedbackComment = document.getElementById('llm-feedback-comment');

    // --- Event Listeners ---
    analyzeBtn.addEventListener('click', handleAnalysisRequest);
    analyzeAnotherBtn.addEventListener('click', showInitialView);
    
    llmThumbUp.addEventListener('click', () => setThumbRating('up'));
    llmThumbDown.addEventListener('click', () => setThumbRating('down'));
    llmFeedbackSubmit.addEventListener('click', handleFeedbackSubmit);

    // --- View Switching ---
    function showView(viewId) {
        allViews.forEach(v => v.style.display = 'none');
        document.getElementById(viewId).style.display = 'block';
    }
    function showInitialView() { 
        showView('initial-view'); 
        hideError(); 
        // Reset feedback state
        llmThumbRating = null;
        llmThumbUp.classList.remove('selected');
        llmThumbDown.classList.remove('selected');
        llmFeedbackComment.value = '';
        llmFeedbackSubmit.disabled = false;
        llmFeedbackSubmit.textContent = 'Submit Feedback';
    }

    // --- Core Logic ---
    async function handleAnalysisRequest() {
        analyzeBtn.disabled = true;
        analyzeBtn.textContent = 'Importing Transcript...';
        hideError();

        try {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            if (!tab) throw new Error("Could not find active tab.");
            const response = await chrome.tabs.sendMessage(tab.id, { type: 'SCRAPE_TRANSCRIPT' });

            if (response && response.success) {
                originalTranscript = response.transcript;
                await sendTranscriptToBackend(response.transcript);
            } else {
                throw new Error(response.error || "Failed to get transcript.");
            }
        } catch (error) {
            showError(error.message);
        } finally {
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = 'Run Analysis';
        }
    }

    async function sendTranscriptToBackend(transcript) {
        analyzeBtn.textContent = 'Analyzing...';
        try {
            // The new backend default is 'v3_final', so no specific payload is needed
            const response = await fetch(`http://localhost:8080/analyze_with_llm`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ transcript })
            });
            if (!response.ok) throw new Error((await response.json()).detail || 'Backend error.');
            lastAnalysisData = await response.json();
            
            updateResultsUI(lastAnalysisData);
            showView('results-view');

        } catch (error) {
            showError(error.message);
        }
    }

    async function handleFeedbackSubmit() {
        const payload = { 
            model_type: 'llm_v3_final', 
            original_transcript: originalTranscript, 
            model_analysis: lastAnalysisData, 
            user_feedback: { rating: llmThumbRating, comment: llmFeedbackComment.value.trim() } 
        };

        llmFeedbackSubmit.disabled = true;
        llmFeedbackSubmit.textContent = 'Submitting...';
        try {
            const response = await fetch('http://localhost:8080/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (!response.ok) throw new Error('Failed to submit feedback.');
            llmFeedbackSubmit.textContent = 'Thank You!';
        } catch (err) {
            llmFeedbackSubmit.textContent = 'Submission Failed';
            setTimeout(() => { 
                llmFeedbackSubmit.disabled = false; 
                llmFeedbackSubmit.textContent = 'Submit Feedback'; 
            }, 2000);
        }
    }

    // --- UI Update Functions ---
    function setThumbRating(rating) {
        llmThumbRating = rating;
        llmThumbUp.classList.toggle('selected', rating === 'up');
        llmThumbDown.classList.toggle('selected', rating === 'down');
    }
    
    function updateResultsUI(data) {
        // 1. Update the Emotion Meter (Compassion vs. Contempt)
        const compassionData = data.compassion_vs_contempt;
        if (compassionData) {
            const score = compassionData.score; // 0 to 100
            const angle = 180 - (score / 100) * 180; // Map 0-100 to 180-0 degrees
            const r = 70, cx = 110, cy = 100;
            const rad = (angle * Math.PI) / 180;
            const x2 = cx + r * Math.cos(rad);
            const y2 = cy - r * Math.sin(rad);
            document.getElementById('llm-gaugeNeedle').setAttribute('x2', x2);
            document.getElementById('llm-gaugeNeedle').setAttribute('y2', y2);
            document.getElementById('gauge-score').textContent = score;
            document.getElementById('llm-compassion-rationale').textContent = compassionData.rationale;
        }

        // 2. Display the Top 3 Emotions from RoBERTa
        const emotionsContainer = document.getElementById('top-emotions-container');
        emotionsContainer.innerHTML = '<h3>Rationale supported by:</h3>';
        if (data.top_emotions && data.top_emotions.length > 0) {
            data.top_emotions.forEach(emo => {
                const item = document.createElement('div');
                item.className = 'emotion-item';
                item.innerHTML = `
                    <span class="emotion-name">${emo.emotion}</span>
                    <span class="emotion-score">${(emo.score * 100).toFixed(1)}%</span>
                `;
                emotionsContainer.appendChild(item);
            });
        }

        // 3. Display the other dimensions with score bars
        const listEl = document.getElementById('llm-dimension-list');
        listEl.innerHTML = '';
        const labels = {
            creativity_vs_order: ['Order', 'Creativity'],
            safety_vs_threat: ['Threat', 'Safety'],
            reporting_vs_opinion: ['Opinion', 'Reporting']
        };

        for (const key in data) {
            if (key === 'compassion_vs_contempt' || key === 'top_emotions') continue;

            const item = data[key];
            const score = item.score;
            const percentage = (Math.abs(score) / 5) * 50;
            const color = score >= 0 ? '#4caf50' : '#ff4d4f'; // Green/Red
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

    function showError(msg) { errorEl.style.display = 'block'; errorEl.textContent = msg; }
    function hideError() { errorEl.style.display = 'none'; errorEl.textContent = ''; }
});

