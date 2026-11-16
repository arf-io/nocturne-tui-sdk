#!/usr/bin/env python3
"""Exercise native selector semantics through real Chromium pointer/keyboard events.

Inputs: freshly built self-contained gallery and an installed Chromium executable.
Outputs: selector-browser.json, console checks, and an actual native-canvas PNG.
Exit 0 only when every assertion passes. This is not target-platform/art approval.
Example: python3 native/scripts/check_selectors_browser.py
"""
from pathlib import Path
import base64, hashlib, json, os, shutil
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

def main():
    records, errors, requests = [], [], []
    html = ROOT / 'Nocturne-Test-Harness.html'
    with sync_playwright() as playwright:
        executable = os.environ.get('CHROMIUM') or shutil.which('chromium') or shutil.which('google-chrome')
        browser = playwright.chromium.launch(headless=True, executable_path=executable, args=['--no-sandbox'])
        page = browser.new_page(viewport={'width': 1440, 'height': 1100}, device_scale_factor=1)
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('request', lambda request: requests.append(request.url))
        page.set_content(html.read_text())
        page.wait_for_function('window.nativeLab !== undefined', timeout=30000)
        def check(name, condition):
            try:
                if not condition():
                    raise AssertionError(name)
                records.append({'name': name, 'status': 'PASS'})
            except Exception as error:
                records.append({'name': name, 'status': 'FAIL', 'reason': str(error)})
            print(records[-1]['status'], name, flush=True)
        def command(value):
            page.evaluate('c=>{nativeLab.scene.command(c);nativeLab.draw();}', value)
        def entry():
            return page.evaluate('nativeLab.scene.info().registeredStates.find(r=>r.id===1)')
        def moveCell(x, y):
            page.locator('#canvas').scroll_into_view_if_needed()
            rect = page.locator('#canvas').bounding_box()
            size = page.evaluate('[nativeView.frame.width,nativeView.frame.height]')
            page.mouse.move(rect['x'] + (x+.5)*rect['width']/size[0], rect['y'] + (y+.5)*rect['height']/size[1])
        # The fixture uses the public core independently of the gallery's new recipe.
        page.evaluate("()=>{nativeLab.hold();nativeLab.scene.command({op:'reset',seed:2030});nativeLab.hold();nativeLab.draw();}")
        for c in [
            {'op':'environment','stars':0,'style':'solid'},
            {'op':'widget','id':1,'kind':'button','x':8,'y':8,'width':42,'height':5,'text':'Native hover / selected / pressed','material':1,'alpha':.2},
            {'op':'state-register','id':1,'path':'/test/button','role':'control','target':{'family':'widget','id':1}},
            {'op':'style-rule','id':1,'selector':{'family':'widget','states':{'hover':True}},'style':{'material':2},'priority':10},
            {'op':'style-rule','id':2,'selector':{'family':'widget','states':{'pressed':True}},'style':{'material':3},'priority':20},
        ]: command(c)
        camera = page.evaluate('nativeLab.scene.info().camera')
        moveCell(15,10)
        check('passive pointer movement reaches native hover', lambda: entry()['states']['hover'])
        check('hover rule changes resolved material', lambda: entry()['effective']['material']==2)
        check('passive movement does not alter camera', lambda: page.evaluate('nativeLab.scene.info().camera')==camera)
        page.mouse.down()
        check('pointer press comes from native hit owner', lambda: entry()['states']['pressed'] and entry()['effective']['material']==3)
        page.mouse.up()
        check('release clears pressed but retains hover', lambda: not entry()['states']['pressed'] and entry()['states']['hover'])
        check('selection toggles through the native button', lambda: entry()['states']['selected'])
        page.mouse.move(1,1)
        check('leaving canvas clears native hover', lambda: not entry()['states']['hover'] and entry()['effective']['material']==1)
        moveCell(15,10);page.mouse.down()
        page.evaluate("window.dispatchEvent(new Event('blur'))")
        check('window blur cancels capture and native pressed state', lambda: not entry()['states']['pressed'] and not entry()['states']['hover'])
        page.mouse.up()
        command({'op':'pointer','phase':'cancel','x':-1,'y':-1})
        command({'op':'define','path':'/load','value':25})
        command({'op':'style-rule','id':3,'selector':{'family':'widget','path':'/test/button'},'style':{'alpha':{'path':'/load','inputMin':0,'inputMax':100,'outputMin':.1,'outputMax':.9}}})
        check('native map resolves continuous alpha', lambda: abs(entry()['effective']['alpha']-.3)<1e-9)
        page.evaluate('window.selectorSnapshot=nativeLab.scene.snapshot();for(let i=0;i<8;i++){nativeLab.draw();nativeLab.scene.info();}')
        check('render and metadata leave complete snapshot byte-identical', lambda: page.evaluate('nativeLab.scene.snapshot().every((v,i)=>v===selectorSnapshot[i])'))
        command({'op':'widget','id':1,'alpha':.4})
        check('base edit survives under appearance override', lambda: entry()['authored']['alpha']==.4 and abs(entry()['effective']['alpha']-.3)<1e-9)
        command({'op':'remove-style-rule','id':3})
        check('rule removal exposes latest authored alpha', lambda: entry()['effective']['alpha']==.4)
        check('all interaction leaves held simulation unchanged', lambda: page.evaluate('nativeLab.scene.info().clock.timeUs')==0)
        found = page.evaluate("nativeLab.recipes.some(r=>r.id==='selector-studio')")
        check('Selector Studio is an actual native recipe', lambda: found)
        if found:
            page.locator('#selector-panel').evaluate('(element)=>element.open=true')
            page.locator('#selector-open').click()
            page.evaluate('nativeLab.hold();nativeLab.draw();')
            page.locator('#selector-load').fill('75')
            page.locator('#selector-fault').select_option('1')
            page.locator('#selector-set').click()
            check('companion controls commit native values and guarded appearance', lambda: entry()['effective']['material']==6)
            check('companion panel shows native inspection data', lambda: '/studio/controls/one' in page.locator('#selector-state').inner_text())
            check('load changes native gauge alpha without base mutation', lambda: page.evaluate("(()=>{let r=nativeLab.scene.info().registeredStates.find(r=>r.id===20);return Math.abs(r.effective.alpha-.7)<1e-9&&r.authored.alpha===.1;})()"))
            page.locator('#selector-base').click()
            check('authoring button changes base under alarm override', lambda: entry()['authored']['material']==3 and entry()['effective']['material']==6)
            page.locator('#selector-remove').click()
            check('remove controls expose authored color without replaying scene', lambda: entry()['effective']['material']==3 and page.evaluate('nativeLab.scene.info().styleRules.length')==0)
            page.locator('#draft').fill('Accepted input stays immediate with selectors.')
            check('draft input stays immediate during held selector presentation', lambda: page.evaluate("nativeLab.scene.info().prompt.text==='Accepted input stays immediate with selectors.'"))
            page.locator('#selector-open').click();page.evaluate('nativeLab.hold();nativeLab.draw();')
            moveCell(20,13)
            page.mouse.down();page.mouse.up();moveCell(65,13)
            png = page.evaluate("canvas.toDataURL('image/png').split(',')[1]")
            path = ROOT/'evidence/screens/selector-studio.png';path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(base64.b64decode(png))
        check('no page exceptions', lambda: not errors)
        check('no requests for providers, fonts or external assets', lambda: not requests)
        browser.close()
    result = {'scope':'Actual Chromium events through shipped HTML and C/WASM selectors; blur dispatched as a focus-lifecycle event. Not a physical platform/art acceptance.', 'htmlSha256':hashlib.sha256(html.read_bytes()).hexdigest(), 'checks':records,'errors':errors,'requests':requests,'passed':all(r['status']=='PASS' for r in records)}
    (ROOT/'evidence/selector-browser.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'checks':len(records),'passed':result['passed']},indent=2))
    return 0 if result['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
