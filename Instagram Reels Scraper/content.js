let isScrolling = false;

function scrollNext() {
    if (!isScrolling) return;

    try {
        // Select dynamically based on observed structure
        const reels = document.querySelectorAll('div[class*="x78zum5"]');
        if (reels.length > 0) {
            const lastReel = reels[reels.length - 1];
            const rect = lastReel.getBoundingClientRect();
            window.scrollBy({ top: rect.top, behavior: 'smooth' });
            console.log('Scrolling to last reel');
        } else {
            console.log('No reels found, waiting...');
        }

        // Wait for next scroll
        setTimeout(scrollNext, 2000);
    } catch (error) {
        console.error('Error during scrolling:', error);
    }
}

// Observer to detect new reels
const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
        console.log('DOM mutation detected');
        scrollNext(); // Trigger scrolling dynamically
    }
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "START_SCRAPING") {
        console.log('Starting scroll process');
        isScrolling = true;
        observer.observe(document.body, { childList: true, subtree: true }); // Start observing
        scrollNext();
    } else if (message.action === "STOP_SCRAPING") {
        console.log('Stopping scroll');
        isScrolling = false;
        observer.disconnect(); // Stop observing
    }
});
