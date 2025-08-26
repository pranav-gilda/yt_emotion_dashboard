// This script controls the extension's side panel behavior.

// Only enable the side panel on YouTube video pages.
chrome.tabs.onUpdated.addListener(async (tabId, info, tab) => {
    if (!tab.url) return;
    const url = new URL(tab.url);
    if (url.hostname === "www.youtube.com") {
        await chrome.sidePanel.setOptions({
            tabId,
            path: "sidepanel.html",
            enabled: true,
        });
    } else {
        // Disable the side panel on other sites
        await chrome.sidePanel.setOptions({
            tabId,
            enabled: false,
        });
    }
});

// Open the side panel when the user clicks the extension's toolbar icon.
chrome.action.onClicked.addListener((tab) => {
    chrome.sidePanel.open({ windowId: tab.windowId });
});
