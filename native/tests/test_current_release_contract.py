"""Actual committed declaration versus native writer; authored before metadata repair."""
import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'native/bindings/python'))
sys.path.insert(0,str(ROOT/'native/scripts'))
from nocturne_native import NativeScene
from release_identity import loadReleaseIdentity

class CurrentReleaseContract(unittest.TestCase):
    def test_committed_release_matches_real_native_writer(self):
        release=loadReleaseIdentity(ROOT)
        with NativeScene(2030) as scene:
            source=scene.snapshot();info=scene.info_complete();contract=info['contract']
            self.assertEqual(info['build'],release['build'])
            self.assertEqual(release['abi'],contract['abiVersion'])
            self.assertEqual(int(release['snapshotSchema'],16),contract['snapshotSchema'])
            self.assertEqual(int.from_bytes(source[12:16],'little'),contract['snapshotSchema'])
            self.assertEqual(len(source),contract['snapshotCapacityBytes'])
            self.assertEqual(scene.snapshot(),source)
    def test_candidate_retains_honest_scope_and_nonblocking_pending_records(self):
        release=loadReleaseIdentity(ROOT)
        if release['state']=='RELEASE_CANDIDATE':self.assertIs(release['fullRC4Qualified'],False)
        self.assertEqual(release['releasePolicy'],'native/docs/RELEASE-POLICY-2026-10-06.md')
        for record in release['pendingReleaseItems']:self.assertIs(record['releaseBlocking'],False)
        historical=json.loads((ROOT/'BUILD-IDENTITY.json').read_text())
        self.assertEqual(historical['snapshotSchema'],'0x20261006')
        self.assertEqual(historical['sourceBaseline'],release['sourceBaseline'])
