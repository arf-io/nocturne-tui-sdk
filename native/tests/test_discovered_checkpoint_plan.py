"""Actual generated strict plan must enter a real immutable checkpoint store."""
import json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT.parent/'tools/qualification'))
import qualify
from checkpoints import CheckpointStore,SAFE_CASE
class DiscoveredCheckpointPlan(unittest.TestCase):
    def test_actual_strict_plan_creates_real_checkpoint_manifest(self):
        result=subprocess.run([sys.executable,str(ROOT/'scripts/qualify.py'),'--strict','--capture','--list'],cwd=ROOT,capture_output=True,text=True,check=True)
        plan=json.loads(result.stdout)
        self.assertGreater(len(plan),300)
        self.assertEqual(len({c['id'] for c in plan}),len(plan))
        for case in plan:self.assertIsNotNone(SAFE_CASE.fullmatch(case['id']),case['id'])
        with tempfile.TemporaryDirectory() as directory:
            binding={'plan':plan,'source':qualify.fingerprint()['sha256']}
            with CheckpointStore(Path(directory).resolve()/'store',binding) as store:
                self.assertEqual(len(store.cases),len(plan))
                actual=json.loads((store.directory/'MANIFEST.json').read_text())
                self.assertEqual(actual['binding'],binding)
    def test_discovered_ids_stable_distinct_and_safe(self):
        values=[qualify.discoveredCaseId('wasm',name) for name in ('bindings/typescript/a.test.mjs','bindings/typescript/a_test.mjs','other/a.test.mjs')]
        self.assertEqual(len(set(values)),3)
        for value in values:self.assertIsNotNone(SAFE_CASE.fullmatch(value));self.assertLess(len(value),240)
        self.assertEqual(values[0],qualify.discoveredCaseId('wasm','bindings/typescript/a.test.mjs'))
        for kind,path in (('../unsafe','a.mjs'),('wasm','../a.mjs'),('wasm','/a.mjs')):
            with self.assertRaises(ValueError):qualify.discoveredCaseId(kind,path)
