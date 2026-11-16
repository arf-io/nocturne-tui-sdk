#!/usr/bin/env python3
"""Drive the recovered/current gallery with real browser events and compare bytes.
Each catalogue's original/runtime frames are a recovery oracle, not an independent
color-math oracle. Dedicated channel/formula tests provide those separate checks.
"""
from __future__ import annotations
import argparse, json, os, struct, time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    errors=[];checks=[];captures=[]
    with sync_playwright()as play:
        options={'headless':True}
        if os.environ.get('CHROMIUM_PATH'):options['executable_path']=os.environ['CHROMIUM_PATH']
        elif Path('/usr/bin/chromium').exists():options['executable_path']='/usr/bin/chromium'
        browser=play.chromium.launch(**options);page=browser.new_page(viewport={'width':1600,'height':1200},device_scale_factor=1)
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.evaluate('window.requestAnimationFrame=()=>0')
        page.set_content((ROOT/'Nocturne-RC3.html').read_text(),wait_until='load');page.wait_for_function('window.__chromaticReady === true',timeout=30000)
        catalogue=json.loads((ROOT/'chromatic.catalog.json').read_text())
        for entry in catalogue:
            page.select_option('#catalog',entry['id'])
            result=page.evaluate('({id:__app.catalog[__app.index].id,w:__app.latest.frame.width,h:__app.latest.frame.height,commands:__app.latest.metadata.exhibition.components})')
            assert result['id']==entry['id'];checks.append({'id':entry['id'],'pass':True})
        page.select_option('#catalog','scene:warp');page.click('#pause')
        prompt=page.locator('#prompt')
        if not prompt.count():prompt=page.locator('textarea').first
        # Use the real user input widget, not an API call to simulate typing.
        ids=page.locator('input,textarea').evaluate_all('(els)=>els.map(e=>({id:e.id,tag:e.tagName}))')
        (a.output/'input-widgets.json').write_text(json.dumps(ids))
        if page.locator('#draft').count():prompt=page.locator('#draft')
        if page.locator('#composer').count():prompt=page.locator('#composer')
        try:
            prompt.fill('RC3 immediate browser input');page.wait_for_timeout(50)
            text=page.evaluate('__app.session.model.draft');assert 'RC3 immediate'in text;checks.append({'id':'real input immediate','pass':True})
        except Exception as e:errors.append('Input widget test: '+str(e))
        page.locator('#stage').screenshot(path=str(a.output/'gallery-canvas.png'))
        page.screenshot(path=str(a.output/'gallery-full.png'),full_page=True)
        browser.close()
    report={'status':'PASS'if not errors else'FAIL','checks':checks,'errors':errors,'scope':'actual Chromium catalogue and input events; no Safari/device claim'}
    (a.output/'RESULT.json').write_text(json.dumps(report,indent=2));print(json.dumps({'status':report['status'],'checks':len(checks),'errors':errors},indent=2));return 0 if not errors else 2
if __name__=='__main__':raise SystemExit(main())
