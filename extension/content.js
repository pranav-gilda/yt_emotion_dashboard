// This script is now designed to be programmatically injected.

async function getTranscriptFromPage() {
    // Helper function to make POST requests
    async function postData(url = "", data = {}) {
        const response = await fetch(url, {
            method: "POST", mode: "cors", cache: "no-cache", credentials: "same-origin",
            headers: { "Content-Type": "application/json", Accept: "application/json" },
            redirect: "follow", referrerPolicy: "no-referrer", body: JSON.stringify(data)
        });
        return response.json();
    }

    // Helper function to fetch raw text or JSON
    async function fetchData(url, json = false) {
        try {
            const response = await fetch(url);
            if (json) return await response.json();
            else return await response.text();
        } catch (e) { return null; }
    }

    // Helper function to unescape special characters from XML
    function unescapeXml(escapedXml, parser) {
        const doc = parser.parseFromString(escapedXml, "text/html");
        return doc.documentElement.textContent;
    }

    // Main function to parse the transcript XML
    function formatXML(xml) {
        const docParser = new DOMParser();
        const doc = docParser.parseFromString(xml, 'application/xml');
        let texts = doc.querySelectorAll('text');
        let chunks = [];
        for (let t of texts) {
            let text = unescapeXml(t.textContent, docParser);
            text = text.replace(/\s+/g, ' ').trim();
            if (text.length > 0) {
                chunks.push(text);
            }
        }
        return chunks;
    }

    // Fetches and processes the XML from a given URL
    async function getChunks(url) {
        try {
            const transcript = await fetchData(url);
            if (!transcript) return [];
            return formatXML(transcript);
        } catch (e) { return []; }
    }

    // Finds the best available English transcript URL from the video's metadata
    function getTranscriptURL(yt) {
        const captions = yt.captions ? yt.captions.playerCaptionsTracklistRenderer : null;
        if (!captions || !captions.captionTracks) return null;
        
        const englishTrack = captions.captionTracks.find(t => t.languageCode === 'en');
        if (englishTrack) return englishTrack.baseUrl;

        const translatableTrack = captions.captionTracks.find(t => t.isTranslatable);
        if (translatableTrack) return translatableTrack.baseUrl + '&tlang=en';

        return null;
    }

    // Main logic to get the full transcript text
    async function getTranscript(videoId) {
        const payload = { videoId, "context": { "client": { "clientName": "WEB", "clientVersion": "2.20210721.00.00" } } };
        const json = await postData("https://www.youtube.com/youtubei/v1/player", payload);
        if (json.error || !json.captions) throw new Error('Could not retrieve video data or captions.');
        
        const transcriptUrl = getTranscriptURL(json);
        if (!transcriptUrl) throw new Error('No English or translatable transcript found for this video.');
        
        const chunks = await getChunks(transcriptUrl);
        return chunks.join(' ');
    }

    // --- Script Execution ---
    try {
        const url = new URL(window.location.href);
        const videoId = url.searchParams.get("v");
        if (!videoId) throw new Error("Could not find video ID in URL.");
        
        const fullTranscript = await getTranscript(videoId);
        return { success: true, transcript: fullTranscript };
    } catch (err) {
        console.error("Content Script Error:", err);
        return { success: false, error: err.message };
    }
}

// Immediately execute the function. The return value is passed to the background script.
getTranscriptFromPage();
