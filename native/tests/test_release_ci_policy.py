"""Static release-CI policy checks; these do not claim any hosted CI execution."""
from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/rc4-native.yml"
PINS = ROOT / "tools/ci/action-pins.json"

class ReleaseCiPolicyTests(unittest.TestCase):
    def setUp(self):
        self.workflow = WORKFLOW.read_text()

    def testAllExternalActionsUseVerifiedFullCommitPins(self):
        self.assertTrue(PINS.is_file(), "Missing verified action-pin provenance")
        pins = {row["repository"]: row for row in json.loads(PINS.read_text())}
        actions = re.findall(r"^\s+-?\s*uses:\s*([^@\s]+)@([^\s#]+)", self.workflow, re.MULTILINE)
        self.assertEqual(len(actions), 5)
        for repository, commit in actions:
            with self.subTest(repository=repository):
                self.assertRegex(commit, r"^[0-9a-f]{40}$")
                self.assertEqual(commit, pins[repository]["commit"])
                self.assertEqual(pins[repository]["type"], "commit")
                self.assertRegex(pins[repository]["tag"], r"^v[0-9]+$")
                self.assertEqual(pins[repository]["source"],
                                 "https://api.github.com/repos/" + repository + "/git/ref/tags/" + pins[repository]["tag"])

    def testManualLinuxAndMacosMatrixIsExplicit(self):
        self.assertIn("workflow_dispatch:", self.workflow)
        self.assertRegex(self.workflow, r"os:\s*\[ubuntu-24\.04,\s*macos-14\]")
        self.assertIn("fail-fast: false", self.workflow)
        self.assertIn("runs-on: " + "$" + "{{ matrix.os }}", self.workflow)
        self.assertNotRegex(self.workflow, re.compile(r"^\s+(push|pull_request):", re.MULTILINE))

    def testRust188IsInstalledAndSelectedExplicitly(self):
        self.assertIn("rustup toolchain install 1.88.0", self.workflow)
        self.assertIn("rustup which --toolchain 1.88.0 rustc", self.workflow)
        self.assertIn("RUSTC=", self.workflow)
        self.assertIn("RUSTDOC=", self.workflow)
        self.assertIn("CARGO_NET_OFFLINE:", self.workflow)

    def testPythonBrowserVersionUsesExistingPinnedRequirements(self):
        requirements = (ROOT / "tools/requirements-qualification.txt").read_text()
        self.assertIn("playwright==1.55.0", requirements)
        self.assertIn("-r tools/requirements-qualification.txt", self.workflow)
        self.assertNotIn("playwright==1.57.0", self.workflow)

    def testRealNativeAndDependencyHostGatesAreScheduled(self):
        for command in ("sh build-native.sh",
                        "sh qualify-native.sh --strict --capture",
                        "python3 native/scripts/qualify_dependency_hosts.py",
                        "python3 native/hosts/ratatui/qualify.py",
                        "python3 native/scripts/check_host_inputs.py"):
            self.assertIn(command, self.workflow)
        for host in ("prompt-toolkit", "terminal-kit", "bubbletea", "ratatui"):
            self.assertIn("--host " + host, self.workflow)
        self.assertIn("cargo fetch --locked", self.workflow)
        self.assertIn("go mod verify", self.workflow)
        self.assertIn("npm ci --prefix native/hosts/terminal-kit", self.workflow)
        self.assertNotIn("continue-on-error: true", self.workflow)

    def testUnavailableMacosFrameworkGateCannotPassSilently(self):
        self.assertIn("MacOS framework qualification remains blocked", self.workflow)
        self.assertIn('"status": "BLOCKED"', self.workflow)
        self.assertIn('"fullRC4Qualified": False', self.workflow)
        self.assertIn("exit 3", self.workflow)

    def testPerTargetEvidenceIsRetainedEvenWhenCommandsFail(self):
        self.assertIn("if: always()", self.workflow)
        self.assertIn("rc4-native-evidence-" + "$" + "{{ matrix.os }}", self.workflow)
        self.assertIn("$" + "{{ runner.temp }}/nocturne-ci/", self.workflow)
        self.assertIn("if-no-files-found: error", self.workflow)

if __name__ == "__main__":
    unittest.main()

