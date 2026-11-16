import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
from native.tests.current_writer_contract import current_schema, snapshot_size
import math,struct,zlib,unittest
from nocturne_native import NativeScene
CMD=dict(op='field',x=10,y=5,width=1,speed=8,strength=.7,lifeMs=4000,material=0)
def smooth(p):return p*p*(3-2*p)
def oracle(n,t,x,y):
 age=t/1e6;band=2;d=math.hypot(2*(x-10),4*(y-5));radius=16*age
 return max([smooth(max(0,1-abs(d-radius+4*band*k)/band))/(1+.42*k) for k in range(n)])*smooth(1-age/4)*.7
def old(b):
 b=bytearray(b[:13497408]);struct.pack_into('<I',b,16,len(b)-24);struct.pack_into('<I',b,12,0x20261047);struct.pack_into('<I',b,28,0x20261047);struct.pack_into('<I',b,20,zlib.crc32(b[24:]));return b
class SoftFronts(unittest.TestCase):
 def test_independent_fronts_and_purity(self):
  for n in [1,3,16]:
   with NativeScene() as s:
    s.command({**CMD,'rings':n})
    for t in [0,250000,1000000,2000000,3999000]:
     s.advance_to(t);before=s.snapshot()
     for x,y in [(10,5),(10.25,5),(12,5),(14,5),(18,5),(22,5),(10,8)]:self.assertAlmostEqual(s.field_sample(1,x,y)[0],oracle(n,t,x,y),delta=2e-6)
     s.render();self.assertEqual(before,s.snapshot())
 def test_invalid_atomic_and_owned_replay(self):
  with NativeScene() as s:
   for n in [0,17,-1,1.5,'3',True]:
    before=s.snapshot()
    with self.assertRaises(ValueError):s.command({**CMD,'rings':n})
    self.assertEqual(before,s.snapshot())
   s.command({**CMD,'rings':3});b=s.snapshot();s.advance_to(1000000);end=s.snapshot();s.restore(b);s.advance_to(1000000);self.assertEqual(end,s.snapshot())
 def test_schema47_preserved_and_rejects_new_payload(self):
  with NativeScene() as s:
   s.command(CMD);before=s.render();s.restore(old(s.snapshot()));self.assertEqual(before,s.render());self.assertEqual(struct.unpack_from('<I',s.snapshot(),12)[0],current_schema())
   s.command({**CMD,'rings':3});b=s.snapshot()
   with self.assertRaises(ValueError):s.restore(old(b))
   self.assertEqual(b,s.snapshot())
 def test_queued_old_schema_guard(self):
  with NativeScene() as s:
   s.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'batch','commands':[{**CMD,'rings':3}]}});b=s.snapshot()
   with self.assertRaises(ValueError):s.restore(old(b))
   self.assertEqual(b,s.snapshot())
 def test_binding_and_inner_ring_visible_in_real_frame(self):
  with NativeScene() as s:
   s.command({'op':'environment','stars':0,'background':0,'style':'solid','sampling':'cell'});s.command({'op':'prompt','active':False});s.command({'op':'resize','width':40,'height':15})
   s.command({'op':'material','id':2,'space':'rgb','channels':{'r':1,'g':0,'b':0}});s.command({**CMD,'rings':1,'material':2});s.advance_to(1000000)
   self.assertEqual(s.render().words()[5*40+10][2],0)
   s.command({'op':'define','path':'/rings','value':3,'binding':{'family':'field','id':1,'field':'rings'}})
   self.assertEqual(s.info()['fields'][0]['rings'],3);self.assertGreater(s.render().words()[5*40+10][2],0)
   before=s.snapshot()
   for value in [0,17,1.5]:
    with self.assertRaises(ValueError):s.command({'op':'set','path':'/rings','value':value})
    self.assertEqual(before,s.snapshot())
