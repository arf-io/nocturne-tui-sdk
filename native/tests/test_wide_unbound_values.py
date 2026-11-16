"""Real numeric storage domains, attachment and historical semantic validation."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
from native.tests.current_writer_contract import current_schema, snapshot_size
import struct,sys,unittest,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
CURRENT=current_schema()
def old_schema(data,schema):
    data=bytearray(data[:13548744]);struct.pack_into('<I',data,16,len(data)-24);struct.pack_into('<I',data,12,schema);struct.pack_into('<I',data,28,schema)
    struct.pack_into('<I',data,20,zlib.crc32(data[24:]));return data

class WideUnboundValues(unittest.TestCase):
    def test_wide_direct_expression_and_readonly_sources_are_pure_and_replayable(self):
        with NativeScene(42) as scene:
            scene.command({'op':'define','path':'/source','value':1e12,'readonly':True})
            scene.command({'op':'define','path':'/out','value':0})
            scene.command({'op':'set','path':'/out','expression':{'negate':{'path':'/source'}}})
            self.assertEqual(scene.info()['values'],{'/source':1e12,'/out':-1e12})
            before=scene.snapshot();self.assertEqual(struct.unpack_from('<I',before,12)[0],CURRENT)
            scene.render();scene.info_complete();self.assertTrue(before==scene.snapshot())
            scene.advance_to(500000);expected=scene.snapshot();scene.restore(before);scene.advance_to(500000)
            self.assertTrue(scene.snapshot()==expected)

    def test_supported_wide_properties_attach_detach_and_keep_resource_bounds(self):
        for base,binding,value in [
            ({'op':'environment','background':0},{'family':'environment','id':0,'field':'background'},0xffffff),
            ({'op':'material','id':3,'space':'rgb'},{'family':'material','id':3,'field':'alpha.seed'},4294967295),
            ({'op':'widget','id':1,'kind':'text','text':'wide'},{'family':'widget','id':1,'field':'width'},2147483647)]:
            with self.subTest(binding=binding),NativeScene(42) as scene:
                scene.command(base);scene.command({'op':'define','path':'/control','value':value})
                scene.command({'op':'bind','path':'/control','binding':binding})
                scene.command({'op':'bind','path':'/control','binding':None})
                self.assertEqual(scene.info()['values']['/control'],value)
                self.assertIsNone(scene.info()['valueDescriptors']['/control']['binding'])
                before=scene.snapshot()
                with self.assertRaises(ValueError):scene.command({'op':'bind','path':'/control','binding':{'family':'accessibility','id':0,'field':'screenReader'}})
                self.assertTrue(scene.snapshot()==before)

    def test_outside_domain_readonly_and_batch_failures_reject_atomically(self):
        with NativeScene(42) as scene:
            scene.command({'op':'define','path':'/out','value':7})
            scene.command({'op':'define','path':'/locked','value':1e12,'readonly':True})
            for command in [
                {'op':'set','path':'/out','value':1e12+1},
                {'op':'set','path':'/out','expression':{'multiply':[1e12,2]}},
                {'op':'set','path':'/locked','value':0},
                {'op':'batch','commands':[{'op':'set','path':'/out','value':0xffffff},{'op':'set','path':'/locked','value':0}]}]:
                before=scene.snapshot()
                with self.subTest(command=command),self.assertRaises(ValueError):scene.command(command)
                self.assertTrue(scene.snapshot()==before)

    def test_schema55_preserves_original_unbound_rejection_before_promotion(self):
        with NativeScene(42) as scene:
            scene.command({'op':'define','path':'/out','value':7});old=old_schema(scene.snapshot(),0x20261055)
            scene.restore(old);self.assertEqual(scene.info()['values']['/out'],7)
            self.assertEqual(struct.unpack_from('<I',scene.snapshot(),12)[0],CURRENT)
            scene.command({'op':'set','path':'/out','value':1000001});before=scene.snapshot()
            for schema in (0x20261055,0x20261054):
                with self.subTest(schema=schema),self.assertRaises(ValueError):scene.restore(old_schema(before,schema))
                self.assertTrue(scene.snapshot()==before)

    def test_old_pending_domain_rejects_new_unbound_but_keeps_valid_wide_binding(self):
        for bound in (False,True):
            with self.subTest(bound=bound),NativeScene(42) as scene:
                scene.command({'op':'environment','background':0})
                define={'op':'define','path':'/out','value':0}
                if bound:define['binding']={'family':'environment','id':0,'field':'background'}
                scene.command(define)
                value=0xffffff if bound else 1000001
                scene.command({'op':'schedule','id':1,'atUs':1000000,'command':{'op':'set','path':'/out','value':value}})
                before=scene.snapshot();legacy=old_schema(before,0x20261055)
                if bound:
                    scene.restore(legacy);scene.advance_to(1000000)
                    self.assertEqual(scene.info()['values']['/out'],value)
                else:
                    with self.assertRaises(ValueError):scene.restore(legacy)
                    self.assertTrue(scene.snapshot()==before)
