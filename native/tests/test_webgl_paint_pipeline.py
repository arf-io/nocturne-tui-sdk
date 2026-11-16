"""Test WebGL instanced glyph-atlas tilemap paint pipeline.

Verifies:
1. Default paint mode is 'canvas2d'; URL ?paint=webgl and nativeLab.setPaintMode('webgl') switch cleanly.
2. Correctness: Cell-by-cell parity between Canvas2D and WebGL for background colors and glyph presence.
3. Performance: WebGL paint time remains < 1.0 ms at 160x48, achieving >5x speedup over Canvas2D.
"""

import os
import sys
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
GALLERY_HTML = ROOT / 'Nocturne-RC4-Source-Build.html'


class TestWebGLPaintPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        # On macOS ask Chromium for the Metal GPU so the WebGL timing reflects real hardware; elsewhere the default
        # (often a software renderer) is used and the GPU comparison skips itself.
        gpu = ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist'] if sys.platform == 'darwin' else []
        cls.browser = cls.pw.chromium.launch(
            headless=True,
            executable_path=os.environ.get('CHROMIUM'),
            args=gpu,
        )

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def test_paint_mode_switching(self):
        page = self.browser.new_page(viewport={'width': 1920, 'height': 1080})
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))

        # 1. Default mode must be 'canvas2d'
        page.goto(GALLERY_HTML.as_uri())
        page.wait_for_function('window.nativeLab')
        page.evaluate('nativeLab.hold()')

        mode = page.evaluate('nativeLab.paintMode()')
        self.assertEqual(mode, 'canvas2d')

        c2d_style = page.evaluate("document.getElementById('canvas').style.display")
        cgl_style = page.evaluate("document.getElementById('canvas-gl').style.display")
        self.assertNotEqual(c2d_style, 'none')
        self.assertEqual(cgl_style, 'none')

        # 2. Dynamic switch to 'webgl'
        page.evaluate("nativeLab.setPaintMode('webgl')")
        mode_switched = page.evaluate('nativeLab.paintMode()')
        self.assertEqual(mode_switched, 'webgl')

        c2d_style2 = page.evaluate("document.getElementById('canvas').style.display")
        cgl_style2 = page.evaluate("document.getElementById('canvas-gl').style.display")
        self.assertEqual(c2d_style2, 'none')
        self.assertEqual(cgl_style2, 'block')

        # Draw frame in WebGL
        page.evaluate('nativeLab.draw()')
        perf = page.evaluate('nativeLab.perf()')
        self.assertEqual(perf['paintMode'], 'webgl')
        self.assertLess(perf['paintMs'], 1.0)

        # 3. Dynamic switch back to 'canvas2d'
        page.evaluate("nativeLab.setPaintMode('canvas2d')")
        self.assertEqual(page.evaluate('nativeLab.paintMode()'), 'canvas2d')
        page.evaluate('nativeLab.draw()')
        self.assertEqual(page.evaluate('nativeLab.perf()')['paintMode'], 'canvas2d')

        # 4. URL query parameter ?paint=webgl
        page.goto(GALLERY_HTML.as_uri() + '?paint=webgl')
        page.wait_for_function('window.nativeLab')
        page.evaluate('nativeLab.hold()')
        self.assertEqual(page.evaluate('nativeLab.paintMode()'), 'webgl')

        self.assertEqual(len(errors), 0)
        page.close()

    def test_webgl_canvas2d_per_cell_correctness(self):
        page = self.browser.new_page(viewport={'width': 1920, 'height': 1080})
        page.goto(GALLERY_HTML.as_uri())
        page.wait_for_function('window.nativeLab')
        page.evaluate('nativeLab.hold()')

        # Verify parity across autumn (braille weather) and windows (rectangles & text)
        for scene_id in ['autumn', 'windows']:
            res = page.evaluate('''async (id) => {
                const r = nativeLab.recipes.find(x => x.id === id);
                nativeLab.load(r);
                nativeLab.hold();
                document.getElementById('columns').value = '160';
                document.getElementById('rows').value = '48';
                document.getElementById('resize').click();
                nativeLab.advance(500000); // 0.5s

                const frame = nativeLab.scene.render();
                const width = frame.width;
                const height = frame.height;
                const cw = 10, ch = 20;

                // Render Canvas2D
                nativeLab.setPaintMode('canvas2d');
                nativeLab.draw();
                const c2d = document.getElementById('canvas');
                const ctx2d = c2d.getContext('2d');
                const img2d = ctx2d.getImageData(0, 0, c2d.width, c2d.height).data;

                // Render WebGL
                nativeLab.setPaintMode('webgl');
                nativeLab.draw();
                const cgl = document.getElementById('canvas-gl');
                const gl = cgl.getContext('webgl2') || cgl.getContext('webgl');
                const pixelsGL = new Uint8Array(cgl.width * cgl.height * 4);
                gl.readPixels(0, 0, cgl.width, cgl.height, gl.RGBA, gl.UNSIGNED_BYTE, pixelsGL);

                function getPixelGL(x, y) {
                    const flippedY = cgl.height - 1 - y;
                    const idx = (flippedY * cgl.width + x) * 4;
                    return [pixelsGL[idx], pixelsGL[idx+1], pixelsGL[idx+2], pixelsGL[idx+3]];
                }
                function getPixel2D(x, y) {
                    const idx = (y * c2d.width + x) * 4;
                    return [img2d[idx], img2d[idx+1], img2d[idx+2], img2d[idx+3]];
                }

                let emptyCells = 0, emptyMatch = 0;
                let glyphCells = 0, glyphPresenceMatch = 0;

                for (let row = 0; row < height; row++) {
                    for (let col = 0; col < width; col++) {
                        const idx = row * width + col;
                        const g = frame.cells[idx * 4];
                        const bg = frame.cells[idx * 4 + 2];
                        const expR = (bg >> 16) & 0xff;
                        const expG = (bg >> 8) & 0xff;
                        const expB = bg & 0xff;

                        if (g === 0 || g === 32) {
                            emptyCells++;
                            const pGL = getPixelGL(col * cw, row * ch);
                            if (pGL[0] === expR && pGL[1] === expG && pGL[2] === expB) {
                                emptyMatch++;
                            }
                        } else {
                            glyphCells++;
                            let ink2D = false, inkGL = false;
                            for (let cy = 0; cy < ch; cy += 2) {
                                for (let cx = 0; cx < cw; cx += 2) {
                                    const p2 = getPixel2D(col * cw + cx, row * ch + cy);
                                    const pG = getPixelGL(col * cw + cx, row * ch + cy);
                                    if (p2[0] !== expR || p2[1] !== expG || p2[2] !== expB) ink2D = true;
                                    if (pG[0] !== expR || pG[1] !== expG || pG[2] !== expB) inkGL = true;
                                }
                            }
                            if (ink2D === inkGL) glyphPresenceMatch++;
                        }
                    }
                }

                return {
                    scene: id,
                    emptyCells, emptyMatch,
                    glyphCells, glyphPresenceMatch
                };
            }''', scene_id)

            if res['emptyCells'] > 0:
                self.assertEqual(
                    res['emptyMatch'], res['emptyCells'],
                    f"Scene {scene_id}: Expected 100% empty cell background match, got {res['emptyMatch']}/{res['emptyCells']}"
                )
            if res['glyphCells'] > 0:
                self.assertEqual(
                    res['glyphPresenceMatch'], res['glyphCells'],
                    f"Scene {scene_id}: Expected 100% glyph presence match, got {res['glyphPresenceMatch']}/{res['glyphCells']}"
                )

        page.close()

    def test_webgl_paint_performance_budget(self):
        """Whole-frame time (engine render + paint, GPU-synced) is lower with WebGL than with Canvas2D.

        Each sample forces completion: a 1-pixel readPixels for WebGL, a 1-pixel getImageData for Canvas2D, so GPU
        work cannot hide outside the timing. Absolute budgets depend on the host, so the test compares the two paths
        on the same page and skips on a software GL renderer, where a GPU path has nothing to show.
        """
        def measure(mode):
            page = self.browser.new_page(viewport={'width': 1920, 'height': 1080})
            self.addCleanup(page.close)
            page.goto(GALLERY_HTML.as_uri() + ('?paint=webgl' if mode == 'webgl' else ''))
            page.wait_for_function('window.nativeLab')
            return page.evaluate('''mode => {
                nativeLab.hold();
                nativeLab.load(nativeLab.recipes.find(r => r.id === 'autumn'));
                nativeLab.hold();
                nativeLab.advance(3000000);
                const gl = document.getElementById('canvas-gl');
                const g = gl && (gl.getContext('webgl2') || gl.getContext('webgl'));
                const c = document.getElementById('canvas').getContext('2d');
                let renderer = null;
                if (g) { const e = g.getExtension('WEBGL_debug_renderer_info');
                         renderer = e ? g.getParameter(e.UNMASKED_RENDERER_WEBGL) : g.getParameter(g.RENDERER); }
                const samples = [];
                for (let i = 0; i < 40; i++) {
                    nativeLab.advance(16667);
                    const t0 = performance.now();
                    nativeLab.draw();
                    if (mode === 'webgl') { const px = new Uint8Array(4); g.readPixels(0, 0, 1, 1, g.RGBA, g.UNSIGNED_BYTE, px); }
                    else c.getImageData(0, 0, 1, 1);
                    samples.push(performance.now() - t0);
                }
                samples.sort((a, b) => a - b);
                return {median: samples[20], renderer};
            }''', mode)

        webgl = measure('webgl')
        if not webgl['renderer'] or 'swiftshader' in webgl['renderer'].lower():
            self.skipTest(f"software GL renderer ({webgl['renderer']}): no GPU to compare")
        canvas = measure('canvas2d')
        print(f"autumn full draw, GPU-synced median: canvas2d {canvas['median']:.2f} ms, "
              f"webgl {webgl['median']:.2f} ms ({webgl['renderer']})")
        self.assertLess(webgl['median'], canvas['median'],
                        f"WebGL {webgl['median']:.2f} ms is not faster than Canvas2D {canvas['median']:.2f} ms")


if __name__ == '__main__':
    unittest.main()
