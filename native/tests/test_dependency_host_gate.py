"""Qualification policy tests are infrastructure, never framework acceptance."""
import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from qualify_dependency_hosts import offlineEnvironment,outcome,sourceFingerprint,sourceSummary
class PolicyTests(unittest.TestCase):
 def test_offline_environment_is_explicit_and_keeps_external_cache(self):
  env={'PATH':'/tools','GOMODCACHE':'/cache','GOFLAGS':'-race -mod=readonly','GOPROXY':'https://bad','GOSUMDB':'sum.golang.org','GOTOOLCHAIN':'auto'}
  with tempfile.TemporaryDirectory() as td:
   prepared=offlineEnvironment(env,Path(td))
  self.assertEqual(prepared['GOMODCACHE'],'/cache');self.assertEqual(prepared['GOFLAGS'],'-race -mod=readonly')
  self.assertEqual(prepared['GOPROXY'],'off');self.assertEqual(prepared['GOSUMDB'],'off');self.assertEqual(prepared['GOTOOLCHAIN'],'local')
  self.assertEqual(env['GOPROXY'],'https://bad')
 def test_dependency_mutation_flag_rejects(self):
  for flags in ['-mod=mod','-mod=vendor','-modfile=other.mod','-mod readonly -mod=mod']:
   with self.subTest(flags=flags),self.assertRaises(ValueError):offlineEnvironment({'GOFLAGS':flags},Path('/tmp'))
 def test_no_empty_or_running_claim_can_pass(self):
  self.assertEqual(outcome([]),'FAIL');self.assertEqual(outcome([{'status':'RUNNING'}]),'FAIL')
  for status in ['BLOCKED','TIMEOUT','INTERRUPTED','FAIL']:
   self.assertEqual(outcome([{'status':'PASS'},{'status':status}]),status)
  self.assertEqual(outcome([{'status':'PASS'}]),'PASS')
 def test_source_receipt_covers_both_hosts_and_excludes_external_build_products(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)
   files={
    'native/hosts/terminal-kit/host.mjs':'host one',
    'native/hosts/terminal-kit/package-lock.json':'lock one',
    'native/hosts/bubbletea/main.go':'host two',
    'native/hosts/bubbletea/go.sum':'lock two',
    'native/tests/fixtures/dependency-hosts.ndjson':'fixture',
   }
   for name,content in files.items():
    path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content)
   (root/'native/hosts/terminal-kit/node_modules').mkdir()
   (root/'native/hosts/terminal-kit/node_modules/pkg.js').write_text('external dependency')
   (root/'native/target').mkdir();(root/'native/target/generated').write_text('build output')
   before=sourceFingerprint(root)
   self.assertEqual(set(before),set(files))
   summary=sourceSummary(before)
   self.assertEqual(set(summary),{'sha256','files'})
   self.assertEqual(summary['files'],before)
   self.assertEqual(len(summary['sha256']),64)
   (root/'native/hosts/bubbletea/main.go').write_text('changed host two')
   after=sourceFingerprint(root)
   self.assertNotEqual(before['native/hosts/bubbletea/main.go'],after['native/hosts/bubbletea/main.go'])
   self.assertEqual(before['native/hosts/terminal-kit/host.mjs'],after['native/hosts/terminal-kit/host.mjs'])
   self.assertNotEqual(summary['sha256'],sourceSummary(after)['sha256'])
 def test_source_fingerprint_excludes_only_native_dist(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)
   files={
    'native/src/nocturne.c':'native source',
    'native/hosts/terminal-kit/host.mjs':'host source',
    'native/hosts/terminal-kit/package-lock.json':'host lock',
    'native/bindings/rust/Cargo.lock':'SDK lock',
    'native/tests/fixtures/dependency-hosts.ndjson':'fixture',
    'tools/release/archive_size_audit.py':'archive helper',
    'tools/release/publish_github.py':'publish helper',
    'docs/dist/reference.txt':'ordinary documentation',
    'dist/reference.txt':'ordinary root dist source',
    'native/dist-assets/reference.txt':'similar prefix source',
    'native/docs/dist/reference.txt':'nested dist source',
    'docs/native/dist/reference.txt':'nested native dist source',
   }
   excluded={
    'native/dist/generated.wasm':'generated WASM',
    'native/dist/objects/core.o':'generated object',
    'native/target/generated':'build output',
    'native/hosts/terminal-kit/node_modules/pkg.js':'external dependency',
    '.git/HEAD':'git metadata',
    'native/scripts/__pycache__/cached.pyc':'cached bytecode',
   }
   for name,content in {**files,**excluded}.items():
    path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content)
   before=sourceFingerprint(root)
   for name in files:
    with self.subTest(retained=name):self.assertIn(name,before)
   self.assertNotIn('native/dist/generated.wasm',sorted(before))
   self.assertEqual(set(before),set(files))
   summary=sourceSummary(before)
   self.assertEqual(summary['files'],before)
   for name,content in excluded.items():(root/name).write_text('rebuilt '+content)
   after=sourceFingerprint(root)
   self.assertEqual(after,before)
   self.assertEqual(sourceSummary(after),summary)
   for name,content in files.items():
    with self.subTest(changed=name):
     (root/name).write_text('changed '+content)
     after=sourceFingerprint(root)
     self.assertNotEqual(before[name],after[name])
     self.assertNotEqual(sourceSummary(before)['sha256'],sourceSummary(after)['sha256'])
     self.assertEqual({p for p in before.keys()|after.keys() if before.get(p)!=after.get(p)},{name})
     before=after
 def test_fresh_gallery_build_does_not_change_source_fingerprint(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)
   source={
    'native/scripts/build_gallery.py':'gallery generator source',
    'native/reference/host.html':'authored host HTML',
    'docs/Nocturne-RC4.html':'similarly named documentation',
    'docs/native/Nocturne-RC4-Source-Build.html':'nested similarly named documentation',
    'native/docs/Nocturne-RC4-Source-Build.html':'native documentation',
    'Nocturne-RC4-Source-Build.html':'root similarly named source',
    'native/Nocturne-RC4.html':'native similarly named source',
   }
   for name,content in source.items():
    path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content)
   before=sourceFingerprint(root)
   self.assertEqual(set(before),set(source))
   generated=['Nocturne-RC4.html','native/Nocturne-RC4-Source-Build.html']
   for name in generated:(root/name).write_text('new gallery build product')
   self.assertEqual(sourceFingerprint(root),before)
   for name in generated:(root/name).write_text('rebuilt gallery product')
   self.assertEqual(sourceFingerprint(root),before)
   for name,content in source.items():
    with self.subTest(authored=name):
     (root/name).write_text('changed '+content)
     after=sourceFingerprint(root)
     self.assertEqual({p for p in before.keys()|after.keys() if before.get(p)!=after.get(p)},{name})
     before=after
if __name__=='__main__':unittest.main(verbosity=2)
