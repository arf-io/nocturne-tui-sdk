"""Authored, unexecuted scenic-batch contracts for actual fluid-volume geometry."""
import ctypes as C, math, struct, sys, unittest,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene

def setup(s,tail=0,delay=0):
 s.command(dict(op='floor',enabled=False));s.command(dict(op='surface',id=1,restitution=1,friction=0,settleSpeed=0))
 s.command(dict(op='ribbon',points=[[0,0,-2],[0,0,0]],width=2,surfaceId=1))
 s.command(dict(op='flow',id=1,flux=2,stages=[dict(name='channel',tailUs=tail,delayUs=delay)]))
 s.command(dict(op='flow-surface',surfaceId=1,flowId=1,stage='channel',referenceFlux=2))
 s.command(dict(op='flow-thickness',surfaceId=1,width=2,speed=2,maxDepth=1,direction=[0,1,0]))
class FlowThickness(unittest.TestCase):
 def test_actual_closed_volume_and_independent_cross_section(self):
  with NativeScene() as s:
   setup(s);sample=s.flow_thickness(1);self.assertAlmostEqual(sample[0],2);self.assertAlmostEqual(sample[1],.5);self.assertAlmostEqual(sample[2],1)
   rows=s.surface_triangles(1);self.assertEqual(len(rows),12)
   ys=[r[k] for r in rows for k in [2,5,8]];self.assertEqual(min(ys),0);self.assertEqual(max(ys),.5)
   # Signed tetrahedral volume is checked against footprint area * depth.
   volume=0
   for r in rows:
    a,b,c=r[1:4],r[4:7],r[7:10]
    volume+=sum(a[k]*(b[(k+1)%3]*c[(k+2)%3]-b[(k+2)%3]*c[(k+1)%3]) for k in range(3))/6
   self.assertAlmostEqual(abs(volume),2,places=10)
 def test_delay_tail_stop_purity_and_replay(self):
  with NativeScene() as s:
   setup(s,tail=1000000,delay=250000);self.assertEqual(s.flow_thickness(1)[1],0)
   s.advance_to(1250000);self.assertAlmostEqual(s.flow_thickness(1)[1],.5*(1-math.exp(-1)),places=10)
   before=s.snapshot();s.surface_triangles(1);s.render();s.info();self.assertEqual(s.snapshot(),before)
   s.command(dict(op='flow-rate',id=1,flux=0));saved=s.snapshot();s.advance_to(2500000);end=s.snapshot();self.assertAlmostEqual(s.flow_thickness(1)[1],.5*(math.exp(-1)-math.exp(-2.25)),places=10)
   s.restore(saved);s.advance_to(2500000);self.assertEqual(s.snapshot(),end)
 def test_geometry_ownership_capacity_and_removal(self):
  with NativeScene() as s:
   setup(s);before=s.snapshot()
   for command in [dict(op='mesh',triangles=[]),dict(op='flow-thickness',surfaceId=1,width=2,speed=2,maxDepth=1),dict(op='remove-flow-surface',surfaceId=1),dict(op='flow-rate',id=1,flux=5)]:
    with self.assertRaises(ValueError):s.command(command)
    self.assertEqual(s.snapshot(),before)
   s.command(dict(op='remove-flow-thickness',surfaceId=1));self.assertIsNone(s.flow_thickness(1));self.assertEqual(len(s.surface_triangles(1)),2)
   s.command(dict(op='remove-flow-surface',surfaceId=1));s.command(dict(op='mesh',triangles=[]))
 def test_particle_hits_top_face_at_actual_depth(self):
  with NativeScene() as s:
   setup(s)
   s.command(dict(op='emitter',id=1,effect='weather/autumn-drift',count=1,runningTimeMs=0,shape='point',position=[0,1,-1],velocity=[0,-240,0],extent=[0,0,0],spread=[0,0,0],gravity=[0,0,0],wind=[0,0,0],windVariation=[0,0,0],drag=0,lift=0,flutterHz=0,flutterAmount=0,tumble=[0,0,0],deposit=False,collision=True,lifetimeMinMs=10000,lifetimeMaxMs=10000,sizeMin=.1,sizeMax=.1,colliders={'surfaces':[1]}))
   s.advance_to(8333);p=s.particles()[0];self.assertAlmostEqual(p[7]/65536,240,delta=2/65536);self.assertAlmostEqual(p[4]/65536,2.001,delta=2/65536)
 def test_schema33_restores_without_new_volume_ownership(self):
  with NativeScene() as s:
   s.command(dict(op='define',path='/flag',value=True));data=bytearray(s.snapshot()[:24+12503520]);struct.pack_into('<I',data,28,0x20261033);struct.pack_into('<III',data,12,0x20261033,12503520,zlib.crc32(data[24:]));s.restore(data)
   self.assertTrue(s.info()['values']['/flag']);self.assertIsNone(s.flow_thickness(1))

 def test_invalid_dimension_direction_and_short_buffers_are_atomic(self):
  with NativeScene() as s:
   setup(s);before=s.snapshot();s.flow_thickness(1);s.surface_triangles(1)
   out=(C.c_double*12)(*([123]*12));fn=s._lib.nrFlowThickness
   self.assertEqual(fn(s._context,1,out,5),-1);self.assertEqual(list(out),[123]*12)
   fn=s._lib.nrSurfaceTriangles;self.assertEqual(fn(s._context,1,None,0),12);self.assertEqual(fn(s._context,1,out,1),-1);self.assertEqual(list(out),[123]*12)
   for command in [dict(op='surface-waves',surfaceId=1,waves=[[1,1,0,0,0]]),dict(op='flow-thickness',surfaceId=2,width=0,speed=2,maxDepth=1,direction=[0,0,0])]:
    with self.assertRaises(ValueError):s.command(command)
    self.assertEqual(s.snapshot(),before)
 def test_checksum_correct_bad_owned_vertex_weight_rejects(self):
  with NativeScene() as s:
   setup(s);before=s.snapshot();bad=bytearray(before);struct.pack_into('<I',bad,24+12503520+16*56+4,2);struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]))
   with self.assertRaises(ValueError):s.restore(bad)
   self.assertEqual(s.snapshot(),before)
 def test_older_schema_cannot_smuggle_new_scheduled_command(self):
  with NativeScene() as s:
   s.command(dict(op='surface',id=1));s.command(dict(op='ribbon',points=[[0,0,-2],[0,0,0]],width=2,surfaceId=1));s.command(dict(op='flow',id=1,flux=2,stages=[dict(name='channel')]))
   s.command(dict(op='flow-surface',surfaceId=1,flowId=1,stage='channel',referenceFlux=2));s.command(dict(op='schedule',id=1,atUs=500000,command=dict(op='flow-thickness',surfaceId=1,width=2,speed=2,maxDepth=1)))
   before=s.snapshot();data=bytearray(before[:24+12503520]);struct.pack_into('<I',data,28,0x20261033);struct.pack_into('<III',data,12,0x20261033,12503520,zlib.crc32(data[24:]))
   with self.assertRaises(ValueError):s.restore(data)
   self.assertEqual(s.snapshot(),before)

 def test_rising_volume_hits_a_stationary_particle_with_relative_velocity(self):
  with NativeScene() as s:
   setup(s,tail=10000)
   s.command(dict(op='emitter',id=1,effect='weather/autumn-drift',count=1,runningTimeMs=0,shape='point',position=[0,.1,-1],velocity=[0,0,0],extent=[0,0,0],spread=[0,0,0],gravity=[0,0,0],wind=[0,0,0],windVariation=[0,0,0],drag=0,lift=0,flutterHz=0,flutterAmount=0,tumble=[0,0,0],deposit=False,collision=True,lifetimeMinMs=10000,lifetimeMaxMs=10000,sizeMin=.1,sizeMax=.1,colliders={'surfaces':[1]}))
   s.advance_to(8333);depth=.5*(1-math.exp(-.8333));p=s.particles()[0]
   self.assertAlmostEqual(p[7]/65536,2*120*depth,delta=3/65536);self.assertAlmostEqual(p[4]/65536,2*depth-.099,delta=3/65536)
 def test_buoyancy_uses_upper_face_instead_of_prism_bottom(self):
  with NativeScene() as s:
   setup(s);s.command(dict(op='float-body',id=1,surfaceId=1,position=[0,0,-1],radius=.1,mass=1000,gravity=0,drag=0));s.advance_to(8333)
   self.assertAlmostEqual(s.float_body(1)[9],1,places=12)
 def test_shared_lip_components_have_independent_closed_volume_oracles(self):
  with NativeScene() as s:
   for ident in [1,2]:s.command(dict(op='surface',id=ident))
   s.command(dict(op='ribbon',points=[[0,3,-2],[0,3,0]],width=2,surfaceId=1));s.command(dict(op='flow',id=1,flux=2,stages=[dict(name='channel'),dict(name='sheet')]))
   s.command(dict(op='waterfall',channelSurfaceId=1,sheetSurfaceId=2,flowId=1,channelStage='channel',sheetStage='sheet',referenceFlux=2,drop=3))
   ledger=s.info()['flows']
   for surface,speed,direction in [(1,2,[0,1,0]),(2,4,[0,0,-1])]:s.command(dict(op='flow-thickness',surfaceId=surface,width=2,speed=speed,maxDepth=1,direction=direction))
   self.assertEqual(s.info()['flows'],ledger)
   for surface,expected in [(1,2),(2,1.5)]:
    volume=0
    for row in s.surface_triangles(surface):
     a,b,c=row[1:4],row[4:7],row[7:10]
     volume+=sum(a[k]*(b[(k+1)%3]*c[(k+2)%3]-b[(k+2)%3]*c[(k+1)%3]) for k in range(3))/6
    self.assertAlmostEqual(abs(volume),expected,places=10)

 def test_serial_equal_reservoir_flux_drives_geometry_and_matches_ledger(self):
  def response(t):return 0 if t<=0 else 1-math.exp(-t)*(1+t)
  with NativeScene() as s:
   s.command(dict(op='surface',id=1));s.command(dict(op='ribbon',points=[[0,0,-2],[0,0,0]],width=2,surfaceId=1))
   s.command(dict(op='flow',id=1,flux=2,stages=[dict(name='first',delayUs=250000,tailUs=1000000),dict(name='second',delayUs=125000,tailUs=1000000),dict(name='third')]))
   s.command(dict(op='flow-surface',surfaceId=1,flowId=1,stage='third',referenceFlux=2));s.command(dict(op='flow-thickness',surfaceId=1,width=2,speed=2,maxDepth=1))
   for time in [0,375000,500000,1375000]:
    s.advance_to(time);sample=s.flow_thickness(1);expected=2*response(time/1000000-.375)
    self.assertAlmostEqual(sample[0],expected,places=10);self.assertAlmostEqual(sample[0],s.info()['flows'][0]['stages'][2]['flux'],delta=5.1e-7)
    rows=s.surface_triangles(1)
    if sample[1]>0:self.assertAlmostEqual(max(r[k] for r in rows for k in (2,5,8)),expected/4,places=10)
    else:self.assertEqual(rows,[])
   s.command(dict(op='flow-rate',id=1,flux=0));saved=s.snapshot();s.advance_to(2750000);sample=s.flow_thickness(1)
   self.assertAlmostEqual(sample[0],2*(response(2.375)-response(1)),places=10);self.assertAlmostEqual(sample[0],s.info()['flows'][0]['stages'][2]['flux'],delta=5.1e-7)
   after=s.snapshot();s.render();s.flow_thickness(1);s.surface_triangles(1);self.assertEqual(after,s.snapshot());s.restore(saved);s.advance_to(2750000);self.assertEqual(after,s.snapshot())

 def test_hydraulic_settings_edit_without_rebuilding_owned_mesh(self):
  with NativeScene() as s:
   setup(s);ids=[r[0] for r in s.surface_triangles(1)];ledger=s.info()['flows'];foam=s.surface_foam_transport(1)
   s.command(dict(op='flow-thickness-settings',surfaceId=1,width=4,speed=1));sample=s.flow_thickness(1)
   self.assertEqual(sample,[2,.5,2,4,1,1]);self.assertEqual([r[0] for r in s.surface_triangles(1)],ids);self.assertEqual(s.info()['flows'],ledger);self.assertEqual(s.surface_foam_transport(1),foam)
   s.command(dict(op='flow-thickness-settings',surfaceId=1,speed=2));self.assertEqual(s.flow_thickness(1)[1],.25)
   before=s.snapshot()
   for command in [dict(op='flow-thickness-settings',surfaceId=1),dict(op='flow-thickness-settings',surfaceId=1,width=.1),dict(op='flow-thickness-settings',surfaceId=1,speed=0),dict(op='flow-thickness-settings',surfaceId=1,width=4,direction=[0,1,0])]:
    with self.assertRaises(ValueError):s.command(command)
    self.assertEqual(s.snapshot(),before)
 def test_hydraulic_settings_pending_missing_target_is_recoverable(self):
  with NativeScene() as s:
   setup(s);s.command(dict(op='schedule',id=1,atUs=500000,command=dict(op='flow-thickness-settings',surfaceId=1,width=4)))
   s.command(dict(op='remove-flow-thickness',surfaceId=1));blocked=s.snapshot();s.restore(blocked)
   with self.assertRaises(ValueError):s.advance_to(500000)
   self.assertEqual(s.snapshot(),blocked);s.restore(blocked);s.command(dict(op='cancel-schedule',id=1));s.advance_to(500000)

 def test_hydraulic_surface_bindings_addressability_and_dormant_recovery(self):
  with NativeScene() as s:
   setup(s)
   for field,value in [('width',4),('speed',1)]:s.command(dict(op='define',path='/'+field,value=value,binding=dict(family='surface',id=1,field='thickness.'+field)))
   self.assertEqual(s.flow_thickness(1),[2,.5,2,4,1,1]);s.command(dict(op='set',path='/speed',value=2));self.assertEqual(s.flow_thickness(1)[1],.25)
   before=s.snapshot()
   with self.assertRaises(ValueError):s.command(dict(op='set',path='/width',value=.1))
   self.assertEqual(s.snapshot(),before)
   old=bytearray(before[:24+12508512]);struct.pack_into('<I',old,28,0x20261034);struct.pack_into('<III',old,12,0x20261034,12508512,zlib.crc32(old[24:]))
   with self.assertRaises(ValueError):s.restore(old)
   self.assertEqual(s.snapshot(),before)
   s.command(dict(op='schedule',id=1,atUs=500000,command=dict(op='set',path='/width',value=8)));s.command(dict(op='remove-flow-thickness',surfaceId=1));blocked=s.snapshot();s.restore(blocked)
   with self.assertRaises(ValueError):s.advance_to(500000)
   self.assertEqual(s.snapshot(),blocked);s.restore(blocked);s.command(dict(op='cancel-schedule',id=1));s.command(dict(op='bind',path='/width',binding=None));s.command(dict(op='set',path='/width',value=8));s.advance_to(500000)

 def test_hydraulic_bindings_match_public_command_oracle_through_replay(self):
  with NativeScene(19) as s,NativeScene(19) as oracle:
   for scene in [s,oracle]:setup(scene)
   for field in ['width','speed']:s.command(dict(op='define',path='/'+field,value=2,binding=dict(family='surface',id=1,field='thickness.'+field)))
   for time,width,speed in [(250000,4,1),(500000,8,2),(750000,2,2)]:
    for scene in [s,oracle]:scene.advance_to(time)
    s.command(dict(op='batch',commands=[dict(op='set',path='/width',value=width),dict(op='set',path='/speed',value=speed)]));oracle.command(dict(op='flow-thickness-settings',surfaceId=1,width=width,speed=speed))
    self.assertEqual(s.flow_thickness(1),oracle.flow_thickness(1));self.assertEqual(s.surface_triangles(1),oracle.surface_triangles(1));self.assertEqual(s.info()['flows'],oracle.info()['flows'])
   start=s.snapshot();s.advance_to(1000000);finish=s.snapshot();s.restore(start);s.advance_to(1000000);self.assertEqual(s.snapshot(),finish)
   oracle.advance_to(1000000)
   for field in ['width','speed']:s.command(dict(op='remove-value',path='/'+field))
   self.assertEqual(s.snapshot(),oracle.snapshot())

 def testVolumeAppendAndRetirementAccountWaterAndThermalInventories(self):
  with NativeScene() as s:
   s.command(dict(op='surface',id=1));s.command(dict(op='ribbon',points=[[0,0,-2],[0,0,0]],width=2,surfaceId=1));s.command(dict(op='flow',id=1,flux=2,stages=[dict(name='channel')]));s.command(dict(op='flow-surface',surfaceId=1,flowId=1,stage='channel',referenceFlux=2))
   s.command(dict(op='surface-water',surfaceId=1,capacity=1,evaporationUs=1000000));s.command(dict(op='surface-water-add',triangleIndex=0,volume=.5))
   s.command(dict(op='surface-thermal',triangleIndex=0,temperature=400,capacity=2,power=4));s.command(dict(op='surface-thermal',triangleIndex=1,temperature=300,capacity=2));s.command(dict(op='surface-thermal-link',id=1,fromTriangle=0,toTriangle=1,conductance=3));s.advance_to(500000)
   water=s.water_sample(0);thermal=[s.thermal_sample(i) for i in range(2)];start=s.snapshot()
   s.command(dict(op='flow-thickness',surfaceId=1,width=2,speed=2,maxDepth=1));self.assertEqual(s.water_sample(0),water);self.assertEqual([s.thermal_sample(i) for i in range(2)],thermal);self.assertEqual(len(s.info()['thermalLinks']),1)
   s.command(dict(op='remove-flow-thickness',surfaceId=1));info=s.info();self.assertAlmostEqual(info['surfaceWater'][0]['exportedVolume'],.5*math.exp(-.5),places=6);self.assertAlmostEqual(info['surfaceThermal']['exportedEnergy'],1402,places=5);self.assertNotIn('thermalLinks',info)
   self.assertIsNone(s.thermal_sample(0));self.assertEqual(s.water_sample(0)[1:7],[0,0,0,0,0,0]);finish=s.snapshot();s.restore(start)
   s.command(dict(op='flow-thickness',surfaceId=1,width=2,speed=2,maxDepth=1));s.command(dict(op='remove-flow-thickness',surfaceId=1));self.assertEqual(s.snapshot(),finish)
