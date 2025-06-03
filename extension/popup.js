document.addEventListener('DOMContentLoaded', function() {
    const videoTitle = document.getElementById('videoTitle');
    const gaugeNeedle = document.getElementById('gaugeNeedle');
    const respectValue = document.getElementById('respectValue');
    const contemptValue = document.getElementById('contemptValue');
    const refreshBtn = document.getElementById('refreshBtn');
    const error = document.getElementById('error');

    const SCALE_MIN = -0.2;
    const SCALE_MAX = 0.2;

    function updateGauge(avgRespect, avgContempt) {
        const combinedScore = avgRespect - avgContempt;
        const min = SCALE_MIN, max = SCALE_MAX;
        const angle = 180 - ((combinedScore - min) / (max - min)) * 180;
        const r = 70;
        const cx = 110, cy = 100;
        const rad = (angle * Math.PI) / 180;
        const x2 = cx + r * Math.cos(rad);
        const y2 = cy - r * Math.sin(rad);
        gaugeNeedle.setAttribute('x2', x2);
        gaugeNeedle.setAttribute('y2', y2);

        respectValue.innerHTML = `<b>${avgRespect.toFixed(3)}</b>`;
        contemptValue.innerHTML = `<b>${avgContempt.toFixed(3)}</b>`;
    }

    function showError(msg) {
        error.style.display = 'block';
        error.innerHTML = msg + '<br><button id="tryAgainBtn" style="margin-top:8px;">Try Again</button>';
        document.getElementById('tryAgainBtn').onclick = () => tryBootstrapFromStorage();
    }

    function hideError() {
        error.style.display = 'none';
    }

    async function analyzeVideo(videoData, retries = 3, delay = 1200) {
        try {
            hideError();
            videoTitle.textContent = 'Analyzing video...';
            respectValue.innerHTML = '-';
            contemptValue.innerHTML = '-';

            const response = await fetch(`http://localhost:8080/process_video`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: videoData.url })
            });
            if (!response.ok) {
                const errorText = await response.text();
                if (errorText.includes('No transcript available') && retries > 0) {
                    setTimeout(() => analyzeVideo(videoData, retries - 1, delay), delay);
                    return;
                }
                showError(`Failed to process video: ${errorText}`);
                videoTitle.textContent = 'Error';
                return;
            }
            const data = await response.json();
            videoTitle.textContent = 'Video Analysis';
            updateGauge(data.avg_respect_score, data.avg_contempt_score);
        } catch (err) {
            showError(err.message);
            videoTitle.textContent = 'Error';
        }
    }

    chrome.runtime.onMessage.addListener((msg) => {
        if (msg.type === 'NEW_VIDEO' && msg.data) {
            analyzeVideo(msg.data);
        }
    });

    function tryBootstrapFromStorage(retries = 5) {
        chrome.storage.local.get('currentVideo', res => {
            if (res.currentVideo && res.currentVideo.url) {
                analyzeVideo(res.currentVideo);
            } else if (retries > 0) {
                setTimeout(() => tryBootstrapFromStorage(retries - 1), 400);
            } else {
                showError('No video selected');
            }
        });
    }

    tryBootstrapFromStorage();
    if (refreshBtn) refreshBtn.addEventListener('click', tryBootstrapFromStorage);
});
