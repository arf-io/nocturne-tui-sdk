#!/usr/bin/env python3
"""Package the full Pearl Fleet source SDK and verify every ZIP entry.
Excludes font assets, dependency caches, vendor checkouts and Git internals.
Example: python3 scripts/package_fleet.py --output /tmp/pearl-release --git-bundle /tmp/pearl.bundle
"""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,zipfile,re
from package_studio import sourceFiles,ROOT,TEXT_SUFFIXES,FONT_SUFFIXES

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--git-bundle',type=Path);a=p.parse_args();out=a.output.resolve()
 if out==ROOT or ROOT in out.parents:p.error('Output must be outside the source checkout')
 out.mkdir(parents=True,exist_ok=True);files=dict(sourceFiles())
 if a.git_bundle:files['git/nocturne-pearl-fleet.bundle']=a.git_bundle.read_bytes()
 try:commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 except (OSError,subprocess.CalledProcessError):commit=None
 files['BUILD-IDENTITY.json']=(json.dumps({'version':'0.3.0-preview','sourceCommit':commit,'executionReport':'docs/fleet/TEST_REPORT.md','fontAssetsIncluded':False,'realAgentsConnected':False},indent=2)+'\n').encode()
 text=['# Nocturne / Pearl Fleet — complete source contents','## File tree','```text\n'+'\n'.join(sorted(files))+'\n```']
 for name,data in files.items():
  q=Path(name)
  if q.suffix not in TEXT_SUFFIXES and q.name not in {'Makefile','.gitignore'}:continue
  if name.startswith(('dist/','legacy/')) or name in {'Nocturne-Gallery.html','Nocturne-Studio.html','Nocturne-Pearl-Fleet.html'}:continue
  try:body=data.decode('utf-8')
  except UnicodeDecodeError:continue
  fence='`'*max(4,1+max((len(x) for x in re.findall(r'`+',body)),default=0));text.extend([f'\n## {name}\n',f'{fence}{q.suffix.lstrip(".")}\n{body}\n{fence}'])
 files['SOURCE-CONTENTS.md']='\n'.join(text).encode()
 manifest={name:hashlib.sha256(data).hexdigest() for name,data in sorted(files.items())}
 files['SHA256SUMS.txt']=''.join(f'{h}  {name}\n' for name,h in manifest.items()).encode()
 archive=out/'nocturne-pearl-fleet-v0.3.zip'
 with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for name,data in sorted(files.items()):
   info=zipfile.ZipInfo('nocturne-fleet/'+name,date_time=(2026,9,17,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,data)
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None
  for name,h in manifest.items():assert hashlib.sha256(z.read('nocturne-fleet/'+name)).hexdigest()==h,name
  assert not any(Path(n).suffix.lower() in FONT_SUFFIXES for n in z.namelist())
 (out/'Nocturne-Pearl-Fleet-Source-Contents.md').write_bytes(files['SOURCE-CONTENTS.md'])
 for name in ['Nocturne-Pearl-Fleet.html','dist/fleet/Nocturne-Pearl-Fleet.mp4','dist/fleet/Nocturne-Pearl-Fleet.png','dist/fleet/Nocturne-Pearl-Fleet-workspace.png','dist/fleet/Nocturne-Pearl-Fleet-streaming.png','dist/fleet/Nocturne-Pearl-Fleet-dense.png']:
  if (ROOT/name).is_file():shutil.copyfile(ROOT/name,out/Path(name).name)
 for path in (ROOT/'docs/fleet').glob('*.md'):(out/'docs').mkdir(exist_ok=True);shutil.copyfile(path,out/'docs'/path.name)
 result={'archive':archive.name,'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'entries':len(files),'sourceCommit':commit,'verifiedArchive':True,'fontAssetsIncluded':False}
 (out/'RELEASE.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
