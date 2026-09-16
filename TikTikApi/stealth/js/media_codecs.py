"""
Media Codecs Mock - Mocks canPlayType for Media Codecs

What it does:
    Patches HTMLMediaElement.prototype.canPlayType to return realistic
    codec support information.

Why:
    Headless browsers may report different codec support than real browsers.
"""

media_codecs = """
try {
    var originalCanPlayType = HTMLMediaElement.prototype.canPlayType;
    HTMLMediaElement.prototype.canPlayType = function(type) {
        if (typeof type !== 'string') return '';
        var result = originalCanPlayType.apply(this, arguments);
        if (result === '') {
            if (type.indexOf('audio/mp4; codecs="mp4a.40.2"') !== -1) return 'probably';
            if (type.indexOf('video/mp4; codecs="avc1.42E01E, mp4a.40.2"') !== -1) return 'probably';
        }
        return result;
    };
} catch(e) {}
"""
