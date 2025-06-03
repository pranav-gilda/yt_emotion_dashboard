// Simple function to send URL to background script
function sendVideoUrl() {
    const currentURL = window.location.href;
    console.log('[content] Sending URL to background:', currentURL);
    
    safeSendMessage({ url: currentURL });
}

// Listen for SPA navigation (YouTube uses pushState/replaceState)
(function(history) {
    const pushState = history.pushState;
    const replaceState = history.replaceState;
    history.pushState = function() {
        const result = pushState.apply(history, arguments);
        window.dispatchEvent(new Event("locationchange"));
        return result;
    };
    history.replaceState = function() {
        const result = replaceState.apply(history, arguments);
        window.dispatchEvent(new Event("locationchange"));
        return result;
    };
    window.addEventListener("popstate", function() {
        window.dispatchEvent(new Event("locationchange"));
    });
})(window.history);

// Listen for URL changes
window.addEventListener("locationchange", sendVideoUrl);

// Initial page load
console.log('[content] Content script loaded');
sendVideoUrl();

// == Speedometer Overlay for YouTube ==

// --- Inject CSS ---
const style = document.createElement('style');
style.textContent = `
#yt-speedo-overlay {
  position: fixed;
  top: 80px;
  right: 40px;
  z-index: 99999;
  background: #23272f;
  border-radius: 18px;
  box-shadow: 0 2px 16px #000a;
  padding: 18px 18px 10px 18px;
  width: 260px;
  transition: opacity 0.3s;
  opacity: 0.97;
  color: #fff;
  font-family: 'Segoe UI', Arial, sans-serif;
}
#yt-speedo-refresh-icon {
  position: absolute;
  top: 8px;
  right: 12px;
  background: none;
  border: none;
  color: #aaa;
  font-size: 1.3em;
  cursor: pointer;
  padding: 2px 6px;
  z-index: 2;
}
#yt-speedo-refresh-icon:hover {
  color: #fff;
}
#yt-speedo-info {
  position: absolute;
  bottom: 6px;
  left: 50%;
  transform: translateX(-50%);
  background: #333;
  border: none;
  color: #fff;
  font-size: 1em;
  cursor: pointer;
  padding: 6px 18px;
  border-radius: 8px;
  font-weight: bold;
  box-shadow: 0 1px 4px #0005;
  display: flex;
  align-items: center;
  gap: 6px;
}
#yt-speedo-info:hover {
  background: #444;
}
#yt-speedo-modal {
  display: none;
  position: fixed;
  top: 80px;
  right: 40px;
  width: 260px;
  max-width: 95vw;
  height: 520px;
  max-height: 90vh;
  background: #23272f;
  border-radius: 18px;
  box-shadow: 0 2px 16px #000a;
  padding: 24px 18px 18px 18px;
  z-index: 100000;
  overflow-y: auto;
}
#yt-speedo-modal h2 {
  margin: 0 0 16px 0;
  font-size: 1.2em;
  color: #fff;
  text-align: center;
}
#yt-speedo-modal-section {
  margin-bottom: 18px;
}
#yt-speedo-modal .emotions-row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}
#yt-speedo-modal .emotions-col {
  flex: 1;
}
#yt-speedo-modal .emotions-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
#yt-speedo-modal .emotion-item {
  background: #2a2f3a;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 0.95em;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
#yt-speedo-modal .emotion-label {
  color: #fff;
}
#yt-speedo-modal .emotion-type {
  color: #aaa;
  font-size: 0.9em;
}
#yt-speedo-modal-close {
  position: absolute;
  top: 12px;
  right: 12px;
  background: none;
  border: none;
  color: #aaa;
  font-size: 1.2em;
  cursor: pointer;
}
#yt-speedo-modal-close:hover {
  color: #fff;
}
`;
document.head.appendChild(style);

// --- Inject Overlay HTML ---
function injectSpeedoOverlay() {
  if (document.getElementById('yt-speedo-overlay')) return;
  const overlay = document.createElement('div');
  overlay.id = 'yt-speedo-overlay';
  overlay.innerHTML = `
    <button id="yt-speedo-refresh-icon" title="Refresh" style="position:absolute;top:14px;left:14px;width:32px;height:32px;display:flex;align-items:center;justify-content:center;background:#23272f;border:none;color:#2196f3;cursor:pointer;z-index:3;padding:0;border-radius:50%;box-shadow:0 1px 4px #0003;transition:background 0.2s;"><svg xmlns='http://www.w3.org/2000/svg' width='20' height='20' fill='none' viewBox='0 0 24 24'><path d='M17.65 6.35A7.95 7.95 0 0 0 12 4V1l-4 4 4 4V6c1.93 0 3.68.78 4.95 2.05A7 7 0 1 1 5 12H3a9 9 0 1 0 14.65-5.65z' fill='#2196f3'/></svg></button>
    <button id="yt-speedo-close" title="Close" style="position:absolute;top:14px;right:14px;font-size:1.2em;background:none;border:none;color:#aaa;cursor:pointer;z-index:3;">&times;</button>
    <h3 style="text-align:center;font-size:1.1em;font-weight:bold;margin:0 0 8px 0;position:relative;z-index:1;">Video Analysis</h3>
    <svg id="yt-speedo-gauge" width="220" height="120" viewBox="0 0 220 120" style="display:block;margin:0 auto;">
      <path d="M20,100 A90,90 0 0,1 200,100" fill="none" stroke="#444" stroke-width="18"/>
      <path id="yt-gauge-arc" d="M20,100 A90,90 0 0,1 200,100" fill="none" stroke="url(#yt-gauge-gradient)" stroke-width="14"/>
      <defs>
        <linearGradient id="yt-gauge-gradient">
          <stop offset="0%" stop-color="#ff4d4f"/>
          <stop offset="50%" stop-color="#ffd700"/>
          <stop offset="100%" stop-color="#4caf50"/>
        </linearGradient>
      </defs>
      <line id="yt-gauge-needle" x1="110" y1="100" x2="110" y2="30" stroke="#fff" stroke-width="5" stroke-linecap="round"/>
      <circle cx="110" cy="100" r="8" fill="#23272f" stroke="#888" stroke-width="3"/>
      <text x="20" y="115" fill="#bbb" font-size="0.95em">-0.2</text>
      <text x="185" y="115" fill="#bbb" font-size="0.95em" text-anchor="end">+0.2</text>
    </svg>
    <div id="yt-speedo-labels" style="display:flex;justify-content:space-between;margin:8px 0 0 0;font-size:1em;z-index:2;position:relative;">
      <span>Contempt: <span id="yt-contempt-value" style="font-weight:bold;">-</span></span>
      <span>Respect: <span id="yt-respect-value" style="font-weight:bold;">-</span></span>
    </div>
    <button id="yt-speedo-info" title="Learn More" style="margin:14px auto 0 auto;display:flex;align-items:center;justify-content:center;background:#333;border:none;color:#fff;font-size:1em;cursor:pointer;padding:6px 18px;border-radius:8px;font-weight:bold;box-shadow:0 1px 4px #0005;gap:6px;width:100%;z-index:3;position:relative;"><svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' fill='none' viewBox='0 0 24 24' style='margin-right:4px;'><circle cx='12' cy='12' r='10' stroke='#2196f3' stroke-width='2' fill='none'/><rect x='11' y='10' width='2' height='7' rx='1' fill='#2196f3'/><rect x='11' y='7' width='2' height='2' rx='1' fill='#2196f3'/></svg> Learn More</button>
  `;
  document.body.appendChild(overlay);

  // Add modal HTML
  let modal = document.getElementById('yt-speedo-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'yt-speedo-modal';
    document.body.appendChild(modal);
  }
  modal.style.zIndex = 100000;
  modal.style.display = 'none';

  // Add event listeners
  document.getElementById('yt-speedo-close').onclick = () => {
    overlay.style.display = 'none';
  };
  document.getElementById('yt-speedo-refresh-icon').onclick = () => {
    analyzeCurrentVideo();
  };
  document.getElementById('yt-speedo-info').onclick = (e) => {
    e.stopPropagation();
    modal.style.display = 'block';
    modal.focus && modal.focus();
  };
  // Modal close event is attached in updateInfoModal
}

// --- Gauge Update Logic ---
function updateSpeedoGauge(avgRespect, avgContempt) {
  const combinedScore = avgRespect - avgContempt;
  const min = -0.2, max = 0.2;
  const angle = 180 - ((combinedScore - min) / (max - min)) * 180;
  const r = 70;
  const cx = 110, cy = 100;
  const rad = (angle * Math.PI) / 180;
  const x2 = cx + r * Math.cos(rad);
  const y2 = cy - r * Math.sin(rad);

  const needle = document.getElementById('yt-gauge-needle');
  if (needle) {
    needle.setAttribute('x2', x2);
    needle.setAttribute('y2', y2);
  }

  const respectValue = document.getElementById('yt-respect-value');
  if (respectValue) respectValue.innerHTML = `<b>${avgRespect.toFixed(3)}</b>`;

  const contemptValue = document.getElementById('yt-contempt-value');
  if (contemptValue) contemptValue.innerHTML = `<b>${avgContempt.toFixed(3)}</b>`;
}

// Safe sendMessage wrapper to avoid connection errors
function safeSendMessage(message, callback) {
  try {
    chrome.runtime.sendMessage(message, callback);
  } catch (e) {
    if (!e.message.includes('Could not establish connection')) throw e;
  }
}

// --- Analysis Logic ---
async function analyzeCurrentVideo(retries = 3, delay = 1200) {
  injectSpeedoOverlay();
  const overlay = document.getElementById('yt-speedo-overlay');
  overlay.querySelector('h3').textContent = 'Analyzing video...';
  document.getElementById('yt-respect-value').innerHTML = '-';
  document.getElementById('yt-contempt-value').innerHTML = '-';

  try {
    const url = window.location.href;
    // Notify background for badge/history
    safeSendMessage({ url });

    const response = await fetch('http://localhost:8080/process_video', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });

    if (!response.ok) {
      const errorText = await response.text();
      if (errorText.includes('No transcript available') && retries > 0) {
        setTimeout(() => analyzeCurrentVideo(retries - 1, delay), delay);
        return;
      }
      overlay.querySelector('h3').textContent = 'Error';
      document.getElementById('yt-respect-value').innerHTML = '-';
      document.getElementById('yt-contempt-value').innerHTML = '-';
      return;
    }

    const data = await response.json();
    overlay.querySelector('h3').textContent = 'Video Analysis';
    // Update gauge with new aggregate scores
    updateSpeedoGauge(data.aggregate_scores.respect, data.aggregate_scores.contempt);
    document.getElementById('yt-respect-value').innerHTML = `<b>${data.aggregate_scores.respect.toFixed(3)}</b>`;
    document.getElementById('yt-contempt-value').innerHTML = `<b>${data.aggregate_scores.contempt.toFixed(3)}</b>`;

    // Update modal content with new structure
    updateInfoModal(data);

    // Set badge
    safeSendMessage({ action: 'setBadge', value: 'Y' });
  } catch (err) {
    overlay.querySelector('h3').textContent = 'Error';
    document.getElementById('yt-respect-value').innerHTML = '-';
    document.getElementById('yt-contempt-value').innerHTML = '-';
  }
}

// --- Modal Update Logic ---
function updateInfoModal(data) {
  const modal = document.getElementById('yt-speedo-modal');
  if (!modal) return;
  // Helper to render a category section
  function renderCategory(title, emotions, aggScore, color) {
    // Change Gratitude to Positive if in Respect
    if (title === 'Respect') {
      emotions = emotions.filter(e => e.label !== 'Gratitude');
    }
    if (title === 'Positive') {
      // Add Gratitude to Positive if not present
      if (!emotions.some(e => e.label === 'Gratitude') && data.emotions.respect) {
        const gratitude = data.emotions.respect.find(e => e.label === 'Gratitude');
        if (gratitude) emotions.push(gratitude);
      }
    }
    return `
      <div class="modal-cat-header" style="color:${color};font-weight:bold;font-size:1.08em;margin:18px 0 6px 0;display:flex;align-items:center;justify-content:space-between;">
        <span>${title}</span>
        <span style="background:${color};color:#fff;padding:2px 10px;border-radius:8px;font-size:1.05em;">${aggScore.toFixed(3)}</span>
      </div>
      <div class="emotions-list">
        ${emotions.map(e => `<div class="emotion-item"><span class="emotion-label">${e.label}</span><span class="emotion-score" style="color:${color};font-weight:bold;">${e.score.toFixed(3)}</span></div>`).join('')}
      </div>
    `;
  }
  // Color palette for categories
  const colors = {
    Respect: '#4caf50',
    Contempt: '#ff4d4f',
    Neutral: '#ffd700',
    Positive: '#2196f3',
    Negative: '#9c27b0'
  };
  modal.innerHTML = `
    <button id="yt-speedo-modal-close" title="Close">&times;</button>
    <h2 style="font-size:1.25em;font-weight:bold;text-align:center;margin-bottom:10px;">About the Analysis</h2>
    <div id="yt-speedo-modal-section">
      <div style="margin-bottom:14px;font-size:1.05em;color:#eee;">This extension uses the <b>RoBERTa-GoEmotions</b> model to analyze the emotional content of YouTube video transcripts. The model detects 28 different emotions and attitudes in the text.<br><br>The speedometer shows the balance between <b style='color:${colors.Respect}'>respect</b> (positive) and <b style='color:${colors.Contempt}'>contempt</b> (negative) emotions. The needle position indicates the overall emotional tone of the video.</div>
      ${renderCategory('Respect', data.emotions.respect, data.aggregate_scores.respect, colors.Respect)}
      ${renderCategory('Contempt', data.emotions.contempt, data.aggregate_scores.contempt, colors.Contempt)}
      ${renderCategory('Neutral', data.emotions.neutral, data.aggregate_scores.neutral, colors.Neutral)}
      ${renderCategory('Positive', data.emotions.positive, data.aggregate_scores.positive, colors.Positive)}
      ${renderCategory('Negative', data.emotions.negative, data.aggregate_scores.negative, colors.Negative)}
      <div style="margin-top:18px;font-size:1.05em;color:#bbb;">
        <b>Dominant Emotion:</b> <span style="color:#fff;font-weight:bold;">${data.dominant_emotion}</span> &nbsp; <b>Score:</b> <span style="color:#fff;">${data.dominant_emotion_score.toFixed(3)}</span><br>
        <b>Dominant Attitude:</b> <span style="color:#fff;font-weight:bold;">${data.dominant_attitude_emotion}</span> &nbsp; <b>Score:</b> <span style="color:#fff;">${data.dominant_attitude_score.toFixed(3)}</span>
      </div>
    </div>
  `;
  // Re-attach close event
  document.getElementById('yt-speedo-modal-close').onclick = () => {
    modal.style.display = 'none';
  };
}

// --- Detect Video Changes and Inject Overlay ---
let lastUrl = '';
function checkAndAnalyze() {
  if (window.location.href !== lastUrl && (/youtube\.com\/watch|youtu\.be\//.test(window.location.href))) {
    lastUrl = window.location.href;
    analyzeCurrentVideo();
  }
}
window.addEventListener("locationchange", checkAndAnalyze);
setInterval(checkAndAnalyze, 1000);
checkAndAnalyze(); // Initial run
