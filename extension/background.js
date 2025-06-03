// Listen for messages from content.js and popup.js
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.url) {
      // Save the URL in storage
      chrome.storage.local.set({ currentVideo: { url: message.url } });
      // Forward to popup if open
      chrome.runtime.sendMessage({
          type: "NEW_VIDEO",
          data: { url: message.url }
      });
      // Add to history
      chrome.storage.local.get("urlList", result => {
          const list = result.urlList || [];
          if (!list.includes(message.url)) {
              list.push(message.url);
              chrome.storage.local.set({ urlList: list });
          }
      });
      sendResponse && sendResponse({ status: "ok" });
  }
  if (message.action === 'setBadge') {
      chrome.action.setBadgeText({ text: message.value });
      chrome.action.setBadgeBackgroundColor({ color: "#4caf50" });
  }
  return true;
});

// Keep a history of all watched URLs
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === "complete"
        && tab.url
        && (tab.url.includes("youtube.com") || tab.url.includes("youtu.be"))
    ) {
        chrome.storage.local.get("urlList", result => {
            const list = result.urlList || [];
            if (!list.includes(tab.url)) {
                list.push(tab.url);
                chrome.storage.local.set({ urlList: list }, () => {
                    // Optionally log for debugging
                    // console.log("[background] urlList updated:", tab.url);
                });
            }
        });
    }
});
