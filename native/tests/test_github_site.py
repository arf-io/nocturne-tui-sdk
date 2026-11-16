"""Real static-site/ZIP fixtures, using the actual reference renderer."""
import hashlib,importlib.util,json,subprocess,sys,tempfile,unittest,zipfile
from pathlib import Path
SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
def load(name):
 spec=importlib.util.spec_from_file_location(name,SCRIPTS/(name+'.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
site=load('build_github_site');docs=load('build_reference_docs')
class GithubSite(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name);self.source=self.base/'current';self.source.mkdir();self.rendered=self.base/'rendered';self.output=self.base/'bundle';self.gallery=self.base/'gallery.html'
  self.gallery.write_text('<!doctype html><html><title>Nocturne</title><a href="docs/rendered/README.html?view=1#guide">Reference</a><details id="workshop-panel"><summary>Workshop</summary></details><canvas id="canvas"></canvas></html>')
  (self.source/'README.md').write_text('# Guide\n\n[Code](example.py) · [Other](Other.md?view=1#other)\n')
  (self.source/'Other.md').write_text('# Other\n\nText.\n')
  (self.source/'example.py').write_text('print(42)\n')
  (self.source/'manifest.json').write_text(json.dumps({'schema':'nocturne.reference.v1','title':'Nocturne','pages':['README.md','Other.md']}))
  docs.build(self.source,self.rendered)
 def build(self):return site.build(self.output,self.rendered,self.source,self.gallery)
 def test_actual_cli_archive_links_and_exact_gallery(self):
  (self.base/'.env').write_text('PRIVATE FIXTURE');(self.base/'old.log').write_text('old');(self.base/'history.bundle').write_bytes(b'historical fixture')
  result=subprocess.run([sys.executable,str(SCRIPTS/'build_github_site.py'),'--output',str(self.output),'--documentation-output',str(self.rendered),'--documentation-source',str(self.source),'--gallery',str(self.gallery)],text=True,capture_output=True)
  self.assertEqual(result.returncode,0,result.stderr);report=site.verify(self.output);self.assertGreater(report['files'],5)
  self.assertEqual((self.output/'site/gallery.html').read_bytes(),self.gallery.read_bytes());self.assertIn('gallery.html#workshop-panel',(self.output/'site/index.html').read_text());self.assertTrue((self.output/'site/docs/rendered/Nocturne-SDK-Reference.pdf').read_bytes().startswith(b'%PDF'))
  names=zipfile.ZipFile(self.output/'site.zip').namelist();self.assertEqual(len(names),len(set(names)));self.assertNotIn('.env',names);self.assertFalse(any(n.endswith(('BUILD.json','.log','.bundle')) for n in names))
  self.assertEqual((self.output/'MANIFEST.json').read_bytes(),(self.output/'site/MANIFEST.json').read_bytes())
 def test_member_missing_changed_extra_and_symlink_rejected(self):
  self.build();p=self.output/'site/gallery.html';original=p.read_bytes()
  p.write_bytes(original+b'changed')
  with self.assertRaisesRegex(ValueError,'Asset hash'):site.verify(self.output)
  p.write_bytes(original);p.unlink()
  with self.assertRaisesRegex(ValueError,'inventory'):site.verify(self.output)
  p.write_bytes(original);extra=self.output/'site/extra.txt';extra.write_text('extra')
  with self.assertRaisesRegex(ValueError,'inventory'):site.verify(self.output)
  extra.unlink();p.unlink();p.symlink_to(self.gallery)
  with self.assertRaisesRegex(ValueError,'Symlink'):site.verify(self.output)
 def test_archive_duplicate_extra_and_tamper_rejected(self):
  self.build();z=self.output/'site.zip';original=z.read_bytes()
  for name,data,error in [('gallery.html',b'changed','Duplicate ZIP'),('extra.txt',b'extra','ZIP inventory')]:
   with self.subTest(name=name):
    with zipfile.ZipFile(z,'a') as archive:archive.writestr(name,data)
    with self.assertRaisesRegex(ValueError,error):site.verify(self.output)
    z.write_bytes(original)
  with zipfile.ZipFile(z) as archive:rows=[(info,archive.read(info)) for info in archive.infolist()]
  with zipfile.ZipFile(z,'w') as archive:
   for info,data in rows:archive.writestr(info,b'changed' if info.filename=='gallery.html' else data)
  with self.assertRaisesRegex(ValueError,'ZIP bytes'):site.verify(self.output)
 def test_stale_markdown_and_rendered_asset_rejected(self):
  p=self.source/'README.md';old=p.read_bytes();p.write_bytes(old+b'changed')
  with self.assertRaisesRegex(ValueError,'Documentation source hash'):self.build()
  p.write_bytes(old);p=self.rendered/'README.html';p.write_bytes(p.read_bytes()+b'changed')
  with self.assertRaisesRegex(ValueError,'Documentation output hash'):self.build()
  self.assertFalse(self.output.exists())
 def test_missing_and_escaping_local_links_and_anchor_rejected(self):
  for target in ['missing.html','../outside.html','%2e%2e/outside.html','docs/rendered/README.html#absent']:
   with self.subTest(target=target):
    self.gallery.write_text('<a href="'+target+'">Broken</a><details id="workshop-panel"></details>')
    with self.assertRaisesRegex(ValueError,'link|anchor|escape'):self.build()
    self.assertFalse(self.output.exists())
 def test_non_github_urls_and_unsafe_schemes_rejected(self):
  for text in ['<a href="https://wiki.example.org/">x</a>','<script src="https://example.com/x.js"></script>','<a href="//evil.test/x">x</a>','<a href="https://github.com.evil.test/">x</a>','<a href="javascript:alert(1)">x</a>','<style>body{background:url(https://example.com/x.png)}</style>',"<script>fetch('https://example.com/data')</script>","<script>fetch('//example.com/data')</script>","<script>fetch('HTTPS://example.com/data')</script>"]:
   with self.subTest(text=text):
    self.output=self.base/('bundle-'+hashlib.sha256(text.encode()).hexdigest()[:10])
    self.gallery.write_text(text+'<details id="workshop-panel"></details>')
    with self.assertRaisesRegex(ValueError,'External|scheme'):self.build()
 def test_source_symlink_receipt_path_and_private_asset_rejected(self):
  real=self.source/'example.py';real.unlink();real.symlink_to(self.gallery)
  with self.assertRaisesRegex(ValueError,'Symlink'):self.build()
  real.unlink();real.write_text('print(42)\n');p=self.rendered/'BUILD.json';b=json.loads(p.read_text());b['outputs']['../escape.html']={'bytes':0,'sha256':'0'*64};p.write_text(json.dumps(b))
  with self.assertRaisesRegex(ValueError,'path'):self.build()
  del b['outputs']['../escape.html'];b['sourceAssets']['.env']='0'*64;p.write_text(json.dumps(b))
  with self.assertRaisesRegex(ValueError,'public asset'):self.build()
 def test_refuses_existing_output_and_wrong_release_host(self):
  self.output.mkdir()
  with self.assertRaisesRegex(ValueError,'already exists'):self.build()
  self.output.rmdir()
  with self.assertRaisesRegex(ValueError,'External'):site.build(self.output,self.rendered,self.source,self.gallery,sdk_url='https://example.com/sdk.zip')
 def test_public_receipts_excluded_but_verified(self):
  # An actual reference rebuild records this receipt; it is never public site content.
  receipt=self.source/'images/CAPTURES.json';receipt.parent.mkdir();receipt.write_text(json.dumps({'schema':'nocturne.reference-captures.v1','captures':[],'sources':{str(self.gallery):docs.sha(self.gallery)},'scope':'Static fixture; no runtime captures.'}));docs.build(self.source,self.rendered)
  self.build();a=self.output/'site/docs/current/images/CAPTURES.json';b=self.output/'site/docs/rendered/images/CAPTURES.json';self.assertEqual(a.read_bytes(),b.read_bytes());derived=json.loads(a.read_text());self.assertEqual(derived['schema'],'nocturne.public-reference-captures.v1');self.assertEqual(derived['originalManifestSha256'],docs.sha(receipt));self.assertEqual(derived['sourceArtifacts'],[{'name':'gallery.html','sha256':docs.sha(self.gallery)}]);self.assertNotIn(str(self.base),a.read_text())

if __name__=='__main__':unittest.main()
