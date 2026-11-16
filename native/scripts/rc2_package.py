"""Compact current SDK packaging; archival source and records remain in Git."""
from pathlib import Path,PurePosixPath
import hashlib,json,os,zipfile

ROOT_NAMES={'README.md','RELEASE.json','LICENSE','LICENSE.md','LICENSE.txt','build-native.sh','run-native.sh','native-env.sh','qualify-native.sh'}
ROOTS=('src/','include/','native/src/','native/include/','native/freestanding/','native/unicode/','native/bindings/','native/hosts/','native/examples/','native/tests/','native/scripts/','docs/current/','tools/ci/','tools/qualification/')
NATIVE_NAMES={'native/build.sh','native/run.sh','native/recipes.json','native/palettes.json','native/catalogue.json','native/port-ledger.json','native/web/template.html','native/web/workshop_fields.json','native/web/workshop_help.json',
 'integrations/tdfiglet_bridge.py',  # imported by native/examples/tdfiglet_scene.py for the Gallery build
 'native/contract/NULLIFICATION.json','native/contract/NULLIFICATION.schema.json',
 'native/contract/GALLERY-ADMISSION.json'}  # read by build_gallery.py (provenance admission and nullification) and build_reference_docs.py
SKIP={'.git','target','node_modules','__pycache__','.pytest_cache'}
FONTS={'.ttf','.otf','.woff','.woff2','.tdf','.flf','.pfb','.pfa','.fon','.fnt'}
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def currentPayload(root,tracked):
 root=Path(root).resolve();selected={}
 for name in tracked:
  rel=PurePosixPath(name)
  if rel.is_absolute() or '..'in rel.parts or '\\'in name:raise ValueError('Unsafe tracked path')
  if any(x in SKIP for x in rel.parts) or rel.suffix.lower()in FONTS:continue
  if name not in ROOT_NAMES|NATIVE_NAMES and not name.startswith(ROOTS):continue
  path=root/name
  if path.is_symlink():raise ValueError('Unexpected SDK symlink: '+name)
  if not path.is_file():raise FileNotFoundError(name)
  selected[name]=path
 return selected
def writeArchive(destination,files,metadata):
 destination=Path(destination);manifest={**metadata,'files':{name:{'bytes':path.stat().st_size,'sha256':sha(path)}for name,path in sorted(files.items())}}
 temporary=destination.with_suffix(destination.suffix+'.part')
 with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
  for name,path in sorted(files.items()):
   info=zipfile.ZipInfo('nocturne-sdk/'+name,(2026,10,16,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=(0o100755 if os.access(path,os.X_OK)else 0o100644)<<16;z.writestr(info,path.read_bytes())
  info=zipfile.ZipInfo('nocturne-sdk/MANIFEST.json',(2026,10,16,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,json.dumps(manifest,indent=2)+'\n')
 from release_archive import verifyArchive
 verifyArchive(temporary);os.replace(temporary,destination);return manifest

def inside(root,name):
 rel=PurePosixPath(name)
 if not name or rel.is_absolute()or '..'in rel.parts or rel.as_posix()!=name or '\\'in name:raise ValueError('Unsafe documentation path')
 path=Path(root)/name
 if path.is_symlink()or not path.resolve().is_relative_to(Path(root).resolve()):raise ValueError('Documentation link escapes its root')
 return path

def referencePayload(root,output):
 root=Path(root);source=root/'docs/current';output=Path(output)
 record=json.loads((output/'BUILD.json').read_text())
 if sha(source/'manifest.json')!=record['manifestSha256']:raise ValueError('Documentation source manifest changed')
 for name,digest in {**record['sources'],**record.get('sourceAssets',{})}.items():
  if sha(inside(source,name))!=digest:raise ValueError('Documentation source changed: '+name)
 actual={p.relative_to(output).as_posix()for p in output.rglob('*')if p.is_file()}
 if actual!=set(record['outputs'])|{'BUILD.json'}:raise ValueError('Documentation output membership changed')
 selected={'docs/rendered/BUILD.json':output/'BUILD.json'}
 for name,item in record['outputs'].items():
  path=inside(output,name)
  if path.stat().st_size!=item['bytes']or sha(path)!=item['sha256']:raise ValueError('Documentation output changed: '+name)
  selected['docs/rendered/'+name]=path
 return selected

def validateRC2Receipt(receipt,currentFingerprint):
 from release_identity import validateCompletedBuild
 from rc2_release_plan import REQUIRED_CASE_IDS,NATIVE_STEPS
 validateCompletedBuild(receipt,currentFingerprint)
 scope=receipt.get('qualificationScope',{});ids=receipt.get('expectedCaseIds',[])
 required=set(REQUIRED_CASE_IDS)|{step for step,_ in NATIVE_STEPS}|{'rc2-project-codegen','rc2-browser','rc2-reference-docs','rc2-reference-validate','rc2-plan-regressions'}
 if receipt.get('qualificationProfile')!='rc2'or receipt.get('runtimePlanQualified')is not True or scope.get('profile')!='rc2'or scope.get('exhaustive')is not False or scope.get('includedCaseIds')!=ids or not required.issubset(ids)or len(ids)!=len(set(ids)):raise ValueError('Complete declared RC2 qualification profile required')
 if [x.get('id')for x in receipt.get('commands',[])]!=ids or any(x.get('status')!='PASS'or type(x.get('exitCode'))is not int or x['exitCode']!=0 for x in receipt['commands']):raise ValueError('RC2 case execution is incomplete or failed')
 coverage=receipt.get('coverage',{})
 if coverage.get('sourceFingerprint')!=currentFingerprint or coverage.get('passed')is not True or coverage.get('requiredPercent',0)<70 or coverage.get('nativeLinePercent',0)<coverage['requiredPercent']:raise ValueError('Source-matching measured coverage required')
 shipping=receipt.get('shippingModeVerification',{})
 if shipping.get('sourceFingerprint')!=currentFingerprint or any(shipping.get(k)is not True for k in ['passed','fourRuntimePassed','measuredReplayEqual']):raise ValueError('Source-matching uninstrumented shipping replay required')

def validateGalleryArtifact(path,record,wasm):
 import base64,re
 path=Path(path);wasm=Path(wasm)
 if not isinstance(record,dict)or path.stat().st_size!=record.get('bytes')or sha(path)!=record.get('sha256'):raise ValueError('Gallery differs from qualified artifact')
 text=path.read_text();digest=sha(wasm)
 match=re.search(r"const workshopWasm=Uint8Array.from\(atob\('([A-Za-z0-9+/=]+)'\)",text)
 if not match or hashlib.sha256(base64.b64decode(match[1],validate=True)).hexdigest()!=digest or ('data-wasm-sha256="'+digest+'"')not in text:raise ValueError('Gallery embedded WASM differs from SDK')
 return record

def packageRC2(root,out,release,receipt,contractPath,documentationOutput):
 import shutil,subprocess
 from qualify import fingerprint
 from sdk_contract import validateSDKContractArtifacts
 from delivery_integrity import closeDelivery,verifyDelivery
 root=Path(root);out=Path(out);validateRC2Receipt(receipt,fingerprint()['sha256'])
 contract=json.loads(Path(contractPath).read_text());validateSDKContractArtifacts(contract,root)
 tracked=subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')
 files=currentPayload(root,[x for x in tracked if x]);files.update(referencePayload(root,documentationOutput))
 for entry in contract['artifacts'].values():files[entry['path']]=root/entry['path']
 gallery=root/'native/Nocturne-RC4-Source-Build.html'
 if not gallery.is_file():raise FileNotFoundError(gallery)
 validateGalleryArtifact(gallery,receipt.get('gallery'),root/contract['artifacts']['wasm']['path'])
 files['Nocturne-Gallery.html']=gallery
 files['SDK-CONTRACT.json']=Path(contractPath)
 files['VERIFICATION.json']=root/'native/evidence/BUILD-VERIFICATION.json'
 # Exact differential-test inputs are fixtures, not an evidence-directory dump.
 from original_c_oracles import originalOracleInputs
 for path in originalOracleInputs(root/'native'):
  if path.is_file():files[path.relative_to(root).as_posix()]=path
 metadata={'build':release['build'],'sourceCommit':release['sourceCommit'],'sourceFingerprint':receipt['sourceAfter'],'qualificationProfile':'rc2','exhaustiveQualification':False,'scope':receipt['qualificationScope'],'documentationManifestSha256':sha(root/'docs/current/manifest.json')}
 prefix=release['artifactPrefix'];sdk=out/(prefix+'-SDK.zip');manifest=writeArchive(sdk,files,metadata)
 shutil.copyfile(gallery,out/(prefix+'.html'))
 shutil.copytree(root/'docs/current',out/'docs/current',dirs_exist_ok=True);shutil.copytree(documentationOutput,out/'docs/rendered',dirs_exist_ok=True)
 shutil.copyfile(root/'README.md',out/'README.md');shutil.copyfile(root/'native/evidence/BUILD-VERIFICATION.json',out/'VERIFICATION.json');shutil.copyfile(contractPath,out/'SDK-CONTRACT.json')
 result={**metadata,'sdk':{'name':sdk.name,'bytes':sdk.stat().st_size,'sha256':sha(sdk),'manifestEntries':len(manifest['files'])},'freshExtractionPassed':False}
 (out/'PACKAGE-VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
 closeDelivery(out,partBytes=2*1024**3);verifyDelivery(out)
 print(json.dumps(result,indent=2));return result
