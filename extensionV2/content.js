console.log('[Content Script] Loaded. Using direct transcript fetch method.');

// --- All functions below are from your teammate's version ---

async function postData(url = "", data = {}) {
    const response = await fetch(url, {
        method: "POST",
        mode: "cors",
        cache: "no-cache",
        credentials: "same-origin",
        headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
        },
        redirect: "follow",
        referrerPolicy: "no-referrer",
        body: JSON.stringify(data),
    });
    return response.json();
}

async function fetchData(url, json = false) {
    try {
        const response = await fetch(url);
        if (json) return await response.json();
        else return await response.text();
    } catch (e) {
        return null;
    }
}

function unescapeXml(escapedXml, parser) {
    const doc = parser.parseFromString(escapedXml, "text/html");
    return doc.documentElement.textContent;
}

function formatXML(xml) {
    const docParser = new DOMParser();
    const doc = docParser.parseFromString(xml, 'application/xml');
    let texts = doc.querySelectorAll('text');
    let chunks = [];
    for (let t of texts) {
        let start = parseFloat(t.getAttribute('start')) * 1000;
        let dur = parseFloat(t.getAttribute('dur')) * 1000;
        if (isNaN(dur)) dur = 0.01;
        let end = start + dur;
        let text = unescapeXml(t.textContent, docParser);
        text = text.replace(/\s+/g, ' ');
        if (text > '') {
            chunks.push({ text, start, end, dur });
        }
    }
    return chunks;
}

async function getChunks(url) {
    try {
        const transcript = await fetchData(url);
        return formatXML(transcript);
    } catch (e) {
        return [];
    }
}

function getTranscriptURLAndLanguage(yt, preferredLanguage = 'en') {
    const captions = yt.captions ? yt.captions.playerCaptionsTracklistRenderer : null;
    if (!captions || !captions.captionTracks) {
        // No captions at all.
        return null;
    }

    // Find an English track, auto-generated or manual
    let englishTrack = captions.captionTracks.find(t => t.languageCode === 'en');
    
    // If no explicit English track, find the default track IF it's translatable to English
    if (!englishTrack) {
        const defaultTrack = captions.captionTracks.find(t => t.isTranslatable);
        if (defaultTrack) {
            // Return its URL with a translate flag to English
            return defaultTrack.baseUrl + '&tlang=en';
        }
    }

    // If an English track was found, return its URL
    if (englishTrack) {
        return englishTrack.baseUrl;
    }
    
    // If all else fails, no usable transcript found
    return null;
}

async function getTranscript(videoId = 'LPZh9BOjkQs') {
    const payload = {
        videoId,
        "context": { "client": { "clientName": "WEB", "clientVersion": "2.20210721.00.00" } }
    };
    const json = await postData("https://www.youtube.com/youtubei/v1/player", payload);
    
    if (json.error || !json.captions) {
        throw new Error('Could not retrieve video data or captions.');
    }
    
    const transcriptUrl = getTranscriptURLAndLanguage(json, 'en');
    if (!transcriptUrl) {
        throw new Error('No English transcript found for this video.');
    }
    
    const chunks = await getChunks(transcriptUrl);
    return chunks.map(c => c.text).join(' ');
}


// --- Main listener for the side panel's request ---
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'SCRAPE_TRANSCRIPT') {
        (async () => {
            try {
                // Get video ID from the current page URL
                const url = new URL(window.location.href);
                const videoId = url.searchParams.get("v");
                if (!videoId) {
                    throw new Error("Could not find video ID in the URL.");
                }
                
                // Fetch the transcript
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