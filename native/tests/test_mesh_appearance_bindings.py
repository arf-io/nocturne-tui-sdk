"""Appearance edits preserve mesh topology and accumulated scenic state."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
TRIANGLES=[{'a':[-10,0,-10],'b':[10,0,-10],'c':[0,0,10],'surfaceId':1,'color':0x123456,'alpha':.6},
 {'a':[10,0,-10],'b':[20,0,-10],'c':[10,0,10],'surfaceId':1,'color':0x654321,'alpha':.3}]
class MeshAppearanceBindings(unittest.TestCase):
 def test_bound_and_direct_appearance_preserve_foam_ledger_and_replay(self):
  for family,identity,field,value,edit in [
   ('mesh',0,'alpha',.2,{'alpha':.2}),('mesh',0,'color',0xabcdef,{'color':0xabcdef}),
   ('mesh',0,'sampling',2,{'sampling':'braille'}),
   ('triangle',1,'alpha',.2,{'triangleIndex':1,'alpha':.2}),
   ('triangle',1,'color',0xabcdef,{'triangleIndex':1,'color':0xabcdef})]:
   with self.subTest(family=family,field=field),NativeScene(42) as s,NativeScene(42) as oracle:
    for scene in [s,oracle]:
     for command in [{'op':'surface','id':1},{'op':'mesh','triangles':TRIANGLES},
      {'op':'surface-waves','surfaceId':1,'waves':[[1,1,0,0,0]]},{'op':'surface-foam','surfaceId':1,'curvatureThreshold':0}]:scene.command(command)
     scene.advance_to(250000)
    ledger=s.surface_foam(1)
    s.command({'op':'define','path':'/appearance','value':value,'binding':{'family':family,'id':identity,'field':field}})
    oracle.command({'op':'mesh-style',**edit});self.assertEqual(s.surface_foam(1),ledger)
    s.command({'op':'remove-value','path':'/appearance'});self.assertEqual(s.snapshot(),oracle.snapshot())
    start=s.snapshot();s.advance_to(1000000);finish=s.snapshot();s.render();self.assertEqual(finish,s.snapshot())
    s.restore(start);s.advance_to(1000000);self.assertEqual(finish,s.snapshot())
 def test_frames_match_independently_imported_authored_triangles(self):
  import copy
  for edit in [{'alpha':.2},{'color':0xabcdef},{'triangleIndex':1,'alpha':.2},{'sampling':'braille'}]:
   with self.subTest(edit=edit),NativeScene(42) as s,NativeScene(42) as oracle:
    expected=copy.deepcopy(TRIANGLES)
    targets=[edit['triangleIndex']] if 'triangleIndex' in edit else range(len(expected))
    for index in targets:
     for field in ['alpha','color']:
      if field in edit:expected[index][field]=edit[field]
    for scene,triangles in [(s,TRIANGLES),(oracle,expected)]:
     scene.command({'op':'surface','id':1});scene.command({'op':'mesh','triangles':triangles,**({'sampling':edit['sampling']} if scene is oracle and 'sampling' in edit else {})})
    s.command({'op':'mesh-style',**edit})
    self.assertEqual(s.render().bytes,oracle.render().bytes)
 def test_removed_index_requires_explicit_rebinding(self):
  with NativeScene(42) as s:
   s.command({'op':'surface','id':1});s.command({'op':'mesh','triangles':TRIANGLES})
   s.command({'op':'define','path':'/triangle','value':.5,'binding':{'family':'triangle','id':1,'field':'alpha'}})
   s.command({'op':'mesh','triangles':TRIANGLES[:1]});before=s.snapshot()
   with self.assertRaises(ValueError):s.command({'op':'set','path':'/triangle','value':.8})
   self.assertEqual(before,s.snapshot())
   s.command({'op':'bind','path':'/triangle','binding':{'family':'triangle','id':0,'field':'alpha'}})
 def test_invalid_appearance_rejects_atomically(self):
  with NativeScene(42) as s:
   s.command({'op':'surface','id':1});s.command({'op':'mesh','triangles':TRIANGLES})
   for edit in [{'alpha':2},{'triangleIndex':2,'alpha':.5},{'triangleIndex':0,'sampling':'braille'},{'color':.5},{},{'alpha':.5,'color':-1}]:
    before=s.snapshot()
    with self.subTest(edit=edit),self.assertRaises(ValueError):s.command({'op':'mesh-style',**edit})
    self.assertEqual(before,s.snapshot())
if __name__=='__main__':unittest.main()
