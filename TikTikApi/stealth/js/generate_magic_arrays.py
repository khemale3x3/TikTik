"""
Generate Magic Arrays - Mocks MimeType and Plugin Arrays

What it does:
    Creates mock MimeTypeArray and PluginArray objects that resemble
    a real browser's plugin registry.

Why:
    Headless browsers typically have empty plugin arrays, which is a
    common bot detection vector.
"""

generate_magic_arrays = """
function generateMagicArray() {
    var pluginData = [
        {
            name: 'Chrome PDF Plugin',
            description: 'Portable Document Format',
            filename: 'internal-pdf-viewer',
            mimeTypes: [{type: 'application/x-google-chrome-pdf', suffixes: 'pdf', description: 'Portable Document Format'}]
        },
        {
            name: 'Chrome PDF Viewer',
            description: '',
            filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
            mimeTypes: [{type: 'application/pdf', suffixes: 'pdf', description: ''}]
        },
        {
            name: 'Native Client',
            description: '',
            filename: 'internal-nacl-plugin',
            mimeTypes: [{type: 'application/x-nacl', suffixes: '', description: 'Native Client Executable'}, {type: 'application/x-pnacl', suffixes: '', description: 'Portable Native Client Executable'}]
        }
    ];

    var mimes = [];
    var plugins = [];

    pluginData.forEach(function(p, i) {
        var plugin = {
            name: p.name,
            description: p.description,
            filename: p.filename,
            length: p.mimeTypes.length,
            item: function(index) { return p.mimeTypes[index] || null; },
            namedItem: function(name) {
                return p.mimeTypes.find(function(m) { return m.type === name; }) || null;
            },
            [Symbol.iterator]: function*() { yield* p.mimeTypes; }
        };

        p.mimeTypes.forEach(function(m) {
            m.enabledPlugin = plugin;
            mimes.push(m);
        });

        plugins.push(plugin);
    });

    Object.defineProperty(navigator, 'plugins', {
        get: function() {
            var arr = plugins;
            arr.item = function(index) { return plugins[index] || null; };
            arr.namedItem = function(name) {
                return plugins.find(function(p) { return p.name === name; }) || null;
            };
            arr.refresh = function() {};
            arr[Symbol.iterator] = function*() { yield* plugins; };
            Object.defineProperty(arr, 'length', { get: function() { return plugins.length; } });
            return arr;
        },
        configurable: true
    });

    Object.defineProperty(navigator, 'mimeTypes', {
        get: function() {
            var arr = mimes;
            arr.item = function(index) { return mimes[index] || null; };
            arr.namedItem = function(name) {
                return mimes.find(function(m) { return m.type === name; }) || null;
            };
            arr[Symbol.iterator] = function*() { yield* mimes; };
            Object.defineProperty(arr, 'length', { get: function() { return mimes.length; } });
            return arr;
        },
        configurable: true
    });
}

generateMagicArray();
"""
