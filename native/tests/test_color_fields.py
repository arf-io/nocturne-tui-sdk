"""Real C color fields: independent analytic curve, lifecycle and ABI boundaries."""
import ctypes as C,math,struct,zlib,unittest
from nocturne_native import NativeScene
BASE={'op':'field','x':10,'y':5,'width':3,'speed':2,'strength':.7,'lifeMs':4000,'seed':71}
def intensity(cmd,t,x,y):
 age=t/1e6;rect=cmd.get('surface');cx=cmd.get('x',10)+age*cmd.get('velocity',[0,0])[0]+(rect['x'] if rect else 0);cy=cmd.get('y',5)+age*cmd.get('velocity',[0,0])[1]+(rect['y'] if rect else 0)
 if rect and not(rect['x']<=x<rect['x']+rect['width'] and rect['y']<=y<rect['y']+rect['height']):return 0,cx,cy
 band=cmd.get('width',3)*2;dist=math.hypot(2*(x-cx),4*(y-cy));continuous=cmd.get('continuous',False);d=dist-(0 if continuous else 2*age*cmd.get('speed',2))
 if abs(d)>5*band:return 0,cx,cy
 angle=(dist-2*age*cmd.get('speed',2))/(band+.01)*cmd.get('frequency',100)-age*90+cmd.get('phase',0)
 a=math.radians(angle);mix=cmd.get('interference',0);wave=(1-mix)*(.5+.5*math.cos(a))+mix*(.5+.5*math.cos(2*a+math.radians(cmd.get('seed',71)%360)))
 return (.2+.8*wave)*cmd.get('strength',.7)/(1+abs(d/band)**cmd.get('falloff',2))*(1 if continuous else 1-age/(cmd.get('lifeMs',4000)/1000)),cx,cy
def legacy(blob,schema=0x20261046):
 b=bytearray(blob[:13478976]);struct.pack_into('<I',b,12,schema);struct.pack_into('<I',b,28,schema);struct.pack_into('<I',b,16,len(b)-24);struct.pack_into('<I',b,20,zlib.crc32(b[24:])&0xffffffff);return b
class ColorFields(unittest.TestCase):
 def test_independent_equations_every_control_and_purity(self):
  for patch in [{},{'continuous':True},{'falloff':1},{'falloff':8},{'frequency':0},{'frequency':237,'phase':-71},{'interference':.8},{'velocity':[3,-2]},{'surface':{'x':8,'y':3,'width':20,'height':15},'x':4,'y':6}]:
   with self.subTest(patch=patch),NativeScene() as s:
    command={**BASE,**patch};s.command(command)
    for t in [0,500000,1500000]:
     s.advance_to(t);before=s.snapshot()
     for x,y in [(10,5),(13,7),(17,8),(2,1),(80,40)]:
      row=s.field_sample(1,x,y);oracle,cx,cy=intensity(command,t,x,y);self.assertAlmostEqual(row[0],oracle,delta=2e-6);self.assertAlmostEqual(row[2],cx);self.assertAlmostEqual(row[3],cy)
     s.render();self.assertEqual(s.snapshot(),before)
 def test_default_explicit_controls_and_legacy_preserve_frame(self):
  with NativeScene() as a,NativeScene() as b:
   a.command(BASE);b.command({**BASE,'continuous':False,'falloff':2,'frequency':100,'phase':0,'interference':0,'velocity':[0,0]})
   for t in [0,333333,1700000]:
    a.advance_to(t);b.advance_to(t);self.assertEqual(a.render().bytes,b.render().bytes)
   before=a.snapshot();frame=a.render().bytes;a.restore(legacy(before));self.assertEqual(a.render().bytes,frame);self.assertEqual(a.snapshot()[32:13478976],before[32:13478976])
 def test_continuous_lifetime_remove_clear_and_slot_reuse(self):
  with NativeScene() as s:
   s.command({**BASE,'continuous':True,'lifeMs':1});s.command(BASE);s.advance_to(5000000);self.assertIsNotNone(s.field_sample(1,10,5));self.assertIsNone(s.field_sample(2,10,5));s.command({'op':'remove-field','id':1});self.assertIsNone(s.field_sample(1,10,5));s.command(BASE);s.advance_to(10000000);self.assertIsNone(s.field_sample(3,10,5));s.command({**BASE,'continuous':True});s.command({'op':'clear','scope':'weather'});self.assertIsNone(s.field_sample(4,10,5))
 def test_invalid_controls_and_remove_atomic(self):
  bad=[{'falloff':x} for x in [0,9,2.5,'two']]+[{'frequency':x} for x in [-1,1001]]+[{'phase':3601},{'interference':1.1},{'continuous':1},{'velocity':[1]},{'velocity':[0,101]},{'surface':{'x':0,'y':0,'width':0,'height':10}},{'surface':{'x':0,'y':0,'width':10,'height':10,'bad':1}},{'surface':{'x':0,'width':10,'height':10}}]
  with NativeScene() as s:
   s.command(BASE);before=s.snapshot()
   for patch in bad:
    with self.subTest(patch=patch),self.assertRaises(ValueError):s.command({**BASE,**patch})
    self.assertEqual(s.snapshot(),before)
   for id in [0,999,1.5]:
    with self.assertRaises(ValueError):s.command({'op':'remove-field','id':id})
    self.assertEqual(s.snapshot(),before)
 def test_material_alpha_color_render_and_surface_clip(self):
  with NativeScene() as s,NativeScene() as background:
   for scene in [s,background]:
    scene.command({'op':'environment','stars':0,'background':0,'style':'solid','sampling':'cell'});scene.command({'op':'prompt','active':False});scene.command({'op':'resize','width':40,'height':15})
   s.command({'op':'material','id':2,'space':'rgb','channels':{'r':1,'g':0,'b':0},'alpha':.25});cmd={**BASE,'material':2,'continuous':True,'surface':{'x':8,'y':3,'width':20,'height':10},'x':5,'y':3};s.command(cmd)
   row=s.field_sample(1,13,6);self.assertEqual(row[1],0xff0000);self.assertAlmostEqual(row[0],intensity(cmd,0,13,6)[0]*.25,delta=2e-6);self.assertEqual(s.field_sample(1,7,6)[0],0);self.assertEqual(s.field_sample(1,28,6)[0],0)
   actual=s.render().words();empty=background.render().words();self.assertNotEqual(actual,empty)
   for i,(a,b) in enumerate(zip(actual,empty)):
    if not (8<=i%40<28 and 3<=i//40<13):self.assertEqual(a,b)
   s.command({'op':'material','id':2,'alpha':0});self.assertEqual(s.field_sample(1,13,6)[0],0);self.assertEqual(s.render().bytes,background.render().bytes)
 def test_all_new_value_bindings_and_invalid_rollback(self):
  cases=[('continuous',True),('falloff',4),('frequency',72),('phase',90),('interference',.3),('velocity.x',3),('velocity.y',-2),('material',0)]
  for field,value in cases:
   with self.subTest(field=field),NativeScene() as s:
    s.command(BASE);s.command({'op':'define','path':'/control','value':value,'binding':{'family':'field','id':1,'field':field}});meta=s.info()['fields'][0];actual=meta['velocity'][0 if field.endswith('x') else 1] if field.startswith('velocity.') else meta[field];self.assertEqual(actual,value);before=s.snapshot()
    with self.assertRaises(ValueError):s.command({'op':'set','path':'/control','value':-10000})
    self.assertEqual(s.snapshot(),before)
 def test_schedule_partition_old_feature_guard_and_corruption(self):
  with NativeScene() as s:
   s.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'batch','commands':[{**BASE,'continuous':True,'phase':45}]}});start=s.snapshot();s.advance_to(900000);done=s.snapshot();s.restore(start)
   for t in [100000,499999,500000,700000,900000]:s.advance_to(t)
   self.assertEqual(s.snapshot(),done)
   with self.assertRaises(ValueError):s.restore(legacy(start))
   self.assertEqual(s.snapshot(),done)
   corrupt=bytearray(done);struct.pack_into('<I',corrupt,13478976,2);struct.pack_into('<I',corrupt,20,zlib.crc32(corrupt[24:])&0xffffffff)
   with self.assertRaises(ValueError):s.restore(corrupt)
   self.assertEqual(s.snapshot(),done)
 def test_real_C_owned_output_invalid_absent_alias_and_alignment(self):
  with NativeScene() as s:
   s.command(BASE);fn=s._lib.nrFieldSample;fn.argtypes=[C.c_void_p,C.c_uint32,C.c_double,C.c_double,C.c_void_p,C.c_uint32];fn.restype=C.c_int;out=(C.c_double*4)(*([99]*4));before=s.snapshot()
   for id,x,y,capacity in [(0,0,0,4),(1,float('nan'),0,4),(1,0,float('inf'),4),(1,0,0,3)]:self.assertEqual(fn(s._context,id,x,y,out,capacity),-1);self.assertEqual(list(out),[99]*4)
   self.assertEqual(fn(s._context,123,0,0,out,4),0);self.assertEqual(list(out),[99]*4);self.assertEqual(fn(s._context,1,0,0,C.byref(out,1),4),-1);self.assertEqual(fn(s._context,1,0,0,s._context,4),-1);self.assertEqual(s.snapshot(),before)
   row=s.field_sample(1,10,5);row[0]=-99;self.assertGreater(s.field_sample(1,10,5)[0],0)
 def test_surface_value_bindings_discovery_and_old_queued_binding_guard(self):
  for field,value in [('surface.x',2),('surface.y',3),('surface.width',40),('surface.height',12)]:
   with self.subTest(field=field),NativeScene() as s:
    s.command({**BASE,'surface':{'x':0,'y':0,'width':20,'height':10}});s.command({'op':'define','path':'/uv','value':value,'binding':{'family':'field','id':1,'field':field}});self.assertEqual(s.info()['fields'][0]['surface'][field.split('.')[1]],value)
    contract=s.info()['contract']['queryContracts']['nrFieldSample'];self.assertEqual(contract['rowWords'],4);self.assertTrue(contract['pure']);self.assertEqual(contract['coordinates'],'screen-cells')
  with NativeScene() as s:
   s.command(BASE);s.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'define','path':'/frequency','value':80,'binding':{'family':'field','id':1,'field':'frequency'}}});before=s.snapshot()
   with self.assertRaises(ValueError):s.restore(legacy(before))
   self.assertEqual(s.snapshot(),before)
if __name__=='__main__':unittest.main()
