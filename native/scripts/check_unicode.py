#!/usr/bin/env python3
"""Execute the independent four-binding Unicode oracle and retain gate artifacts.

The underlying runner always receives a new directory. The standard qualification
artifact paths retain the latest executed outputs; immutable case checkpoints and
the execution journal preserve their source binding and success/failure status.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]

def main():
    evidence=ROOT/'evidence'
    evidence.mkdir(exist_ok=True)
    output=evidence/'unicode-conformance'
    if output.is_symlink():
        raise ValueError('Unicode gate artifact directory cannot be a symlink')
    with tempfile.TemporaryDirectory(prefix='.unicode-conformance-',dir=evidence) as temporary:
        fresh=Path(temporary)/'run'
        subprocess.run([sys.executable,str(ROOT/'scripts/qualify_grapheme.py'),
                        '--output',str(fresh)],check=True,cwd=ROOT)
        report=json.loads((fresh/'RESULTS.json').read_text())
        if not report['passed'] or report['mismatches'] or set(report['results'])!={'python','typescript','go','rust'}:
            raise ValueError('Incomplete four-runtime Unicode qualification')
        for script,name in [('check_bidi_characters.py','bidi-characters.json'),
                            ('check_bidi_classes.py','bidi-classes.json')]:
            subprocess.run([sys.executable,str(ROOT/'scripts'/script),'--output',str(fresh/name)],check=True,cwd=ROOT)
            if not json.loads((fresh/name).read_text())['passed']:
                raise ValueError('Incomplete native bidi conformance')
        subprocess.run([os.environ.get('NODE','node'),str(ROOT/'scripts/check_bidi_wasm.mjs'),
                        str(fresh/'bidi-wasm.json')],check=True,cwd=ROOT)
        if not json.loads((fresh/'bidi-wasm.json').read_text())['passed']:
            raise ValueError('Incomplete WASM bidi conformance')
        output.mkdir(exist_ok=True)
        # Publish the summary last. A failed runner never replaces the previous
        # artifacts and its enclosing journal remains nonpassing.
        files=sorted(p for p in fresh.iterdir() if p.name!='RESULTS.json')
        for path in [*files,fresh/'RESULTS.json']:
            if not path.is_file() or path.is_symlink():
                raise ValueError('Unexpected Unicode gate artifact')
            os.replace(path,output/path.name)
    print('PASS: independent Unicode segmentation/width oracle through all four bindings')

if __name__=='__main__':
    main()
