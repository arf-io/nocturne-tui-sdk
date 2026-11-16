#!/usr/bin/env python3
"""Verify, safely extract and rebuild an exported Spatial Atelier SDK.
Runs real local tests; never downloads packages or modifies a remote repository.
Usage: python3 scripts/verify_atelier_release.py release.zip /tmp/atelier-check
The destination must not already exist. Requires cc, Python, Node22 and Git.
"""
from pathlib import Path, PurePosixPath
import argparse,hashlib,json,os,stat,subprocess,time,zipfile

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('archive',type=Path);p.add_argument('destination',type=Path);a=p.parse_args();dest=a.destination.resolve()
 if dest.exists():p.error('Destination exists; select an unused directory')
 dest.mkdir(parents=True)
 with zipfile.ZipFile(a.archive) as z:
  if sum(i.file_size for i in z.infolist())>1024**3:raise ValueError('Archive expands beyond 1 GiB limit')
  for item in z.infolist():
   n=PurePosixPath(item.filename)
   if n.is_absolute() or '..' in n.parts or not n.parts or n.parts[0]!='nocturne-atelier' or '\\' in item.filename:raise ValueError('Unsafe archive path')
   if stat.S_ISLNK(item.external_attr>>16):raise ValueError('Symlinks are not accepted')
  z.extractall(dest)
 root=dest/'nocturne-atelier';count=0
 for line in(root/'SHA256SUMS.txt').read_text().splitlines():
  expected,name=line.split('  ',1);q=(root/name).resolve()
  if root not in q.parents or not q.is_file():raise ValueError('Invalid manifest path: '+name)
  if hashlib.sha256(q.read_bytes()).hexdigest()!=expected:raise ValueError('Checksum mismatch: '+name)
  count+=1
 identity=json.loads((root/'BUILD-IDENTITY.json').read_text());steps=[]
 commands=[['sh','scripts/build.sh'],['python3','-m','unittest','discover','-s','tests','-p','test_*.py','-v'],['node','--test','tests/atelier/contracts.mjs','tests/atelier/settings.mjs','tests/atelier/rendering.mjs'],['node','tests/fleet/parity.mjs'],['node','tests/observatory/contracts.mjs'],['python3','scripts/check_atelier_tty.py']]
 for i,command in enumerate(commands):
  start=time.monotonic();run=subprocess.run(command,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=180)
  (dest/f'check-{i+1}.txt').write_text(run.stdout);steps.append({'argv':command,'exitCode':run.returncode,'seconds':round(time.monotonic()-start,3)})
  if run.returncode:raise RuntimeError('Check failed: '+' '.join(command)+'\n'+run.stdout[-4000:])
 bundle=root/'git/nocturne-spatial-atelier.bundle';recovered=dest/'recovered-git'
 subprocess.run(['git','clone',str(bundle),str(recovered)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=recovered,text=True).strip();assert head==identity['sourceCommit'],(head,identity)
 for name in ['Nocturne-Spatial-Atelier.html','bindings/typescript/atelier.ts','bindings/typescript/particles.ts']:
  assert(root/name).read_bytes()==(recovered/name).read_bytes(),name
 result={'archive':str(a.archive.resolve()),'manifestEntriesVerified':count,'checks':steps,'recoveredCommit':head,'gallerySourceBuild':identity['gallerySourceBuild'],'gitArchiveSourceParity':True,'passed':True,'rustCompiled':False,'physicalDevicesTested':False}
 (dest/'EXTRACTED-VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
