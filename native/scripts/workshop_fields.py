#!/usr/bin/env python3
"""Regenerate native/web/workshop_fields.json from the TypeScript command contract.

The Workshop field index is the compiler's view of native/bindings/typescript/contracts.ts: every NativeCommand
operation, and for each the direct and nested authoring fields with their declared types and finite choices. It is
bound to the contract by sourceSha256, so any byte change to contracts.ts needs this regeneration (build_gallery.py
refuses a stale index).

The walk is scripts/gallery_option_coverage.mjs run with no gallery cases; this keeps only its declared operations
and the op/field/types/choices of each field. Type strings come from the TypeScript checker, so use the bound compiler
(TypeScript 5.8.3): pass --typescript or set NOCTURNE_TYPESCRIPT_MODULE to its lib/typescript.js. Run with --check to
compare without writing.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

NATIVE = Path(__file__).resolve().parents[1]
CONTRACT = NATIVE / 'bindings/typescript/contracts.ts'
OUTPUT = NATIVE / 'web/workshop_fields.json'
EXPECTED_TYPESCRIPT = '5.8.3'


def typescript_module(explicit=None):
    module = explicit or os.environ.get('NOCTURNE_TYPESCRIPT_MODULE')
    if not module:
        raise SystemExit('workshop_fields.py: pass --typescript or set NOCTURNE_TYPESCRIPT_MODULE to TypeScript lib/typescript.js')
    return str(Path(module).resolve())


def generate(module, node='node'):
    version = subprocess.run([node, '-e', 'console.log(require(process.argv[1]).version)', module],
                             check=True, capture_output=True, text=True).stdout.strip()
    if version != EXPECTED_TYPESCRIPT:
        raise SystemExit(f'workshop_fields.py: TypeScript {version} found; the index is generated with {EXPECTED_TYPESCRIPT}')
    with tempfile.TemporaryDirectory(prefix='workshop-fields-') as directory:
        cases = Path(directory) / 'cases.json'
        out = Path(directory) / 'coverage.json'
        cases.write_text('[]')
        subprocess.run([node, str(NATIVE / 'scripts/gallery_option_coverage.mjs'), module, str(cases), str(out)],
                       check=True, capture_output=True, text=True)
        coverage = json.loads(out.read_text())
    record = {'sourceSha256': hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
              'operations': coverage['declaredOperations'],
              'fields': [{key: row[key] for key in ('op', 'field', 'types', 'choices')} for row in coverage['fields']]}
    return json.dumps(record, indent=2, ensure_ascii=False) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--typescript', help='path to TypeScript lib/typescript.js (default: NOCTURNE_TYPESCRIPT_MODULE)')
    parser.add_argument('--check', action='store_true', help='exit 1 if the committed index differs; write nothing')
    args = parser.parse_args()
    text = generate(typescript_module(args.typescript))
    current = OUTPUT.read_text(encoding='utf-8') if OUTPUT.is_file() else None
    if args.check:
        print(json.dumps({'upToDate': text == current}))
        return 0 if text == current else 1
    if text != current:
        OUTPUT.write_text(text, encoding='utf-8')
    record = json.loads(text)
    print(json.dumps({'operations': len(record['operations']), 'fields': len(record['fields']), 'changed': text != current}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
