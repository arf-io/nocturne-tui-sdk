"""Native captured initial XYZ pose and angular rate, with independent age oracle."""
import gzip
import math
import struct
import sys
import unittest
import zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class ParticleMotion(unittest.TestCase):
    def command(self,**changes):
        c=dict(op='emitter',id=1,seed=79,count=3,runningTimeMs=0,effect='weather/autumn-drift',shape='point',position=[0,0,0],velocity=[0,0,0],spread=[0,0,0],gravity=[0,0,0],wind=[0,0,0],windVariation=[0,0,0],drag=0,lift=0,flutterAmount=0,collision=False,deposit=False,lifetimeMinMs=10000,lifetimeMaxMs=10000,initialOrientation=[10,20,30],angularVelocity=[30,-60,90])
        c.update(changes);return c
    def testCapturedXYZPoseUsesIndependentParticleAge(self):
        with NativeScene() as s:
            s.command(self.command());s.advance_to(1000000)
            motions=s.particle_motions();self.assertEqual(len(motions),3)
            for p,m in zip(s.particles(),motions):
                self.assertEqual(p[0],m[0]);age=p[10]/120
                for actual,initial,rate in zip(m[1:4],(10,20,30),(30,-60,90)):
                    self.assertAlmostEqual(actual,initial+age*rate,places=10)
                self.assertEqual(m[4:],(30,-60,90))
            before=s.snapshot();s.render();s.info_complete();s.particle_motions()
            self.assertEqual(before,s.snapshot())
    def testStaticAuthoredPoseAndAngularOnlyDefaults(self):
        with NativeScene() as s:
            c=self.command();del c['angularVelocity'];s.command(c);s.advance_to(1000000)
            self.assertEqual(s.particle_motions()[0][1:],(10,20,30,0,0,0))
        with NativeScene() as s:
            c=self.command();del c['initialOrientation'];s.command(c);s.advance_to(8333)
            self.assertEqual(s.particle_motions()[0][1:4],(0,0,0))
    def testNestedAuthoringCompilesToTheSameNativeMotion(self):
        c=self.command()
        nested=dict(op='weather-author',schema='nocturne.weather-authoring/v1',id=1,effect=c['effect'],emission={k:c[k] for k in ('seed','count','runningTimeMs')},birth={k:c[k] for k in ('shape','position','velocity','spread','initialOrientation','angularVelocity')},forces={k:c[k] for k in ('gravity','wind','windVariation','drag','lift','flutterAmount')},collision=dict(enabled=False,deposit=False),lifecycle={k:c[k] for k in ('lifetimeMinMs','lifetimeMaxMs')})
        with NativeScene() as a,NativeScene() as b:
            a.command(c);b.command(nested);self.assertEqual(a.snapshot(),b.snapshot())
    def testInvalidAndUnsupportedMotionRejectsAtomically(self):
        with NativeScene() as s:
            before=s.snapshot()
            for patch in (dict(initialOrientation=[0,0]),dict(initialOrientation=[3601,0,0]),dict(angularVelocity=[0,721,0]),dict(angularVelocity=[None,0,0]),dict(effect='weather/silver-squall')):
                with self.assertRaises(ValueError):s.command(self.command(**patch))
                self.assertEqual(before,s.snapshot())
    def testReplayPauseClearAndReusePreserveOwnership(self):
        with NativeScene() as a,NativeScene() as b:
            a.command(self.command());a.advance_to(500000);b.restore(a.snapshot())
            for s in (a,b):s.advance_to(1000000)
            self.assertEqual(a.particle_motions(),b.particle_motions());self.assertEqual(a.render().bytes,b.render().bytes)
            a.command(dict(op='pause',paused=True));before=a.particle_motions();a.advance_to(2000000);self.assertEqual(before,a.particle_motions())
            a.command(dict(op='clear-instance',id=1));c=self.command();del c['initialOrientation'];del c['angularVelocity'];a.command(c)
            self.assertEqual(a.particle_motions(),[])
    def testSchema07RetainsUniformFramesGeometryAndIntent(self):
        old=gzip.decompress((ROOT/'tests/fixtures/schema-20261007-particle-motion.snapshot.gz').read_bytes())
        with NativeScene() as s:
            s.restore(old);new=s.snapshot();self.assertEqual(new[32:24+4643032],old[32:])
            self.assertEqual(s.info()['emitters'][0]['distribution'],'uniform');self.assertEqual(s.particle_motions(),[])
    def testForgedNonfiniteMotionRejectsWithCorrectChecksum(self):
        with NativeScene() as s:
            s.command(self.command());s.advance_to(8333);before=s.snapshot();bad=bytearray(before)
            struct.pack_into('<d',bad,24+4643032,float('nan'));struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]))
            with self.assertRaises(ValueError):s.restore(bad)
            self.assertEqual(before,s.snapshot())

    def testUnauthoredPayloadAndUnknownPaddingReject(self):
        with NativeScene() as s:
            s.command(self.command());before=s.snapshot()
            for offset,value in ((4643032+48,0),(4643032+52,1)):
                bad=bytearray(before);struct.pack_into('<i',bad,24+offset,value);struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]))
                with self.assertRaises(ValueError):s.restore(bad)
                self.assertEqual(before,s.snapshot())
