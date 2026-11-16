#!/usr/bin/env python3
"""Hash and compare release archives, including all removals and compression costs.

No extraction or code execution. Directory entries are omitted. A single common
root directory is normalized; no other paths are remapped. Preserved files are not
an assertion of implemented/ported features or runtime compatibility.
"""
from __future__ import annotations
import argparse,hashlib,json,stat,zipfile
from pathlib import Path,PurePosixPath
from collections import defaultdict

def shaFile(path:Path)->str:
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()

def category(path:str)->str:
    if path.startswith('git/') and path.endswith('.bundle'):return 'Git history bundles'
    if '/evidence/capture/' in path:return 'Native frame/video capture'
    if path.startswith('native/dist/'):return 'Native build outputs'
    if path.startswith('native/evidence/'):return 'Native reports and other evidence'
    if path.startswith('dist/'):return 'Historical build outputs and previews'
    if path.startswith('legacy/'):return 'Historical reference source and galleries'
    if path.startswith(('native/src/','native/include/','native/bindings/','native/hosts/')):return 'Current implementation and bindings'
    if path.startswith(('tests/','native/tests/')):return 'Tests and reference fixtures'
    if path.startswith('git/'):return 'Git support files'
    return 'Other source, documentation and metadata'

def implementation(path:str)->bool:
    prefixes=('native/src/','native/include/','native/bindings/','native/hosts/','src/','include/','bindings/','sdk/','apps/')
    return path.startswith(prefixes) and path.endswith(('.c','.h','.inc','.rs','.go','.py','.ts','.js','.mjs','.tsx','.json','.toml','.mod','.sum'))

def inventoryArchive(path:Path)->dict:
    """Return exact members, sizes and SHA-256; raise for unsafe/ambiguous ZIPs."""
    path=Path(path);files={};groups=defaultdict(lambda:{'members':0,'uncompressedBytes':0,'compressedBytes':0})
    with zipfile.ZipFile(path) as archive:
        members=[m for m in archive.infolist() if not m.is_dir()]
        names=[m.filename for m in members]
        if len(names)!=len(set(names)):raise ValueError('Duplicate archive member')
        if sum(m.file_size for m in members)>8_000_000_000:raise ValueError('Archive exceeds accounting safety limit')
        first={PurePosixPath(n).parts[0] for n in names}
        root=next(iter(first)) if len(first)==1 and all(len(PurePosixPath(n).parts)>1 for n in names) else None
        for member in members:
            raw=PurePosixPath(member.filename)
            if raw.is_absolute() or '..' in raw.parts or '\\' in member.filename:raise ValueError('Unsafe archive path')
            if stat.S_ISLNK(member.external_attr>>16):raise ValueError('Symlink member requires separate review')
            normalized=PurePosixPath(*raw.parts[1:]).as_posix() if root else raw.as_posix()
            digest=hashlib.sha256()
            with archive.open(member) as stream:
                for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
            record={'bytes':member.file_size,'compressedBytes':member.compress_size,'sha256':digest.hexdigest(),'category':category(normalized)}
            files[normalized]=record;g=groups[record['category']];g['members']+=1;g['uncompressedBytes']+=member.file_size;g['compressedBytes']+=member.compress_size
    compressed=sum(v['compressedBytes'] for v in files.values());size=path.stat().st_size
    return {'name':path.name,'sha256':shaFile(path),'bytes':size,'fileCount':len(files),'uncompressedBytes':sum(v['bytes'] for v in files.values()),'compressedPayloadBytes':compressed,'zipStructureBytes':size-compressed,'normalizedRoot':root,'categories':dict(groups),'files':files}

def compareArchives(before:Path,after:Path)->dict:
    """Compare every payload path; never infer feature parity from archive size."""
    old=inventoryArchive(before);new=inventoryArchive(after);a=old['files'];b=new['files']
    removed=sorted(a.keys()-b.keys());added=sorted(b.keys()-a.keys());shared=a.keys()&b.keys()
    changed=sorted(n for n in shared if a[n]['sha256']!=b[n]['sha256'])
    unchanged=sorted(shared-set(changed));hashes=defaultdict(list)
    for n,v in b.items():hashes[v['sha256']].append(n)
    groups=[]
    for key in sorted(old['categories'].keys()|new['categories'].keys()):
        x=old['categories'].get(key,{}).get('compressedBytes',0);y=new['categories'].get(key,{}).get('compressedBytes',0)
        groups.append({'category':key,'beforeCompressedBytes':x,'afterCompressedBytes':y,'savedCompressedBytes':x-y})
    sourceRemoved=[n for n in removed if implementation(n)]
    return {'schema':'nocturne.archive.comparison.v1','before':old,'after':new,'removed':removed,'added':added,'changed':changed,'unchanged':unchanged,'sameContentElsewhere':{n:hashes[a[n]['sha256']] for n in removed if a[n]['sha256'] in hashes},'implementationRemoved':sourceRemoved,'noImplementationFilesRemoved':not sourceRemoved,'featurePortingQualified':False,'categoryChanges':groups,'sizeReductionBytes':old['bytes']-new['bytes'],'structureReductionBytes':old['zipStructureBytes']-new['zipStructureBytes']}

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('before',type=Path);parser.add_argument('after',type=Path);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();report=compareArchives(args.before,args.after);args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('sizeReductionBytes','implementationRemoved','noImplementationFilesRemoved','featurePortingQualified')},indent=2))
    return 2 if report['implementationRemoved'] else 0
if __name__=='__main__':raise SystemExit(main())
