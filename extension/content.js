// This content script's job is to listen for requests from the side panel
// and scrape the transcript from the page when asked.

console.log('[Content Script] Loaded and listening for messages.');

/**
 * Listens for messages from other parts of the extension (like the side panel).
 * When it receives a 'SCRAPE_TRANSCRIPT' request, it finds the transcript on the page
 * and sends the result back as a direct response.
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    // Check if the message is the one we're waiting for
    if (message.type === 'SCRAPE_TRANSCRIPT') {
        console.log('[Content Script] Received SCRAPE_TRANSCRIPT request.');
        
        // This is the selector your supervisor provided to find the transcript text elements.
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
        sendResponse({ success: true, transcript: fullTranscript });
    }
    
    // Return true to indicate that we will send a response asynchronously.
    // This is important to keep the message channel open.
    return true;
});
