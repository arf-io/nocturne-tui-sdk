"""Execute all retained root Python and npm test entry points, retaining failures."""
import json,subprocess,sys
from pathlib import Path
repository=Path(__file__).resolve().parents[2];output=Path(sys.argv[1]).resolve();output.mkdir(parents=True,exist_ok=True)
if (output/'RESULTS.json').exists():raise SystemExit('Use a fresh historical evidence directory')
sourceCommit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repository,text=True).strip()
# Reference builds rewrite tracked legacy binaries. Execute in a detached
# checkout so they cannot dirty the qualified SDK source or its package inputs.
root=output.parent/('reference-checkout-'+output.name)
with (output/'reference-checkout.log').open('wb') as log:
 subprocess.run(['git','worktree','add','--detach',str(root),sourceCommit],cwd=repository,stdout=log,stderr=subprocess.STDOUT,check=True)
# Retained engines are reference implementations; rebuild their own inputs.
# This does not dispatch current native APIs to the historical JavaScript core.
plan=[('reference-native-wasm-build',['sh','scripts/build.sh','--wasm']),
      ('reference-typescript-build',['tsc','-p','tsconfig.json']),
      ('reference-continuity-build',['tsc','-p','tsconfig.continuity.json']),
      ('python-root',[sys.executable,'-m','unittest','discover','-s','tests','-v'])]
for folder in sorted({path.parent for path in (root/'tests').rglob('test*.py')}):
 if folder!=root/'tests':plan.append(('python-'+folder.relative_to(root).as_posix().replace('/','-'),[sys.executable,'-m','unittest','discover','-s',str(folder),'-v']))
for name in json.loads((root/'package.json').read_text())['scripts']:
 if name=='test' or name.startswith('test:'):plan.append((name,['npm','run',name]))
rows=[]
for name,argv in plan:
 with (output/(name.replace(':','-')+'.log')).open('wb') as log:
  try:code=subprocess.run(argv,cwd=root,stdout=log,stderr=subprocess.STDOUT,timeout=1800).returncode
  except subprocess.TimeoutExpired:code=124
 rows.append({'suite':name,'argv':argv,'exitCode':code})
 (output/'RESULTS.json').write_text(json.dumps({'sourceCommit':sourceCommit,'referenceCheckout':str(root),'complete':len(rows)==len(plan),'passed':len(rows)==len(plan) and all(row['exitCode']==0 for row in rows),'suites':rows},indent=2)+'\n')
if any(row['exitCode'] for row in rows):raise SystemExit(1)
