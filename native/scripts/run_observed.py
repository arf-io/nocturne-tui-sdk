#!/usr/bin/env python3
from pathlib import Path
import sys,subprocess,time,json
name=sys.argv[1];argv=sys.argv[2:];root=Path(__file__).resolve().parents[1];start=time.monotonic()
with (root/'evidence'/f'{name}.log').open('w') as log:
 try:r=subprocess.run(argv,cwd=root,stdout=log,stderr=subprocess.STDOUT,timeout=240);code=r.returncode;status='PASS' if code==0 else 'FAIL'
 except subprocess.TimeoutExpired:code=124;status='TIMEOUT'
(root/'evidence'/f'{name}.json').write_text(json.dumps({'command':argv,'exitCode':code,'status':status,'seconds':time.monotonic()-start},indent=2)+'\n')
sys.exit(code)
