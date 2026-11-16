"""The Gallery's Design panel exposes the hidden-particle look and applies it at once, through the real WASM scene.

Runs the built Gallery (sh build-native.sh) in Chromium. The controls are environment occlusionTint (slider 0..1)
and occludedDots (hidden or merge); there is no Apply button. Each change must reach the engine immediately, draw the
frame the engine draws for that command, and the controls must follow the engine after a scene load or a restore.
"""
import os
import unittest
from pathlib import Path

from playwright.sync_api import sync_playwright

NATIVE = Path(__file__).resolve().parents[1]
GALLERY = Path(os.environ.get('NOCTURNE_OCCLUSION_GALLERY_PATH', NATIVE / 'Nocturne-Test-Harness.html'))

SAME_FRAME_AFTER = """command=>{const s=nativeLab.scene,after=s.render().bytes.slice(),saved=s.snapshot();
 s.restore(window.occlusionBefore);let p;do{p=s.command(command);}while(p===1);const oracle=s.render().bytes.slice();s.restore(saved);
 return after.length===oracle.length&&after.every((v,i)=>v===oracle[i]);}"""
CHANGED = "()=>{const a=nativeLab.scene.render().bytes,b=window.occlusionBeforeFrame;return a.length!==b.length||a.some((v,i)=>v!==b[i]);}"
REMEMBER = "()=>{window.occlusionBefore=nativeLab.scene.snapshot();window.occlusionBeforeFrame=nativeLab.scene.render().bytes.slice();}"


class OcclusionGallery(unittest.TestCase):
    def test_design_panel_controls_apply_immediately_and_follow_the_engine(self):
        if not GALLERY.is_file():
            self.fail(f'build the Gallery first (sh build-native.sh): missing {GALLERY}')
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={'width': 1440, 'height': 900})
                page.set_default_timeout(60000)
                errors = []
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.goto(GALLERY.resolve().as_uri())
                page.wait_for_function('window.nativeLab')
                page.select_option('#scenes', 'autumn')
                page.evaluate('nativeLab.hold()')
                page.evaluate("()=>{const s=nativeLab.scene;s.command({op:'pause',paused:false});while(s.command({op:'time',timeUs:30000000})===1){}s.command({op:'pause',paused:true});nativeLab.draw();}")
                page.locator('#project-panel').evaluate('e=>e.open=true')
                # The controls live in the Design panel and there is nothing to apply.
                self.assertEqual(page.locator('#project-panel > summary').inner_text(), 'Design')
                self.assertEqual(page.locator('#project-panel #occlusion-look').count(), 1)
                self.assertEqual(page.locator('#occlusion-look button').count(), 0)
                self.assertEqual(page.locator('#occlusion-tint').get_attribute('type'), 'range')
                self.assertEqual((page.locator('#occlusion-tint').get_attribute('min'), page.locator('#occlusion-tint').get_attribute('max')), ('0', '1'))
                self.assertEqual(page.locator('#occluded-dots option').evaluate_all('o=>o.map(x=>x.value)'), ['hidden', 'merge'])
                page.locator('#occlusion-tint').scroll_into_view_if_needed()
                self.assertTrue(page.locator('#occlusion-tint').is_visible())
                self.assertEqual(page.locator('#occlusion-tint').input_value(), '1')
                self.assertEqual(page.locator('#occluded-dots').input_value(), 'hidden')

                page.evaluate(REMEMBER)
                page.locator('#occlusion-tint').fill('0.35')
                environment = page.evaluate('nativeLab.scene.info().environment')
                self.assertEqual(environment['occlusionTint'], 0.35)
                self.assertEqual(page.locator('#occlusion-tint-value').inner_text(), '0.35')
                self.assertTrue(page.evaluate(CHANGED), 'the tint did not change the drawn frame')
                self.assertTrue(page.evaluate(SAME_FRAME_AFTER, {'op': 'environment', 'occlusionTint': 0.35}))

                page.evaluate(REMEMBER)
                page.select_option('#occluded-dots', 'merge')
                self.assertEqual(page.evaluate('nativeLab.scene.info().environment.occludedDots'), 'merge')
                self.assertTrue(page.evaluate(CHANGED), 'merge did not change the drawn frame')
                self.assertTrue(page.evaluate(SAME_FRAME_AFTER, {'op': 'environment', 'occludedDots': 'merge'}))
                page.evaluate('()=>{window.occlusionLook=nativeLab.scene.snapshot();}')  # kept in the page: about 30 MB

                # A scene load resets the engine; the controls show the engine's values, not stale ones.
                page.select_option('#scenes', 'snow')
                page.evaluate('nativeLab.hold()')
                page.evaluate('nativeLab.draw()')
                self.assertEqual(page.evaluate('nativeLab.scene.info().environment.occlusionTint'), 1)
                self.assertEqual(page.locator('#occlusion-tint').input_value(), '1')
                self.assertEqual(page.locator('#occluded-dots').input_value(), 'hidden')
                # And a restore brings both back.
                page.evaluate('()=>{nativeLab.scene.restore(window.occlusionLook);nativeLab.draw();}')
                self.assertEqual(page.locator('#occlusion-tint').input_value(), '0.35')
                self.assertEqual(page.locator('#occlusion-tint-value').inner_text(), '0.35')
                self.assertEqual(page.locator('#occluded-dots').input_value(), 'merge')
                self.assertFalse(page.locator('#error').inner_text())
                self.assertEqual(errors, [])
            finally:
                browser.close()


if __name__ == '__main__':
    unittest.main()
