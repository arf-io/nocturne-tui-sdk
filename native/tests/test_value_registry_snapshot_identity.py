"""ValueStore identity remains unique across checksum-correct imports."""
from pathlib import Path
import sys,unittest,struct,zlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class ValueRegistrySnapshotIdentity(unittest.TestCase):
 def test_duplicate_numeric_and_typed_paths_reject_atomically(self):
  for value in [2,True,'NOC',{'id':'noc-1'}]:
   with self.subTest(value=value),NativeScene(42) as s:
    s.command({'op':'define','path':'/first-identity','value':1});s.command({'op':'define','path':'/second-identity','value':value})
    good=s.snapshot();damaged=bytearray(good);offset=good.index(b'/second-identity\0')
    path=b'/first-identity';damaged[offset:offset+128]=path+b'\0'*(128-len(path))
    struct.pack_into('<I',damaged,20,zlib.crc32(damaged[24:]))
    with self.assertRaises(ValueError):s.restore(damaged)
    self.assertEqual(good,s.snapshot());self.assertEqual(len(s.info()['valueDescriptors']),2)
 def test_pending_batch_import_preserves_source_ownership_and_execution(self):
  with NativeScene(42) as s:
   s.command({'op':'define','path':'/source','value':3});s.command({'op':'define','path':'/out','value':0})
   s.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'batch','commands':[
    {'op':'set','path':'/out','expression':{'path':'/source'}},{'op':'set','path':'/source','value':4}]}})
   saved=s.snapshot();s.restore(saved);self.assertEqual(saved,s.snapshot())
   with self.assertRaises(ValueError):s.command({'op':'remove-value','path':'/source'})
   self.assertEqual(saved,s.snapshot());s.advance_to(500000)
   self.assertEqual(s.info()['values'],{'/source':4,'/out':3})
if __name__=='__main__':unittest.main()
