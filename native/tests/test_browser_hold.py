"""Actual Chromium hold owns its scene until explicit demo rotation resumes."""
import os
from pathlib import Path
import unittest
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]

class BrowserHold(unittest.TestCase):
 def test_hold_retains_scene_past_rotation_deadline_and_resume_rotates(self):
  errors=[]
  with sync_playwright()as pw:
   browser=pw.chromium.launch(headless=True,executable_path=os.environ.get('CHROMIUM'))
   page=browser.new_page();page.on('pageerror',lambda error:errors.append(str(error)))
   try:
    page.set_content((ROOT/'Nocturne-Test-Harness.html').read_text());page.wait_for_function('window.nativeLab !== undefined')
    page.locator('#scenes').select_option('silk');page.locator('#attract').click()
    self.assertEqual(page.locator('#attract').get_attribute('aria-pressed'),'true')
    before=page.evaluate("""()=>{nativeLab.hold();window.heldSnapshot=nativeLab.scene.snapshot();const info=nativeLab.scene.info();return {identity:document.querySelector('#scenes').value,clock:info.clock,text:info.prompt.text};}""")
    page.wait_for_timeout(13000)
    after=page.evaluate("""()=>{const s=nativeLab.scene,info=s.info(),snapshot=s.snapshot();return {identity:document.querySelector('#scenes').value,clock:info.clock,text:info.prompt.text,rotation:document.querySelector('#attract').getAttribute('aria-pressed'),unchanged:snapshot.length===heldSnapshot.length&&snapshot.every((v,i)=>v===heldSnapshot[i])};}""")
    self.assertEqual(after['identity'],before['identity'],'held scene was replaced by automatic demo rotation')
    self.assertEqual(after['rotation'],'false');self.assertEqual(after['clock'],before['clock']);self.assertTrue(after['clock']['paused'])
    self.assertEqual(after['text'],before['text']);self.assertTrue(after['unchanged'],'held render changed the native snapshot')
    self.assertEqual(page.locator('#attract').inner_text(),'Resume demos')
    page.locator('#attract').click();self.assertEqual(page.locator('#attract').get_attribute('aria-pressed'),'true')
    page.wait_for_timeout(13000)
    self.assertNotEqual(page.locator('#scenes').input_value(),before['identity'],'explicit Resume demos did not rotate')
    page.evaluate('nativeLab.hold()');self.assertEqual(page.locator('#attract').get_attribute('aria-pressed'),'false')
    self.assertTrue(page.evaluate('nativeLab.scene.info().clock.paused'));self.assertEqual(errors,[])
   finally:browser.close()

if __name__=='__main__':unittest.main(verbosity=2)
