// This content script's job is to listen for requests from the side panel
// and scrape the transcript from the page when asked.

console.log('[Content Script] Loaded and listening for messages.');

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

async function getChunks(url) {
    try {
        const transcript = await fetchData(url)
        return formatXML(transcript)
    } catch (e) {
        return []
    }
}

function formatXML(xml) {
    const docParser = new DOMParser()
    const doc = docParser.parseFromString(xml, 'application/xml')
    let texts = doc.querySelectorAll('text')
    let chunks = []
    for (let t of texts) {
        let start = parseFloat(t.getAttribute('start')) * 1000
        let dur = parseFloat(t.getAttribute('dur')) * 1000
        if (isNaN(dur))
            dur = 0.01
        let end = start + dur
        let text = unescapeXml(t.textContent, docParser)
        text = text.replace(/\s+/g, ' ')
        if (text > '') {
            chunks.push({ text, start, end, dur })
        }
    }
    return chunks
}

function unescapeXml(escapedXml, parser) {
    const doc = parser.parseFromString(escapedXml, "text/html")
    return doc.documentElement.textContent;
}

async function fetchData(url, json = false) {
  try {
    const response = await fetch(url)
    if (json)
        return await response.json()
    else
        return await response.text()
  } catch (e) {
    return null
  }
}

function getTranscriptURLAndLanguage(yt, preferredLanguage = 'en') {
    const captions = yt.captions ? yt.captions.playerCaptionsTracklistRenderer : null
    if (!captions || !captions.captionTracks)
        return { defaultLanguage: 'en', transcripts: {} }
    const idx = captions.defaultAudioTrackIndex ?? 0
    const audioTrack = captions.audioTracks[idx]
    let defaultCaptionTrackIndex = audioTrack.defaultCaptionTrackIndex ?? 0
    if (!defaultCaptionTrackIndex && audioTrack.captionTrackIndices && audioTrack.captionTrackIndices.length > 0)
        defaultCaptionTrackIndex = audioTrack.captionTrackIndices[0]
    const captionTrack = captions.captionTracks[defaultCaptionTrackIndex]
    const translatable = captions.captionTracks.filter(c => c.isTranslatable === true)
    let defaultLanguage = 'en'
    let obj = {}
    if (captionTrack) {
        defaultLanguage = captionTrack.languageCode
        if (defaultLanguage.indexOf('-') !== -1)
            defaultLanguage = defaultLanguage.split('-')[0]
        obj[defaultLanguage] = captionTrack.baseUrl
    }
    // for iOS, we always want the English track because the DistilBert only works with English for now
    if (!obj['en']) {
        if (captionTrack && captionTrack.isTranslatable) {
            obj['en'] = captionTrack.baseUrl + '&tlang=en'
        } else if (translatable.length > 0) {
            obj['en'] = translatable[0].baseUrl + '&tlang=en'
        }
    }
    if (preferredLanguage !== 'en') {
        if (captionTrack && captionTrack.isTranslatable) {
            obj[preferredLanguage] = captionTrack.baseUrl + '&tlang=' + preferredLanguage
        } else if (translatable.length > 0) {
            obj[preferredLanguage] = translatable[0].baseUrl + '&tlang=' + preferredLanguage
        }
    }
    const translationLanguages = {}
    if (captions.translationLanguages) {
        for (let l of captions.translationLanguages) {
            translationLanguages[l.languageCode] = l.languageName.simpleText
        }
    }
    return { defaultLanguage, transcripts: obj, translationLanguages }
}

async function getTranscript(videoId = 'LPZh9BOjkQs', languageCode = 'en') {
    const payload = {
        videoId,
        "context": {
            "client": {
                "hl": "en",
                "clientName": "WEB",
                "clientVersion": "2.20210721.00.00",
                "clientScreen": "WATCH",
                "mainAppWebInfo": {
                    "graftUrl": "/watch?v=" + videoId
                }
            },
            "user": {
                "lockedSafetyMode": false
            },
            "request": {
                "useSsl": true,
                "internalExperimentFlags": [],
                "consistencyTokenJars": []
            }
        },
        "playbackContext": {
            "contentPlaybackContext": {
                "vis": 0,
                "splay": false,
                "autoCaptionsDefaultOn": false,
                "autonavState": "STATE_NONE",
                "html5Preference": "HTML5_PREF_WANTS",
                "lactMilliseconds": "-1"
            }
        },
        "racyCheckOk": false,
        "contentCheckOk": false
    }
    // https://stackoverflow.com/questions/67615278/get-video-info-youtube-endpoint-suddenly-returning-404-not-found
    const json = await postData(
        "https://release-youtubei.sandbox.googleapis.com/youtubei/v1/player", payload)
    const obj = {}
    if (json.error || json.videoDetails === undefined)
        return { error: 'invalid video' }
    obj.videoId = json.videoDetails.videoId
    obj.title = json.videoDetails.title
    obj.description = json.videoDetails.shortDescription

    obj.viewCount = json.videoDetails.viewCount
    obj.duration = parseInt(json.videoDetails.lengthSeconds)
    if (json.microformat && json.microformat.playerMicroformatRenderer)
        obj.publishDate = json.microformat.playerMicroformatRenderer.publishDate
    obj.thumbnail = `https://img.youtube.com/vi/${obj.videoId}/mqdefault.jpg`
    const { defaultLanguage, transcripts, translationLanguages } = getTranscriptURLAndLanguage(json, languageCode)
    obj.translationLanguages = translationLanguages
    obj.defaultLanguage = defaultLanguage ?? 'en'
    for (let languageCode in transcripts) {
        const chunks = await getChunks(transcripts[languageCode])
        obj[languageCode] = { chunks }
    }
    return obj
}

/**
 * Listens for messages from other parts of the extension (like the side panel).
 * When it receives a 'SCRAPE_TRANSCRIPT' request, it finds the transcript on the page
 * and sends the result back as a direct response.
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    // Check if the message is the one we're waiting for
    if (message.type === 'SCRAPE_TRANSCRIPT') {
        console.log('[Content Script] Received SCRAPE_TRANSCRIPT request.');
        /*// This is the selector your supervisor provided to find the transcript text elements.
        const transcriptElements = document.querySelectorAll(
            'yt-formatted-string.segment-text.style-scope.ytd-transcript-segment-renderer'
        );

        // If no elements are found, it means the transcript is not open on the page.
        if (transcriptElements.length === 0) {
            console.warn('[Content Script] No transcript segments found on the page.');
            // Send a failure response back to the side panel.
            sendResponse({ success: false, error: "Transcript not visible. Please click 'Show transcript' on the YouTube page first." });
            return; // Stop the function here.
        }

        // If elements are found, extract their text content.
        const texts = Array.from(transcriptElements)
            .map(el => el.textContent.trim())
            .filter(t => t.length > 0);
        
        const fullTranscript = texts.join(' ');

        console.log('[Content Script] Transcript scraped successfully.');
        // Send the successful result back to the side panel.
        sendResponse({ success: true, transcript: fullTranscript });*/

        (async () => {
            try {
                const url = new URL(window.location.href);
                const videoId = url.searchParams.get("v");
                const obj = await getTranscript(videoId, 'en');
                const fullTranscript = obj.en.chunks.map(c => c.text).join(' ')
                sendResponse({ success: true, transcript: fullTranscript });
            } catch (err) {
                sendResponse({ success: false });
            }
        })();        
    }

    // Return true to indicate that we will send a response asynchronously.
    // This is important to keep the message channel open.
    return true;
});