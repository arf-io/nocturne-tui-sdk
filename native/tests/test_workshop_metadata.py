import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import build_gallery
import qualify

class WorkshopMetadata(unittest.TestCase):
    def testWorkshopDataParticipatesInSourceFingerprint(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'web').mkdir()
            path=root/'web/workshop_fields.json';path.write_text('{}')
            before=qualify.fingerprint(root)['sha256'];path.write_text('{"changed":true}')
            self.assertNotEqual(before,qualify.fingerprint(root)['sha256'])

    def testSourceBoundMetadataAndStaleSourceRejection(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'web').mkdir();(root/'bindings/typescript').mkdir(parents=True)
            source=root/'bindings/typescript/contracts.ts';source.write_text('Current interface\n')
            record={'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'operations':['input'],
                    'fields':[{'op':'input','field':'text','types':['string'],'choices':[]}]}
            (root/'web/workshop_fields.json').write_text(json.dumps(record))
            self.assertEqual(build_gallery.readWorkshopMetadata(root),record)
            source.write_text('Changed interface\n')
            with self.assertRaises(ValueError):build_gallery.readWorkshopMetadata(root)

    def testPackagedHelpRequiresOnlyCurrentDataAndRejectsStaleFields(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'web').mkdir();(root/'bindings/typescript').mkdir(parents=True)
            source=root/'bindings/typescript/contracts.ts';source.write_text('Current interface')
            metadata={'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'operations':['input'],'fields':[{'op':'input','field':'text','types':['string'],'choices':[]}]}
            record={'schema':'nocturne.workshop-help.v1','sourceSha256':metadata['sourceSha256'],'parameters':{'input.text':{'description':'Inserted Unicode text','section':'Input','default':None,'sourceFields':['text']}}}
            path=root/'web/workshop_help.json';path.write_text(json.dumps(record))
            self.assertEqual(build_gallery.readWorkshopHelp(root,metadata),record)
            record['parameters']['input.missing']=record['parameters']['input.text'];path.write_text(json.dumps(record))
            with self.assertRaises(ValueError):build_gallery.readWorkshopHelp(root,metadata)
            record['parameters'].pop('input.missing');record['sourceSha256']='0'*64;path.write_text(json.dumps(record))
            with self.assertRaises(ValueError):build_gallery.readWorkshopHelp(root,metadata)

    def testPackagedHelpIsBoundToSourceFingerprint(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'web').mkdir();path=root/'web/workshop_help.json';path.write_text('{}')
            before=qualify.fingerprint(root)['sha256'];path.write_text('{"changed":true}')
            self.assertNotEqual(before,qualify.fingerprint(root)['sha256'])

    def testCommittedIndexRegeneratesFromTheContract(self):
        # scripts/workshop_fields.py is the index generator; the committed file must be its exact output.
        import os,subprocess
        module=os.environ.get('NOCTURNE_TYPESCRIPT_MODULE')
        if not module or not Path(module).is_file():self.skipTest('NOCTURNE_TYPESCRIPT_MODULE (TypeScript lib/typescript.js) is not set')
        version=subprocess.run(['node','-e','console.log(require(process.argv[1]).version)',module],capture_output=True,text=True,check=True).stdout.strip()
        if version!='5.8.3':self.skipTest('type strings in the index are those of TypeScript 5.8.3, found '+version)
        script=Path(__file__).resolve().parents[1]/'scripts/workshop_fields.py'
        result=subprocess.run([sys.executable,str(script),'--check','--typescript',module],capture_output=True,text=True,timeout=300)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

if __name__=='__main__':unittest.main()
