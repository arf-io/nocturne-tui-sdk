"""Versioned document files at the host boundary; no native filesystem access."""
import json
import os
from pathlib import Path
import tempfile

PROFILE = 'nocturne-document-v1'

def save_document(scene, path):
    """Atomically replace a file with accepted text/caret, without scene mutation."""
    prompt = scene.info_complete()['prompt']
    data = (json.dumps({'profile': PROFILE, 'text': prompt['text'],
                       'caret': prompt['caret']}, ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')
    path = Path(path)
    fd, name = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as file:
            file.write(data)
            file.flush()
            os.fsync(file.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)

def load_document(scene, path):
    """Validate before one atomic native draft command; never emit input weather.

    This imports a document, not native history, clocks, physics or editor mode.
    """
    with Path(path).open('rb') as file:
        data = file.read()
    value = json.loads(data.decode('utf-8'))
    if not isinstance(value, dict) or set(value) != {'profile', 'text', 'caret'}:
        raise ValueError('Invalid document fields')
    if value['profile'] != PROFILE or not isinstance(value['text'], str):
        raise ValueError('Unsupported document profile')
    if type(value['caret']) is not int or not 0 <= value['caret'] <= len(value['text']):
        raise ValueError('Invalid document caret')
    scene.command({'op': 'draft', 'text': value['text'], 'caret': value['caret'], 'emitWeather': False})
