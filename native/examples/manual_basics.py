#!/usr/bin/env python3
"""Execute the manual's context, render, rejection and recovery walkthrough."""
from pathlib import Path
import argparse
import hashlib
import json
import sys

NATIVE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(NATIVE/'bindings/python'))
from nocturne_native import NativeScene

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library',type=Path)
    args=parser.parse_args()
    library=args.library or NATIVE/'dist'/('libnocturne_native.dylib' if sys.platform=='darwin' else 'libnocturne_native.so')
    library=library.resolve(strict=True)
    with NativeScene(seed=2030,library=library) as scene:
        scene.command({'op':'input','text':'Hello, Nocturne'})
        saved=scene.snapshot()
        frame=scene.render()
        renderPure=scene.snapshot()==saved
        rejected=False
        try:scene.command({'op':'manual-unknown-command'})
        except ValueError:rejected=True
        rejectionPreservedState=rejected and scene.snapshot()==saved
        scene.command({'op':'input','text':'A changed document'})
        scene.restore(saved)
        restored=scene.render()
        document=scene.info()['prompt']['text']
        record={'document':document,'width':frame.width,'height':frame.height,
                'frameBytes':len(frame.bytes),'snapshotBytes':len(saved),
                'renderPure':renderPure,'rejectionPreservedState':rejectionPreservedState,
                'restorePreservedFrame':restored.bytes==frame.bytes,
                'librarySha256':hashlib.sha256(library.read_bytes()).hexdigest()}
        if not all(record[key] for key in ('renderPure','rejectionPreservedState','restorePreservedFrame')):
            raise RuntimeError('Manual walkthrough invariant failed')
        print(json.dumps(record,indent=2))

if __name__=='__main__':main()
