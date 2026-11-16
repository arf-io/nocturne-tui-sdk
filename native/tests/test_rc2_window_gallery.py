"""Recovered RC2 windows must reach the actual gallery and shared WASM core."""
import json
from contextlib import contextmanager
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
sys.path.insert(0, str(ROOT / 'examples'))


class RC2WindowGallery(unittest.TestCase):
    def test_complete_source_effects_have_owned_isolated_and_application_recipes(self):
        from rc2_window_studies import build_rc2_window_studies
        from gallery_cases import build_cases
        source = json.loads((ROOT / 'examples/rc2_window_presets.json').read_text())
        cases = build_rc2_window_studies()
        self.assertEqual(len(source['effects']), 21)
        self.assertEqual(len(cases), 46)
        expected = {f'rc2-{name}-{mode}' for name in ['windows', 'shapes'] +
                    ['window-' + effect for effect in source['effects']]
                    for mode in ('isolated', 'application')}
        self.assertEqual({case['id'] for case in cases}, expected)
        catalogue = {case['id']: case for case in build_cases()}
        self.assertEqual({identity: catalogue[identity] for identity in expected},
                         {case['id']: case for case in cases})
        for case in cases:
            contents = [c for c in case['commands'] if c['op'] == 'window-content']
            self.assertEqual([c['label'] for c in contents], ['pearl', 'atlas', 'iris'])
            self.assertEqual([c['sourceIndex'] for c in contents], [0, 1, 2])
            self.assertEqual([c['text'] for c in contents],
                             [w['content'] for w in source['scenes'][case['originalScene']]['windows']])
            self.assertEqual(case['provenance']['htmlSha256'], source['source']['htmlSha256'])
            self.assertEqual(case['provenance']['release'], '0.9.0-rc.2')
            if case.get('originalEffect'):
                self.assertEqual([a['timeUs'] for a in case['actions']], [1000000, 3000000])
                self.assertEqual([a['command']['action'] for a in case['actions']], ['minimize', 'restore'])
        demos = [case for case in cases if case['demo']]
        self.assertEqual([case['id'] for case in demos],
                         ['rc2-windows-application', 'rc2-shapes-application'])
        for case in demos:
            self.assertEqual([c for c in case['commands'] if c['op'] == 'window-application'],
                             [{'op':'window-application', 'paletteWindowId':1, 'scene':case['originalScene']}])
        cases[0]['commands'].clear()
        self.assertTrue(build_rc2_window_studies()[0]['commands'])

    @contextmanager
    def open_gallery(self, playwright, *, reduced_motion='reduce'):
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={'width':1280,'height':900}, reduced_motion=reduced_motion)
            path = Path(os.environ.get('NOCTURNE_RC2_GALLERY_PATH', ROOT / 'Nocturne-RC4-Source-Build.html'))
            self.assertTrue(path.is_file(), 'Build the aligned gallery once before this test group')
            page.goto(path.resolve().as_uri() + '#scene=rc2-windows-isolated&timeUs=0')
            page.wait_for_function('window.nativeLab !== undefined')
            yield page
        finally:
            browser.close()

    def test_real_wasm_menu_preserves_original_documents_provenance_and_stage(self):
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p, self.open_gallery(p) as page:
            errors = []; page.on('pageerror', lambda error: errors.append(str(error)))
            entries = page.locator('#scenes option').evaluate_all('(items)=>items.map(i=>i.value)')
            self.assertEqual(sum(s.startswith('rc2-') for s in entries), 46)
            self.assertEqual(page.evaluate('nativeLab.demoRecipes.filter(r=>r.id.startsWith("rc2-")).map(r=>r.id)'),
                             ['rc2-windows-application', 'rc2-shapes-application'])
            for identity in ('rc2-windows-isolated', 'rc2-shapes-isolated', 'rc2-window-genie-isolated',
                             'rc2-windows-application', 'rc2-shapes-application'):
                page.select_option('#scenes', identity)
                page.evaluate('nativeLab.hold();nativeLab.draw()')
                info = page.evaluate('nativeLab.scene.infoComplete()')
                if identity.endswith('-application'):
                    self.assertEqual(info['windowApplication']['scene'], identity.split('-')[1])
                    self.assertEqual(info['windowApplication']['paletteWindowId'], 1)
                else:
                    self.assertIsNone(info['windowApplication'])
                self.assertEqual(page.locator('#columns').input_value(), '136')
                self.assertEqual(page.locator('#rows').input_value(), '44')
                self.assertEqual(page.evaluate('nativeLab.scene.render().width'), 136)
                self.assertEqual(page.evaluate('nativeLab.scene.render().height'), 44)
                self.assertEqual([w['content']['label'] for w in info['windows']], ['pearl','atlas','iris'])
                self.assertIn('SIGNAL IS A MATERIAL', info['windows'][0]['text'])
                self.assertIn('TOPOLOGY WITHOUT DUPLICATES', info['windows'][1]['text'])
                self.assertIn('OPEN / CLOSE / TRANSFORM', info['windows'][2]['text'])
                self.assertIn('0.9.0-rc.2', page.locator('#demo-provenance').inner_text())
                self.assertIn(identity, page.locator('#demo-provenance').inner_text())
                self.assertTrue(page.evaluate('(()=>{const a=nativeLab.scene.snapshot();nativeLab.draw();const b=nativeLab.scene.snapshot();return a.length===b.length&&a.every((v,i)=>v===b[i]);})()'))
                self.assertEqual(page.locator('#attract').get_attribute('aria-pressed'), 'false')
                for width,height in [(1280,900),(390,844),(1440,500)]:
                    page.set_viewport_size({'width':width,'height':height})
                    bounds = page.locator('.stage').bounding_box()
                    self.assertGreaterEqual(bounds['y'], 0)
                    self.assertLessEqual(bounds['y'] + bounds['height'], height + 1)
                    self.assertFalse(page.evaluate('document.documentElement.scrollWidth>innerWidth'))
            self.assertEqual(errors, [])

    def test_original_effect_actions_and_local_draft_survive_recipe_switch(self):
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p, self.open_gallery(p, reduced_motion='no-preference') as page:
            page.select_option('#scenes','rc2-window-genie-application')
            page.evaluate('nativeLab.hold();nativeLab.scene.command({op:"draft",text:"Local retained draft",emitWeather:false});nativeLab.draw()')
            page.evaluate('nativeLab.advance(1425000);nativeLab.draw()')
            rows = page.evaluate('nativeLab.scene.infoComplete().windows')
            self.assertAlmostEqual(rows[0]['content']['visibility'], .5, places=6)
            self.assertTrue(all(w['content']['visibility']==1 for w in rows[1:]))
            page.evaluate('nativeLab.advance(2425000);nativeLab.draw()')
            self.assertEqual(page.evaluate('nativeLab.scene.infoComplete().windows[0].content.visibility'), 1)
            page.select_option('#scenes','rc2-shapes-application')
            page.evaluate('nativeLab.hold();nativeLab.draw()')
            self.assertEqual(page.evaluate('nativeLab.scene.infoComplete().prompt.text'),'Local retained draft')
            self.assertEqual(page.locator('#attract').get_attribute('aria-pressed'), 'false')
            page.locator('#scenes').focus();page.keyboard.press('ArrowDown');page.keyboard.press('Enter')
            self.assertEqual(page.evaluate('scrollY'), 0)


if __name__ == '__main__':
    unittest.main()
