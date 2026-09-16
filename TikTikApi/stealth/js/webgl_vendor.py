"""
WebGL Vendor Mock

What it does:
    Patches WebGLRenderingContext.getParameter to return realistic
    GPU vendor/renderer information.

Why:
    Headless browsers may report generic or missing WebGL info.
"""

webgl_vendor = """
try {
    var getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
        if (parameter === 37445) {
            return opts.webgl_vendor || 'Intel Inc.';
        }
        if (parameter === 37446) {
            return opts.webgl_renderer || 'Intel Iris OpenGL Engine';
        }
        return getParameter.apply(this, arguments);
    };

    // Also patch WebGL2 if available
    if (typeof WebGL2RenderingContext !== 'undefined') {
        var getParameter2 = WebGL2RenderingContext.prototype.getParameter;
        WebGL2RenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) {
                return opts.webgl_vendor || 'Intel Inc.';
            }
            if (parameter === 37446) {
                return opts.webgl_renderer || 'Intel Iris OpenGL Engine';
            }
            return getParameter2.apply(this, arguments);
        };
    }
} catch(e) {}
"""
