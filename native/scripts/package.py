#!/usr/bin/env python3
"""Package tested current SDK and full development references. No remote writes.

The local build gate must pass; a blocked Rust/art gate is preserved, never promoted.
Toolchains, caches, environment secrets and font files are excluded.
"""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,sys,zipfile
ROOT=Path(__file__).resolve().parents[2]
SKIP={'.git','.venv','node_modules','__pycache__','target','.pytest_cache','.nocturne-tools','rust-target'}
FONTS={'.ttf','.otf','.woff','.woff2','.tdf','.flf','.pfb','.pfa','.fon','.fnt'}
DIST={'libnocturne_native.so','libnocturne_native.dylib','nocturne_native.wasm'}
def sha(path):
 h=hashlib.sha256()
 with path.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def archive(path,assets,head):
 manifest={r:{'bytes':p.stat().st_size,'sha256':sha(p)}for p,r in assets}
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
  for p,r in assets:
   info=zipfile.ZipInfo('nocturne-sdk/'+r,(2026,9,28,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=(0o100755 if os.access(p,os.X_OK)else 0o100644)<<16
   z.writestr(info,p.read_bytes())
  info=zipfile.ZipInfo('nocturne-sdk/MANIFEST.json',(2026,9,28,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
  z.writestr(info,json.dumps({'scope':'Every payload file except this manifest','build':'0.9.0-rc.4+sdk.2','sourceCommit':head,'files':manifest},indent=2)+'\n')
 with zipfile.ZipFile(path)as z:
  if z.testzip():raise RuntimeError('ZIP CRC failure')
 return {'file':path.name,'payloadFiles':len(assets),'bytes':path.stat().st_size,'sha256':sha(path)}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);a=p.parse_args();out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=True)
 if out.is_relative_to(ROOT):raise SystemExit('Output directory must be outside the source tree')
 receipt=json.loads((ROOT/'native/evidence/BUILD-VERIFICATION.json').read_text())
 if not receipt.get('localBuildVerified'):raise SystemExit('Refusing package: current local build gates have not passed')
 from qualify import fingerprint
 if fingerprint()['sha256']!=receipt['sourceAfter']:raise SystemExit('Source changed after verification')
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 history=ROOT/'git/nocturne-rc4-source.bundle';history.parent.mkdir(exist_ok=True)
 if history.exists():history.unlink()
 subprocess.run(['git','bundle','create',str(history),'--all'],cwd=ROOT,check=True)
 # A bundle is opaque to ZIP filters: fail closed if any reachable Git path is a font.
 objects=subprocess.check_output(['git','rev-list','--objects','--all'],cwd=ROOT,text=True)
 if any(Path(line.split(' ',1)[1]).suffix.lower()in FONTS for line in objects.splitlines()if' 'in line):
  raise SystemExit('History contains font assets; do not redistribute this bundle')
 full=[]
 for current,dirs,files in os.walk(ROOT):
  dirs[:]=[d for d in dirs if d not in SKIP]
  folder=Path(current);rel=folder.relative_to(ROOT)
  if rel.parts[:3]==('native','evidence','capture'):dirs[:]=[];continue
  for name in sorted(files):
   path=folder/name;r=path.relative_to(ROOT)
   if path.is_symlink()or path.suffix.lower()in FONTS or name.endswith('.pyc'):continue
   if name in {'.DS_Store','preview.cells'}or name.startswith('.env')or name in {'credentials','id_rsa','id_ed25519'}:continue
   if len(r.parts)==1 and name in {'MANIFEST.json','SHA256SUMS.txt','SOURCE-CONTENTS.md','CHECKSUMS.sha256'}:continue
   if r.parts[:2]==('native','dist')and name not in DIST:continue
   # Source.1 reference evidence remains available, but its large duplicate runtime
   # logs/captures are not recopied into the new distribution.
   if r.parts[:3]==('native','reference-evidence','pre-sdk.2-final-run'):continue
   full.append((path,r.as_posix()))
 full.sort(key=lambda x:x[1])
 rootFiles={'README.md','LLM-HANDOFF.md','CHANGELOG-RC4-SDK2.md','LICENSE','LICENSE.md','NOTICE','Makefile','build-native.sh','run-native.sh','run-framework.sh','qualify-native.sh','native-env.sh','build.sh','run.sh','qualify.sh'}
 def current(rel):
  if rel in rootFiles or rel=='.github/workflows/rc4-native.yml':return True
  if not rel.startswith('native/'):return False
  return not rel.startswith(('native/reference-evidence/','native/web/reference-host.html'))
 runtime=[x for x in full if current(x[1])]
 manifests=[archive(out/'Nocturne-RC4-SDK.zip',runtime,head),archive(out/'Nocturne-RC4-Full-Development.zip',full,head)]
 html=ROOT/'native/Nocturne-RC4-Source-Build.html';shutil.copy2(html,out/'Nocturne-RC4-Gallery.html')
 with zipfile.ZipFile(out/'Nocturne-RC4-Gallery.zip','w',zipfile.ZIP_DEFLATED)as z:
  z.write(html,'Nocturne-RC4-Gallery.html');z.writestr('READ-FIRST.txt','Nocturne RC4 sdk.2. Open the HTML. This is the current implemented development build, not a fully qualified historical-art release. The SDK contains exact test receipts and remaining release gates.\n')
 for src,dest in [('README.md','Nocturne-RC4-README.md'),('LLM-HANDOFF.md','Nocturne-RC4-Handoff.md'),('native/evidence/BUILD-VERIFICATION.json','Nocturne-RC4-Build-Verification.json'),('native/docs/BUILD-SCOPE.md','Nocturne-RC4-Release-Status.md'),('native/CAPABILITY-STATUS.json','Nocturne-RC4-Capability-Status.json')]:shutil.copy2(ROOT/src,out/dest)
 cap=ROOT/'native/evidence/capture'
 if(cap/'MANIFEST.json').exists():
  with zipfile.ZipFile(out/'Nocturne-RC4-Capture-Evidence.zip','w',zipfile.ZIP_DEFLATED,compresslevel=4)as z:
   for p in sorted(cap.iterdir()):
    if p.is_file():z.write(p,'capture/'+p.name)
  shutil.copy2(cap/'Nocturne-RC4-Source-Build.mp4',out/'Nocturne-RC4-Captured.mp4')
 result={'build':'0.9.0-rc.4+sdk.2','sourceCommit':head,'verifiedSourceDigest':receipt['sourceAfter'],'localBuildVerified':receipt['localBuildVerified'],'fourRuntimeVerified':receipt['fourRuntimeVerified'],'fullRC4Qualified':False,'archives':manifests,'gallerySha256':sha(html),'wasmSha256':sha(ROOT/'native/dist/nocturne_native.wasm'),'notes':'Runtime SDK excludes historical engines; full development archive retains source history outside the current runtime closure. Source.1 inputs are unchanged.'}
 (out/'PACKAGE-RECEIPT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
