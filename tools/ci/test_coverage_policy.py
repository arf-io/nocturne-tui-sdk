"""Exercise coverage decisions with executed LLVM profiles and real Git refs."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parent

class CoveragePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name).resolve()
        ci = cls.root / 'tools/ci'
        ci.mkdir(parents=True)
        shutil.copy(SOURCE / 'coverage_gate.py', ci)
        production = cls.root / 'native/src'
        production.mkdir(parents=True)
        tests = cls.root / 'native/tests'
        tests.mkdir()
        dist = cls.root / 'native/dist'
        dist.mkdir()
        source = production / 'policy_fixture.c'
        source.write_text("""int policy_branch(int value) {
    int result = 1;
    if (value > 0) {
        result += 2;
    } else {
        result += 4;
    }
    return result;
}
int policy_unused(int value) {
    return value + 7;
}
""")
        excluded = tests / 'uncalled.c'
        excluded.write_text('int nonproduction_fixture(int value) {\n' +
                            ''.join(f'    value += {number};\n' for number in range(1, 21)) +
                            '    return value;\n}\n')
        compiler = shutil.which(os.environ.get('CC', 'clang'))
        if not compiler or any(not shutil.which(name) for name in ['llvm-profdata', 'llvm-cov']):
            raise RuntimeError('Actual Clang, llvm-profdata and llvm-cov are required')
        cls.library = dist / ('libnocturne_native.dylib' if sys.platform == 'darwin' else 'libnocturne_native.so')
        subprocess.run([compiler, '-O0', '-fprofile-instr-generate', '-fcoverage-mapping',
                        '-fPIC', '-dynamiclib' if sys.platform == 'darwin' else '-shared',
                        str(source), str(excluded), '-o', str(cls.library)], check=True, capture_output=True)
        cls.env = dict(os.environ)
        cls.profile_dirs = {}
        cls.summaries = {}
        for mode in ['low', 'partial', 'complete']:
            profiles = cls.root / ('profiles-' + mode)
            profiles.mkdir()
            cls.profile_dirs[mode] = profiles
            environment = dict(cls.env, LLVM_PROFILE_FILE=str(profiles / 'fixture-%p.profraw'))
            script = ('import ctypes,sys; library=ctypes.CDLL(sys.argv[1]); '
                      'assert library.policy_branch(0)==5; '
                      + ('assert library.policy_branch(1)==3; ' if mode != 'low' else '')
                      + ('assert library.policy_unused(2)==9; ' if mode == 'complete' else ''))
            subprocess.run([sys.executable, '-c', script, str(cls.library)], env=environment, check=True)
            merged = cls.root / (mode + '.profdata')
            raw = list(profiles.glob('*.profraw'))
            if not raw:
                raise RuntimeError('Executed fixture did not write its LLVM profile')
            subprocess.run(['llvm-profdata', 'merge', '-sparse', *map(str, raw), '-o', str(merged)], check=True)
            export = json.loads(subprocess.check_output(['llvm-cov', 'export', str(cls.library),
                                                        '-instr-profile=' + str(merged)], text=True))
            native = [row for data in export['data'] for row in data['files']
                      if Path(row['filename']).resolve().is_relative_to(production)]
            if len(native) != 1:
                raise RuntimeError('Fixture coverage did not identify its production file')
            cls.summaries[mode] = native[0]['summary']['lines']

    def setUp(self):
        git = self.root / '.git'
        if git.exists():
            shutil.rmtree(git)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        (self.root / 'tools/ci/coverage-ratchet.json').write_text('{"nativeLinePercent":70}')

    def native_summary(self, mode):
        return self.summaries[mode]

    def prepare_alternate_root(self):
        root = self.root / 'wrong-source-root'
        ci = root / 'tools/ci'
        ci.mkdir(parents=True, exist_ok=True)
        shutil.copy(SOURCE / 'coverage_gate.py', ci)
        (ci / 'coverage-ratchet.json').write_text('{"nativeLinePercent":70}')
        dist = root / 'native/dist'
        dist.mkdir(parents=True, exist_ok=True)
        shutil.copy(self.library, dist / self.library.name)
        return root

    def run_gate(self, mode='partial', *, root=None, profiles=None):
        root = root or self.root
        profiles = profiles or self.profile_dirs[mode]
        return subprocess.run([sys.executable, str(root / 'tools/ci/coverage_gate.py'),
                               '--profiles', str(profiles), '--output', str(root / 'out')],
                              env=self.env, capture_output=True, text=True)

    def test_floor_and_production_only_denominator(self):
        self.assertEqual(self.run_gate('partial').returncode, 0)
        report = json.loads((self.root / 'out/RESULTS.json').read_text())
        production = self.native_summary('partial')
        self.assertEqual(report['totalLines'], production['count'])
        self.assertEqual(report['coveredLines'], production['covered'])
        self.assertEqual(report['files'], 1)
        self.assertNotEqual(self.run_gate('low').returncode, 0)

    def test_empty_profiles_and_empty_denominator_fail(self):
        wrong_root = self.prepare_alternate_root()
        self.assertNotEqual(self.run_gate('partial', root=wrong_root).returncode, 0)
        empty = self.root / 'empty-profiles'
        empty.mkdir(exist_ok=True)
        self.assertNotEqual(self.run_gate('partial', profiles=empty).returncode, 0)

    def test_protected_branch_ratchet_cannot_be_lowered(self):
        summary = self.native_summary('partial')
        percent = 100 * summary['covered'] / summary['count']
        protected = int(percent) + 1
        self.assertGreater(protected, 70)
        policy = self.root / 'tools/ci/coverage-ratchet.json'
        policy.write_text(json.dumps({'nativeLinePercent': protected}))
        subprocess.run(['git', 'add', 'tools/ci/coverage-ratchet.json'], cwd=self.root, check=True)
        subprocess.run(['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.test',
                        'commit', '-qm', 'baseline'], cwd=self.root, check=True)
        subprocess.run(['git', 'update-ref', 'refs/remotes/origin/integration', 'HEAD'],
                       cwd=self.root, check=True)
        policy.write_text('{"nativeLinePercent":1}')
        self.assertNotEqual(self.run_gate('partial').returncode, 0)
        self.assertEqual(self.run_gate('complete').returncode, 0)
        report = json.loads((self.root / 'out/RESULTS.json').read_text())
        self.assertEqual(report['requiredPercent'], protected)
        next_policy = json.loads((self.root / 'out/coverage-ratchet.next.json').read_text())
        self.assertEqual(next_policy['nativeLinePercent'], report['nativeLinePercent'])

    def test_executed_profiles_and_binary_are_real(self):
        self.assertGreater(self.library.stat().st_size, 1000)
        self.assertTrue(list(self.profile_dirs['partial'].glob('*.profraw')))
        self.assertTrue(all(p.stat().st_size > 0 for p in self.profile_dirs['partial'].glob('*.profraw')))
        result = self.run_gate('partial')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertGreater((self.root / 'out/core.profdata').stat().st_size, 0)
        workflow = (SOURCE.parents[1] / '.forgejo/workflows/nocturne.yml').read_text()
        self.assertLess(workflow.index('name: Linux native prerequisites'), workflow.index('name: Release CI policy'))

if __name__ == '__main__':
    unittest.main()
