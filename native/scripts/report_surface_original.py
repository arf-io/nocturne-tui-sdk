#!/usr/bin/env python3
"""Display retained full-cell Surface4 comparisons without synthetic artwork."""
from pathlib import Path
import getpass,gzip,hashlib,json,struct,datetime
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'evidence/surface-original-20261014';F=D/'frames-02'
def read(n):return json.loads(gzip.decompress((F/(n+'.json.gz')).read_bytes()))
def sha(b):return hashlib.sha256(b).hexdigest()
def cellsha(c):return sha(struct.pack('<'+'I'*len(c),*c))
def rle(c):
 out=[]
 for i in range(0,len(c),4):
  cell=c[i:i+4]
  if out and out[-1][1:]==cell:out[-1][0]+=1
  else:out.append([1]+cell)
 return out
requests,original,native,wasm=[read(n) for n in ('requests','original','native','wasm')]
assert len(requests)==len(original)==len(native)==len(wasm)==168
rows=[];views=[]
for q,o,n,w in zip(requests,original,native,wasm):
 assert o['cells']==n==w
 rows.append({'case':q['name'],'effect':q['effect'],'backend':q['backend'],'width':q['width'],'height':q['height'],'timeMs':q['timeMs'],'controls':q['controls'],'originalFrameSha256':cellsha(o['cells']),'nativeFrameSha256':cellsha(n),'wasmFrameSha256':cellsha(w),'wordsCompared':len(n),'exact':True})
 views.append({'name':q['name'],'width':q['width'],'height':q['height'],'original':rle(o['cells']),'native':rle(n),'wasm':rle(w)})
manifest={'status':'PASS','time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'principal':getpass.getuser(),'sourceHTMLSha256':'375c4468c886728bc790b8d8cc3bdddc2a046532a4d792cde190f1b522a66385','sourceWASMSha256':'aa04c1705a5982b924d420971bfcbc7bbedd49f1ea527a9900531b61b0c92a09','sourceArchiveSha256':'9280288a52737d2bfe54379627f5cbe8a280c939a3eece79a1be08eaa6041e63','originalFixture':'tests/fixtures/original-rc2-workbench-docs.html.gz','nativeCases':168,'wasmCases':168,'identityCount':4,'comparison':'Every uint32 word including glyph, foreground, background and ID; no masks. Actual original EffectPainter.local over identical recorded base cells. Authored control cases call original engine, weather and particle APIs with declared options.','limits':['Surface4 tile and composition proof does not establish enclosing original application parity.','Velocity and clipping are preserved native extensions, checked separately.','Previous optics source without paint source remains a separate equation sampler.','Release-wide qualification belongs to the integration worktree.'],'cases':rows,'files':{str(p.relative_to(D)):sha(p.read_bytes()) for p in F.iterdir() if p.is_file()},'binaries':{n:sha((ROOT/'dist'/n).read_bytes()) for n in ['libnocturne_native.dylib','nocturne_native.wasm']}}
(D/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
html="""<!doctype html><html lang="en"><meta charset="utf-8"><title>Surface4 original evidence</title><style>body{font:16px system-ui;background:#10151e;color:#dae5ed;margin:24px}a{color:#87ceda}select{font:inherit;padding:8px}.frames{display:flex;gap:16px;flex-wrap:wrap}canvas{max-width:100%;image-rendering:pixelated}figure{margin:12px 0}p{max-width:1000px;line-height:1.5}</style><h1>Surface4 — actual original and native frames</h1><p>168 cases per backend. Four original identities, three viewports and centers, two control sets, seven times including birth and expiry. Every cell word matches the retained original painter. No masks. Canvases display recorded buffers; glyph appearance depends on the browser font.</p><p><a href="manifest.json">Hashes and case manifest</a> · <a href="source-run-04.log">Native/WASM log</a> · <a href="controls-route-red.log">Retained failed control run</a> · <a href="normal-route-run-04.log">Normal gallery route log</a></p><p>This proves the four original ripple layers and tile composition. Gallery route proof separately compares native/WASM and does not claim original surrounding application parity.</p><label>Recorded case <select id="case"></select></label><div class="frames" id="frames"></div><script>const records=@@DATA@@;const select=document.getElementById('case');records.forEach((r,i)=>select.add(new Option(r.name,i)));function rgb(n){return '#'+n.toString(16).padStart(6,'0')}function draw(){const r=records[select.value||0],wrap=document.getElementById('frames');wrap.replaceChildren();for(const name of ['original','native','wasm']){const fig=document.createElement('figure'),cap=document.createElement('figcaption'),canvas=document.createElement('canvas');cap.textContent=name;canvas.width=r.width*8;canvas.height=r.height*16;const c=canvas.getContext('2d');c.font='16px monospace';c.textBaseline='top';let i=0;for(const row of r[name])for(let n=0;n<row[0];n++,i++){let x=(i%r.width)*8,y=Math.floor(i/r.width)*16;c.fillStyle=rgb(row[3]);c.fillRect(x,y,8,16);c.fillStyle=rgb(row[2]);if(row[1]===0x2580)c.fillRect(x,y,8,8);else if(row[1]===0x2584)c.fillRect(x,y+8,8,8);else if(row[1]!==32&&row[1])c.fillText(String.fromCodePoint(row[1]),x,y)}fig.append(cap,canvas);wrap.append(fig)}}select.onchange=draw;draw();</script></html>"""
(D/'report.html').write_text(html.replace('@@DATA@@',json.dumps(views,separators=(',',':'))))
print(json.dumps({'native':len(rows),'wasm':len(rows),'identities':len({r['effect'] for r in rows}),'reportBytes':(D/'report.html').stat().st_size}))
