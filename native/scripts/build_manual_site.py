"""Build a self-contained manual whose visible content is rendered by Nocturne WASM."""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import re
import posixpath
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    if a.output.exists():p.error('Output already exists')
    chapters=[]
    paths=sorted((ROOT/'docs/manual').glob('*.md'),key=lambda p:(p.name!='README.md',p.name))
    paths+=sorted(p for p in (ROOT/'docs').glob('*.md') if not p.name.startswith('TDD-'))
    for path in paths:
        identity=path.stem.lower() if path.parent.name=='manual' else 'reference-'+path.stem.lower()
        source=path.read_bytes().decode('utf-8');chapters.append({'id':identity,'sourcePath':str(path.relative_to(ROOT)),'title':source.splitlines()[0].lstrip('# '),
            'source':source,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    contents='# Manual contents\n\nCurrent application chapters and bundled reference documents. Dated references retain their original evidence scope.\n\n'
    for chapter in chapters:
        target=posixpath.relpath(chapter['sourcePath'],'docs/manual')
        contents+='- ['+chapter['title'].replace('[','').replace(']','')+']('+target+')\n'
    chapters.insert(1,{'id':'contents','sourcePath':'docs/manual/CONTENTS.md','title':'Manual contents','source':contents,'sha256':hashlib.sha256(contents.encode()).hexdigest()})
    wasm=(ROOT/'dist/nocturne_native.wasm').read_bytes();binding=(ROOT/'bindings/typescript/native_scene.mjs').read_text()
    data={'chapters':chapters,'wasmSha256':hashlib.sha256(wasm).hexdigest(),'bindingSha256':hashlib.sha256(binding.encode()).hexdigest()}
    html=(ROOT/'web/manual_site.html').read_text()
    for key,value in {'@@DATA@@':json.dumps(data,ensure_ascii=True).replace('<','\\u003c'),
        '@@WASM@@':base64.b64encode(wasm).decode(),'@@BINDING@@':binding.replace('export { NativeScene };','')}.items():
        if key not in html:raise ValueError('Missing site token '+key)
        html=html.replace(key,value)
    a.output.write_text(html);print(json.dumps({'output':str(a.output),'chapters':len(chapters),'wasmSha256':data['wasmSha256']}))
if __name__=='__main__':main()
