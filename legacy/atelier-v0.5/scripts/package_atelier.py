#!/usr/bin/env python3
"""Package a verified source checkout, generated gallery, docs/evidence and Git
history. Excludes fonts, symlinks, dependency caches and temporary preview shots.
The output directory must be outside the checkout. No remote or Library writes.
"""
from pathlib import Path
import argparse,hashlib,json,re,shutil,subprocess,zipfile
from package_studio import ROOT,sourceFiles,TEXT_SUFFIXES,FONT_SUFFIXES
FONT_SUFFIXES=FONT_SUFFIXES|{'.flf','.ttc','.otc'}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--git-bundle',type=Path);a=p.parse_args();out=a.output.resolve()
 if out==ROOT or ROOT in out.parents:p.error('Output must be outside checkout')
 out.mkdir(parents=True,exist_ok=True)
 temporary={'first.png','inspect-dag.png','inspect-windows.png','warp-updated.png','browser-tested.png','legacy-pid.txt','preview-exit.txt','interrupt-before.txt'}
 files={n:d for n,d in sourceFiles() if Path(n).suffix.lower() not in FONT_SUFFIXES and not(n.startswith('dist/atelier/') and Path(n).name in temporary)}
 if a.git_bundle:
  if not a.git_bundle.is_file():p.error('Missing Git bundle')
  files['git/nocturne-spatial-atelier.bundle']=a.git_bundle.read_bytes()
 try:commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
 except (OSError,subprocess.CalledProcessError):commit=None;branch=None
 gallery=(ROOT/'Nocturne-Spatial-Atelier.html').read_text();match=re.search(r'"build":"([0-9a-f]+)"',gallery)
 identity={'version':'0.5.0-source-preview','sourceCommit':commit,'branch':branch,'gallerySourceBuild':match.group(1) if match else None,'executionReport':'docs/atelier/TEST_REPORT.md','fontAssetsIncluded':False,'realAgentsConnected':False,'physicalSensorsTested':False,'rustCompiledLocally':False,'optionalHeadlessIntegrationTestedLocally':False}
 files['BUILD-IDENTITY.json']=(json.dumps(identity,indent=2)+'\n').encode()
 contents=['# Nocturne Spatial Atelier / complete source contents','## File tree','```text\n'+'\n'.join(sorted(files))+'\n```']
 for name,data in sorted(files.items()):
  q=Path(name)
  if q.suffix not in TEXT_SUFFIXES|{'.csv'} and q.name not in {'Makefile','.gitignore'}:continue
  if name.startswith(('dist/','legacy/')) or (q.suffix=='.html' and '/' not in name):continue
  try:body=data.decode('utf-8')
  except UnicodeDecodeError:continue
  fence='`'*max(4,1+max((len(v)for v in re.findall(r'`+',body)),default=0));contents.extend([f'\n## {name}\n',f'{fence}{q.suffix.lstrip(".")}\n{body}\n{fence}'])
 files['SOURCE-CONTENTS.md']='\n'.join(contents).encode();manifest={n:hashlib.sha256(d).hexdigest() for n,d in sorted(files.items())};files['SHA256SUMS.txt']=''.join(f'{v}  {k}\n' for k,v in manifest.items()).encode()
 archive=out/'nocturne-spatial-atelier-v0.5.zip'
 with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9)as z:
  for name,data in sorted(files.items()):
   info=zipfile.ZipInfo('nocturne-atelier/'+name,date_time=(2026,9,18,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,data)
 with zipfile.ZipFile(archive)as z:
  assert z.testzip() is None
  for name,digest in manifest.items():assert hashlib.sha256(z.read('nocturne-atelier/'+name)).hexdigest()==digest,name
  assert not any(Path(n).suffix.lower() in FONT_SUFFIXES for n in z.namelist())
 for n in ['LLM-HANDOFF.md','BUILD-IDENTITY.json','SHA256SUMS.txt']: (out/n).write_bytes(files[n])
 (out/'Nocturne-Spatial-Atelier-Source-Contents.md').write_bytes(files['SOURCE-CONTENTS.md'])
 for n in ['START-HERE.html','Nocturne-Spatial-Atelier.html','dist/atelier/Nocturne-Spatial-Atelier-60fps.mp4','dist/atelier/Nocturne-Spatial-Atelier-Contact.png','dist/atelier/Nocturne-Spatial-Atelier.png','dist/atelier/Nocturne-Spatial-Atelier-windows.png']:
  if(ROOT/n).is_file():shutil.copyfile(ROOT/n,out/Path(n).name)
 docs=out/'docs';docs.mkdir(exist_ok=True)
 for q in (ROOT/'docs/atelier').glob('*.md'):shutil.copyfile(q,docs/q.name)
 result={'archive':archive.name,'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'manifestEntries':len(manifest),'zipEntries':len(files),'sourceCommit':commit,'gallerySourceBuild':identity['gallerySourceBuild'],'branch':branch,'verifiedArchive':True,'fontAssetsIncluded':False}
 (out/'RELEASE.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
