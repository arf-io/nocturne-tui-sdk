"""Real files and Git repositories for SDK delivery; tests precede implementation."""
import json,subprocess,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from delivery_integrity import closeDelivery,verifyDelivery,exportPatch,verifyPatch
class DeliveryIntegrity(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()
    def test_inventory_and_ordered_split_reassembly(self):
        out=self.root/'out';out.mkdir();(out/'SDK.zip').write_bytes(bytes(range(256))*9)
        closeDelivery(out,partBytes=700)
        result=verifyDelivery(out);self.assertTrue(result['passed']);self.assertEqual(result['reassembledFiles'],1)
        manifest=json.loads((out/'DELIVERY.json').read_text());self.assertIn('SDK.zip',manifest['files']);self.assertTrue((out/'SHA256SUMS.txt').is_file())
    def test_corrupt_missing_and_changed_files_reject(self):
        for failure in ['corrupt','missing','changed']:
            with self.subTest(failure=failure):
                out=self.root/failure;out.mkdir();(out/'SDK.zip').write_bytes(b'abcdefgh'*200);closeDelivery(out,partBytes=500)
                part=next(out.glob('*.part-*'))
                if failure=='missing':part.unlink()
                elif failure=='corrupt':part.write_bytes(b'bad')
                else:(out/'SDK.zip').write_bytes(b'changed')
                with self.assertRaises(ValueError):verifyDelivery(out)
    def test_symlink_and_manifest_traversal_reject(self):
        out=self.root/'out';out.mkdir();(self.root/'outside').write_bytes(b'secret');(out/'link').symlink_to(self.root/'outside')
        with self.assertRaises(ValueError):closeDelivery(out)
        (out/'link').unlink();(out/'SDK.zip').write_bytes(b'abc');closeDelivery(out)
        p=out/'DELIVERY.json';d=json.loads(p.read_text());d['files']['../outside']={'bytes':6,'sha256':'0'*64};p.write_text(json.dumps(d))
        with self.assertRaises(ValueError):verifyDelivery(out)
    def test_actual_git_patch_replay_and_wrong_baseline(self):
        repo=self.root/'repo';repo.mkdir()
        def git(*args):return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.STDOUT,text=True).strip()
        git('init');git('config','user.name','Delivery test');git('config','user.email','delivery@example.invalid')
        (repo/'source.txt').write_text('old\n');git('add','.');git('commit','-m','baseline');base=git('rev-parse','HEAD')
        (repo/'binary.dat').write_bytes(bytes(range(256)));(repo/'source.txt').write_text('Unicode 中\n');(repo/'run.sh').write_text('#!/bin/sh\nexit 0\n');(repo/'run.sh').chmod(0o755);git('add','.');git('commit','-m','change');head=git('rev-parse','HEAD')
        out=self.root/'patch';out.mkdir();record=exportPatch(repo,base,head,out)
        self.assertTrue(verifyPatch(repo,record,out,self.root/'restored')['passed'])
        record=dict(record,baseline=head)
        with self.assertRaises(ValueError):verifyPatch(repo,record,out,self.root/'wrong')

class DeliveryNegativeInventory(DeliveryIntegrity):
    def test_unadvertised_file_and_checksum_changes_reject(self):
        for failure in ['extra','checksum','order']:
            with self.subTest(failure=failure):
                out=self.root/failure;out.mkdir();(out/'SDK.zip').write_bytes(b'abcd'*400);closeDelivery(out,partBytes=500)
                if failure=='extra':(out/'extra').write_bytes(b'x')
                elif failure=='checksum':(out/'SHA256SUMS.txt').write_text('wrong')
                else:
                    p=out/'DELIVERY.json';d=json.loads(p.read_text());d['splits']['SDK.zip'].reverse();p.write_text(json.dumps(d))
                with self.assertRaises(ValueError):verifyDelivery(out)
