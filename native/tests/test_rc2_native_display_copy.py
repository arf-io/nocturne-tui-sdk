"""Current presentation copy, measured from actual native frames and diagnostics."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import re,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'bindings/python'),str(ROOT/'examples')]
from nocturne_native import NativeScene
from rc2_window_studies import build_rc2_window_studies
from native.tests.test_original_atelier_windows import commands
class NativeDisplayCopy(unittest.TestCase):
 def test_real_application_headers_retain_titles_without_version_narration(self):
  cases=[(x['commands'],x['originalScene'].upper())for x in build_rc2_window_studies() if x['demo']]+[(commands(),'SPATIAL ATELIER')]
  forbidden=re.compile(r'v0\.\d|\b0\.5\b|VOL V|recovery dock|INPUT IS IMMEDIATE|beyond the rectangle|spatial glass',re.I)
  for cs,title in cases:
   with self.subTest(scene=title),NativeScene(2030)as s:
    for c in cs:s.command(c)
    frame=s.render();w=frame.width;words=list(frame.words());rows=[''.join(chr(c[0])for c in words[y*w:(y+1)*w])for y in (1,3,frame.height-2)]
    text='\n'.join(rows);self.assertIsNone(forbidden.search(text),text)
    self.assertIn('SPATIAL ATELIER' if title=='SPATIAL ATELIER' else 'KINETIC',text)
 def test_reference_bridge_changes_only_named_human_literals(self):
  import gzip,hashlib
  from native.tests.historical_reference import load_rc2_workbench
  from native.tests.presentation_copy_reference import current_presentation,REPLACEMENTS
  sources={'kinetic':load_rc2_workbench(),'atelier':gzip.decompress((ROOT/'tests/fixtures/original-atelier-spatial-v0.5.html.gz').read_bytes()).decode()}
  self.assertEqual(hashlib.sha256(sources['atelier'].encode()).hexdigest(),'01500ccd3106f40a7f0b3e21fe4a580f1e0666980e998930feaf94bff730aced')
  for kind,source in sources.items():
   expected=source
   for old,new in REPLACEMENTS[kind]:
    self.assertEqual(source.count(old),1,(kind,old));expected=expected.replace(old,new,1)
   self.assertEqual(current_presentation(source,kind),expected)
   with self.assertRaises(AssertionError):current_presentation(source.replace(REPLACEMENTS[kind][0][0],'changed',1),kind)
 def test_historical_frame_bridge_rejects_art_or_copy_changes(self):
  import gzip
  from native.tests.presentation_copy_reference import assert_current_chrome
  with NativeScene(2030)as scene:
   scene.restore(gzip.decompress((ROOT/'tests/fixtures/window-application-schema69.bin.gz').read_bytes()))
   frame=scene.render();historical=gzip.decompress((ROOT/'tests/fixtures/window-application-schema69-frame.bin.gz').read_bytes())
   assert_current_chrome(self,frame.bytes,historical,frame.width,frame.height,'kinetic')
   # Every non-copy word remains exact; a geometry cell cannot be hidden by the bridge.
   bad=bytearray(frame.bytes);bad[(10*frame.width+20)*16]^=1
   with self.assertRaises(AssertionError):assert_current_chrome(self,bad,historical,frame.width,frame.height,'kinetic')
   bad=bytearray(frame.bytes);bad[(1*frame.width+2)*16]^=1
   with self.assertRaises(AssertionError):assert_current_chrome(self,bad,historical,frame.width,frame.height,'kinetic')
 def test_native_diagnostics_describe_operation_without_provenance_narration(self):
  excluded={'first_prompt.c','ui.c','prompt_appearance.c','state.c','commands.c'}
  failures=[]
  for p in sorted((ROOT/'src').glob('*.c')):
   if p.name in excluded:continue
   for literal in re.findall(r'(?:return\s+)?(?:reject|fail|bad)\([^;]*?"([^"\n]*)"',p.read_text()):
    if re.search(r'\b(original|recovered|first.version)\b',literal,re.I):failures.append((p.name,literal))
  self.assertEqual(failures,[])
if __name__=='__main__':unittest.main()
