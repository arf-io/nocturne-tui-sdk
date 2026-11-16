#!/usr/bin/env python3
"""Deterministic inventory of every HTML edition on this host.

For each file: byte size, SHA-256, every <script> block (SHA-256, length, type),
every embedded base64 WebAssembly module (decoded SHA-256, byte length, parsed
import and export sections) and a byte-identity group id so identical editions
are counted once without losing provenance. No rendering, no execution.
"""
import base64, glob, hashlib, json, os, re, sys

ROOT = sys.argv[1]
OUT = sys.argv[2]
os.chdir(ROOT)

FILES = sorted(glob.glob('legacy/editions/*.html')) + sorted(
    f for f in glob.glob('Nocturne-*.html') if f != 'Nocturne-RC4.html') + ['legacy/Nocturne-Gallery-v0.1.html']

SCRIPT_RE = re.compile(rb'<script([^>]*)>(.*?)</script>', re.S | re.I)
B64_RE = re.compile(rb'AGFzbQ[A-Za-z0-9+/=]{64,}')


def sha(b):
    return hashlib.sha256(b).hexdigest()


def leb(buf, i):
    r = 0; s = 0
    while True:
        b = buf[i]; i += 1
        r |= (b & 0x7f) << s
        if not b & 0x80:
            return r, i
        s += 7


def wasm_sections(buf):
    """Return imports, exports and a section list from a wasm binary; tolerant."""
    info = {'valid': False, 'sections': [], 'imports': [], 'exports': [], 'error': None}
    try:
        if buf[:4] != b'\0asm':
            info['error'] = 'bad magic'; return info
        info['version'] = int.from_bytes(buf[4:8], 'little')
        i = 8
        while i < len(buf):
            sid = buf[i]; i += 1
            size, i = leb(buf, i)
            body = buf[i:i + size]; i += size
            info['sections'].append({'id': sid, 'bytes': size})
            if sid == 2:  # import
                n, j = leb(body, 0)
                for _ in range(n):
                    ml, j = leb(body, j); mod = body[j:j + ml].decode('utf-8', 'replace'); j += ml
                    fl, j = leb(body, j); fld = body[j:j + fl].decode('utf-8', 'replace'); j += fl
                    kind = body[j]; j += 1
                    if kind == 0:
                        _, j = leb(body, j)
                    elif kind == 1:
                        j += 1; flags = body[j]; j += 1; _, j = leb(body, j)
                        if flags & 1: _, j = leb(body, j)
                    elif kind == 2:
                        flags = body[j]; j += 1; _, j = leb(body, j)
                        if flags & 1: _, j = leb(body, j)
                    elif kind == 3:
                        j += 2
                    info['imports'].append({'module': mod, 'field': fld, 'kind': kind})
            elif sid == 7:  # export
                n, j = leb(body, 0)
                for _ in range(n):
                    nl, j = leb(body, j); name = body[j:j + nl].decode('utf-8', 'replace'); j += nl
                    kind = body[j]; j += 1
                    _, j = leb(body, j)
                    info['exports'].append({'name': name, 'kind': kind})
        info['valid'] = True
    except Exception as e:  # keep going, record the failure
        info['error'] = f'{type(e).__name__}: {e}'
    return info


records = []
for f in FILES:
    raw = open(f, 'rb').read()
    rec = {'path': f, 'bytes': len(raw), 'sha256': sha(raw), 'scripts': [], 'wasmModules': []}
    title = re.search(rb'<title>(.*?)</title>', raw, re.S | re.I)
    rec['title'] = title.group(1).decode('utf-8', 'replace').strip() if title else None
    for m in SCRIPT_RE.finditer(raw):
        attrs, body = m.group(1), m.group(2)
        rec['scripts'].append({'attrs': attrs.decode('utf-8', 'replace').strip(), 'bytes': len(body), 'sha256': sha(body)})
    for m in B64_RE.finditer(raw):
        b64 = m.group(0)
        try:
            blob = base64.b64decode(b64 + b'=' * (-len(b64) % 4), validate=False)
        except Exception as e:
            rec['wasmModules'].append({'offset': m.start(), 'error': str(e)}); continue
        info = wasm_sections(blob)
        rec['wasmModules'].append({'offset': m.start(), 'base64Length': len(b64), 'bytes': len(blob), 'sha256': sha(blob),
                                   'valid': info['valid'], 'version': info.get('version'), 'error': info['error'],
                                   'sectionCount': len(info['sections']),
                                   'importCount': len(info['imports']), 'imports': info['imports'],
                                   'exportCount': len(info['exports']),
                                   'exportNames': [e['name'] for e in info['exports']]})
    records.append(rec)

# byte-identity groups across whole files and across modules
by_file = {}
for r in records:
    by_file.setdefault(r['sha256'], []).append(r['path'])
by_module = {}
for r in records:
    for w in r['wasmModules']:
        if 'sha256' in w:
            by_module.setdefault(w['sha256'], []).append(r['path'])
for r in records:
    r['identicalFiles'] = [p for p in by_file[r['sha256']] if p != r['path']]

out = {
    'schema': 'nocturne.artwork-inventory.modules.v1',
    'scope': 'Every Nocturne HTML edition present in this checkout (legacy/editions, root Nocturne-*.html except the generated Nocturne-RC4.html, legacy/Nocturne-Gallery-v0.1.html). Static byte inspection only; nothing executed or rendered.',
    'files': records,
    'identicalFileGroups': [{'sha256': k, 'paths': v} for k, v in by_file.items() if len(v) > 1],
    'identicalModuleGroups': [{'sha256': k, 'paths': v} for k, v in by_module.items() if len(v) > 1],
    'distinctModuleCount': len(by_module),
    'distinctFileCount': len(by_file),
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, 'w'), indent=1, sort_keys=True)
print('files', len(records), 'distinct files', len(by_file), 'distinct modules', len(by_module))
for g in out['identicalFileGroups']:
    print('IDENTICAL FILES', g['paths'])
for r in records:
    for w in r['wasmModules']:
        print(f"{r['path']:52} wasm {w.get('bytes','?'):>8} {str(w.get('sha256'))[:12]} valid={w.get('valid')} imports={w.get('importCount')} exports={w.get('exportCount')} err={w.get('error')}")
