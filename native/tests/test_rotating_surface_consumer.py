from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'native/bindings/python'))
from nocturne_native import NativeScene

class RotatingSurfaceConsumer(unittest.TestCase):
    def testActualExampleCompletesIndependentPhysicsAndPresentationChecks(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'report.json'
            result=subprocess.run([sys.executable,str(ROOT/'native/examples/rotating_surface.py'),'--output',str(output)],capture_output=True,text=True,timeout=30,cwd=ROOT)
            self.assertEqual(result.returncode,0,result.stderr)
            report=json.loads(output.read_text())
            self.assertTrue(report['stopFrozen']);self.assertTrue(report['replayGeometry'])
            self.assertEqual(len(report['samples']),3)
            self.assertTrue(all(row['queryPure'] and row['renderPure'] for row in report['samples']))
            self.assertTrue(any(set(row['visibleWindowIds'])=={1,2} for row in report['samples']))
    def testObsoleteWindowCoordinatesRejectWithoutMutation(self):
        with NativeScene() as scene:
            before=scene.snapshot()
            with self.assertRaises(ValueError):scene.command({'op':'window','id':1,'x':2,'y':2})
            self.assertEqual(before,scene.snapshot())

if __name__=='__main__':unittest.main()
