"""Actual normal-picker original scenic control and clock behavior."""
from pathlib import Path
import os,unittest,math
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
HTML=Path(os.environ.get('NOCTURNE_SCENIC_GALLERY_PATH',ROOT/'Nocturne-RC4-Source-Build.html'))
class OriginalScenicGallery(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.pw=sync_playwright().start();cls.browser=cls.pw.chromium.launch(headless=True,executable_path=os.environ.get('CHROMIUM'))
 @classmethod
 def tearDownClass(cls):cls.browser.close();cls.pw.stop()
 def setUp(self):
  self.page=self.browser.new_page(viewport=dict(width=1440,height=900));self.errors=[];self.page.on('pageerror',lambda e:self.errors.append(str(e)));self.page.set_content(HTML.read_text());self.page.wait_for_function('window.nativeLab');self.page.evaluate('nativeLab.hold()')
 def tearDown(self):self.page.close()
 def load(self,name):
  self.page.locator('#scenes').select_option('original-'+name);self.page.evaluate('nativeLab.hold();nativeLab.draw()')
 def test_normal_named_routes_real_controls_and_camera(self):
  for name,title in [('pearl-cascade','Pearl Cascade'),('copper-causeway','Copper Causeway'),('tidal-glass','Tidal Glass'),('silt','Silt')]:
   self.assertEqual(self.page.locator('#scenes option[value="original-'+name+'"]').count(),1,name)
   self.load(name);self.assertEqual(self.page.locator('#title').inner_text(),title);self.assertEqual(self.page.evaluate('nativeLab.scene.info().sceneArt.scene'),name)
   self.page.locator('#scenic-source-panel').evaluate('(e)=>e.open=true');self.assertTrue(self.page.locator('#scenic-landscapeSpeed').is_visible());self.assertTrue(self.page.locator('#scenic-waveHeight').is_visible())
   before=self.page.evaluate('({camera:nativeLab.scene.info().camera,frame:Array.from(nativeLab.scene.render().cells)})')
   picked=self.page.evaluate('''()=>{const f=nativeLab.scene.render();for(let y=Math.floor(f.height/3);y<f.height*3/4;y++)for(let x=Math.floor(f.width/4);x<f.width*2/5;x++){const i=(y*f.width+x)*4;if(f.cells[i]>32&&f.cells[i+1]!==f.cells[i+2])return {x:x+.3,y:y+.6,width:f.width,height:f.height};}return null;}''');self.assertIsNotNone(picked,'real off-center source geometry')
   self.page.evaluate('''()=>{const c=document.getElementById('canvas');c.addEventListener('pointerdown',e=>{const r=c.getBoundingClientRect(),f=nativeLab.scene.render();window.scenicPointer={x:(e.clientX-r.left)*f.width/r.width,y:(e.clientY-r.top)*f.height/r.height};},{once:true});}''')
   box=self.page.locator('#canvas').bounding_box();x=box['x']+box['width']*picked['x']/picked['width'];y=box['y']+box['height']*picked['y']/picked['height'];self.page.mouse.move(x,y);self.page.mouse.down();held=self.page.evaluate('nativeLab.scene.info().camera');pointer=self.page.evaluate('scenicPointer');self.assertIsNotNone(held['grabbed']);self.assertIsNone(held['controls']['anchor']);self.page.mouse.move(x+40,y+20,steps=4);moved=self.page.evaluate('nativeLab.scene.info().camera');self.assertEqual(moved['grabbed'],held['grabbed'])
   def project(camera):
    dx,dy,dz=[held['grabbed'][i]-camera['position'][i] for i in range(3)];dz=-dz;cy,sy=math.cos(math.radians(camera['yaw'])),math.sin(math.radians(camera['yaw']));cp,sp=math.cos(math.radians(camera['pitch'])),math.sin(math.radians(camera['pitch']));cr,sr=math.cos(math.radians(camera['roll'])),math.sin(math.radians(camera['roll']));a,b=dx*cy-dz*sy,dx*sy+dz*cy;u=dy*cp-b*sp;xx,yy=a*cr+u*sr,u*cr-a*sr;return [picked['width']/2+xx*picked['width']/camera['span'],picked['height']/2-yy*picked['width']/(2*camera['span'])]
   for camera in (held,moved):
    px,py=project(camera);self.assertAlmostEqual(px,pointer['x'],delta=.3,msg='source world anchor must retain original image X');self.assertAlmostEqual(py,pointer['y'],delta=.3,msg='source world anchor must retain original image Y')
   self.page.mouse.up();after=self.page.evaluate('({camera:nativeLab.scene.info().camera,frame:Array.from(nativeLab.scene.render().cells)})');self.assertIsNone(after['camera']['grabbed']);self.assertNotEqual(before['camera'],after['camera']);self.assertNotEqual(before['frame'],after['frame']);self.assertFalse(self.errors)
 def test_piecewise_motion_controls_presets_and_hold(self):
  self.page.evaluate("nativeLab.load(nativeLab.recipes.find(r=>r.id==='original-pearl-cascade'));nativeLab.hold();nativeLab.advance(1700000)");self.page.locator('#scenic-source-panel').evaluate('(e)=>e.open=true');self.page.locator('#scenic-waterFlow').fill('1.6');self.page.locator('#scenic-apply-rates').click();self.page.evaluate('nativeLab.advance(1000000)');self.assertEqual(self.page.evaluate('nativeLab.scene.info().sceneArt.timeMs'),3300)
  self.page.locator('#scenic-waterFlow').fill('0');self.page.locator('#scenic-apply-rates').click();self.page.evaluate('nativeLab.advance(1000000)');self.assertEqual(self.page.evaluate('nativeLab.scene.info().sceneArt.timeMs'),3300)
  self.load('copper-causeway');a=self.page.evaluate('Array.from(nativeLab.scene.render().cells)');self.page.evaluate('nativeLab.advance(1000000)');b=self.page.evaluate('Array.from(nativeLab.scene.render().cells)');self.assertNotEqual(a,b);self.page.wait_for_timeout(70);self.assertEqual(b,self.page.evaluate('Array.from(nativeLab.scene.render().cells)'))
  self.load('tidal-glass');self.page.locator('#scenic-source-panel').evaluate('(e)=>e.open=true');self.page.locator('#scenic-preset').select_option('winter-swell');self.page.locator('#scenic-apply-preset').click();self.assertEqual(self.page.evaluate('nativeLab.scene.info().sceneArt.detail.waveHeight'),3.1015625);self.assertFalse(self.errors)

 def test_real_play_hold_and_workspace_replay(self):
  self.page.evaluate("nativeLab.load(nativeLab.recipes.find(r=>r.id==='original-copper-causeway'));nativeLab.hold();nativeLab.advance(1700000)")
  a=self.page.evaluate('Array.from(nativeLab.scene.render().cells)');self.page.locator('#play').evaluate('e=>e.closest("details").open=true');self.page.locator('#play').click();self.page.wait_for_timeout(100);self.page.evaluate('nativeLab.hold()');b=self.page.evaluate('Array.from(nativeLab.scene.render().cells)');self.assertNotEqual(a,b);self.page.wait_for_timeout(100);self.assertEqual(b,self.page.evaluate('Array.from(nativeLab.scene.render().cells)'))
  self.assertTrue(self.page.evaluate("()=>{const session=nativeLab.scenicSession(),s=session.checkpoint(),frame=nativeLab.scene.render().cells.slice();nativeLab.advance(1000000);session.restore(s);const restored=nativeLab.scene.render().cells;return frame.length===restored.length&&frame.every((v,i)=>v===restored[i]);}"));self.assertFalse(self.errors)
