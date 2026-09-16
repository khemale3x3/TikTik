"""
Navigator Vendor Mock

What it does:
    Sets navigator.vendor to a realistic value if configured.

Why:
    Incorrect navigator.vendor values are a bot detection signal.
"""

navigator_vendor = """
try {
    if (opts.navigator_vendor) {
        Object.defineProperty(navigator, 'vendor', {
            get: function() { return opts.navigator_vendor; },
            configurable: true
        });
    }
} catch(e) {}
"""
