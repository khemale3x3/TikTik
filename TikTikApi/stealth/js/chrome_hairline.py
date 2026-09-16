"""
Chrome Hairline Detection - Patches offsetHeight

What it does:
    Patches Element.prototype.offsetHeight to return consistent values.
    Hairline detection is a technique where bots are identified by elements
    having unexpectedly small heights.

Why:
    Headless browsers may render elements differently, causing hairline
    detection scripts to flag the browser as automated.
"""

chrome_hairline = """
try {
    var originalOffsetHeight = Object.getOwnPropertyDescriptor(
        Element.prototype, 'offsetHeight'
    );
    if (originalOffsetHeight) {
        Object.defineProperty(Element.prototype, 'offsetHeight', {
            get: function() {
                var value = originalOffsetHeight.get.call(this);
                if (value === 1) return 2;
                return value;
            },
            configurable: true
        });
    }
} catch(e) {}
"""
