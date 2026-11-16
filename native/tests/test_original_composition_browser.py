from pathlib import Path
import json,hashlib,os,tempfile,unittest
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class OriginalCompositionBrowser(unittest.TestCase):
 def test_real_layers_input_arrival_and_host_timeline_replay(self):
  with tempfile.TemporaryDirectory(prefix='nocturne-composition-browser-')as directory,sync_playwright()as p:
   E=Path(directory)
   b=p.chromium.launch(headless=True);page=b.new_page(viewport={'width':1440,'height':900},accept_downloads=True);errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(Path(os.environ.get('NOCTURNE_COMPOSITION_GALLERY_PATH',ROOT/'Nocturne-RC4-Source-Build.html')).as_uri());page.wait_for_function('window.nativeLab');page.select_option('#scenes','original-composition-snow');page.evaluate('nativeLab.hold();nativeLab.load(nativeLab.recipes.find(q=>q.id==="original-composition-snow"));nativeLab.hold();nativeLab.draw()');page.locator('#draft').fill('Local 🪶 é input stays immediate');page.locator('#draft').press('ArrowLeft');before=page.evaluate('nativeLab.scene.info().prompt');assert before['text']=='Local 🪶 é input stays immediate'
   page.locator('#motion-panel').evaluate('(e)=>e.open=true')
   page.locator('summary').filter(has_text='Configuration').first.evaluate('(e)=>e.parentElement.open=true')
   page.locator('#save').evaluate('(e)=>{for(let p=e.parentElement;p;p=p.parentElement)if(p.tagName==="DETAILS")p.open=true}')
   with page.expect_download()as event:page.click('#save')
   event.value.save_as(E/'composed-before-arrival.nrstate')
   page.evaluate('nativeLab.advance(1100000);nativeLab.draw()');after=page.evaluate('nativeLab.scene.info().prompt');assert after==before
   frame=page.evaluate('Array.from(nativeLab.scene.render().cells)');line=page.evaluate("()=>{const f=nativeLab.scene.render();return Array.from({length:29},(_,i)=>String.fromCodePoint(f.cells[(5*136+5+i)*4])).join('')}");assert line=='Incoming text / original fade'
   page.screenshot(path=str(E/'oblique-composition-real-browser.png'));page.click('#restore');assert page.evaluate('nativeLab.scene.info().clock.timeUs')==0
   page.evaluate('nativeLab.advance(1100000);nativeLab.draw()');assert page.evaluate('Array.from(nativeLab.scene.render().cells)')==frame
   page.locator('#snapshot-file').set_input_files(E/'composed-before-arrival.nrstate');page.wait_for_function('nativeLab.scene.info().clock.timeUs===0&&!nativeLab.scene.infoComplete().textRuns.some(q=>q.id===41)');page.evaluate('nativeLab.hold();nativeLab.advance(1100000);nativeLab.draw()');assert not any(q['id']==41 for q in page.evaluate('nativeLab.scene.infoComplete().textRuns'))
   assert page.evaluate('nativeLab.scene.info().prompt')==before;assert not errors,errors
   E.joinpath('BROWSER-COMPOSITION-RESULT.json').write_text(json.dumps({'pass':True,'unicodeDraftAndCaretPreserved':True,'originalArrivalVisible':True,'savedHostTimelineReplayExact':True,'nativeOnlyImportDoesNotResurrectActions':True,'pageErrors':errors},indent=2));b.close();print('PASS actual composed source flight/background/windows/prompt/arrival and timeline boundaries')

if __name__=='__main__':unittest.main()
