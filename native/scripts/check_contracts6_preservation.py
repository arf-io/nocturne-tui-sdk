#!/usr/bin/env python3
"""Compare the original Contracts 6 scenes with the current native core.

Arguments: the exact supplied Contracts 6 ZIP. The whole input SHA and selected
library/recipe manifest hashes are checked before loading its trusted library.
Output: native/evidence/BASELINE-FRAME-COMPARISON.json. Exit nonzero for mismatch.
This is baseline regression evidence, not approval of every historical animation.
Example: python3 native/scripts/check_contracts6_preservation.py /path/to/Contracts6-SDK.zip
"""
from pathlib import Path
import argparse, hashlib, json, sys, tempfile, zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
BASELINE_SHA='ad92eb123708391cca6ab4e1bc296a417e312927a36ed9b3d3a9c8d468be73f8'

def fileHash(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline',type=Path);args=parser.parse_args()
    if fileHash(args.baseline)!=BASELINE_SHA:parser.error('Not the exact supplied Contracts 6 archive')
    records=[]
    with tempfile.TemporaryDirectory(prefix='nocturne-contracts6-') as temporary:
        library=Path(temporary)/'libcontracts6.so'
        with zipfile.ZipFile(args.baseline) as archive:
            manifest=json.loads(archive.read('nocturne-sdk/MANIFEST.json'))
            selected={}
            for relative in ['native/dist/libnocturne_native.so','native/recipes.json']:
                content=archive.read('nocturne-sdk/'+relative);entry=manifest['files'][relative]
                if len(content)!=entry['bytes'] or hashlib.sha256(content).hexdigest()!=entry['sha256']:raise ValueError('Baseline member hash mismatch: '+relative)
                selected[relative]=content
            library.write_bytes(selected['native/dist/libnocturne_native.so'])
            recipes=json.loads(selected['native/recipes.json'])
        for recipe in recipes:
            with NativeScene(2030,library=library) as before, NativeScene(2030) as after:
                for scene in (before,after):
                    scene.command({'op':'resize','width':160,'height':48})
                    for command in recipe['commands']:scene.command(command)
                for timeUs in [0,900000,2300000]:
                    before.advance_to(timeUs);after.advance_to(timeUs)
                    old=before.render().bytes;new=after.render().bytes
                    record={'scene':recipe['id'],'timeUs':timeUs,'baselineCells':hashlib.sha256(old).hexdigest(),'currentCells':hashlib.sha256(new).hexdigest(),'cellsIdentical':old==new,'particlesIdentical':before.particles()==after.particles()}
                    records.append(record)
            print(recipe['id'],all(r['cellsIdentical'] and r['particlesIdentical'] for r in records if r['scene']==recipe['id']),flush=True)
    result={'scope':'Twenty unchanged Contracts 6 native recipes, fixed seed 2030 and 160x48 cells, three explicit timestamps each. No selector rules. No snapshot-schema equality or entire historical optical approval inferred.','baselineSha256':BASELINE_SHA,'currentLibrarySha256':fileHash(ROOT/'dist/libnocturne_native.so'),'checks':records,'passed':all(r['cellsIdentical'] and r['particlesIdentical'] for r in records)}
    (ROOT/'evidence/BASELINE-FRAME-COMPARISON.json').write_text(json.dumps(result,indent=2)+'\n')
    print('matched frames',len(records),'PASS' if result['passed'] else 'FAIL')
    return 0 if result['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
