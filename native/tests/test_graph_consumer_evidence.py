"""Graph consumer receipts use fresh directories and preserve earlier evidence."""
from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class GraphConsumerEvidence(unittest.TestCase):
    def testExplicitEvidenceDirectoryRunsActualConsumersAndKeepsHistory(self):
        history = ROOT / 'evidence/graph-consumer'
        before = {str(path.relative_to(history)):hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in history.rglob('*') if path.is_file()}
        summary = ROOT / 'evidence/graph-consumer.json'
        summaryBefore = summary.read_bytes() if summary.exists() else None
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'observed-consumers'
            result = subprocess.run([sys.executable, str(ROOT/'scripts/check_graph_consumer.py'),
                                     '--evidence-dir', str(output)], capture_output=True, text=True, timeout=120)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            receipt = json.loads((output/'RESULT.json').read_text())
            self.assertTrue(receipt['passed'])
            self.assertEqual(receipt['evidenceDirectory'], str(output))
            self.assertGreaterEqual(len(receipt['checks']), 5)
            self.assertTrue(all(row['status']=='PASS' for row in receipt['commands']))
            self.assertGreater((output/'graph.cells').stat().st_size, 0)
            self.assertEqual(json.loads((output/'graph-info.json').read_text()),
                             json.loads((output/'cpp-run.log').read_text()))
            for row in receipt['commands']:
                self.assertEqual(hashlib.sha256((output/row['log']).read_bytes()).hexdigest(), row['logSha256'])
        self.assertEqual({str(path.relative_to(history)):hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in history.rglob('*') if path.is_file()}, before)
        self.assertEqual(summary.read_bytes() if summary.exists() else None, summaryBefore)

    def testExplicitExistingEvidenceIsRefusedWithoutOverwriting(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            marker = output/'preserve.txt'; marker.write_text('prior evidence')
            result = subprocess.run([sys.executable, str(ROOT/'scripts/check_graph_consumer.py'),
                                     '--evidence-dir', str(output)], capture_output=True, text=True, timeout=30)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(marker.read_text(), 'prior evidence')
            self.assertEqual(sorted(path.name for path in output.iterdir()), ['preserve.txt'])

    def testDefaultAttemptsAreUniqueWithoutReplacingHistoricalDirectory(self):
        specification = importlib.util.spec_from_file_location('graph_consumer_check', ROOT/'scripts/check_graph_consumer.py')
        module = importlib.util.module_from_spec(specification); specification.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            historical = root/'graph-consumer'; historical.mkdir()
            (historical/'prior.log').write_text('historical observation')
            first = module.newEvidenceDirectory(root)
            second = module.newEvidenceDirectory(root)
            self.assertNotEqual(first, second)
            self.assertTrue(first.is_dir() and second.is_dir())
            self.assertEqual(first.parent, root/'graph-consumer-runs')
            self.assertEqual((historical/'prior.log').read_text(), 'historical observation')


if __name__ == '__main__':
    unittest.main(verbosity=2)
