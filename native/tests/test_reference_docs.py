import importlib.util,json,tempfile,unittest
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/'scripts/build_reference_docs.py'
spec=importlib.util.spec_from_file_location('reference_docs',SCRIPT)
docs=importlib.util.module_from_spec(spec);spec.loader.exec_module(docs)

class ReferenceDocs(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  (self.root/'guide.md').write_text('# Guide\n\n[Next](next.md#next)\n\n```json\n{"op":"pause","paused":true}\n```\n')
  (self.root/'next.md').write_text('# Next\n\nContent.\n')
  self.manifest={'schema':'nocturne.reference.v1','title':'SDK reference','pages':['guide.md','next.md']}
  (self.root/'manifest.json').write_text(json.dumps(self.manifest))
 def test_command_guidance_uses_known_fields_and_contract_hash(self):
  inventory={'sourceSha256':'a'*64,'operations':['widget'],'fields':[{'op':'widget','field':'value','types':['number | undefined'],'choices':[]}]}
  help={'sourceSha256':'a'*64,'parameters':{'widget.value':{'default':'0','description':'Value within the authored range.'}}}
  text=docs.command_reference(inventory,help)
  self.assertIn('number | undefined',text);self.assertIn('Default: 0.',text);self.assertIn('Value within the authored range.',text)
  empty={'sourceSha256':'a'*64,'parameters':{'widget.value':{'default':None,'defaultLabel':None,'description':'Value within the authored range.'}}}
  self.assertNotIn('Default:',docs.command_reference(inventory,empty))
  with self.assertRaises(ValueError):docs.command_reference(inventory,{**help,'sourceSha256':'b'*64})
  with self.assertRaises(ValueError):docs.command_reference(inventory,{**help,'parameters':{'widget.missing':{}}})
 def test_component_registry_covers_all_widget_kinds(self):
  import re
  repo=Path(__file__).resolve().parents[2]
  kinds=set(re.findall("'([^']+)'",re.search(r"export type WidgetKind = ([^;]+);",(repo/'native/bindings/typescript/contracts.ts').read_text())[1]))
  components=json.loads((repo/'docs/current/components.json').read_text())['components']
  self.assertEqual(kinds,{x['id'][7:] for x in components if x['id'].startswith('widget-')})
  self.assertEqual(len(components),len({x['id'] for x in components}))
  self.assertTrue(all(len(x['states'])>=2 for x in components))
 def test_command_reference_matches_actual_compiler_inventory(self):
  import hashlib
  repo=Path(__file__).resolve().parents[2]
  inventory=json.loads((repo/'docs/current/command-inventory.json').read_text())
  actual=json.loads((repo/'native/web/workshop_fields.json').read_text())
  self.assertEqual(inventory,actual)
  self.assertEqual(inventory['sourceSha256'],hashlib.sha256((repo/'native/bindings/typescript/contracts.ts').read_bytes()).hexdigest())
  text=(repo/'docs/current/Commands.md').read_text()
  help=json.loads((repo/'docs/current/command-help.json').read_text())
  self.assertEqual(help,json.loads((repo/'native/web/workshop_help.json').read_text()))
  self.assertEqual(text,docs.command_reference(inventory,help))
  for op in inventory['operations']:self.assertIn('## '+op+'\n',text)
  for field in inventory['fields']:self.assertIn('**`'+field['field']+'`**',text)
 def test_root_navigation_points_to_current_guides(self):
  import re
  repo=Path(__file__).resolve().parents[2];text=(repo/'README.md').read_text()
  targets=re.findall(r'\[[^\]]+\]\(([^)]+)\)',text)
  self.assertIn('docs/current/README.md',targets)
  self.assertFalse(any(t.startswith('native/docs/') or t.startswith('docs/rc4') for t in targets))
  for name in ['C.md','WASM-TypeScript.md','Python.md','Go.md','Rust.md','Web.md']:
   self.assertIn('docs/current/'+name,targets)
 def test_current_contract_is_packaged_and_navigable(self):
  repo=Path(__file__).resolve().parents[2];root=repo/'docs/current'
  manifest=json.loads((root/'manifest.json').read_text())
  self.assertIn('Contract.md',manifest['pages'])
  self.assertIn('Contract.md',manifest['pdfs']['Nocturne-Guide.pdf'])
  text=(root/'Contract.md').read_text()
  for target in ['Commands.md','C.md','Input-and-Motion.md','Materials-and-Rendering.md','Composition.md']:
   self.assertIn(']('+target+')',text)
  self.assertIn('Contract.md',(root/'README.md').read_text())
  self.assertIn('docs/current/Contract.md',(repo/'README.md').read_text())
 def test_valid_link_and_code(self):
  self.assertEqual([p.name for p in docs.validate(self.root)],['guide.md','next.md'])
 def test_rejects_missing_and_escaping_links(self):
  for target in ['missing.md','../escape.md','next.md#absent']:
   with self.subTest(target=target):
    (self.root/'guide.md').write_text('# Guide\n[Link]('+target+')\n')
    with self.assertRaises(ValueError):docs.validate(self.root)
 def test_rejects_duplicate_pages_and_unclosed_fence(self):
  self.manifest['pages'].append('guide.md');(self.root/'manifest.json').write_text(json.dumps(self.manifest))
  with self.assertRaises(ValueError):docs.validate(self.root)
  self.manifest['pages'].pop();(self.root/'manifest.json').write_text(json.dumps(self.manifest))
  (self.root/'guide.md').write_text('# Guide\n```python\nprint(1)\n')
  with self.assertRaises(ValueError):docs.validate(self.root)
 def test_rejects_invalid_json_example(self):
  (self.root/'guide.md').write_text('# Guide\n```json\n{broken}\n```\n')
  with self.assertRaises(ValueError):docs.validate(self.root)
 def test_rejects_changed_capture(self):
  (self.root/'images').mkdir();(self.root/'images/a.png').write_bytes(b'not a screenshot')
  (self.root/'images/CAPTURES.json').write_text(json.dumps({'captures':[{'image':'a.png','pngSha256':'0'*64}]}))
  with self.assertRaises(ValueError):docs.validate(self.root)
 def test_registry_requires_every_state_and_equal_native_wasm_cells(self):
  import hashlib
  (self.root/'images').mkdir();image=b'PNG test fixture';(self.root/'images/a.png').write_bytes(image)
  (self.root/'components.json').write_text(json.dumps({'components':[{'id':'a','states':[{'id':'default'},{'id':'active'}]}]}))
  row={'component':'a','state':'default','image':'a.png','pngSha256':hashlib.sha256(image).hexdigest(),'nativeWasmEqual':True,'cellSha256':'a'*64,'nativeCellSha256':'a'*64}
  path=self.root/'images/CAPTURES.json';path.write_text(json.dumps({'captures':[row]}))
  with self.assertRaises(ValueError):docs.validate(self.root)
  rows=[row,{**row,'state':'active'}];path.write_text(json.dumps({'captures':rows}));docs.validate(self.root)
  rows[1]['nativeCellSha256']='b'*64;path.write_text(json.dumps({'captures':rows}))
  with self.assertRaises(ValueError):docs.validate(self.root)
 def test_pdf_keeps_state_heading_image_and_caption_together(self):
  from PIL import Image
  from pypdf import PdfReader
  Image.new('RGB',(100,100),(12,30,40)).save(self.root/'figure.png')
  self.manifest['pages']=['guide.md'];(self.root/'manifest.json').write_text(json.dumps(self.manifest))
  for lines in range(28,38):
   with self.subTest(lines=lines):
    (self.root/'guide.md').write_text('# Guide\n\n'+('<br/>'.join(['Reference line']*lines))+'\n\n### Measured figure state\n\n![Measured figure caption](figure.png)\n')
    out=self.root/'output';docs.build(self.root,out);pdf=PdfReader(out/'Nocturne-SDK-Reference.pdf')
    imagePages=[i for i,p in enumerate(pdf.pages) if len(p.images)]
    captionPages=[i for i,p in enumerate(pdf.pages) if 'Measured figure caption' in p.extract_text()]
    self.assertEqual(imagePages,captionPages)
    headingPages=[i for i,p in enumerate(pdf.pages) if 'Measured figure state' in p.extract_text()]
    self.assertEqual(imagePages,headingPages)
 def test_pdf_and_html_derive_same_markdown(self):
  from pypdf import PdfReader
  (self.root/'example.py').write_text('print(42)\n')
  with (self.root/'guide.md').open('a') as f:f.write('\n[Example](example.py)\n')
  out=self.root/'output';record=docs.build(self.root,out)
  self.assertEqual((out/'example.py').read_text(),'print(42)\n')
  self.assertTrue(PdfReader(out/'Nocturne-SDK-Reference.pdf').outline)
  text='\n'.join(p.extract_text() for p in PdfReader(out/'Nocturne-SDK-Reference.pdf').pages)
  self.assertIn('Guide',text);self.assertIn('Content.',text)
  self.assertIn('Content.',(out/'next.html').read_text())
  self.assertIn('href="Nocturne-SDK-Reference.pdf"',(out/'guide.html').read_text())
  self.assertEqual(record['pageSources'],['guide.md','next.md'])
  self.assertEqual(record['sourceAssets']['example.py'],docs.sha(self.root/'example.py'))
  self.assertEqual(record['sourceAssets']['manifest.json'],docs.sha(self.root/'manifest.json'))

if __name__=='__main__':unittest.main()
