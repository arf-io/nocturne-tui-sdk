"""Real retained resource controls; independent public authoring is the oracle."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
from native.tests.current_writer_contract import current_schema, snapshot_size
import unittest
import struct, zlib
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"bindings/python"))
from nocturne_native import NativeScene
from test_firework_stages import emitter
from test_electrical_graphs import arc

BURST = {'glitterHz':30, 'glitterDepth':.2, 'coreAlpha':.3,
         'residualMs':350.125, 'residualAlpha':.4}
ELECTRICAL = {'speed':20, 'jitter':.5, 'alpha':.4, 'flicker':.2,
              'delayMs':50.125, 'holdMs':150.125, 'fadeMs':250.125,
              'repeatMs':3000.125}

def bind(scene, family, ident, field, value):
    scene.command({'op':'define','path':'/control','value':value,
                   'binding':{'family':family,'id':ident,'field':field}})

class ResourceAnimationBindings(unittest.TestCase):
    def test_burst_controls_match_direct_edits_without_replacing_living_particles(self):
        for field, value in BURST.items():
            with self.subTest(field=field), NativeScene(42) as scene, NativeScene(42) as oracle:
                for s in (scene, oracle):
                    s.command(emitter(count=8)); s.advance_to(250000)
                particles = scene.particles()
                bind(scene, 'emitter', 1, field, value)
                oracle.command({'op':'burst-style','id':1,field:value})
                self.assertEqual(scene.particles(), particles)
                scene.command({'op':'remove-value','path':'/control'})
                self.assertEqual(scene.snapshot(), oracle.snapshot())
                for clock in (500000, 1000000):
                    scene.advance_to(clock); oracle.advance_to(clock)
                    self.assertEqual(scene.snapshot(), oracle.snapshot())
                    self.assertEqual(scene.render().bytes, oracle.render().bytes)

    def test_burst_invalid_values_and_wrong_algorithm_roll_back(self):
        for effect in ('weather/chrysanthemum','weather/rain-threads'):
            with NativeScene() as scene:
                scene.command(emitter(effect=effect))
                bad = [('glitterHz',61), ('glitterDepth',-1), ('coreAlpha',2),
                       ('residualAlpha',-1), ('residualMs',0), ('residualMs',.0005)]
                if effect == 'weather/rain-threads': bad += list(BURST.items())
                for field, value in bad:
                    saved = scene.snapshot()
                    with self.subTest(effect=effect,field=field,value=value), self.assertRaises(ValueError):
                        bind(scene,'emitter',1,field,value)
                    self.assertEqual(scene.snapshot(),saved)

    def test_electrical_controls_match_independent_authoring_at_same_epoch(self):
        for field, value in ELECTRICAL.items():
            with self.subTest(field=field), NativeScene(42) as scene, NativeScene(42) as oracle:
                scene.command(arc()); oracle.command(arc(**{field:value}))
                bind(scene,'electrical-arc',7,field,value)
                scene.command({'op':'remove-value','path':'/control'})
                self.assertEqual(scene.snapshot(),oracle.snapshot())
                for clock in (200000,700000,2000000,3500000):
                    scene.advance_to(clock); oracle.advance_to(clock)
                    self.assertEqual(scene.snapshot(),oracle.snapshot())
                    self.assertEqual(scene.render().bytes,oracle.render().bytes)

    def test_electrical_live_alpha_edit_preserves_leader_epoch_and_replays(self):
        with NativeScene() as scene:
            scene.command(arc()); scene.advance_to(700000)
            before = scene.info_complete()['electricalArcs'][0]
            bind(scene,'electrical-arc',7,'alpha',.4)
            after = scene.info_complete()['electricalArcs'][0]
            self.assertEqual(after['segments'],before['segments'])
            self.assertEqual(after['phase'],before['phase'])
            self.assertAlmostEqual(after['opacity'],before['opacity']/2)
            start = scene.snapshot(); scene.advance_to(1850000)
            end = scene.snapshot(); frame = scene.render().bytes
            scene.restore(start)
            for clock in (900000,1200000,1850000): scene.advance_to(clock)
            self.assertEqual(scene.snapshot(),end)
            self.assertEqual(scene.render().bytes,frame)

    def test_electrical_invalid_and_coupled_repeat_changes_roll_back(self):
        with NativeScene() as scene:
            scene.command(arc(repeatMs=2500))
            bad = [('speed',0), ('speed',1), ('jitter',17), ('alpha',2),
                   ('flicker',-1), ('delayMs',1000), ('holdMs',1000),
                   ('fadeMs',1000), ('repeatMs',1), ('delayMs',.0005),
                   ('points.0.x',2), ('seed',42)]
            for field, value in bad:
                saved = scene.snapshot()
                with self.subTest(field=field,value=value), self.assertRaises(ValueError):
                    bind(scene,'electrical-arc',7,field,value)
                self.assertEqual(scene.snapshot(),saved)
            saved = scene.snapshot()
            with self.assertRaises(ValueError): bind(scene,'electrical-arc',99,'alpha',.4)
            self.assertEqual(scene.snapshot(),saved)

    def test_schema54_promotes_unchanged_payload_but_rejects_new_binding_authoring(self):
        def prior(data):
            b=bytearray(data[:13548744]) # Exact schema54 payload13548720 + header24.
            struct.pack_into('<I',b,16,len(b)-24)
            for offset in (12,28): struct.pack_into('<I',b,offset,0x20261054)
            struct.pack_into('<I',b,20,zlib.crc32(b[24:]) & 0xffffffff)
            return bytes(b)
        with NativeScene() as scene:
            scene.command(emitter()); scene.command(arc())
            saved=scene.snapshot(); scene.restore(prior(saved))
            self.assertEqual(scene.snapshot(),saved)
            for family,ident,field,value in [('emitter',1,'glitterHz',30),('electrical-arc',7,'alpha',.4)]:
                with self.subTest(family=family):
                    scene.restore(saved); bind(scene,family,ident,field,value)
                    current=scene.snapshot()
                    with self.assertRaises(ValueError): scene.restore(prior(current))
                    self.assertEqual(scene.snapshot(),current)
                    scene.restore(saved)
                    scene.command({'op':'schedule','id':9,'atUs':1000000,'command':
                        {'op':'batch','commands':[{'op':'define','path':'/queued','value':value,
                        'binding':{'family':family,'id':ident,'field':field}}]}})
                    current=scene.snapshot()
                    with self.assertRaises(ValueError): scene.restore(prior(current))
                    self.assertEqual(scene.snapshot(),current)

    def test_missing_resource_pending_sets_restore_then_apply_to_recreated_target(self):
        for family,ident,field,value in [('emitter',1,'glitterDepth',.2),('electrical-arc',7,'alpha',.4)]:
            with self.subTest(family=family), NativeScene() as scene:
                scene.command(emitter() if family=='emitter' else arc())
                bind(scene,family,ident,field,.5)
                scene.command({'op':'schedule','id':9,'atUs':1000000,
                               'command':{'op':'set','path':'/control','value':value}})
                scene.command({'op':'clear-instance' if family=='emitter' else 'remove-electrical-arc','id':ident})
                saved=scene.snapshot(); scene.restore(saved)
                self.assertEqual(scene.snapshot(),saved)
                scene.command(emitter() if family=='emitter' else arc())
                scene.advance_to(1000000)
                self.assertEqual(scene.info_complete()['values']['/control'],value)
                q=scene.info_complete()
                self.assertEqual(q['emitters'][0]['burstStages'][field] if family=='emitter'
                                 else q['electricalArcs'][0][field],value)

    def test_runtime_discovery_identifies_resource_animation_contract_and_owned_arrays(self):
        with NativeScene() as scene:
            saved=scene.snapshot();contract=scene.info_complete()['contract']
            self.assertIn('electrical-arc',contract['bindingFamilies'])
            for feature in ('resource-animation-bindings','electrical-selectors'):
                self.assertIn(feature,contract['features'])
            self.assertEqual(contract['snapshotSchema'],current_schema())
            self.assertEqual(contract['snapshotCapacityBytes'],len(saved))
            contract['bindingFamilies'].clear();contract['features'].clear()
            self.assertIn('electrical-arc',scene.info_complete()['contract']['bindingFamilies'])
            self.assertEqual(scene.snapshot(),saved)
