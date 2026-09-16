"""
Navigator User Agent Mock

What it does:
    Overrides navigator.userAgent to remove the "HeadlessChrome" string
    that headless browsers include.

Why:
    "HeadlessChrome" in the user agent is the most obvious bot detection signal.
"""

navigator_userAgent = """
try {
    if (opts.navigator_user_agent) {
        Object.defineProperty(navigator, 'userAgent', {
            get: function() { return opts.navigator_user_agent; },
            configurable: true
        });
    } else {
        // Remove HeadlessChrome from existing user agent
        var ua = navigator.userAgent;
        if (ua.indexOf('HeadlessChrome') !== -1) {
            Object.defineProperty(navigator, 'userAgent', {
                get: function() { return ua.replace('HeadlessChrome', 'Chrome'); },
                configurable: true
            });
        }
    }
} catch(e) {}
"""
