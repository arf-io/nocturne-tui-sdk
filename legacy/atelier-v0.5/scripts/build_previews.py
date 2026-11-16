"""Record actual WASM cell output at 30 FPS. No browser-only material effects."""
from pathlib import Path
import base64
import json
import os
import subprocess
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dist'
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'), headless=True, args=['--no-sandbox'])
    page = browser.new_page(viewport={'width':1440,'height':1160}, device_scale_factor=1)
    page.set_content((ROOT/'Nocturne-Gallery.html').read_text(), wait_until='load')
    page.wait_for_function('window.__nocturne !== undefined')
    page.evaluate('''() => {
      const n=window.__nocturne; n.setPlaying(false);
      const out=document.createElement('canvas');out.width=1440;out.height=1160;
      const ctx=out.getContext('2d');
      const tile=document.createElement('canvas');
      window.drawRecordingFrame=(frameIndex)=>{
        const t=6000+Math.floor(frameIndex*1000/30),secondHalf=frameIndex>=180;
        const indices=secondHalf?[1,3,9,15]:[0,5,8,10];
        ctx.fillStyle='#11100E';ctx.fillRect(0,0,out.width,out.height);
        ctx.fillStyle='#D6CCBC';ctx.font='34px Georgia';ctx.fillText('NOCTURNE  /  prompting surfaces',32,52);
        ctx.fillStyle='#A9BDB3';ctx.font='14px monospace';
        ctx.fillText('ACTUAL TERMINAL CELLS  ·  30 FPS MOTION  ·  BRAILLE / BLOCKS / TRUE COLOR',33,82);
        indices.forEach((index,j)=>{
          const preset=n.PRESETS[index],config=n.presetConfig(preset,84,28);
          config.values.valuePermille=Math.round(500+450*Math.sin(t/750));
          const frame=n.engine.render(config,t,preset.text||'Make something that feels alive.');
          n.paint(tile,frame,8,16);
          const x=32+(j%2)*704,y=136+Math.floor(j/2)*514;
          ctx.fillStyle='#D6CCBC';ctx.font='18px Georgia';ctx.fillText(preset.name,x,y-18);
          ctx.drawImage(tile,x,y,672,448);
          ctx.strokeStyle='#39342C';ctx.lineWidth=1;ctx.strokeRect(x-.5,y-.5,673,449);
        });
        ctx.fillStyle='#968C7E';ctx.font='13px monospace';
        ctx.fillText('Warm near-black. Pastel peaks. Coordinate-anchored stars. No raster shaders or simulated glow.',32,1130);
        return out.toDataURL('image/png').split(',')[1];
      };
    }''')
    (OUT/'Nocturne-Studies.png').write_bytes(base64.b64decode(page.evaluate('window.drawRecordingFrame(0)')))
    (OUT/'Nocturne-Studies-II.png').write_bytes(base64.b64decode(page.evaluate('window.drawRecordingFrame(180)')))
    encoder=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','image2pipe','-framerate','30','-i','pipe:0','-c:v','libx264','-preset','fast','-crf','18','-threads','2','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'Nocturne-Studies.mp4')],stdin=subprocess.PIPE)
    try:
        for start in range(0,360,12):
            images=page.evaluate('(start)=>Array.from({length:12},(_,offset)=>window.drawRecordingFrame(start+offset))',start)
            for image in images:encoder.stdin.write(base64.b64decode(image))
        encoder.stdin.close()
        if encoder.wait(timeout=30)!=0:raise RuntimeError('ffmpeg failed')
    finally:
        if encoder.poll() is None:encoder.kill();encoder.wait()
    browser.close()
(OUT/'preview-provenance.json').write_text(json.dumps({'source':'C kernel compiled to WASM; actual glyph/foreground/background cells','capture':'Chromium canvas cell renderer','frames':360,'fps':30,'seconds':12,'browserOnlyMaterialEffects':False,'data':'synthetic demo values'},indent=2)+'\n')
print('Created two contact sheets and a 12-second 30 FPS MP4 from actual cells.')
