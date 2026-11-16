"""Actual child-process fixtures verify publish atomicity; these are not host qualification."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,tempfile,time,unittest
ROOT=Path(__file__).resolve().parents[1]
class UnicodeDocumentGate(unittest.TestCase):
 def run_gate(self,root):
  # Load the unchanged production gate; only its explicit test source root differs.
  code="import importlib.util;from pathlib import Path;s=importlib.util.spec_from_file_location('actual_gate',"+repr(str(ROOT/'scripts/check_unicode_document_hosts.py'))+");m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.ROOT=Path("+repr(str(root))+");m.main()"
  env=dict(os.environ);env['PYTHONPATH']=str(ROOT/'scripts');env['PYTHONDONTWRITEBYTECODE']='1'
  argv=[sys.executable,'-c',code];started=time.time()
  child=subprocess.Popen(argv,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);output,_=child.communicate();result=subprocess.CompletedProcess(argv,child.returncode,output)
  evidence=ROOT/'evidence/unicode-gate-unit-children'/str(time.time_ns());evidence.mkdir(parents=True);(evidence/'child.log').write_text(output)
  (evidence/'RESULT.json').write_text(json.dumps({'scope':'negative publication-gate child fixture, not host qualification','argv':argv,'childPid':child.pid,'exitCode':child.returncode,'seconds':time.time()-started,'environmentSha256':hashlib.sha256(json.dumps(env,sort_keys=True).encode()).hexdigest(),'logSha256':hashlib.sha256((evidence/'child.log').read_bytes()).hexdigest()},indent=2)+'\n')
  return result
 def testLastHostFailureRetainsPreviousPublishedEvidence(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);out=root/'evidence/unicode-document-hosts';out.mkdir(parents=True);old=out/'RESULTS.json';old.write_bytes(b'previous')
   (root/'hosts/bubbletea').mkdir(parents=True);(root/'hosts/bubbletea/go.mod').write_text('module document_gate_fixture\n\ngo 1.22\n');(root/'hosts/bubbletea/main.go').write_text('package main\nfunc main() {}\n')
   rust=root/'hosts/ratatui';(rust/'examples').mkdir(parents=True);(rust/'Cargo.toml').write_text('[package]\nname="document-gate-failure-fixture"\nversion="0.1.0"\nedition="2021"\n')
   # Real compiled negative child deliberately exits7, never claims a passing host.
   (rust/'examples/unicode_document.rs').write_text('fn main(){std::process::exit(7);}\n')
   (rust/'Cargo.lock').write_text('version = 4\n\n[[package]]\nname = "document-gate-failure-fixture"\nversion = "0.1.0"\n')
   scripts=root/'scripts';scripts.mkdir();calls=root/'actual-host-calls.jsonl'
   driver="import argparse,json,subprocess,sys;from pathlib import Path;sys.path.insert(0,"+repr(str(ROOT/'bindings/python'))+");from nocturne_native import NativeScene\np=argparse.ArgumentParser();p.add_argument('--host');p.add_argument('--binary');p.add_argument('--output');a=p.parse_args();f=Path("+repr(str(calls))+");f.open('a').write(json.dumps({'host':a.host})+'\\n')\nif a.host=='ratatui':subprocess.run([a.binary],check=True)\nwith NativeScene() as s:\n s.command({'op':'draft','text':'Actual ABI fixture é中👩‍🚀','emitWeather':False});before=s.snapshot();frame=s.render();assert s.snapshot()==before;data=frame.bytes\nd=Path(a.output);d.mkdir();names=['terminal.bin','scroll-terminal.bin'] if a.host in ['standalone','prompt-toolkit'] else ['terminal.bin','shift-navigation.bin','drag-selection.bin']\nfor name in names:(d/name).write_bytes(data)\n(d/'RESULTS.json').write_text(json.dumps({'passed':True,'host':a.host,'scope':'C ABI child fixture, not terminal host qualification','sourceFiles':{}}))\n"
   for name in ['check_unicode_document.py','check_bubbletea_unicode.py']:(scripts/name).write_text(driver)
   result=self.run_gate(root);self.assertNotEqual(result.returncode,0,result.stdout);self.assertIn('returned non-zero exit status 7',result.stdout)
   hosts=[json.loads(line)['host'] for line in calls.read_text().splitlines()];self.assertEqual(hosts,['standalone','prompt-toolkit','bubbletea','ratatui'])
   self.assertEqual(old.read_bytes(),b'previous');self.assertEqual(list(out.iterdir()),[old]);self.assertEqual(list((root/'evidence').iterdir()),[out])
 def testRedirectedOutputRejectedBeforeBuild(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'evidence').mkdir();target=root/'target';target.mkdir();(root/'evidence/unicode-document-hosts').symlink_to(target,target_is_directory=True)
   result=self.run_gate(root);self.assertNotEqual(result.returncode,0);self.assertIn('Unicode document output cannot be a symlink',result.stdout);self.assertEqual(list(target.iterdir()),[])
