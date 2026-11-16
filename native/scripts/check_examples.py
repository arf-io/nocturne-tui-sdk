#!/usr/bin/env python3
"""Execute shipped source examples and compare owned frame bytes; no generated mocks."""
from pathlib import Path
import subprocess,tempfile,hashlib,json,shutil,sys
from cargo_example import buildExample
ROOT=Path(__file__).resolve().parents[1]
results=[]
with tempfile.TemporaryDirectory(prefix='nocturne-examples-')as tmp:
 tmp=Path(tmp)
 commands={'python':[sys.executable,str(ROOT/'examples/snapshot.py')],'typescript':['node',str(ROOT/'examples/snapshot.mjs')]}
 subprocess.run(['go','build','-o',str(ROOT/'dist/go-snapshot'),'./cmd/snapshot'],cwd=ROOT/'bindings/go',check=True)
 commands['go']=[str(ROOT/'dist/go-snapshot')]
 if shutil.which('cargo'):
  executable=buildExample(ROOT/'bindings/rust/Cargo.toml','snapshot',ROOT/'evidence/rust-example-build.log')
  commands['rust']=[str(executable)]
 for name,argv in commands.items():
  run=tmp/name;run.mkdir();r=subprocess.run(argv,cwd=run,capture_output=True,text=True,timeout=30);data=(run/'preview.cells').read_bytes()if r.returncode==0 else b''
  results.append({'language':name,'exitCode':r.returncode,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'stderr':r.stderr})
 passed=all(r['exitCode']==0 for r in results) and len({r['sha256']for r in results})==1
 report={'scope':'Executed source examples through direct C/WASM, matching output bytes. Rust only included when its compiler ran.','results':results,'passed':passed,'rustExecuted':'rust'in commands}
 (ROOT/'evidence/examples.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
 if not passed:raise SystemExit(2)
