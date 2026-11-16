"""Exercise the self-contained gallery using embedded HTML, without network access."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import json,hashlib,os
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dist/studio';OUT.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1600,'height':1100});errors=[];requests=[]
    page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url))
    page.set_content((ROOT/'Nocturne-Studio.html').read_text());page.wait_for_function('window.nocturneStudio!==undefined');page.locator('#play').click();t=page.evaluate('window.nocturneMetrics.timeMs')
    page.locator('#prompt').fill('waves');page.locator('#prompt').dispatch_event('input');a=page.evaluate('({...window.nocturneMetrics})');assert a['dataCount']>=1 and a['timeMs']==t
    page.locator('#value').fill('830');page.locator('#value').dispatch_event('input');assert page.evaluate('window.nocturneMetrics.value')==830;assert page.evaluate('window.nocturneMetrics.timeMs')==t
    page.locator('#feed').check();page.wait_for_timeout(180);page.locator('#feed').uncheck();assert page.evaluate('window.nocturneMetrics.dataCount')>a['dataCount'];assert page.evaluate('window.nocturneMetrics.timeMs')==t
    scenes=json.loads((ROOT/'studio.scenes.json').read_text())['scenes']
    for scene in scenes:
        page.evaluate('(id)=>window.nocturneStudio.selectScene(id)',scene['id']);assert page.locator('#error').inner_text()=='',scene['id'];page.locator('#stage').screenshot(path=str(OUT/(scene['id']+'.png')))
    # All material palettes render; this does not assert every combination is attractive.
    for palette in json.loads((ROOT/'palettes.json').read_text())['palettes']:
        page.locator('#palette').select_option(palette['id']);assert page.locator('#error').inner_text()=='',palette['id']
    page.evaluate('window.nocturneStudio.selectScene("fleet")');page.locator('#semantic button').filter(has_text='SYNTHESIS').click();assert '21' in page.locator('#inspector').inner_text() and '22' in page.locator('#inspector').inner_text()
    page.evaluate('window.nocturneStudio.selectScene("controls")');disabled=page.locator('#semantic button').filter(has_text='Destructive');assert disabled.is_disabled()
    page.locator('#modal').click();assert page.evaluate('window.nocturneMetrics.modalOpen');page.keyboard.press('Escape');assert not page.evaluate('window.nocturneMetrics.modalOpen')
    page.evaluate('window.nocturneStudio.selectScene("charts")');page.locator('#stage').focus();page.keyboard.press('Tab');page.keyboard.press('ArrowRight');assert 'sample' in page.locator('#inspector').inner_text()
    page.locator('#palette').select_option('smart-dark');page.evaluate('window.nocturneStudio.selectScene("starwrite")');page.locator('#nova').click();page.locator('#timeline').fill(str(t+1100));page.locator('#timeline').dispatch_event('input');page.screenshot(path=str(OUT/'studio-gallery.png'),full_page=True)
    assert not errors,errors;assert not requests,requests
    result={'status':'PASS','scenes':len(scenes),'palettes':48,'pausedDataUpdates':True,'disabledSelection':True,'multiParentInspection':True,'modalEscape':True,'keyboardChartInspection':True,'networkRequests':len(requests),'pageErrors':errors,'mode':'embedded HTML via set_content; local file navigation blocked by browser policy in this runtime'}
    (OUT/'browser-tests.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));browser.close()
