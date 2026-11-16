#!/usr/bin/env python3
"""Publish committed Nocturne history to an explicitly selected private GitHub repo.

Uses the operator's GitHub CLI credential helper. No token argument, no force push,
no installation, no archive reconstruction, no guessing between accounts. --plan
performs no GitHub/network or write operations. Existing repositories require
--update-existing and a matching already-configured private remote.
"""
from __future__ import annotations
import argparse,hashlib,json,os,re,shutil,subprocess,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def invoke(argv:list[str],cwd:Path,check:bool=True)->subprocess.CompletedProcess:
    result=subprocess.run(argv,cwd=cwd,text=True,capture_output=True,timeout=180,env={**os.environ,'GH_PROMPT_DISABLED':'1','GIT_TERMINAL_PROMPT':'0'})
    if check and result.returncode:raise RuntimeError(f'{argv[0]} {argv[1]} failed ({result.returncode}): {result.stderr.strip()}')
    return result

def validateRepository(value:str)->str:
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*/[A-Za-z0-9][A-Za-z0-9_.-]*',value) or '..' in value or value.endswith('.git'):
        raise ValueError('Specify OWNER/REPOSITORY, not a URL, path, or option')
    return value

def ensurePrivateDestination(client,repository:str,updateExisting:bool)->None:
    """Create only when lookup establishes absence; verify name and private flag.

    Errors, unknown state and string-valued privacy are not treated as success.
    Tests use PublicationDouble; normal operation uses GitHubClient below.
    """
    state=client.lookup(repository)
    if state is not None and not updateExisting:raise RuntimeError('Repository exists; no change made. Use --update-existing only for the matching configured remote.')
    if state is None:
        if updateExisting:raise RuntimeError('Update target is absent; omit --update-existing to create it')
        client.create(repository);state=client.lookup(repository)
    if not isinstance(state,dict) or state.get('private') is not True or state.get('full_name','').casefold()!=repository.casefold():
        raise RuntimeError('Private visibility and exact destination not confirmed. No source pushed.')

def restoreHistory(root:Path)->None:
    """Restore the current verified bundle without replacing any working files."""
    if (root/'.git').is_dir():return
    if (root/'.git').exists():raise RuntimeError('Existing worktree marker; use its original Git checkout')
    manifest=json.loads((root/'MANIFEST.json').read_text())
    entries=[(n,r) for n,r in manifest['files'].items() if n.startswith('git/') and n.endswith('.bundle')]
    if len(entries)!=1:raise RuntimeError('Expected one current history bundle in release manifest')
    name,record=entries[0];bundle=(root/name).resolve()
    try:bundle.relative_to(root.resolve())
    except ValueError:raise RuntimeError('Bundle path escapes SDK root')
    if not bundle.is_file() or bundle.stat().st_size!=record['bytes'] or hashlib.sha256(bundle.read_bytes()).hexdigest()!=record['sha256']:
        raise RuntimeError('History bundle does not match manifest')
    head=manifest.get('sourceCommit','')
    if not re.fullmatch(r'[0-9a-f]{40}',head):raise RuntimeError('Manifest source commit missing')
    heads=invoke(['git','bundle','list-heads',str(bundle)],root).stdout.splitlines()
    refs=[line.split(' ',1) for line in heads]
    matching=[ref[11:] for sha,ref in refs if sha==head and ref.startswith('refs/heads/')]
    branch=manifest.get('branch')
    if branch not in matching:
        if len(matching)!=1:raise RuntimeError('Current branch not unambiguously recorded')
        branch=matching[0]
    with tempfile.TemporaryDirectory(prefix='nocturne-history-',dir=root.parent) as temp:
        work=Path(temp)/'history';work.mkdir()
        # Import into a bare object database first. A normal init may attach HEAD
        # to master/main, which is also in a union bundle: Git correctly refuses
        # fetching into that checked-out branch. No working tree exists yet.
        invoke(['git','init','--bare','-q',str(work/'.git')],root)
        invoke(['git','bundle','verify',str(bundle)],work)
        # Retain every named ref, not only clone's default branch. HEAD has its
        # own explicit branch decision, avoiding archive fallback to RC3.
        specs=[f'{ref}:{ref}' for _,ref in refs if ref.startswith('refs/')]
        invoke(['git','fetch','--no-tags',str(bundle),*specs],work)
        invoke(['git','symbolic-ref','HEAD','refs/heads/'+branch],work)
        # Convert only this newly created database to an ordinary checkout.
        # read-tree creates the index, never writes over SDK/operator files.
        invoke(['git','config','core.bare','false'],work)
        invoke(['git','read-tree',head],work)
        invoke(['git','fsck','--full'],work)
        shutil.move(str(work/'.git'),str(root/'.git'))
    # Archive bytes are left unchanged; read-tree populates the index only.

def publicationRefs(root:Path)->dict[str,str]:
    lines=invoke(['git','for-each-ref','--format=%(objectname) %(refname)','refs/heads','refs/tags','refs/archive'],root).stdout.splitlines()
    result={}
    for line in lines:
        sha,source=line.split(' ',1)
        destination=('refs/tags/nocturne-archive/'+source[len('refs/archive/'):]) if source.startswith('refs/archive/') else source
        if destination in result:raise RuntimeError('Conflicting archived reference mapping')
        result[destination]=source
    if not result:raise RuntimeError('No committed references to publish')
    return result

class GitHubClient:
    def __init__(self,root:Path):self.root=root
    def lookup(self,repository:str):
        r=invoke(['gh','api','repos/'+repository],self.root,False)
        if r.returncode:
            if re.search(r'\(HTTP 404\)',r.stderr):return None
            raise RuntimeError('Repository lookup did not establish absence: '+r.stderr.strip())
        return json.loads(r.stdout)
    def create(self,repository:str):
        invoke(['gh','repo','create',repository,'--private','--disable-wiki','--description','Nocturne native terminal materials and spatial UI SDK'],self.root)

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('repository',type=validateRepository)
    parser.add_argument('--root',type=Path,default=ROOT);parser.add_argument('--plan',action='store_true');parser.add_argument('--update-existing',action='store_true')
    a=parser.parse_args();root=a.root.resolve();url='https://github.com/'+a.repository+'.git'
    if a.plan:
        print(json.dumps({'repository':a.repository,'visibility':'private','root':str(root),'steps':['verify/restore current bundled history','require clean tracked source','read gh authenticated login','create private repository or verify explicitly authorized matching existing remote','verify private visibility before push','atomic non-force push of heads, tags, and mapped archive refs','verify every remote SHA and private visibility'],'requires':['git','gh authenticated account'],'networkOrWritePerformed':False},indent=2));return 0
    if not shutil.which('git') or not shutil.which('gh'):raise RuntimeError('git and authenticated gh are required; no package or credential is installed by this script')
    restoreHistory(root)
    if invoke(['git','status','--porcelain','--untracked-files=no'],root).stdout.strip():raise RuntimeError('Tracked work differs from commit; review and commit changes before publication')
    branch=invoke(['git','symbolic-ref','--short','HEAD'],root).stdout.strip()
    remote=invoke(['git','remote','get-url','github'],root,False)
    if remote.returncode==0 and remote.stdout.strip()!=url:raise RuntimeError('github remote points at a different repository')
    if a.update_existing and remote.returncode:raise RuntimeError('--update-existing requires the existing matching github remote')
    invoke(['gh','auth','status','--hostname','github.com'],root)
    login=invoke(['gh','api','user','--jq','.login'],root).stdout.strip()
    print(f'Authenticated as {login}; destination {a.repository}; PRIVATE ONLY.',flush=True)
    client=GitHubClient(root);ensurePrivateDestination(client,a.repository,a.update_existing)
    invoke(['gh','auth','setup-git','--hostname','github.com'],root)
    if remote.returncode:invoke(['git','remote','add','github',url],root)
    refs=publicationRefs(root)
    invoke(['git','push','--atomic','github',*[src+':'+dst for dst,src in refs.items()]],root)
    if not a.update_existing:invoke(['gh','repo','edit',a.repository,'--default-branch',branch],root)
    remoteRefs={ref:sha for sha,ref in (line.split() for line in invoke(['git','ls-remote','github'],root).stdout.splitlines())}
    checked={}
    for dst,src in refs.items():
        local=invoke(['git','rev-parse',src],root).stdout.strip()
        if remoteRefs.get(dst)!=local:raise RuntimeError('Remote verification failed for '+dst)
        checked[dst]=local
    state=client.lookup(a.repository)
    if not state or state.get('private') is not True:raise RuntimeError('Post-push privacy check failed; investigate repository immediately')
    receipt={'repository':a.repository,'visibility':'private','login':login,'branch':branch,'verifiedRefs':checked,'commit':invoke(['git','rev-parse','HEAD'],root).stdout.strip(),'remoteVerified':True}
    path=root/'evidence/publication/GITHUB-VERIFIED.json';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2));return 0
if __name__=='__main__':
    try:raise SystemExit(main())
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as error:raise SystemExit('Publication stopped: '+str(error))
