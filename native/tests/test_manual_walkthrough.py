"""Run the documented consumer against the actual native library."""
from pathlib import Path
import json
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]

class ManualWalkthrough(unittest.TestCase):
    def testActualDocumentRenderRestoreAndAtomicRejection(self):
        result=subprocess.run([sys.executable,str(ROOT/'native/examples/manual_basics.py')],
                              cwd=ROOT,capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stderr)
        record=json.loads(result.stdout)
        self.assertEqual(record['document'],'Hello, Nocturne')
        self.assertTrue(record['renderPure'])
        self.assertTrue(record['rejectionPreservedState'])
        self.assertTrue(record['restorePreservedFrame'])
        self.assertEqual(record['frameBytes'],record['width']*record['height']*16)
        self.assertGreater(record['snapshotBytes'],24)
        self.assertEqual(len(record['librarySha256']),64)

    def testMissingExplicitLibraryFailsInsteadOfUsingAnotherCore(self):
        result=subprocess.run([sys.executable,str(ROOT/'native/examples/manual_basics.py'),
                               '--library',str(ROOT/'native/dist/does-not-exist.so')],
                              cwd=ROOT,capture_output=True,text=True,timeout=30)
        self.assertNotEqual(result.returncode,0)
        self.assertEqual(result.stdout,'')

if __name__=='__main__':unittest.main()
