import unittest,sys,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'examples'))
class ProductCopy(unittest.TestCase):
 def test_authored_labels_clean_without_changing_components_or_events(self):
  from product_copy import public_recipe
  case={'id':'original-pearl','name':'Original Pearl Curves / eight-dot atelier','subtitle':'Full geometry. No block substitutions.','commands':[{'op':'widget','id':7,'kind':'donut','text':'Original instruments','width':20,'sampling':'braille'},{'op':'trigger','id':8,'event':'Original event','payload':{'text':'Recovered draft v0.5'}}],'provenance':{'source':'original-fixture'}}
  before=copy.deepcopy(case);out=public_recipe(case)
  self.assertEqual(case,before);self.assertEqual(out['id'],before['id']);self.assertEqual(out['commands'][1],before['commands'][1]);self.assertEqual(out['provenance'],before['provenance']);self.assertEqual(out['commands'][0]['sampling'],'braille');self.assertEqual(out['commands'][0]['width'],20)
  self.assertNotIn('Original',out['name']);self.assertNotIn('eight-dot atelier',out['name']);self.assertNotIn('No block',out['subtitle']);self.assertEqual(out['commands'][0]['text'],'Instruments')
 def test_nested_and_timed_display_copy_is_clean_without_changing_payloads(self):
  from product_copy import public_recipe
  case={'commands':[{'op':'batch','commands':[{'op':'window','id':3,'title':'Original Observatory palette'}]},{'op':'emit-intent','path':'/event','value':{'text':'Original data'}}],'actions':[{'timeUs':3,'command':{'op':'text','id':1,'text':'Incoming text / original fade'}}]}
  out=public_recipe(case)
  self.assertEqual(out['commands'][0]['commands'][0]['title'],'Observatory palette')
  self.assertEqual(out['actions'][0]['command']['text'],'Incoming text / fade')
  self.assertEqual(out['commands'][1],case['commands'][1]);self.assertEqual(out['actions'][0]['timeUs'],3)
 def test_all_visible_gallery_copy_is_plain(self):
  from gallery_cases import build_cases
  import re
  banned=re.compile(r'\b(original|recovered|first.version|restored)\b|no block substitutions|full geometry|no foreign controller|shared contracts|all data is synthetic',re.I)
  failures=[(case['id'],key) for case in build_cases() for key in ['name','subtitle'] if banned.search(case.get(key,''))]
  self.assertEqual(len(failures),0,str(failures[:10]))
 def test_shipped_example_prose_has_no_recovery_or_version_narration(self):
  # RC2 copy-only extension: inspect public literal prose, never identifiers,
  # provenance records, imported documents, history state or event payload data.
  import ast,io,re,tokenize
  banned=re.compile(r"\b(?:original|recovered|restored|first[ -](?:version|prompt)|RC[1-9]\d*|v0\.\d+)\b|never canned frames|not byte-identical historical full screens",re.I)
  visible={'name','subtitle','title','label','detail','description','text'};failures=[]
  def literals(node):
   if isinstance(node,ast.Constant) and isinstance(node.value,str):yield node.value
   elif isinstance(node,ast.JoinedStr):
    for value in node.values:
     if isinstance(value,ast.Constant) and isinstance(value.value,str):yield value.value
   elif isinstance(node,ast.BinOp):yield from literals(node.left);yield from literals(node.right)
  def check(path,node,values):
   for value in values:
    if banned.search(value):failures.append((path.name,getattr(node,'lineno',0),value[:110]))
  def visit(path,node):
   if isinstance(node,ast.Dict):
    for key,value in zip(node.keys,node.values):
     name=key.value if isinstance(key,ast.Constant) else None
     if name in {'provenance','expectedSourceModal','payload'}:continue
     if name in visible:check(path,value,literals(value))
     visit(path,value)
    return
   if isinstance(node,(ast.Module,ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
    text=ast.get_docstring(node)
    if text:check(path,node,[text])
   if isinstance(node,(ast.Assign,ast.AugAssign)):
    targets=node.targets if isinstance(node,ast.Assign) else [node.target]
    if any(isinstance(t,ast.Subscript) and isinstance(t.slice,ast.Constant) and t.slice.value in visible for t in targets):check(path,node,literals(node.value))
   if isinstance(node,ast.Call):
    if isinstance(node.func,ast.Name) and node.func.id=='atelier_text_command' and node.args:check(path,node,literals(node.args[0]))
    if isinstance(node.func,ast.Name) and node.func.id=='dict' or isinstance(node.func,ast.Attribute) and node.func.attr=='update':
     for keyword in node.keywords:
      if keyword.arg in visible:check(path,keyword.value,literals(keyword.value))
   for child in ast.iter_child_nodes(node):visit(path,child)
  for path in sorted((Path(__file__).resolve().parents[1]/'examples').glob('*.py')):
   source=path.read_text();visit(path,ast.parse(source))
   for token in tokenize.generate_tokens(io.StringIO(source).readline):
    if token.type==tokenize.COMMENT and banned.search(token.string):failures.append((path.name,token.start[0],token.string))
  self.assertEqual(failures,[],str(failures[:20]))
if __name__=='__main__':unittest.main()
