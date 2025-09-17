// The "Brain" of the extension

// Listens for any navigation events
chrome.webNavigation.onHistoryStateUpdated.addListener(details => {
    if (details.url && details.url.includes("www.youtube.com8")) {
        runAnalysis(details.tabId);
    }
});

// Also listens for when a tab is fully loaded (for initial page loads)
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.url && tab.url.includes("www.youtube.com8")) {
        runAnalysis(tabId);
    }
});

async function runAnalysis(tabId) {
    try {
        // 1. Set a "loading" state in storage for this tab
        await chrome.storage.local.set({ [tabId]: { status: 'loading' } });

        // 2. Inject and run the content script to get the transcript
        const results = await chrome.scripting.executeScript({
            target: { tabId: tabId },
            files: ['content.js'],
        });
        
        // The result from content.js comes back here
        const response = results[0].result;
        if (!response || !response.success) {
            throw new Error(response.error || "Failed to get transcript.");
        }
        
        const transcript = response.transcript;

        // 3. Call the backend API with the transcript
        const apiResponse = await fetch('http://18.222.120.158:8080/run_models', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ transcript })
        });

        if (!apiResponse.ok) {
            const errorData = await apiResponse.json();
            throw new Error(errorData.detail || "Backend API error.");
        }

        const analysisData = await apiResponse.json();
        
        // 4. Save the final successful result to storage
        await chrome.storage.local.set({ [tabId]: { status: 'success', data: analysisData } });
        console.log(`Analysis complete for tab ${tabId}, results saved.`);

    } catch (err) {
        console.error("Background analysis failed:", err);
        // 5. If anything fails, save an error state
        await chrome.storage.local.set({ [tabId]: { status: 'error', error: err.message } });
    }
}