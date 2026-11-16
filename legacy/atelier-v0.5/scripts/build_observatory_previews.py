#!/usr/bin/env python3
"""Actual cell screenshots and a 60 FPS explicit-time recording. No shaders.
The optional movie requires ffmpeg. No font assets are copied or packaged.
"""
import argparse,base64,json,os,subprocess,time
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dist/observatory';OUT.mkdir(exist_ok=True)
RECIPES=['pearl-wave','hyperlane','copper-orbit','neon-bbs','gold-glass','winterfall']
p=argparse.ArgumentParser();p.add_argument('--video',action='store_true');a=p.parse_args()
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),headless=True,args=['--no-sandbox']);page=b.new_page(viewport={'width':1580,'height':1100});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def load():
  page.goto('about:blank');page.set_content((ROOT/'Nocturne-Observatory.html').read_text());page.wait_for_function('window.observatoryApp');page.evaluate('observatoryApp.setAuto(false)')
 load()
 shots=[]
 for index,recipe in enumerate(RECIPES):
  load();page.select_option('#recipe',recipe)
  page.evaluate('''(i)=>{const a=observatoryApp;a.model.resize(136,44);a.model.setTime(5200);a.model.demoData(1200);if(i===4){a.model.toggleWindow(1,'maximized');a.model.setTime(5410);}if(i===5){a.model.emit(67,25,'*','snow');a.model.setTime(6000);}a.paint();}''',index)
  data=page.locator('#stage').evaluate("e=>e.toDataURL('image/png').split(',')[1]");path=OUT/f'Observatory-{recipe}.png';path.write_bytes(base64.b64decode(data));shots.append(path)
 load();page.locator('#stage').focus();page.keyboard.type('Immediate ink, even between frames.');page.screenshot(path=str(OUT/'Nocturne-Observatory.png'),full_page=False)
 # Combined browser render+raster performance, warmed; physical presentation excluded.
 perf=page.evaluate('''()=>{const a=observatoryApp;a.setAuto(false);const s=[];for(let i=0;i<90;i++){a.model.setTime(6000+i*1000/60);const b=performance.now();a.paint();if(i>=10)s.push(performance.now()-b);}s.sort((a,b)=>a-b);return {viewport:[a.model.width,a.model.height],warmup:10,samples:s.length,medianMs:s[40],p95Ms:s[76],maxMs:s[79],excludes:['physical display','terminal emulator','terminal transport']}}''')
 (OUT/'performance-browser.json').write_text(json.dumps(perf,indent=2)+'\n')
 if a.video:
  command=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','image2pipe','-framerate','60','-vcodec','png','-i','-','-an','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'Nocturne-Observatory-60fps.mp4')]
  proc=subprocess.Popen(command,stdin=subprocess.PIPE);n=0
  try:
   for section,recipe in enumerate(RECIPES):
    load();page.select_option('#recipe',recipe);base=page.evaluate('observatoryApp.model.motionMs');baseData=page.evaluate('observatoryApp.model.dataMs')
    for frame in range(120):
     data=page.evaluate('''([base,f,section,baseData])=>{const a=observatoryApp,t=base+f*1000/60;a.model.setTime(t);a.model.demoData(baseData+f*1000/60);if(f===2)a.model.input('Light follows the event.');if(f===25)a.model.emit(75,23,'*',section===5?'snow':'nova');if(section===4&&f===12)a.model.toggleWindow(1,'maximized');if(section===4&&f===70)a.model.toggleWindow(1,'maximized');a.paint();return document.getElementById('stage').toDataURL('image/png').split(',')[1];}''',[base,frame,section,baseData]);proc.stdin.write(base64.b64decode(data));n+=1
   proc.stdin.close();assert proc.wait(timeout=40)==0
  finally:
   if proc.poll() is None:proc.kill();proc.wait()
  (OUT/'preview-report.json').write_text(json.dumps({'frames':n,'fps':60,'seconds':n/60,'source':'actual shared-cell renderer, explicit timestamps','syntheticData':True,'physical60FpsClaim':False},indent=2)+'\n')
 assert not errors,errors;b.close()
# Contact sheet: original cell output and simple editorial labels.
fontPath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';font=ImageFont.truetype(fontPath,18)
w=1088;h=704;gap=18;label=44;sheet=Image.new('RGB',(2*w+gap*3,3*(h+label)+gap*4),'#0b1016');d=ImageDraw.Draw(sheet)
labels=['PEARL / reactive braille signal','HYPERLANE / free-vector XYZ flight','COPPER / orbital shared-parent DAG','STARFALL / neon BBS exchange','GLASS / expanding workspaces','WINTERFALL / typographic weather']
for i,path in enumerate(shots):
 x=gap+(i%2)*(w+gap);y=gap+(i//2)*(h+label+gap);d.text((x,y+8),labels[i],font=font,fill='#c9d0cc');im=Image.open(path).convert('RGB');sheet.paste(im.resize((w,h)),(x,y+label))
sheet.save(OUT/'Nocturne-Observatory-Contact.png')
print(json.dumps({'screenshots':len(shots)+1,'browserPerformance':perf,'video':a.video},indent=2))
