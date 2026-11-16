/**
 * Nocturne WebGL Instanced Glyph-Atlas Tilemap Renderer
 *
 * Replaces per-cell Canvas2D fillRect/fillText loops with a single instanced quad
 * draw call sampling a pre-baked glyph texture atlas.
 */

export class WebGLTilemapRenderer {
  constructor(canvas, fontGallery) {
    this.canvas = canvas;
    this.fontGallery = fontGallery;
    this.cw = 10;
    this.ch = 20;
    this.atlasCols = 64;
    this.atlasRows = 64;
    this.atlasWidth = this.atlasCols * this.cw;   // 640
    this.atlasHeight = this.atlasRows * this.ch; // 1280
    this.glyphToSlot = new Map();
    this.nextSlot = 1; // Slot 0 is reserved for transparent space
    this.atlasDirty = false;

    // Try WebGL2 first, fallback to WebGL1 with ANGLE_instanced_arrays
    const glOpts = {
      alpha: false,
      antialias: false,
      depth: false,
      stencil: false,
      preserveDrawingBuffer: true
    };
    let gl = canvas.getContext('webgl2', glOpts);
    let isWebGL2 = true;
    let extInstanced = null;

    if (!gl) {
      gl = canvas.getContext('webgl', glOpts) || canvas.getContext('experimental-webgl', glOpts);
      isWebGL2 = false;
      if (gl) {
        extInstanced = gl.getExtension('ANGLE_instanced_arrays');
        if (!extInstanced) {
          throw new Error('WebGL instanced arrays not supported');
        }
      }
    }
    if (!gl) throw new Error('WebGL not supported');

    this.gl = gl;
    this.isWebGL2 = isWebGL2;
    this.extInstanced = extInstanced;

    // Helper wrappers for instanced calls
    this.drawArraysInstanced = (mode, first, count, primcount) => {
      if (this.isWebGL2) {
        this.gl.drawArraysInstanced(mode, first, count, primcount);
      } else {
        this.extInstanced.drawArraysInstancedANGLE(mode, first, count, primcount);
      }
    };
    this.vertexAttribDivisor = (index, divisor) => {
      if (this.isWebGL2) {
        this.gl.vertexAttribDivisor(index, divisor);
      } else {
        this.extInstanced.vertexAttribDivisorANGLE(index, divisor);
      }
    };

    // Offscreen 2D canvas for rasterizing the atlas
    this.atlasCanvas = document.createElement('canvas');
    this.atlasCanvas.width = this.atlasWidth;
    this.atlasCanvas.height = this.atlasHeight;
    this.atlasCtx = this.atlasCanvas.getContext('2d', { willReadFrequently: true });

    // Shaders & Program
    this._initProgram();

    // Buffers & VAO
    this._initBuffers();

    // Build the pre-baked atlas
    this._initAtlas();
  }

  _initProgram() {
    const gl = this.gl;
    const vsSource = `
      attribute vec2 a_quad;        // Unit quad [0..1, 0..1]
      attribute vec2 a_cellCoord;   // (col, row) in terminal grid
      attribute vec4 a_bgColor;     // (r, g, b, a) normalized
      attribute vec4 a_fgColor;     // (r, g, b, a) normalized
      attribute vec2 a_atlasCoord;  // (col, row) in glyph atlas

      uniform vec2 u_gridSize;      // (cols, rows)
      uniform vec2 u_cellSize;      // (cw, ch) in pixels
      uniform vec2 u_atlasSize;     // (width, height) of atlas texture

      varying vec4 v_bgColor;
      varying vec4 v_fgColor;
      varying vec2 v_uv;

      void main() {
        vec2 pixelPos = (a_cellCoord + a_quad) * u_cellSize;
        vec2 screenSize = u_gridSize * u_cellSize;
        vec2 clipPos = (pixelPos / screenSize) * 2.0 - 1.0;
        gl_Position = vec4(clipPos.x, -clipPos.y, 0.0, 1.0);

        vec2 atlasPixelPos = (a_atlasCoord + a_quad) * u_cellSize;
        v_uv = atlasPixelPos / u_atlasSize;
        v_bgColor = a_bgColor;
        v_fgColor = a_fgColor;
      }
    `;

    const fsSource = `
      precision mediump float;
      uniform sampler2D u_atlas;

      varying vec4 v_bgColor;
      varying vec4 v_fgColor;
      varying vec2 v_uv;

      void main() {
        float glyphAlpha = texture2D(u_atlas, v_uv).a;
        vec3 color = mix(v_bgColor.rgb, v_fgColor.rgb, glyphAlpha);
        gl_FragColor = vec4(color, 1.0);
      }
    `;

    const vs = this._compileShader(gl.VERTEX_SHADER, vsSource);
    const fs = this._compileShader(gl.FRAGMENT_SHADER, fsSource);
    const program = gl.createProgram();
    gl.attachShader(program, vs);
    gl.attachShader(program, fs);
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      throw new Error('Program link failed: ' + gl.getProgramInfoLog(program));
    }
    this.program = program;

    // Attribute locations
    this.a_quad = gl.getAttribLocation(program, 'a_quad');
    this.a_cellCoord = gl.getAttribLocation(program, 'a_cellCoord');
    this.a_bgColor = gl.getAttribLocation(program, 'a_bgColor');
    this.a_fgColor = gl.getAttribLocation(program, 'a_fgColor');
    this.a_atlasCoord = gl.getAttribLocation(program, 'a_atlasCoord');

    // Uniform locations
    this.u_gridSize = gl.getUniformLocation(program, 'u_gridSize');
    this.u_cellSize = gl.getUniformLocation(program, 'u_cellSize');
    this.u_atlasSize = gl.getUniformLocation(program, 'u_atlasSize');
    this.u_atlas = gl.getUniformLocation(program, 'u_atlas');
  }

  _compileShader(type, source) {
    const gl = this.gl;
    const shader = gl.createShader(type);
    gl.shaderSource(shader, source);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      const err = gl.getShaderInfoLog(shader);
      gl.deleteShader(shader);
      throw new Error('Shader compile failed: ' + err);
    }
    return shader;
  }

  _initBuffers() {
    const gl = this.gl;

    // Unit quad buffer (TRIANGLE_STRIP: 4 vertices)
    const quadVertices = new Float32Array([
      0, 0,
      1, 0,
      0, 1,
      1, 1
    ]);
    this.quadBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, this.quadBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, quadVertices, gl.STATIC_DRAW);

    // Dynamic instance buffer
    this.instanceBuffer = gl.createBuffer();
    this.maxInstances = 0;
    this.instanceData = null;
  }

  _initAtlas() {
    const gl = this.gl;
    const ctx = this.atlasCtx;
    ctx.clearRect(0, 0, this.atlasWidth, this.atlasHeight);

    // Slot 0: transparent space
    this.glyphToSlot.set(0, 0);
    this.glyphToSlot.set(32, 0);

    // 1. ASCII printable characters (33..126)
    for (let c = 33; c <= 126; c++) {
      this._bakeTextGlyph(c, String.fromCharCode(c));
    }

    // 2. Braille patterns (0x2800..0x28ff, 256 masks)
    const dots = [[.2,.1],[.2,.3],[.2,.55],[.7,.1],[.7,.3],[.7,.55],[.2,.8],[.7,.8]];
    for (let mask = 0; mask <= 255; mask++) {
      const glyph = 0x2800 + mask;
      const slot = this._allocSlot(glyph);
      const { x, y } = this._slotPos(slot);
      ctx.fillStyle = '#ffffff';
      for (let bit = 0; bit < 8; bit++) {
        if (mask & (1 << bit)) {
          const [column, row] = dots[bit];
          ctx.fillRect(x + column * this.cw, y + row * this.ch, this.cw * .2, this.ch * .1);
        }
      }
    }

    // 3. Block elements (0x2580..0x259f)
    for (let glyph = 0x2580; glyph <= 0x259f; glyph++) {
      const slot = this._allocSlot(glyph);
      const { x, y } = this._slotPos(slot);
      ctx.fillStyle = '#ffffff';
      switch (glyph) {
        case 0x2588: // Full block
          ctx.fillRect(x, y, this.cw, this.ch);
          break;
        case 0x2580: // Upper half
          ctx.fillRect(x, y, this.cw, this.ch / 2);
          break;
        case 0x2584: // Lower half
          ctx.fillRect(x, y + this.ch / 2, this.cw, this.ch / 2);
          break;
        case 0x258c: // Left half
          ctx.fillRect(x, y, this.cw / 2, this.ch);
          break;
        case 0x2590: // Right half
          ctx.fillRect(x + this.cw / 2, y, this.cw / 2, this.ch);
          break;
        case 0x2581: ctx.fillRect(x, y + this.ch * 7 / 8, this.cw, this.ch / 8); break;
        case 0x2582: ctx.fillRect(x, y + this.ch * 6 / 8, this.cw, this.ch * 2 / 8); break;
        case 0x2583: ctx.fillRect(x, y + this.ch * 5 / 8, this.cw, this.ch * 3 / 8); break;
        case 0x2585: ctx.fillRect(x, y + this.ch * 3 / 8, this.cw, this.ch * 5 / 8); break;
        case 0x2586: ctx.fillRect(x, y + this.ch * 2 / 8, this.cw, this.ch * 6 / 8); break;
        case 0x2587: ctx.fillRect(x, y + this.ch * 1 / 8, this.cw, this.ch * 7 / 8); break;
        case 0x2589: ctx.fillRect(x, y, this.cw * 7 / 8, this.ch); break;
        case 0x258a: ctx.fillRect(x, y, this.cw * 6 / 8, this.ch); break;
        case 0x258b: ctx.fillRect(x, y, this.cw * 5 / 8, this.ch); break;
        case 0x258d: ctx.fillRect(x, y, this.cw * 3 / 8, this.ch); break;
        case 0x258e: ctx.fillRect(x, y, this.cw * 2 / 8, this.ch); break;
        case 0x258f: ctx.fillRect(x, y, this.cw * 1 / 8, this.ch); break;
        case 0x2594: ctx.fillRect(x, y, this.cw, this.ch / 8); break;
        case 0x2595: ctx.fillRect(x + this.cw * 7 / 8, y, this.cw / 8, this.ch); break;
        default:
          this._drawTextIntoCell(x, y, String.fromCodePoint(glyph));
          break;
      }
    }

    // 4. Box drawing characters (0x2500..0x257f)
    for (let glyph = 0x2500; glyph <= 0x257f; glyph++) {
      this._bakeTextGlyph(glyph, String.fromCodePoint(glyph));
    }

    // Create GPU Texture
    this.atlasTexture = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, this.atlasTexture);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, this.atlasCanvas);
  }

  _allocSlot(glyph) {
    if (this.glyphToSlot.has(glyph)) return this.glyphToSlot.get(glyph);
    if (this.nextSlot >= this.atlasCols * this.atlasRows) {
      // Atlas full, wrap to dynamic pool after fixed range
      this.nextSlot = 512;
    }
    const slot = this.nextSlot++;
    this.glyphToSlot.set(glyph, slot);
    return slot;
  }

  _slotPos(slot) {
    const col = slot % this.atlasCols;
    const row = Math.floor(slot / this.atlasCols);
    return { col, row, x: col * this.cw, y: row * this.ch };
  }

  _drawTextIntoCell(x, y, text) {
    const ctx = this.atlasCtx;
    ctx.save();
    ctx.beginPath();
    ctx.rect(x, y, this.cw, this.ch);
    ctx.clip();
    ctx.font = this.fontGallery ? this.fontGallery.canvasFont(16) : '16px monospace';
    ctx.textBaseline = 'middle';
    ctx.textAlign = 'left';
    ctx.fillStyle = '#ffffff';
    ctx.fillText(text, x, y + this.ch / 2 + 1);
    ctx.restore();
  }

  _bakeTextGlyph(glyph, char) {
    const slot = this._allocSlot(glyph);
    const { x, y } = this._slotPos(slot);
    this._drawTextIntoCell(x, y, char);
    return slot;
  }

  getGlyphSlot(glyph) {
    if (glyph === 0 || glyph === 32) return 0;
    if (this.glyphToSlot.has(glyph)) return this.glyphToSlot.get(glyph);

    // Dynamic on-demand fallback glyph
    const slot = this._allocSlot(glyph);
    const { x, y, col, row } = this._slotPos(slot);
    const char = String.fromCodePoint(glyph <= 0x10ffff ? glyph : 0xfffd);

    // Clear slot on atlas canvas
    this.atlasCtx.clearRect(x, y, this.cw, this.ch);
    this._drawTextIntoCell(x, y, char);
    this.atlasDirty = true;
    return slot;
  }

  ensureCapacity(numCells) {
    if (numCells <= this.maxInstances) return;
    const gl = this.gl;
    this.maxInstances = Math.max(numCells, 7680);
    // Attributes per instance:
    // cellCol (f32: 4B)
    // cellRow (f32: 4B)
    // bgColor (u8x4: 4B)
    // fgColor (u8x4: 4B)
    // atlasCol (f32: 4B)
    // atlasRow (f32: 4B)
    // Stride = 24 bytes (6 words)
    this.instanceStride = 24;
    this.instanceBufferBytes = this.maxInstances * this.instanceStride;
    this.instanceData = new ArrayBuffer(this.instanceBufferBytes);
    this.f32View = new Float32Array(this.instanceData);
    this.u32View = new Uint32Array(this.instanceData);

    gl.bindBuffer(gl.ARRAY_BUFFER, this.instanceBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, this.instanceBufferBytes, gl.DYNAMIC_DRAW);
  }

  render(frame, promptSpans = [], promptSource = []) {
    const gl = this.gl;
    const width = frame.width;
    const height = frame.height;
    const numCells = width * height;
    const cw = this.cw;
    const ch = this.ch;

    // Viewport & Canvas resize
    if (this.canvas.width !== width * cw || this.canvas.height !== height * ch) {
      this.canvas.width = width * cw;
      this.canvas.height = height * ch;
    }
    gl.viewport(0, 0, this.canvas.width, this.canvas.height);

    this.ensureCapacity(numCells);

    // Check prompt covered cells
    const covered = new Map();
    for (const r of promptSpans) {
      if (r[7]) {
        for (let j = 0; j < r[4]; j++) {
          const idx = r[6] * width + r[5] + j;
          if (frame.cells[idx * 4 + 3] === 0x40000000) {
            covered.set(idx, { span: r, offset: j });
          }
        }
      }
    }

    const f32 = this.f32View;
    const u32 = this.u32View;
    const atlasCols = this.atlasCols;
    const cells = frame.cells;

    // Populate instance buffer
    let ptr = 0;
    for (let i = 0; i < numCells; i++) {
      const baseIdx = i * 4;
      const col = i % width;
      const row = Math.floor(i / width);
      let g = cells[baseIdx];
      let fg = cells[baseIdx + 1];
      const bg = cells[baseIdx + 2];

      // Handle prompt span character override
      if (covered.has(i)) {
        const info = covered.get(i);
        const r = info.span;
        const scalars = promptSource.slice(r[0], r[1]);
        if (scalars.length) scalars[0] = String.fromCodePoint(r[9]);
        const text = scalars.join('');
        if (info.offset < text.length) {
          g = text.codePointAt(info.offset) || 32;
          fg = cells[(r[6] * width + r[5]) * 4 + 1];
        } else {
          g = 32;
        }
      }

      const slot = (g === 0 || g === 32) ? 0 : this.getGlyphSlot(g);
      const atlasCol = slot % atlasCols;
      const atlasRow = Math.floor(slot / atlasCols);

      // Extract RGB components into 0xAABBGGRR for Uint32 little-endian upload
      const bgR = (bg >> 16) & 0xff;
      const bgG = (bg >> 8) & 0xff;
      const bgB = bg & 0xff;
      const bgPack = (0xff << 24) | (bgB << 16) | (bgG << 8) | bgR;

      const fgR = (fg >> 16) & 0xff;
      const fgG = (fg >> 8) & 0xff;
      const fgB = fg & 0xff;
      const fgPack = (0xff << 24) | (fgB << 16) | (fgG << 8) | fgR;

      // Layout:
      // f32[ptr + 0] = col
      // f32[ptr + 1] = row
      // u32[ptr + 2] = bgPack
      // u32[ptr + 3] = fgPack
      // f32[ptr + 4] = atlasCol
      // f32[ptr + 5] = atlasRow
      f32[ptr] = col;
      f32[ptr + 1] = row;
      u32[ptr + 2] = bgPack;
      u32[ptr + 3] = fgPack;
      f32[ptr + 4] = atlasCol;
      f32[ptr + 5] = atlasRow;

      ptr += 6;
    }

    // Upload instance buffer to GPU
    gl.bindBuffer(gl.ARRAY_BUFFER, this.instanceBuffer);
    gl.bufferSubData(gl.ARRAY_BUFFER, 0, f32.subarray(0, ptr));

    // Draw
    gl.useProgram(this.program);

    gl.uniform2f(this.u_gridSize, width, height);
    gl.uniform2f(this.u_cellSize, cw, ch);
    gl.uniform2f(this.u_atlasSize, this.atlasWidth, this.atlasHeight);

    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, this.atlasTexture);
    if (this.atlasDirty) {
      gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, gl.RGBA, gl.UNSIGNED_BYTE, this.atlasCanvas);
      this.atlasDirty = false;
    }
    gl.uniform1i(this.u_atlas, 0);

    // Bind Quad Vertex Buffer
    gl.bindBuffer(gl.ARRAY_BUFFER, this.quadBuffer);
    gl.enableVertexAttribArray(this.a_quad);
    gl.vertexAttribPointer(this.a_quad, 2, gl.FLOAT, false, 8, 0);
    this.vertexAttribDivisor(this.a_quad, 0);

    // Bind Instance Buffer
    gl.bindBuffer(gl.ARRAY_BUFFER, this.instanceBuffer);
    const stride = 24;

    gl.enableVertexAttribArray(this.a_cellCoord);
    gl.vertexAttribPointer(this.a_cellCoord, 2, gl.FLOAT, false, stride, 0);
    this.vertexAttribDivisor(this.a_cellCoord, 1);

    gl.enableVertexAttribArray(this.a_bgColor);
    gl.vertexAttribPointer(this.a_bgColor, 4, gl.UNSIGNED_BYTE, true, stride, 8);
    this.vertexAttribDivisor(this.a_bgColor, 1);

    gl.enableVertexAttribArray(this.a_fgColor);
    gl.vertexAttribPointer(this.a_fgColor, 4, gl.UNSIGNED_BYTE, true, stride, 12);
    this.vertexAttribDivisor(this.a_fgColor, 1);

    gl.enableVertexAttribArray(this.a_atlasCoord);
    gl.vertexAttribPointer(this.a_atlasCoord, 2, gl.FLOAT, false, stride, 16);
    this.vertexAttribDivisor(this.a_atlasCoord, 1);

    // Single instanced draw call
    this.drawArraysInstanced(gl.TRIANGLE_STRIP, 0, 4, numCells);
  }
}
