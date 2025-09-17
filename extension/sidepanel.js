// This script is now just the "display" for the analysis.
document.addEventListener('DOMContentLoaded', async function() {
    // --- All Element References (You need all of these from your HTML) ---
    const inputView = document.getElementById('input-view');
    const resultsView = document.getElementById('results-view');
    const detailsView = document.getElementById('details-view');
    const importBtn = document.getElementById('importBtn'); 
    const backBtn = document.getElementById('backBtn');
    const learnMoreBtn = document.getElementById('learnMoreBtn');
    const submitFeedbackBtn = document.getElementById('submitFeedbackBtn');
    const thumbUpBtn = document.getElementById('thumbUp');
    const thumbDownBtn = document.getElementById('thumbDown');
    const errorEl = document.getElementById('error');
    const emotionSelect = document.getElementById('emotionSelect');
    const feedbackComment = document.getElementById('feedbackComment');
    const gaugeNeedle = document.getElementById('gaugeNeedle');
    const respectValue = document.getElementById('respectValue');
    const contemptValue = document.getElementById('contemptValue');

    const SCALE_MIN = -0.2;
    const SCALE_MAX = 0.2;

    // --- State Variables (Still needed for feedback) ---
    let lastAnalysisData = null;
    let originalTranscript = ''; // This might be unavailable in the new architecture, handle gracefully
    let thumbRating = null;
    
    // All UI helper functions (showInputView, updateGauge, etc.) are needed here.
    function showInputView() { resultsView.style.display = 'none'; detailsView.style.display = 'none'; inputView.style.display = 'block'; hideError(); }
    function showResultsView() { inputView.style.display = 'none'; detailsView.style.display = 'none'; resultsView.style.display = 'block'; resetFeedbackForm(); }
    function showDetailsView() { if (!lastAnalysisData) return; renderDetails(lastAnalysisData); resultsView.style.display = 'none'; detailsView.style.display = 'block'; }
    function setThumbRating(rating) { thumbRating = rating; thumbUpBtn.classList.toggle('selected', rating === 'up'); thumbDownBtn.classList.toggle('selected', rating === 'down'); }
    function resetFeedbackForm() { setThumbRating(null); emotionSelect.value = ""; feedbackComment.value = ""; submitFeedbackBtn.disabled = false; submitFeedbackBtn.textContent = 'Submit Feedback'; }
    function showError(msg) { errorEl.style.display = 'block'; errorEl.textContent = msg; }
    function hideError() { errorEl.style.display = 'none'; errorEl.textContent = ''; }
    function updateGauge(totalRespect, totalContempt) { const combinedScore = totalRespect - totalContempt; const angle = 180 - ((combinedScore - SCALE_MIN) / (SCALE_MAX - SCALE_MIN)) * 180; const r = 70, cx = 110, cy = 100; const rad = (angle * Math.PI) / 180; const x2 = cx + r * Math.cos(rad); const y2 = cy - r * Math.sin(rad); gaugeNeedle.setAttribute('x2', x2); gaugeNeedle.setAttribute('y2', y2); const respectPercent = totalRespect * 100; const contemptPercent = totalContempt * 100; respectValue.innerHTML = `<b>${respectPercent.toFixed(1)}%</b>`; contemptValue.innerHTML = `<b>${contemptPercent.toFixed(1)}%</b>`; }
    function renderDetails(data) { const colors = { Respect: '#4caf50', Contempt: '#ff4d4f', Positive: '#2196f3', Negative: '#9c27b0', Neutral: '#ffd700' }; let detailsHTML = `<h2>Detailed Analysis</h2>`; function renderCategory(title, emotions, specificEmotionsToSum = null) { if (!emotions || !Array.isArray(emotions) || emotions.length === 0) return ''; const totalScore = specificEmotionsToSum ? emotions.reduce((sum, emotion) => specificEmotionsToSum.includes(emotion.label.toLowerCase()) ? sum + emotion.score : sum, 0) : emotions.reduce((sum, emotion) => sum + emotion.score, 0); const totalPercent = (totalScore * 100).toFixed(1); let categoryHTML = `<div class="modal-cat-header" style="color:${colors[title]}; display: flex; justify-content: space-between;"><span>${title}</span><span style="font-weight: bold;">Total: ${totalPercent}%</span></div><div class="emotions-list">`; emotions.forEach(e => { const scorePercent = e.score * 100; categoryHTML += `<div class="emotion-item"><span>${e.label}</span><span style="color:${colors[title]}; font-weight:bold;">${scorePercent.toFixed(1)}%</span></div>`; }); return categoryHTML + `</div>`; } const respectEmotionsForTotal = ['admiration', 'approval', 'caring']; const contemptEmotionsForTotal = ['disapproval', 'disgust', 'annoyance']; detailsHTML += renderCategory('Respect', data.emotions.respect, respectEmotionsForTotal); detailsHTML += renderCategory('Contempt', data.emotions.contempt, contemptEmotionsForTotal); detailsHTML += renderCategory('Positive', data.emotions.positive); detailsHTML += renderCategory('Negative', data.emotions.negative); detailsHTML += renderCategory('Neutral', data.emotions.neutral_breakdown); detailsHTML += `<div class="button-group" style="margin-top: 15px;"><button id="detailsBackBtn">Back to Results</button></div>`; detailsView.innerHTML = detailsHTML; document.getElementById('detailsBackBtn').addEventListener('click', showResultsView); }
    function populateEmotionDropdown(data) { emotionSelect.innerHTML = '<option value="">-- Select an emotion --</option>'; let allEmotions = []; if (data.dominant_emotion) { allEmotions.push(data.dominant_emotion.charAt(0).toUpperCase() + data.dominant_emotion.slice(1)); } for (const category in data.emotions) { if(Array.isArray(data.emotions[category])) { allEmotions.push(...data.emotions[category].map(e => e.label)); } } const uniqueEmotions = [...new Set(allEmotions)]; uniqueEmotions.sort().forEach(emotion => { const option = document.createElement('option'); option.value = emotion.toLowerCase(); option.textContent = emotion; emotionSelect.appendChild(option); }); }
    async function handleFeedbackSubmit() { /* This will need to be adapted if transcript isn't available */ }

    // Event listeners for the static buttons
    backBtn.addEventListener('click', showInputView);
    learnMoreBtn.addEventListener('click', showDetailsView);
    submitFeedbackBtn.addEventListener('click', handleFeedbackSubmit);
    thumbUpBtn.addEventListener('click', () => setThumbRating('up'));
    thumbDownBtn.addEventListener('click', () => setThumbRating('down'));

    // Main function to display the current state from storage
    async function displayCurrentAnalysis() {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!tab) return;

        const result = await chrome.storage.local.get([`${tab.id}`]);
        const tabData = result[tab.id];

        if (!tabData) {
            showInputView();
            importBtn.textContent = 'No analysis for this page.';
            importBtn.disabled = true;
        } else if (tabData.status === 'loading') {
            showInputView();
            importBtn.textContent = 'Analysis in progress...';
            importBtn.disabled = true;
        } else if (tabData.status === 'error') {
            showInputView();
            importBtn.style.display = 'none'; // Hide button on error
            showError(tabData.error);
        } else if (tabData.status === 'success') {
            lastAnalysisData = tabData.data;
            populateEmotionDropdown(lastAnalysisData);
            
            const allEmotionScores = {};
            if (lastAnalysisData.emotions) {
                for (const category in lastAnalysisData.emotions) {
                    if (Array.isArray(lastAnalysisData.emotions[category])) {
                        lastAnalysisData.emotions[category].forEach(e => { allEmotionScores[e.label.toLowerCase()] = e.score; });
                    }
                }
            }
            const respectEmotions = ['admiration', 'approval', 'caring'];
            const contemptEmotions = ['disapproval', 'disgust', 'annoyance'];
            const specificRespectSum = respectEmotions.reduce((sum, emotion) => sum + (allEmotionScores[emotion] || 0), 0);
            const specificContemptSum = contemptEmotions.reduce((sum, emotion) => sum + (allEmotionScores[emotion] || 0), 0);
            updateGauge(specificRespectSum, specificContemptSum);
            
            showResultsView();
        }
    }

    // Listen for real-time updates from the background script
    chrome.storage.onChanged.addListener((changes, area) => {
        if (area === 'local') {
            displayCurrentAnalysis();
        }
    });

    // Initial display when panel is opened
    displayCurrentAnalysis();
});