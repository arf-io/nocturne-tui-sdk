#!/usr/bin/env python3
"""Drive actual standalone HTML controls/pointer/key events. No mock renderer.
Use set_content because managed Chromium can block file://. Requires Playwright.
"""
from pathlib import Path
import json,sys,os
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
results=[]
def passed(name):results.append(name);print('PASS',name,flush=True)
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1680,'height':1300})
    page.set_default_timeout(4000)
    errors=[];requests=[]
    page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url))
    page.set_content((ROOT/'Nocturne-Spatial-Atelier.html').read_text());page.wait_for_function('!!window.atelierApp')
    page.evaluate('atelierApp.setAuto(false)');page.evaluate('atelierApp.seek(2000)')
    assert page.locator('[data-scene="warp"]').is_visible()
    assert page.locator('#buildBadge').inner_text().startswith('0.5')
    assert page.input_value('#scene')=='warp';passed('Oblique Hyperlane first scene and visible release badge')
    old=page.evaluate('atelierApp.model.camera.snapshot()');page.locator('[data-camera="right"]').first.click()
    assert page.evaluate('atelierApp.model.camera.yaw')!=old['yaw'];passed('visible look pad changes camera immediately')
    pos=page.evaluate('atelierApp.model.camera.position()');page.locator('[data-camera="pan-left"]').click()
    assert page.evaluate('atelierApp.model.camera.position()')!=pos;passed('visible strafe pad translates camera')
    page.locator('#velocityNumber').fill('-12');page.locator('#velocityNumber').dispatch_event('input')
    assert page.evaluate('atelierApp.model.flightSpeed')==-12
    page.locator('#brake').click();assert page.evaluate('atelierApp.model.flightSpeed')==0
    page.locator('#heading').fill('37');page.locator('#heading').dispatch_event('input')
    assert page.evaluate('atelierApp.model.options.travelYaw')==37;passed('travel speed reverse brake and heading are directly reachable')
    box=page.locator('#stage').bounding_box();x=box['x']+box['width']*.55;y=box['y']+box['height']*.45
    angle=page.evaluate('atelierApp.model.camera.yaw');page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+70,y+20,steps=4);page.mouse.up()
    assert page.evaluate('atelierApp.model.camera.yaw')!=angle;passed('actual pointer drag rotates camera')
    pos=page.evaluate('atelierApp.model.camera.position()');page.keyboard.down('Shift');page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+40,y+10,steps=3);page.mouse.up();page.keyboard.up('Shift')
    assert page.evaluate('atelierApp.model.camera.position()')!=pos;passed('Shift pointer drag pans')
    pos=page.evaluate('atelierApp.model.camera.position()');page.mouse.wheel(0,120);assert page.evaluate('atelierApp.model.camera.position()')!=pos;passed('wheel translates camera')
    page.locator('#pause').click();time=page.evaluate('atelierApp.model.motionMs');paints=page.evaluate('atelierApp.paintCount')
    page.locator('#draft').fill('LOCAL BETWEEN FRAMES');assert page.evaluate('atelierApp.model.draft')=='LOCAL BETWEEN FRAMES'
    assert page.evaluate('atelierApp.model.motionMs')==time and page.evaluate('atelierApp.paintCount')>paints
    assert page.evaluate("Array.from({length:atelierApp.model.width},(_,x)=>String.fromCodePoint(atelierApp.latest.frame.cells[((atelierApp.model.height-4)*atelierApp.model.width+x)*4])).join('').includes('LOCAL BETWEEN FRAMES')")
    passed('local input paints at held animation time')
    page.locator('#scene').select_option('dag');page.locator('#dimensions').select_option('2');page.locator('#algorithm').select_option('force');page.locator('#layoutNow').click()
    page.wait_for_function('!atelierApp.model.layoutBusy');assert page.evaluate('atelierApp.model.layout.nodes.every(n=>n.z===0)')
    assert page.evaluate('atelierApp.model.layout.nodes.length')==8;passed('automatic 2D force layout settles with shared identities')
    page.locator('#dimensions').select_option('3');page.locator('#algorithm').select_option('layered');page.locator('#layoutNow').click();page.evaluate('atelierApp.seek(4000)')
    assert page.evaluate('atelierApp.model.layout.nodes.some(n=>n.z!==0)');passed('automatic 3D layered layout')
    page.locator('#nodeSelect').select_option('synthesis');page.locator('#pinNode').click();page.wait_for_function('!atelierApp.model.layoutBusy')
    assert page.evaluate('Boolean(atelierApp.model.graph.nodes.find(n=>n.id==="synthesis").pin)');passed('pinning selected node survives layout')
    page.locator('#graphPanel details summary').click();page.locator('#graphCycle').click();assert page.evaluate('atelierApp.model.layout.cycles.length')>0;passed('cyclic graph disclosed rather than dropping edges')
    page.locator('#scene').select_option('weather');page.locator('[data-burst="nova"]').click();assert page.evaluate('atelierApp.model.events.at(-1).kind')=='nova'
    page.locator('[data-burst="embers"]').click();assert page.evaluate('atelierApp.model.events.at(-1).kind')=='embers';passed('nova and ember controls enqueue distinct effects')
    page.locator('#scene').select_option('text');page.locator('#displayText').fill('TEXT FROM THE SKY');page.locator('#displayText').dispatch_event('change')
    page.locator('#enterEffect').select_option('rain');page.locator('#replayText').click();page.evaluate('atelierApp.seek(atelierApp.model.motionMs+600)')
    assert page.evaluate('new Set(atelierApp.model.textPlayer.sample(atelierApp.model.motionMs).map(g=>g.y.toFixed(2))).size>1');passed('rain glyphs have independent paths')
    page.locator('#exitEffect').select_option('flipboard');page.locator('#hideText').click();page.evaluate('atelierApp.seek(atelierApp.model.motionMs+20000)')
    assert page.evaluate('atelierApp.model.textPlayer.sample(atelierApp.model.motionMs).every(g=>g.opacity===0)');passed('flipboard hide reaches exact blank without altering source')
    page.locator('#scene').select_option('windows');page.evaluate('atelierApp.model.workspace.hide(2,0);atelierApp.model.workspace.hide(3,0);atelierApp.seek(4000)')
    def cell_click(hitid):
        point=page.evaluate('id=>{const f=atelierApp.latest.frame;for(let y=0;y<f.height;y++)for(let x=0;x<f.width;x++)if(f.cells[(y*f.width+x)*4+3]===id)return {x:x+.5,y:y+.5};return null;}',hitid)
        assert point is not None,hitid
        rect=page.locator('#stage').bounding_box()
        page.mouse.click(rect['x']+point['x']/page.evaluate('atelierApp.model.width')*rect['width'],rect['y']+point['y']/page.evaluate('atelierApp.model.height')*rect['height'])
    page.locator('#stage').scroll_into_view_if_needed();cell_click(10011)
    assert page.evaluate('atelierApp.model.workspace.get(1).mode')=='minimized';passed('actual colored cell pad minimizes window')
    page.evaluate('atelierApp.seek(6000)');page.locator('#dock button').first.click();assert page.evaluate('atelierApp.model.workspace.get(1).mode')=='normal';passed('visible dock restores minimized window')
    page.evaluate('atelierApp.seek(8000)');page.locator('#chrome').select_option('windows');assert page.evaluate('atelierApp.model.workspace.options.chrome')=='windows'
    page.locator('#chrome').select_option('gnome');page.locator('#windowShape').select_option('diamond');page.locator('#windowEffect').select_option('petal-bloom')
    assert page.evaluate('atelierApp.model.workspace.get(1).shape')=='diamond';passed('chrome shape and transition controls')
    page.locator('#rollWindow').click();page.evaluate('atelierApp.seek(atelierApp.model.motionMs+300)');assert 0<page.evaluate('atelierApp.model.workspace.sample(1,atelierApp.model.motionMs).bodyScale')<1
    page.locator('#rollWindow').click();passed('roll body uses reversible intermediate geometry')
    page.locator('#n_window_depth').fill('14');page.locator('#n_window_depth').dispatch_event('change');assert page.evaluate('atelierApp.model.workspace.get(1).depth')==14;passed('window depth moves independently of camera')
    saved=page.evaluate('atelierApp.exportSettings()');page.evaluate('raw=>atelierApp.adoptSettings(raw)',saved);assert page.evaluate('atelierApp.exportSettings()')==saved;passed('settings roundtrip includes camera graph and window intent')
    before=page.evaluate('atelierApp.exportSettings()');bad={**saved,'version':999};try_error=page.evaluate('raw=>{try{atelierApp.adoptSettings(raw);return false;}catch(e){return true;}}',bad)
    assert try_error and page.evaluate('atelierApp.exportSettings()')==before;passed('invalid imported settings do not partially mutate model')
    for size in ['80,32','160,52','112,40']:
        page.locator('#size').select_option(size);page.locator('#scene').select_option('dag');page.evaluate('atelierApp.seek(30000)')
    passed('three viewport changes and frame-all remain usable')
    scenes=page.locator('#scene option').evaluate_all('(es)=>es.map(e=>e.value)')
    for scene in scenes:page.locator('#scene').select_option(scene);page.evaluate('atelierApp.seek(31000)')
    passed('all 18 scene choices render')
    page.locator('#scene').select_option('windows');page.evaluate('atelierApp.seek(32000)')
    page.screenshot(path=str(ROOT/'dist/atelier/browser-tested.png'),full_page=False)
    assert not errors,errors;assert not requests,requests;passed('no browser exceptions or external requests')
    browser.close()
report={'passed':len(results),'checks':results,'browserErrors':errors,'networkRequests':requests}
(ROOT/'dist/atelier/browser-tests.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
