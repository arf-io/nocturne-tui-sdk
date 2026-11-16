#!/usr/bin/env python3
"""Capture the actual browser canvas at EVERY tick in the frozen capture plan.
Browser pixels use that canvas's intrinsic 8x16 cell raster at device scale 1.
Canonical cells are independently compared with the TypeScript replay. This is
not a physical GPU/terminal screenshot, and no requestAnimationFrame time is used.
"""
from __future__ import annotations
import argparse,base64,hashlib,json,os,subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('evidence',type=Path);p.add_argument('--no-video',action='store_true');a=p.parse_args();plan=json.loads((a.evidence/'CAPTURE-PLAN.json').read_text());out=a.evidence/'browser-ticks';out.mkdir(exist_ok=True);entries=[];failures=[]
    with sync_playwright()as q:
        options={'headless':True}
        if os.environ.get('CHROMIUM_PATH'):options['executable_path']=os.environ['CHROMIUM_PATH']
        elif Path('/usr/bin/chromium').exists():options['executable_path']='/usr/bin/chromium'
        browser=q.chromium.launch(**options)
        page=browser.new_page(viewport={'width':max(1600,plan['width']*8+100),'height':max(1200,plan['height']*16+300)},device_scale_factor=1)
        page.on('pageerror',lambda e:failures.append(str(e)))
        page.evaluate('window.requestAnimationFrame=()=>0')
        page.set_content((ROOT/'Nocturne-RC3.html').read_text(),wait_until='load');page.wait_for_function('window.__chromaticReady',timeout=30000)
        for case in plan['cases']:
            folder=out/case['name'];folder.mkdir(exist_ok=True)
            page.evaluate('async()=>{app=await ExhibitionSession.create(bytes,DATA.schema,DATA.catalog);window.__app=app;}')
            page.evaluate('p=>send("demo-resize",p)',{'width':plan['width'],'height':plan['height']});page.evaluate('id=>send("demo-open",{id})',case['id'])
            page.evaluate('()=>{const c=document.querySelector("#stage");document.body.appendChild(c);Object.assign(c.style,{position:"absolute",left:"0",top:"0",zIndex:"999999",width:c.width+"px",height:c.height+"px",maxWidth:"none",padding:"0",margin:"0",border:"0",transform:"none"});}')
            for i in range(case['frames']):
                for event in case['commands']:
                    if event['frame']==i:page.evaluate('c=>send(c.op,c.payload)',event)
                t=i*1000//plan['fps']
                encoded=page.evaluate('t=>{const r=send("demo-time",{timeMs:t});const b=new Uint8Array(r.frame.cells.buffer,r.frame.cells.byteOffset,r.frame.cells.byteLength);let s="";for(let i=0;i<b.length;i+=4096)s+=String.fromCharCode(...b.subarray(i,i+4096));return btoa(s);}',t)
                raw=base64.b64decode(encoded);reference=a.evidence/'frames/typescript'/case['name']/f'frame-{i:06d}.cells';same=reference.is_file()and reference.read_bytes()==raw
                file=folder/f'frame-{i:06d}.png';page.locator('#stage').screenshot(path=str(file),scale='css',animations='disabled')
                with Image.open(file)as image: resolution=list(image.size)
                if resolution!=[plan['width']*8,plan['height']*16]:failures.append(f"Capture was rescaled: {case['name']} tick {i}: {resolution}")
                if not same:
                    file.with_suffix('.cells').write_bytes(raw)
                    file.with_suffix('.json').write_text(json.dumps({'width':plan['width'],'height':plan['height'],'timeMs':t}))
                entries.append({'case':case['name'],'tick':i,'timeMs':t,'cellsSHA256':hashlib.sha256(raw).hexdigest(),'resolution':resolution,'cellsEqualDirect':same,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'bytes':file.stat().st_size})
                if not same:failures.append(f"Browser/direct mismatch: {case['name']} tick {i}")
            if not a.no_video:
                with (folder/'ffmpeg.log').open('w')as log:
                    r=subprocess.run(['ffmpeg','-v','error','-y','-framerate',str(plan['fps']),'-i',str(folder/'frame-%06d.png'),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',str(folder/'review.mp4')],stdout=log,stderr=log,timeout=1800)
                if r.returncode:failures.append('Video encode failed '+case['name'])
                else:
                    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames,width,height','-of','json',str(folder/'review.mp4')],timeout=30))
                    (folder/'video.json').write_text(json.dumps(probe,indent=2))
                    if int(probe['streams'][0]['nb_read_frames'])!=case['frames']:failures.append('Video frame-count mismatch '+case['name'])
        browser.close()
    report={'status':'PASS'if not failures and len(entries)==plan['expectedFrames']else'FAIL','captured':len(entries),'expected':plan['expectedFrames'],'resolution':[plan['width']*8,plan['height']*16],'scope':'actual browser canvas PNG at every declared tick; intrinsic resolution, no stride','failures':failures}
    (a.evidence/'BROWSER-TICKS.json').write_text(json.dumps(report,indent=2));(a.evidence/'BROWSER-FRAME-MANIFEST.jsonl').write_text(''.join(json.dumps(x)+'\n'for x in entries));print(json.dumps(report,indent=2));return 0 if report['status']=='PASS'else 2
if __name__=='__main__':raise SystemExit(main())
