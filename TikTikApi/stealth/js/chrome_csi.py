"""
Chrome CSI Mock - Mocks window.chrome.csi

What it does:
    Creates a mock window.chrome.csi object with timing information.
    Real Chrome browsers expose this for page load metrics.

Why:
    Missing chrome.csi is a headless browser fingerprint.
"""

chrome_csi = """
if (window.chrome && !window.chrome.csi) {
    window.chrome.csi = function() {
        return {
            onloadT: Date.now(),
            pageT: performance.now(),
            startE: Date.now(),
            tran: 15
        };
    };
}
"""
