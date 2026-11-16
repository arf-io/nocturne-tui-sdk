"""Independently verify each emitted SDK archive; absence is failure."""
from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parents[2]
archives=list(Path(sys.argv[1]).glob('*SDK.zip'))
if not archives:raise SystemExit('SDK archive absent')
for index,archive in enumerate(archives):
 subprocess.run([sys.executable,str(root/'native/scripts/verify_contracts_package.py'),str(archive),'--destination',str(Path(sys.argv[2])/str(index)),'--report-dir',str(Path(sys.argv[3])/str(index)),'--timeout','86400','--step-timeout','7200'],check=True)
