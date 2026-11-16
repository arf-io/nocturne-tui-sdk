#!/usr/bin/env python3
"""Close a completed RC2 runtime plan with measured coverage and shipping replay."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
LANGUAGES=('python','typescript','go','rust')
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def replayBinding(evidence):
 result={}
 for language in LANGUAGES:
  path=Path(evidence)/('parity-'+language+'.jsonl');data=path.read_bytes();rows=[json.loads(line)for line in data.splitlines()]
  if not rows or any(row.get('index')!=index or not {'frame','state','metadata','motions'}.issubset(row)for index,row in enumerate(rows)):raise ValueError('Incomplete replay records: '+language)
  result[language]={'sha256':hashlib.sha256(data).hexdigest(),'records':len(rows)}
 return result

def requireSameReplay(measured,shipping):
 for language in LANGUAGES:
  if measured.get(language)!=shipping.get(language):raise ValueError('Shipping replay differs from measured '+language)

def main():
 from qualify import fingerprint
 from release_identity import validateCompletedBuild
 from delivery_runner import atomicJson
 from sdk_contract import captureSDKArtifacts
 from package_contracts import validateShippingCore
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--profiles',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve()
 if out.is_relative_to(ROOT.parent)or out.exists():p.error('Use a new external output directory')
 out.mkdir(parents=True);receiptPath=ROOT/'evidence/BUILD-VERIFICATION.json';receipt=json.loads(receiptPath.read_text());source=fingerprint()['sha256'];validateCompletedBuild(receipt,source)
 if receipt.get('qualificationProfile')!='rc2'or receipt.get('runtimePlanQualified')is not True:raise ValueError('Completed RC2 runtime profile required')
 parity=json.loads((ROOT/'evidence/parity.json').read_text())
 if parity.get('fourRuntimePassed')is not True or parity.get('profile')!='rc2':raise ValueError('Actual four-runtime RC2 replay required')
 measured=replayBinding(ROOT/'evidence');measuredArtifacts=captureSDKArtifacts(ROOT.parent);started=time.monotonic();steps=[]
 def run(name,argv,env=None,cwd=ROOT):
  before=time.monotonic();log=out/(name+'.log')
  with log.open('wb')as stream:result=subprocess.run(argv,cwd=cwd,env=env,stdout=stream,stderr=subprocess.STDOUT)
  steps.append({'id':name,'argv':list(map(str,argv)),'exitCode':result.returncode,'seconds':round(time.monotonic()-before,3),'log':log.name,'logSha256':digest(log)})
  atomicJson(out/'STEPS.json',steps)
  if result.returncode:raise RuntimeError(name+' failed; see '+str(log))
 run('coverage',[sys.executable,str(ROOT.parent/'tools/ci/coverage_gate.py'),'--profiles',str(a.profiles.resolve()),'--output',str(out/'coverage')],cwd=ROOT.parent)
 coverage=json.loads((out/'coverage/RESULTS.json').read_text());coverage.update(sourceFingerprint=source,measuredArtifacts=measuredArtifacts,reportSha256=digest(out/'coverage/coverage.json'))
 env=dict(os.environ);env['NOCTURNE_COVERAGE']='0';env.pop('LLVM_PROFILE_FILE',None)
 run('shipping-build',[sys.executable,'scripts/build.py'],env=env)
 native=ROOT/'dist'/('libnocturne_native.dylib'if sys.platform=='darwin'else 'libnocturne_native.so');inspection=validateShippingCore(native)
 run('shipping-parity',[sys.executable,'scripts/parity.py','--require-rust','--profile','rc2'],env=env)
 shipping=replayBinding(ROOT/'evidence');requireSameReplay(measured,shipping);shippingParity=json.loads((ROOT/'evidence/parity.json').read_text())
 if shippingParity.get('fourRuntimePassed')is not True or shippingParity.get('planSha256')!=parity['planSha256']:raise ValueError('Shipping replay plan changed or failed')
 run('shipping-contract',[sys.executable,'scripts/capture_sdk_contract.py','--output','evidence/SDK-CONTRACT.json'],env=env)
 if fingerprint()['sha256']!=source:raise ValueError('Source changed while closing shipping verification')
 shippingRecord={'passed':True,'sourceFingerprint':source,'fourRuntimePassed':True,'measuredReplayEqual':True,'planSha256':parity['planSha256'],'measuredReplay':measured,'shippingReplay':shipping,'artifacts':captureSDKArtifacts(ROOT.parent),'nativeInspection':inspection,'seconds':round(time.monotonic()-started,3),'steps':steps}
 receipt.update(coverage=coverage,shippingModeVerification=shippingRecord,remainingReleaseGates=['Extracted SDK build and runtime verification'])
 from rc2_package import validateRC2Receipt,validateGalleryArtifact
 validateGalleryArtifact(ROOT/'Nocturne-RC4-Source-Build.html',receipt.get('gallery'),ROOT/'dist/nocturne_native.wasm')
 validateRC2Receipt(receipt,source);atomicJson(receiptPath,receipt);atomicJson(out/'BUILD-VERIFICATION.json',receipt)
 print(json.dumps({'coverage':coverage['nativeLinePercent'],'shippingReplayEqual':True,'seconds':shippingRecord['seconds']}))
if __name__=='__main__':main()
