"""Release identity stays consistent across RELEASE.json, the runtime, the Rust crate and the API prose.

Readiness audit rows QUAL-3 and QUAL-5 (docs/1.0.0-READINESS-AUDIT-20261031.md): the runtime
reported 1.0.0-rc.2 while RELEASE.json said 1.0.0-rc.3, and three documents named three
different snapshot writers. These checks need no built library; the runtime readback itself is
asserted by test_prompt_appearance.test_runtime_build_matches_release_identity.
"""
import json
import re
import unittest
from pathlib import Path

NATIVE = Path(__file__).resolve().parents[1]
REPO = NATIVE.parent


class ReleaseIdentity(unittest.TestCase):
    def setUp(self):
        self.release = json.loads((REPO / 'RELEASE.json').read_text())

    def test_runtime_source_and_rust_crate_carry_the_release_build(self):
        build = self.release['build']
        state = (NATIVE / 'src/state.c').read_text()
        self.assertIn('{\\"build\\":\\"' + build + '\\"', state, 'nrInfo build string must equal RELEASE.json build')
        toml = (NATIVE / 'bindings/rust/Cargo.toml').read_text()
        self.assertRegex(toml, r'(?m)^version = "' + re.escape(build) + '"$')
        lock = (NATIVE / 'bindings/rust/Cargo.lock').read_text()
        self.assertRegex(lock, r'name = "nocturne-native"\nversion = "' + re.escape(build) + '"')

    def test_snapshot_schema_identity_matches_the_source_constant(self):
        header = (NATIVE / 'src/internal.h').read_text()
        schema = re.search(r'#define NR_STATE_SCHEMA (0x[0-9a-fA-F]+)u', header).group(1).lower()
        self.assertEqual(self.release['snapshotSchema'].lower(), schema)
        self.assertEqual(self.release['compiledArtifactSnapshotSchema'].lower(), schema)
        for name in ('CURRENT-API-1.0.0.md', 'native/docs/API.md'):
            text = (REPO / name).read_text()
            with self.subTest(document=name):
                self.assertIn(schema, text)
                self.assertIn(self.release['build'], text)

    def test_release_is_the_final_1_0_0(self):
        self.assertEqual(self.release['state'], 'RELEASE')
        self.assertEqual(self.release['build'], '1.0.0')
