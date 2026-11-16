"""Use real local Git remotes to check upward publication and concurrent pushes."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parent

class RatchetPublicationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.root = base / 'checkout'
        self.remote = base / 'remote.git'
        subprocess.run(['git', 'init', '-q', '--bare', str(self.remote)], check=True)
        subprocess.run(['git', 'init', '-q', '-b', 'integration', str(self.root)], check=True)
        self.ci = self.root / 'tools/ci'
        self.ci.mkdir(parents=True)
        shutil.copy(SOURCE / 'ratchet_coverage.py', self.ci)
        self.policy = self.ci / 'coverage-ratchet.json'
        self.policy.write_text('{"nativeLinePercent":70}\n')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.test')
        self.git('add', '.')
        self.git('commit', '-qm', 'baseline')
        self.git('remote', 'add', 'origin', str(self.remote))
        self.git('push', '-q', 'origin', 'integration')
        self.next = base / 'next.json'

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.root, text=True).strip()

    def run_ratchet(self, percent, branch='integration'):
        self.next.write_text(json.dumps({'nativeLinePercent': percent}))
        return subprocess.run([sys.executable, str(self.ci / 'ratchet_coverage.py'), str(self.next)],
                              env=dict(os.environ, GITHUB_REF='refs/heads/' + branch,
                                       NOCTURNE_CI_TOKEN='local-fixture-token'),
                              capture_output=True, text=True)

    def test_upward_only_and_protected_branches(self):
        head = self.git('rev-parse', 'HEAD')
        self.assertEqual(self.run_ratchet(70).returncode, 0)
        self.assertEqual(head, self.git('rev-parse', 'HEAD'))
        self.assertNotEqual(self.run_ratchet(80, 'feature').returncode, 0)
        self.assertEqual(self.run_ratchet(80).returncode, 0)
        self.assertEqual(json.loads(self.policy.read_text())['nativeLinePercent'], 80)
        remote = self.git('ls-remote', 'origin', 'refs/heads/integration').split()[0]
        self.assertEqual(remote, self.git('rev-parse', 'HEAD'))
        self.assertEqual(self.run_ratchet(75).returncode, 0)
        self.assertEqual(json.loads(self.policy.read_text())['nativeLinePercent'], 80)

    def test_invalid_percentage_and_dirty_checkout_refuse_mutation(self):
        head = self.git('rev-parse', 'HEAD')
        for value in [float('nan'), float('inf'), 101, 69, True]:
            self.assertNotEqual(self.run_ratchet(value).returncode, 0)
            self.assertEqual(head, self.git('rev-parse', 'HEAD'))
        self.policy.write_text('{"nativeLinePercent":71}\n')
        self.assertNotEqual(self.run_ratchet(80).returncode, 0)
        self.assertEqual(head, self.git('rev-parse', 'HEAD'))

    def test_generated_receipts_are_retained_without_committing_them(self):
        receipt = self.root / 'native/evidence/receipt.json'
        receipt.parent.mkdir(parents=True)
        receipt.write_text('{"status":"old"}')
        self.git('add', '.')
        self.git('commit', '-qm', 'tracked receipt')
        self.git('push', '-q', 'origin', 'integration')
        receipt.write_text('{"status":"new"}')
        self.git('add', 'native/evidence/receipt.json')
        self.assertEqual(self.run_ratchet(80).returncode, 0)
        self.assertEqual(self.git('show', 'HEAD:native/evidence/receipt.json'), '{"status":"old"}')
        self.assertEqual(receipt.read_text(), '{"status":"new"}')

    def test_concurrent_remote_change_is_not_overwritten(self):
        competitor = self.root.parent / 'competitor'
        subprocess.run(['git', 'clone', '-q', '-b', 'integration', str(self.remote), str(competitor)], check=True)
        (competitor / 'other-agent.txt').write_text('concurrent work\n')
        subprocess.run(['git', 'add', '.'], cwd=competitor, check=True)
        subprocess.run(['git', '-c', 'user.name=Other', '-c', 'user.email=other@example.test',
                        'commit', '-qm', 'other agent'], cwd=competitor, check=True)
        subprocess.run(['git', 'push', '-q', 'origin', 'integration'], cwd=competitor, check=True)
        remote = self.git('ls-remote', 'origin', 'refs/heads/integration').split()[0]
        self.assertNotEqual(self.run_ratchet(80).returncode, 0)
        self.assertEqual(remote, self.git('ls-remote', 'origin', 'refs/heads/integration').split()[0])

if __name__ == '__main__':
    unittest.main()
