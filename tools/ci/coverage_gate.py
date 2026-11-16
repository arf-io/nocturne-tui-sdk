"""Measure native production coverage; enforce floor and tracked ratchet."""
import argparse,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--profiles',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[2];a.output.mkdir(parents=True,exist_ok=True)
profiles=sorted(a.profiles.glob('*.profraw'))
if not profiles:raise SystemExit('No executed native profiles; coverage cannot pass')
merged=a.output/'core.profdata'
subprocess.run(['llvm-profdata','merge','-sparse',*[str(x) for x in profiles],'-o',str(merged)],check=True)
lib=root/'native/dist/libnocturne_native.so'
if not lib.exists():lib=root/'native/dist/libnocturne_native.dylib'
export=subprocess.check_output(['llvm-cov','export',str(lib),'-instr-profile='+str(merged)],text=True)
(a.output/'coverage.json').write_text(export)
files=[f for data in json.loads(export)['data'] for f in data['files'] if Path(f['filename']).resolve().is_relative_to(root/'native/src')]
count=sum(f['summary']['lines']['count'] for f in files);covered=sum(f['summary']['lines']['covered'] for f in files)
if not count:raise SystemExit('Production coverage denominator is empty')
policy=json.loads((root/'tools/ci/coverage-ratchet.json').read_text());threshold=max(70,policy['nativeLinePercent'])
# A PR cannot lower the policy already committed on either protected branch.
for branch in ['main','integration']:
 result=subprocess.run(['git','show',f'origin/{branch}:tools/ci/coverage-ratchet.json'],capture_output=True,text=True,cwd=root)
 if result.returncode==0:threshold=max(threshold,json.loads(result.stdout)['nativeLinePercent'])
percent=100*covered/count
report={'coveredLines':covered,'totalLines':count,'nativeLinePercent':percent,'requiredPercent':threshold,'passed':percent>=threshold,'files':len(files)}
(a.output/'RESULTS.json').write_text(json.dumps(report,indent=2)+'\n')
(a.output/'coverage-ratchet.next.json').write_text(json.dumps({'nativeLinePercent':max(threshold,percent)},indent=2)+'\n')
print(json.dumps(report,indent=2))
if percent<threshold:raise SystemExit('Native coverage below ratcheted floor')
