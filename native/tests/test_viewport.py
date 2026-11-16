"""Viewport dimensions follow caller needs, not the former 240 by 100 ceiling."""
import ctypes as C,unittest,sys,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class Viewport(unittest.TestCase):
    def setUp(self):self.s=NativeScene();self.addCleanup(self.s.close)
    def testPopulatedNarrowViewportDoesNotCrashOrLoseDocuments(self):
        script='''from nocturne_native import NativeScene
s=NativeScene()
s.command(dict(op='window',id=1,title='retained title',text='retained document'))
s.command(dict(op='draft',text='abcdef',emitWeather=False))
for w,h in [(3,5),(1,1),(2,2),(4,6),(5,7),(160,48)]:
 s.command(dict(op='resize',width=w,height=h))
 before=s.snapshot();f=s.render()
 assert (f.width,f.height)==(w,h)
 assert s.snapshot()==before
 assert s.info()['prompt']['text']=='abcdef'
s.close()
'''
        import os
        env=dict(os.environ,PYTHONPATH=str(ROOT/'bindings/python'))
        result=subprocess.run([sys.executable,'-c',script],env=env,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
    def testNarrowPromptVerticalMovementKeepsDirection(self):
        for width in [1,2,3,4,5]:
            self.s.command(dict(op='resize',width=width,height=5))
            self.s.command(dict(op='draft',text='abcdef',caret=3,emitWeather=False))
            self.s.command(dict(op='key',key='ArrowUp'))
            self.assertEqual(self.s.info()['prompt']['caret'],2)
            self.s.command(dict(op='key',key='ArrowDown'))
            self.assertEqual(self.s.info()['prompt']['caret'],3)
    def testWideTallAndLargeViewportsRenderExactDimensions(self):
        for w,h in [(400,24),(80,180),(320,120),(1024,16),(20,512),(1,1),(3,5)]:
            self.s.command(dict(op='resize',width=w,height=h));before=self.s.snapshot();f=self.s.render()
            self.assertEqual((f.width,f.height),(w,h));self.assertEqual(len(f.bytes),w*h*16);self.assertEqual(self.s.snapshot(),before)
    def testGrowShrinkAndRestoreRetainOwnedFrames(self):
        self.s.command(dict(op='resize',width=400,height=120));saved=self.s.snapshot();large=self.s.render();copied=large.bytes
        self.s.command(dict(op='resize',width=32,height=12));small=self.s.render()
        self.s.restore(saved);self.assertEqual(self.s.render().bytes,copied);self.assertEqual(large.bytes,copied);self.assertEqual((small.width,small.height),(32,12))
    def testRepresentationAndNonpositiveSizesRejectAtomically(self):
        for w,h in [(0,48),(-1,48),(160,0),(160,-1),(1.5,48),(2**32,48),(2**31,1),(65536,65536)]:
            saved=self.s.snapshot()
            with self.assertRaises(ValueError):self.s.command(dict(op='resize',width=w,height=h))
            self.assertEqual(saved,self.s.snapshot())
    def testExternalBufferFailureDoesNotReplaceWorkingMemory(self):
        lib=self.s._lib;lib.nrRenderMemorySize.argtypes=[C.c_void_p];lib.nrRenderMemorySize.restype=C.c_uint64
        lib.nrSetRenderMemory.argtypes=[C.c_void_p,C.c_void_p,C.c_uint64];lib.nrSetRenderMemory.restype=C.c_int
        self.s.command(dict(op='resize',width=320,height=120));self.s.render();expected=self.s.render().bytes;before=self.s.snapshot()
        memory=C.create_string_buffer(64)
        self.assertEqual(lib.nrSetRenderMemory(self.s._context,memory,64),-1)
        self.assertEqual(lib.nrSetRenderMemory(self.s._context,self.s._context,lib.nrRenderMemorySize(self.s._context)),-1)
        self.assertEqual(lib.nrSetRenderMemory(self.s._context,C.byref(memory,1),64),-1)
        self.assertEqual(self.s.render().bytes,expected);self.assertEqual(before,self.s.snapshot())
    def testNativeWithoutLargeScratchFailsSafelyThenBindingCanRecover(self):
        self.s.command(dict(op='resize',width=400,height=120));before=self.s.snapshot()
        self.assertEqual(self.s._lib.nrRender(self.s._context),0)
        self.assertEqual(before,self.s.snapshot());self.assertEqual(self.s.render().width,400)
    def testRecoverFromUnallocatedHugeViewportWithoutRenderingIt(self):
        self.s.command(dict(op='resize',width=1000000,height=100))
        self.s.command(dict(op='reset'));self.assertEqual(self.s.render().width,160)
    def testPointerBeyondFormerCoordinateBoundAndResizeProvisioning(self):
        self.s.command(dict(op='resize',width=2048,height=16))
        self.s.command(dict(op='pointer',phase='move',x=1800,y=8))
        self.assertEqual(self.s.render().width,2048)
