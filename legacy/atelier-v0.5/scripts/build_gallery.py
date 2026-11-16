"""Embed the compiled TypeScript binding, schema, presets and WASM into one HTML file."""
import base64
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'web/gallery.template.html').read_text()
binding=(ROOT/'dist/typescript/nocturne.js').read_text().replace('export ','')
for key,value in {
 '/*__BINDING__*/':binding,
 '/*__SCHEMA__*/':(ROOT/'schema.json').read_text().strip(),
 '/*__PRESETS__*/':(ROOT/'presets.json').read_text().strip(),
 '/*__WASM__*/':base64.b64encode((ROOT/'dist/nocturne.wasm').read_bytes()).decode(),
}.items():
 source=source.replace(key,value)
(ROOT/'Nocturne-Gallery.html').write_text(source)
print(f'Built {ROOT / "Nocturne-Gallery.html"} ({len(source.encode()):,} bytes)')
