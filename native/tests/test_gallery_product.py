"""The shipped Gallery (native/Nocturne-RC4-Source-Build.html) shows only admitted artwork.

The test harness (Nocturne-Test-Harness.html) runs every study for the browser checks; this test is about the page
users receive. In a real browser it requires that the picker library and the attract rotation hold exactly the
admission ledger's artwork (after nullification), that no excluded entry is reachable by deep link, that the
Workshop panels open their labelled SDK examples without error, and that the harness is not the shipped page.
"""
import importlib.util
import json
import os
import re
import sys
import unittest
from pathlib import Path

NATIVE = Path(__file__).resolve().parents[1]
GALLERY = NATIVE / 'Nocturne-RC4-Source-Build.html'
sys.path.insert(0, str(NATIVE / 'scripts'))
_spec = importlib.util.spec_from_file_location('gallery_nullification', Path(__file__).resolve().with_name('gallery_nullification.py'))
gallery_nullification = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gallery_nullification)
PRIVATE = NATIVE.parent / 'tools/release/private_strings.json'
PANELS = {'anatomy-open': 'leaf-anatomy', 'mixed-open': 'mixed-materials', 'condition-open': 'condition-console',
          'selector-open': 'selector-studio', 'plot-open': 'pearl-curves', 'notifications-load': 'notifications'}


@unittest.skipUnless(GALLERY.is_file(), 'build the Gallery first (sh build-native.sh)')
class ShippedGallery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        import gallery_provenance
        cls.ledger = gallery_provenance.read_ledger()
        library, struck = gallery_nullification.committed(NATIVE)
        cls.expected = [r['id'] for r in library if r['id'] not in struck] if library is not None else gallery_provenance.admitted_ids()
        cls.excluded = sorted(struck)
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(headless=True, executable_path=os.environ.get('CHROMIUM') or None)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def open(self, hash_='', ready='window.nativeLab'):
        page = self.browser.new_page(viewport={'width': 1500, 'height': 1000})
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        self.addCleanup(page.close)
        page.goto(GALLERY.as_uri() + hash_)
        page.wait_for_function(ready, timeout=120000)
        return page, errors

    def test_library_and_attract_hold_only_admitted_artwork(self):
        page, errors = self.open()
        ids = page.evaluate('nativeLab.recipes.map(r=>r.id)')
        self.assertEqual(ids, self.expected)
        self.assertLess(len(ids), 1000, 'the shipped Gallery must not carry the test harness library')
        attract = page.evaluate('nativeLab.demoRecipes.map(r=>r.id)')
        self.assertTrue(attract)
        self.assertLessEqual(set(attract), set(ids))
        invented = page.evaluate("""nativeLab.recipes.filter(r=>(r.commands||[]).some(c=>c.op==='mesh'&&(c.triangles||[]).length&&
            c.triangles.every(t=>t.color===0x42b8bc||t.color===0xc586e1))).map(r=>r.id)""")
        self.assertEqual(invented, [], 'the shipped Gallery shows the invented placeholder mesh')
        self.assertFalse([i for i in ids if i.startswith('original-tdf-')], 'the wordmark specimens are withheld')
        options = page.evaluate("[...document.querySelectorAll('#scenes option')].map(o=>o.value).filter(Boolean)")
        self.assertFalse(set(options) & set(self.excluded), 'an excluded entry is offered by the picker')
        self.assertEqual(errors, [])

    @unittest.skipUnless(PRIVATE.is_file(), 'tools/release/private_strings.json is private-only and is not in the public tree; the export scans for it')
    def test_the_shipped_library_names_nothing_private(self):
        # The library as the page serves it (ids, names, subtitles, commands), not the page's embedded binaries, where a short
        # pattern matches base64 by chance.
        page, errors = self.open()
        library = json.dumps(page.evaluate('nativeLab.recipes'), ensure_ascii=False)
        pattern = re.compile(json.loads(PRIVATE.read_text())['pattern'], re.I)
        self.assertEqual(sorted({m.group(0) for m in pattern.finditer(library)}), [], 'a shipped recipe names something private')
        self.assertEqual(errors, [])

    def test_excluded_entries_are_not_reachable_by_deep_link(self):
        # A link to an entry the Gallery does not ship is refused with a visible error; nothing is loaded.
        # A fixture entry too, in the source repository; the public tree leaves the fixture entries out, so it has none to name.
        fixture = next((i for i in self.excluded if i.startswith('resource-ownership-')), None)
        for ident in ('no-such-recipe', 'rain', *([fixture] if fixture else [])):
            with self.subTest(ident):
                page, errors = self.open('#scene=' + ident, ready="document.querySelector('#error')?.textContent.length>0")
                self.assertTrue(errors, 'the page did not refuse the link')
                self.assertFalse(page.evaluate('Boolean(window.nativeLab)'))
                self.assertNotEqual(page.evaluate("document.querySelector('#scenes').value"), ident)
        page, errors = self.open('#scene=' + self.expected[0])
        self.assertEqual(errors, [])

    def test_workshop_examples_are_labelled_and_open_from_their_panels(self):
        page, errors = self.open()
        examples = page.evaluate('nativeLab.examples.map(r=>r.id)')
        self.assertTrue(set(examples) <= set(self.ledger['workshopExamples']['ids']))
        self.assertFalse(set(examples) & set(page.evaluate('nativeLab.recipes.map(r=>r.id)')))
        for button, ident in PANELS.items():
            with self.subTest(button):
                page.evaluate("id=>{const e=document.getElementById(id);let d=e.closest('details');while(d){d.open=true;d=d.parentElement.closest('details');}}", button)
                page.locator('#' + button).click()
                self.assertEqual(page.locator('#error').inner_text(), '', f'{button} reported an error')
                self.assertTrue(page.evaluate('id=>nativeLab.example(id)!==undefined', ident))
        self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
