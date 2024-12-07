// popup.js
document.addEventListener('DOMContentLoaded', function() {
    console.log('Popup loaded'); // Debug log
    
    document.getElementById('startScrapingBtn').addEventListener('click', async () => {
        console.log('Start button clicked'); // Debug log
        
        const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
        console.log('Found active tab:', tab); // Debug log
        
        if (tab) {
            chrome.tabs.sendMessage(tab.id, {action: "START_SCRAPING"}, response => {
                console.log('Response received:', response); // Debug log
            });
        }
    });
});