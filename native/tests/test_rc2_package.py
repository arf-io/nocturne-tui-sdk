"""RC2 payloads keep current docs and source without copying archival prose/logs."""
import sys,tempfile,unittest,json,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from rc2_package import currentPayload,writeArchive
from release_archive import verifyArchive
class RC2Package(unittest.TestCase):
 def test_selection_keeps_art_and_bindings_but_not_archived_documentation(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   names=['README.md','RELEASE.json','native/src/art.c','native/include/nocturne_native.h','native/bindings/python/nocturne_native.py','native/bindings/rust/Cargo.toml','native/tests/test_contract.py','native/tests/fixtures/art.gz','docs/current/README.md','docs/current/images/leaf.png','native/docs/RECOVERED.md','HANDOFF.md','native/evidence/log.json','native/dist/stale.o','native/bindings/rust/target/cache','native/examples/a.py','native/examples/__pycache__/a.pyc']
   for name in names:
    p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(name.encode())
   selected=currentPayload(root,names)
   for name in names[:10]:self.assertIn(name,selected)
   for name in ['native/docs/RECOVERED.md','HANDOFF.md','native/evidence/log.json','native/dist/stale.o','native/bindings/rust/target/cache']:self.assertNotIn(name,selected)
   self.assertIn('native/examples/a.py',selected);self.assertNotIn(names[-1],selected)
 def test_archive_is_exact_and_detects_tampering(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);source=root/'code.c';source.write_text('int x;')
   archive=root/'sdk.zip';manifest=writeArchive(archive,{'native/src/code.c':source},{'build':'1.0.0-rc.2'})
   self.assertEqual(verifyArchive(archive),manifest)
   with zipfile.ZipFile(archive,'a') as z:z.writestr('nocturne-sdk/extra','unexpected')
   with self.assertRaisesRegex(ValueError,'Unlisted'):verifyArchive(archive)
 def test_release_rejects_missing_failed_or_different_profile_receipts(self):
  from rc2_package import validateRC2Receipt
  from rc2_release_plan import REQUIRED_CASE_IDS,NATIVE_STEPS
  import copy
  ids=list(REQUIRED_CASE_IDS)+[step for step,_ in NATIVE_STEPS]+['rc2-project-codegen','rc2-browser','rc2-reference-docs','rc2-reference-validate','rc2-plan-regressions']
  digest='a'*64;record={'complete':True,'sourceUnchanged':True,'localBuildVerified':True,'fourRuntimeVerified':True,'sourceBefore':digest,'sourceAfter':digest,'qualificationProfile':'rc2','runtimePlanQualified':True,'expectedCaseIds':ids,'qualificationScope':{'profile':'rc2','exhaustive':False,'includedCaseIds':ids},'commands':[{'id':name,'status':'PASS','exitCode':0}for name in ids],'coverage':{'sourceFingerprint':digest,'passed':True,'nativeLinePercent':80,'requiredPercent':70},'shippingModeVerification':{'sourceFingerprint':digest,'passed':True,'fourRuntimePassed':True,'measuredReplayEqual':True}}
  validateRC2Receipt(record,digest)
  for key,value in [('qualificationProfile','exhaustive'),('runtimePlanQualified',False),('coverage',{}),('shippingModeVerification',{})]:
   bad=copy.deepcopy(record);bad[key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):validateRC2Receipt(bad,digest)
  bad=copy.deepcopy(record);bad['commands'][-1]['exitCode']=1
  with self.assertRaises(ValueError):validateRC2Receipt(bad,digest)
 def test_gallery_payload_requires_the_actual_bound_wasm_and_html(self):
  from rc2_package import validateGalleryArtifact
  import base64,hashlib
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);wasm=root/'core.wasm';wasm.write_bytes(b'wasm input fixture');page=root/'gallery.html';digest=hashlib.sha256(wasm.read_bytes()).hexdigest()
   page.write_text('<footer data-wasm-sha256="'+digest+'"></footer><script>const workshopWasm=Uint8Array.from(atob(\''+base64.b64encode(wasm.read_bytes()).decode()+"'),c=>c.charCodeAt(0));</script>")
   record={'sha256':hashlib.sha256(page.read_bytes()).hexdigest(),'bytes':page.stat().st_size}
   validateGalleryArtifact(page,record,wasm)
   wasm.write_bytes(b'changed runtime')
   with self.assertRaisesRegex(ValueError,'WASM'):validateGalleryArtifact(page,record,wasm)
   page.write_text('changed page')
   with self.assertRaisesRegex(ValueError,'Gallery'):validateGalleryArtifact(page,record,wasm)
 def test_documentation_requires_exact_sources_and_outputs(self):
  from rc2_package import referencePayload
  import hashlib
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);source=root/'docs/current';output=root/'rendered';source.mkdir(parents=True);output.mkdir()
   (source/'manifest.json').write_text('{}');(source/'README.md').write_text('# SDK')
   (output/'guide.pdf').write_bytes(b'%PDF-actual-file')
   digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
   record={'manifestSha256':digest(source/'manifest.json'),'sources':{'README.md':digest(source/'README.md')},'outputs':{'guide.pdf':{'bytes':(output/'guide.pdf').stat().st_size,'sha256':digest(output/'guide.pdf')}}}
   (output/'BUILD.json').write_text(json.dumps(record))
   self.assertIn('docs/rendered/guide.pdf',referencePayload(root,output))
   (source/'README.md').write_text('# Changed')
   with self.assertRaisesRegex(ValueError,'source'):referencePayload(root,output)
   (source/'README.md').write_text('# SDK');(output/'guide.pdf').write_bytes(b'corrupt')
   with self.assertRaisesRegex(ValueError,'output'):referencePayload(root,output)
 def test_source_selection_refuses_links_and_missing_tracked_files(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'README.md').symlink_to('/dev/null')
   with self.assertRaises(ValueError):currentPayload(root,['README.md'])
   with self.assertRaises(FileNotFoundError):currentPayload(root,['native/src/gone.c'])
 def test_selection_includes_gallery_typography_bridge_but_not_pty_integrations(self):
  """The Gallery build imports integrations/tdfiglet_bridge.py; an extracted SDK must carry it."""
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   names=['integrations/tdfiglet_bridge.py','integrations/pty/package.json','integrations/pty/pty_broker.py','integrations/afd_bridge.py','native/examples/tdfiglet_scene.py']
   for name in names:
    p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(name.encode())
   selected=currentPayload(root,names)
   self.assertIn('integrations/tdfiglet_bridge.py',selected);self.assertIn('native/examples/tdfiglet_scene.py',selected)
   for name in names[1:4]:self.assertNotIn(name,selected)
if __name__=='__main__':unittest.main()
