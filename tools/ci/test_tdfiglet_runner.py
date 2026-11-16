"""Synthetic child failures test orchestration, not TDF/native/WASM acceptance."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import check_tdfiglet


class TdfigletRunner(unittest.TestCase):
    def fixture(self, directory):
        root = Path(directory)
        font, binary = root / 'font.tdf', root / 'tdfiglet'
        font.write_bytes(b'synthetic font')
        binary.write_bytes(b'synthetic executable; never executed')
        return binary, font, root / 'results'

    def invoke(self, binary, font, output, executor):
        digest = hashlib.sha256(font.read_bytes()).hexdigest()
        with patch.object(check_tdfiglet, 'FONT_SHA256', digest):
            report = check_tdfiglet.run(binary, font, output, executor=executor)
        self.assertEqual(json.loads((output / 'RESULTS.json').read_text()), report)
        return report

    def test_timeout_is_retained_and_later_fonts_execute(self):
        observed = []
        def execute(command, **kwargs):
            observed.append(command)
            self.assertEqual(kwargs['timeout'], 180)
            if '--subfont' in command and command[command.index('--subfont') + 1] == '0':
                raise subprocess.TimeoutExpired(command, 180)
            return subprocess.CompletedProcess(command, 0)
        with tempfile.TemporaryDirectory() as directory:
            report = self.invoke(*self.fixture(directory), execute)
        self.assertTrue(report['complete'])
        self.assertFalse(report['passed'])
        self.assertEqual(len(observed), 5)
        self.assertEqual([row['status'] for row in report['attempts']],
                         ['FAIL', 'NOT_EXECUTED', 'PASS', 'PASS', 'PASS', 'PASS'])
        self.assertEqual(report['attempts'][0]['errorType'], 'TimeoutExpired')

    def test_wasm_failure_cannot_be_hidden_by_later_success(self):
        def execute(command, **kwargs):
            return subprocess.CompletedProcess(command, 7 if any(argument.endswith('subfont-2/cases.json') for argument in command) else 0)
        with tempfile.TemporaryDirectory() as directory:
            report = self.invoke(*self.fixture(directory), execute)
        self.assertFalse(report['passed'])
        self.assertEqual(report['attempts'][3]['exitCode'], 7)
        self.assertEqual(report['attempts'][-1]['status'], 'PASS')

    def test_success_requires_all_six_runtime_attempts_in_both_modes(self):
        def execute(command, **kwargs):
            if '--mode' in command:
                self.assertEqual(command[command.index('--mode') + 1], 'both')
            return subprocess.CompletedProcess(command, 0)
        with tempfile.TemporaryDirectory() as directory:
            report = self.invoke(*self.fixture(directory), execute)
        self.assertTrue(report['passed'])
        self.assertEqual(len(report['attempts']), 6)

    def test_wrong_font_and_existing_receipts_are_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            binary, font, output = self.fixture(directory)
            def unexpected(*args, **kwargs):
                self.fail('Rejected inputs must not launch children')
            with self.assertRaises(ValueError):
                check_tdfiglet.run(binary, font, output, executor=unexpected)
            self.assertFalse(output.exists())
            output.mkdir()
            marker = output / 'preserved.txt'
            marker.write_text('old receipt')
            with patch.object(check_tdfiglet, 'FONT_SHA256', hashlib.sha256(font.read_bytes()).hexdigest()):
                with self.assertRaises(FileExistsError):
                    check_tdfiglet.run(binary, font, output, executor=unexpected)
            self.assertEqual(marker.read_text(), 'old receipt')


if __name__ == '__main__':
    unittest.main()
