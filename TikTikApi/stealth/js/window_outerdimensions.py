"""
Window Outer Dimensions Mock

What it does:
    Patches window.outerWidth and window.outerHeight to return realistic
    dimensions that match a real browser window.

Why:
    Headless browsers may report 0 for outer dimensions.
"""

window_outerdimensions = """
try {
    if (window.outerWidth === 0) {
        Object.defineProperty(window, 'outerWidth', {
            get: function() { return window.innerWidth; },
            configurable: true
        });
    }
    if (window.outerHeight === 0) {
        Object.defineProperty(window, 'outerHeight', {
            get: function() { return window.innerHeight + 85; },
            configurable: true
        });
    }
} catch(e) {}
"""
