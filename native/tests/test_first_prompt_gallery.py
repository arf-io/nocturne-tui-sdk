"""Normal browser routes use original prompt cells and current immediate input."""
import os,json,unittest
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class FirstPromptGallery(unittest.TestCase):
 def test_original_presets_cursor_and_current_draft_are_public_controls(self):
  with sync_playwright()as pw:
   browser=pw.chromium.launch(headless=True,executable_path=os.environ.get('CHROMIUM'));page=browser.new_page(viewport={'width':1440,'height':900});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.set_content(Path(os.environ.get('NOCTURNE_FIRST_GALLERY_PATH',ROOT/'Nocturne-RC4-Source-Build.html')).read_text());page.wait_for_function('window.nativeLab');page.evaluate('nativeLab.hold()')
   expected=json.loads((ROOT/'tests/fixtures/first-prompt-v01/presets.json').read_text())
   # All sixteen v0.1 surfaces, layouts 0-4.
   self.assertEqual(len(expected),16);self.assertEqual(page.locator('#first-prompt-style option[data-source-preset]').count(),len(expected))
   page.locator('#draft').fill('Immediate e\u0301 🪶 input');page.locator('#draft').dispatch_event('input')
   for preset in expected:
    page.locator('#first-prompt-style').select_option('first-prompt-'+preset['id']);info=page.evaluate('nativeLab.scene.info()');self.assertEqual(info['prompt']['text'],'Immediate e\u0301 🪶 input');self.assertEqual(info['prompt']['firstPromptSource']['values'][2:4],[preset['values']['effect'],preset['values']['layout']]);self.assertEqual(page.evaluate('nativeLab.scene.promptVisualLayout()'),[])
   for cursor in range(4):
    page.locator('#first-prompt-cursor').select_option(str(cursor));self.assertEqual(page.evaluate('nativeLab.scene.info().prompt.firstPromptSource.values[32]'),cursor)
   self.assertTrue(page.evaluate('()=>{const before=nativeLab.scene.snapshot();nativeLab.draw();const after=nativeLab.scene.snapshot();return before.length===after.length&&before.every((x,i)=>x===after[i]);}'))
   page.locator('#first-prompt-style').select_option('');self.assertIsNone(page.evaluate('nativeLab.scene.info().prompt.firstPromptSource'));self.assertEqual(page.locator('#draft').input_value(),'Immediate e\u0301 🪶 input');self.assertFalse(errors);browser.close()
if __name__=='__main__':unittest.main()
