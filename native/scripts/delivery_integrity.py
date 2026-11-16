"""Closed SDK output inventory, ordered splitting and independent Git patch replay."""
import hashlib,json,subprocess
from pathlib import Path

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def safe(root,name):
    p=Path(name)
    if not name or p.is_absolute() or '..' in p.parts or p.as_posix()!=name:raise ValueError('Unsafe delivery path')
    path=root/p
    if any(parent.is_symlink() for parent in [path,*path.parents] if parent!=root.parent):raise ValueError('Delivery symlink')
    return path

def closeDelivery(output,partBytes=15*1024*1024):
    root=Path(output).resolve()
    if partBytes<1:raise ValueError('Invalid part size')
    files={};splits={}
    for path in sorted(root.rglob('*')):
        if path.is_symlink():raise ValueError('Delivery symlink')
        if not path.is_file():continue
        name=path.relative_to(root).as_posix()
        if name in {'DELIVERY.json','SHA256SUMS.txt'} or '.part-' in name:raise ValueError('Output already closed')
        files[name]={'bytes':path.stat().st_size,'sha256':digest(path)}
        if path.stat().st_size>partBytes:
            parts=[]
            with path.open('rb') as stream:
                index=1
                while block:=stream.read(partBytes):
                    part=name+f'.part-{index:05d}';target=safe(root,part)
                    with target.open('xb') as handle:handle.write(block)
                    parts.append(part);files[part]={'bytes':len(block),'sha256':digest(target)};index+=1
            splits[name]=parts
    record={'schema':'nocturne.delivery.v1','files':files,'splits':splits}
    (root/'DELIVERY.json').write_text(json.dumps(record,indent=2)+'\n')
    sums={name:item['sha256'] for name,item in files.items()};sums['DELIVERY.json']=digest(root/'DELIVERY.json')
    (root/'SHA256SUMS.txt').write_text(''.join(f'{value}  {name}\n' for name,value in sorted(sums.items())))
    return record

def verifyDelivery(output):
    root=Path(output).resolve();record=json.loads((root/'DELIVERY.json').read_text())
    if record.get('schema')!='nocturne.delivery.v1':raise ValueError('Unknown delivery schema')
    files=record['files']
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() or p.is_symlink()}
    if actual!=set(files)|{'DELIVERY.json','SHA256SUMS.txt'}:raise ValueError('Delivery inventory differs')
    for name,item in files.items():
        p=safe(root,name)
        if not p.is_file() or p.stat().st_size!=item['bytes'] or digest(p)!=item['sha256']:raise ValueError('Delivery file differs: '+name)
    sums={name:item['sha256'] for name,item in files.items()};sums['DELIVERY.json']=digest(root/'DELIVERY.json')
    expected=''.join(f'{value}  {name}\n' for name,value in sorted(sums.items()))
    if (root/'SHA256SUMS.txt').read_text()!=expected:raise ValueError('Checksum inventory differs')
    for name,parts in record['splits'].items():
        h=hashlib.sha256();length=0
        if not parts or len(set(parts))!=len(parts):raise ValueError('Invalid split order')
        for index,part in enumerate(parts,1):
            if part!=name+f'.part-{index:05d}' or part not in files:raise ValueError('Invalid split part')
            with safe(root,part).open('rb') as stream:
                for block in iter(lambda:stream.read(1024*1024),b''):h.update(block);length+=len(block)
        if length!=files[name]['bytes'] or h.hexdigest()!=files[name]['sha256']:raise ValueError('Split reassembly differs')
    return {'passed':True,'files':len(files),'reassembledFiles':len(record['splits'])}

def git(repo,*args):
    return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.STDOUT)

def exportPatch(repo,baseline,head,output):
    baseline=git(repo,'rev-parse',baseline+'^{commit}').decode().strip();head=git(repo,'rev-parse',head+'^{commit}').decode().strip()
    patch=Path(output)/'source.patch'
    patch.write_bytes(git(repo,'diff','--binary','--full-index',baseline,head))
    record={'baseline':baseline,'head':head,'tree':git(repo,'rev-parse',head+'^{tree}').decode().strip(),'patch':'source.patch','sha256':digest(patch)}
    (Path(output)/'PATCH.json').write_text(json.dumps(record,indent=2)+'\n');return record

def verifyPatch(repo,record,output,destination):
    patch=safe(Path(output).resolve(),record['patch'])
    if digest(patch)!=record['sha256']:raise ValueError('Patch digest differs')
    dest=Path(destination)
    if dest.exists():raise ValueError('Patch destination exists')
    try:
        subprocess.run(['git','clone','--no-hardlinks','--no-checkout',str(repo),str(dest)],check=True,capture_output=True)
        git(dest,'checkout','--detach',record['baseline']);git(dest,'apply','--index',str(patch))
        tree=git(dest,'write-tree').decode().strip()
        if tree!=record['tree']:raise ValueError('Reapplied patch tree differs')
    except subprocess.CalledProcessError as error:raise ValueError('Patch replay failed') from error
    return {'passed':True,'tree':tree}
