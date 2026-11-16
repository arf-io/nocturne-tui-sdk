#!/usr/bin/env python3
"""Run the real document CLI gate with fresh artifacts, publishing only success."""
import json,os
from pathlib import Path
import subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[1]
def main():
 evidence=ROOT/'evidence';evidence.mkdir(exist_ok=True);output=evidence/'document-persistence'
 if output.is_symlink():raise ValueError('Document gate artifact directory cannot be a symlink')
 with tempfile.TemporaryDirectory(prefix='.document-persistence-',dir=evidence) as temporary:
  expected=['roundtrip-pty.bin','rejected-pty.bin','saved-document.json','scene-switch-pty.bin','empty-scene-switch-pty.bin','scene-undo-pty.bin','RESULTS.json']
  completed=[]
  for host in ['prompt-toolkit','standalone']:
   fresh=Path(temporary)/host
   subprocess.run([sys.executable,str(ROOT/'scripts/check_document_host.py'),'--host',host,'--output',str(fresh)],check=True,cwd=ROOT)
   report=json.loads((fresh/'RESULTS.json').read_text())
   if report.get('passed') is not True or report.get('host')!=host:raise ValueError('Document CLI qualification failed')
   for name in expected:
    if not (fresh/name).is_file() or (fresh/name).is_symlink():raise ValueError('Missing document gate artifact')
   completed.append((host,fresh,report))
  # Validate both hosts before replacing any previous published artifact.
  output.mkdir(exist_ok=True)
  standalone=output/'standalone'
  if standalone.is_symlink():raise ValueError('Standalone artifact directory cannot be a symlink')
  standalone.mkdir(exist_ok=True)
  for host,fresh,report in completed:
   destination=output if host=='prompt-toolkit' else standalone
   for name in expected:
    if name!='RESULTS.json':os.replace(fresh/name,destination/name)
   if host=='standalone':os.replace(fresh/'RESULTS.json',standalone/'RESULTS.json')
  report=completed[0][2]
  report['standalone']=completed[1][2]
  report['scope']='Actual prompt_toolkit and standalone document CLI roundtrips and rejected imports in controlling PTYs'
  summary=Path(temporary)/'summary.json';summary.write_text(json.dumps(report,indent=2)+'\n')
  os.replace(summary,output/'RESULTS.json')
 print('PASS: both real controlling-terminal document CLI persistence hosts')
if __name__=='__main__':main()
