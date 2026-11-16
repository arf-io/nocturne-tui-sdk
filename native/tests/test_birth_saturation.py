"""Bounded native saturation and exact pre-change scheduling/identity preservation."""
import gzip
import hashlib
import json
from pathlib import Path
import sys
import time
import struct
import zlib
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class BirthSaturation(unittest.TestCase):
    def emitter(self,s,**changes):
        c=dict(op='emitter',id=1,count=2048,runningTimeMs=0,lifetimeMinMs=10000,lifetimeMaxMs=10000,collision=False,deposit=False)
        c.update(changes);s.command(c)
    def blockPool(self,s):self.emitter(s);s.advance_to(8333)
    def testMaximumInstantRepeatsAccountAllBirthsWithinBoundedTime(self):
        with NativeScene() as s:
            self.emitter(s,count=100000,cycles=10000,gapMs=0)
            start=time.monotonic();s.advance_to(8333,budget=1);elapsed=time.monotonic()-start
            print(f"Maximum instant repeat core advance: {elapsed:.6f}s",file=sys.stderr)
            self.assertLess(elapsed,2)
            info=s.info();self.assertEqual(info['particles']['born'],2048)
            self.assertEqual(info['particles']['rejected'],1000000000-2048)
            self.assertEqual(info['emitters'][0]['attemptedBirths'],1000000000)
    def testPreChangeSaturationAndPoolReuseAreByteExact(self):
        spec=json.loads((ROOT/'tests/fixtures/birth-saturation-before.json').read_text())
        with NativeScene(spec['seed']) as s:
            for c in spec['commands']:s.command(c)
            s.advance_to(spec['timeUs'])
            before=gzip.decompress((ROOT/'tests/fixtures/birth-saturation-before.snapshot.gz').read_bytes())
            # Compare the independently retained historical payload after
            # projecting out the new append-only snapshot sections and header.
            current=s.snapshot();payload=bytearray(current[24:len(before)])
            payload[4:8]=before[28:32];header=bytearray(before[:24])
            struct.pack_into('<I',header,20,zlib.crc32(payload))
            self.assertEqual(hashlib.sha256(before).hexdigest(),spec['snapshotSha256'])
            self.assertEqual(bytes(header)+payload,before)
            self.assertEqual(s.info()['particles'],spec['particles'])
            # The historical frame pins the old forced-cell blade, explicitly
            # superseded by the operator's true-braille repair. Keep its hash
            # and source receipt unchanged; scheduling must still replay the
            # exact historical state through the corrected current renderer.
            saved=s.snapshot();frame=s.render()
            with NativeScene(1) as restored:
                restored.restore(before)
                self.assertEqual(restored.particles(),s.particles())
                self.assertEqual(restored.info()['particles'],spec['particles'])
                self.assertEqual(restored.render().bytes,frame.bytes)
            self.assertNotEqual(hashlib.sha256(frame.bytes).hexdigest(),spec['frameSha256'])
            braille=[w for w in frame.words() if 0x2800<w[0]<=0x28ff]
            self.assertTrue(any(w[0]==0x28ff and w[1]!=w[2] for w in braille))
            self.assertTrue(any(w[0]<0x28ff and w[1]!=w[2] for w in braille))
            self.assertEqual(s.snapshot(),saved)

    def testDenseNonbrailleSamplingPreservesHistoricalFramesAndOverflow(self):
        # These references were executed from the immutable pre-change C
        # source, independently of the current renderer and its layer budget.
        spec=json.loads((ROOT/'tests/fixtures/birth-sampling-historical.json').read_text())
        for case in spec['cases']:
            with self.subTest(sampling=case['sampling']),NativeScene(spec['seed']) as s:
                for command in spec['commands']:s.command(dict(command,sampling=case['sampling']))
                s.advance_to(spec['timeUs']);saved=s.snapshot();frame=s.render()
                overflow=case['fragmentOverflow']
                if case['sampling']=='hybrid':
                    # Operator directive 2026-11-01 (docs/MIXED-LAYERS.md, Hybrid dictation): hybrid
                    # particles are braille objects, so the retained hybrid frame and its overflow are
                    # superseded. Keep the reference unchanged; the frame and the render diagnostic are
                    # now exactly the braille render's (docs/BRAILLE.md records 715).
                    braille,overflow=self.dense(spec,'braille')
                    self.assertNotEqual(hashlib.sha256(frame.bytes).hexdigest(),case['frameSha256'])
                    self.assertEqual(frame.bytes,braille);self.assertEqual(overflow,715)
                else:self.assertEqual(hashlib.sha256(frame.bytes).hexdigest(),case['frameSha256'])
                self.assertEqual(s.info()['render']['fragmentOverflow'],overflow)
                self.assertEqual(s.info()['particles'],case['particles'])
                self.assertEqual(s.snapshot(),saved)
                self.assertEqual(s.render().bytes,frame.bytes)
                self.assertEqual(s.info()['render']['fragmentOverflow'],overflow)
    def dense(self,spec,sampling):
        with NativeScene(spec['seed']) as s:
            for command in spec['commands']:s.command(dict(command,sampling=sampling))
            s.advance_to(spec['timeUs']);frame=s.render()
            return frame.bytes,s.info()['render']['fragmentOverflow']
    def testBlockedFiniteRateKeepsIntervalAndEndBoundary(self):
        with NativeScene() as s:
            self.blockPool(s)
            s.command(dict(op='emitter',id=2,rate=2.5,runningTimeMs=800,startTimeUs=1000000,collision=False,deposit=False))
            for t,expected in [(1000000,0),(1400000,1),(1800000,2),(2000000,2)]:
                s.advance_to(t);self.assertEqual(s.info()['emitters'][1]['attemptedBirths'],expected)
                self.assertEqual(s.info()['particles']['rejected'],expected)
    def testTinyPositiveRateDoesNotConvertOutOfRangeTimeToBirth(self):
        with NativeScene() as s:
            s.command(dict(op='emitter',id=1,rate=1e-100,runningTimeMs=0,collision=False,deposit=False))
            s.advance_to(1000000);self.assertEqual(s.info()['particles']['born'],0)
    def testBlockedUniformRepeatsHaveIndependentCountOracle(self):
        with NativeScene() as s:
            self.blockPool(s);self.emitter(s,id=2,count=71,runningTimeMs=200,cycles=3,gapMs=150,startTimeUs=8333)
            for t in (16666,83333,199999,200000,349999,350000,550000,900000,1200000):
                s.advance_to(t);info=s.info();tick=info['clock']['step']*1000000//120
                expected=sum(8333+cycle*350000+ordinal*200000//71<=tick for cycle in range(3) for ordinal in range(71))
                self.assertEqual(info['emitters'][1]['attemptedBirths'],expected)
                self.assertEqual(info['particles']['rejected'],expected)

    def testIdentityExhaustionRejectsBirthsWithoutWrappingOrBreakingReplay(self):
        with NativeScene() as s:
            saved=bytearray(s.snapshot())
            # Immutable private prefix: seven uint32 fields precede nextParticle.
            struct.pack_into('<I',saved,24+28,0xfffffffe)
            struct.pack_into('<I',saved,20,zlib.crc32(saved[24:]))
            s.restore(saved);self.emitter(s,count=3);s.advance_to(8333)
            self.assertEqual([p[0]&0xffffffff for p in s.particles()],[0xfffffffe])
            self.assertEqual(s.info()['particles']['rejected'],2)
            saved=s.snapshot();s.restore(saved);self.assertEqual(saved,s.snapshot())
