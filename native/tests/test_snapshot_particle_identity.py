"""Checksummed snapshots cannot counterfeit retained particle/deposit identities."""
import json,struct,subprocess,sys,tempfile,unittest,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class SnapshotParticleIdentity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as folder:
            executable=Path(folder)/'offsets'
            subprocess.run(['cc','-std=c11','-I'+str(ROOT/'include'),'-I'+str(ROOT/'src'),str(ROOT/'tests/identity_offsets.c'),'-o',str(executable)],check=True,capture_output=True)
            cls.offsets=json.loads(subprocess.check_output([str(executable)]))
    def setUp(self):
        self.s=NativeScene()
        self.s.command(dict(op='emitter',id=1,count=2,runningTimeMs=0,position=[0,.1,0],extent=[0,0,0],velocity=[0,-3,0],collision=True,deposit=True))
        self.s.command(dict(op='emitter',id=2,count=2,runningTimeMs=0,position=[0,10,0],extent=[0,0,0],velocity=[0,0,0],collision=False,deposit=False))
        self.s.advance_to(200000);self.assertEqual(self.s.info()['particles']['deposited'],2);self.assertEqual(len(self.s.particles()),2)
    def tearDown(self):self.s.close()
    def rejected(self,offset,value):
        before=self.s.snapshot();bad=bytearray(before);struct.pack_into('<I',bad,24+offset,value);struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]))
        with self.assertRaises(ValueError):self.s.restore(bad)
        self.assertEqual(before,self.s.snapshot())
    def deposit(self,field):return self.offsets['deposit']+self.offsets[field]
    def testDepositIdentityZeroRejects(self):self.rejected(self.deposit('id'),0)
    def testDepositUnallocatedIdentityRejects(self):self.rejected(self.deposit('id'),0xffffffff)
    def testDepositMissingOwnerRejects(self):self.rejected(self.deposit('owner'),0)
    def testDepositOutOfRangeOwnerRejects(self):self.rejected(self.deposit('owner'),65536)
    def testDepositMissingGenerationRejects(self):self.rejected(self.deposit('generation'),0)
    def testDepositFutureGenerationRejects(self):self.rejected(self.deposit('generation'),3)
    def testDuplicateDepositIdentityRejects(self):
        ident=self.s.info()['deposits'][0]['id'];self.rejected(self.deposit('id')+self.offsets['depositSize'],ident)
    def testIdentitySharedByAirborneAndDepositRejects(self):self.rejected(self.deposit('id'),self.s.particles()[0][0])
    def testUnallocatedAirborneIdentityRejects(self):
        self.rejected(self.offsets['particle']+2*self.offsets['particleSize']+self.offsets['particleId'],0xffffffff)
    def testDuplicateAirborneIdentityRejects(self):
        self.rejected(self.offsets['particle']+3*self.offsets['particleSize']+self.offsets['particleId'],self.s.particles()[0][0])
    def testIdentityCounterCannotPrecedeRetainedIdentities(self):self.rejected(self.offsets['nextParticle'],1)
    def testRemovedEmitterDepositsRemainValidWithOriginalOwnership(self):
        self.s.command(dict(op='clear-instance',id=1));before=self.s.snapshot();self.s.restore(before);self.assertEqual(before,self.s.snapshot())
