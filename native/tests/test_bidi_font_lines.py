"""Explicit font-selected line boundaries; deferred combined qualification."""
import ctypes as C
import unittest
from test_hull_immersion import NativeScene

class FontLines(unittest.TestCase):
 def setUp(self):
  self.scene=NativeScene();self.addCleanup(self.scene.close)
  self.fn=self.scene._lib.nrBidiClusterLines
  self.fn.argtypes=[C.POINTER(C.c_uint32),C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32,C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32];self.fn.restype=C.c_int
 def rows(self,text,ends,direction=2):
  source=(C.c_uint32*len(text))(*map(ord,text));lines=(C.c_uint32*len(ends))(*ends);out=(C.c_uint32*(max(1,len(text))*7))()
  count=self.fn(source,len(text),lines,len(ends),direction,out,len(text));self.assertGreaterEqual(count,0)
  return [tuple(out[i*7:i*7+7]) for i in range(count)]
 def test_soft_line_reset_preserves_full_paragraph_resolution(self):
  # Full paragraph base is RTL, including the second line's Latin text.
  rows=self.rows('אב ab ',[3,6]);self.assertEqual([r[0] for r in rows],[2,1,0,5,3,4])
  self.assertEqual([r[5] for r in rows],[1,1,1,1,2,2]);self.assertEqual([r[3] for r in rows],[0,0,0,1,1,1])
 def test_owned_binding_and_aliasing_are_pure(self):
  before=self.scene.snapshot();expected=self.rows('אב ab ',[3,6])
  owned=self.scene.bidi_lines('אב ab ',[3,6]);self.scene.bidi_lines('xyz',[1,3])
  self.assertEqual([tuple(r) for r in owned],expected);self.assertEqual(self.scene.snapshot(),before)
  alias=(C.c_uint32*42)(*map(ord,'אב ab '));ends=(C.c_uint32*2)(3,6)
  self.assertEqual(self.fn(alias,6,ends,2,2,alias,6),6)
  self.assertEqual([tuple(alias[i*7:i*7+7]) for i in range(6)],expected)
 def test_clusters_and_hard_breaks(self):
  rows=self.rows('a\u0301b\nc',[2,4,5]);self.assertEqual([(r[0],r[1],r[3]) for r in rows],[(0,2,0),(2,3,1),(3,4,1),(4,5,2)])
  self.assertEqual(self.rows('',[]),[])
 def test_every_required_separator_has_zero_width_and_a_following_row(self):
  for separator in ['\n','\r','\r\n','\x0b','\x0c','\x85','\u2028','\u2029']:
   with self.subTest(separator=repr(separator)):
    source='A'+separator+'B';end=1+len(separator);before=self.scene.snapshot()
    rows=self.rows(source,[end,len(source)],direction=0)
    self.assertEqual([(r[0],r[1],r[3],r[4]) for r in rows],[(0,1,0,1),(1,end,0,0),(end,end+1,1,1)])
    self.assertEqual(self.scene.bidi_caret(source,100,end,direction=0)[:2],[0,1])
    self.assertEqual(self.scene.grapheme_layout(source,100)[-1][3],1)
    values=(C.c_uint32*len(source))(*map(ord,source));ends=(C.c_uint32*1)(len(source));out=(C.c_uint32*(len(source)*7))(*([777]*(len(source)*7)))
    self.assertEqual(self.fn(values,len(source),ends,1,0,out,len(source)),-1);self.assertEqual(list(out),[777]*len(out));self.assertEqual(self.scene.snapshot(),before)
 def test_discovery_preserves_font_and_cell_metric_distinction(self):
  before=self.scene.snapshot();contract=self.scene.info()['contract'];query=contract['queryContracts']['nrBidiClusterLines']
  self.assertIn('explicit-bidi-lines',contract['features']);self.assertTrue(query['fullParagraphResolution']);self.assertTrue(query['wholeGraphemeLines']);self.assertFalse(query['crossHardBreakAllowed'])
  self.assertEqual(query['widthUnit'],'terminalCellAnnotation');self.assertEqual(query['fields'],['start','end','column','line','width','level','mappedFirstScalar']);self.assertEqual(query['rowWords'],7);self.assertEqual(self.scene.snapshot(),before)
 def test_invalid_boundaries_and_short_output_are_atomic(self):
  source=(C.c_uint32*4)(97,0x301,10,98);out=(C.c_uint32*28)(*([777]*28))
  for ends in ([1,3,4],[4],[2,2,4],[2,3],[2,5]):
   lines=(C.c_uint32*len(ends))(*ends);self.assertEqual(self.fn(source,4,lines,len(ends),2,out,4),-1);self.assertEqual(list(out),[777]*28)
  lines=(C.c_uint32*2)(3,4);self.assertEqual(self.fn(source,4,lines,2,2,out,1),-1);self.assertEqual(list(out),[777]*28)
