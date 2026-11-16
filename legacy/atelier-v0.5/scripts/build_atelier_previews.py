#!/usr/bin/env python3
"""Render actual SDK cells, capture the visible controls, and record explicit-time
60 FPS studies. Requires Playwright/Chromium, Pillow and optional ffmpeg. No font
assets are copied. Movie frames do not claim physical live terminal throughput.
"""
from pathlib import Path
import argparse, base64, json, os, subprocess
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'dist/atelier'; OUT.mkdir(exist_ok=True)
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--video',action='store_true');args=p.parse_args()
STUDIES=[('hyperlane','warp','Oblique Hyperlane / visible XYZ flight'),('graph','dag','Automatic layout / shared-parent graph'),('weather','weather','Electrical Garden / cores, arcs and embers'),('rain','text','Rain / independent character trajectories'),('glass','windows','Shaped glass / 3D planes and a recovery dock'),('prism','text','Prism Weave / opposing color ribbons')]
setup=r'''([id,scene])=>{const a=atelierApp,m=a.model;a.setAuto(false);m.resize(136,44);m.setScene(scene);m.setTime(0);m.configure({motion:true});
if(id==='hyperlane'){m.camera.look(-10,4);m.replaceDraft('LOOK / MOVE / TRAVEL: three independent controls');}
if(id==='graph'){m.beginLayout({dimensions:3,algorithm:'layered'});while(m.layoutBusy)m.stepLayout(40);m.frameGraph();m.camera.orbit(20,-9);}
if(id==='weather'){m.particleConfig={...m.particleConfig,count:100,rise:10,gravity:10,lifeMs:4200,intensity:1};m.emit(34,21,'*','nova');m.emit(88,19,'*','sparks');m.emit(62,29,'*','embers');}
if(id==='rain'){m.configureText({effect:'rain',durationMs:1900,staggerMs:30,travelRows:15,spreadColumns:10,speedJitter:.75,hueSpread:170});m.setDisplayText('EACH CHARACTER FINDS ITS OWN WAY HOME');m.playText('show',true);}
if(id==='flip'){m.configureText({effect:'flipboard',durationMs:1700,staggerMs:20,cycleHz:25});m.setDisplayText('PEARL  /  67%  /  ALL SYSTEMS NOMINAL');m.playText('show',true);}
if(id==='prism'){m.configureText({effect:'prism-weave',durationMs:1800,staggerMs:23,travelRows:8,hueSpread:180});m.setDisplayText('COLOR IS A PLACE WHERE LETTERS MEET');m.playText('show',true);}
if(id==='glass'||id==='genie'||id==='petal'){m.windowConfigure({effect:id==='petal'?'petal-bloom':'genie',durationMs:950});m.workspace.get(1).shape='ellipse';m.workspace.get(2).shape='hexagon';m.workspace.get(2).yaw=-14;m.workspace.get(2).pitch=8;m.workspace.get(3).shape='ticket';m.workspace.get(3).roll=-7;}
a.paint();}'''
shots=[];errors=[]
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),args=['--no-sandbox']);page=b.new_page(viewport={'width':1680,'height':1250});page.on('pageerror',lambda e:errors.append(str(e)))
 def load(id,scene):
  page.goto('about:blank');page.set_content((ROOT/'Nocturne-Spatial-Atelier.html').read_text());page.wait_for_function('!!window.atelierApp');page.evaluate(setup,[id,scene])
 def png():return base64.b64decode(page.locator('#stage').evaluate("e=>e.toDataURL('image/png').split(',')[1]"))
 for id,scene,label in STUDIES:
  load(id,scene);t={'hyperlane':3300,'graph':1900,'weather':600,'rain':1350,'glass':2000,'prism':1500}[id];page.evaluate('(t)=>atelierApp.seek(t)',t);
  if id=='weather':page.evaluate("atelierApp.model.emit(88,19,'*','sparks');atelierApp.seek(650)")
  path=OUT/f'Atelier-{id}.png';path.write_bytes(png());shots.append((path,label))
 load('hyperlane','warp');page.evaluate('atelierApp.seek(3600);atelierApp.syncControls()');page.screenshot(path=str(OUT/'Nocturne-Spatial-Atelier.png'),full_page=False)
 load('glass','windows');page.evaluate('atelierApp.seek(1800);atelierApp.syncControls()');page.screenshot(path=str(OUT/'Nocturne-Spatial-Atelier-windows.png'),full_page=False)
 perf=page.evaluate('''()=>{const a=atelierApp,v=[];for(let i=0;i<100;i++){a.model.setTime(3000+i*1000/60);let t=performance.now();a.paint();if(i>=15)v.push(performance.now()-t);}v.sort((a,b)=>a-b);return{scene:'windows',viewport:[a.model.width,a.model.height],samples:v.length,medianMs:v[Math.floor(v.length/2)],p95Ms:v[Math.floor(v.length*.95)],maxMs:v.at(-1),excludes:['physical display','terminal encoding/transport/emulator']}}''');(OUT/'performance-browser.json').write_text(json.dumps(perf,indent=2)+'\n')
 if args.video:
  sections=[('hyperlane','warp'),('graph','dag'),('weather','weather'),('rain','text'),('flip','text'),('genie','windows'),('petal','windows'),('prism','text')]
  proc=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','image2pipe','-framerate','60','-vcodec','png','-i','-','-an','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'Nocturne-Spatial-Atelier-60fps.mp4')],stdin=subprocess.PIPE);count=0
  try:
   for id,scene in sections:
    load(id,scene)
    for frame in range(0,150,10):
     batch=page.evaluate('''([id,start])=>{const frames=[];for(let f=start;f<start+10;f++){const a=atelierApp,m=a.model,t=f*1000/60;m.setTime(t);if(id==='hyperlane')m.camera.look(.09,.015);if(id==='graph')m.camera.orbit(.17,0);if(id==='weather'&&f===30)m.emit(90,21,'*','sparks');if(id==='weather'&&f===70)m.emit(30,23,'*','nova');if((id==='genie'||id==='petal')&&f===20)m.workspace.hide(1,t);if((id==='genie'||id==='petal')&&f===95)m.workspace.restore(1,t);if(id==='flip'&&f===120)m.playText('hide');a.paint();frames.push(document.getElementById('stage').toDataURL('image/png').split(',')[1]);}return frames;}''',[id,frame])
     for data in batch:proc.stdin.write(base64.b64decode(data));count+=1
   proc.stdin.close();assert proc.wait(timeout=45)==0
  finally:
   if proc.poll() is None:proc.kill();proc.wait()
  (OUT/'preview-report.json').write_text(json.dumps({'frames':count,'fps':60,'seconds':count/60,'source':'actual cell renderer and explicit timestamps','generatedBackgrounds':False,'physical60FpsClaim':False,'sections':[i for i,s in sections]},indent=2)+'\n')
 assert not errors,errors;b.close()
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',19)
W,H=1088,704;gap=20;label=48;sheet=Image.new('RGB',(2*W+3*gap,3*(H+label)+4*gap),'#0b1018');d=ImageDraw.Draw(sheet)
for i,(path,title) in enumerate(shots):
 x=gap+(i%2)*(W+gap);y=gap+(i//2)*(H+label+gap);d.text((x,y+12),title,font=font,fill='#d7d0c7');sheet.paste(Image.open(path).convert('RGB').resize((W,H)),(x,y+label))
sheet.save(OUT/'Nocturne-Spatial-Atelier-Contact.png');print(json.dumps({'screenshots':len(shots)+2,'video':args.video,'browserPerformance':perf,'errors':errors},indent=2))
