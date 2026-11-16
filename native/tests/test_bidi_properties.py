"""Pinned Unicode direction properties, including unassigned default ranges."""
import ctypes as C
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class BidiProperties(unittest.TestCase):
 def setUp(self):
  self.s=NativeScene();self.addCleanup(self.s.close);self.fn=self.s._lib.nrBidiClass
  self.fn.argtypes=[C.c_uint32];self.fn.restype=C.c_int
 def testStrongWeakNeutralAndExplicitControls(self):
  # Stable class values declared by the native header, not guessed script ranges.
  for scalar,value in [(ord('A'),0),(0x5d0,1),(0x627,2),(ord('1'),3),(0x661,4),(ord('+'),5),(ord('$'),6),(ord(','),7),(0x301,8),(0xad,9),(10,10),(9,11),(32,12),(ord('!'),13),(0x202a,14),(0x202d,15),(0x202b,16),(0x202e,17),(0x202c,18),(0x2066,19),(0x2067,20),(0x2068,21),(0x2069,22)]:self.assertEqual(self.fn(scalar),value,hex(scalar))
 def testUnassignedDefaultsAndInvalidScalars(self):
  for scalar,value in [(0x590,1),(0x600,4),(0x7b2,2),(0x20c1,6),(0x10d3a,2),(0x10ffff,9)]:self.assertEqual(self.fn(scalar),value,hex(scalar))
  for scalar in [0xd800,0xdfff,0x110000,0xffffffff]:self.assertEqual(self.fn(scalar),-1)
 def testParagraphDirectionIgnoresIsolateContents(self):
  fn=self.s._lib.nrBidiParagraphLevel;fn.argtypes=[C.POINTER(C.c_uint32),C.c_uint32,C.c_uint32];fn.restype=C.c_int
  def level(text,fallback=0):
   data=(C.c_uint32*max(1,len(text)))(*map(ord,text));return fn(data,len(text),fallback)
  for text,result in [('123 עברית',1),('123 English',0),('123',0),('\u2067עברית\u2069English',0),('\u2066English\u2069עברית',1),('\u2068\u2067עברית\u2069\u2069English',0),('\u2067עברית',0),('\u2069עברית',1),('123\nעברית',0),('العربية',1)]:self.assertEqual(level(text),result,repr(text))
  self.assertEqual(level('123',1),1);self.assertEqual(level('A',2),-1);self.assertEqual(level('\ud800'),-1);self.assertEqual(level('A'*2049),-1)
 def testBracketPairAndMirrorAreIndependentProperties(self):
  fn=self.s._lib.nrBidiBracket;fn.argtypes=[C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32];fn.restype=C.c_int
  out=(C.c_uint32*2)();self.assertEqual(fn(ord('('),out,2),1);self.assertEqual(list(out),[ord(')'),1])
  self.assertEqual(fn(ord(')'),out,2),1);self.assertEqual(list(out),[ord('('),2])
  mirror=self.s._lib.nrBidiMirror;mirror.argtypes=[C.c_uint32];mirror.restype=C.c_int
  self.assertEqual(mirror(ord('<')),ord('>'));self.assertEqual(mirror(ord('A')),ord('A'))
  before=list(out);self.assertEqual(fn(0xd800,out,2),-1);self.assertEqual(list(out),before)
  self.assertEqual(fn(ord('('),out,1),-1);self.assertEqual(list(out),before)
if __name__=='__main__':unittest.main()
