"""Package existing verified outputs; never regenerates renderer fixtures."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT.parent
excluded={'__pycache__','node_modules','target','.git'}

def sources():
    return [p for p in sorted(ROOT.rglob('*')) if p.is_file() and not excluded.intersection(p.relative_to(ROOT).parts)
            and p.name not in {'SOURCE-CONTENTS.md','SHA256SUMS.txt'} and p.suffix not in {'.pyc','.pyo'}]

textFiles=[]
for p in sources():
    if p.suffix in {'.py','.c','.h','.inc','.ts','.js','.mjs','.rs','.go','.mod','.toml','.json','.yaml','.yml','.sh','.html','.md','.txt'} or p.name=='.gitignore':
        textFiles.append(p)
content=['# Nocturne: complete readable sources','', 'This document contains complete source/configuration/documentation files, not patches. Binary assets remain in the archive. The actual file tree is authoritative.', '']
for p in textFiles:
    relative=p.relative_to(ROOT).as_posix()
    content.extend([f'## {relative}','', '``````'+p.suffix.lstrip('.'),p.read_text().rstrip(),'``````',''])
(ROOT/'SOURCE-CONTENTS.md').write_text('\n'.join(content))
files=sources()+[ROOT/'SOURCE-CONTENTS.md']
manifest=''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT).as_posix()}\n' for p in sorted(files))
(ROOT/'SHA256SUMS.txt').write_text(manifest)
archive=DEST/'nocturne-surfaces.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in sorted(files+[ROOT/'SHA256SUMS.txt']):z.write(p,Path(ROOT.name)/p.relative_to(ROOT))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for line in manifest.splitlines():
        digest,relative=line.split('  ',1)
        assert hashlib.sha256(z.read(f'{ROOT.name}/{relative}')).hexdigest()==digest,relative
for src,dest in [(ROOT/'Nocturne-Gallery.html',DEST/'Nocturne-Gallery.html'),
                 (ROOT/'dist/Nocturne-Studies.mp4',DEST/'Nocturne-Studies.mp4'),
                 (ROOT/'dist/Nocturne-Studies.png',DEST/'Nocturne-Studies.png'),
                 (ROOT/'dist/Nocturne-Studies-II.png',DEST/'Nocturne-Studies-II.png'),
                 (ROOT/'SOURCE-CONTENTS.md',DEST/'Nocturne-Source-Contents.md')]:
    shutil.copyfile(src,dest)
report=[]
for p in [archive,DEST/'Nocturne-Gallery.html',DEST/'Nocturne-Studies.mp4',DEST/'Nocturne-Studies.png',DEST/'Nocturne-Studies-II.png',DEST/'Nocturne-Source-Contents.md']:
    report.append({'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(DEST/'Nocturne-Release.json').write_text(json.dumps({'archiveFiles':len(files)+1,'manifestVerified':True,'artifacts':report},indent=2)+'\n')
print(json.dumps(report,indent=2))
