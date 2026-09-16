"""
Navigator Languages Mock

What it does:
    Sets navigator.languages to a realistic language list.

Why:
    Missing or incorrect language lists are a bot detection signal.
"""

navigator_languages = """
try {
    if (opts.languages && opts.languages.length > 0) {
        Object.defineProperty(navigator, 'languages', {
            get: function() { return opts.languages; },
            configurable: true
        });
    }
} catch(e) {}
"""
