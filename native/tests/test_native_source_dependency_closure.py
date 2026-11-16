"""Actual compiler + temporary Git fixtures for the source dependency boundary."""
from pathlib import Path
import hashlib, importlib.util, json, os, subprocess, sys, tempfile, unittest, zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import dependencies
import release_archive

class NativeSourceClosure(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(prefix='nocturne-compiler-closure-');self.addCleanup(self.temp.cleanup)
  self.base=Path(self.temp.name).resolve();self.repo=self.base/'repo';self.native=self.repo/'native'
  for name in ('native/src','native/include','include','src','vendor'):(self.repo/name).mkdir(parents=True,exist_ok=True)
  subprocess.run(['git','init','-q',str(self.repo)],check=True,capture_output=True)
  self.cc=os.environ.get('CC','cc')
 def track(self,*names):subprocess.run(['git','add','--',*names],cwd=self.repo,check=True,capture_output=True)
 def core(self,include):
  (self.native/'src/core.c').write_text(include+'\nint result(void){return 1;}\n')
  self.track('native/src/core.c')
 def audit(self):return dependencies.compilerSourceClosure(self.cc,self.native)
 def test_actual_compiler_admits_exact_tracked_original_files_and_hashes(self):
  header=self.repo/'include/original.h';header.write_text('#define ORIGINAL 3\n')
  data=self.repo/'src/original.inc';data.write_text('#define ORIGINAL_DATA 4\n')
  self.track('include/original.h','src/original.inc')
  self.core('#include "../../include/original.h"\n#include "../../src/original.inc"')
  report=self.audit();self.assertEqual(report['errors'],[])
  records={row['path']:row['sha256']for row in report['sources']}
  self.assertEqual(records['../include/original.h'],hashlib.sha256(header.read_bytes()).hexdigest())
  self.assertEqual(records['../src/original.inc'],hashlib.sha256(data.read_bytes()).hexdigest())
  self.assertIn('src/core.c',records)
 def test_actual_compiler_rejects_untracked_original_root_file(self):
  bad=self.repo/'include/untracked.h';bad.write_text('#define VALUE 1\n');self.core('#include "../../include/untracked.h"')
  report=self.audit();self.assertIn('External source dependency: '+str(bad),report['errors'])
  self.assertNotIn('../include/untracked.h',[row['path']for row in report['sources']])
 def test_actual_compiler_rejects_tracked_symlink_escape(self):
  external=self.base/'external.h';external.write_text('#define VALUE 1\n')
  (self.repo/'include/escape.h').symlink_to(external);self.track('include/escape.h');self.core('#include "../../include/escape.h"')
  report=self.audit();self.assertIn('External source dependency: '+str(external),report['errors'])
 def test_actual_compiler_rejects_unrelated_tracked_repository_header(self):
  bad=self.repo/'vendor/other.h';bad.write_text('#define VALUE 1\n');self.track('vendor/other.h');self.core('#include "../../vendor/other.h"')
  report=self.audit();self.assertIn('External source dependency: '+str(bad),report['errors'])
 def test_existing_native_source_and_exact_compiler_sdk_metadata_are_preserved(self):
  header=self.native/'include/native.h';header.write_text('#define NATIVE 1\n');self.track('native/include/native.h');self.core('#include "native.h"')
  report=self.audit();self.assertEqual(report['errors'],[])
  self.assertIn('include/native.h',[row['path']for row in report['sources']])
  if sys.platform=='darwin':
   selected=dependencies.compilerSdkSettings(self.cc)
   for row in report['compilerSdkMetadata']:
    self.assertEqual(row['path'],str(selected));self.assertEqual(row['sha256'],hashlib.sha256(selected.read_bytes()).hexdigest())


class ExtractedSDKSourceClosure(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(prefix='nocturne-extracted-closure-');self.addCleanup(self.temp.cleanup)
  self.base=Path(self.temp.name).resolve();self.cc=os.environ.get('CC','cc')
  source=self.base/'source';source.mkdir()
  subprocess.run(['git','init','-q',str(source)],check=True,capture_output=True)
  self.payload={
   'native/src/core.c':b'#include "../../include/original.h"\n#include "../../src/original.inc"\nint result(void){return ORIGINAL+DATA;}\n',
   'include/original.h':b'#define ORIGINAL 3\n','src/original.inc':b'#define DATA 4\n',
   'vendor/other.h':b'#define OTHER 2\n'}
  for name,data in self.payload.items():
   path=source/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
  subprocess.run(['git','add','.'],cwd=source,check=True,capture_output=True)
  subprocess.run(['git','-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','actual source fixture'],cwd=source,check=True,capture_output=True)
  bundle=self.base/'fixture.bundle'
  subprocess.run(['git','bundle','create',str(bundle),'--all'],cwd=source,check=True,capture_output=True)
  self.payload['git/nocturne-rc4-contracts.bundle']=bundle.read_bytes()
  self.manifest={'files':{name:{'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}for name,data in self.payload.items()}}
  archive=self.base/'fixture.zip'
  with zipfile.ZipFile(archive,'w') as output:
   for name,data in self.payload.items():output.writestr('nocturne-sdk/'+name,data)
   output.writestr('nocturne-sdk/MANIFEST.json',json.dumps(self.manifest))
  self.repo=release_archive.extractVerified(archive,self.base/'extracted');self.native=self.repo/'native'
 def audit(self):return dependencies.compilerSourceClosure(self.cc,self.native)
 def writeManifest(self): (self.repo/'MANIFEST.json').write_text(json.dumps(self.manifest))
 def test_real_verified_zip_extraction_has_bundle_without_index_and_accepts_exact_sources(self):
  self.assertFalse((self.repo/'.git').exists());self.assertTrue((self.repo/'git/nocturne-rc4-contracts.bundle').is_file())
  report=self.audit();self.assertEqual(report['errors'],[])
  records={row['path']:row['sha256']for row in report['sources']}
  for name in ('src/original.inc','include/original.h'):self.assertEqual(records['../'+name],self.manifest['files'][name]['sha256'])
 def test_same_size_tampered_header_rejected(self):
  path=self.repo/'include/original.h';path.write_bytes(path.read_bytes().replace(b'3',b'9'))
  with self.assertRaisesRegex(ValueError,'Manifest source integrity mismatch'):self.audit()
 def test_changed_size_source_rejected(self):
  path=self.repo/'src/original.inc';path.write_bytes(path.read_bytes()+b'\n')
  with self.assertRaisesRegex(ValueError,'Manifest source integrity mismatch'):self.audit()
 def test_missing_source_file_rejected(self):
  (self.repo/'src/original.inc').unlink()
  with self.assertRaisesRegex(ValueError,'Manifest source missing or unsafe'):self.audit()
 def test_missing_manifest_rejected(self):
  (self.repo/'MANIFEST.json').unlink()
  with self.assertRaisesRegex(ValueError,'Missing or unsafe source dependency manifest'):self.audit()
 def test_unlisted_root_source_rejected_by_actual_compiler(self):
  del self.manifest['files']['src/original.inc'];self.writeManifest()
  report=self.audit();self.assertIn('External source dependency: '+str(self.repo/'src/original.inc'),report['errors'])
 def test_manifest_does_not_admit_unrelated_directory(self):
  with (self.native/'src/core.c').open('a') as out:out.write('#include "../../vendor/other.h"\n')
  report=self.audit();self.assertIn('External source dependency: '+str(self.repo/'vendor/other.h'),report['errors'])
 def test_source_symlink_to_identical_external_bytes_rejected(self):
  path=self.repo/'include/original.h';external=self.base/'external.h';external.write_bytes(path.read_bytes());path.unlink();path.symlink_to(external)
  with self.assertRaisesRegex(ValueError,'Manifest source missing or unsafe'):self.audit()
 def test_source_directory_symlink_escape_rejected(self):
  path=self.repo/'src';external=self.base/'external-src';path.rename(external);path.symlink_to(external,target_is_directory=True)
  with self.assertRaisesRegex(ValueError,'Manifest source missing or unsafe'):self.audit()
 def test_manifest_symlink_rejected(self):
  path=self.repo/'MANIFEST.json';external=self.base/'manifest.json';path.rename(external);path.symlink_to(external)
  with self.assertRaisesRegex(ValueError,'Missing or unsafe source dependency manifest'):self.audit()
 def test_duplicate_manifest_key_rejected(self):
  (self.repo/'MANIFEST.json').write_text('{"files":{},"files":'+json.dumps(self.manifest['files'])+'}')
  with self.assertRaisesRegex(ValueError,'Duplicate manifest key'):self.audit()
 def test_noncanonical_manifest_path_rejected(self):
  self.manifest['files']['src/../include/original.h']=self.manifest['files']['include/original.h'];self.writeManifest()
  with self.assertRaisesRegex(ValueError,'Non-canonical archive path'):self.audit()
 def test_invalid_manifest_source_size_rejected(self):
  self.manifest['files']['src/original.inc']['bytes']=True;self.writeManifest()
  with self.assertRaisesRegex(ValueError,'Invalid payload size'):self.audit()
 def test_ancestor_git_index_does_not_replace_extracted_manifest(self):
  subprocess.run(['git','init','-q',str(self.base/'extracted')],check=True,capture_output=True)
  report=self.audit();self.assertEqual(report['errors'],[])
 def test_manifest_cannot_override_own_index_membership(self):
  subprocess.run(['git','init','-q',str(self.repo)],check=True,capture_output=True)
  subprocess.run(['git','add','native/src/core.c','src/original.inc'],cwd=self.repo,check=True,capture_output=True)
  report=self.audit();self.assertIn('External source dependency: '+str(self.repo/'include/original.h'),report['errors'])
 def test_broken_own_git_marker_does_not_fall_back(self):
  (self.repo/'.git').write_text('gitdir: missing-git-directory\n')
  with self.assertRaisesRegex(ValueError,'Own Git source index unavailable'):self.audit()

if __name__=='__main__':unittest.main()
