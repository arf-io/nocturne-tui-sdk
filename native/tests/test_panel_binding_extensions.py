"""Panel enumeration and hierarchy controls use public-command semantics."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class PanelExtensions(unittest.TestCase):
 def test_controls_match_public_authoring(self):
  cases=[('widget',{'op':'widget','id':1,'kind':'progress'},'border',3,'double'),
   ('widget',{'op':'widget','id':1,'kind':'progress'},'sampling',2,'braille'),
   ('widget',{'op':'widget','id':1,'kind':'progress'},'revealMs',1200,1200),
   ('window',{'op':'window','id':1},'border',3,'double'),
   ('window',{'op':'window','id':1},'shape',2,'ellipse'),
   ('window',{'op':'window','id':1},'group',2,2),
   ('area',{'op':'area','id':1},'border',3,'double'),
   ('area',{'op':'area','id':1},'layout',1,'queue')]
  for family,base,field,value,authored in cases:
   with self.subTest(family=family,field=field),NativeScene(42) as s,NativeScene(42) as oracle:
    for scene in [s,oracle]:scene.command(base);scene.advance_to(250000)
    s.command({'op':'define','path':'/control','value':value,'binding':{'family':family,'id':1,'field':field}})
    oracle.command({'op':family,'id':1,field:authored});s.command({'op':'remove-value','path':'/control'})
    self.assertEqual(s.snapshot(),oracle.snapshot())
    for time in [500000,1000000,2000000]:
     s.advance_to(time);oracle.advance_to(time);self.assertEqual(s.render().bytes,oracle.render().bytes)
 def test_parent_assignment_rejects_missing_self_and_cycles_atomically(self):
  with NativeScene(42) as s:
   s.command({'op':'area','id':1});s.command({'op':'area','id':2,'parent':1})
   for target in [1,2,99]:
    before=s.snapshot()
    with self.subTest(target=target),self.assertRaises(ValueError):s.command({'op':'define','path':'/parent','value':target,'binding':{'family':'area','id':1,'field':'parent'}})
    self.assertEqual(s.snapshot(),before)
   s.command({'op':'define','path':'/parent','value':1,'binding':{'family':'area','id':2,'field':'parent'}})
 def test_plot_and_polygon_applicability_rejects_atomically(self):
  with NativeScene(42) as s:
   s.command({'op':'widget','id':1,'kind':'button'});s.command({'op':'window','id':1})
   for family,field,value in [('widget','sampling',2),('widget','revealMs',1000),('window','shape',11)]:
    before=s.snapshot()
    with self.subTest(field=field),self.assertRaises(ValueError):s.command({'op':'define','path':'/bad','value':value,'binding':{'family':family,'id':1,'field':field}})
    self.assertEqual(before,s.snapshot())
if __name__=='__main__':unittest.main()
