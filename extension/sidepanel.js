document.addEventListener('DOMContentLoaded', function() {
    // --- Element References ---
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

    // --- State Variables ---
    let lastAnalysisData = null;
    let originalTranscript = '';
    let thumbRating = null;

    // --- Event Listeners ---
    importBtn.addEventListener('click', handleImportClick); // Keep the button click for manual runs
    backBtn.addEventListener('click', showInputView);
    learnMoreBtn.addEventListener('click', showDetailsView);
    submitFeedbackBtn.addEventListener('click', handleFeedbackSubmit);
    thumbUpBtn.addEventListener('click', () => setThumbRating('up'));
    thumbDownBtn.addEventListener('click', () => setThumbRating('down'));
    
    async function handleImportClick() {
        // --- LATENCY --- Start the master timer at the moment of the click.
        const t0_startTime = performance.now();

        importBtn.disabled = true;
        importBtn.textContent = 'Importing...';
        hideError();

        try {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            if (!tab) { throw new Error("Could not find an active tab."); }
            const response = await chrome.tabs.sendMessage(tab.id, { type: 'SCRAPE_TRANSCRIPT' });

            const t1_transcriptReceived = performance.now();

            if (response && response.success) {
                await sendTranscriptToBackend(response.transcript, t0_startTime, t1_transcriptReceived);
            } else {
                throw new Error(response.error || "Failed to get transcript. This video may not have one available.");
            }
        } catch (error) {
            console.error("Error communicating with the content script:", error);
            showError(error.message);
            importBtn.disabled = false;
            importBtn.textContent = 'Import Transcript & Analyze';
        }
    }

    async function sendTranscriptToBackend(transcript, t0_startTime, t1_transcriptReceived) {
        importBtn.textContent = 'Analyzing...';
        originalTranscript = transcript;

        try {
            const url = `http://18.222.120.158:8080/run_models`;
            const t2_apiCallStart = performance.now();
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
            const t3_apiResponseReceived = performance.now();
            lastAnalysisData = data;
            populateEmotionDropdown(data);
            
            const allEmotionScores = {};
            if (data.emotions) {
                for (const category in data.emotions) {
                    if (Array.isArray(data.emotions[category])) {
                        data.emotions[category].forEach(e => { allEmotionScores[e.label.toLowerCase()] = e.score; });
                    }
                }
            }
            const respectEmotions = ['admiration', 'approval', 'caring'];
            const contemptEmotions = ['disapproval', 'disgust', 'annoyance'];
            const specificRespectSum = respectEmotions.reduce((sum, emotion) => sum + (allEmotionScores[emotion] || 0), 0);
            const specificContemptSum = contemptEmotions.reduce((sum, emotion) => sum + (allEmotionScores[emotion] || 0), 0);
            updateGauge(specificRespectSum, specificContemptSum);
            
            showResultsView();
            const t4_uiRendered = performance.now();
            logPerformanceMetrics({ t0_startTime, t1_transcriptReceived, t2_apiCallStart, t3_apiResponseReceived, t4_uiRendered });

        } catch (err) {
            showError(err.message);
        } finally {
            importBtn.disabled = false;
            importBtn.textContent = 'Import Transcript & Analyze';
        }
    }

    function logPerformanceMetrics(times) {
        const scrapingTime = times.t1_transcriptReceived - times.t0_startTime;
        const apiTime = times.t3_apiResponseReceived - times.t2_apiCallStart;
        const renderTime = times.t4_uiRendered - times.t3_apiResponseReceived;
        const totalTime = times.t4_uiRendered - times.t0_startTime;

        console.group("🚀 Performance Metrics");
        console.log(`Transcript Scraping: %c${scrapingTime.toFixed(1)} ms`, "color: blue;");
        console.log(`API & Model Latency: %c${apiTime.toFixed(1)} ms`, "color: red; font-weight: bold;");
        console.log(`UI Render Time: %c${renderTime.toFixed(1)} ms`, "color: green;");
        console.log("-------------------------");
        console.log(`Total Time: %c${totalTime.toFixed(1)} ms`, "font-weight: bold;");
        console.groupEnd();
    }

    // --- All other functions are unchanged ---
    function showInputView() { resultsView.style.display = 'none'; detailsView.style.display = 'none'; inputView.style.display = 'block'; hideError(); }
    function showResultsView() { inputView.style.display = 'none'; detailsView.style.display = 'none'; resultsView.style.display = 'block'; resetFeedbackForm(); }
    function showDetailsView() { if (!lastAnalysisData) return; renderDetails(lastAnalysisData); resultsView.style.display = 'none'; detailsView.style.display = 'block'; }
    async function handleFeedbackSubmit() { if (!lastAnalysisData) return; const feedbackData = { rating: thumbRating, user_emotion: emotionSelect.value, comment: feedbackComment.value.trim() }; const payload = { original_transcript: originalTranscript, model_analysis: lastAnalysisData, user_feedback: feedbackData }; submitFeedbackBtn.disabled = true; submitFeedbackBtn.textContent = 'Submitting...'; try { const response = await fetch('http://18.222.120.158:8080/feedback', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }); if (!response.ok) throw new Error('Failed to submit feedback.'); submitFeedbackBtn.textContent = 'Thank You!'; } catch (err) { submitFeedbackBtn.textContent = 'Submission Failed'; setTimeout(() => { submitFeedbackBtn.disabled = false; submitFeedbackBtn.textContent = 'Submit Feedback'; }, 2000); } }
    function setThumbRating(rating) { thumbRating = rating; thumbUpBtn.classList.toggle('selected', rating === 'up'); thumbDownBtn.classList.toggle('selected', rating === 'down'); }
    function resetFeedbackForm() { setThumbRating(null); emotionSelect.value = ""; feedbackComment.value = ""; submitFeedbackBtn.disabled = false; submitFeedbackBtn.textContent = 'Submit Feedback'; }
    function populateEmotionDropdown(data) { emotionSelect.innerHTML = '<option value="">-- Select an emotion --</option>'; let allEmotions = []; if (data.dominant_emotion) { allEmotions.push(data.dominant_emotion.charAt(0).toUpperCase() + data.dominant_emotion.slice(1)); } for (const category in data.emotions) { if(Array.isArray(data.emotions[category])) { allEmotions.push(...data.emotions[category].map(e => e.label)); } } const uniqueEmotions = [...new Set(allEmotions)]; uniqueEmotions.sort().forEach(emotion => { const option = document.createElement('option'); option.value = emotion.toLowerCase(); option.textContent = emotion; emotionSelect.appendChild(option); }); }
    function updateGauge(totalRespect, totalContempt) { const combinedScore = totalRespect - totalContempt; const angle = 180 - ((combinedScore - SCALE_MIN) / (SCALE_MAX - SCALE_MIN)) * 180; const r = 70, cx = 110, cy = 100; const rad = (angle * Math.PI) / 180; const x2 = cx + r * Math.cos(rad); const y2 = cy - r * Math.sin(rad); gaugeNeedle.setAttribute('x2', x2); gaugeNeedle.setAttribute('y2', y2); const respectPercent = totalRespect * 100; const contemptPercent = totalContempt * 100; respectValue.innerHTML = `<b>${respectPercent.toFixed(1)}%</b>`; contemptValue.innerHTML = `<b>${contemptPercent.toFixed(1)}%</b>`; }
    function renderDetails(data) { const colors = { Respect: '#4caf50', Contempt: '#ff4d4f', Positive: '#2196f3', Negative: '#9c27b0', Neutral: '#ffd700' }; let detailsHTML = `<h2>Detailed Analysis</h2>`; function renderCategory(title, emotions, specificEmotionsToSum = null) { if (!emotions || !Array.isArray(emotions) || emotions.length === 0) return ''; const totalScore = specificEmotionsToSum ? emotions.reduce((sum, emotion) => specificEmotionsToSum.includes(emotion.label.toLowerCase()) ? sum + emotion.score : sum, 0) : emotions.reduce((sum, emotion) => sum + emotion.score, 0); const totalPercent = (totalScore * 100).toFixed(1); let categoryHTML = `<div class="modal-cat-header" style="color:${colors[title]}; display: flex; justify-content: space-between;"><span>${title}</span><span style="font-weight: bold;">Total: ${totalPercent}%</span></div><div class="emotions-list">`; emotions.forEach(e => { const scorePercent = e.score * 100; categoryHTML += `<div class="emotion-item"><span>${e.label}</span><span style="color:${colors[title]}; font-weight:bold;">${scorePercent.toFixed(1)}%</span></div>`; }); return categoryHTML + `</div>`; } const respectEmotionsForTotal = ['admiration', 'approval', 'caring']; const contemptEmotionsForTotal = ['disapproval', 'disgust', 'annoyance']; detailsHTML += renderCategory('Respect', data.emotions.respect, respectEmotionsForTotal); detailsHTML += renderCategory('Contempt', data.emotions.contempt, contemptEmotionsForTotal); detailsHTML += renderCategory('Positive', data.emotions.positive); detailsHTML += renderCategory('Negative', data.emotions.negative); detailsHTML += renderCategory('Neutral', data.emotions.neutral_breakdown); detailsHTML += `<div class="button-group" style="margin-top: 15px;"><button id="detailsBackBtn">Back to Results</button></div>`; detailsView.innerHTML = detailsHTML; document.getElementById('detailsBackBtn').addEventListener('click', showResultsView); }
    function showError(msg) { errorEl.style.display = 'block'; errorEl.textContent = msg; }
    function hideError() { errorEl.style.display = 'none'; errorEl.textContent = ''; }

    // --- AUTO-RUN ---
    // Automatically trigger the analysis when the side panel is opened.
    handleImportClick();
});