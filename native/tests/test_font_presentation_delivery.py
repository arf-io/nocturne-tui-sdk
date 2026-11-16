"""External presentation input identity contracts; actual files, no engine mocks."""
import hashlib
from pathlib import Path
import sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from check_font_presentation import fixtures
from qualify import toolExecutables,checkpointPlan

class FontPresentationDelivery(unittest.TestCase):
 def test_external_input_bytes_invalidate_binding_at_same_path(self):
  with tempfile.TemporaryDirectory() as temporary:
   library=Path(temporary)/'engine';font=Path(temporary)/'font'
   library.write_bytes(b'library input');font.write_bytes(b'font input')
   environment={'NOCTURNE_HARFBUZZ_LIBRARY':str(library),'NOCTURNE_SHAPING_FONT':str(font),'PATH':''}
   before=fixtures(environment);binding=toolExecutables({},environment)
   for name in before:self.assertEqual(before[name]['sha256'],binding[name]['sha256'])
   font.write_bytes(b'replaced at same path')
   after=fixtures(environment);changed=toolExecutables({},environment)
   self.assertNotEqual(before['NOCTURNE_SHAPING_FONT']['sha256'],after['NOCTURNE_SHAPING_FONT']['sha256'])
   self.assertNotEqual(binding['NOCTURNE_SHAPING_FONT'],changed['NOCTURNE_SHAPING_FONT'])
   self.assertEqual(binding['NOCTURNE_HARFBUZZ_LIBRARY'],changed['NOCTURNE_HARFBUZZ_LIBRARY'])
 def test_absent_inputs_never_bind_as_available(self):
  with self.assertRaises(ValueError):fixtures({})
  result=toolExecutables({},{'PATH':''})
  for key in ['NOCTURNE_HARFBUZZ_LIBRARY','NOCTURNE_SHAPING_FONT']:self.assertEqual(result[key]['status'],'BLOCKED')
 def test_presentation_checkpoint_retains_consuming_artifacts(self):
  rows=checkpointPlan([('font-presentation',[sys.executable,'scripts/check_font_presentation.py'])],120)
  names={Path(p).name for p in rows[0]['artifacts']}
  self.assertEqual(names,{'RESULTS.json','screen.svg','example-0.stdout','example-0.stderr','example-1.stdout','example-1.stderr'})
