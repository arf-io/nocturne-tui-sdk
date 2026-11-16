"""Actual WASM camera controls in the ordinary gallery."""
import os,unittest
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class CameraControlsGallery(unittest.TestCase):
 def test_camera_rigs_are_visible_beside_or_below_live_viewport(self):
  with sync_playwright() as pw:
   browser=pw.chromium.launch(headless=True)
   try:
    page=browser.new_page(viewport={"width":1440,"height":900})
    page.goto(Path(os.environ.get("NOCTURNE_CAMERA_GALLERY_PATH",ROOT/"Nocturne-Test-Harness.html")).resolve().as_uri())
    page.wait_for_function("window.nativeLab");page.evaluate("nativeLab.hold()")
    self.assertEqual(page.title(),"Nocturne / "+page.evaluate("nativeLab.scene.info().build"))
    self.assertEqual(page.locator("#camera-rig").count(),1,"The ordinary gallery must expose actual camera rig selection")
    page.locator("#camera-controls-panel").evaluate("e=>e.open=true")
    labels=page.locator("#camera-rig option").all_text_contents()
    for label in ["Head","Dolly","Crane / jib","Follow / chase","Head in spacecraft","Anchored orbit"]:
     self.assertIn(label,labels)
    for width,height in [(1440,900),(390,844),(760,420)]:
     with self.subTest(width=width,height=height):
      page.set_viewport_size({"width":width,"height":height});page.locator("#camera-rig").scroll_into_view_if_needed()
      canvas=page.locator("#canvas").bounding_box();picker=page.locator("#camera-rig").bounding_box()
      self.assertGreater(canvas["width"],0);self.assertGreater(canvas["height"],0)
      self.assertGreaterEqual(canvas["x"],0);self.assertGreaterEqual(canvas["y"],0)
      self.assertLessEqual(canvas["x"]+canvas["width"],width+.1);self.assertLessEqual(canvas["y"]+canvas["height"],height+.1)
      self.assertTrue(picker["x"]>=canvas["x"]+canvas["width"]-.1 or picker["y"]>=canvas["y"]+canvas["height"]-.1)
      self.assertEqual(page.locator("#camera-apply").count(),1);self.assertEqual(page.locator("#orbit-start").count(),1)
   finally:browser.close()
 def test_unchanged_body_pose_does_not_apply_head_rotation_twice(self):
  with sync_playwright() as pw:
   browser=pw.chromium.launch(headless=True)
   try:
    page=browser.new_page(viewport={"width":1440,"height":900})
    page.goto(Path(os.environ.get("NOCTURNE_CAMERA_GALLERY_PATH",ROOT/"Nocturne-Test-Harness.html")).resolve().as_uri());page.wait_for_function("window.nativeLab");page.select_option("#scenes","work-graph");page.evaluate("nativeLab.hold()")
    page.evaluate("()=>{const s=nativeLab.scene;for(const c of [{op:'camera',position:[0,8,46],yaw:0,pitch:0,roll:0},{op:'camera-controls',rig:'spacecraft',head:{position:[0,0,0],rotation:[0,30,0]}}]){let pending;do{pending=s.command(c);}while(pending===1);}}")
    page.locator("#camera-controls-panel").evaluate("e=>e.open=true");page.locator("#camera-controls-read").click();page.locator(".camera-pose").evaluate("e=>e.open=true")
    before=page.evaluate("nativeLab.scene.info().camera");self.assertAlmostEqual(before['yaw'],30,places=6)
    page.evaluate("window.bodyPoseFrameBefore=nativeLab.scene.render().bytes.slice()")
    page.locator("#camera-apply").click();after=page.evaluate("nativeLab.scene.info().camera")
    for key in ['position','yaw','pitch','roll']:
     self.assertEqual(after[key],before[key],f'Applying unchanged body pose must preserve composed camera {key}')
    self.assertEqual(after['controls']['head'],before['controls']['head'])
    self.assertTrue(page.evaluate("()=>{const a=nativeLab.scene.render().bytes,b=bodyPoseFrameBefore;return a.length===b.length&&a.every((v,i)=>v===b[i]);}"))
    self.assertFalse(page.locator('#error').inner_text())
   finally:browser.close()
 def test_actual_rig_axis_configuration_readback_and_atomic_rejection(self):
  with sync_playwright() as pw:
   browser=pw.chromium.launch(headless=True)
   try:
    page=browser.new_page(viewport={"width":1440,"height":900});errors=[];page.on("pageerror",lambda e:errors.append(str(e)))
    page.goto(Path(os.environ.get("NOCTURNE_CAMERA_GALLERY_PATH",ROOT/"Nocturne-Test-Harness.html")).resolve().as_uri());page.wait_for_function("window.nativeLab");page.select_option("#scenes","work-graph");page.evaluate("nativeLab.hold()")
    self.assertEqual(page.locator("#camera-rig").count(),1);page.locator("#camera-controls-panel").evaluate("e=>e.open=true")
    page.locator("#draft").fill("Camera controls preserve é 🪶");page.locator("#draft").dispatch_event("input")
    for rig in ['head','dolly','crane','follow','spacecraft','orbit']:
     with self.subTest(rig=rig):
      page.select_option("#camera-rig",rig);self.assertEqual(page.evaluate("nativeLab.scene.info().camera.controls.rig"),rig);self.assertTrue(page.evaluate("nativeLab.scene.info().camera.controls.enabled"))
    page.select_option("#camera-rig","spacecraft");page.select_option("#camera-mode","fly");page.select_option("#camera-input-target","head")
    for axis,action,sensitivity,invert,enabled in [('x','look-y','2.5',True,True),('y','pan-y','0',False,False),('z','orbit-z','3',True,True)]:
     page.select_option('#camera-axis-'+axis+'-action',action);page.locator('#camera-axis-'+axis+'-sensitivity').fill(sensitivity);page.locator('#camera-axis-'+axis+'-invert').set_checked(invert);page.locator('#camera-axis-'+axis+'-enabled').set_checked(enabled)
    for key,values in [('head-position',[1,2,3]),('head-rotation',[10,20,30])]:
     for axis,value in zip('xyz',values):page.locator('#camera-'+key+'-'+axis).fill(str(value))
    page.locator('#camera-anchor-enabled').check()
    for axis,value in zip('xyz',[4,5,6]):page.locator('#camera-anchor-'+axis).fill(str(value))
    page.locator('#camera-controls-apply').click();state=page.evaluate('nativeLab.scene.info().camera.controls')
    self.assertEqual(state['inputTarget'],'head');self.assertEqual(state['mode'],'fly');self.assertEqual(state['head'],{'position':[1,2,3],'rotation':[10,20,30]});self.assertEqual(state['anchor'],[4,5,6]);self.assertEqual(state['inputAxes']['x'],{'action':'look-y','sensitivity':2.5,'invert':True,'enabled':True});self.assertFalse(state['inputAxes']['y']['enabled']);self.assertEqual(state['inputAxes']['y']['sensitivity'],0)
    page.evaluate("()=>{const s=nativeLab.scene,before=s.snapshot();let pending;do{pending=s.command({op:'camera-input',delta:[2,-1,3],pan:false});}while(pending===1);window.expectedCameraInput=s.snapshot();window.expectedCameraInputFrame=s.render().bytes.slice();window.cameraInputChanged=!before.every((v,i)=>v===expectedCameraInput[i]);s.restore(before);}")
    self.assertTrue(page.evaluate('cameraInputChanged'))
    for axis,value in zip('xyz',[2,-1,3]):page.locator('#camera-input-'+axis).fill(str(value))
    page.locator('#camera-input-apply').click();self.assertTrue(page.evaluate('()=>{const s=nativeLab.scene.snapshot(),f=nativeLab.scene.render().bytes;return s.length===expectedCameraInput.length&&s.every((v,i)=>v===expectedCameraInput[i])&&f.every((v,i)=>v===expectedCameraInputFrame[i]);}'))
    page.select_option('#camera-rig','crane')
    for key,values in [('crane-pivot',[2,3,4]),('crane-boom',[0,10,20])]:
     for axis,value in zip('xyz',values):page.locator('#camera-'+key+'-'+axis).fill(str(value))
    page.locator('#camera-controls-apply').click();self.assertEqual(page.evaluate('nativeLab.scene.info().camera.controls.crane'),{'pivot':[2,3,4],'boom':[0,10,20]})
    page.select_option('#camera-rig','follow');page.select_option('#camera-follow-kind','node');node=page.evaluate('nativeLab.scene.info().nodes[0].id');page.locator('#camera-follow-id').fill(str(node));page.locator('#camera-follow-track').check()
    for axis,value in zip('xyz',[0,4,12]):page.locator('#camera-follow-offset-'+axis).fill(str(value))
    page.locator('#camera-controls-apply').click();follow=page.evaluate('nativeLab.scene.info().camera.controls.follow');self.assertEqual(follow['target'],{'kind':'node','id':node});self.assertEqual(follow['offset'],[0,4,12]);self.assertTrue(follow['track'])
    page.evaluate('window.cameraControlsBefore=nativeLab.scene.snapshot();window.cameraControlsFrame=nativeLab.scene.render().bytes.slice()');page.locator('#camera-axis-x-sensitivity').fill('1001');page.locator('#camera-controls-apply').click();self.assertTrue(page.locator('#error').inner_text())
    self.assertTrue(page.evaluate('()=>{const a=nativeLab.scene.snapshot(),b=nativeLab.scene.render().bytes;return a.length===cameraControlsBefore.length&&a.every((v,i)=>v===cameraControlsBefore[i])&&b.every((v,i)=>v===cameraControlsFrame[i]);}'))
    page.locator('#camera-controls-read').click();self.assertNotEqual(page.locator('#camera-axis-x-sensitivity').input_value(),'1001');self.assertEqual(page.evaluate('nativeLab.scene.info().prompt.text'),'Camera controls preserve é 🪶')
    page.locator('#camera-controls-enabled').uncheck();self.assertFalse(page.evaluate('nativeLab.scene.info().camera.controls.enabled'));self.assertFalse(errors)
   finally:browser.close()
if __name__=="__main__":unittest.main()
