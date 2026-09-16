"""
Iframe Content Window - Proxies iframe contentWindow Access

What it does:
    Intercepts access to iframe contentWindow to prevent detection of
    headless browser state.

Why:
    Headless browsers handle iframe contentWindow differently than real
    browsers, which can be detected by anti-bot scripts.
"""

iframe_contentWindow = """
try {
    var originalAttachShadow = Element.prototype.attachShadow;
    if (originalAttachShadow) {
        Element.prototype.attachShadow = function() {
            return originalAttachShadow.apply(this, arguments);
        };
    }
} catch(e) {}
"""
