"""Exercise the local, self-contained gallery with Chromium through Playwright."""
from pathlib import Path
import json
import os
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':1080},device_scale_factor=1)
    errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.set_content((ROOT/'Nocturne-Gallery.html').read_text(), wait_until='load')
    page.wait_for_function('window.__nocturne !== undefined')
    page.evaluate('window.__nocturne.setPlaying(false)')
    page.screenshot(path=str(ROOT/'dist/gallery-top.png'))
    page.evaluate('window.__nocturne.renderAt(10, 6000)')
    before=page.evaluate('window.__nocturne.getState()')
    page.locator('#promptInput').fill('data arrives between animation frames')
    after=page.evaluate('window.__nocturne.getState()')
    assert after['lastMotionMs']==before['lastMotionMs']
    assert after['motionSamples']==before['motionSamples']
    assert after['dataCommits']>before['dataCommits']
    assert after['frame']!=before['frame']
    page.locator('#valuePermille').fill('940')
    value=page.evaluate('window.__nocturne.getState()')
    assert value['lastMotionMs']==before['lastMotionMs']
    assert value['frame']!=after['frame']
    page.locator('#feed').check()
    page.wait_for_timeout(150)
    fed=page.evaluate('window.__nocturne.getState()')
    assert fed['dataCommits']>value['dataCommits']+2
    assert fed['motionSamples']==value['motionSamples']
    page.locator('#feed').uncheck()
    page.locator('#width').fill('120')
    page.locator('#height').fill('35')
    resized=page.evaluate('window.__nocturne.getState()')
    assert len(resized['frame'])==120*35*4
    page.evaluate('window.__nocturne.renderAt(0,6000)')
    page.screenshot(path=str(ROOT/'dist/gallery-top.png'))
    page.evaluate('window.__nocturne.renderAt(10,6000)')
    page.screenshot(path=str(ROOT/'dist/gallery-controls.png'))
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors,errors
    results={'checks':['self-contained document executes','no browser exceptions','paused typing redraw','paused data redraw','independent data stream','resize geometry','mobile width'],'passed':True,'errors':errors}
    (ROOT/'dist/browser-test-results.json').write_text(json.dumps(results,indent=2))
    print(json.dumps(results,indent=2))
    browser.close()
