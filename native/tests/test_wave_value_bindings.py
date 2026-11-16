"""Wave coefficient edits retain the surface and match public wave configuration."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class WaveValueBindings(unittest.TestCase):
 def test_every_coefficient_matches_public_wave_replacement(self):
  initial=[[1,.2,.3,2,.4],[.5,.1,.2,1,.3]]
  for index in range(2):
   for member,name in enumerate(['amplitude','kx','kz','omega','phase']):
    with self.subTest(index=index,name=name),NativeScene(42) as s,NativeScene(42) as oracle:
     for scene in [s,oracle]:
      scene.command({'op':'surface','id':1});scene.command({'op':'mesh','triangles':[{'a':[-10,0,-10],'b':[10,0,-10],'c':[0,0,10],'surfaceId':1}]})
      scene.command({'op':'surface-waves','surfaceId':1,'waves':initial});scene.advance_to(250000)
     expected=[row[:] for row in initial];expected[index][member]=.75
     s.command({'op':'define','path':'/wave','value':.75,'binding':{'family':'surface-wave','id':1,'field':f'waves.{index}.{name}'}})
     oracle.command({'op':'surface-waves','surfaceId':1,'waves':expected});s.command({'op':'remove-value','path':'/wave'})
     self.assertEqual(s.snapshot(),oracle.snapshot())
     start=s.snapshot();s.advance_to(1000000);oracle.advance_to(1000000);self.assertEqual(s.snapshot(),oracle.snapshot())
     finish=s.snapshot();s.render();self.assertEqual(finish,s.snapshot());s.restore(start);s.advance_to(1000000);self.assertEqual(finish,s.snapshot())
 def test_capacity_missing_index_and_noncanonical_fields_reject_atomically(self):
  with NativeScene(42) as s:
   s.command({'op':'surface','id':1});s.command({'op':'surface-waves','surfaceId':1,'waves':[[128,0,0,0,0],[128,0,0,0,0]]})
   for field,value in [('waves.0.amplitude',129),('waves.2.phase',1),('waves.00.phase',1),('waves.-1.phase',1),('waves.0.unknown',1)]:
    before=s.snapshot()
    with self.subTest(field=field),self.assertRaises(ValueError):s.command({'op':'define','path':'/bad','value':value,'binding':{'family':'surface-wave','id':1,'field':field}})
    self.assertEqual(before,s.snapshot())
 def test_removed_index_rejects_until_explicit_rebinding(self):
  with NativeScene(42) as s:
   s.command({'op':'surface','id':1});s.command({'op':'surface-waves','surfaceId':1,'waves':[[1,0,0,0,0],[1,0,0,0,0]]})
   s.command({'op':'define','path':'/wave','value':1,'binding':{'family':'surface-wave','id':1,'field':'waves.1.amplitude'}})
   s.command({'op':'surface-waves','surfaceId':1,'waves':[[1,0,0,0,0]]});before=s.snapshot()
   with self.assertRaises(ValueError):s.command({'op':'set','path':'/wave','value':.5})
   self.assertEqual(before,s.snapshot())
   s.command({'op':'bind','path':'/wave','binding':{'family':'surface-wave','id':1,'field':'waves.0.amplitude'}})
   s.command({'op':'set','path':'/wave','value':.5});self.assertEqual(s.info()['values']['/wave'],.5)
if __name__=='__main__':unittest.main()
