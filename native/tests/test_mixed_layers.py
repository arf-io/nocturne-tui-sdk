"""Coverage ownership, explicit per-object styles, and leaf-detail acceptance."""
import ctypes as C
import json
from pathlib import Path
import subprocess
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
DOTS=(1,8,2,16,4,32,64,128)
class Cell(C.Structure):
    _fields_=[(name,C.c_uint32)for name in ('glyph','foreground','background','id')]
class MixedLayers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Compile a native fixture against the current implementation, not a mocked renderer.
        sources=[str(p)for p in sorted((ROOT/'src').glob('*.c'))if p.name!='wasm_mem.c']
        cls.fixture=ROOT/'dist/layer-fixture.so'
        subprocess.run(['cc','-shared','-fPIC','-std=c11','-O2','-ffp-contract=off','-fno-fast-math','-fno-math-errno','-I'+str(ROOT/'include'),'-I'+str(ROOT/'src'),*sources,str(ROOT/'tests/layer_fixture.c'),'-o',str(cls.fixture)],check=True,capture_output=True)
        cls.lib=C.CDLL(str(cls.fixture));cls.lib.layerProbe.argtypes=[C.c_uint,C.c_double,C.c_int,C.c_int,C.c_int,C.POINTER(Cell)]
    def probe(self,mask=23,alpha=.2,front=0,sampling=2,duplicates=1):
        cell=Cell();self.assertEqual(self.lib.layerProbe(mask,alpha,front,sampling,duplicates,C.byref(cell)),0);return cell
    def testGroundDoesNotBecomeForegroundMask(self):
        for m in range(1,256):
            a=self.probe(m,0);b=self.probe(m,.8)
            self.assertEqual(a.glyph,0x2800+m);self.assertEqual(b.glyph,a.glyph)
    def testOpaqueFloorBehindStillPreservesDetailedGeometry(self):
        self.assertEqual(self.probe(87,1).glyph,0x2857)
    def testOpaqueSurfaceInFrontOccludesRatherThanXray(self):
        self.assertEqual(self.probe(87,1,1).glyph,0x2580)
    def testTranslucentSurfaceInFrontPreservesTintedSilhouette(self):
        a=self.probe(23,0,1);b=self.probe(23,.5,1)
        self.assertEqual(a.glyph,b.glyph);self.assertNotEqual(a.foreground,b.foreground)
    def testRepeatedRasterSamplesDoNotAccumulateOpacity(self):
        a=self.probe(49,.3,0,2,1);b=self.probe(49,.3,0,2,8)
        self.assertEqual(bytes(a),bytes(b))
    def testExplicitBlockAndBrailleModesRemainDistinct(self):
        for m in (1,7,65,255):
            self.assertEqual(self.probe(m,.3,0,2).glyph,0x2800+m)
            self.assertEqual(self.probe(m,.3,0,1).glyph,0x2580)
    def testFloorOnlyIsNotAnUnrequestedBrailleRectangle(self):
        self.assertEqual(self.probe(0,.2).glyph,0x2580)
    def scene(self):
        s=NativeScene(42);self.addCleanup(s.close);s.command({'op':'environment','stars':0,'style':'solid'});return s
    def emitter(self,s,**patch):
        cfg=dict(op='emitter',id=1,effect='weather/autumn-drift',count=1,runningTimeMs=0,position=[0,6,0],extent=[0,0,0],velocity=[0,0,0],spread=[0,0,0],gravity=[0,0,0],wind=[0,0,0],windVariation=[0,0,0],drag=0,lift=0,tumble=[0,0,0],flutterHz=0,flutterAmount=0,sizeMin=6,sizeMax=6,deposit=False,collision=False,lifetimeMinMs=10000,lifetimeMaxMs=10000,birthFadeMs=0)
        cfg.update(patch);s.command(cfg)
    def testAuthoredDefaultIsNotGlobalBraille(self):
        s=self.scene();s.command({'op':'environment','style':'plasma'});s.advance_to(100000)
        self.assertTrue(any(g==0x2580 for g,fg,bg,ident in s.render().words()if ident==0))
    def testPerEmitterAndFloorPoliciesValidateAndReplay(self):
        s=self.scene();self.emitter(s,sampling='braille',surfaceAlpha=.15)
        s.command({'op':'floor','sampling':'half','visible':True})
        s.advance_to(400000);saved=s.snapshot();a=s.render().bytes
        s.command({'op':'emitter-style','id':1,'sampling':'cell','surfaceAlpha':.5});s.restore(saved)
        self.assertEqual(s.render().bytes,a)
    def testStyleEditsCannotRespawnOrRetargetParticles(self):
        s=self.scene();self.emitter(s);s.advance_to(700000);particles=s.particles();before=s.info()['clock']
        s.command({'op':'emitter-style','id':1,'sampling':'half','surfaceAlpha':0,'veinContrast':1})
        self.assertEqual(particles,s.particles());self.assertEqual(before,s.info()['clock'])
    def testUnsupportedStylesRejectAtomically(self):
        s=self.scene();self.emitter(s)
        for cmd in ({'op':'emitter-style','id':1,'sampling':'automatic'},{'op':'emitter-style','id':2,'sampling':'cell'},{'op':'floor','sampling':'oops'},{'op':'emitter-style','id':1,'surfaceAlpha':1.1}):
            snap=s.snapshot()
            with self.assertRaises(ValueError):s.command(cmd)
            self.assertEqual(snap,s.snapshot())
    def testLeafOnlySettingsRejectOnNonLeafEmitter(self):
        s=self.scene();s.command({'op':'emitter','id':1,'effect':'weather/silver-squall','count':1})
        for patch in ({'surfaceAlpha':.1},{'veinContrast':.9},{'backTint':.3},{'twoSided':False}):
            saved=s.snapshot()
            with self.assertRaises(ValueError):s.command({'op':'emitter-style','id':1,**patch})
            self.assertEqual(saved,s.snapshot())
        s.command({'op':'emitter-style','id':1,'sampling':'half'})
        with self.assertRaises(ValueError):s.command({'op':'emitter','id':2,'effect':'weather/silver-squall','surfaceAlpha':.1})
    def testLeafOutlineIsNotFilledByItsOwnBlade(self):
        s=self.scene();s.command({'op':'camera','position':[0,6,30],'yaw':0,'pitch':0,'orthographic':True,'span':32})
        self.emitter(s,surfaceAlpha=0,veinContrast=1);s.advance_to(500000)
        original=[g for g,fg,bg,ident in s.render().words()]
        s.command({'op':'emitter-style','id':1,'surfaceAlpha':.2})
        updated=[g for g,fg,bg,ident in s.render().words()]
        dots=[i for i,g in enumerate(original)if 0x2800<g<=0x28ff]
        self.assertGreater(len(dots),40)
        self.assertTrue(all(updated[i]==original[i]for i in dots))
    def testLeafVeinsChangeNativeOutput(self):
        s=self.scene();self.emitter(s,surfaceAlpha=.12,veinContrast=0);s.advance_to(500000)
        a=s.render().bytes;s.command({'op':'emitter-style','id':1,'veinContrast':1});self.assertNotEqual(a,s.render().bytes)
    def testBlockAndBrailleWidgetsCoexistForWholeReveal(self):
        s=self.scene()
        for i,mode in ((1,'braille'),(2,'cell')):
            s.command({'op':'widget','id':i,'kind':'pie','x':i*35,'y':8,'width':30,'height':16,'data':[1],'sampling':mode,'revealMs':1000,'alpha':0})
        for tick in range(1,61):
            s.advance_to(tick*1000000//60);w=s.render().words()
            for i,mode in ((1,'braille'),(2,'cell')):
                glyphs=[g for g,fg,bg,ident in w if ident==(0x30000000|i) and g!=32]
                
                if tick==60:self.assertTrue(glyphs)
                self.assertTrue(all((0x2800<g<=0x28ff)if mode=='braille'else g==0x2588 for g in glyphs))
    def testPerspectiveDepthIsReciprocalAfterScreenClipping(self):
        # At screen midpoint the endpoint depths 5 and 20 interpolate to 8, not 12.5.
        self.assertAlmostEqual(self.lib.lineDepthProbe()/1024,8,delta=.25)
    def testTextOverFullBlockInheritsActualBlockColor(self):
        self.assertEqual(self.lib.opaqueBackdropProbe(),0xabcdef)
if __name__=='__main__':unittest.main()
