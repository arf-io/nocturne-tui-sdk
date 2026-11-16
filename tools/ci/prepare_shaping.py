"""Provision hash-bound external fixtures outside the checkout."""
import hashlib,json,sys,tarfile,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parents[2]
output=Path(sys.argv[1]).resolve();output.mkdir(parents=True,exist_ok=True)
if output.is_relative_to(root):raise SystemExit('Fixtures must remain outside checkout')
receipt=json.loads((root/'native/evidence/shaping-preparation-20261010/PREPARATION.json').read_text())
for item in receipt['artifacts']:
 target=output/item['name']
 with urllib.request.urlopen(item['url'],timeout=120) as response:target.write_bytes(response.read())
 if hashlib.sha256(target.read_bytes()).hexdigest()!=item['sha256'] or target.stat().st_size!=item['bytes']:raise SystemExit('Fixture digest mismatch: '+item['name'])
 with tarfile.open(target) as archive:archive.extractall(output,filter='data')
