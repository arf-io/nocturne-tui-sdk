#!/usr/bin/env python3
"""Load a workshop composition through the native SDK and export its screen."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

NATIVE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(NATIVE / 'bindings/python'))
from nocturne_native import NativeScene


def validate_document(document):
    if (
        not isinstance(document, dict)
        or document.get('schema') != 'nocturne.composition.v1'
        or set(document) != {'schema', 'seed', 'commands'}
    ):
        raise ValueError('Unsupported composition document')
    if type(document['seed']) is not int or not 0 <= document['seed'] <= 0xffffffff:
        raise ValueError('Composition seed must be uint32')
    if not isinstance(document['commands'], list) or any(
        not isinstance(command, dict) or not isinstance(command.get('op'), str)
        for command in document['commands']
    ):
        raise ValueError('Composition commands must be command objects')
    return document


class CompositionApplication:
    """Own a native scene; the consuming host supplies subsequent input and time."""

    def __init__(self, document, *, library=None, time_us=0):
        # JSON ownership prevents later edits to the caller's document becoming
        # edits to this application's authored input.
        self.document = validate_document(json.loads(json.dumps(document)))
        if type(time_us) is not int or time_us < 0:
            raise ValueError('Scene time must be nonnegative integer microseconds')
        self.scene = NativeScene(seed=self.document['seed'], library=library)
        try:
            if self.document['commands']:
                self.scene.batch(self.document['commands'])
            if time_us:
                self.scene.advance_to(time_us)
        except Exception:
            self.scene.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, *exception):
        self.scene.close()


def export_screen(application, original, library, output):
    """Stage a complete file set before publishing a new output directory."""
    if output.exists():
        raise ValueError('Output already exists')
    scene = application.scene
    snapshot = scene.snapshot()
    frame = scene.render()
    if scene.snapshot() != snapshot:
        raise RuntimeError('Rendering changed retained scene state')
    info = scene.info_complete()
    files = {
        'composition.json': original,
        'scene.cells': frame.bytes,
        'scene.snapshot': snapshot,
        'scene-info.json': (json.dumps(info, indent=2) + '\n').encode(),
    }
    manifest = {
        'schema': 'nocturne.native-composition-application.v1',
        'librarySha256': hashlib.sha256(library.read_bytes()).hexdigest(),
        'abiVersion': info['contract']['abiVersion'],
        'snapshotSchema': '0x' + format(info['contract']['snapshotSchema'], 'x'),
        'timeUs': info['clock']['timeUs'],
        'width': frame.width,
        'height': frame.height,
        'files': {},
    }
    stage = Path(tempfile.mkdtemp(dir=output.parent, prefix='.nocturne-screen-'))
    try:
        for name, data in files.items():
            (stage / name).write_bytes(data)
            manifest['files'][name] = {
                'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
            }
        (stage / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
        if output.exists():
            raise ValueError('Output appeared during export')
        stage.rename(output)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return {'passed': True, 'renderPure': True, 'exportDirectory': str(output),
            'scope': 'Native starting application screen; not final SDK qualification',
            'manifest': manifest}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('document', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--library', type=Path)
    parser.add_argument('--time-us', type=int, default=0)
    arguments = parser.parse_args()
    try:
        output = arguments.output.resolve()
        if output.exists():
            raise ValueError('Output already exists')
        library = arguments.library or NATIVE / 'dist' / (
            'libnocturne_native.dylib' if sys.platform == 'darwin' else 'libnocturne_native.so'
        )
        library = library.resolve(strict=True)
        original = arguments.document.read_bytes()
        with CompositionApplication(json.loads(original), library=library,
                                    time_us=arguments.time_us) as application:
            result = export_screen(application, original, library, output)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, RuntimeError) as error:
        print(json.dumps({'passed': False, 'error': str(error)}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
