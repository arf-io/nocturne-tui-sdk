from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]

class ManualSite(unittest.TestCase):
    def testActualWasmNavigationSourceAndNarrowViewport(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/'manual.html'
            subprocess.run([sys.executable,str(ROOT/'native/scripts/build_manual_site.py'),'--output',str(output)],cwd=ROOT,check=True,capture_output=True)
            with sync_playwright() as pw:
                browser=pw.chromium.launch();page=browser.new_page();errors=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto(output.as_uri());page.wait_for_function('window.manualSite?.ready')
                self.assertGreater(page.evaluate('manualSite.scene.info().widgets.length'),4)
                self.assertEqual(page.evaluate('manualSite.chapter.source'),page.locator('#source').text_content())
                self.assertTrue(page.evaluate('manualSite.scene.render().bytes.some(value=>value!==0)'))
                painted=page.evaluate('Array.from(manualSite.scene.render().cells).filter((_,i)=>i%4===0).map(x=>String.fromCodePoint(x)).join("")')
                self.assertIn('NOCTURNE SDK',painted)
                self.assertGreater(page.evaluate('manualSite.links.length'),0)
                link=page.evaluate('manualSite.visibleLinks[0]')
                page.locator('canvas').click(position={'x':link['x'],'y':link['y']})
                page.wait_for_function('id=>manualSite.chapter.id===id',arg=link['id'])
                self.assertEqual(page.evaluate('manualSite.page'),0)
                page.keyboard.press('PageDown');self.assertEqual(page.evaluate('manualSite.page'),1)
                page.keyboard.press('Home');self.assertEqual(page.evaluate('manualSite.page'),0)
                page.evaluate('location.hash="readme"');page.wait_for_function('manualSite.chapter.id === "readme"')
                first=page.evaluate('manualSite.chapter.id');page.keyboard.press('ArrowRight')
                self.assertNotEqual(page.evaluate('manualSite.chapter.id'),first)
                region=page.evaluate('manualSite.regions.nextPage')
                page.locator('canvas').click(position={'x':region['x'],'y':region['y']})
                self.assertEqual(page.evaluate('manualSite.page'),1)
                page.evaluate('location.hash="readme"')
                page.wait_for_function('manualSite.chapter.id === "readme"')
                self.assertEqual(page.evaluate('manualSite.page'),0)
                self.assertEqual(page.evaluate('manualSite.runtimeVerified'),True)
                page.keyboard.press('Home');page.wait_for_function('manualSite.chapter.id === "contents"')
                self.assertGreater(page.evaluate('manualSite.links.length'),16)
                self.assertEqual(page.evaluate('manualSite.page'),0)
                page.get_by_role('button',name='Contents',exact=True).focus()
                self.assertTrue(page.evaluate('manualSite.scene.info().widgets.find(w=>w.id===8).selected'))
                anchor=page.locator('#references a').first;label=anchor.text_content();anchor.focus()
                self.assertEqual(page.evaluate('document.activeElement.textContent'),label)
                self.assertIn(label,page.evaluate('manualSite.scene.info().widgets.find(w=>w.id===9).text'))
                self.assertIn('Link: ',page.evaluate('Array.from(manualSite.scene.render().cells).filter((_,i)=>i%4===0).map(x=>String.fromCodePoint(x)).join("")'))
                page.set_viewport_size({'width':390,'height':844});page.emulate_media(reduced_motion='reduce')
                page.wait_for_function('manualSite.columns < 60')
                self.assertLessEqual(page.locator('canvas').bounding_box()['width'],390)
                page.evaluate('location.hash="missing-chapter"');page.wait_for_function('manualSite.error !== null')
                self.assertIn('Unknown chapter',page.locator('#status').text_content())
                self.assertEqual(errors,[]);browser.close()
    def testBuilderRefusesOverwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/'manual.html';output.write_text('preserve')
            r=subprocess.run([sys.executable,str(ROOT/'native/scripts/build_manual_site.py'),'--output',str(output)],cwd=ROOT,capture_output=True)
            self.assertNotEqual(r.returncode,0);self.assertEqual(output.read_text(),'preserve')
    def testEveryBundledChapterHasVerifiedSourceAndRealNativeFirstPage(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/'manual.html'
            subprocess.run([sys.executable,str(ROOT/'native/scripts/build_manual_site.py'),'--output',str(output)],cwd=ROOT,check=True,capture_output=True)
            with sync_playwright() as pw:
                browser=pw.chromium.launch();page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto(output.as_uri());page.wait_for_function('manualSite.ready')
                result=page.evaluate('''async()=>{
                  const rows=[];
                  for(const chapter of data.chapters){
                    location.hash=chapter.id;await new Promise(resolve=>setTimeout(resolve,0));
                    const native=manualSite.scene.info().widgets.find(w=>w.id===6),frame=manualSite.scene.render();
                    rows.push({id:chapter.id,adopted:manualSite.chapter.id===chapter.id,
                      owned:native.text===manualSite.body,accessible:document.querySelector('#source').textContent===chapter.source,
                      frame:frame.bytes.length===frame.width*frame.height*16});
                  }
                  return {verified:manualSite.contentVerified,expected:data.chapters.length,rows};
                }''')
                self.assertTrue(result['verified']);self.assertEqual(len(result['rows']),result['expected'])
                self.assertTrue(all(all(row[k] for k in ['adopted','owned','accessible','frame']) for row in result['rows']),result)
                self.assertEqual(errors,[]);browser.close()
    def testAlteredChapterIdentityFailsBeforeReady(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/'manual.html'
            subprocess.run([sys.executable,str(ROOT/'native/scripts/build_manual_site.py'),'--output',str(output)],cwd=ROOT,check=True,capture_output=True)
            import re
            output.write_text(re.sub(r'"sha256": "[a-f0-9]{64}"','"sha256": "'+('0'*64)+'"',output.read_text(),count=1))
            with sync_playwright() as pw:
                browser=pw.chromium.launch();page=browser.new_page();page.goto(output.as_uri());page.wait_for_function('manualSite.error !== null')
                self.assertIn('chapter identity',page.locator('#status').text_content());self.assertFalse(page.evaluate('manualSite.ready'));browser.close()
    def testAlteredRuntimeIdentityFailsExplicitly(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/'manual.html'
            subprocess.run([sys.executable,str(ROOT/'native/scripts/build_manual_site.py'),'--output',str(output)],cwd=ROOT,check=True,capture_output=True)
            import re
            source=output.read_text();source=re.sub(r'"wasmSha256": "[a-f0-9]{64}"','"wasmSha256": "'+('0'*64)+'"',source)
            output.write_text(source)
            with sync_playwright() as pw:
                browser=pw.chromium.launch();page=browser.new_page();page.goto(output.as_uri())
                page.wait_for_function('manualSite.error !== null')
                self.assertIn('runtime identity',page.locator('#status').text_content())
                self.assertFalse(page.evaluate('manualSite.ready'));browser.close()

if __name__=='__main__':unittest.main()
