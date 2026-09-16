"""
Navigator Platform Mock

What it does:
    Sets navigator.platform to a realistic value if configured.

Why:
    Headless browsers may report incorrect platform information.
"""

navigator_platform = """
try {
    if (opts.navigator_platform) {
        Object.defineProperty(navigator, 'platform', {
            get: function() { return opts.navigator_platform; },
            configurable: true
        });
    }
} catch(e) {}
"""
