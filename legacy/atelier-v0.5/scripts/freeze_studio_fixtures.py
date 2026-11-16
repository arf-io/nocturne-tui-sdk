"""Explicit maintainer operation. Never invoked by ordinary tests or CI."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from studio import Studio,Node,Impulse
if '--accept-new-reference' not in sys.argv:raise SystemExit('Requires --accept-new-reference; review changes before committing')
cases=[]
for pattern in range(12):
 for pixel in range(4):cases.append(dict(name=f'pattern-{pattern}-pixel-{pixel}',config=dict(width=31,height=13,pattern=pattern,pixelMode=pixel),timeMs=1234+pattern*73,nodes=[],events=[]))
for i,kind in enumerate(['text','box','rule','button','item','cursor','progress','bars','pie','donut','scatter','line','digits','edge']):cases.append(dict(name='node-'+kind,config=dict(width=40,height=18),timeMs=5432,nodes=[dict(kind=kind,x=2,y=2,width=30,height=10,id=7,text='67',data=[200,400,700,900],value=670,colorAnimation=2)],events=[]))
for kind in range(2):cases.append(dict(name=f'impulse-{kind}',config=dict(width=40,height=18),timeMs=7000,nodes=[],events=[dict(x=20,y=9,atMs=6000,strength=1000,kind=kind,id=15)]))
for mode in range(5):cases.append(dict(name=f'focus-{mode}-long-clock',config=dict(width=31,height=13,focusMode=mode,focusX=2560,focusY=1536,pattern=3),timeMs=10**12,nodes=[],events=[]))
for mode in [0,1,2]:cases.append(dict(name=f'quantize-{mode}',config=dict(width=31,height=13,quantize=mode,pattern=4,pivotX=-70000,pivotY=42000,rotationMode=2),timeMs=4294969999,nodes=[],events=[]))
def fnv(b):
 h=14695981039346656037
 for v in b:h=((h^v)*1099511628211)&((1<<64)-1)
 return f'{h:016x}'
for c in cases:
 f=Studio(**c['config']).render(c['timeMs'],nodes=[Node(**n) for n in c['nodes']],events=[Impulse(**e) for e in c['events']]);c['sha256']=hashlib.sha256(f.tobytes()).hexdigest();c['fnv64']=fnv(f.tobytes())
(ROOT/'tests/studio.fixtures.json').write_text(json.dumps(cases,indent=2)+'\n')
# Dependency-free Rust fixture checks generated from the SAME accepted cases.
lines=['#![allow(non_snake_case,unused_mut)]','// Generated only by explicit fixture acceptance. Not run during CI.','use nocturne_surfaces::studio::{Studio,StageKey,Node,NodeKey,NodeKind,Impulse};','fn fnv(bytes:&[u8])->u64 {bytes.iter().fold(14695981039346656037u64,|h,b|(h^(*b as u64)).wrapping_mul(1099511628211))}','#[test] fn acceptedStudioFixtures(){']
for c in cases:
 lines.append('{let mut s=Studio::new().unwrap();')
 for k,v in c['config'].items():lines.append(f's.set(StageKey::{k[0].upper()+k[1:]},{v}).unwrap();')
 lines.append('let mut nodes=Vec::new();')
 for n in c['nodes']:
  lines.append(f'let mut n=Node::new(NodeKind::{n["kind"].title()},{n["x"]},{n["y"]},{n["width"]},{n["height"]}).unwrap();n.text="67".into();n.data=vec![200,400,700,900];n.set(NodeKey::Id,7);n.set(NodeKey::Value,670);n.set(NodeKey::ColorAnimation,2);nodes.push(n);')
 lines.append('let mut events=Vec::new();')
 for e in c['events']:lines.append(f'events.push(Impulse{{xQ8:{e["x"]*256},yQ8:{e["y"]*256},strength:1000,kind:{e["kind"]},atMs:6000,id:15}});')
 lines.append(f'assert_eq!(fnv(&s.render({c["timeMs"]},&nodes,&events).unwrap().toBytes()),0x{c["fnv64"]}u64,"{c["name"]}");}}')
lines.append('}')
(ROOT/'bindings/rust/tests').mkdir(exist_ok=True)
(ROOT/'bindings/rust/tests/studio_fixtures.rs').write_text('\n'.join(lines)+'\n')
print('Accepted',len(cases),'cross-language cases')
