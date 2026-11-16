"""Authored widget inspection supports host reconciliation without rendering."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class WidgetMetadata(unittest.TestCase):
 def test_full_series_and_signed_geometry_boundaries_are_pure_and_atomic(self):
  with NativeScene(42) as s:
   data=[-1000000 if index%2 else 1000000 for index in range(128)]
   s.command({'op':'widget','id':1,'kind':'bars','x':-2147483648,'y':2147483647,
    'width':2147483647,'height':2147483647,'data':data})
   saved=s.snapshot();widget=s.info()['widgets'][0]
   self.assertEqual(widget['data'],data);self.assertEqual(widget['x'],-2147483648)
   self.assertEqual(widget['y'],2147483647);self.assertEqual(widget['width'],2147483647)
   self.assertEqual(widget['height'],2147483647);self.assertEqual(s.snapshot(),saved)
   for change in [{'width':0},{'height':2147483648},{'x':-2147483649},{'y':.5},
    {'alpha':1.01},{'data':[0]*129},{'data':[1000001]}]:
    with self.subTest(change=change):
     with self.assertRaises(ValueError):s.command({'op':'widget','id':1,**change})
     self.assertEqual(s.snapshot(),saved);self.assertEqual(s.info()['widgets'][0],widget)
   s.command({'op':'widget','id':1,'data':[]});self.assertEqual(s.info()['widgets'][0]['data'],[])
   self.assertEqual(widget['data'],data)
 def test_authored_properties_roundtrip_bind_teardown_and_owned_query(self):
  with NativeScene(42) as s:
   properties={'x':-123,'y':456,'width':2000000000,'height':1000000000,'padding':2,
    'material':3,'backgroundMaterial':4,'alpha':.75,'enabled':False,'selected':True,
    'active':True,'min':-2,'max':5,'mode':3,'text':'NOC 日本','value':.5,'data':[1,2,4]}
   s.command({'op':'widget','id':1,'kind':'donut','border':'heavy','pulseMs':250,**properties})
   saved=s.snapshot();info=s.info()['widgets'][0]
   for key,value in properties.items():self.assertEqual(info[key],value,key)
   self.assertEqual(info['border'],4);self.assertEqual(info['kind'],9);self.assertEqual(info['pulseUs'],250000)
   self.assertEqual(s.snapshot(),saved);s.restore(saved);self.assertEqual(s.info()['widgets'][0],info)
   s.command({'op':'define','path':'/alpha','value':.6,'binding':{'family':'widget','id':1,'field':'alpha'}})
   s.command({'op':'remove-value','path':'/alpha'});self.assertEqual(s.info()['widgets'][0]['alpha'],.6)
   self.assertEqual(info['alpha'],.75)
   s.command({'op':'widget','id':1,'data':[9]});self.assertEqual(info['data'],[1,2,4])
   self.assertEqual(s.info()['widgets'][0]['data'],[9])
if __name__=='__main__':unittest.main()
