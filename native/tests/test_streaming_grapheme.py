import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import ctypes as C,sys,unittest,subprocess,tempfile,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
from native.tests.host_environment import node_executable,wasm_toolchain
class StreamingGrapheme(unittest.TestCase):
 def setUp(self):
  self.scene=NativeScene();self.addCleanup(self.scene.close);self.lib=self.scene._lib
  self.breaks=self.lib.nrGraphemeBreaks;self.breaks.argtypes=[C.POINTER(C.c_uint32),C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32];self.breaks.restype=C.c_int
  self.layout=self.lib.nrDocumentGraphemeLayout;self.layout.argtypes=[C.POINTER(C.c_uint32),C.c_uint32,C.c_uint32,C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32];self.layout.restype=C.c_int
  self.text='Aé👩‍🔧🇺🇸\t\r\n'.replace('\\t','\t').replace('\\r','\r').replace('\\n','\n')*30001
  self.source=(C.c_uint32*len(self.text))(*map(ord,self.text))
 def test_large_boundaries_layout_and_navigation(self):
  count=len(self.text);clusters=30001*6
  self.assertEqual(count,330011)
  self.assertEqual(self.breaks(self.source,count,None,0),clusters+1)
  out=(C.c_uint32*(clusters+1))();self.assertEqual(self.breaks(self.source,count,out,clusters+1),clusters+1)
  expected=[11*k+b for k in range(30001) for b in (0,1,3,6,8,9)]+[count]
  self.assertEqual(list(out),expected)
  rows=(C.c_uint32*(clusters*5))();self.assertEqual(self.layout(self.source,count,1,10,rows,clusters),clusters)
  expected_rows=[]
  for k in range(30001):
   for a,b,x,w in [(0,1,0,1),(1,3,1,1),(3,6,2,2),(6,8,4,2),(8,9,6,2),(9,11,8,0)]:expected_rows.extend([11*k+a,11*k+b,x,k,w])
  self.assertEqual(list(rows),expected_rows)
  for name,want in [('Before',330003),('After',330006),('Floor',330003)]:
   fn=getattr(self.lib,'nrGrapheme'+name);fn.argtypes=[C.POINTER(C.c_uint32),C.c_int,C.c_int];fn.restype=C.c_int
   self.assertEqual(fn(self.source,count,330005),want)
 def test_large_invalid_and_short_output_are_atomic(self):
  out=(C.c_uint32*30)(*([0xdeadbeef]*30))
  self.assertEqual(self.breaks(self.source,len(self.text),out,30),-1)
  self.assertEqual(self.layout(self.source,len(self.text),1,10,out,6),-1)
  self.source[-1]=0xd800
  self.assertEqual(self.breaks(self.source,len(self.text),None,0),-1)
  self.assertEqual(self.layout(self.source,len(self.text),1,10,out,6),-1)
  self.assertEqual(list(out),[0xdeadbeef]*30)
 def test_import_free_wasm_with_64k_stack(self):
  clang,wasm_ld=wasm_toolchain();node=node_executable()
  with tempfile.TemporaryDirectory(prefix='nocturne-streaming-unicode-') as directory:
   dest=Path(directory);objects=[]
   for name in ['grapheme.c','text_width.c','wasm_mem.c']:
    obj=dest/(name+'.o');objects.append(str(obj))
    subprocess.run([clang,'--target=wasm32','-std=c11','-O2','-nostdlib','-ffreestanding','-fno-builtin','-I'+str(ROOT/'include'),'-I'+str(ROOT/'src'),'-I'+str(ROOT/'freestanding'),'-c',str(ROOT/'src'/name),'-o',str(obj)],check=True,capture_output=True,text=True)
   wasm=dest/'streaming.wasm'
   exports=['nrGraphemeBreaks','nrGraphemeBefore','nrGraphemeAfter','nrGraphemeFloor','nrDocumentGraphemeLayout','nrAlloc']
   subprocess.run([wasm_ld,'--no-entry','--export-memory','--stack-first','-z','stack-size=65536','--initial-memory=16777216',*[f'--export={x}' for x in exports],*objects,'-o',str(wasm)],check=True,capture_output=True,text=True)
   result=subprocess.run([node,str(ROOT/'tests/streaming_grapheme_wasm.mjs'),str(wasm)],check=True,capture_output=True,text=True)
   self.assertEqual(json.loads(result.stdout),{'status':'PASS','sourceScalars':330011,'exactClusters':180006,'exactLayoutWords':900030,'imports':0})
if __name__=='__main__':unittest.main()
