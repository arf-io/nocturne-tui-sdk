"""Exercise the shipped self-contained bytes; no network or imagined screenshots."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import json,os
ROOT=Path(__file__).resolve().parents[1]
def main():
 checks=[];errors=[];requests=[]
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),headless=True,args=['--no-sandbox'])
  page=browser.new_page(viewport={'width':1540,'height':1100});page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url))
  page.set_content((ROOT/'Nocturne-Observatory.html').read_text(),wait_until='load');page.wait_for_function('window.observatoryApp !== undefined',timeout=30000);page.evaluate('observatoryApp.setAuto(false)');checks.append('self-contained initialization and 16 thumbnails')
  assert page.locator('#scenes button').count()==16
  result=page.evaluate('''()=>{const a=observatoryApp;a.model.configure({motion:false});a.clock.setPaused(true,performance.now());a.model.setTime(a.clock.timeMs);a.paint();const t=a.model.motionMs,b=a.inputCount;const d=document.getElementById('draft');d.value='instant local ink';d.dispatchEvent(new Event('input',{bubbles:true}));const node=a.latest.nodes.find(n=>n.text==='instant local ink');return {timeSame:t===a.model.motionMs,commits:a.inputCount-b,opacity:node.fgOpacity,reveal:node.revealMs||0}}''')
  assert result=={'timeSame':True,'commits':1,'opacity':1000,'reveal':0},result;checks.append('DOM input commits and paints synchronously at frozen motion time')
  before=page.evaluate('observatoryApp.model.motionMs');page.locator('#n_fps').fill('30');page.locator('#n_fps').dispatch_event('change');page.locator('#n_fps').fill('60');page.locator('#n_fps').dispatch_event('change');assert page.evaluate('observatoryApp.model.motionMs')==before;checks.append('FPS control changes no animation time')
  page.locator('#n_gradientScreens').fill('2');page.locator('#n_gradientScreens').dispatch_event('change');assert page.evaluate('observatoryApp.model.options.gradientScreens')==2;page.locator('#stopWidths').fill('1, 2, .5');page.locator('#stopWidths').dispatch_event('change');assert page.evaluate('observatoryApp.model.options.stopWidths')==[1,2,.5];checks.append('screen-sized nonuniform stop spacing')
  page.locator('#commands').click();page.locator('#stage').press('w');page.locator('#stage').press('a');page.locator('#stage').press('r');page.locator('#stage').press('p');page.locator('#stage').press('Enter');assert page.evaluate('observatoryApp.model.scene')=='warp';assert not page.evaluate('observatoryApp.model.showPalette');checks.append('command palette filters and keyboard activates')
  page.locator('#stage').press('Alt+ArrowRight');assert page.evaluate('observatoryApp.model.options.cameraYaw')==3;checks.append('XYZ keyboard camera rotation')
  for scene in page.locator('#scene option').evaluate_all('(a)=>a.map(x=>x.value)'):
   page.locator('#scene').select_option(scene);assert page.locator('#error').inner_text()==''
  checks.append('all 16 workspace selectors')
  for palette in page.locator('#palette option').evaluate_all('(a)=>a.map(x=>x.value)'):
   page.locator('#palette').select_option(palette);assert page.locator('#error').inner_text()==''
  checks.append('all 48 palette controls')
  page.locator('#palette').select_option('smart-dark');page.locator('#scene').select_option('bbs-config');assert page.locator('#semantics button:disabled').count()>=1;checks.append('disabled controls have non-activatable companion buttons')
  page.locator('#scene').select_option('controls');page.locator('#stage').focus();page.locator('#stage').press('Tab');assert page.evaluate('observatoryApp.model.focusId')>0;assert page.evaluate('observatoryApp.latest.nodes.some(n=>n.id===observatoryApp.model.focusId&&n.state===2)');checks.append('keyboard focus receives selected cell treatment')
  page.locator('#scene').select_option('windows');page.evaluate('''()=>{const a=observatoryApp;a.model.toggleWindow(0,'maximized');a.model.setTime(a.model.motionMs+560);a.paint()}''');assert page.evaluate('observatoryApp.model.windowProgress(observatoryApp.model.windows[0])')==1;page.evaluate('''()=>{const a=observatoryApp;a.model.toggleWindow(0,'maximized');a.model.setTime(a.model.motionMs+560);a.paint()}''');checks.append('window expansion and collapse endpoints')
  page.evaluate('observatoryApp.clock.seek(observatoryApp.model.motionMs,performance.now())');box=page.locator('#stage').bounding_box();assert box
  x=box['x']+8*box['width']/136;y=box['y']+7.4*box['height']/44;old=page.evaluate('observatoryApp.model.windows[0].x');page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+35,y+15,steps=4);page.mouse.up();assert page.evaluate('observatoryApp.model.windows[0].x')!=old;checks.append('pointer title drag changes window position')
  page.locator('#scene').select_option('nano');page.locator('#editor').fill('First line\nSecond line');assert page.evaluate('observatoryApp.model.editor')=='First line\nSecond line';page.locator('#stage').focus();page.locator('#stage').press('End');page.locator('#stage').press('x');page.locator('#stage').press('Backspace');assert page.evaluate('observatoryApp.model.editor')=='First line\nSecond line';checks.append('scratch editor renders text and corrects it immediately')
  page.locator('#source').fill('demo.audio');page.locator('#bind').click();assert page.evaluate('observatoryApp.model.bus.bindings.length')==1;page.locator('#clearRoutes').click();assert page.evaluate('observatoryApp.model.bus.bindings.length')==0;checks.append('explicit modulation route install and removal')
  for width,height in [(36,18),(80,28),(144,48),(240,100)]:
   page.evaluate('(s)=>{observatoryApp.model.resize(...s);observatoryApp.paint()}',[width,height])
  checks.append('four geometry extremes render without exception')
  for recipe in page.locator('#recipe option').evaluate_all('(a)=>a.map(x=>x.value).filter(Boolean)'):
   page.locator('#recipe').select_option(recipe);assert page.locator('#error').inner_text()==''
  checks.append('all 12 authored recipes apply through actual controls')
  assert not requests,requests;assert not errors,errors;checks.append('no network requests or uncaught browser errors')
  browser.close()
 report={'status':'PASS','checks':checks,'count':len(checks),'physicalAudioTested':False,'realAgentsConnected':False};(ROOT/'dist/observatory/browser-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
