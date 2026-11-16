"""The Gallery's retained Canvas2D paint is pixel-identical to the full pass, in actual Chromium.

draw() repaints only the cells whose words changed since the last painted frame (plus every cell under
a prompt span), merging background runs. For the four pacing scenes and prompt-presentation scenes, at
several times, the canvas a live sequence of incremental frames leaves is read with getImageData and
compared byte for byte with the same frame painted by the unmodified full pass
(nativeLab.paintReference()) and by a forced full repaint of the retained path
(nativeLab.invalidatePaint()). The frame's cells must be the same words under all three paints, so the
comparison is of paint alone; and the incremental frame must have repainted some but not all cells, so
the test cannot pass by comparing two full passes. Transitions are checked the same way: a recipe switch
painted incrementally, and a round trip through WebGL paint.
"""

import os
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
GALLERY_HTML = Path(os.environ.get('NOCTURNE_GALLERY_PATH', ROOT / 'Nocturne-Test-Harness.html'))
PACING_SCENES = ('autumn', 'rain', 'windows', 'text')
FRAMES_PER_CHECK = 10
CHECKS_PER_SCENE = 3
FRAME_US = 1_000_000 // 30

# Paint one frame (advancing the held scene first when asked), then compare the canvas with the same
# frame painted by the reference full pass and by a forced full repaint of the retained path.
COMPARE = r"""async advanceUs=>{
 if(advanceUs)nativeLab.advance(advanceUs);
 nativeLab.draw();
 const lab=nativeLab,c=document.getElementById('canvas'),ctx=c.getContext('2d');
 const perf={...lab.lastPerf()},n=nativeView.frame.width*nativeView.frame.height;
 const words=()=>{const f=nativeView.frame;return {cells:Array.from(f.cells),width:f.width,height:f.height};};
 const pixels=()=>ctx.getImageData(0,0,c.width,c.height).data;
 const incremental=pixels(),incrementalWords=words();
 lab.paintReference();const reference=pixels(),referenceWords=words(),referencePerf={...lab.lastPerf()};
 lab.invalidatePaint();lab.draw();const forced=pixels(),forcedWords=words(),forcedPerf={...lab.lastPerf()};
 const sameWords=(a,b)=>a.width===b.width&&a.height===b.height&&a.cells.length===b.cells.length&&a.cells.every((v,i)=>v===b.cells[i]);
 const diff=(a,b)=>{if(a.length!==b.length)return {bytes:-1};let bytes=0,first=-1;for(let i=0;i<a.length;i++)if(a[i]!==b[i]){bytes++;if(first<0)first=i;}
  return {bytes,first:first<0?null:{x:(first>>2)%c.width,y:Math.floor((first>>2)/c.width)}};};
 let wideColours=0;for(let i=0;i<incrementalWords.cells.length;i+=4)if(incrementalWords.cells[i+1]>0xffffff||incrementalWords.cells[i+2]>0xffffff)wideColours++;
 return {cells:n,painted:perf.paintedCells,full:perf.fullPaint,mode:perf.paintMode,referenceFull:referencePerf.fullPaint,forcedFull:forcedPerf.fullPaint,
  forcedPainted:forcedPerf.paintedCells,sameWords:sameWords(incrementalWords,referenceWords)&&sameWords(incrementalWords,forcedWords),
  wideColours,prompt:(window.nativePromptPaint||[]).length,size:[c.width,c.height],
  incrementalVsReference:diff(incremental,reference),forcedVsReference:diff(forced,reference)};
}"""

LOAD = """id=>{const r=nativeLab.recipes.find(r=>r.id===id);if(!r)throw Error('Missing recipe '+id);nativeLab.load(r);nativeLab.hold();return true;}"""


class TestCanvas2dRetainedPaint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(headless=True, executable_path=os.environ.get('CHROMIUM'))
        cls.page = cls.browser.new_page(viewport={'width': 1600, 'height': 900})
        cls.errors = []
        cls.page.on('pageerror', lambda e: cls.errors.append(str(e)))
        # A file URL is a secure context, which the font upload's crypto.subtle digest needs.
        cls.page.goto(GALLERY_HTML.resolve().as_uri())
        cls.page.wait_for_function('window.nativeLab !== undefined', timeout=300000)
        cls.prompt_scenes = cls.page.evaluate(
            "nativeLab.recipes.filter(r=>r.id.startsWith('prompt-presentation-')).map(r=>r.id).slice(0,2)")

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def assertIdentical(self, result, label, incremental=True):
        self.assertEqual(result['mode'], 'canvas2d', label)
        self.assertTrue(result['sameWords'], f'{label}: the three paints must paint the same cell words')
        self.assertEqual(result['wideColours'], 0, f'{label}: a colour word above 0xffffff has no defined fillStyle')
        self.assertTrue(result['referenceFull'] and result['forcedFull'], label)
        self.assertEqual(result['forcedPainted'], result['cells'], label)
        if incremental:
            self.assertFalse(result['full'], f'{label}: the checked frame must be painted incrementally')
            self.assertGreater(result['painted'], 0, f'{label}: an advanced frame repaints some cells')
            self.assertLess(result['painted'], result['cells'], f'{label}: an incremental frame repaints fewer than all cells')
        self.assertEqual(result['incrementalVsReference']['bytes'], 0, f"{label}: retained paint differs from the full pass {result['incrementalVsReference']}")
        self.assertEqual(result['forcedVsReference']['bytes'], 0, f"{label}: forced full repaint differs from the full pass {result['forcedVsReference']}")

    def run_scene(self, scene):
        self.page.evaluate(LOAD, scene)
        self.page.evaluate("nativeLab.setPaintMode('canvas2d');nativeLab.draw()")
        results = []
        for check in range(CHECKS_PER_SCENE):
            for _ in range(FRAMES_PER_CHECK - 1):
                self.page.evaluate("us=>{nativeLab.advance(us);nativeLab.draw();}", FRAME_US)
            result = self.page.evaluate(COMPARE, FRAME_US)
            self.assertIdentical(result, f'{scene} check {check + 1}')
            results.append(result)
        return results

    def test_pacing_scenes_paint_identically(self):
        for scene in PACING_SCENES:
            with self.subTest(scene=scene):
                results = self.run_scene(scene)
                print(f"{scene}: painted {[r['painted'] for r in results]} of {results[0]['cells']} cells; 0 differing bytes")
        self.assertEqual(self.errors, [])

    def test_prompt_scenes_paint_identically(self):
        self.assertTrue(self.prompt_scenes, 'prompt-presentation recipes are present')
        painted_prompt = 0
        for scene in self.prompt_scenes:
            with self.subTest(scene=scene):
                results = self.run_scene(scene)
                painted_prompt += sum(r['prompt'] for r in results)
                print(f"{scene}: painted {[r['painted'] for r in results]} of {results[0]['cells']} cells, prompt spans {[r['prompt'] for r in results]}; 0 differing bytes")
        self.assertGreater(painted_prompt, 0, 'the prompt scenes paint prompt span text')
        self.assertEqual(self.errors, [])

    def test_recipe_switch_and_webgl_round_trip_paint_identically(self):
        self.run_scene('rain')
        # A recipe switch with no invalidation: the next frame is painted from the previous recipe's cells.
        self.page.evaluate(LOAD, 'windows')
        switched = self.page.evaluate(COMPARE, FRAME_US)
        self.assertIdentical(switched, 'switch rain -> windows')
        # canvas2d -> webgl -> canvas2d: frames painted by WebGL never reach the 2D canvas, so the return repaints in full.
        first = self.page.evaluate("us=>{nativeLab.setPaintMode('webgl');for(let i=0;i<5;i++){nativeLab.advance(us);nativeLab.draw();}nativeLab.setPaintMode('canvas2d');return nativeLab.lastPerf();}", FRAME_US)
        self.assertEqual((first['paintMode'], first['fullPaint']), ('canvas2d', True), 'the first canvas2d frame after WebGL is a full repaint')
        returned = self.page.evaluate(COMPARE, FRAME_US)
        self.assertIdentical(returned, 'after webgl round trip')
        self.assertEqual(self.errors, [])

    def test_resize_repaints_in_full_and_identically(self):
        self.run_scene('autumn')
        first = self.page.evaluate("""()=>{document.getElementById('columns').value='120';document.getElementById('rows').value='40';
          document.getElementById('resize').click();return {...nativeLab.lastPerf(),width:nativeView.frame.width,height:nativeView.frame.height};}""")
        self.assertEqual((first['width'], first['height']), (120, 40), 'the resize reached the scene')
        # act() repaints synchronously after the resize command, so lastPerf is the first frame at the new size.
        self.assertEqual((first['paintMode'], first['fullPaint']), ('canvas2d', True), 'the first frame at a new size is a full repaint')
        for _ in range(FRAMES_PER_CHECK - 1):
            self.page.evaluate("us=>{nativeLab.advance(us);nativeLab.draw();}", FRAME_US)
        self.assertIdentical(self.page.evaluate(COMPARE, FRAME_US), 'after resize to 120x40')
        self.page.evaluate("()=>{document.getElementById('columns').value='160';document.getElementById('rows').value='48';document.getElementById('resize').click();nativeLab.draw();}")
        self.assertEqual(self.errors, [])

    def test_font_change_repaints_identically(self):
        fonts = [Path(os.environ[name]) for name in ('NOCTURNE_SHAPING_FONT', 'NOCTURNE_OTF_FONT') if os.environ.get(name)]
        if not fonts:
            self.skipTest('NOCTURNE_SHAPING_FONT is not provisioned on this host')
        import hashlib
        self.run_scene('text')
        self.page.locator('#typography').evaluate('(e)=>e.open=true')
        for font in fonts:
            with self.subTest(font=font.name):
                self.page.locator('#font-file').set_input_files(str(font))
                self.page.wait_for_function('(sha)=>document.getElementById("font-status").dataset.sha256===sha', arg=hashlib.sha256(font.read_bytes()).hexdigest())
                self.assertIn('NocturneUploadedFont_', self.page.evaluate('document.getElementById("canvas").getContext("2d").font'))
                for _ in range(FRAMES_PER_CHECK - 1):
                    self.page.evaluate("us=>{nativeLab.advance(us);nativeLab.draw();}", FRAME_US)
                self.assertIdentical(self.page.evaluate(COMPARE, FRAME_US), f'after loading {font.name}')
        self.page.locator('#font-default').click()
        for _ in range(FRAMES_PER_CHECK - 1):
            self.page.evaluate("us=>{nativeLab.advance(us);nativeLab.draw();}", FRAME_US)
        self.assertIdentical(self.page.evaluate(COMPARE, FRAME_US), 'after restoring the default font')
        self.assertEqual(self.errors, [])


if __name__ == '__main__':
    unittest.main()
