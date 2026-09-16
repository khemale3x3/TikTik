"""
Navigator Permissions Mock

What it does:
    Proxies navigator.permissions.query to return realistic permission states.

Why:
    Headless browsers may return different permission states than real browsers.
"""

navigator_permissions = """
try {
    var originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = function(parameters) {
        if (parameters.name === 'notifications') {
            return Promise.resolve({ state: Notification.permission });
        }
        return originalQuery.apply(this, arguments);
    };
} catch(e) {}
"""
