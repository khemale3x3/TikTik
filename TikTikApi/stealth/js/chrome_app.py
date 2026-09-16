"""
Chrome App Mock - Mocks window.chrome.app

What it does:
    Creates a mock window.chrome.app object that resembles a real Chrome browser.
    Headless browsers typically lack this object, making them detectable.

Why:
    TikTik checks for the existence and properties of window.chrome to
    determine if the browser is a real Chrome instance.
"""

chrome_app = """
if (!window.chrome) {
    window.chrome = {};
}
if (!window.chrome.app) {
    window.chrome.app = {
        isInstalled: false,
        InstallState: {
            DISABLED: 'disabled',
            INSTALLED: 'installed',
            NOT_INSTALLED: 'not_installed'
        },
        RunningState: {
            CANNOT_RUN: 'cannot_run',
            READY_TO_RUN: 'ready_to_run',
            RUNNING: 'running'
        },
        getDetails: function() { return null; },
        getIsInstalled: function() { return false; },
        installState: function(callback) { if (callback) callback('not_installed'); },
        runningState: function() { return 'cannot_run'; }
    };
}
"""
