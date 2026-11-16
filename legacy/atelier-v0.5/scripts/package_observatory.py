#!/usr/bin/env python3
"""Export a complete source SDK, readable code, evidence and verified manifest.
Outputs must be outside the checkout. No font assets, dependency caches or symlinks.
"""
from pathlib import Path
import argparse,hashlib,json,re,shutil,subprocess,zipfile
from package_studio import ROOT,sourceFiles,TEXT_SUFFIXES,FONT_SUFFIXES
FONT_SUFFIXES=FONT_SUFFIXES|{'.flf','.ttc','.otc'}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--git-bundle',type=Path);a=p.parse_args();out=a.output.resolve()
 if out==ROOT or ROOT in out.parents:p.error('Output must be outside the checkout')
 out.mkdir(parents=True,exist_ok=True)
 files={name:data for name,data in sourceFiles() if Path(name).suffix.lower() not in FONT_SUFFIXES and not (name.startswith('dist/observatory/') and (Path(name).name.endswith('-first.png') or Path(name).name in {'first.png','optimized.png'}))}
 if a.git_bundle:
  if not a.git_bundle.is_file():p.error('Missing Git bundle')
  files['git/nocturne-observatory.bundle']=a.git_bundle.read_bytes()
 try:commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 except (OSError,subprocess.CalledProcessError):commit=None
 identity={'version':'0.4.0-source-preview','sourceCommit':commit,'branch':'feature/vol4-observatory','executionReport':'docs/observatory/TEST_REPORT.md','fontAssetsIncluded':False,'realAgentsConnected':False,'physicalSensorsTested':False,'rustCompiledLocally':False,'optionalHeadlessIntegrationTestedLocally':False}
 files['BUILD-IDENTITY.json']=(json.dumps(identity,indent=2)+'\n').encode()
 contents=['# Nocturne Observatory / complete source contents','## File tree','```text\n'+'\n'.join(sorted(files))+'\n```']
 for name,data in sorted(files.items()):
  q=Path(name)
  if q.suffix not in TEXT_SUFFIXES|{'.csv'} and q.name not in {'Makefile','.gitignore'}:continue
  if name.startswith(('dist/','legacy/')) or q.name in {'Nocturne-Gallery.html','Nocturne-Studio.html','Nocturne-Pearl-Fleet.html','Nocturne-Observatory.html'}:continue
  try:body=data.decode('utf-8')
  except UnicodeDecodeError:continue
  fence='`'*max(4,1+max((len(v)for v in re.findall(r'`+',body)),default=0));contents.extend([f'\n## {name}\n',f'{fence}{q.suffix.lstrip(".")}\n{body}\n{fence}'])
 files['SOURCE-CONTENTS.md']='\n'.join(contents).encode()
 manifest={name:hashlib.sha256(data).hexdigest() for name,data in sorted(files.items())}
 files['SHA256SUMS.txt']=''.join(f'{digest}  {name}\n'for name,digest in manifest.items()).encode()
 archive=out/'nocturne-observatory-v0.4.zip'
 with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9)as z:
  for name,data in sorted(files.items()):
   info=zipfile.ZipInfo('nocturne-observatory/'+name,date_time=(2026,9,17,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,data)
 with zipfile.ZipFile(archive)as z:
  assert z.testzip() is None
  for name,digest in manifest.items():assert hashlib.sha256(z.read('nocturne-observatory/'+name)).hexdigest()==digest,name
  assert not any(Path(n).suffix.lower() in FONT_SUFFIXES for n in z.namelist())
 (out/'Nocturne-Observatory-Source-Contents.md').write_bytes(files['SOURCE-CONTENTS.md']);(out/'LLM-HANDOFF.md').write_bytes(files['LLM-HANDOFF.md']);(out/'SHA256SUMS.txt').write_bytes(files['SHA256SUMS.txt'])
 for name in ['Nocturne-Observatory.html','Nocturne-Pearl-Fleet.html','dist/observatory/Nocturne-Observatory-60fps.mp4','dist/observatory/Nocturne-Observatory-Contact.png','dist/observatory/Nocturne-Observatory.png']:
  if (ROOT/name).is_file():shutil.copyfile(ROOT/name,out/Path(name).name)
 docs=out/'docs';docs.mkdir(exist_ok=True)
 for path in (ROOT/'docs/observatory').glob('*.md'):shutil.copyfile(path,docs/path.name)
 result={'archive':archive.name,'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'manifestEntries':len(manifest),'zipEntries':len(files),'sourceCommit':commit,'branch':identity['branch'],'verifiedArchive':True,'fontAssetsIncluded':False}
 (out/'RELEASE.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
