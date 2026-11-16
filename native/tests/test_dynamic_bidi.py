import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import ctypes as C,sys,unittest,subprocess,tempfile,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
from native.tests.host_environment import node_executable,wasm_toolchain
class DynamicBidi(unittest.TestCase):
 def setUp(self):
  self.scene=NativeScene();self.addCleanup(self.scene.close);self.lib=self.scene._lib
  self.fn=self.lib.nrDocumentBidiClusterLayout
  self.fn.argtypes=[C.POINTER(C.c_uint32)]+[C.c_uint32]*4+[C.POINTER(C.c_uint32),C.c_uint32,C.POINTER(C.c_uint32),C.c_uint64];self.fn.restype=C.c_int
  self.old=self.lib.nrBidiClusterLayout;self.old.argtypes=self.fn.argtypes[:7];self.old.restype=C.c_int
 def rows(self,text,columns=0xffffffff,direction=2):
  values=(C.c_uint32*max(1,len(text)))(*map(ord,text));out=(C.c_uint32*(max(1,len(text))*7))();scratch=(C.c_uint32*(40*(len(text)+1)))()
  n=self.fn(values,len(text),1,columns,direction,out,len(text),scratch,len(scratch));self.assertGreaterEqual(n,0)
  return [list(out[i*7:i*7+7]) for i in range(n)]
 def test_large_paragraph_keeps_remote_strong_context(self):
  text='אב'+' '*70000+'Z';rows=self.rows(text)
  self.assertEqual(len(rows),70003)
  self.assertEqual([r[0] for r in rows],list(range(70002,-1,-1)))
  for x,r in enumerate(rows):self.assertEqual(r,[70002-x,70003-x,x,0,1,2 if x==0 else 1,ord(text[70002-x])])
 def test_many_whole_paragraphs_keep_exact_layout(self):
  unit=self.rows('אב\n');rows=self.rows('אב\n'*25001,80)
  self.assertEqual(len(rows),len(unit)*25001)
  for k in range(25001):
   for j,ref in enumerate(unit):
    want=ref.copy();want[0]+=k*3;want[1]+=k*3;want[3]+=k
    self.assertEqual(rows[k*len(unit)+j],want)
 def test_pinned_unicode_inputs_match_existing_layout(self):
  checked=0
  for line in (ROOT/'unicode/17.0.0/BidiCharacterTest.txt').read_text().splitlines():
   if not line or line.startswith('#'):continue
   fields=line.split(';');text=''.join(chr(int(c,16)) for c in fields[0].split());direction=int(fields[1])
   values=(C.c_uint32*max(1,len(text)))(*map(ord,text));out=(C.c_uint32*(max(1,len(text))*7))()
   n=self.old(values,len(text),1,11,direction,out,len(text));self.assertGreaterEqual(n,0)
   self.assertEqual(self.rows(text,11,direction),[list(out[i*7:i*7+7]) for i in range(n)])
   checked+=1
   if checked==1000:break
  self.assertEqual(checked,1000)
 def test_failures_leave_output_unchanged(self):
  values=(C.c_uint32*3)(0x5d0,65,0x5d1);out=(C.c_uint32*21)(*([99]*21));scratch=(C.c_uint32*160)()
  for capacity,words in [(2,160),(3,159)]:self.assertEqual(self.fn(values,3,1,80,2,out,capacity,scratch,words),-1)
  values[2]=0xd800;self.assertEqual(self.fn(values,3,1,80,2,out,3,scratch,160),-1)
  self.assertEqual(list(out),[99]*21)
 def test_import_free_wasm_large_paragraphs(self):
  clang,wasm_ld=wasm_toolchain();node=node_executable()
  with tempfile.TemporaryDirectory(prefix='nocturne-dynamic-bidi-') as directory:
   dest=Path(directory);objects=[]
   for name in ['bidi.c','grapheme.c','text_width.c','wasm_mem.c']:
    obj=dest/(name+'.o');objects.append(str(obj))
    subprocess.run([clang,'--target=wasm32','-std=c11','-O2','-nostdlib','-ffreestanding','-fno-builtin','-I'+str(ROOT/'include'),'-I'+str(ROOT/'src'),'-I'+str(ROOT/'freestanding'),'-c',str(ROOT/'src'/name),'-o',str(obj)],check=True,capture_output=True,text=True)
   wasm=dest/'dynamic-bidi.wasm'
   subprocess.run([wasm_ld,'--no-entry','--export-memory','--stack-first','-z','stack-size=65536','--initial-memory=33554432','--export=nrDocumentBidiClusterLayout','--export=nrAlloc',*objects,'-o',str(wasm)],check=True,capture_output=True,text=True)
   result=subprocess.run([node,str(ROOT/'tests/dynamic_bidi_wasm.mjs'),str(wasm)],check=True,capture_output=True,text=True)
   self.assertEqual(json.loads(result.stdout),{'status':'PASS','singleParagraphScalars':70003,'separateParagraphs':25001,'imports':0})
if __name__=='__main__':unittest.main()
