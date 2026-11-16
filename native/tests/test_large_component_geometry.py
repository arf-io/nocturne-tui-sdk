"""Large component layouts must retain geometry and render only visible work.

This acceptance batch accompanies removal of legacy 240x100/200-world-unit
ceilings. It is not a declaration that authoring-only acceptance qualifies
rendering: visible rendering and snapshot replay are separate assertions.
"""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
KINDS=['text','box','rule','button','item','cursor','progress','bars','pie','donut','scatter','line','digits','edge','checkbox','radio','select','scrollbar']
class LargeComponentGeometry(unittest.TestCase):
 def scene(self):
  s=NativeScene(42);self.addCleanup(s.close)
  s.command({'op':'resize','width':512,'height':160})
  s.command({'op':'prompt','active':False})
  return s
 def preserved(self,s):
  saved=s.snapshot();s.render();self.assertEqual(s.snapshot(),saved)
  s.restore(saved);self.assertEqual(s.snapshot(),saved)
 def test_all_widget_kinds_accept_layout_beyond_legacy_viewport(self):
  for kind in KINDS:
   with self.subTest(kind=kind):
    s=self.scene();s.command({'op':'widget','id':1,'kind':kind,'x':300,'y':110,'width':300,'height':120,'value':.5,'data':[.2,.4,.6,.8],'text':'Large retained layout','alpha':.7})
    self.assertEqual(s.info()['widgets'][0]['kind'],KINDS.index(kind));self.preserved(s)
 def test_widget_geometry_bindings_match_independent_direct_edits(self):
  for field,value in [('x',350),('y',120),('width',1024),('height',256)]:
   with self.subTest(field=field):
    s=self.scene();oracle=self.scene()
    for scene in [s,oracle]:scene.command({'op':'widget','id':1,'kind':'box','x':10,'y':10,'width':40,'height':10})
    s.command({'op':'define','path':'/geometry','value':value,'binding':{'family':'widget','id':1,'field':field}})
    oracle.command({'op':'widget','id':1,field:value})
    s.command({'op':'remove-value','path':'/geometry'});self.assertEqual(s.snapshot(),oracle.snapshot());self.assertEqual(s.render().bytes,oracle.render().bytes)
 def test_area_large_nested_layout_and_bindings_restore(self):
  s=self.scene();s.command({'op':'area','id':1,'x':300,'y':110,'width':500,'height':200})
  s.command({'op':'area','id':2,'parent':1,'x':-20,'y':0,'width':800,'height':400})
  s.command({'op':'status','id':1,'area':2,'text':'Retained nested notification','durationMs':0})
  for field,value in [('x',350),('y',120),('width',1024),('height',256)]:
   s.command({'op':'define','path':'/area/'+field,'value':value,'binding':{'family':'area','id':2,'field':field}})
  self.preserved(s)
 def test_text_and_indicator_coordinates_follow_large_layout(self):
  s=self.scene();s.command({'op':'text','id':1,'text':'Beyond the old component limits','x':350,'y':120,'width':1024,'durationMs':0})
  s.command({'op':'indicator','id':1,'x':400,'y':130,'sequence':'◐◓◑◒'})
  self.preserved(s)
 def test_window_world_dimensions_and_reader_column_limits(self):
  s=self.scene();s.command({'op':'window','id':1,'width':1000,'height':1000,'minColumns':300,'maxColumns':1024,'title':'Large window','text':'Retained document'})
  for field,value in [('width',1500),('height',2000),('minColumns',350),('maxColumns',2048)]:
   s.command({'op':'define','path':'/window/'+field,'value':value,'binding':{'family':'window','id':1,'field':field}})
  self.preserved(s)
 def test_far_offscreen_layout_is_bounded_by_viewport_not_authored_area(self):
  s=self.scene()
  # A source-size loop over this rectangle is unacceptable even on a small viewport.
  s.command({'op':'widget','id':1,'kind':'box','x':-1000000000,'y':-1000000000,'width':2000000000,'height':2000000000})
  self.preserved(s)
 def test_clipped_line_matches_independent_integer_raster(self):
  dots=[1,8,2,16,4,32,64,128]
  for points in [[0,0,1,1],[0,1,1,0],[1,0,0,1],[1,1,0,0]]:
   with self.subTest(points=points):
    s=self.scene();s.command({'op':'widget','id':1,'kind':'edge','x':-100,'y':-20,'width':700,'height':200,'data':points,'sampling':'braille','value':1,'alpha':0})
    x0=-200+round(points[0]*1399);y0=-80+round(points[1]*799)
    x1=-200+round(points[2]*1399);y1=-80+round(points[3]*799)
    dx=abs(x1-x0);sx=1 if x0<x1 else -1;dy=-abs(y1-y0);sy=1 if y0<y1 else -1;error=dx+dy;expected={}
    while True:
     if 0<=x0<1024 and 4<=y0<636:
      cell=(x0//2,y0//4);expected[cell]=expected.get(cell,0)|dots[(y0%4)*2+x0%2]
     if x0==x1 and y0==y1:break
     twice=error*2
     if twice>=dy:error+=dy;x0+=sx
     if twice<=dx:error+=dx;y0+=sy
    actual={}
    for i,(glyph,fg,bg,owner) in enumerate(s.render().words()):
     if owner==0x30000001:actual[(i%512,i//512)]=glyph-0x2800
    self.assertEqual(actual,expected)
 def test_large_prompt_row_preferences_keep_the_draft_visible(self):
  s=self.scene();s.command({'op':'prompt','active':True,'mode':'grow','minRows':120,'maxRows':1000});s.command({'op':'draft','text':'Retained large prompt','emitWeather':False});self.preserved(s)
  s.command({'op':'prompt','minRows':2147483647,'maxRows':2147483647});self.preserved(s)
  self.assertTrue(any(owner==0x40000000 for glyph,fg,bg,owner in s.render().words()))
 def test_wide_viewport_pointer_survives_snapshot_restore(self):
  s=self.scene();s.command({'op':'resize','width':1600,'height':20});s.command({'op':'pointer','phase':'down','x':1500,'y':10});self.preserved(s)
 def test_nonpositive_and_unrepresentable_integer_geometry_is_atomic(self):
  s=self.scene();s.command({'op':'widget','id':1,'kind':'box'})
  for command in [{'op':'widget','id':1,'width':0},{'op':'widget','id':1,'height':-1},{'op':'widget','id':1,'width':2.5},{'op':'widget','id':1,'x':2147483648}]:
   saved=s.snapshot()
   with self.assertRaises(ValueError):s.command(command)
   self.assertEqual(s.snapshot(),saved)
if __name__=='__main__':unittest.main()
