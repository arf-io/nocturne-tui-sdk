"""Real snapshot-layout compatibility across the Contracts 6/7 source merge."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import gzip
from pathlib import Path
import sys
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bindings/python"))
from nocturne_native import NativeScene
from native.tests.current_writer_contract import current_schema

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name):
    return gzip.decompress((FIXTURES / name).read_bytes())


class SnapshotLayoutMerge(unittest.TestCase):
    def setUp(self):
        self.scene = NativeScene(5001)

    def tearDown(self):
        self.scene.close()

    def assertRejectedWithoutMutation(self, payload):
        before = self.scene.snapshot()
        with self.assertRaises(ValueError):
            self.scene.restore(bytes(payload))
        self.assertEqual(self.scene.snapshot(), before)

    def testIncomingExpandedSchema03FixtureLoadsAndPromotesToCurrent06(self):
        data = fixture("schema-20261003-contracts7-registered-style.snapshot.gz")
        original = bytes(data)
        self.assertEqual(int.from_bytes(data[12:16], "little"), 0x20261003)
        self.assertEqual(int.from_bytes(data[16:20], "little"), 4_498_608)
        self.scene.restore(data)
        self.assertEqual(data, original)
        info = self.scene.info()
        self.assertEqual(info["registeredStates"][0]["path"], "/lab/one")
        self.assertEqual(info["styleRules"][0]["id"], 1)
        emitted = self.scene.snapshot()
        self.assertEqual(int.from_bytes(emitted[12:16], "little"), current_schema())
        self.assertEqual(int.from_bytes(emitted[16:20], "little"), len(emitted)-24)
        self.scene.restore(emitted)
        self.assertEqual(self.scene.info()["registeredStates"][0]["path"], "/lab/one")

    def testLocalLegacySchema03RemainsDistinctFromExpandedSchema03(self):
        data = fixture("schema-20261003-retained-intent-selector.snapshot.gz")
        original = bytes(data)
        self.assertEqual(int.from_bytes(data[12:16], "little"), 0x20261003)
        self.assertEqual(int.from_bytes(data[16:20], "little"), 4_414_376)
        self.scene.restore(data)
        self.assertEqual(data, original)
        self.assertEqual(self.scene.info()["triggers"][0]["intentCandidate"]["value"], 7)
        emitted = self.scene.snapshot()
        self.assertEqual(int.from_bytes(emitted[12:16], "little"), current_schema())
        self.assertEqual(self.scene.info()["registeredStates"], [])

    def testLocalSchema04IntentActionSurvivesMigration(self):
        data = fixture("schema-20261004-intent-action.snapshot.gz")
        original = bytes(data)
        self.assertEqual(int.from_bytes(data[12:16], "little"), 0x20261004)
        self.scene.restore(data)
        self.assertEqual(data, original)
        rule = self.scene.info()["triggers"][0]
        self.assertEqual(rule["valueSource"], "intentValue")
        self.assertEqual(rule["event"], "/approved")
        self.assertEqual(int.from_bytes(self.scene.snapshot()[12:16], "little"), current_schema())

    def testExpandedSchema03CannotBeRelabeledAsLocal04(self):
        data = bytearray(fixture("schema-20261003-contracts7-registered-style.snapshot.gz"))
        data[12:16] = (0x20261004).to_bytes(4, "little")
        data[20:24] = (zlib.crc32(data[24:]) & 0xffffffff).to_bytes(4, "little")
        self.assertRejectedWithoutMutation(data)

    def testKnownSchemaRejectsWrongLengthTruncationAndBadChecksum(self):
        expanded = fixture("schema-20261003-contracts7-registered-style.snapshot.gz")
        self.assertRejectedWithoutMutation(expanded[:-1])
        self.assertRejectedWithoutMutation(expanded + b"\0")
        bad_crc = bytearray(expanded)
        bad_crc[24 + 512] ^= 1
        self.assertRejectedWithoutMutation(bad_crc)
        old = fixture("schema-20261004-intent-action.snapshot.gz")
        wrong_size = bytearray(old)
        wrong_size[16:20] = (4_498_608).to_bytes(4, "little")
        self.assertRejectedWithoutMutation(wrong_size)

    def testUnknownSchemaRejectsWithoutMutation(self):
        data = bytearray(fixture("schema-20261003-contracts7-registered-style.snapshot.gz"))
        data[12:16] = (0x202610ff).to_bytes(4, "little")
        data[20:24] = (zlib.crc32(data[24:]) & 0xffffffff).to_bytes(4, "little")
        self.assertRejectedWithoutMutation(data)


if __name__ == "__main__":
    unittest.main()
