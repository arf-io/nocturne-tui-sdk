#!/usr/bin/env python3
"""Independently verify, extract, rebuild and strictly qualify the delivered SDK.

Uses real child completion, not polling a prior receipt. The result is written on
success or failure. A complete four-runtime pass and matching rebuilt artifacts
are mandatory. No packages or compilers are installed by verification.
"""
from pathlib import Path
import argparse,hashlib,json,math,os,subprocess,sys
from delivery_runner import RunJournal,atomicJson
from release_archive import verifyArchive,extractVerified
from delivery_integrity import verifyDelivery,verifyPatch
from sdk_contract import validateSDKContract,compareSDKContracts,validateSDKContractArtifacts
from release_identity import validateCompletedBuild

def extractedQualificationStatus(build, fingerprint, declaredFullQualification):
    """Validate executed receipt identity before propagating a release claim."""
    validateCompletedBuild(build, fingerprint, declaredFullQualification)
    return declaredFullQualification and build.get('fullRC4Qualified') is True

def verificationCommands(python, evidence, stepTimeoutSeconds):
    """Keep the extracted qualifier's step budget separate from child lifetime."""
    if not math.isfinite(stepTimeoutSeconds) or stepTimeoutSeconds <= 0:
        raise ValueError('Qualification step timeout must be positive and finite')
    return [
        ('extracted-build', ['sh', 'build-native.sh']),
        ('extracted-strict-qualification', [
            python, 'native/scripts/qualify.py', '--strict',
            '--evidence-dir', str(evidence),
            '--step-timeout', str(stepTimeoutSeconds),
        ]),
    ]

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        while block:=f.read(1024*1024):h.update(block)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('archive',type=Path);p.add_argument('--destination',type=Path,required=True)
    p.add_argument('--report-dir',type=Path,required=True);p.add_argument('--rust-bin',type=Path)
    p.add_argument('--timeout',type=float,default=1800,help='Maximum seconds for each build or qualification child')
    p.add_argument('--step-timeout',type=float,default=900,help='Seconds allowed for each extracted qualification step; a step with a longer declared floor (fingerprint-stability, 1800) keeps it')
    args=p.parse_args()
    if any(not math.isfinite(value) or value <= 0 for value in [args.timeout,args.step_timeout]):
        p.error('Child and step timeouts must be positive and finite')
    archive=args.archive.resolve();dest=args.destination.resolve();out=args.report_dir.resolve()
    if dest.exists():p.error('Destination must not exist')
    if out.is_relative_to(dest):p.error('Keep extraction evidence outside the extracted source')
    env=dict(os.environ)
    if args.rust_bin:env['PATH']=str(args.rust_bin.resolve())+os.pathsep+env.get('PATH','')
    env['CARGO_NET_OFFLINE']='true';env['CARGO_TERM_COLOR']='never'
    result={'schema':'nocturne.rc4.package-verification.v3','archive':archive.name,'archiveSha256':sha(archive),'passed':False,'fullRC4Qualified':False}
    with RunJournal(out) as run:
        try:
            result['deliveryIntegrity']=verifyDelivery(archive.parent)
            manifest=verifyArchive(archive);root=extractVerified(archive,dest)
            result['manifestEntries']=len(manifest['files']);result['manifestPassed']=True
            release=json.loads((root/'RELEASE.json').read_text())
            packagedContract=json.loads((root/'SDK-CONTRACT.json').read_text())
            validateSDKContract(packagedContract,release,manifest['sourceFingerprint'])
            validateSDKContractArtifacts(packagedContract,root)
            result['packagedRuntimeContractValid']=True
            # Validate the SAME restoration path used by private publication before
            # tests intentionally regenerate evidence. No working file is overwritten.
            sys.path.insert(0,str(root/'tools/release'))
            from publish_github import restoreHistory,publicationRefs
            restoreHistory(root)
            dirty=subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=root,text=True)
            if dirty.strip():raise RuntimeError('Restored SDK differs from tracked source: '+dirty)
            refs=publicationRefs(root)
            patchRecord=json.loads((archive.parent/'PATCH.json').read_text())
            if patchRecord['baseline']!=manifest['sourceBaseline'] or patchRecord['head']!=manifest['sourceCommit']:
                raise ValueError('Patch identity differs from SDK manifest')
            result['patchReapplication']=verifyPatch(root,patchRecord,archive.parent,dest/'patch-reapplied')
            result['publicationHistoryRestored']=True
            result['trackedSourceCleanBeforeBuild']=True
            result['publicationRefCount']=len(refs)
            result['archiveRefCount']=sum(ref.startswith('refs/tags/nocturne-archive/') for ref in refs)
            files=['native/dist/nocturne_native.wasm','native/Nocturne-RC4-Source-Build.html','Nocturne-RC4.html']
            # The distributed native binary is Linux x86-64. Cross-platform rebuilds
            # may be valid but are not promised byte-identical to a Linux shared library.
            library=root/'native/dist'/('libnocturne_native.dylib' if sys.platform=='darwin' else 'libnocturne_native.so')
            if library.is_file():files.append(library.relative_to(root).as_posix())
            before={rel:sha(root/rel) for rel in files}
            for label,argv in verificationCommands(sys.executable,out/'qualification',args.step_timeout):
                check=run.runStep(label,argv,root,timeoutSeconds=args.timeout,env=env)
                if check['status']!='PASS':raise RuntimeError(label+' did not pass')
            result['comparisons']={rel:{'before':before[rel],'after':sha(root/rel),'identical':before[rel]==sha(root/rel)} for rel in files}
            if not all(item['identical'] for item in result['comparisons'].values()):raise RuntimeError('Rebuilt artifacts differ')
            headDir=dest/'restored-history';bundle=root/'git/nocturne-rc4-contracts.bundle'
            check=run.runStep('extracted-history-clone',['git','clone',str(bundle),str(headDir)],root,timeoutSeconds=args.timeout,env=env)
            if check['status']!='PASS':raise RuntimeError('Cannot restore delivered Git bundle')
            head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=headDir,text=True).strip()
            if head!=manifest['sourceCommit']:raise RuntimeError('Restored Git HEAD does not match manifest')
            check=run.runStep('extracted-history-fsck',['git','fsck','--full'],headDir,timeoutSeconds=args.timeout,env=env)
            if check['status']!='PASS':raise RuntimeError('Git history failed integrity checking')
            result['sourceCommit']=head
            build=json.loads((root/'native/evidence/BUILD-VERIFICATION.json').read_text())
            result['fourRuntimeVerified']=bool(build.get('fourRuntimeVerified'));result['qualification']=build
            if not result['fourRuntimeVerified']:raise RuntimeError('Extracted four-runtime result is not true')
            rebuiltContract=json.loads((root/'native/evidence/SDK-CONTRACT.json').read_text())
            validateSDKContractArtifacts(rebuiltContract,root)
            result['runtimeContract']=compareSDKContracts(packagedContract,rebuiltContract,release,build['sourceAfter'])
            if build['sourceAfter']!=manifest['sourceFingerprint']:raise RuntimeError('Rebuilt source differs from SDK contract source')
            result['runtimeContractMatched']=True
            result['fullRC4Qualified']=extractedQualificationStatus(build,manifest['sourceFingerprint'],release['fullRC4Qualified'])
            result['passed']=True;run.finish(True,manifestEntries=result['manifestEntries'],sourceCommit=head,fourRuntimeVerified=True,fullRC4Qualified=result['fullRC4Qualified'])
        except Exception as error:
            result['exception']=str(error);run.finish(False,reason=str(error))
        finally:
            result['commands']=run.record['commands'];atomicJson(out/'EXTRACTED-VERIFICATION.json',result)
    print(json.dumps({k:result.get(k) for k in ['passed','manifestEntries','sourceCommit','fourRuntimeVerified','fullRC4Qualified','exception']},indent=2))
    return 0 if result['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
