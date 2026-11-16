#!/usr/bin/env python3
"""Create one complete, four-runtime-tested development SDK and portable gallery.

No dependency installation, remote mutation, version renaming without source
changes, or publication from RUNNING receipts. Verification after extraction is a
separate executable step; this packager never declares that future result.
"""
from pathlib import Path
import argparse,hashlib,json,os,re,shutil,subprocess,zipfile
from qualify import fingerprint
from release_archive import verifyArchive
from release_identity import loadReleaseIdentity, validateCompletedBuild
from sdk_contract import validateSDKContract,validateSDKContractArtifacts
from dependencies import inspectNativeSymbols
ROOT=Path(__file__).resolve().parents[2]
FONTS={'.ttf','.otf','.woff','.woff2','.tdf','.flf','.pfb','.pfa','.fon','.fnt'}
SKIP={'.git','.venv','node_modules','target','__pycache__','.pytest_cache','.nocturne-tools'}

def validateShippingCore(path:Path)->dict:
    """Reject profiling and forbidden host imports in the actual selected SDK DSO."""
    path=Path(path)
    if path.is_symlink() or not path.is_file():raise ValueError('Shipping core must be a regular binary')
    try:
        symbols=subprocess.run(['nm',str(path)],capture_output=True,text=True,check=True)
        linked=inspectNativeSymbols(path)
    except (OSError,subprocess.CalledProcessError) as error:
        raise ValueError('Shipping core binary inspection failed: '+str(error)) from error
    profiling=[line.split()[-1] for line in symbols.stdout.splitlines()
               if line.split() and ('__llvm_profile' in line or '__llvm_prf' in line)]
    errors=list(linked['errors'])
    if profiling:errors.append('Coverage-instrumented core cannot be shipped')
    if errors:raise ValueError('; '.join(errors))
    return {**linked,'path':str(path),'sha256':sha(path),'instrumented':False,'profilingSymbols':profiling}

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        while data:=stream.read(1024*1024):h.update(data)
    return h.hexdigest()

def includeTrackedReleaseMetadata(root:Path,files:dict)->None:
    """Retain exact tracked declarations; evidence and manifest carry build outcomes."""
    for name in ['BUILD-IDENTITY.json','RELEASE.json']:
        path=root/name
        if not path.is_file():raise FileNotFoundError(name)
        files[name]=path

def copyHandoffDocuments(root: Path, out: Path, prefix: str) -> list:
    """Export maintained guidance, retaining legacy bytes under a separate name."""
    root = Path(root)
    out = Path(out)
    current = root / 'HANDOFF.md'
    legacy = root / 'LLM-HANDOFF.md'
    primary = current if current.is_file() else legacy
    selections = []
    if primary.is_file():
        selections.append((primary, prefix + '-Handoff.md'))
    if legacy.is_file():
        selections.append((legacy, prefix + '-LLM-Handoff.md'))
    copied = []
    for source, name in selections:
        destination = out / name
        shutil.copyfile(source, destination)
        copied.append({'source': source.name, 'name': name, 'sha256': sha(destination)})
    return copied


def textSource(files,release):
    """Emit complete UTF-8 text payloads with a committed release identity."""
    sections=['# Nocturne '+release['build']+': full source contents\n\n',
              'Source commit: '+release['sourceCommit']+'\n\n',
              'Source baseline: '+release['sourceBaseline']+'\n\n',
              'Binary payloads remain complete in the SDK and are identified below by size and SHA-256.\n']
    for rel,path in sorted(files.items()):
        data=path.read_bytes()
        try:
            if b'\0' in data:raise UnicodeError('binary payload')
            content=data.decode('utf-8')
        except UnicodeError:
            sections.append('\n## '+rel+'\n\nBinary payload: '+str(len(data))+' bytes; SHA-256 '+sha(path)+'.\n')
            continue
        runs=re.findall('(?m)^[ \t]*('+chr(96)+'+)',content)
        fence=chr(96)*max(4,max(map(len,runs),default=0)+1)
        sections.extend(['\n## '+rel+'\n\n'+fence+'\n',content,'\n'+fence+'\n'])
    return ''.join(sections)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--capture',action='store_true');p.add_argument('--documentation-output',type=Path,help='validated current Markdown-derived PDF/HTML build');a=p.parse_args()
    release=loadReleaseIdentity(ROOT)
    prefix=release['artifactPrefix']
    out=a.output.resolve()
    if out.is_relative_to(ROOT):raise SystemExit('Output must be outside the source checkout')
    out.mkdir(parents=True,exist_ok=True)
    receipt=json.loads((ROOT/'native/evidence/BUILD-VERIFICATION.json').read_text())
    validateCompletedBuild(receipt,fingerprint()['sha256'],release['fullRC4Qualified'])
    contractPath=ROOT/'native/evidence/SDK-CONTRACT.json'
    contractRecord=json.loads(contractPath.read_text())
    validateSDKContract(contractRecord,release,receipt['sourceAfter'])
    validateSDKContractArtifacts(contractRecord,ROOT)
    validateShippingCore(ROOT/contractRecord['artifacts']['native']['path'])
    # Only generated evidence may be dirty. Source, lockfiles and scripts must be committed.
    changes=subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=ROOT,text=True).splitlines()
    if any(not name.startswith('native/evidence/') for name in changes):raise SystemExit('Uncommitted non-evidence source: '+repr(changes))
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    sourceBase=release['sourceBaseline']
    changed=subprocess.check_output(['git','diff','--name-only',sourceBase,'HEAD','--','native/src','native/include'],cwd=ROOT,text=True).splitlines()
    if not changed:raise SystemExit('No native implementation changes from the input baseline')
    if release.get('qualificationProfile')=='rc2':
        if a.documentation_output is None:raise SystemExit('RC2 requires --documentation-output')
        from rc2_package import packageRC2
        packageRC2(ROOT,out,release,receipt,contractPath,a.documentation_output);return
    reachable=subprocess.check_output(['git','rev-list','--objects','--all'],cwd=ROOT,text=True)
    if any(Path(line.split(' ',1)[1]).suffix.lower() in FONTS for line in reachable.splitlines() if ' ' in line):raise SystemExit('Font file exists in reachable history; cannot distribute this bundle')
    history=out/'history.bundle'
    if history.exists():history.unlink()
    subprocess.run(['git','bundle','create',str(history),'--all'],cwd=ROOT,check=True)
    files={}
    for rel in subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0'):
        if not rel:continue
        path=ROOT/rel;r=Path(rel)
        # Recovery snapshots are retained in Git/history, not repeated in the SDK payload.
        if len(r.parts)>1 and r.parts[0]=='evidence' and r.parts[1].startswith('reboot-'):continue
        if any(part in SKIP for part in r.parts) or path.suffix.lower() in FONTS:continue
        if rel in {'SOURCE-CONTENTS.md','SHA256SUMS.txt','MANIFEST.json','PACKAGE-MANIFEST.json'}:continue
        if path.is_symlink():raise SystemExit('Unexpected source symlink: '+rel)
        if path.is_file():files[rel]=path
    # Current generated artifacts are explicitly included; arbitrary untracked files are not.
    for rel in ['native/dist/libnocturne_native.so','native/dist/libnocturne_native.dylib','native/dist/nocturne_native.wasm','native/Nocturne-RC4-Source-Build.html']:
        path=ROOT/rel
        if path.is_file():files[rel]=path
    for path in (ROOT/'native/evidence').rglob('*'):
        if path.is_file() and not path.is_symlink() and not path.is_relative_to(ROOT/'native/evidence/capture'):
            if path.stat().st_size<16*1024**2:files[path.relative_to(ROOT).as_posix()]=path
    files['git/nocturne-rc4-contracts.bundle']=history
    files['SDK-CONTRACT.json']=contractPath
    files['Nocturne-RC4.html']=ROOT/'native/Nocturne-RC4-Source-Build.html'
    sourceDoc=out/(prefix+'-Full-Source.md');sourceDoc.write_text(textSource(files,release));files['NATIVE-SOURCE-CONTENTS.md']=sourceDoc
    buildInfo={'build':release['build'],'sourceCommit':head,'sourceBaseline':sourceBase,'nativeChanges':changed,'sourceFingerprint':receipt['sourceAfter'],'localBuildVerified':True,'fourRuntimeVerified':True,'fullRC4Qualified':release['fullRC4Qualified'],'scope':release['scope']}
    includeTrackedReleaseMetadata(ROOT,files)
    (out/'BUILD-IDENTITY.json').write_text(json.dumps(buildInfo,indent=2)+'\n')
    manifest={'build':release['build'],'sourceCommit':head,'sourceBaseline':sourceBase,'sourceFingerprint':receipt['sourceAfter'],'fullRC4Qualified':release['fullRC4Qualified'],'branch':subprocess.check_output(['git','symbolic-ref','--short','HEAD'],cwd=ROOT,text=True).strip(),'files':{rel:{'bytes':path.stat().st_size,'sha256':sha(path)} for rel,path in sorted(files.items())}}
    archive=out/(prefix+'-SDK.zip');temporary=archive.with_suffix('.zip.part')
    with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for rel,path in sorted(files.items()):
            i=zipfile.ZipInfo('nocturne-sdk/'+rel,(2026,9,30,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED
            i.external_attr=(0o100755 if os.access(path,os.X_OK) else 0o100644)<<16;z.writestr(i,path.read_bytes())
        i=zipfile.ZipInfo('nocturne-sdk/MANIFEST.json',(2026,9,30,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16
        z.writestr(i,json.dumps(manifest,indent=2)+'\n')
    verifyArchive(temporary);os.replace(temporary,archive)
    html=out/(prefix+'.html');shutil.copyfile(ROOT/'native/Nocturne-RC4-Source-Build.html',html)
    gallery=out/(prefix+'-Gallery.zip')
    with zipfile.ZipFile(gallery,'w',zipfile.ZIP_DEFLATED) as z:
        z.write(html,html.name);z.writestr('READ-FIRST.txt',release['build']+'\nOpen '+html.name+'. No installation needed. Native implementation and four language bindings were tested; the declared release scope remains authoritative.\n')
    for rel,name in [('README.md',prefix+'-README.md'),('native/evidence/BUILD-VERIFICATION.json',prefix+'-Verification.json'),('native/evidence/TEST-REPORT.md',prefix+'-Test-Report.md'),('native/docs/BUILD-SCOPE.md',prefix+'-Scope.md')]:
        if (ROOT/rel).is_file():shutil.copyfile(ROOT/rel,out/name)
    handoffDocuments=copyHandoffDocuments(ROOT,out,prefix)
    changePaths=sorted(ROOT.glob('CHANGELOG*.md'))
    if changePaths:(out/(prefix+'-Changes.md')).write_text('\n\n'.join('# '+path.name+'\n\n'+path.read_text() for path in changePaths)+'\n')
    for rel,name in [('docs/rc4-contracts4/ARCHIVE-SIZE-AUDIT.md','Nocturne-RC4-Archive-Size-Audit.md'),('docs/rc4-contracts4/ARCHIVE-COMPARISON.json','Nocturne-RC4-Archive-Comparison.json'),('native/docs/NOTIFICATIONS.md','Nocturne-RC4-Notification-Contract.md')]:
        shutil.copyfile(ROOT/rel,out/name)
    with zipfile.ZipFile(out/(prefix+'-Evidence.zip'),'w',zipfile.ZIP_DEFLATED) as z:
        for rel,path in sorted(files.items()):
            if rel.startswith('native/evidence/'):z.write(path,rel)
    if a.capture:
        cap=ROOT/'native/evidence/capture';capReceipt=json.loads((cap/'MANIFEST.json').read_text())
        with zipfile.ZipFile(out/(prefix+'-Capture.zip'),'w',zipfile.ZIP_DEFLATED,compresslevel=4) as z:
            for frame in capReceipt['frames']:
                for kind in ['png','cells']:
                    path=cap/frame[kind]
                    if sha(path)!=frame[kind+'Sha256']:raise RuntimeError('Capture hash mismatch')
                    z.write(path,'capture/'+path.name)
            z.write(cap/'MANIFEST.json','capture/MANIFEST.json')
            video=cap/'Nocturne-RC4-Source-Build.mp4'
            if sha(video)!=capReceipt['videoSha256']:raise RuntimeError('Capture video hash mismatch')
            z.write(video,'capture/Nocturne-RC4.mp4')
        shutil.copyfile(video,out/(prefix+'.mp4'))
    from delivery_integrity import exportPatch,closeDelivery,verifyDelivery
    exportPatch(ROOT,sourceBase,head,out)
    history.unlink() # bundled inside the one complete SDK
    result={**buildInfo,'sdk':{'name':archive.name,'bytes':archive.stat().st_size,'sha256':sha(archive),'manifestEntries':len(files)},'freshExtractionPassed':False,'handoffDocuments':handoffDocuments}
    (out/'PACKAGE-VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    for path in out.iterdir():
        if path.is_file():path.chmod(0o644)
    closeDelivery(out)
    verifyDelivery(out)
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
