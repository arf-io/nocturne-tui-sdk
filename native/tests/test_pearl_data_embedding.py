"""Exercise the real gallery builder and original module closure."""
from pathlib import Path
import sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import build_gallery
class PearlDataEmbedding(unittest.TestCase):
 def test_real_builder_embeds_original_source_closure(self):
  with tempfile.TemporaryDirectory() as directory:
   page=Path(directory)/'actual-gallery.html'
   build_gallery.main(output=page,features=('original-pearl-data',))
   html=page.read_text()
   self.assertTrue('@@PEARL_DATA@@' not in html,'Original host code must be in the actual generated gallery')
   for name in ('StudioDataSource','observatorySample','PearlStageSession'):
    self.assertIn(name,html)
   self.assertIn('pearl-studio-original',html);self.assertIn('pearl-fleet-original',html)
if __name__=='__main__':unittest.main()
