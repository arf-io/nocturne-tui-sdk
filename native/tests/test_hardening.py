import unittest,ctypes as C,json,sys,struct,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class Hardening(unittest.TestCase):
 def setUp(self):self.s=NativeScene()
 def tearDown(self):self.s.close()
 def test_duplicate_decoded_keys_and_bad_unicode(self):
  for raw in [b'{"op":"reset","op":"input"}',b'{"op":"input","text":"\\ud800"}',b'{"op":"input","text":"\\u0000"}',b'{"op":"reset","se\\u0065d":1,"seed":2}',b'{"op":"time","timeUs":1e999}',b'{"op":"reset"} trailing',b'{"op":"input","text":"\xc0\xaf"}']:
   old=self.s.snapshot()
   with self.assertRaises(ValueError):self.s.command_raw(raw)
   self.assertEqual(old,self.s.snapshot())
 def test_unknown_field_nested(self):
  for cmd in [{'op':'material','channels':{'x':3}},{'op':'material','alpha':{'initial':1,'foo':3}},{'op':'flight','steps':[{'kind':'turn','durationMs':1000,'wat':3}]}]:
   before=self.s.snapshot()
   with self.assertRaises(ValueError):self.s.command(cmd)
   self.assertEqual(before,self.s.snapshot())
 def test_failed_trigger_atomic(self):
  for cmd in [{'op':'define','path':'/heat','value':0},{'op':'define','path':'/color','value':30,'binding':{'family':'material','id':1,'field':'hue'}},{'op':'trigger','id':1,'source':'/heat','target':'/color','threshold':10,'value':999}]:self.s.command(cmd)
  before=self.s.snapshot()
  with self.assertRaises(ValueError):self.s.command({'op':'set','path':'/heat','value':11})
  self.assertEqual(before,self.s.snapshot())
 def test_catchup_and_pause(self):
  self.assertEqual(self.s.command({'op':'time','timeUs':1000000,'budget':1}),1)
  self.assertEqual(self.s.info()['clock']['step'],1)
  self.s.advance_to(1000000)
  self.assertEqual(self.s.info()['clock']['step'],120)
  self.s.command({'op':'pause','paused':True});self.s.command({'op':'time','timeUs':2000000});self.assertEqual(self.s.info()['clock']['timeUs'],1000000)
 def test_full_capacity_reject_preserves_draft(self):
  self.s.command({'op':'prompt','presentation':'framed','maxChars':2048})
  self.s.command({'op':'draft','text':'x'*2048,'emitWeather':False});before=self.s.snapshot()
  with self.assertRaises(ValueError):self.s.command({'op':'input','text':'y'})
  self.assertEqual(before,self.s.snapshot())
 def test_look_does_not_brake_flight(self):
  self.s.command({'op':'flight','steps':[{'kind':'turn','durationMs':5000,'speed':8,'yaw':90,'bank':25}]});self.s.advance_to(1000000)
  a=self.s.info()['camera']['position'];self.s.command({'op':'look','yaw':35});self.s.advance_to(2000000)
  self.assertTrue(self.s.info()['camera']['flightActive']);self.assertNotEqual(a,self.s.info()['camera']['position'])
 def test_back_to_front_drag(self):
  for yaw in (0,180):
   self.s.command({'op':'reset'});self.s.command({'op':'camera','position':[0,8,40 if yaw==0 else -40],'yaw':yaw,'pitch':0});self.s.command({'op':'window','id':1,'title':'Window','text':'Readable','position':[0,8,0]});self.s.advance_to(1000000)
   f=self.s.render();cells=f.words();points=[(i%f.width,i//f.width) for i,c in enumerate(cells) if c[3]==0x20000001];self.assertTrue(points)
   x,y=points[len(points)//2];before=self.s.info()['windows'][0]['position'];self.s.command({'op':'pointer','phase':'down','x':x,'y':y});self.s.command({'op':'pointer','phase':'move','x':x+4,'y':y});after=self.s.info()['windows'][0]['position'];self.assertGreater((after[0]-before[0])*(1 if yaw==0 else -1),0)
 def test_graph_retarget_does_not_snap(self):
  for i in range(1,4):self.s.command({'op':'node','id':i,'label':f'Complete node {i}','position':[i*15,0,0]})
  self.s.command({'op':'select','id':1,'durationMs':1000});self.s.advance_to(300000);before=self.s.info()['nodes']
  self.s.command({'op':'select','id':2,'durationMs':1000});after=self.s.info()['nodes'];self.assertEqual([n['position'] for n in before],[n['position'] for n in after]);self.assertEqual(self.s.info()['selection'],2)
 def test_compositing_alpha_identity(self):
  for blend in range(28):
   self.assertEqual(self.s.composite(0x123456,0xeeaa99,65535,0,blend)[0],0x123456)
  self.assertEqual(self.s.composite(0xffffff,0x123456,65535,65535,0),(0x123456,65535))
  self.assertEqual(self.s.composite(0xffffff,0x123456,65535,65535,0,1),(0,0))
 def test_invalid_snapshot_schema(self):
  b=bytearray(self.s.snapshot());b[12]^=1;before=self.s.snapshot()
  with self.assertRaises(ValueError):self.s.restore(b)
  self.assertEqual(before,self.s.snapshot())
