#!/usr/bin/env python3
"""Package the source SDK, complete readable sources and integrity manifest.

No network or persistent-library writes. Excludes caches, Git internals, vendor
checkouts and font assets. Optional --git-bundle includes a caller-created bundle.
Example: python3 scripts/package_studio.py --output /tmp/nocturne-release
"""
from __future__ import annotations
import argparse,hashlib,json,shutil,subprocess,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXCLUDED_DIRS={'.git','node_modules','__pycache__','target','vendor','.pytest_cache'}
FONT_SUFFIXES={'.ttf','.otf','.woff','.woff2','.tdf','.pfa','.pfb','.bdf','.pcf','.fon','.fnt'}
TEXT_SUFFIXES={'.py','.c','.h','.inc','.rs','.go','.ts','.js','.mjs','.json','.md','.yml','.yaml','.toml','.sh','.conf','.html','.txt'}
def sourceFiles():
    """Yield portable relative paths and bytes; never include symlinks or font files."""
    for path in sorted(ROOT.rglob('*')):
        rel=path.relative_to(ROOT)
        if not path.is_file() or path.is_symlink() or any(p in EXCLUDED_DIRS for p in rel.parts):continue
        if path.suffix.lower() in FONT_SUFFIXES or path.suffix in {'.pyc','.bundle','.zip'}:continue
        if rel.as_posix() in {'SOURCE-CONTENTS.md','SHA256SUMS.txt'} or path.name.startswith('tty-debug'):continue
        yield rel.as_posix(),path.read_bytes()
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True,type=Path);parser.add_argument('--git-bundle',type=Path);args=parser.parse_args()
    output=args.output.resolve()
    if output==ROOT or ROOT in output.parents:parser.error('--output must be outside the source tree')
    output.mkdir(parents=True,exist_ok=True);files=dict(sourceFiles())
    if args.git_bundle:
        if not args.git_bundle.is_file():parser.error('Git bundle does not exist')
        files['git/nocturne-studio.bundle']=args.git_bundle.read_bytes()
    try:commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,stderr=subprocess.DEVNULL,text=True).strip()
    except (OSError,subprocess.CalledProcessError):commit=None
    files['BUILD-IDENTITY.json']=(json.dumps({'version':'0.2.0-preview','sourceCommit':commit,'executionReport':'docs/TEST_REPORT_STUDIO.md','fontAssetsIncluded':False},indent=2)+'\n').encode()
    # Generated full contents include original source/template, not repeated bundles,
    # embedded WASM HTML or another previous full-source dump.
    source=['# Nocturne Studio / complete source contents\n','## File tree\n','```text\n'+'\n'.join(sorted(files))+'\n```\n']
    for name,data in files.items():
        p=Path(name)
        if p.suffix not in TEXT_SUFFIXES and p.name not in {'Makefile','.gitignore'}:continue
        if name.startswith(('dist/','legacy/')) or name in {'Nocturne-Studio.html','Nocturne-Gallery.html'}:continue
        try:text=data.decode('utf-8')
        except UnicodeDecodeError:continue
        fence='`'*max(4,1+max((len(x) for x in __import__('re').findall(r'`+',text)),default=0))
        source.extend([f'\n## {name}\n',f'{fence}{p.suffix.lstrip(".")}\n{text}\n{fence}\n'])
    allText='\n'.join(source).encode();files['SOURCE-CONTENTS.md']=allText
    manifest={name:hashlib.sha256(data).hexdigest() for name,data in sorted(files.items())}
    files['SHA256SUMS.txt']=''.join(f'{digest}  {name}\n' for name,digest in manifest.items()).encode()
    archive=output/'nocturne-studio-v0.2.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(files.items()):
            info=zipfile.ZipInfo('nocturne-studio/'+name,date_time=(2026,9,17,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,data)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,digest in manifest.items():assert hashlib.sha256(z.read('nocturne-studio/'+name)).hexdigest()==digest,name
        assert not any(Path(n).suffix.lower() in FONT_SUFFIXES for n in z.namelist())
    (output/'Nocturne-Studio-Source-Contents.md').write_bytes(allText)
    for src,name in [('Nocturne-Studio.html','Nocturne-Studio.html'),('dist/studio/Nocturne-Studio.mp4','Nocturne-Studio.mp4'),('dist/studio/Nocturne-Studio-Contact.png','Nocturne-Studio-Contact.png')]:
        if (ROOT/src).is_file():shutil.copyfile(ROOT/src,output/name)
    summary={'archive':archive.name,'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'entries':len(files),'sourceCommit':commit,'verifiedArchive':True,'fontAssetsIncluded':False}
    (output/'nocturne-release.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
