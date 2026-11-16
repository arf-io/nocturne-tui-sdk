"""Generate binding key/range declarations from the canonical schema."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
schema=json.loads((ROOT/'schema.json').read_text())
fields='// Generated from schema.json.\npackage nocturne\n\ntype Field struct {index int; minimum,maximum int32}\n\nvar FIELDS=map[string]Field{\n'
for f in schema['fields']:fields+=f'    "{f["name"]}":{{{f["index"]},{f["minimum"]},{f["maximum"]}}},\n'
(ROOT/'bindings/go/fields.go').write_text(fields+'}\n')
rs='// Generated from schema.json.\n#[repr(usize)]\n#[derive(Clone, Copy, Debug)]\npub enum Key {\n'
for f in schema['fields']:rs+=f'    {f["name"][0].upper()+f["name"][1:]} = {f["index"]},\n'
rs+='}\npub(crate) const RANGES: [(i32,i32); '+str(len(schema['fields']))+'] = [\n'
rs+=''.join(f'    ({f["minimum"]}, {f["maximum"]}),\n' for f in schema['fields'])+'];\n'
(ROOT/'bindings/rust/src/keys.rs').write_text(rs)
