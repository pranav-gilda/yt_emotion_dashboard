console.log('[Content Script] Loaded. Using direct transcript fetch method.');

// --- All helper functions for fetching transcript from YouTube's internal API ---
async function postData(url = "", data = {}) { /* ... Omitted for brevity, code is identical to previous correct version ... */ const response = await fetch(url, { method: "POST", mode: "cors", cache: "no-cache", credentials: "same-origin", headers: { "Content-Type": "application/json", Accept: "application/json", }, redirect: "follow", referrerPolicy: "no-referrer", body: JSON.stringify(data), }); return response.json(); }
async function fetchData(url, json = false) { try { const response = await fetch(url); if (json) return await response.json(); else return await response.text(); } catch (e) { return null; } }
function unescapeXml(escapedXml, parser) { const doc = parser.parseFromString(escapedXml, "text/html"); return doc.documentElement.textContent; }
function formatXML(xml) { const docParser = new DOMParser(); const doc = docParser.parseFromString(xml, 'application/xml'); let texts = doc.querySelectorAll('text'); let chunks = []; for (let t of texts) { let text = unescapeXml(t.textContent, docParser); text = text.replace(/\s+/g, ' ').trim(); if (text.length > 0) { chunks.push(text); } } return chunks; }
async function getChunks(url) { try { const transcript = await fetchData(url); if (!transcript) return []; return formatXML(transcript); } catch (e) { return []; } }
function getTranscriptURL(yt) { const captions = yt.captions ? yt.captions.playerCaptionsTracklistRenderer : null; if (!captions || !captions.captionTracks) return null; const englishTrack = captions.captionTracks.find(t => t.languageCode === 'en'); if (englishTrack) return englishTrack.baseUrl; const translatableTrack = captions.captionTracks.find(t => t.isTranslatable); if (translatableTrack) return translatableTrack.baseUrl + '&tlang=en'; return null; }
async function getTranscript(videoId) { const payload = { videoId, context: { client: { clientName: "WEB", clientVersion: "2.20210721.00.00" } } }; const json = await postData("https://www.youtube.com/youtubei/v1/player", payload); if (json.error || !json.captions) throw new Error('Could not retrieve video data or captions.'); const transcriptUrl = getTranscriptURL(json); if (!transcriptUrl) throw new Error('No English or translatable transcript found for this video.'); const chunks = await getChunks(transcriptUrl); return chunks.join(' '); }

// --- Main listener for the side panel's request ---
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'SCRAPE_TRANSCRIPT') {
        (async () => {
            try {
                const url = new URL(window.location.href);
                const videoId = url.searchParams.get("v");
                if (!videoId) {
                    throw new Error("Could not find video ID in the URL.");
                }
                const fullTranscript = await getTranscript(videoId);
                sendResponse({ success: true, transcript: fullTranscript });
            } catch (err) {
                console.error("Transcript fetch error:", err);
                sendResponse({ success: false, error: err.message });
            }
        })(); 
        return true; // Keep message channel open for async response
    }
});