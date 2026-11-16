#!/usr/bin/env python3
"""Create a deterministic, complete source-only development candidate, without Git.

This is deliberately NOT package_contracts.py: that historical packager requires
private union history and a whole SDK release run. Source inputs have neither.
No files are silently excluded. Disallowed material rejects the entire package.
Integrity is verified with release_archive; build/host qualification is separate.
"""
from __future__ import annotations
import argparse, hashlib, json, os, stat, zipfile
from pathlib import Path
from release_archive import verifyArchive

FORBIDDEN_PARTS={'.git','.hg','.svn','vendor','node_modules','target','compiler',
                 'rust-toolchain','cargo-home','.cargo','__pycache__','.venv','keys'}
FORBIDDEN_SUFFIXES={'.bundle','.ttf','.otf','.woff','.woff2','.pfb','.pfa','.fon','.fnt','.pem','.key'}
STAMP=(1980,1,1,0,0,0)


def sha(path: Path) -> str:
    """Stream SHA-256 for a file without loading large fixtures into memory."""
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        while data:=stream.read(1024*1024):digest.update(data)
    return digest.hexdigest()


def packageSource(root: Path, output: Path) -> dict:
    """Package all regular source files into a NEW ZIP with an exact manifest.

    Inputs: source root and outside-root output ZIP. Returns verified manifest.
    Rejects noncanonical paths, links/special files, known private/cache/compiler/
    font material, an existing output, or a reserved root MANIFEST.json. Filesystem
    errors propagate. No source writes, Git operations, signing or publication.
    Byte identity is deterministic with the same Python/zlib implementation.
    Filename screening is not a substitute for the operator's secret/license audit.
    Example: packageSource(Path('clean-source'), Path('/tmp/source-candidate.zip'))
    """
    root,output=root.resolve(),output.absolute()
    if not root.is_dir():raise NotADirectoryError(str(root))
    if output.resolve().is_relative_to(root):raise ValueError('Output must be outside source')
    if output.exists() or output.is_symlink():raise FileExistsError(str(output))
    files={}
    for path in sorted(root.rglob('*')):
        relative=path.relative_to(root);name=relative.as_posix()
        if any(part in FORBIDDEN_PARTS for part in relative.parts) or path.suffix.lower() in FORBIDDEN_SUFFIXES:
            raise ValueError('Disallowed source material: '+name)
        if path.is_symlink():raise ValueError('Symlink source: '+name)
        if path.is_dir():continue
        if not stat.S_ISREG(path.stat().st_mode):raise ValueError('Nonregular source: '+name)
        if any(c in name for c in ('\\',':','\x00')) or any(p in ('','.','..') for p in relative.parts):
            raise ValueError('Noncanonical source path: '+name)
        if name=='MANIFEST.json':raise ValueError('Reserved packaging manifest exists in source')
        files[name]={'bytes':path.stat().st_size,'sha256':sha(path),'executable':bool(path.stat().st_mode&0o111)}
    if not files:raise ValueError('No source payload')
    manifest={'schema':'nocturne.source-candidate.v1','sourceRole':'preserved development source candidate',
              'stableRelease':False,'fullRC4Qualified':False,'gitHistoryIncluded':False,'files':files}
    output.parent.mkdir(parents=True,exist_ok=True)
    # Exclusive creation protects operator files. A failed write is an unfinished
    # artifact, never accepted; verification runs after the ZIP is fully closed.
    with output.open('xb') as raw,zipfile.ZipFile(raw,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for relative,entry in files.items():
            path=root/relative
            info=zipfile.ZipInfo('nocturne-sdk/'+relative,STAMP)
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=(0o100755 if entry['executable'] else 0o100644)<<16
            with path.open('rb') as source,archive.open(info,'w') as target:
                while block:=source.read(1024*1024):target.write(block)
        info=zipfile.ZipInfo('nocturne-sdk/MANIFEST.json',STAMP)
        info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
        archive.writestr(info,json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    verified=verifyArchive(output)
    if verified!=manifest:raise ValueError('Verified manifest differs')
    return verified


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=packageSource(args.source,args.output)
    print(json.dumps({'files':len(result['files']),'archiveSha256':sha(args.output),
                      'integrityVerified':True,'stableRelease':False},indent=2))

if __name__=='__main__':main()
