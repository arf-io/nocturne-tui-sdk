"""Real registered circuit appearance and retained ownership contracts."""
import unittest,struct,zlib
from test_electrical_graphs import arc
from nocturne_native import NativeScene

def register(s):
    s.command({'op':'state-register','id':21,'path':'/alarms/circuit','role':'alarm',
               'target':{'family':'electrical-arc','id':7}})
def entry(s):return next(q for q in s.info_complete()['registeredStates'] if q['id']==21)
def rule(s, **style):
    s.command({'op':'style-rule','id':1,'selector':{'family':'electrical-arc','role':'alarm'},'style':style})
class ElectricalSelectors(unittest.TestCase):
    def test_reversible_override_changes_real_frame_but_preserves_authored_circuit(self):
        with NativeScene() as s:
            s.command(arc());register(s);s.advance_to(700000)
            circuit=s.info_complete()['electricalArcs'];before=s.render().bytes
            rule(s,alpha=0);saved=s.snapshot()
            self.assertEqual(entry(s)['authored']['alpha'],.8)
            self.assertEqual(entry(s)['effective']['alpha'],0)
            self.assertNotEqual(s.render().bytes,before)
            self.assertEqual(s.info_complete()['electricalArcs'],circuit)
            self.assertEqual(s.snapshot(),saved)
            s.command({'op':'remove-style-rule','id':1})
            self.assertEqual(s.render().bytes,before)
    def test_removed_target_becomes_dormant_then_same_id_reactivates(self):
        with NativeScene() as s:
            s.command(arc());register(s);rule(s,alpha=.25)
            s.command({'op':'remove-electrical-arc','id':7})
            self.assertFalse(entry(s)['exists'])
            s.command(arc());self.assertTrue(entry(s)['exists'])
            self.assertEqual(entry(s)['effective']['alpha'],.25)
            s.command({'op':'state-update','id':21,'active':False})
            self.assertEqual(entry(s)['effective']['alpha'],.8)
    def test_inapplicable_properties_and_missing_targets_are_atomic(self):
        with NativeScene() as s:
            s.command(arc());register(s)
            for style in ({'sampling':'pixel'},{'surfaceAlpha':.5},{'alpha':2},{'color':42}):
                saved=s.snapshot()
                with self.subTest(style=style),self.assertRaises(ValueError):rule(s,**style)
                self.assertEqual(s.snapshot(),saved)
            saved=s.snapshot()
            with self.assertRaises(ValueError):
                s.command({'op':'state-register','id':22,'path':'/missing','role':'alarm',
                           'target':{'family':'electrical-arc','id':0}})
            self.assertEqual(s.snapshot(),saved)
    def test_historical54_cannot_carry_circuit_registration(self):
        with NativeScene() as s:
            s.command(arc());register(s);saved=s.snapshot();old=bytearray(saved)
            for off in (12,28):struct.pack_into('<I',old,off,0x20261054)
            struct.pack_into('<I',old,20,zlib.crc32(old[24:])&0xffffffff)
            with self.assertRaises(ValueError):s.restore(old)
            self.assertEqual(s.snapshot(),saved)
