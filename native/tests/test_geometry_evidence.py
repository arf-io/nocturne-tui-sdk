"""Real filesystem/process custody checks for a scoped qualification receipt."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from qualify_surface_geometry import retainReplayArtifacts


class GeometryEvidence(unittest.TestCase):
    def testFailedCurrentProcessCannotInheritPriorReplayArtifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'prior';destination=root/'current'
            source.mkdir();destination.mkdir()
            old={'parity.json':b'{"run":"prior","fourRuntimePassed":true}',
                 'parity-python.jsonl':b'prior frame and state evidence\n',
                 'plan.ndjson':b'{"op":"reset","seed":1}\n',
                 'go-build.log':b'prior successful build\n'}
            for name,data in old.items():(source/name).write_bytes(data)
            failed=subprocess.run([sys.executable,'-c','raise SystemExit(7)'],cwd=source)
            self.assertEqual(failed.returncode,7)
            retainReplayArtifacts(source,destination,passed=failed.returncode==0)
            self.assertEqual(list(destination.iterdir()),[],
                             'A failed current command copied prior replay proof')
            for name,data in old.items():self.assertEqual((source/name).read_bytes(),data)

    def testCompletedCurrentProcessRetainsItsWrittenArtifact(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'source';destination=root/'receipt'
            source.mkdir();destination.mkdir()
            process=subprocess.run([sys.executable,'-c',
                'from pathlib import Path; Path("parity-python.jsonl").write_text("current-process-output\\n")'],cwd=source)
            self.assertEqual(process.returncode,0)
            retainReplayArtifacts(source,destination,passed=process.returncode==0)
            self.assertEqual((destination/'parity-python.jsonl').read_bytes(),b'current-process-output\n')


if __name__=='__main__':unittest.main()
