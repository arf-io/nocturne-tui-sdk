"""Numeric bindings behave like public authored edits, including bounds/ownership."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class ValueAddressing(unittest.TestCase):
 def test_camera_scalar_bindings_match_authored_pose_and_projection(self):
  fields=[('position.x',12,'position',[12,6,30]),('position.y',9,'position',[0,9,30]),('position.z',25,'position',[0,6,25]),('yaw',20,'yaw',20),('pitch',-15,'pitch',-15),('roll',30,'roll',30),('near',.5,'near',.5),('far',150,'far',150),('fov',50,'fov',50),('span',30,'span',30),('orthographic',1,'orthographic',True)]
  for field,value,key,expected in fields:
   with self.subTest(field=field),NativeScene(42) as actual,NativeScene(42) as reference:
    base=[{'op':'camera','position':[0,6,30],'yaw':0,'pitch':0,'roll':0,'near':.1,'far':200,'fov':70,'span':40,'orthographic':False},{'op':'mesh','triangles':[{'a':[-8,-4,0],'b':[0,8,0],'c':[8,-4,0],'color':0x45bbce}]}]
    for s in (actual,reference):
     for command in base:s.command(command)
    actual.command({'op':'define','path':'/control','value':value,'binding':{'family':'camera','field':field}})
    reference.command({'op':'camera',key:expected})
    self.assertEqual(actual.render().bytes,reference.render().bytes)
    self.assertEqual(actual.info()['camera'],reference.info()['camera'])
    self.assertEqual(actual.info()['camera'][key],expected)
 def test_widget_numeric_geometry_matches_authored_controls(self):
  for field,value in [('x',12),('y',14),('width',28),('height',6),('padding',1),('min',-.5),('max',2),('mode',2),('pulseMs',400),('cellAspect',3),('innerRadius',.7),('startAngle',45),('sweepAngle',200)]:
   with self.subTest(field=field),NativeScene(42) as actual,NativeScene(42) as reference:
    command={'op':'widget','id':1,'kind':'donut','x':8,'y':10,'width':32,'height':12,'data':[2,3,5],'alpha':.8,'value':.5}
    for s in (actual,reference):s.command(command)
    actual.command({'op':'define','path':'/control','value':value,'binding':{'family':'widget','id':1,'field':field}})
    reference.command({'op':'widget','id':1,field:value})
    actual.advance_to(500000);reference.advance_to(500000)
    self.assertEqual(actual.render().bytes,reference.render().bytes)
    self.assertEqual(actual.info()['widgets'],reference.info()['widgets'])
 def test_invalid_ranges_and_missing_fields_reject_atomically(self):
  with NativeScene() as s:
   s.command({'op':'widget','id':1,'kind':'button'})
   for family,field,value in [('camera','pitch',90),('camera','fov',151),('camera','far',.1),('camera','orthographic',.5),('widget','width',2.5),('widget','max',0),('widget','innerRadius',.5),('widget','sweepAngle',20),('widget','unknown',2)]:
    before=s.snapshot()
    with self.subTest(field=field),self.assertRaises(ValueError):s.command({'op':'define','path':'/bad','value':value,'binding':{'family':family,'id':1 if family=='widget' else 0,'field':field}})
    self.assertEqual(s.snapshot(),before)
 def test_trigger_target_failure_rolls_back_source_and_camera(self):
  with NativeScene() as s:
   s.command({'op':'define','path':'/control','value':60,'binding':{'family':'camera','field':'fov'}})
   s.command({'op':'define','path':'/alarm','value':0})
   s.command({'op':'trigger','id':1,'source':'/alarm','threshold':0,'target':'/control','value':200})
   before=s.snapshot()
   with self.assertRaises(ValueError):s.command({'op':'set','path':'/alarm','value':1})
   self.assertEqual(s.snapshot(),before)
 def test_pose_binding_captures_flight_and_position_rejects_owned_path(self):
  with NativeScene() as s:
   s.command({'op':'flight','steps':[{'kind':'cruise','durationMs':2000,'speed':5}]});s.advance_to(1000000)
   pose=s.info()['camera']['position']
   s.command({'op':'define','path':'/yaw','value':30,'binding':{'family':'camera','field':'yaw'}})
   self.assertEqual(s.info()['camera']['position'],pose);self.assertFalse(s.info()['camera']['flightActive'])
   s.command({'op':'path-travel','id':1,'target':{'family':'camera','id':0},'points':[[0,0,0],[4,0,0]],'speed':1})
   before=s.snapshot()
   with self.assertRaises(ValueError):s.command({'op':'define','path':'/position','value':2,'binding':{'family':'camera','field':'position.x'}})
   self.assertEqual(s.snapshot(),before)
 def test_bound_update_persists_and_render_is_pure(self):
  with NativeScene() as s:
   s.command({'op':'define','path':'/projection','value':60,'binding':{'family':'camera','field':'fov'}})
   s.command({'op':'set','path':'/projection','value':80});saved=s.snapshot();s.render();self.assertEqual(s.snapshot(),saved)
   s.command({'op':'set','path':'/projection','value':100});s.restore(saved);s.command({'op':'set','path':'/projection','value':80});self.assertEqual(s.snapshot(),saved)
if __name__=='__main__':unittest.main()
