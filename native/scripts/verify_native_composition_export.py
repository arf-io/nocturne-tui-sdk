#!/usr/bin/env python3
"""Recreate a native composition export without modifying its files."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

NATIVE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(NATIVE / 'examples'))
from composition_application import CompositionApplication

EXPECTED_FILES = {'MANIFEST.json', 'composition.json', 'scene.cells',
                  'scene.snapshot', 'scene-info.json'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify(directory, library):
    if {path.name for path in directory.iterdir()} != EXPECTED_FILES:
        raise ValueError('Unexpected export file set')
    files = {}
    for name in EXPECTED_FILES:
        path = directory / name
        if path.is_symlink() or not path.is_file():
            raise ValueError('Regular export files required')
        files[name] = path.read_bytes()
    manifest = json.loads(files['MANIFEST.json'])
    if manifest['schema'] != 'nocturne.native-composition-application.v1':
        raise ValueError('Unknown native export schema')
    if set(manifest['files']) != EXPECTED_FILES - {'MANIFEST.json'}:
        raise ValueError('Invalid manifest file set')
    for name, record in manifest['files'].items():
        if len(files[name]) != record['bytes'] or sha(files[name]) != record['sha256']:
            raise ValueError('File custody mismatch: ' + name)
    library_hash = sha(library.read_bytes())
    if library_hash != manifest['librarySha256']:
        raise ValueError('Requested native runtime differs from export')
    document = json.loads(files['composition.json'])
    with CompositionApplication(document, library=library, time_us=manifest['timeUs']) as application:
        scene = application.scene
        snapshot = scene.snapshot()
        frame = scene.render()
        if scene.snapshot() != snapshot:
            raise ValueError('Rendering changed recreated state')
        info = scene.info_complete()
    contract = info['contract']
    if (manifest['abiVersion'] != contract['abiVersion']
            or manifest['snapshotSchema'] != '0x' + format(contract['snapshotSchema'], 'x')):
        raise ValueError('Recreated ABI/schema differs')
    if (manifest['width'] != frame.width or manifest['height'] != frame.height
            or manifest['timeUs'] != info['clock']['timeUs']):
        raise ValueError('Recreated dimensions or clock differ')
    if snapshot != files['scene.snapshot']:
        raise ValueError('Recreated snapshot differs')
    if frame.bytes != files['scene.cells']:
        raise ValueError('Recreated frame differs')
    # Canonical JSON comparison retains boolean/number distinctions that Python
    # dictionary equality alone would lose (True compares equal to 1).
    expected_info = json.dumps(info, sort_keys=True, allow_nan=False)
    received_info = json.dumps(json.loads(files['scene-info.json']), sort_keys=True, allow_nan=False)
    if expected_info != received_info:
        raise ValueError('Recreated metadata differs')
    return {'passed': True, 'scope': 'Native composition reconstruction; not full SDK qualification',
            'librarySha256': library_hash, 'documentSha256': sha(files['composition.json']),
            'frameSha256': sha(frame.bytes), 'snapshotSha256': sha(snapshot)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--library', type=Path)
    arguments = parser.parse_args()
    library = arguments.library or NATIVE / 'dist' / (
        'libnocturne_native.dylib' if sys.platform == 'darwin' else 'libnocturne_native.so'
    )
    try:
        result = verify(arguments.directory.resolve(), library.resolve(strict=True))
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, RuntimeError, KeyError, TypeError) as error:
        print(json.dumps({'passed': False, 'error': str(error)}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
