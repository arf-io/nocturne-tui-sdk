import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import pathlib,os,sys,hashlib,importlib.util,unittest,json
W=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);sys.path.insert(0,str(W));from native.bindings.python.nocturne_native import NativeScene as RealScene
trace=[];sha=lambda b:hashlib.sha256(b).hexdigest();current=None
class RecordedScene:
 def __init__(self,*args,**kwargs):
  self.s=RealScene(*args,**kwargs);self.rows=[];self.slots={};trace.append({'seed':args[0]if args else 2030,'steps':self.rows})
 def close(self):self.rows.append({'op':'close'});self.s.close()
 def command(self,c):
  try:r=self.s.command(c)
  except ValueError:self.rows.append({'op':'command','command':c,'reject':True});raise
  self.rows.append({'op':'command','command':c,'reject':False});return r
 def info(self):
  r=self.s.info();self.rows.append({'op':'info','expected':r});return r
 def render(self):
  r=self.s.render();self.rows.append({'op':'render','sha256':sha(r.bytes)});return r
 def snapshot(self):
  r=self.s.snapshot();digest=sha(r);slot=self.slots.setdefault(digest,len(self.slots));self.rows.append({'op':'snapshot','slot':slot,'sha256':digest});return r
 def restore(self,b):
  self.s.restore(b);self.rows.append({'op':'restore','slot':self.slots[sha(b)]})
 def advance_to(self,t):self.s.advance_to(t);self.rows.append({'op':'advance','timeUs':t})
spec=importlib.util.spec_from_file_location('pointer_tests',W/'native/tests/test_workbench_pointer_preservation.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.NativeScene=RecordedScene
names=unittest.defaultTestLoader.getTestCaseNames(m.WorkbenchPointerPreservation);names.remove('test_native_wasm_replays_every_focused_public_call');assert len(names)==8
result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(m.WorkbenchPointerPreservation(name)for name in names));out.write_text(json.dumps({'schema':'nocturne.actual-public-pointer-trace.v1','scope':'Real native calls and returned whole frame/snapshot hashes from all8 independent methods; WASM executes the same public trace. This is cross-backend parity, not original-renderer wholeframe equivalence.','trace':trace},separators=(',',':')));raise SystemExit(0 if result.wasSuccessful()else 1)
