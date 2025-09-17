chrome.tabs.onUpdated.addListener(async (tabId, info, tab) => {
    if (!tab.url) return;
    const url = new URL(tab.url);
    if (url.hostname.includes("youtube.com")) {
        await chrome.sidePanel.setOptions({
            tabId,
            path: "sidepanel.html",
            enabled: true,
        });
    } else {
        await chrome.sidePanel.setOptions({
            tabId,
            enabled: false,
        });
    }
});

chrome.action.onClicked.addListener((tab) => {
    chrome.sidePanel.open({ windowId: tab.windowId });
});