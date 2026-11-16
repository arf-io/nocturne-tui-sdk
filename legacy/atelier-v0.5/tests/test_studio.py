"""Acceptance tests specified before Studio implementation; not self-updating snapshots."""
import unittest,sys,ctypes as ct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from studio import Studio,Node,Impulse,tween
class StudioAcceptance(unittest.TestCase):
 def testReplayAndOwnedFrames(self):
  s=Studio(width=48,height=16); a=s.render(1234); before=a.tobytes(); s.render(5432)
  self.assertEqual(before,a.tobytes()); self.assertEqual(before,s.render(1234).tobytes())
 def testEveryPatternEveryPixelMode(self):
  for p in range(12):
   for mode in range(4):
    with self.subTest(pattern=p,mode=mode):
     s=Studio(width=31,height=13,pattern=p,pixelMode=mode); self.assertEqual(len(s.render(3500).cells),403)
 def testImmediateDataFrozenMotion(self):
  s=Studio(width=40,height=12)
  self.assertNotEqual(s.render(3000,nodes=[Node('text',2,2,20,1,text='a')]).tobytes(),s.render(3000,nodes=[Node('text',2,2,20,1,text='b')]).tobytes())
 def testStableGlyphs(self):
  s=Studio(width=45,height=18,stars=1,starDensity=1000,novaChance=0,pixelMode=0,pattern=0)
  a=s.render(900); b=s.render(3600)
  both=[(x.glyph,y.glyph) for x,y in zip(a.cells,b.cells) if x.glyph!=32 and y.glyph!=32]
  self.assertGreater(len(both),10); self.assertTrue(all(x==y for x,y in both))
 def testNoQuotesColonsOrMultiDotDefaults(self):
  s=Studio(); bad=set(map(ord,[':',"'",'"','⠉','⠒']))
  self.assertFalse(set(s.config.glyphs[:s.get('starGlyphCount')])&bad)
 def testGrowPreservesWorldSky(self):
  a=Studio(width=20,height=12,pattern=0,novaChance=0).render(3456)
  b=Studio(width=40,height=20,pattern=0,novaChance=0).render(3456)
  for y in range(12):
   for x in range(20): self.assertEqual(a.cell(x,y),b.cell(x,y))
 def testRippleReplay(self):
  s=Studio(width=40,height=20,stars=0); ev=Impulse(20,10,1000,atMs=1000)
  self.assertNotEqual(s.render(1600).tobytes(),s.render(1600,events=[ev]).tobytes())
  self.assertEqual(s.render(1600,events=[ev]).tobytes(),s.render(1600,events=[ev]).tobytes())
 def testFutureAndExpiredRipples(self):
  s=Studio(width=30,height=12,stars=0)
  for time,eventTime in [(1000,2000),(10000,0)]:self.assertEqual(s.render(time).tobytes(),s.render(time,events=[Impulse(12,6,atMs=eventTime)]).tobytes())
 def testNovaIsExplicitAndReplayable(self):
  s=Studio(width=40,height=16,stars=0,novaChance=0)
  ev=Impulse(20,8,kind=1,atMs=0)
  self.assertNotEqual(s.render(700).cell(20,8),s.render(700,events=[ev]).cell(20,8))
 def testInputValidation(self):
  for kw in [dict(width=-1),dict(height=257),dict(periodMs=0),dict(pixelMode=4),dict(unknown=3)]:
   with self.assertRaises((ValueError,KeyError)):Studio(**kw)
  with self.assertRaises(ValueError):Studio().render(-1)
 def testEmptyAndOffscreenPivot(self):
  self.assertEqual(len(Studio(width=0).render(0).cells),0)
  self.assertEqual(len(Studio(width=20,height=10,pivotX=-100000,pivotY=400000,pattern=4).render(10**12).cells),200)
 def testAllWidgetsAndHitAreas(self):
  s=Studio(width=80,height=30)
  for kind in ['text','box','rule','button','item','cursor','progress','bars','pie','donut','scatter','line','digits','edge']:
   with self.subTest(kind=kind):
    n=Node(kind,2,2,30,10,id=2,text='67',data=[200,600,800,900],value=670)
    self.assertEqual(len(s.render(4000,nodes=[n]).cells),2400)
 def testDisabledDoesNotFallThrough(self):
  s=Studio(width=20,height=10)
  nodes=[Node('button',1,1,10,3,id=1),Node('button',1,1,10,3,id=2,state=3)]
  self.assertIsNone(s.hit(nodes,2,2)); self.assertEqual(s.hit(nodes[:1],2,2)[0],1)
 def testTweenBoundaries(self):
  for ease in range(4):
   self.assertEqual(tween(0,1000,0,1000,ease),0);self.assertEqual(tween(0,1000,1000,1000,ease),1000)
   self.assertEqual(tween(0,1000,9999,1000,ease),1000)
  self.assertEqual(tween(0,670,0,0,1),670)
 def testTextCannotEmitControls(self):
  f=Studio(width=20,height=5).render(0,nodes=[Node('text',0,0,20,1,text='a\x1b[31mb')])
  self.assertNotIn(27,[c.glyph for c in f.cells])
 def testMalformedCompositorFrames(self):
  from nocturne import Frame,Cell
  s=Studio(width=2,height=2);valid=s.render(0)
  for malformed in [Frame(2,2,(Cell*1)()),Frame(-1,2,(Cell*1)()),Frame(2,2,[])]:
   with self.assertRaises((ValueError,TypeError)):s.composite(malformed,valid)
  alias=Frame(valid.width,valid.height,valid.cells)
  with self.assertRaises(ValueError):s.composite(alias,valid)
 def testOpacityIdentity(self):
  s=Studio(width=20,height=8); f=s.render(1500); before=f.tobytes()
  s.composite(f,s.render(8000),fgOpacity=0,bgOpacity=0)
  self.assertEqual(f.tobytes(),before)
if __name__=='__main__':unittest.main()
