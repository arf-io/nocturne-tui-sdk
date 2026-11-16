"""Independent synthetic advance references; deferred combined qualification."""
import sys,unittest
from dataclasses import replace
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'hosts/python'))
from font_shaper import PositionedGlyph,ShapedRun,ShapedSegment
from font_layout import paragraph_source_edges,hit_source_edge,GlyphInkRegion,clip_ink_regions,hit_ink_region
from font_layout import capture_text_run,text_run_capture_current

def segment(source,start,line,level,glyphs):
 run=ShapedRun(source,'rtl' if level&1 else 'ltr','Arab' if level&1 else 'Latn','und','fixture',0,'fixture',1000,(),tuple(glyphs))
 return ShapedSegment(start,start+len(source),line,level,run,tuple(((i+1,7),) for i in range(len(glyphs))))

class SourceEdges(unittest.TestCase):
 def test_captured_geometry_checks_context_epoch_source_and_identity(self):
  class FakeScene:
   source='A';clusters=[[1,0,1,7]]
   def text_run_source(self,kind,id):return self.source
   def text_run_clusters(self,kind,id):return self.clusters
  scene=FakeScene();capture=capture_text_run(scene,0,0,host_epoch=3)
  self.assertTrue(text_run_capture_current(scene,capture,host_epoch=3))
  self.assertFalse(text_run_capture_current(FakeScene(),capture,host_epoch=3))
  self.assertFalse(text_run_capture_current(scene,capture,host_epoch=4))
  scene.source='B';self.assertFalse(text_run_capture_current(scene,capture,host_epoch=3))
  scene.source='A';scene.clusters[0][0]=2;self.assertEqual(capture.clusters,((1,0,1,7),))
  self.assertFalse(text_run_capture_current(scene,capture,host_epoch=3))
 def test_whitespace_and_ligatures_keep_real_span_ends(self):
  # Two advances: a three-scalar ligature and a blank space. No interior guess.
  runs=[segment('ffi ',0,0,0,[PositionedGlyph(1,0,3,600,0,0,0,0),PositionedGlyph(2,3,4,200,0,0,0,0)])]
  edges=paragraph_source_edges(runs,font_size=10,x=5,baseline=20)
  self.assertEqual([(e.offset,e.x) for e in edges],[(0,5),(3,11),(3,11),(4,13)])
  self.assertEqual(hit_source_edge(edges,12.9,20).offset,4)
  self.assertEqual(hit_source_edge(edges,11,20).affinity,'downstream')
  self.assertFalse(any(e.offset in (1,2) for e in edges));self.assertEqual(edges[0].identities,((1,7),))
 def test_rtl_edges_alignment_and_row_proximity(self):
  runs=[segment('אב',10,0,1,[PositionedGlyph(1,1,2,300,0,0,0,0),PositionedGlyph(2,0,1,400,0,0,0,0)]),segment('A',20,1,0,[PositionedGlyph(3,0,1,500,0,0,0,0)])]
  edges=paragraph_source_edges(runs,font_size=10,x=5,baseline=20,line_height=30,alignment='right',content_width=20)
  self.assertEqual([(e.offset,e.x,e.baseline) for e in edges],[(12,18,20),(11,21,20),(11,21,20),(10,25,20),(20,20,50),(21,25,50)])
  self.assertEqual(hit_source_edge(edges,25,48).offset,21)
  self.assertEqual(hit_source_edge(edges,18,20).offset,12)
 def test_empty_and_invalid_geometry(self):
  self.assertEqual(paragraph_source_edges([]),());self.assertIsNone(hit_source_edge([],0,0))
  with self.assertRaises(ValueError):paragraph_source_edges([],line_height=0)
  with self.assertRaises(ValueError):hit_source_edge([],float('nan'),0)
 def test_viewport_clips_geometry_without_changing_source_ownership(self):
  region=GlyphInkRegion(0,3,0,0,10,((1,7),(2,7),(3,7)),-5,-10,25,20)
  clipped=clip_ink_regions([region],(0,0,10,10))
  self.assertEqual(len(clipped),1);self.assertEqual((clipped[0].left,clipped[0].top,clipped[0].right,clipped[0].bottom),(0,0,10,10))
  self.assertEqual((clipped[0].start,clipped[0].end,clipped[0].identities),(region.start,region.end,region.identities))
  self.assertEqual(region.left,-5);self.assertEqual(hit_ink_region(clipped,5,5),clipped[0])
  self.assertIsNone(hit_ink_region([region],15,5,viewport=(0,0,10,10)))
  self.assertIsNone(hit_ink_region([region],10,5,viewport=(0,0,10,10)))
  self.assertEqual(clip_ink_regions([region],(0,0,0,10)),())
  with self.assertRaises(ValueError):clip_ink_regions([region],(10,0,0,10))
 def test_source_edge_pointer_is_gated_by_window_viewport(self):
  runs=[segment('A',0,0,0,[PositionedGlyph(1,0,1,500,0,0,0,0)])]
  edges=paragraph_source_edges(runs,font_size=10,x=0,baseline=10)
  self.assertIsNone(hit_source_edge(edges,11,10,viewport=(0,0,10,20)))
  self.assertEqual(hit_source_edge(edges,4,10,viewport=(0,0,10,20)).offset,1)
 def test_source_edges_copy_mutable_identities_and_reject_malformed_records(self):
  run=segment('A',0,0,0,[PositionedGlyph(1,0,1,500,0,0,0,0)])
  identifiers=[[[1,7]]];mutable=replace(run,identities=identifiers)
  edges=paragraph_source_edges([mutable]);identifiers[0][0][0]=99
  self.assertEqual(edges[0].identities,((1,7),))
  for changed in [dict(x=float('nan')),dict(offset=-1),dict(level=127),dict(affinity='unknown'),dict(identities=((0,7),))]:
   with self.assertRaises(ValueError):hit_source_edge([replace(edges[0],**changed)],0,0)
  with self.assertRaises(ValueError):paragraph_source_edges([replace(run,start=-1,end=0)])
