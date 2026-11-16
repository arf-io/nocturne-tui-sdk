import json,sys
from playwright.sync_api import sync_playwright
from pathlib import Path
url=(Path(__file__).resolve().parents[1]/'Nocturne-RC4-Source-Build.html').as_uri()
ids=['autumn','pearl-observatory-tmux','silk','windows','embers']
with sync_playwright() as p:
    for headed_gpu in (False,):
        b=p.chromium.launch(args=['--use-angle=metal','--enable-gpu','--ignore-gpu-blocklist'])
        for mode in ('canvas2d','webgl'):
            pg=b.new_page(viewport={'width':1680,'height':1000}); pg.goto(url+('?paint=webgl' if mode=='webgl' else '')); pg.wait_for_function('window.nativeLab&&window.nativeView')
            renderer=pg.evaluate("(()=>{const c=document.getElementById('canvas-gl');const g=c&&(c.getContext('webgl2')||c.getContext('webgl'));if(!g)return 'none';const e=g.getExtension('WEBGL_debug_renderer_info');return e?g.getParameter(e.UNMASKED_RENDERER_WEBGL):g.getParameter(g.RENDERER)})()")
            for rid in ids:
                ok=pg.evaluate("id=>{const r=nativeLab.recipes.find(r=>r.id===id);if(!r)return false;nativeLab.hold();nativeLab.load(r);nativeLab.hold();nativeLab.advance(3000000);return true}",rid)
                if not ok: continue
                ms=pg.evaluate("""mode=>{const gl=document.getElementById('canvas-gl');const g=gl&&(gl.getContext('webgl2')||gl.getContext('webgl'));const c=document.getElementById('canvas').getContext('2d');const out=[];
                  for(let i=0;i<40;i++){nativeLab.advance(16667);const t0=performance.now();nativeLab.draw();
                    if(mode==='webgl'){const px=new Uint8Array(4);g.readPixels(0,0,1,1,g.RGBA,g.UNSIGNED_BYTE,px);}else{c.getImageData(0,0,1,1);}
                    out.push(performance.now()-t0);}out.sort((a,b)=>a-b);return {median:out[20],p90:out[36]}}""",mode)
                print(mode,rid,json.dumps(ms),'renderer=' + str(renderer)[:60] if mode=='webgl' and rid==ids[0] else '')
            pg.close()
        b.close()
