"""
Navigator Plugins Mock

What it does:
    Mocks navigator.plugins to return a realistic plugin list.
    Headless browsers typically have empty or minimal plugin lists.

Why:
    Empty navigator.plugins is one of the most common bot detection signals.
"""

navigator_plugins = """
try {
    if (Object.getOwnPropertyDescriptor(navigator, 'plugins')) {
        var plugins = Object.getOwnPropertyDescriptor(navigator, 'plugins');
        if (plugins.get && plugins.get.toString().indexOf('native code') === -1) {
            // Already mocked, skip
        }
    }
} catch(e) {}
"""
