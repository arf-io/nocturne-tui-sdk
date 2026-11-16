"""Authored panel controls are inspectable without projection or clock edits."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class PanelMetadata(unittest.TestCase):
 def test_window_source_and_transition_epoch_survive_bound_geometry_edits(self):
  with NativeScene(42) as s:
   properties={'width':2000000000,'height':1000000000,'position':[1,2,3],
    'yaw':12,'pitch':13,'roll':14,'alpha':.6,'group':7,'title':'NOC 日本','text':'Retained source',
    'minColumns':30,'maxColumns':80,'anchorX':.2,'anchorY':.8,'overshoot':.3,
    'scatter':16,'bend':8,'folds':5,'meshColumns':12,'meshRows':10}
   s.command({'op':'window','id':1,'durationMs':1200,**properties})
   saved=s.snapshot();window=next(item for item in s.info()['windows'] if item['id']==1)
   for field,value in properties.items():self.assertEqual(window[field],value,field)
   self.assertEqual(window['durationUs'],1200000);self.assertEqual(window['atUs'],0)
   self.assertEqual(s.snapshot(),saved);s.restore(saved)
   self.assertEqual(next(item for item in s.info()['windows'] if item['id']==1),window)
   s.command({'op':'define','path':'/width','value':1234,'binding':{'family':'window','id':1,'field':'width'}})
   s.command({'op':'remove-value','path':'/width'})
   changed=next(item for item in s.info()['windows'] if item['id']==1)
   self.assertEqual(changed['width'],1234);self.assertEqual(changed['atUs'],0)
   self.assertEqual(changed['text'],'Retained source');self.assertEqual(window['width'],2000000000)
 def test_area_geometry_layout_and_timing_are_owned_and_pure(self):
  with NativeScene(42) as s:
   properties={'x':-2147483648,'y':2147483647,'width':2147483647,'height':2147483647,
    'padding':2,'margin':1,'alpha':.7,'hideEmpty':True,'speedX':12,'speedY':3,'layout':'queue'}
   s.command({'op':'area','id':1,'fadeMs':500,'gapMs':250,**properties})
   saved=s.snapshot();area=next(item for item in s.info()['areas'] if item['id']==1)
   for field,value in properties.items():self.assertEqual(area[field],value,field)
   self.assertEqual(area['fadeUs'],500000);self.assertEqual(area['gapUs'],250000)
   self.assertEqual(s.snapshot(),saved);s.restore(saved)
   self.assertEqual(next(item for item in s.info()['areas'] if item['id']==1),area)
   s.command({'op':'define','path':'/width','value':1234,'binding':{'family':'area','id':1,'field':'width'}})
   s.command({'op':'remove-value','path':'/width'})
   self.assertEqual(next(item for item in s.info()['areas'] if item['id']==1)['width'],1234)
   self.assertEqual(area['width'],2147483647)
if __name__=='__main__':unittest.main()
