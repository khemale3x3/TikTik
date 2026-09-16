"""
Stealth JS Utils - Shared JavaScript Utility Functions

What it does:
    Provides helper JavaScript functions used by other stealth scripts.
    These include utility functions for proxying object properties
    and creating mock browser API objects.

Why:
    Centralizing JS utilities prevents code duplication across stealth
    scripts and ensures consistent behavior.
"""

utils = """
// Utility functions for stealth scripts
const _utils = {
    // Proxy getter/setter on an object
    proxyGetter: function(obj, prop, getter) {
        Object.defineProperty(obj, prop, {
            get: getter,
            configurable: true
        });
    },
    // Create a simple mock function
    mockFunction: function(name) {
        return function() {
            return {};
        };
    }
};
"""
