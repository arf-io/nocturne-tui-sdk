#!/usr/bin/env python3
"""Extract, rebuild and execute the actual RC2 SDK in a fresh directory."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,sys,time
from release_archive import verifyArchive,extractVerified

def extraction_environment(base):
 """Environment for the extracted SDK's checks: uninstrumented, and the TypeScript module bound
 the way qualify.py binds it, so generated-application tests never fall back to a checkout layout."""
 env=dict(base);env['NOCTURNE_COVERAGE']='0';env['PYTHONDONTWRITEBYTECODE']='1';env.pop('LLVM_PROFILE_FILE',None)
 if not env.get('NOCTURNE_TYPESCRIPT_MODULE'):
  tsc=shutil.which('tsc',path=env.get('PATH'))
  if tsc:env['NOCTURNE_TYPESCRIPT_MODULE']=str(Path(tsc).resolve().parent.parent/'lib/typescript.js')
 return env

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--discard-build',action='store_true');a=p.parse_args()
 archive=a.archive.resolve();out=a.output.resolve();manifest=verifyArchive(archive)
 if manifest.get('qualificationProfile')!='rc2':raise ValueError('RC2 qualification profile required')
 if out.exists():raise FileExistsError(out)
 out.mkdir(parents=True);sdk=extractVerified(archive,out/'extracted');native=sdk/'native';steps=[];started=time.monotonic();env=extraction_environment(os.environ)
 def run(name,argv,cwd=native):
  log=out/(name+'.log');at=time.monotonic()
  with log.open('wb')as stream:r=subprocess.run(argv,cwd=cwd,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=900)
  steps.append({'id':name,'argv':list(map(str,argv)),'exitCode':r.returncode,'seconds':round(time.monotonic()-at,3),'log':log.name,'logSha256':hashlib.sha256(log.read_bytes()).hexdigest()});(out/'STEPS.json').write_text(json.dumps(steps,indent=2)+'\n')
  if r.returncode:raise RuntimeError(name+' failed; see '+str(log))
  return log
 probe="""import sys,json,hashlib;sys.path.insert(0,'bindings/python');from nocturne_native import NativeScene
with NativeScene(9616)as s:
 for c in [{'op':'resize','width':100,'height':36},{'op':'environment','stars':0},{'op':'prompt-appearance','cursor':{'shape':'custom','glyph':'◆','blinkMs':0},'weather':{'style':'nova'}},{'op':'draft','text':'文é 🪷','emitWeather':True},{'op':'time','timeUs':150000}]:s.command(c)
 print(json.dumps({'contract':s.info()['contract'],'frame':hashlib.sha256(s.render().bytes).hexdigest(),'snapshot':hashlib.sha256(s.snapshot()).hexdigest()},sort_keys=True))
"""
 before=run('shipping-probe',[sys.executable,'-c',probe]).read_text()
 run('rebuild',[sys.executable,'scripts/build.py'])
 after=run('rebuilt-probe',[sys.executable,'-c',probe]).read_text()
 if before!=after:raise ValueError('Extracted source rebuild differs from shipping runtime')
 gallery=out/'rebuilt-gallery.html';run('gallery-rebuild',[sys.executable,'scripts/build_gallery.py','--output',str(gallery)])
 run('four-runtime-replay',[sys.executable,'scripts/parity.py','--require-rust','--profile','rc2'])
 parity=json.loads((native/'evidence/parity.json').read_text())
 if parity.get('fourRuntimePassed')is not True:raise ValueError('Extracted SDK four-runtime replay failed')
 run('generated-applications',['node','--test','bindings/typescript/composition-project.test.mjs','bindings/typescript/composition-codegen.test.mjs','bindings/typescript/composition-presets.test.mjs'])
 env['NOCTURNE_COMPOSITION_GALLERY']=str(gallery)
 run('browser-compositor',[sys.executable,'-m','unittest','tests.test_composition_gallery','-v'])
 report={'schema':'nocturne.rc2-extracted-sdk.v1','passed':True,'archive':str(archive),'archiveSha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'build':manifest['build'],'sourceCommit':manifest['sourceCommit'],'sourceFingerprint':manifest['sourceFingerprint'],'sourceRebuildEqual':True,'fourRuntimePassed':True,'replayCommands':parity['commands'],'steps':steps,'seconds':round(time.monotonic()-started,3),'workingDirectoryRemoved':a.discard_build}
 (out/'RESULTS.json').write_text(json.dumps(report,indent=2)+'\n')
 if a.discard_build:shutil.rmtree(out/'extracted');gallery.unlink()
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
