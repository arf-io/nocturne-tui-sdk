import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class VisualContracts(unittest.TestCase):
 def test_pie_respects_values_not_equal_voronoi_sectors(self):
  with NativeScene() as s:
   s.command({'op':'resize','width':120,'height':70});s.command({'op':'environment','stars':0})
   s.command({'op':'widget','id':1,'kind':'pie','x':10,'y':3,'width':90,'height':52,'data':[90,10],'padding':0,'alpha':0,'sampling':'cell'})
   f=s.render();colors=[s.oklch(.72,.09,180),s.oklch(.72,.09,259)];counts=[sum(1 for g,fg,bg,id in f.words() if g==0x2588 and fg==color) for color in colors]
   self.assertGreater(counts[0],counts[1]*7,counts)
   self.assertLess(counts[0],counts[1]*12,counts)
 def test_zero_pie_values_do_not_create_wedges(self):
  with NativeScene() as s:
   s.command({'op':'widget','id':1,'kind':'donut','x':5,'y':4,'width':35,'height':12,'data':[0,0]})
   self.assertFalse(any(g==0x2588 and id==0x30000001 for g,fg,bg,id in s.render().words()))
 def test_foreground_letters_inherit_weather_backdrop(self):
  with NativeScene() as a,NativeScene() as b:
   for s in (a,b):
    s.command({'op':'resize','width':80,'height':24});s.command({'op':'environment','stars':0});s.command({'op':'prompt','alpha':0})
    s.command({'op':'field','effect':'surface-field/silk-tide','x':6,'y':21,'lifeMs':6000,'speed':3,'strength':.8,'width':2});s.advance_to(800000)
   b.command({'op':'draft','text':'      ','emitWeather':False})
   a.command({'op':'draft','text':'abcdef','emitWeather':False})
   wa=a.render().words();wb=b.render().words()
   checked=0
   for i,(g,fg,bg,id) in enumerate(wa):
    if id==0x40000000 and 97<=g<=102:
     checked+=1;self.assertEqual(bg,wb[i][2]);self.assertEqual(fg,0xe4dacc)
   self.assertEqual(checked,6)
 def test_readable_window_measures_body_not_only_title(self):
  body='Perspective must preserve complete document lines.'
  with NativeScene()as s:
   s.command({'op':'resize','width':120,'height':42});s.command({'op':'camera','position':[0,8,30],'pitch':0});s.command({'op':'window','id':1,'title':'Short','text':body,'position':[0,8,0],'width':44,'height':18});s.advance_to(900000)
   f=s.render();words=f.words();rows=[''.join(chr(g)for g,_,_,_ in words[y*f.width:(y+1)*f.width])for y in range(f.height)]
   self.assertTrue(any(body in row for row in rows),'A short title must not force gratuitous midword body wrapping')
