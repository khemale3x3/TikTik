"""
Chrome Load Times Mock - Mocks window.chrome.loadTimes

What it does:
    Creates a mock window.chrome.loadTimes function that returns
    page load timing information.

Why:
    Missing chrome.loadTimes is a headless browser fingerprint.
"""

chrome_load_times = """
if (window.chrome && !window.chrome.loadTimes) {
    window.chrome.loadTimes = function() {
        var performance = window.performance || window.webkitPerformance;
        var timing = performance ? performance.timing : undefined;
        if (timing) {
            return {
                requestTime: timing.navigationStart / 1000,
                startLoadTime: timing.navigationStart / 1000,
                commitLoadTime: timing.responseStart / 1000,
                finishDocumentLoadTime: timing.domContentLoadedEventEnd / 1000,
                finishLoadTime: timing.loadEventEnd / 1000,
                firstPaintTime: timing.navigationStart / 1000,
                firstPaintAfterLoadTime: 0,
                navigationType: 'Other',
                wasFetchedViaSpdy: true,
                wasNpnNegotiated: true,
                npnNegotiatedProtocol: 'h2',
                wasAlternateProtocolAvailable: false,
                connectionInfo: 'h2'
            };
        }
        return {};
    };
}
"""
