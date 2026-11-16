#!/usr/bin/env python3
"""Extract exact payload, verify every manifest entry, rebuild, then rerun source checks."""
from pathlib import Path,PurePosixPath
import argparse,json,hashlib,zipfile,subprocess,sys,time,os

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('archive');p.add_argument('--destination',required=True);p.add_argument('--report',required=True);a=p.parse_args()
 archive=Path(a.archive).resolve();dest=Path(a.destination).resolve();reportPath=Path(a.report).resolve()
 if dest.exists():raise SystemExit('Refusing to overwrite extraction directory')
 dest.mkdir(parents=True);result={'archive':archive.name,'archiveSha256':sha(archive),'checks':[],'passed':False};started=time.monotonic()
 def record(name,argv,cwd):
  log=reportPath.parent/('extract-'+name+'.log');start=time.monotonic()
  with log.open('wb')as f:r=subprocess.run(argv,cwd=cwd,stdout=f,stderr=subprocess.STDOUT,timeout=400)
  item={'id':name,'exitCode':r.returncode,'seconds':round(time.monotonic()-start,3),'log':log.name,'logSha256':sha(log)};result['checks'].append(item);reportPath.write_text(json.dumps(result,indent=2)+'\n');print(name,r.returncode,flush=True)
  if r.returncode:raise RuntimeError('Extracted check failed: '+name)
 try:
  with zipfile.ZipFile(archive)as z:
   names=z.namelist()
   if len(names)!=len(set(names)):raise RuntimeError('Duplicate ZIP paths')
   for info in z.infolist():
    path=PurePosixPath(info.filename)
    if path.is_absolute()or'..'in path.parts or not path.parts or path.parts[0]!='nocturne-sdk':raise RuntimeError('Unsafe path')
    if (info.external_attr>>16)&0o170000==0o120000:raise RuntimeError('Symlink not allowed')
   if z.testzip():raise RuntimeError('Archive CRC failed')
   z.extractall(dest)
  root=dest/'nocturne-sdk';manifest=json.loads((root/'MANIFEST.json').read_text());observed={x.relative_to(root).as_posix()for x in root.rglob('*')if x.is_file()and x.relative_to(root).as_posix()!='MANIFEST.json'}
  if observed!=set(manifest['files']):raise RuntimeError('Unlisted/missing payload files')
  for rel,item in manifest['files'].items():
   path=root/rel
   if path.stat().st_size!=item['bytes']or sha(path)!=item['sha256']:raise RuntimeError('Manifest mismatch: '+rel)
  result['manifestEntriesVerified']=len(manifest['files']);result['archiveCrcPassed']=True
  html=root/'native/Nocturne-RC4-Source-Build.html';wasm=root/'native/dist/nocturne_native.wasm';lib=root/'native/dist'/('libnocturne_native.dylib'if sys.platform=='darwin'else'libnocturne_native.so')
  before={'html':sha(html),'wasm':sha(wasm),'nativeLibrary':sha(lib)}
  record('qualify',[sys.executable,'native/scripts/qualify.py'],root)
  after={'html':sha(html),'wasm':sha(wasm),'nativeLibrary':sha(lib)}
  result['rebuiltBefore']=before;result['rebuiltAfter']=after;result['rebuiltByteIdentical']=before==after
  if before!=after:raise RuntimeError('Rebuilt artifacts differ')
  bundle=root/'git/nocturne-rc4-source.bundle'
  if bundle.exists():
   record('bundle-clone',['git','clone',str(bundle),str(dest/'history')],root)
   head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=dest/'history',text=True).strip();result['gitHead']=head
   if head!=manifest['sourceCommit']:raise RuntimeError('Git head mismatch')
  else:result['gitHistory']='Not included in the runtime-only archive; retained in full-development archive'
  result['localQualification']=json.loads((root/'native/evidence/BUILD-VERIFICATION.json').read_text());result['passed']=True
 except Exception as e:result['exception']=str(e)
 result['seconds']=round(time.monotonic()-started,3);reportPath.write_text(json.dumps(result,indent=2)+'\n');print('Extraction verification',result['passed'])
 return 0 if result['passed']else 2
if __name__=='__main__':raise SystemExit(main())
