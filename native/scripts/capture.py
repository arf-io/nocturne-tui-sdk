#!/usr/bin/env python3
"""Every declared tick: current WASM cells + intrinsic-resolution canvas PNG + MP4.

Does not sample by wall-clock screenshots or skip ticks. Defaults to thirteen explicit
scenes, two seconds each at 60 Hz. This finite review plan is not whole-SDK approval.
"""
from pathlib import Path
import argparse,json,hashlib,base64,shutil,subprocess,os
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fps',type=int,default=60);p.add_argument('--seconds',type=float,default=2);p.add_argument('--scenes',default='autumn,rain,chrysanthemum,silk,work-graph,windows,notifications,instruments,pearl-curves,leaf-anatomy,mixed-materials,condition-console,selector-studio');a=p.parse_args()
 if not 1<=a.fps<=120 or not 0<a.seconds<=30:p.error('fps 1..120 and seconds (0,30]')
 cases=a.scenes.split(',');recipeIds={r['id']for r in json.loads((ROOT/'recipes.json').read_text())}
 if set(cases)-recipeIds:p.error('Unknown scene ID')
 target=ROOT/'evidence/capture';target.mkdir(exist_ok=True);records=[];per=int(a.seconds*a.fps);total=per*len(cases)
 if shutil.disk_usage(target).free<total*600000+300_000_000:raise RuntimeError('Insufficient free space; no frames dropped to fit')
 with sync_playwright()as p:
  browser=p.chromium.launch(headless=True,executable_path=os.environ.get('CHROMIUM')or shutil.which('chromium'),args=['--no-sandbox']);page=browser.new_page(viewport={'width':1800,'height':1300},device_scale_factor=1)
  page.set_content((ROOT/'Nocturne-Test-Harness.html').read_text());page.wait_for_function('window.nativeLab')
  for case in cases:
   page.evaluate("id=>{nativeLab.load(nativeLab.recipes.find(r=>r.id===id));nativeLab.hold(true);nativeLab.draw();}",case)
   offset={'autumn':3500000,'rain':1200000,'chrysanthemum':50000,'silk':200000,'work-graph':900000,'windows':900000}.get(case,0)
   for tick in range(per):
    timeUs=offset+tick*1_000_000//a.fps
    result=page.evaluate("us=>{const s=nativeLab.scene;s.command({op:'pause',paused:false});s.advanceTo(us);s.command({op:'pause',paused:true});nativeLab.draw();const f=nativeView.frame;let raw='';for(let i=0;i<f.bytes.length;i+=16384)raw+=String.fromCharCode(...f.bytes.subarray(i,i+16384));return {png:canvas.toDataURL('image/png').split(',')[1],cells:btoa(raw),width:canvas.width,height:canvas.height};}",timeUs)
    index=len(records);prefix=f'frame-{index:06d}';png=base64.b64decode(result['png']);cells=base64.b64decode(result['cells']);(target/(prefix+'.png')).write_bytes(png);(target/(prefix+'.cells')).write_bytes(cells)
    records.append({'scene':case,'tick':tick,'timeUs':timeUs,'png':prefix+'.png','cells':prefix+'.cells','width':result['width'],'height':result['height'],'pngSha256':hashlib.sha256(png).hexdigest(),'cellsSha256':hashlib.sha256(cells).hexdigest()})
   print(case,per,'frames',flush=True)
  browser.close()
 video=target/'Nocturne-RC4-Source-Build.mp4'
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-framerate',str(a.fps),'-i',str(target/'frame-%06d.png'),'-frames:v',str(len(records)),'-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(video)],check=True)
 probe=subprocess.run(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames,width,height,avg_frame_rate','-of','json',str(video)],capture_output=True,text=True,check=True)
 metadata=json.loads(probe.stdout);assert int(metadata['streams'][0]['nb_read_frames'])==len(records)
 report={'scope':'Finite declared-scene review sampled from actual current WASM; every declared tick retained. Human full optical acceptance not implied.','fps':a.fps,'frames':records,'video':metadata,'videoSha256':hashlib.sha256(video.read_bytes()).hexdigest()}
 (target/'MANIFEST.json').write_text(json.dumps(report,indent=2)+'\n');print(len(records),'frames; ffprobe confirms exact frame count')
if __name__=='__main__':main()
