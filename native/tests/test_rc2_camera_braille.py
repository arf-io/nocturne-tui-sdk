"""RC2 operator corrections: wheel dolly and source braille dot/background fidelity."""
import ctypes as C
import math
import hashlib
import json
import os
import subprocess
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'bindings/python'),str(ROOT/'examples')]
from nocturne_native import NativeScene
from original_scenic_routes import build_original_scenic_routes
DOTS=(1,8,2,16,4,32,64,128)
class Cell(C.Structure):
 _fields_=[(name,C.c_uint32)for name in ('glyph','foreground','background','id')]
class RC2CameraBraille(unittest.TestCase):
 def scene(self):
  s=NativeScene(2030);self.addCleanup(s.close);return s
 def resolve(self,s,values,background=0x101319,sampling=1):
  fn=s._lib.nrResolveSourceSamples
  fn.argtypes=[C.POINTER(Cell),C.POINTER(C.c_uint32),C.POINTER(C.c_int32),C.c_uint32,C.c_int]
  cell=Cell();fn(C.byref(cell),(C.c_uint32*8)(*values),(C.c_int32*8)(*[1]*8),background,sampling);return cell
 def test_all_four_scenic_wheels_dolly_without_roll_and_reverse(self):
  for route in build_original_scenic_routes():
   with self.subTest(scene=route['id']):
    s=self.scene()
    for command in route['commands']:s.command(command)
    s.render();before=s.info()['camera'];target=before['target']
    s.command({'op':'wheel','delta':1,'x':80,'y':20});after=s.info()['camera']
    self.assertGreater(math.dist(before['position'],after['position']),.1,'Wheel must translate, not roll')
    self.assertLess(math.dist(after['position'],target),math.dist(before['position'],target))
    self.assertAlmostEqual(before['roll'],after['roll'],places=9)
    s.command({'op':'wheel','delta':-1,'x':80,'y':20});back=s.info()['camera']
    self.assertLess(math.dist(before['position'],back['position']),2e-6)
    self.assertAlmostEqual(before['roll'],back['roll'],places=9)
 def test_wheel_visibly_scales_geometry_in_all_four_scenes_and_projections(self):
  # A finite real mesh in each authored scenic background avoids using the
  # clipped infinite terrain silhouette as a false measure of camera scale.
  color=0xfd01fe
  def bounds(scene):
   points=[]
   for i,(glyph,fg,bg,hit) in enumerate(scene.render().words()):
    if fg!=color or not 0x2800<=glyph<=0x28ff:continue
    for k,dot in enumerate(DOTS):
     if glyph&dot:points.append((2*(i%160)+k%2,4*(i//160)+k//2))
   self.assertGreater(len(points),20,'Measured foreground landmark must really render')
   xs,ys=zip(*points);return (max(xs)-min(xs)+1,max(ys)-min(ys)+1,(max(xs)+min(xs))/2,(max(ys)+min(ys))/2)
  for route in build_original_scenic_routes():
   for ortho in (True,False):
    with self.subTest(scene=route['id'],orthographic=ortho):
     s=self.scene()
     for command in route['commands']:s.command(command)
     s.command({'op':'camera','position':[0,0,100],'yaw':0,'pitch':0,'roll':0,'orthographic':ortho,'span':100})
     s.command({'op':'mesh','sampling':'braille','triangles':[{'a':[2,0,70],'b':[10,0,70],'c':[10,8,70],'color':color,'alpha':1},{'a':[2,0,70],'b':[10,8,70],'c':[2,8,70],'color':color,'alpha':1}]})
     before=bounds(s);cam=s.info()['camera']
     x,y=before[2]/2,before[3]/4
     s.command({'op':'pointer','phase':'down','button':1,'x':x,'y':y})
     anchor=s.info()['camera']['grabbed'];self.assertIsNotNone(anchor)
     s.command({'op':'wheel','delta':5,'x':x,'y':y});near=bounds(s);after=s.info()['camera']
     self.assertGreater(near[0],before[0]*1.08);self.assertGreater(near[1],before[1]*1.08)
     self.assertEqual(after['roll'],cam['roll']);self.assertEqual(after['grabbed'],anchor)
     if ortho:
      self.assertLess(after['span'],cam['span'])
      self.assertAlmostEqual(near[2],before[2],delta=1);self.assertAlmostEqual(near[3],before[3],delta=1)
     s.command({'op':'wheel','delta':-5,'x':x,'y':y});back=bounds(s)
     self.assertEqual(back,before);self.assertLess(math.dist(s.info()['camera']['position'],cam['position']),2e-6)
     s.command({'op':'wheel','delta':-5,'x':x,'y':y});far=bounds(s)
     self.assertLess(far[0],before[0]*.94);self.assertLess(far[1],before[1]*.94)
     s.command({'op':'pointer','phase':'up','button':1,'x':x,'y':y})
 def test_orthographic_wheel_axis_controls_anchor_and_snapshot(self):
  for configured in (False,True):
   with self.subTest(configured=configured):
    s=self.scene()
    for c in build_original_scenic_routes()[0]['commands']:s.command(c)
    if not configured:s.command({'op':'camera-controls','enabled':False})
    s.render();s.command({'op':'pointer','phase':'down','button':1,'x':57.25,'y':16.4})
    before=s.info()['camera'];anchor=before['grabbed'];self.assertIsNotNone(anchor)
    snapshot=s.snapshot();s.command({'op':'wheel','delta':3,'x':57.25,'y':16.4});after=s.info()['camera']
    self.assertLess(after['span'],before['span']);self.assertEqual(after['grabbed'],anchor)
    # Orthographic offset/span is invariant, independent of renderer pixel units.
    for i in range(3):self.assertAlmostEqual((anchor[i]-before['position'][i])/before['span'],(anchor[i]-after['position'][i])/after['span'],delta=1e-7)
    expected=s.snapshot();frame=s.render().bytes;s.restore(snapshot);s.command({'op':'wheel','delta':3,'x':57.25,'y':16.4})
    self.assertEqual(s.snapshot(),expected);self.assertEqual(s.render().bytes,frame)
  s=self.scene()
  for c in build_original_scenic_routes()[0]['commands']:s.command(c)
  for patch in ({'enabled':False},{'enabled':True,'sensitivity':0},{'action':'disabled','sensitivity':1}):
   s.command({'op':'camera-controls','inputAxes':{'z':patch}});before=s.info()['camera'];s.command({'op':'wheel','delta':3,'x':80,'y':20});self.assertEqual(s.info()['camera'],before)
  s.command({'op':'camera-controls','inputAxes':{'z':{'action':'pan-z','sensitivity':1,'enabled':True,'invert':True}}})
  before=s.info()['camera'];s.command({'op':'wheel','delta':3,'x':80,'y':20});after=s.info()['camera'];self.assertGreater(after['span'],before['span']);self.assertEqual(after['roll'],before['roll'])
  s.command({'op':'camera-controls','inputAxes':{'z':{'action':'orbit-z','invert':False}}})
  before=s.info()['camera'];s.command({'op':'wheel','delta':3,'x':80,'y':20});after=s.info()['camera'];self.assertEqual(after['span'],before['span']);self.assertNotEqual(after['roll'],before['roll'])
 def test_orthographic_zoom_respects_existing_subunit_span_domain(self):
  s=self.scene();s.command({'op':'camera','position':[0,0,60],'yaw':0,'pitch':0,'orthographic':True,'span':.5})
  s.command({'op':'camera-controls','rig':'orbit','anchor':[0,0,0]});s.render()
  s.command({'op':'wheel','delta':1,'x':20,'y':10});self.assertLess(s.info()['camera']['span'],.5)
  s.command({'op':'wheel','delta':-1,'x':20,'y':10});self.assertAlmostEqual(s.info()['camera']['span'],.5,places=6)
  s.command({'op':'camera','span':.1});s.command({'op':'wheel','delta':100,'x':20,'y':10});self.assertAlmostEqual(s.info()['camera']['span'],.1,places=6)
 def test_source_braille_preserves_every_mask_and_background(self):
  s=self.scene();bg=0x101319
  for mask in range(256):
   with self.subTest(mask=mask):
    cell=self.resolve(s,[0xe8ddc1 if mask&dot else bg for dot in DOTS],bg)
    self.assertEqual(cell.glyph,0x2800+mask if mask else 32)
    self.assertEqual(cell.background,bg,'Dot gaps must retain unpainted source background')
 def test_full_source_braille_is_not_a_luminance_partition(self):
  s=self.scene();bg=0x101319
  for values in ([0xffffff]*8,[0x010101]*8,[0xffffff,0x050505]*4,[0xf0e0d0,0x332211,0xaa0011,0x336677]*2):
   with self.subTest(values=values):
    cell=self.resolve(s,values,bg);self.assertEqual(cell.glyph,0x28ff)
    self.assertEqual(cell.background,bg)
 def test_explicit_half_source_remains_half_not_braille(self):
  s=self.scene();cell=self.resolve(s,[0xf0e0d0]*4+[0x203040]*4,sampling=0)
  self.assertEqual((cell.glyph,cell.foreground,cell.background),(0x2580,0xf0e0d0,0x203040))
  cell=self.resolve(s,[0x556677]*8,sampling=0)
  self.assertEqual((cell.glyph,cell.foreground,cell.background),(32,0x556677,0x556677))
 def test_xy_anchor_orbit_and_explicit_z_roll_are_preserved(self):
  s=self.scene();s.command({'op':'camera','position':[0,0,60],'yaw':0,'pitch':0,'roll':0})
  s.command({'op':'camera-controls','rig':'orbit','anchor':[0,0,0]})
  before=s.info()['camera'];s.command({'op':'camera-input','delta':[10,5,0]});after=s.info()['camera']
  self.assertNotEqual(before['position'],after['position']);self.assertAlmostEqual(math.dist(after['position'],[0,0,0]),60,delta=2e-6)
  s.command({'op':'camera','position':[0,0,60],'yaw':0,'pitch':0,'roll':0})
  s.command({'op':'camera-controls','inputAxes':{'z':{'action':'orbit-z','sensitivity':1,'invert':False}}})
  before=s.info()['camera'];s.command({'op':'camera-input','delta':[0,0,10]});after=s.info()['camera']
  self.assertGreater(abs(after['roll']-before['roll']),9)
 def test_actual_canvas_full_source_braille_has_eight_islands_and_unpainted_gaps(self):
  from playwright.sync_api import sync_playwright
  s=self.scene();cell=self.resolve(s,[0xe8ddc1]*8)
  module=(ROOT/'bindings/typescript/canvas_braille.mjs').read_text()
  with sync_playwright()as pw:
   browser=pw.chromium.launch(headless=True)
   try:
    page=browser.new_page();page.set_content('<canvas id="c" width="20" height="40"></canvas>')
    page.add_script_tag(type='module',content=module+'\nwindow.paint={paintBraille,paintBlock};');page.wait_for_function('window.paint')
    result=page.evaluate("""v=>{const c=document.querySelector('canvas'),ctx=c.getContext('2d'),hex=x=>'#'+x.toString(16).padStart(6,'0');ctx.fillStyle=hex(v[2]);ctx.fillRect(0,0,20,40);ctx.fillStyle=hex(v[1]);if(!paint.paintBraille(ctx,v[0],0,0,20,40))paint.paintBlock(ctx,v[0],0,0,20,40);const p=ctx.getImageData(0,0,20,40).data,seen=new Uint8Array(800),color=n=>(p[n*4]<<16|p[n*4+1]<<8|p[n*4+2]);let islands=0,ink=0;for(let n=0;n<800;n++){if(color(n)!==v[1])continue;ink++;if(seen[n])continue;islands++;const todo=[n];seen[n]=1;while(todo.length){const x=todo.pop();for(const q of [x%20?x-1:-1,x%20<19?x+1:-1,x-20,x+20])if(q>=0&&q<800&&!seen[q]&&color(q)===v[1]){seen[q]=1;todo.push(q)}}}return{islands,ink,gap:color(410)};}""",[cell.glyph,cell.foreground,cell.background])
    self.assertEqual(result,dict(islands=8,ink=128,gap=0x101319))
   finally:browser.close()
 def test_public_native_wasm_wheel_replay_and_render_purity(self):
  cases=build_original_scenic_routes();expected=[]
  for route in cases:
   s=self.scene()
   for command in route['commands']:s.command(command)
   states=[]
   for command in [None,{'op':'wheel','delta':1,'x':80,'y':20},{'op':'wheel','delta':-1,'x':80,'y':20}]:
    if command:s.command(command)
    before=s.snapshot();frame=s.render();self.assertEqual(hashlib.sha256(s.snapshot()).digest(),hashlib.sha256(before).digest())
    self.assertTrue(all(g==32 or 0x2800<=g<=0x28ff for g,fg,bg,hit in frame.words()))
    self.assertTrue(all(bg==0x101319 for g,fg,bg,hit in frame.words()))
    states.append(dict(camera=s.info()['camera'],frame=hashlib.sha256(frame.bytes).hexdigest()))
   expected.append(states)
  script="""import{readFileSync}from'node:fs';import{pathToFileURL}from'node:url';import{createHash}from'node:crypto';const root=process.argv[1],{NativeScene}=await import(pathToFileURL(root+'/bindings/typescript/native_scene.mjs'));const scene=await NativeScene.create(readFileSync(root+'/dist/nocturne_native.wasm'),2030),cases=JSON.parse(readFileSync(0,'utf8')),out=[],hash=x=>createHash('sha256').update(x).digest('hex');for(const route of cases){scene.command({op:'reset',seed:2030});for(const c of route.commands)while(scene.command(c)===1){}const rows=[];for(const c of [null,{op:'wheel',delta:1,x:80,y:20},{op:'wheel',delta:-1,x:80,y:20}]){if(c)while(scene.command(c)===1){}const before=hash(scene.snapshot()),frame=scene.render();if(hash(scene.snapshot())!==before)throw Error('render mutated state');rows.push({camera:scene.info().camera,frame:hash(frame.bytes)})}out.push(rows)}console.log(JSON.stringify(out));"""
  run=subprocess.run(['node','--input-type=module','-e',script,str(ROOT)],input=json.dumps(cases),capture_output=True,text=True,timeout=30)
  self.assertEqual(run.returncode,0,run.stderr);self.assertEqual(json.loads(run.stdout),expected)

class RC2CameraGallery(unittest.TestCase):
 def test_real_wheel_over_all_four_gallery_scenes_never_rolls(self):
  from playwright.sync_api import sync_playwright
  with sync_playwright()as pw:
   browser=pw.chromium.launch(headless=True)
   try:
    page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(Path(os.environ.get('NOCTURNE_CAMERA_GALLERY_PATH',ROOT/'Nocturne-Test-Harness.html')).resolve().as_uri());page.wait_for_function('window.nativeLab')
    for route in build_original_scenic_routes():
     with self.subTest(scene=route['id']):
      page.select_option('#scenes',route['id']);page.evaluate('nativeLab.hold();nativeLab.draw()')
      canvas=page.locator('#canvas');canvas.scroll_into_view_if_needed();box=canvas.bounding_box()
      page.mouse.move(box['x']+box['width']*.5,box['y']+box['height']*.4)
      before=page.evaluate('nativeLab.scene.info().camera');page.mouse.wheel(0,-100)
      page.wait_for_function('(p)=>nativeLab.scene.info().camera.position.some((v,i)=>v!==p[i])',arg=before['position'])
      after=page.evaluate('nativeLab.scene.info().camera')
      self.assertAlmostEqual(before['roll'],after['roll'],places=9)
      self.assertLess(after['span'],before['span'],'Real wheel must visibly magnify orthographic scenes')
      self.assertLess(math.dist(after['position'],before['target']),math.dist(before['position'],before['target']))
      page.mouse.wheel(0,100);page.wait_for_timeout(30);back=page.evaluate('nativeLab.scene.info().camera')
      self.assertAlmostEqual(before['span'],back['span'],places=6)
      self.assertAlmostEqual(before['roll'],back['roll'],places=9);self.assertLess(math.dist(before['position'],back['position']),2e-6)
      self.assertFalse(page.locator('#error').inner_text())
    self.assertFalse(errors)
   finally:browser.close()

if __name__=='__main__':unittest.main()
