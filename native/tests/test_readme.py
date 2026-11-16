"""Validate current README links and actual screenshot provenance."""
from pathlib import Path
import hashlib,json,re,unittest
ROOT=Path(__file__).resolve().parents[2]
PRIVATE=ROOT/'tools/release/private_strings.json'
HOSTS=('github.com','raw.githubusercontent.com','nocturne.arf.io')
class Readme(unittest.TestCase):
 def test_links_use_github_or_existing_local_sources(self):
  text=(ROOT/'README.md').read_text()
  links=re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',text)
  self.assertTrue(links)
  for target in links:
   with self.subTest(target=target):
    if re.match(r'https?://',target):self.assertRegex(target,r'^https://(?:'+'|'.join(map(re.escape,HOSTS))+r')(?:/|$)')
    elif not target.startswith('#'):self.assertTrue((ROOT/target.split('#')[0]).is_file(),target)
 def test_readme_names_nothing_private(self):
  if not PRIVATE.is_file():self.skipTest('tools/release/private_strings.json is private-only and is not in the public tree; the export scans for it')
  pattern=re.compile(json.loads(PRIVATE.read_text())['pattern'],re.I)
  text=(ROOT/'README.md').read_text()
  self.assertIsNone(pattern.search(text),'README.md matches the private-string pattern')
 def test_python_example_runs_against_the_actual_runtime(self):
  import os,subprocess,sys
  block=re.search(r'```python\n(.*?)\n```',(ROOT/'README.md').read_text(),re.S).group(1)
  env=dict(os.environ);env['PYTHONPATH']=str(ROOT/'native/bindings/python')+os.pathsep+env.get('PYTHONPATH','')
  result=subprocess.run([sys.executable,'-c',block],cwd=ROOT,env=env,capture_output=True,text=True,check=True)
  self.assertEqual(result.stdout.strip(),'80 24 30720')
 def test_screenshots_are_actual_captured_components(self):
  text=(ROOT/'README.md').read_text();images=re.findall(r'!\[[^\]]*\]\(([^)]+)\)',text)
  self.assertGreaterEqual(len(images),3,'README needs feature screenshots')
  captures=json.loads((ROOT/'docs/current/images/CAPTURES.json').read_text())['captures']
  known={r['image']:r['pngSha256']for r in captures if r['nativeWasmEqual']is True}
  for image in images:
   p=ROOT/image;self.assertIn(p.name,known);self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),known[p.name])
if __name__=='__main__':unittest.main()
