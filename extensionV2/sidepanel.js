document.addEventListener('DOMContentLoaded', function() {
  console.log('Side panel JavaScript loaded successfully!');

  // --- State ---
  let lastAnalysisData = null;
  let originalTranscript = '';

  // Concurrency / race guards
  let isAnalyzing = false;
  let latestRunId = 0;
  let inFlightController = null;

  // --- Elements ---
  const allViews = document.querySelectorAll('.view');
  const initialView = document.getElementById('initial-view');
  const resultsView = document.getElementById('results-view');
  const errorEl = document.getElementById('error');

  const analyzeBtn = document.getElementById('analyze-btn') || null;
  const learnMoreBtn = document.getElementById('learn-more');
  const detailsEl = document.getElementById('details');
  const gaugeStatusEl = document.getElementById('gauge-status');
  const gaugeSpinnerEl = document.getElementById('gauge-spinner');
  const gaugeStatusResultEl = document.getElementById('gauge-status-result');
  const warningLineEl = document.getElementById('warning-line');

  // --- Feedback (optional) ---
  let llmThumbRating = null;
  const llmThumbUp = document.getElementById('llm-thumb-up') || null;
  const llmThumbDown = document.getElementById('llm-thumb-down') || null;
  const llmFeedbackComment = document.getElementById('llm-feedback-comment') || null;
  const llmFeedbackSubmit = document.getElementById('llm-feedback-submit') || null;

  // --- Events ---
  if (analyzeBtn) analyzeBtn.addEventListener('click', () => safeStartAnalysis('manual'));

  if (learnMoreBtn) {
    learnMoreBtn.addEventListener('click', () => {
      if (!detailsEl) return;
      const isHidden = detailsEl.style.display === 'none';
      detailsEl.style.display = isHidden ? 'block' : 'none';
      learnMoreBtn.textContent = isHidden ? 'Hide Details' : 'Learn More';
    });
  }

  // Feedback listeners (guarded)
  if (llmThumbUp) {
    llmThumbUp.addEventListener('click', () => setThumbRating('up'));
  }
  if (llmThumbDown) {
    llmThumbDown.addEventListener('click', () => setThumbRating('down'));
  }
  if (llmFeedbackSubmit) {
    llmFeedbackSubmit.addEventListener('click', handleFeedbackSubmit);
  }

  // --- View helpers ---
  function showView(viewId) {
    allViews.forEach(v => v.style.display = 'none');
    const el = document.getElementById(viewId);
    if (el) el.style.display = 'block';
  }

  function resetResultsDomPlaceholders() {
    const gaugeScoreEl = document.getElementById('gauge-score');
    if (gaugeScoreEl) gaugeScoreEl.textContent = '--';
    const statusResultEl = document.getElementById('gauge-status-result');
    if (statusResultEl) statusResultEl.textContent = '';
    const rationaleEl = document.getElementById('llm-compassion-rationale');
    if (rationaleEl) rationaleEl.textContent = '';
    const listEl = document.getElementById('llm-dimension-list');
    if (listEl) listEl.innerHTML = '';
    const cNeedle = document.getElementById('calc-gaugeNeedle');
    const cHub = document.getElementById('calc-gaugeHub');
    if (cNeedle) cNeedle.style.display = 'none';
    if (cHub) cHub.style.display = 'none';

    // Reset feedback UI (if present)
    llmThumbRating = null;
    if (llmThumbUp) llmThumbUp.classList.remove('selected');
    if (llmThumbDown) llmThumbDown.classList.remove('selected');
    if (llmFeedbackComment) llmFeedbackComment.value = '';
    if (llmFeedbackSubmit) {
      llmFeedbackSubmit.disabled = false;
      llmFeedbackSubmit.textContent = 'Submit Feedback';
    }
  }

  function showInitialView() {
    showView('initial-view');
    hideError();

    if (gaugeStatusEl) gaugeStatusEl.textContent = 'Calculating';
    if (gaugeSpinnerEl) gaugeSpinnerEl.style.display = 'block';
    if (gaugeStatusResultEl) gaugeStatusResultEl.textContent = '';
    if (warningLineEl) warningLineEl.style.display = 'none';
    if (detailsEl) detailsEl.style.display = 'none';
    if (learnMoreBtn) learnMoreBtn.textContent = 'Learn More';

    resetResultsDomPlaceholders();
  }

  function withTimeout(promise, ms, timeoutMessage = 'Operation timed out.') {
    let id;
    const timeout = new Promise((_, reject) => {
      id = setTimeout(() => reject(new Error(timeoutMessage)), ms);
    });
    return Promise.race([promise.finally(() => clearTimeout(id)), timeout]);
  }

  // --- Safe run orchestration ---
  async function safeStartAnalysis(reason = 'auto') {
    if (isAnalyzing) {
      console.log(`[${reason}] analysis ignored (already running)`);
      return;
    }

    // Cancel any in-flight fetches from older runs
    if (inFlightController) {
      inFlightController.abort();
      inFlightController = null;
    }

    isAnalyzing = true;
    latestRunId += 1;
    const thisRun = latestRunId;

    showInitialView();

    if (analyzeBtn) {
      analyzeBtn.disabled = true;
      analyzeBtn.textContent = 'Importing Transcript...';
    }

    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab) throw new Error("Could not find active tab.");

      const response = await withTimeout(
        chrome.tabs.sendMessage(tab.id, { type: 'SCRAPE_TRANSCRIPT' }),
        15000,
        'Transcript request timed out. Make sure the video is playing and captions exist.'
      );

      if (thisRun !== latestRunId) return; // dropped

      if (response && response.success) {
        originalTranscript = response.transcript;
        await sendTranscriptToBackend(response.transcript, thisRun);
      } else {
        throw new Error(response?.error || "Failed to get transcript.");
      }
    } catch (error) {
      showError(error.message);
    } finally {
      if (analyzeBtn) {
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = 'Run Analysis';
      }
      if (thisRun === latestRunId) isAnalyzing = false;
    }
  }

  async function sendTranscriptToBackend(transcript, thisRun) {
    if (analyzeBtn) analyzeBtn.textContent = 'Analyzing...';

    inFlightController = new AbortController();

    try {
      const response = await fetch(`http://18.222.120.158:5001/analyze_with_llm`, {
        method: 'POST',
        mode: 'cors',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ transcript }),
        signal: inFlightController.signal,
      });

      if (thisRun !== latestRunId) return; // dropped

      if (!response.ok) {
        let detail = '';
        try { detail = (await response.json()).detail; } catch {}
        throw new Error(detail || 'Backend error.');
      }

      lastAnalysisData = await response.json();

      if (thisRun !== latestRunId) return; // dropped

      await renderFreshResults(lastAnalysisData, thisRun);

      if (thisRun !== latestRunId) return; // dropped
      showView('results-view');
    } catch (error) {
      if (error.name === 'AbortError') {
        console.log(`[run ${thisRun}] fetch aborted`);
        return;
      }
      showError(error.message);
    } finally {
      inFlightController = null;
    }
  }

  function renderFreshResults(data, thisRun) {
    return new Promise(resolve => {
      requestAnimationFrame(() => {
        if (thisRun !== latestRunId) return resolve();
        updateResultsUI(data);
        resolve();
      });
    });
  }

  // --- DOM Updates ---
  function updateResultsUI(data) {
    // Gauge
    const compassionData = data.compassion_vs_contempt;
    if (compassionData) {
      const rawScore = compassionData.score; // -5..+5
      const displayScore = Math.round(((rawScore + 5) / 10) * 100);
      const angle = 225 - (displayScore / 100) * 270;

      const hubX = 130, hubY = 60, L = 80;
      const rad = (angle * Math.PI) / 180;
      const x2 = hubX + L * Math.cos(rad);
      const y2 = hubY - L * Math.sin(rad);

      const rNeedle = document.getElementById('result-gaugeNeedle');
      if (rNeedle) {
        rNeedle.setAttribute('x1', hubX);
        rNeedle.setAttribute('y1', hubY);
        rNeedle.setAttribute('x2', x2);
        rNeedle.setAttribute('y2', y2);
        rNeedle.style.display = 'block';
      }

      const rHub = document.getElementById('result-gaugeHub');
      if (rHub) rHub.style.display = 'block';

      const rationale = document.getElementById('llm-compassion-rationale');
      if (rationale) rationale.textContent = compassionData.rationale || '';

      if (gaugeStatusEl) gaugeStatusEl.textContent = '';
      if (gaugeSpinnerEl) gaugeSpinnerEl.style.display = 'none';
      if (gaugeStatusResultEl) {
        const label =
          rawScore <= -3 ? 'High Contempt' :
          rawScore <  -1 ? 'Moderate Contempt' :
          rawScore <=  1 ? 'Neutral' :
          rawScore <   3 ? 'Moderate Respect' :
                           'High Respect';
        gaugeStatusResultEl.textContent = label;
      }

      if (warningLineEl) {
        warningLineEl.style.display = rawScore < -2 ? 'block' : 'none';
        warningLineEl.textContent = rawScore < -2
          ? 'Contempt levels in this video are above your usual average.'
          : '';
      }
    }

    // Other Metrics
    const listEl = document.getElementById('llm-dimension-list');
    if (listEl) {
      const labels = {
        safety_vs_threat: ['Threat', 'Safety'],
        reporting_vs_opinion: ['Opinion', 'Fact']
      };

      ['safety_vs_threat', 'reporting_vs_opinion'].forEach(key => {
        const item = data[key];
        if (!item || typeof item.score === 'undefined') return;

        const score = item.score;                       // -5..+5
        const magnitudePct = (Math.abs(score) / 5) * 50;
        const fillLeft = score > 0 ? '50%' : `calc(50% - ${magnitudePct}%)`;
        const fillBg = score > 0
          ? 'linear-gradient(90deg, #ffffff 0%, #5E35B1 100%)'
          : 'linear-gradient(270deg, #ffffff 0%, #ff9800 100%)';
        const tickLeft = score > 0
          ? `calc(50% + ${magnitudePct}%)`
          : `calc(50% - ${magnitudePct}%)`;

        const [leftLabel, rightLabel] = labels[key];

        const el = document.createElement('div');
        el.className = 'dimension-item';
        el.innerHTML = `
          <div class="dimension-header">
            <span class="dimension-label-left">${leftLabel}</span>
            <span class="dimension-label-right">${rightLabel}</span>
          </div>
          <div class="score-bar-container">
            <div class="score-zero-tick"></div>
            <div class="score-bar" style="
              left:${fillLeft};
              width:${score === 0 ? 0 : magnitudePct}%;
              background:${fillBg};
            "></div>
            ${score === 0 ? '' : `
              <div class="score-score-tick" style="left:${tickLeft};"></div>
              <div class="score-value-label" style="left:${tickLeft};">
                ${Number(score.toFixed(1)) % 1 === 0 ? Math.round(score) : score.toFixed(1)}
              </div>
            `}
          </div>
          <div class="bar-labels"><span>-5</span><span>5</span></div>
          <div class="dimension-rationale">${item.rationale || ''}</div>
        `;
        listEl.appendChild(el);
      });
    }
  }

  // --- Feedback helpers ---
  function setThumbRating(rating) {
    llmThumbRating = rating;
    if (llmThumbUp) llmThumbUp.classList.toggle('selected', rating === 'up');
    if (llmThumbDown) llmThumbDown.classList.toggle('selected', rating === 'down');
  }

  async function handleFeedbackSubmit() {
    if (!llmFeedbackSubmit) return;
    const payload = { 
      model_type: 'llm_v3_final',
      original_transcript: originalTranscript,
      model_analysis: lastAnalysisData,
      user_feedback: { 
        rating: llmThumbRating, 
        comment: llmFeedbackComment ? llmFeedbackComment.value.trim() : '' 
      } 
    };

    llmFeedbackSubmit.disabled = true;
    llmFeedbackSubmit.textContent = 'Submitting...';
    try {
      const response = await fetch('http://18.222.120.158:5001/feedback', {
        method: 'POST',
        mode: 'cors',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
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

  // --- Errors ---
  function showError(msg) {
    errorEl.style.display = 'block';
    errorEl.textContent = msg;
    if (gaugeSpinnerEl) gaugeSpinnerEl.style.display = 'none';
    if (gaugeStatusEl) gaugeStatusEl.textContent = '';
  }
  function hideError() {
    errorEl.style.display = 'none';
    errorEl.textContent = '';
  }

  // --- Auto start ---
  showInitialView();
  setTimeout(() => safeStartAnalysis('auto-init'), 50);

  // --- YouTube URL watcher (debounced & gated) ---
  let lastVideoId = null;
  let lastUrl = null;
  let watchTimer = null;

  async function monitorYouTubeVideoChange() {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab || !tab.url) return;

      const url = tab.url;
      const match = url.match(/[?&]v=([^&]+)/) || url.match(/youtu\.be\/([^?]+)/);
      const currentVideoId = match ? match[1] : null;

      const urlChanged = url !== lastUrl;
      const videoChanged = currentVideoId && currentVideoId !== lastVideoId;

      if ((urlChanged || videoChanged) && /youtube\.com\/watch|youtu\.be\//.test(url)) {
        lastUrl = url;
        lastVideoId = currentVideoId || null;

        if (watchTimer) clearTimeout(watchTimer);
        watchTimer = setTimeout(() => {
          if (!isAnalyzing) {
            console.log('[watcher] starting analysis for new video/url');
            safeStartAnalysis('watcher');
          } else {
            console.log('[watcher] analysis in progress, will try later');
          }
        }, 600);
      }
    } catch (err) {
      console.warn('monitorYouTubeVideoChange error:', err);
    }
  }

  setInterval(monitorYouTubeVideoChange, 1000);
});