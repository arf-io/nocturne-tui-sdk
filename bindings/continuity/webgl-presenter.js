/** Optional browser WebGL2 cell presenter. The renderer still produces ordinary
 * terminal cells on CPU/WASM. This class accelerates presentation, NOT world math.
 * No font file is fetched/bundled: glyph masks use the user's local monospace font.
 * Hosts retain a Canvas2D fallback and call dispose() on shutdown. */
class WebGLCellPresenter {
    constructor(canvas) {
        this.canvas = canvas;
        const gl = canvas.getContext('webgl2', { alpha: false, antialias: false, preserveDrawingBuffer: true });
        if (!gl)
            throw Error('WebGL2 unavailable; keep Canvas2D selected');
        this.gl = gl;
        this.lost = false;
        this.width = 0;
        this.height = 0;
        this.slots = new Map();
        this.dirtyAtlas = true;
        this.nextSlot = 0;
        this.pending = new Uint32Array(0);
        this.atlas = document.createElement('canvas');
        this.atlas.width = 512;
        this.atlas.height = 1024;
        this.context = this.atlas.getContext('2d');
        this.context.font = '13px monospace';
        this.context.textBaseline = 'alphabetic';
        this.context.fillStyle = '#fff';
        const vertex = `#version 300 es
  void main(){vec2 p=vec2(float((gl_VertexID<<1)&2),float(gl_VertexID&2));gl_Position=vec4(p*2.0-1.0,0.0,1.0);}`;
        const fragment = `#version 300 es
  precision highp float;precision highp int;precision highp usampler2D;
  uniform usampler2D cells;uniform sampler2D atlas;uniform ivec2 grid;
  out vec4 color;
  vec3 rgb(uint n){return vec3(float((n>>16u)&255u),float((n>>8u)&255u),float(n&255u))/255.0;}
  void main(){ivec2 pixel=ivec2(int(gl_FragCoord.x),grid.y*16-1-int(gl_FragCoord.y));ivec2 at=pixel/ivec2(8,16);uvec4 c=texelFetch(cells,at,0);ivec2 local=pixel%ivec2(8,16);int slot=int(c.r);ivec2 a=ivec2(slot%64*8,slot/64*16)+local;float mask=texelFetch(atlas,a,0).a;color=vec4(mix(rgb(c.b),rgb(c.g),mask),1.0);}`;
        const compile = (type, src) => { const shader = gl.createShader(type); gl.shaderSource(shader, src); gl.compileShader(shader); if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
            const msg = gl.getShaderInfoLog(shader);
            gl.deleteShader(shader);
            throw Error(msg);
        } return shader; };
        this.program = gl.createProgram();
        const vs = compile(gl.VERTEX_SHADER, vertex), fs = compile(gl.FRAGMENT_SHADER, fragment);
        gl.attachShader(this.program, vs);
        gl.attachShader(this.program, fs);
        gl.linkProgram(this.program);
        gl.deleteShader(vs);
        gl.deleteShader(fs);
        if (!gl.getProgramParameter(this.program, gl.LINK_STATUS))
            throw Error(gl.getProgramInfoLog(this.program));
        this.cellTexture = gl.createTexture();
        this.atlasTexture = gl.createTexture();
        this.vao = gl.createVertexArray();
        for (const [unit, texture] of [[0, this.cellTexture], [1, this.atlasTexture]]) {
            gl.activeTexture(gl.TEXTURE0 + unit);
            gl.bindTexture(gl.TEXTURE_2D, texture);
            gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
            gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
            gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
            gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
        }
        this.onLost = e => { e.preventDefault(); this.lost = true; };
        canvas.addEventListener('webglcontextlost', this.onLost);
        this.slot(32);
        this.slot(63);
    }
    /** Allocate a bounded glyph-atlas entry. Braille and half blocks use exact cell
     * coverage matching the Canvas renderer. Others use the local system font. */
    slot(code) {
        if (this.slots.has(code))
            return this.slots.get(code);
        if (this.nextSlot >= 4096)
            return this.slots.get(63) ?? 0;
        const slot = this.nextSlot++, x = slot % 64 * 8, y = Math.floor(slot / 64) * 16, c = this.context;
        this.slots.set(code, slot);
        c.clearRect(x, y, 8, 16);
        c.save();
        c.beginPath();
        c.rect(x, y, 8, 16);
        c.clip();
        if (code === 0x2580)
            c.fillRect(x, y, 8, 8);
        else if (code === 0x2584)
            c.fillRect(x, y + 8, 8, 8);
        else if (code === 0x258c)
            c.fillRect(x, y, 4, 16);
        else if (code === 0x2590)
            c.fillRect(x + 4, y, 4, 16);
        else if (code >= 0x2800 && code <= 0x28ff) {
            const bits = [1, 8, 2, 16, 4, 32, 64, 128];
            for (let i = 0; i < 8; i++)
                if ((code - 0x2800) & bits[i])
                    c.fillRect(x + (i % 2 ? 5 : 1), y + Math.floor(i / 2) * 4 + 1, 2, 2);
        }
        else if (code > 32 && code <= 0x10ffff)
            c.fillText(String.fromCodePoint(code), x, y + 13);
        c.restore();
        this.dirtyAtlas = true;
        return slot;
    }
    /** Present an owned frame without modifying its cells. No clocks/readback are
     * required on the interactive path. Throws on unavailable/lost context. */
    present(frame) {
        if (this.lost)
            throw Error('WebGL2 context lost; switch to Canvas2D');
        const gl = this.gl, W = frame.width, H = frame.height;
        if (!Number.isInteger(W) || !Number.isInteger(H) || W < 1 || H < 1 || W > 512 || H > 256 || frame.cells.length !== W * H * 4)
            throw RangeError('Cell frame');
        if (this.canvas.width !== W * 8 || this.canvas.height !== H * 16) {
            this.canvas.width = W * 8;
            this.canvas.height = H * 16;
        }
        if (this.pending.length !== frame.cells.length)
            this.pending = new Uint32Array(frame.cells.length);
        for (let i = 0; i < frame.cells.length; i += 4) {
            this.pending[i] = this.slot(frame.cells[i]);
            this.pending[i + 1] = frame.cells[i + 1];
            this.pending[i + 2] = frame.cells[i + 2];
            this.pending[i + 3] = frame.cells[i + 3];
        }
        gl.activeTexture(gl.TEXTURE0);
        gl.bindTexture(gl.TEXTURE_2D, this.cellTexture);
        if (this.width !== W || this.height !== H) {
            this.width = W;
            this.height = H;
            gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA32UI, W, H, 0, gl.RGBA_INTEGER, gl.UNSIGNED_INT, this.pending);
        }
        else
            gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, W, H, gl.RGBA_INTEGER, gl.UNSIGNED_INT, this.pending);
        gl.activeTexture(gl.TEXTURE1);
        gl.bindTexture(gl.TEXTURE_2D, this.atlasTexture);
        if (this.dirtyAtlas) {
            gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
            gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, this.atlas);
            this.dirtyAtlas = false;
        }
        gl.useProgram(this.program);
        gl.bindVertexArray(this.vao);
        gl.viewport(0, 0, W * 8, H * 16);
        gl.disable(gl.BLEND);
        gl.uniform1i(gl.getUniformLocation(this.program, 'cells'), 0);
        gl.uniform1i(gl.getUniformLocation(this.program, 'atlas'), 1);
        gl.uniform2i(gl.getUniformLocation(this.program, 'grid'), W, H);
        gl.drawArrays(gl.TRIANGLES, 0, 3);
    }
    dispose() { const g = this.gl; this.canvas.removeEventListener('webglcontextlost', this.onLost); g.deleteTexture(this.cellTexture); g.deleteTexture(this.atlasTexture); g.deleteVertexArray(this.vao); g.deleteProgram(this.program); this.lost = true; }
}

export {WebGLCellPresenter};
