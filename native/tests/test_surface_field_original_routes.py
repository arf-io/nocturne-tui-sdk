"""Normal gallery Surface4 routes use actual C/WASM source painter."""
import base64,gzip,hashlib,json,os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class SurfaceOriginalRoutes(unittest.TestCase):
 def test_normal_picker_play_and_peak_complete_native_wasm_frames(self):
  from playwright.sync_api import sync_playwright
  captures=[]
  with sync_playwright() as p:
   browser=p.chromium.launch(headless=True);page=browser.new_page(reduced_motion='reduce')
   page.goto(Path(os.environ.get('NOCTURNE_ORIGINAL_GALLERY',ROOT/'Nocturne-RC4-Source-Build.html')).resolve().as_uri());page.wait_for_function('window.nativeLab')
   page.locator('#effect').evaluate("e=>e.closest('details').open=true")
   for effect in ('silk-tide','satin-rings','opal-fronts','interference-tide'):
    for mode in ('peak','play'):
     page.select_option('#effect','surface-field/'+effect)
     if mode=='peak':page.click('#effect-peak');page.evaluate('nativeLab.hold();nativeLab.draw()')
     else:page.uncheck('#reduced-motion');page.evaluate("document.getElementById('effect-play').click();nativeLab.hold();nativeLab.advance(750000);nativeLab.draw()")
     info=page.evaluate('nativeLab.scene.infoComplete()');self.assertEqual(info['fields'][0]['paint'],'source');self.assertEqual(info['fields'][0]['optics'],'source')
     snapshot=page.evaluate("(()=>{let a=nativeLab.scene.snapshot(),s='';for(let i=0;i<a.length;i+=32768)s+=String.fromCharCode(...a.subarray(i,i+32768));return btoa(s)})()")
     raw=base64.b64decode(snapshot);rendered=page.evaluate('(()=>{const f=nativeLab.scene.render();return {width:f.width,height:f.height,cells:Array.from(f.cells)}})()');wasm=rendered['cells']
     with NativeScene(1) as native:
      native.restore(raw);before=native.snapshot();frame=native.render().bytes;self.assertEqual(before,native.snapshot());cells=list(memoryview(frame).cast('I'));self.assertEqual(cells,wasm)
     captures.append({'key':effect+'-'+mode,'effect':'surface-field/'+effect,'mode':mode,'timeUs':info['clock']['timeUs'],'width':rendered['width'],'height':rendered['height'],'snapshotSha256':hashlib.sha256(raw).hexdigest(),'native':cells,'wasm':wasm})
   browser.close()
  if os.environ.get('NOCTURNE_SURFACE_ROUTE_EVIDENCE'):
   d=Path(os.environ['NOCTURNE_SURFACE_ROUTE_EVIDENCE']);d.mkdir(parents=True,exist_ok=True);(d/'frames.json.gz').write_bytes(gzip.compress(json.dumps(captures,separators=(',',':')).encode(),mtime=0));(d/'comparison.json').write_text(json.dumps({'cases':len(captures),'mismatches':0,'scope':'Actual normal gallery Play/Peak native versus WASM complete frames. Original painter correspondence is separately covered by168 original-oracle cases; this does not claim original enclosing application UI parity.'},indent=2)+'\n')
if __name__=='__main__':unittest.main()
