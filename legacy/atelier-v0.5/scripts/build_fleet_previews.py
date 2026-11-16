#!/usr/bin/env python3
"""Record the actual WASM cell renderer at explicit timestamps, 30 frames/second.
Requires Playwright/Chromium and ffmpeg. No downloaded imagery or font assets.
"""
from pathlib import Path
import base64,json,os,subprocess,time
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dist/fleet';OUT.mkdir(exist_ok=True)
start=time.monotonic()
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),args=['--no-sandbox'])
    page=b.new_page(viewport={'width':1740,'height':1260},device_scale_factor=1)
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content((ROOT/'Nocturne-Pearl-Fleet.html').read_text());page.wait_for_function('window.fleetApp')
    page.evaluate('fleetApp.stop();fleetApp.step(6000)')
    page.locator('#stage').screenshot(path=str(OUT/'Nocturne-Pearl-Fleet.png'))
    page.screenshot(path=str(OUT/'Nocturne-Pearl-Fleet-Studio.png'),full_page=True)
    log=open(OUT/'video-encode.txt','w')
    proc=subprocess.Popen(['ffmpeg','-y','-loglevel','warning','-f','image2pipe','-vcodec','png','-framerate','30','-i','pipe:0','-an','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-vf','pad=ceil(iw/2)*2:ceil(ih/2)*2','-movflags','+faststart',str(OUT/'Nocturne-Pearl-Fleet.mp4')],stdin=subprocess.PIPE,stderr=log)
    for i in range(360):
        url=page.evaluate('''(i)=>{
          const c=fleetApp.controller,t=6000+Math.floor(i*1000/30);c.setTime(t);
          if(i===36)c.openAgent('atlas');
          if(i===65)c.send('Trace the queue and keep the fleet visible.');
          if(i===195)c.scroll(8);
          if(i===220)c.liveTail();
          if(i===240)c.closeAgent();
          if(i===280){c.configure({dense:true});c.selectAgent('prism');}
          if(i===295)c.openAgent('prism');
          // Independent 80-ms synthetic source, sampled into this 30-fps film.
          const prior=i?Math.floor((i-1)*1000/30/80):-1,now=Math.floor(i*1000/30/80);
          for(let tick=prior+1;tick<=now;tick++)c.advanceDemo(10000+tick*80);
          fleetApp.paint();return document.getElementById('stage').toDataURL('image/png');
        }''',i)
        proc.stdin.write(base64.b64decode(url.split(',',1)[1]))
        if i in (55,100,132,285):
            name={55:'workspace',100:'streaming',132:'conversation',285:'dense'}[i]
            (OUT/f'Nocturne-Pearl-Fleet-{name}.png').write_bytes(base64.b64decode(url.split(',',1)[1]))
    proc.stdin.close();code=proc.wait(timeout=15);log.close();assert code==0;assert not errors,errors
    stats=page.evaluate('({...fleetMetrics})');b.close()
report={'frames':360,'fps':30,'durationSeconds':12,'source':'actual shared C/WASM cell frames; scripted explicit time; synthetic telemetry','browserErrors':errors,'elapsedSeconds':round(time.monotonic()-start,2),'lastFrame':stats}
(OUT/'preview-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
