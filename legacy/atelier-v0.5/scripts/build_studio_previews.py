"""Record explicit-time actual cell frames, not screenshots enhanced with shaders.

Optional dependencies: Playwright/Chromium, Pillow, ffmpeg. Produces a 12-second
30-FPS MP4 plus a six-scene contact sheet. Uses no bundled or downloaded fonts.
"""
from pathlib import Path
import base64,os,subprocess,json
from playwright.sync_api import sync_playwright
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dist/studio';OUT.mkdir(exist_ok=True)
STUDIES=[('starwrite','black-creme','STARWRITE / glyphs, novae, concentric light'),('row-current','neon-dreams','ROW CURRENT / rapid center, slower neighbors'),('pivot-room','copper','PIVOT ROOM / turning light beyond the frame'),('charts','smart-dark','CHART ROOM / braille data, not pixel graphics'),('fleet','winter','FLEET / a graph with shared parents'),('typography','gold','TYPE / original segment geometry and hue motion')]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),headless=True,args=['--no-sandbox'])
 page=b.new_page(viewport={'width':1600,'height':1100});page.set_content((ROOT/'Nocturne-Studio.html').read_text());page.wait_for_function('window.nocturneStudio!==undefined');page.locator('#play').click()
 ff=subprocess.Popen(['ffmpeg','-loglevel','error','-y','-f','image2pipe','-framerate','30','-i','-','-vf','scale=1000:700:flags=lanczos','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'Nocturne-Studio.mp4')],stdin=subprocess.PIPE)
 stills=[]
 try:
  for sid,palette,title in STUDIES:
   page.locator('#reset').click();page.evaluate('(s)=>window.nocturneStudio.selectScene(s)',sid);page.locator('#palette').select_option(palette)
   if sid=='starwrite':
    page.evaluate('window.nocturneStudio.config().values.rippleOpacity=120');page.locator('#prompt').fill('light');page.locator('#prompt').dispatch_event('input');page.locator('#nova').click()
   for i in range(60):
    timeMs=i*1000//30
    encoded=page.evaluate('''({t,title})=>{const slider=document.getElementById('timeline');slider.value=t;slider.dispatchEvent(new Event('input'));const src=document.getElementById('stage');const c=document.createElement('canvas');c.width=1000;c.height=700;const ctx=c.getContext('2d');ctx.fillStyle='#111018';ctx.fillRect(0,0,1000,700);ctx.font='19px monospace';ctx.fillStyle='#d8cbbb';ctx.fillText(title,24,32);ctx.drawImage(src,0,52,1000,640);return c.toDataURL('image/png').split(',')[1];}''',dict(t=timeMs,title=title))
    png=base64.b64decode(encoded);ff.stdin.write(png)
    if i==42:
     file=OUT/(sid+'-preview.png');file.write_bytes(png);stills.append(file)
  ff.stdin.close();rc=ff.wait(timeout=30)
  if rc:raise RuntimeError('ffmpeg failed')
 finally:
  if ff.poll() is None:ff.kill();ff.wait()
 b.close()
 canvas=Image.new('RGB',(1500,1575),'#111018')
 for n,file in enumerate(stills):
  im=Image.open(file).convert('RGB').resize((750,525),Image.Resampling.LANCZOS);canvas.paste(im,((n%2)*750,(n//2)*525))
 canvas.save(OUT/'Nocturne-Studio-Contact.png')
 (OUT/'preview-record.json').write_text(json.dumps({'frames':360,'fps':30,'durationSeconds':12,'source':'actual embedded WASM cell renderer; explicit time; 6 scenes','effects':'no shader, blur or glow added','notABenchmark':True},indent=2)+'\n')
 print('Created actual-cell MP4 and contact sheet')
