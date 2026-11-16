"""Unexecuted scenic-batch contracts: shared-edge inventory transport."""
import ctypes as C, math, struct, sys, unittest, zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
TRIANGLES=[dict(a=[0,0,0],b=[1,0,0],c=[0,0,1],surfaceId=1),dict(a=[1,0,0],b=[1,0,1],c=[0,0,1],surfaceId=1)]
def seed(s):
 s.command(dict(op='floor',enabled=False));s.command(dict(op='surface',id=1,restitution=1,friction=0,settleSpeed=0))
 s.command(dict(op='mesh',triangles=TRIANGLES));s.command(dict(op='surface-foam',surfaceId=1,sourceRate=0,decay=0,impactGain=.001))
 s.command(dict(op='emitter',id=1,effect='weather/autumn-drift',count=1,runningTimeMs=0,shape='point',position=[.2,1,.2],velocity=[0,-240,0],extent=[0,0,0],spread=[0,0,0],gravity=[0,0,0],wind=[0,0,0],windVariation=[0,0,0],drag=0,lift=0,flutterHz=0,flutterAmount=0,tumble=[0,0,0],deposit=False,collision=True,lifetimeMinMs=10000,lifetimeMaxMs=10000,sizeMin=1,sizeMax=1,colliders={'surfaces':[1]}))
 s.advance_to(8333)
class FoamTransport(unittest.TestCase):
 def test_independent_square_flux_balance_and_replay(self):
  with NativeScene(2030) as s:
   seed(s);initial=s.surface_foam_transport(1);self.assertAlmostEqual(initial[0][1],.24,places=12);self.assertEqual(initial[1][1],0)
   s.command(dict(op='surface-foam-transport',surfaceId=1,velocity=[1,0]));saved=s.snapshot();s.advance_to(16666)
   rows=s.surface_foam_transport(1);amount=.24*2/120
   self.assertAlmostEqual(rows[0][1],.24-amount,places=12);self.assertAlmostEqual(rows[1][1],amount,places=12)
   self.assertAlmostEqual(rows[0][6],amount,places=12);self.assertAlmostEqual(rows[1][5],amount,places=12)
   for r in rows:self.assertAlmostEqual(r[2]+r[5],r[1]+r[3]+r[4]+r[6],places=12)
   end=s.snapshot();s.restore(saved);s.advance_to(16666);self.assertEqual(s.snapshot(),end)
   before=s.snapshot();owned=s.surface_foam_transport(1);owned[0][1]=99;s.render();s.info();s.surface_foam_transport(1);self.assertEqual(s.snapshot(),before)
 def test_high_speed_positivity_closed_boundary_and_reverse(self):
  with NativeScene(2030) as s:
   seed(s);s.command(dict(op='surface-foam-transport',surfaceId=1,velocity=[1000,1000]));s.advance_to(16666)
   rows=s.surface_foam_transport(1);self.assertAlmostEqual(rows[0][1],0,places=12);self.assertAlmostEqual(rows[1][1],.24,places=12)
   s.advance_to(25000);self.assertAlmostEqual(s.surface_foam_transport(1)[1][1],.24,places=12)
   s.command(dict(op='surface-foam-transport',surfaceId=1,velocity=[-1000,-1000]));s.advance_to(33333)
   rows=s.surface_foam_transport(1);self.assertAlmostEqual(rows[0][1],.24,places=12);self.assertAlmostEqual(rows[1][1],0,places=12)
 def test_clear_mesh_and_disabled_source_lifetimes(self):
  with NativeScene(2030) as s:
   seed(s);s.command(dict(op='surface-foam',surfaceId=1,enabled=False));s.command(dict(op='surface-foam-transport',surfaceId=1,velocity=[1,0]));s.advance_to(16666)
   self.assertGreater(s.surface_foam_transport(1)[1][5],0)
   s.command(dict(op='clear-surface-foam',surfaceId=1));self.assertTrue(all(r[1:]==[0]*6 for r in s.surface_foam_transport(1)))
   s.command(dict(op='mesh',triangles=TRIANGLES));self.assertTrue(all(r[1:]==[0]*6 for r in s.surface_foam_transport(1)))
 def test_invalid_authoring_and_short_query_are_atomic(self):
  with NativeScene(2030) as s:
   seed(s);before=s.snapshot()
   for patch in [dict(velocity=[1]),dict(velocity=[1,0,0]),dict(velocity=[1001,0]),dict(velocity=[True,0]),dict(velocity=[1,0],unknown=1),dict(surfaceId=2,velocity=[1,0])]:
    with self.subTest(patch=patch),self.assertRaises(ValueError):s.command(dict(op='surface-foam-transport',surfaceId=1,**{k:v for k,v in patch.items() if k!='surfaceId'}) if 'surfaceId' not in patch else dict(op='surface-foam-transport',**patch))
    self.assertEqual(before,s.snapshot())
   s.surface_foam_transport(1);out=(C.c_double*14)(*([123]*14));fn=s._lib.nrSurfaceFoamTransport
   self.assertEqual(fn(s._context,1,None,0),2);self.assertEqual(fn(s._context,1,out,1),-1);self.assertEqual(list(out),[123]*14)
 def test_schema32_promotes_existing_typed_values_and_pending_formulas(self):
  with NativeScene(2030) as s:
   seed(s);s.command(dict(op='define',path='/flag',value=True));s.command(dict(op='define',path='/n',value=1))
   s.command(dict(op='schedule',id=1,atUs=16666,command=dict(op='set',path='/n',expression={'path':'/n'})))
   data=bytearray(s.snapshot()[:24+12499168]);struct.pack_into('<I',data,28,0x20261032);struct.pack_into('<III',data,12,0x20261032,12499168,zlib.crc32(data[24:]))
   s.restore(data);self.assertTrue(s.info()['values']['/flag']);self.assertEqual(s.surface_foam_transport(1)[0][5:],[0,0]);s.advance_to(16666)
 def test_checksum_correct_negative_transfer_rejects(self):
  with NativeScene(2030) as s:
   seed(s);before=s.snapshot();data=bytearray(before);struct.pack_into('<d',data,24+12499168+256,-1);struct.pack_into('<I',data,20,zlib.crc32(data[24:]))
   with self.assertRaises(ValueError):s.restore(data)
   self.assertEqual(s.snapshot(),before)

 def test_destination_saturation_is_an_explicit_loss_not_generation(self):
  with NativeScene(2030) as s:
   seed(s);data=bytearray(s.snapshot());cell=24+4788952+16*48+32
   struct.pack_into('<dd',data,cell,.9,.9);struct.pack_into('<I',data,20,zlib.crc32(data[24:]));s.restore(data)
   s.command(dict(op='surface-foam-transport',surfaceId=1,velocity=[1000,1000]));s.advance_to(16666);rows=s.surface_foam_transport(1)
   self.assertAlmostEqual(rows[0][1],0,places=12);self.assertEqual(rows[1][1],1);self.assertAlmostEqual(rows[1][4],.14,places=12)
   self.assertAlmostEqual(sum(r[2] for r in rows),sum(r[1]+r[3]+r[4] for r in rows),places=12)
 def test_nonmanifold_and_vertical_mesh_changes_reject_atomically(self):
  with NativeScene(2030) as s:
   seed(s);s.command(dict(op='surface-foam-transport',surfaceId=1,velocity=[1,0]));before=s.snapshot()
   for triangles in [TRIANGLES+[dict(a=[1,0,0],b=[2,0,2],c=[0,0,1],surfaceId=1)],[dict(a=[0,0,0],b=[0,1,0],c=[0,0,1],surfaceId=1)]]:
    with self.assertRaises(ValueError):s.command(dict(op='mesh',triangles=triangles))
    self.assertEqual(s.snapshot(),before)
 def test_velocity_binding_has_public_command_oracle(self):
  with NativeScene(2030) as s,NativeScene(2030) as oracle:
   for scene in [s,oracle]:seed(scene)
   rows=s.surface_foam_transport(1);s.command(dict(op='define',path='/drift',value=1,binding=dict(family='surface-foam',id=1,field='velocity.x')))
   self.assertEqual(s.surface_foam_transport(1),rows);s.command(dict(op='remove-value',path='/drift'));oracle.command(dict(op='surface-foam-transport',surfaceId=1,velocity=[1,0]))
   self.assertEqual(s.snapshot(),oracle.snapshot());s.advance_to(16666);oracle.advance_to(16666);self.assertEqual(s.snapshot(),oracle.snapshot())
 def test_schema32_cannot_smuggle_new_scheduled_transport(self):
  with NativeScene(2030) as s:
   seed(s);s.command(dict(op='schedule',id=1,atUs=16666,command=dict(op='surface-foam-transport',surfaceId=1,velocity=[1,0])))
   before=s.snapshot();data=bytearray(before[:24+12499168]);struct.pack_into('<I',data,28,0x20261032);struct.pack_into('<III',data,12,0x20261032,12499168,zlib.crc32(data[24:]))
   with self.assertRaises(ValueError):s.restore(data)
   self.assertEqual(s.snapshot(),before)
