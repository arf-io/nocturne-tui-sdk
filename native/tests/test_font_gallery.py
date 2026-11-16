"""Real browser font parsing and pixels; supplied files stay outside the SDK."""
from pathlib import Path
import hashlib,json,os,tempfile,unittest
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class FontGallery(unittest.TestCase):
 def test_actual_configured_font_formats_and_failed_load_preserve_face(self):
  module=(ROOT/'bindings/typescript/font_gallery.mjs').read_text().replace('export function','function')
  fonts=[Path(os.environ['NOCTURNE_SHAPING_FONT'])]
  if os.environ.get('NOCTURNE_OTF_FONT'):fonts.append(Path(os.environ['NOCTURNE_OTF_FONT']))
  with tempfile.TemporaryDirectory()as directory,sync_playwright()as p:
   pagePath=Path(directory)/'fonts.html';pagePath.write_text('<canvas id="c" width="600" height="90"></canvas>')
   b=p.chromium.launch(headless=True);page=b.new_page();page.goto(pagePath.as_uri());page.add_script_tag(content=module);page.evaluate('window.fontController=createFontGallery()');records=[]
   for font in fonts:
    raw=font.read_bytes();expected=hashlib.sha256(raw).hexdigest();magic=raw[:4]
    self.assertIn(magic,[b'OTTO',b'\x00\x01\x00\x00',b'true'])
    got=page.evaluate('async r=>{const ctx=document.getElementById(\'c\').getContext(\'2d\');ctx.font=fontController.canvasFont(48);const oldWidth=ctx.measureText(\'Nocturne ffi Wx\').width;const m=await fontController.load(Uint8Array.from(r.bytes),r.name);ctx.clearRect(0,0,600,90);ctx.font=fontController.canvasFont(48);ctx.fillStyle=\'#fff\';ctx.fillText(\'Nocturne ffi Wx\',0,60);return{metadata:m,oldWidth,loaded:document.fonts.check(\'48px "\'+m.family+\'"\'),width:ctx.measureText(\'Nocturne ffi Wx\').width,pixels:Array.from(ctx.getImageData(0,0,600,90).data).filter((v,i)=>i%4===3&&v>0).length}}',{'bytes':list(raw),'name':font.name})
    self.assertEqual(got['metadata']['sha256'],expected);self.assertTrue(got['loaded']);self.assertGreater(got['pixels'],100);self.assertNotEqual(got['oldWidth'],got['width']);self.assertGreater(got['width'],100);records.append(got)
    rejected=page.evaluate("async()=>{const before=fontController.metadata();let rejected=false;try{await fontController.load(Uint8Array.from([1,2,3]),'not-a-font.otf')}catch{rejected=true}return{before,after:fontController.metadata(),rejected}}");self.assertTrue(rejected['rejected']);self.assertEqual(rejected['before'],rejected['after'])
   raw=fonts[0].read_bytes();race=page.evaluate("async bytes=>{const pending=fontController.load(Uint8Array.from(bytes),'late.ttf');fontController.reset();const result=await pending;return{result,metadata:fontController.metadata()}}",list(raw));self.assertFalse(race['result']['applied']);self.assertIsNone(race['metadata']['sha256']);b.close()
   if os.environ.get('NOCTURNE_FONT_GALLERY_EVIDENCE'):Path(os.environ['NOCTURNE_FONT_GALLERY_EVIDENCE']).write_text(json.dumps(records,indent=2))
if __name__=='__main__':unittest.main()
