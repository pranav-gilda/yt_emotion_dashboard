document.addEventListener('DOMContentLoaded', function() {
    // --- Element References ---
    const inputView = document.getElementById('input-view');
    const resultsView = document.getElementById('results-view');
    const detailsView = document.getElementById('details-view');
    
    const analyzeBtn = document.getElementById('analyzeBtn');
    const backBtn = document.getElementById('backBtn');
    const learnMoreBtn = document.getElementById('learnMoreBtn');
    const submitFeedbackBtn = document.getElementById('submitFeedbackBtn');
    const thumbUpBtn = document.getElementById('thumbUp');
    const thumbDownBtn = document.getElementById('thumbDown');
    
    const transcriptInput = document.getElementById('transcriptInput');
    const errorEl = document.getElementById('error');
    const emotionSelect = document.getElementById('emotionSelect');
    const feedbackComment = document.getElementById('feedbackComment');
    
    const gaugeNeedle = document.getElementById('gaugeNeedle');
    const respectValue = document.getElementById('respectValue');
    const contemptValue = document.getElementById('contemptValue');

    const SCALE_MIN = -0.2;
    const SCALE_MAX = 0.2;

    // --- State Variables ---
    let lastAnalysisData = null;
    let originalTranscript = '';
    let thumbRating = null;

    // --- Event Listeners ---
    analyzeBtn.addEventListener('click', handleAnalysis);
    backBtn.addEventListener('click', showInputView);
    learnMoreBtn.addEventListener('click', showDetailsView);
    submitFeedbackBtn.addEventListener('click', handleFeedbackSubmit);
    
    thumbUpBtn.addEventListener('click', () => setThumbRating('up'));
    thumbDownBtn.addEventListener('click', () => setThumbRating('down'));

    // --- View Switching Logic ---
    function showInputView() {
        resultsView.style.display = 'none';
        detailsView.style.display = 'none';
        inputView.style.display = 'block';
        transcriptInput.value = '';
        hideError();
    }

    function showResultsView() {
        inputView.style.display = 'none';
        detailsView.style.display = 'none';
        resultsView.style.display = 'block';
        resetFeedbackForm();
    }

    function showDetailsView() {
        if (!lastAnalysisData) return;
        renderDetails(lastAnalysisData);
        resultsView.style.display = 'none';
        detailsView.style.display = 'block';
    }

    // --- Core Logic ---
    async function handleAnalysis() {
        const transcript = transcriptInput.value.trim().replace(/\n/g, ' ');
        if (!transcript) {
            showError('Please paste a transcript first.');
            return;
        }

        originalTranscript = transcript;
        analyzeBtn.disabled = true;
        analyzeBtn.textContent = 'Analyzing...';
        hideError();

        try {
            const url = `http://18.222.120.158:8080/run_models`;
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ transcript: transcript })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Backend returned an error.');
            }

            const data = await response.json();
            lastAnalysisData = data;
            
            populateEmotionDropdown(data);
            updateGauge(data.aggregate_scores.respect, data.aggregate_scores.contempt);
            showResultsView();

        } catch (err) {
            showError(err.message);
        } finally {
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = 'Analyze';
        }
    }

    async function handleFeedbackSubmit() {
        if (!lastAnalysisData) {
            alert('No analysis data to submit feedback for.');
            return;
        }

        const feedbackData = {
            rating: thumbRating,
            user_emotion: emotionSelect.value,
            comment: feedbackComment.value.trim()
        };

        const payload = {
            original_transcript: originalTranscript,
            model_analysis: lastAnalysisData,
            user_feedback: feedbackData
        };

        submitFeedbackBtn.disabled = true;
        submitFeedbackBtn.textContent = 'Submitting...';

        try {
            const response = await fetch('http://18.222.120.158:8080/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) throw new Error('Failed to submit feedback.');

            submitFeedbackBtn.textContent = 'Thank You!';

        } catch (err) {
            submitFeedbackBtn.textContent = 'Submission Failed';
            setTimeout(() => {
                submitFeedbackBtn.disabled = false;
                submitFeedbackBtn.textContent = 'Submit Feedback';
            }, 2000);
        }
    }

    // --- UI Update & Helper Functions ---
    function setThumbRating(rating) {
        thumbRating = rating;
        thumbUpBtn.style.backgroundColor = rating === 'up' ? '#007bff' : 'transparent';
        thumbDownBtn.style.backgroundColor = rating === 'down' ? '#007bff' : 'transparent';
    }

    function resetFeedbackForm() {
        setThumbRating(null);
        emotionSelect.value = "";
        feedbackComment.value = "";
        submitFeedbackBtn.disabled = false;
        submitFeedbackBtn.textContent = 'Submit Feedback';
    }

    function populateEmotionDropdown(data) {
        emotionSelect.innerHTML = '<option value="">-- Select an emotion --</option>';
        
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
            emotionSelect.appendChild(option);
        });
    }

    function updateGauge(avgRespect, avgContempt) {
        const combinedScore = avgRespect - avgContempt;
        const angle = 180 - ((combinedScore - SCALE_MIN) / (SCALE_MAX - SCALE_MIN)) * 180;
        const r = 70, cx = 110, cy = 100;
        const rad = (angle * Math.PI) / 180;
        const x2 = cx + r * Math.cos(rad);
        const y2 = cy - r * Math.sin(rad);
        
        gaugeNeedle.setAttribute('x2', x2);
        gaugeNeedle.setAttribute('y2', y2);

        respectValue.innerHTML = `<b>${avgRespect.toFixed(3)}</b>`;
        contemptValue.innerHTML = `<b>${avgContempt.toFixed(3)}</b>`;
    }

    function renderDetails(data) {
        const colors = { Respect: '#4caf50', Contempt: '#ff4d4f', Positive: '#2196f3', Negative: '#9c27b0', Neutral: '#ffd700' };
        
        let detailsHTML = `<h2>Detailed Analysis</h2>`;

        function renderCategory(title, emotions) {
            if (!emotions || emotions.length === 0) return '';
            let categoryHTML = `<div class="modal-cat-header" style="color:${colors[title]}">${title}</div><div class="emotions-list">`;
            emotions.forEach(e => {
                categoryHTML += `<div class="emotion-item"><span>${e.label}</span><span style="color:${colors[title]}; font-weight:bold;">${e.score.toFixed(3)}</span></div>`;
            });
            return categoryHTML + `</div>`;
        }

        detailsHTML += renderCategory('Respect', data.emotions.respect);
        detailsHTML += renderCategory('Contempt', data.emotions.contempt);
        detailsHTML += renderCategory('Positive', data.emotions.positive);
        detailsHTML += renderCategory('Negative', data.emotions.negative);
        detailsHTML += renderCategory('Neutral', data.emotions.neutral_breakdown);
        
        detailsHTML += `<div class="button-group" style="margin-top: 15px;"><button id="detailsBackBtn">Back to Results</button></div>`;
        
        detailsView.innerHTML = detailsHTML;
        document.getElementById('detailsBackBtn').addEventListener('click', showResultsView);
    }

    function showError(msg) {
        errorEl.style.display = 'block';
        errorEl.textContent = msg;
    }

    function hideError() {
        errorEl.style.display = 'none';
        errorEl.textContent = '';
    }
});
