"""Package verified capture originals with a native WASM cell-art preview host."""

import argparse
import base64
import hashlib
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREVIEW_DESCRIPTION = (
    '80x40 native-cell downsample; originals retain full capture fidelity'
)


def parse_arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--media', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument(
        '--inline-media', action='store_true',
        help='Embed originals in HTML using their actual MIME types',
    )
    arguments = parser.parse_args()
    if arguments.output.resolve().exists():
        parser.error('Output already exists')
    return arguments


def load_capture(root):
    """Retain original manifest bytes and independently own the viewer cases."""
    original = (root / 'MEDIA.json').read_bytes()
    capture = json.loads(original)
    if (
        capture.get('schema') != 'nocturne.scene-media.v1'
        or capture.get('passed') is not True
        or capture.get('complete') is not True
        or not capture.get('cases')
    ):
        raise ValueError('Completed capture manifest required')
    cases = json.loads(json.dumps(capture['cases']))
    return original, capture, cases


def verified_media(root, record, *, video):
    """Resolve inside the capture root and check format, size and original hash."""
    source = (root / record['path']).resolve()
    if not source.is_relative_to(root) or not source.is_file():
        raise ValueError('Invalid capture path')
    data = source.read_bytes()
    suffix = '.webm' if video else '.png'
    magic = b'\x1aE\xdf\xa3' if video else b'\x89PNG\r\n\x1a\n'
    if source.suffix.lower() != suffix or not data.startswith(magic):
        raise ValueError('Capture media format differs')
    if (
        len(data) != record['bytes']
        or hashlib.sha256(data).hexdigest() != record['sha256']
    ):
        raise ValueError('Capture custody mismatch')
    return source, data


def package_media(root, stage, cases, *, inline):
    index = 0
    for case in cases:
        if not case['complete']:
            raise ValueError('Incomplete capture case')
        records = [sample['screenshot'] for sample in case['samples']]
        records.append(case['video'])
        for record in records:
            video = record is case['video']
            source, original = verified_media(root, record, video=video)
            filename = f'capture-{index:04d}' + source.suffix
            index += 1
            mime_type = 'video/webm' if video else 'image/png'
            record['sourcePath'] = record['path']
            record['filename'] = filename
            record['mimeType'] = mime_type
            if inline:
                encoded = base64.b64encode(original).decode()
                record['path'] = 'data:' + mime_type + ';base64,' + encoded
            else:
                (stage / filename).write_bytes(original)
                record['path'] = filename


def viewer_document(capture, cases):
    wasm = (ROOT / 'dist/nocturne_native.wasm').read_bytes()
    binding = (ROOT / 'bindings/typescript/native_scene.mjs').read_text()
    provenance = {
        'cases': cases,
        'captureWasmSha256': capture['wasmSha256'],
        'captureGallerySha256': capture['gallerySha256'],
        'viewerWasmSha256': hashlib.sha256(wasm).hexdigest(),
        'preview': PREVIEW_DESCRIPTION,
    }
    replacements = {
        '@@DATA@@': json.dumps(provenance).replace('<', '\\u003c'),
        '@@WASM@@': base64.b64encode(wasm).decode(),
        '@@BINDING@@': binding.replace('export { NativeScene };', ''),
    }
    html = (ROOT / 'web/media_site.html').read_text()
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)
    return html, provenance


def write_manifest(stage):
    files = {}
    for path in sorted(stage.iterdir()):
        files[path.name] = {
            'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    manifest = {
        'schema': 'nocturne.media-site.v1',
        'scope': 'Captured subset, not complete media corpus or final SDK qualification',
        'files': files,
    }
    (stage / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


def main():
    arguments = parse_arguments()
    root = arguments.media.resolve()
    output = arguments.output.resolve()
    original, capture, cases = load_capture(root)
    with tempfile.TemporaryDirectory(dir=output.parent) as temporary:
        stage = Path(temporary)
        package_media(root, stage, cases, inline=arguments.inline_media)
        html, provenance = viewer_document(capture, cases)
        (stage / 'media.html').write_text(html)
        (stage / 'CAPTURE.json').write_bytes(original)
        (stage / 'PROVENANCE.json').write_text(
            json.dumps(provenance, indent=2) + '\n'
        )
        manifest = write_manifest(stage)
        stage.rename(output)
    print(json.dumps({'cases': len(cases), 'files': len(manifest['files'])}))


if __name__ == '__main__':
    main()
