"""Official Unicode 17 oracle and actual native cluster editing boundaries."""
import ctypes as C,hashlib,json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class Grapheme(unittest.TestCase):
    def setUp(self):self.s=NativeScene();self.addCleanup(self.s.close)
    def boundaries(self,values,capacity=None):
        fn=self.s._lib.nrGraphemeBreaks;fn.argtypes=[C.POINTER(C.c_uint32),C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32];fn.restype=C.c_int
        source=(C.c_uint32*max(1,len(values)))(*values);size=len(values)+1 if capacity is None else capacity
        out=(C.c_uint32*max(size,1))(*([0xdeadbeef]*max(size,1)))
        result=fn(source,len(values),out,size)
        return result,list(out)
    def testOfficialUnicode17ExtendedGraphemeConformance(self):
        folder=ROOT/'unicode/17.0.0';manifest=json.loads((folder/'SOURCES.json').read_text())
        for r in manifest['sources']:self.assertEqual(hashlib.sha256((folder/r['name']).read_bytes()).hexdigest(),r['sha256'])
        cases=0
        for line in (folder/'GraphemeBreakTest.txt').read_text().splitlines():
            line=line.split('#')[0].strip()
            if not line:continue
            scalars=[];expected=[]
            for word in line.split():
                if word=='÷':expected.append(len(scalars))
                elif word!='×':scalars.append(int(word,16))
            n,out=self.boundaries(scalars)
            self.assertEqual(out[:n],expected,line);cases+=1
        self.assertEqual(cases,766)
    def testInvalidScalarAndSmallCapacityLeaveOutputUntouched(self):
        for values,capacity in [([0xd800],2),([0x110000],2),([65,66],2)]:
            n,out=self.boundaries(values,capacity);self.assertEqual(n,-1);self.assertEqual(out,[0xdeadbeef]*capacity)
    def testEmptyAndMaximumAsciiBoundaries(self):
        for values in ([],[65]*2048):
            n,out=self.boundaries(values);self.assertEqual(n,len(values)+1);self.assertEqual(out[:n],list(range(len(values)+1)))
    def testOwnedBindingAndNativeFunctionArePure(self):
        before=self.s.snapshot();out=self.s.grapheme_boundaries('Ae\u0301👩\u200d🔧🇺🇸Z')
        self.assertEqual(out,[0,1,3,6,8,9]);self.assertEqual(before,self.s.snapshot())
        out[0]=999;self.assertEqual(self.s.grapheme_boundaries('a'),[0,1])
    def draft(self,text,caret=None):
        c=dict(op='draft',text=text,emitWeather=False)
        if caret is not None:c['caret']=caret
        self.s.command(c)
    def key(self,key):self.s.command(dict(op='key',key=key,unit='grapheme'))
    def testBackspaceDeletesWholeCombiningEmojiAndFlagClusters(self):
        self.draft('Ae\u0301👩\u200d🔧🇺🇸Z')
        for expected in ['Ae\u0301👩\u200d🔧🇺🇸','Ae\u0301👩\u200d🔧','Ae\u0301','A','']:
            self.key('Backspace');self.assertEqual(self.s.info()['prompt']['text'],expected)
    def testArrowMovementAndDeleteUseExtendedBoundaries(self):
        text='Ae\u0301👩\u200d🔧🇺🇸Z';self.draft(text)
        for expected in [8,6,3,1,0]:self.key('ArrowLeft');self.assertEqual(self.s.info()['prompt']['caret'],expected)
        for expected in [1,3,6,8,9]:self.key('ArrowRight');self.assertEqual(self.s.info()['prompt']['caret'],expected)
        self.key('Home');self.key('Delete');self.assertEqual(self.s.info()['prompt']['text'],text[1:])
    def testInteriorCaretDeletesContainingClusterAndUndoRetainsSource(self):
        self.draft('Ae\u0301Z',2);self.key('Backspace');self.assertEqual(self.s.info()['prompt']['text'],'AZ')
        self.s.command(dict(op='key',key='z',ctrl=True));self.assertEqual(self.s.info()['prompt']['text'],'Ae\u0301Z')
    def testUnknownUnitRejectsAtomically(self):
        saved=self.s.snapshot()
        with self.assertRaises(ValueError):self.s.command(dict(op='key',key='Backspace',unit='word'))
        self.assertEqual(saved,self.s.snapshot())
    def testOfflineTableRegenerationMatchesPinnedSource(self):
        result=subprocess.run([sys.executable,str(ROOT/'scripts/generate_grapheme.py'),'--check'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
    def testSizingProbeAndCountBounds(self):
        self.boundaries([]);fn=self.s._lib.nrGraphemeBreaks;one=(C.c_uint32*1)(65);out=(C.c_uint32*1)(0xdeadbeef)
        self.assertEqual(fn(None,0,None,0),1);self.assertEqual(fn(one,1,None,0),2)
        large=(C.c_uint32*2049)(*([65]*2049));self.assertEqual(fn(large,2049,None,0),2050);self.assertEqual(fn(large,2049,out,1),-1);self.assertEqual(fn(None,1,out,1),-1);self.assertEqual(out[0],0xdeadbeef)
    def testOwnedBindingRejectsSurrogatesAndCapacityWithoutMutation(self):
        before=self.s.snapshot()
        for text in ('\ud800','A'*2049):
            with self.assertRaises(ValueError):self.s.grapheme_boundaries(text)
        self.assertEqual(before,self.s.snapshot())
