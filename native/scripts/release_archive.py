#!/usr/bin/env python3
"""Exact release-payload inspection and safe, non-overwriting extraction.

Manifest integrity is independent of build correctness. This module proves only
that every ZIP payload member is declared, unchanged and safely named. The caller
must execute the extracted build and compare its results separately.
"""
from __future__ import annotations
from pathlib import Path,PurePosixPath
import argparse,hashlib,json,os,stat,zipfile

TOP='nocturne-sdk'
MANIFEST=TOP+'/MANIFEST.json'


def _path(name: str) -> PurePosixPath:
    """Reject ambiguous portable path forms before opening any destination."""
    if not isinstance(name,str) or not name or '\\' in name or ':' in name or '\x00' in name:
        raise ValueError('Invalid archive path')
    parts=name.split('/')
    if any(p in {'','.','..'} for p in parts) or parts[0]!=TOP:
        raise ValueError('Non-canonical archive path: '+name)
    return PurePosixPath(name)


def _object(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('Duplicate manifest key: '+key)
        result[key]=value
    return result


def verifyArchive(archivePath: Path, maxExpandedBytes: int=10*1024**3) -> dict:
    """Verify all declared payload bytes, including exact membership.

    Raises ValueError/BadZipFile on unsafe names, capacity violations, duplicate
    names, symlinks, malformed metadata, missing/extra bytes or hash mismatch.
    No files are extracted and no code is executed.
    """
    if maxExpandedBytes<=0:raise ValueError('Positive archive capacity required')
    with zipfile.ZipFile(archivePath) as archive:
        infos=archive.infolist();names=[i.filename for i in infos]
        if len(names)!=len(set(names)):raise ValueError('Duplicate ZIP member')
        total=0
        for i in infos:
            _path(i.filename)
            mode=(i.external_attr>>16)&0o170000
            if i.is_dir() or mode not in {0,stat.S_IFREG}:raise ValueError('Only regular files allowed: '+i.filename)
            if i.flag_bits&1:raise ValueError('Encrypted archive member')
            total+=i.file_size
            if total>maxExpandedBytes:raise ValueError('Expanded archive capacity exceeded')
        if MANIFEST not in names:raise ValueError('Missing release manifest')
        if archive.getinfo(MANIFEST).file_size>16*1024**2:raise ValueError('Oversized manifest')
        manifest=json.loads(archive.read(MANIFEST),object_pairs_hook=_object)
        files=manifest.get('files')
        if not isinstance(files,dict) or not files:raise ValueError('Nonempty payload manifest required')
        declared=set()
        for relative,entry in files.items():
            name=TOP+'/'+relative;_path(name)
            if name==MANIFEST:raise ValueError('Manifest cannot list itself')
            if not isinstance(entry,dict) or type(entry.get('bytes')) is not int or entry['bytes']<0:
                raise ValueError('Invalid payload size')
            h=entry.get('sha256')
            if not isinstance(h,str) or len(h)!=64 or any(c not in '0123456789abcdef' for c in h):
                raise ValueError('Invalid SHA-256 field')
            declared.add(name)
        if set(names)!=(declared|{MANIFEST}):raise ValueError('Unlisted or missing payload member')
        for relative,entry in files.items():
            name=TOP+'/'+relative;info=archive.getinfo(name)
            if info.file_size!=entry['bytes']:raise ValueError('Size mismatch: '+relative)
            h=hashlib.sha256()
            with archive.open(info) as stream:
                while block:=stream.read(1024*1024):h.update(block)
            if h.hexdigest()!=entry['sha256']:raise ValueError('Hash mismatch: '+relative)
        return manifest


def extractVerified(archivePath: Path, destination: Path, maxExpandedBytes: int=10*1024**3) -> Path:
    """Extract a verified archive into a NEW directory; return its SDK root.

    Permission bits are normalized to readable 0644/0755. No symlinks, devices,
    setuid bits, existing-directory writes or arbitrary outside paths are used.
    Partial extraction is retained on I/O failure for inspection, never called a pass.
    """
    if destination.exists():raise FileExistsError(str(destination))
    verifyArchive(archivePath,maxExpandedBytes)
    destination.mkdir(parents=True,exist_ok=False)
    with zipfile.ZipFile(archivePath) as archive:
        for info in archive.infolist():
            relative=_path(info.filename);target=destination.joinpath(*relative.parts)
            target.parent.mkdir(parents=True,exist_ok=True)
            with archive.open(info) as source,target.open('xb') as output:
                while block:=source.read(1024*1024):output.write(block)
            os.chmod(target,0o755 if (info.external_attr>>16)&0o111 else 0o644)
    return destination/TOP


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive',type=Path);parser.add_argument('--extract',type=Path)
    args=parser.parse_args();manifest=verifyArchive(args.archive)
    result={'manifestEntries':len(manifest['files']),'sourceCommit':manifest.get('sourceCommit'),'verified':True}
    if args.extract:result['root']=str(extractVerified(args.archive,args.extract))
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
