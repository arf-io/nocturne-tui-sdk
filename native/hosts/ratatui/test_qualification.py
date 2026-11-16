#!/usr/bin/env python3
"""Test the qualification infrastructure, not the Ratatui framework itself."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

from qualify import Screen, classifyCommand, runCommand, runPty, writeJson


class ReceiptTests(unittest.TestCase):
    def runChild(self, code, timeout=5, environment=None):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            env = dict(os.environ, **(environment or {}))
            result = runCommand("child", [sys.executable, "-c", code], root, env, root, timeout)
            receipt = json.loads((root / "child.json").read_text())
            self.assertEqual(receipt, result)
            self.assertNotEqual(result["status"], "RUNNING")
            self.assertTrue(result["logSha256"])
            return result, (root / "child.log").read_text()

    def testSuccessUsesActualExit(self):
        result, output = self.runChild("print('executed')")
        self.assertEqual((result["status"], result["exitCode"]), ("PASS", 0))
        self.assertIn("executed", output)

    def testNonzeroIsNotSuccess(self):
        result, output = self.runChild("import sys; print('failed'); sys.exit(7)")
        self.assertEqual((result["status"], result["exitCode"]), ("FAIL", 7))
        self.assertIn("failed", output)

    def testEnvironmentReachesTheChild(self):
        result, output = self.runChild("import os; print(os.environ['RUSTC'])", environment={"RUSTC": "/verified/rustc"})
        self.assertEqual(result["status"], "PASS")
        self.assertIn("/verified/rustc", output)

    def testTimeoutWaitsForKilledChild(self):
        result, _ = self.runChild("import signal; signal.pause()", timeout=0.15)
        self.assertEqual(result["status"], "TIMEOUT")
        self.assertLess(result["exitCode"], 0)
        with self.assertRaises(ProcessLookupError):
            os.kill(result["pid"], 0)

    def testMissingExecutableIsBlocked(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = runCommand("absent", [str(root / "no-executable")], root, os.environ.copy(), root, 1)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertIsNone(result["exitCode"])

    def testNonexecutableFileIsBlocked(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            executable = root / "not-executable"
            executable.write_text("not a program")
            executable.chmod(0o600)
            result = runCommand("permission", [str(executable)], root, os.environ.copy(), root, 1)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertIsNone(result["exitCode"])

    def testExistingReceiptIsNotOverwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            writeJson(root / "once.json", {"prior": True})
            with self.assertRaises(FileExistsError):
                runCommand("once", [sys.executable, "-c", "pass"], root, os.environ.copy(), root, 1)
            self.assertEqual(json.loads((root / "once.json").read_text()), {"prior": True})

    def testBadDeadlineRejectedBeforeSpawn(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for timeout in [0, -1, float("inf"), float("nan")]:
                with self.assertRaises(ValueError):
                    runCommand("bad", [sys.executable], root, os.environ.copy(), root, timeout)

    def testBadDependencyIntegrityIsFailureNotMissingCache(self):
        self.assertEqual(classifyCommand(101, "error: failed to download a crate: checksum mismatch"), "FAIL")

    def testDependencyErrorIsBlockedButRetainsCode(self):
        self.assertEqual(classifyCommand(101, "error: no matching package named `ratatui` found"), "BLOCKED")
        self.assertEqual(classifyCommand(101, "error[E0308]: mismatched types"), "FAIL")
        self.assertEqual(classifyCommand(0, "no matching package named"), "PASS")
        self.assertEqual(classifyCommand(7, "application failed"), "FAIL")


class PtyOracleTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "posix", "PTY oracle requires POSIX")
    def testExitBeforeRawSetupCannotPassCleanupQualification(self):
        # Adversarial infrastructure test: this is deliberately NOT a Ratatui host.
        # Merely writing a claimed exit trace and exiting 1 must not qualify cleanup.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            child = root / "early-exit"
            child.write_text(f"#!{sys.executable}\n" +
                "import json,sys\nfrom pathlib import Path\n" +
                "Path(sys.argv[sys.argv.index('--trace')+1]).write_text(" +
                "json.dumps({'event':'exit','note':'never entered raw mode','info':{}})+'\\n')\n" +
                "sys.exit(1)\n")
            child.chmod(0o700)
            result = runPty("early-exit", child, root, os.environ.copy(), 3, None, failure="setup")
            self.assertNotEqual(result["status"], "PASS")


class ScreenTests(unittest.TestCase):
    def testCursorAndIncrementalUtf8(self):
        screen = Screen(20, 10)
        for byte in b"\x1b[2;3H" + "é⣿".encode():
            screen.feed(bytes([byte]))
        self.assertEqual(screen.lines()[1][2:4], "é⣿")

    def testClearAndColorDoNotBecomeText(self):
        screen = Screen(20, 10)
        screen.feed(b"old\x1b[2J\x1b[H\x1b[38;2;1;2;3mNEW\x1b[0m")
        self.assertEqual(screen.lines()[0].rstrip(), "NEW")
        self.assertNotIn("old", "\n".join(screen.lines()))

    def testCarriageReturnAndEraseLine(self):
        screen = Screen(20, 10)
        screen.feed(b"abcdef\rQ\x1b[K")
        self.assertEqual(screen.lines()[0].rstrip(), "Q")

    def testAlternateExitRetainsLastPaintForInspection(self):
        screen = Screen(20, 10)
        screen.feed(b"\x1b[?1049hTITLE\x1b[?1049l")
        self.assertIn("TITLE", "\n".join(screen.lines()))

    def testResizeBoundsAndSplitCsi(self):
        screen = Screen(20, 10)
        screen.feed(b"\x1b[")
        screen.feed(b"999;999H.")
        self.assertEqual(screen.lines()[-1][-1], ".")
        screen.resize(30, 12)
        self.assertEqual((len(screen.lines()), len(screen.lines()[0])), (12, 30))


if __name__ == "__main__":
    unittest.main(verbosity=2)
