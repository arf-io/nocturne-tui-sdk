#!/usr/bin/env python3
"""Require fresh actual Unicode document PTYs for all four terminal hosts."""
import hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path
from cargo_example import buildExample
ROOT=Path(__file__).resolve().parents[1]
HOSTS=['standalone','prompt-toolkit','bubbletea','ratatui']
def main():
 evidence=ROOT/'evidence';evidence.mkdir(exist_ok=True);output=evidence/'unicode-document-hosts'
 if output.is_symlink():raise ValueError('Unicode document output cannot be a symlink')
 with tempfile.TemporaryDirectory(prefix='.unicode-document-',dir=evidence) as temporary:
  staging=Path(temporary);binary=staging/'bubbletea-bin'
  subprocess.run(['go','build','-o',str(binary),'.'],cwd=ROOT/'hosts/bubbletea',check=True)
  rust=buildExample(ROOT/'hosts/ratatui/Cargo.toml','unicode_document',staging/'ratatui-build.log')
  reports={}
  for host in HOSTS:
   destination=staging/host
   if host in ['standalone','prompt-toolkit']:
    command=[sys.executable,str(ROOT/'scripts/check_unicode_document.py'),'--host',host,'--output',str(destination)]
   else:
    command=[sys.executable,str(ROOT/'scripts/check_bubbletea_unicode.py'),'--host',host,'--binary',str(binary if host=='bubbletea' else rust),'--output',str(destination)]
   subprocess.run(command,cwd=ROOT,check=True)
   report=json.loads((destination/'RESULTS.json').read_text())
   if report.get('passed') is not True or report.get('host')!=host:raise ValueError('Unicode document host failed: '+host)
   required=['RESULTS.json','terminal.bin']+(['scroll-terminal.bin'] if host in ['standalone','prompt-toolkit'] else ['shift-navigation.bin','drag-selection.bin'])+(['modal-roundtrip.bin'] if host=='ratatui' else [])
   for name in required:
    if not (destination/name).is_file() or (destination/name).is_symlink():raise ValueError('Missing actual host output: '+host)
   for name,digest in report['sourceFiles'].items():
    if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:raise ValueError('Host source changed during qualification')
   reports[host]=report
  # No previous receipt is replaced before every host succeeds.
  output.mkdir(exist_ok=True)
  for host in HOSTS:
   dest=output/host
   if dest.is_symlink():raise ValueError('Host output cannot be a symlink')
  for host in HOSTS:
   dest=output/host;dest.mkdir(exist_ok=True)
   for artifact in (staging/host).iterdir():os.replace(artifact,dest/artifact.name)
  for name in ['ratatui-build.log','ratatui-build.json']:os.replace(staging/name,output/name)
  summary=staging/'summary.json';summary.write_text(json.dumps(dict(passed=True,scope='Actual Unicode document presentation and input in four controlling-terminal hosts',hosts=reports),indent=2)+'\n')
  os.replace(summary,output/'RESULTS.json')
 print('PASS: four actual Unicode document terminal hosts')
if __name__=='__main__':main()
