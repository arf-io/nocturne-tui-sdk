from pathlib import Path
import importlib.util,json,subprocess,tempfile,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('document_gate',ROOT/'scripts/check_document_persistence.py');gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
class DocumentGate(unittest.TestCase):
 def testFailedChildCannotReplacePreviousArtifacts(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);out=root/'evidence/document-persistence';out.mkdir(parents=True);old=out/'RESULTS.json';old.write_bytes(b'previous')
   with patch.object(gate,'ROOT',root),patch.object(gate.subprocess,'run',side_effect=subprocess.CalledProcessError(2,['host'])):
    with self.assertRaises(subprocess.CalledProcessError):gate.main()
   self.assertEqual(old.read_bytes(),b'previous');self.assertEqual(list(root.joinpath('evidence').iterdir()),[out])
 def testSecondHostFailurePreservesPreviousPublishedArtifacts(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);out=root/'evidence/document-persistence';out.mkdir(parents=True);old=out/'RESULTS.json';old.write_bytes(b'previous');calls=[]
   def child(argv,**kwargs):
    calls.append(argv)
    if len(calls)==2:raise subprocess.CalledProcessError(2,argv)
    fresh=Path(argv[argv.index('--output')+1]);fresh.mkdir(parents=True)
    for name in ['roundtrip-pty.bin','rejected-pty.bin','saved-document.json','scene-switch-pty.bin','empty-scene-switch-pty.bin','scene-undo-pty.bin']:fresh.joinpath(name).write_bytes(b'new')
    fresh.joinpath('RESULTS.json').write_text(json.dumps(dict(passed=True,host='prompt-toolkit')))
   with patch.object(gate,'ROOT',root),patch.object(gate.subprocess,'run',side_effect=child):
    with self.assertRaises(subprocess.CalledProcessError):gate.main()
   self.assertEqual(len(calls),2);self.assertEqual(old.read_bytes(),b'previous');self.assertEqual(list(out.iterdir()),[old])
 def testSymlinkDestinationIsRejectedBeforeExecution(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'evidence').mkdir();(root/'target').mkdir();(root/'evidence/document-persistence').symlink_to(root/'target',target_is_directory=True)
   with patch.object(gate,'ROOT',root),patch.object(gate.subprocess,'run') as run:
    with self.assertRaises(ValueError):gate.main()
    run.assert_not_called()
if __name__=='__main__':unittest.main()
