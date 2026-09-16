"""
Navigator Hardware Concurrency Mock

What it does:
    Sets navigator.hardwareConcurrency to a realistic value (default: 4 cores).
    Headless browsers may report 1 or an unrealistic number.

Why:
    Inconsistent hardware concurrency is a bot detection signal.
"""

navigator_hardwareConcurrency = """
try {
    Object.defineProperty(navigator, 'hardwareConcurrency', {
        get: function() { return opts.navigator_hardware_concurrency || 4; },
        configurable: true
    });
} catch(e) {}
"""
