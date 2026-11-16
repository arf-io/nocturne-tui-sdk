import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'examples'));sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
SPECIMENS=ROOT/'examples/tdf_specimens.json'
class TdfGalleryStudies(unittest.TestCase):
 def test_a_tree_without_the_specimen_data_has_no_studies(self):
  import tdf_gallery_studies
  from unittest import mock
  with mock.patch.object(tdf_gallery_studies,'SPECIMENS',ROOT/'examples/no-such-specimens.json'):
   self.assertEqual(tdf_gallery_studies.build_tdf_gallery_studies(),[])
 @unittest.skipUnless(SPECIMENS.is_file(),'native/examples/tdf_specimens.json is private-only and is not in the public tree')
 def test_real_formatter_cells_are_visible_in_normal_gallery(self):
  from tdf_gallery_studies import build_tdf_gallery_studies
  cases=build_tdf_gallery_studies();self.assertEqual(len(cases),6)
  for case in cases:
   self.assertTrue(case['demo']);self.assertEqual(case['provenance']['fontSha256'],'a947aadf36337988a5961846dd0cfe51454d478ed7e2862e12e44f5c80c251af')
   with NativeScene(2030)as s:
    for c in case['commands']:s.command(c)
    art=next(c for c in case['commands']if c['op']=='cell-art');f=s.render();words=f.words()
    for i,expected in enumerate(art['cells']):
     if expected[0]:self.assertEqual(words[(art['y']+i//art['width'])*f.width+art['x']+i%art['width']][:3],tuple(expected))
if __name__=='__main__':unittest.main()
