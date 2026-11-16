"""Independent acceptance tests for reusable retained serial flow transport."""
import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'bindings/python'))
from nocturne_native import NativeScene

class FlowTransport(unittest.TestCase):
    def create(self, scene, stages, flux=2):
        scene.command(dict(op='flow', id=1, flux=flux, stages=stages))

    def ledger(self, scene):
        flow = scene.info()['flows'][0]
        self.assertAlmostEqual(flow['injectedVolume'], flow['storedVolume'] + flow['deliveredVolume'], places=6)
        return flow

    def testSerialDelaysAndZeroFlowDrain(self):
        with NativeScene() as s:
            self.create(s, [dict(name='channel', delayUs=500000, tailUs=0),
                            dict(name='sheet', delayUs=250000, tailUs=0)])
            s.advance_to(500000)
            f = self.ledger(s)
            self.assertAlmostEqual(f['injectedVolume'], 1)
            self.assertAlmostEqual(f['deliveredVolume'], 0)
            self.assertEqual(f['stages'][0]['flux'], 2)
            self.assertEqual(f['outletFlux'], 0)
            s.advance_to(1000000)
            f = self.ledger(s)
            self.assertAlmostEqual(f['deliveredVolume'], .5)
            self.assertEqual(f['outletFlux'], 2)
            s.command(dict(op='flow-rate', id=1, flux=0))
            s.advance_to(2000000)
            f = self.ledger(s)
            self.assertAlmostEqual(f['injectedVolume'], 2)
            self.assertAlmostEqual(f['deliveredVolume'], 2)
            self.assertAlmostEqual(f['storedVolume'], 0)

    def testReservoirTailMatchesIndependentAnalyticSolution(self):
        with NativeScene() as s:
            self.create(s, [dict(name='basin', delayUs=0, tailUs=500000)])
            s.advance_to(1000000)
            expected_storage = 2 * .5 * (1 - math.exp(-2))
            f = self.ledger(s)
            self.assertAlmostEqual(f['storedVolume'], expected_storage, places=5)
            self.assertAlmostEqual(f['outletFlux'], 2*(1-math.exp(-2)), places=5)
            self.assertAlmostEqual(f['deliveredVolume'], 2 - expected_storage, places=5)
            s.command(dict(op='flow-rate', id=1, flux=0))
            s.advance_to(2000000)
            f = self.ledger(s)
            self.assertAlmostEqual(f['storedVolume'], expected_storage * math.exp(-2), places=5)

    def testNativeClockPartitionReplayAndRenderPurity(self):
        with NativeScene() as s:
            self.create(s, [dict(name='channel', delayUs=250000, tailUs=0),
                            dict(name='spray', delayUs=0, tailUs=500000)])
            saved = s.snapshot()
            s.render()
            self.assertEqual(saved, s.snapshot())
            s.advance_to(1000000)
            expected = s.snapshot()
            s.restore(saved)
            for at in [12345, 111111, 333333, 777777, 1000000]:
                s.advance_to(at)
            self.assertEqual(expected, s.snapshot())

    def testInvalidRateAndStageConfigurationAreAtomic(self):
        with NativeScene() as s:
            self.create(s, [dict(name='channel', delayUs=0, tailUs=0)])
            before = s.snapshot()
            for command in [dict(op='flow-rate', id=1, flux=-1),
                            dict(op='flow-rate', id=999, flux=1),
                            dict(op='flow', id=2, flux=1, stages=[]),
                            dict(op='flow', id=2, flux=1, stages=[dict(name='x', delayUs=-1, tailUs=0)])]:
                with self.assertRaises(ValueError):
                    s.command(command)
                self.assertEqual(before, s.snapshot())

    def testEqualReservoirCascade(self):
        with NativeScene() as s:
            self.create(s, [dict(name='a', tailUs=500000), dict(name='b', tailUs=500000)])
            s.advance_to(1000000)
            expected = 2 * (1 - 1 + 2 * math.exp(-2))
            self.assertAlmostEqual(self.ledger(s)['deliveredVolume'], expected, places=5)

    def testPreviousSchemaMigration(self):
        import struct, zlib
        with NativeScene() as s:
            data = bytearray(s.snapshot()); payload = data[24:24+5069840]
            struct.pack_into('<I', payload, 4, 0x20261018)
            data = data[:24] + payload
            struct.pack_into('<III', data, 12, 0x20261018, len(payload), zlib.crc32(payload))
            s.restore(data)
            self.assertNotIn('flows', s.info())
            self.create(s, [dict(name='a', delayUs=0, tailUs=0)])
            s.advance_to(1000000)
            self.assertEqual(self.ledger(s)['deliveredVolume'], 2)

    def testRateHistoryCapacityRejectsWithoutDroppingWater(self):
        with NativeScene() as s:
            self.create(s, [dict(name='a', tailUs=500000)])
            for k in range(1, 128):
                s.advance_to(k * 1000)
                s.command(dict(op='flow-rate', id=1, flux=1 if k % 2 else 2))
            s.advance_to(128000)
            before = s.snapshot()
            with self.assertRaises(ValueError): s.command(dict(op='flow-rate', id=1, flux=3))
            self.assertEqual(before, s.snapshot())
            self.ledger(s)

    def testCorruptRetainedRateRejectsRestoreAtomically(self):
        import struct, zlib
        with NativeScene() as s:
            self.create(s, [dict(name='a', tailUs=500000)])
            before = s.snapshot(); bad = bytearray(before)
            # Flow header 16 + eight 48-byte stages + first epoch timestamp 8.
            struct.pack_into('<d', bad, 24 + 5069840 + 16 + 8*48 + 8, -1)
            struct.pack_into('<I', bad, 20, zlib.crc32(bad[24:]))
            with self.assertRaises(ValueError): s.restore(bad)
            self.assertEqual(before, s.snapshot())
