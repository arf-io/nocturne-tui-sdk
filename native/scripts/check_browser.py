#!/usr/bin/env python3
"""Exercise exact standalone bytes in Chromium. Native-cell time, real pointer and keyboard input."""
from pathlib import Path
import json,os,shutil,hashlib,traceback,time
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
def motionControlsClearOfCanvas(page):
    """Accept the authored right/bottom layouts without hiding the artwork."""
    return page.evaluate("""()=>{
      const canvas=document.querySelector('#canvas').getBoundingClientRect();
      const controls=document.querySelector('#motion-panel').getBoundingClientRect();
      const visible=canvas.width>0&&canvas.height>0&&canvas.left>=0&&canvas.top>=0&&canvas.right<=innerWidth&&canvas.bottom<=innerHeight;
      const contained=controls.width>0&&controls.height>0&&controls.left>=0&&controls.right<=innerWidth&&document.documentElement.scrollWidth<=innerWidth;
      return visible&&contained&&(controls.left>=canvas.right||controls.top>=canvas.bottom);
    }""")

def main():
    records=[];errors=[];requests=[]
    html=ROOT/'Nocturne-Test-Harness.html';screens=ROOT/'evidence/screens';screens.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as p:
        exe=os.environ.get('CHROMIUM') or shutil.which('chromium') or shutil.which('google-chrome')
        browser=p.chromium.launch(headless=True,executable_path=exe,args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':1440,'height':1100},device_scale_factor=1)
        page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url))
        # This environment disables file:// navigation; set_content runs the exact shipped bytes.
        page.set_content(html.read_text());page.wait_for_function('window.nativeLab !== undefined',timeout=30000)
        def check(name,fn):
            try:
                value=fn()
                if value is False:raise AssertionError(name)
                records.append({'name':name,'status':'PASS'});print('PASS',name,flush=True)
            except Exception as e:records.append({'name':name,'status':'FAIL','reason':str(e)});print('FAIL',name,str(e),flush=True)
        def js(text,arg=None):return page.evaluate(text,arg)
        def load(name):js("id=>{nativeLab.load(nativeLab.recipes.find(r=>r.id===id));nativeLab.hold(true);nativeLab.draw();}",name)
        expectedBuild=json.loads((ROOT.parent/'RELEASE.json').read_text())['build']
        check('WASM current-source build loaded',lambda:js("expected=>nativeLab.scene.info().build===expected",expectedBuild))
        load('silk');page.locator('#draft').fill('abcdef');t=js('nativeLab.scene.info().clock.timeUs')
        page.locator('#draft').press('Control+a');page.locator('#draft').press_sequentially('X')
        check('Ctrl-A inserts at true start',lambda:js("nativeLab.scene.info().prompt.text==='Xabcdef'"))
        page.locator('#draft').press('Control+e');page.locator('#draft').press_sequentially('Z')
        check('Ctrl-E inserts at true end',lambda:js("nativeLab.scene.info().prompt.text==='XabcdefZ'"))
        check('held typing does not advance simulation time',lambda:js('nativeLab.scene.info().clock.timeUs')==t)
        check('one immutable impulse per visible insertion',lambda:js("nativeLab.scene.info().fieldCount>=8"))
        for mode in ['grow','vim-inline','vim-full','marquee']:
            page.locator('#prompt-mode').select_option(mode)
            check('view preserves exact text '+mode,lambda:js("nativeLab.scene.info().prompt.text==='XabcdefZ'"))
        check('full-opacity local ink remains in frame',lambda:js("Array.from(nativeView.frame.cells).filter((v,i)=>i%4===1&&v===0xe4dacc).length>=8"))
        load('flight');js('nativeLab.advance(1000000);nativeLab.draw()')
        before=js('nativeLab.scene.info()');page.locator('#canvas').scroll_into_view_if_needed();rect=page.locator('#canvas').bounding_box()
        x=rect['x']+rect['width']*.68;y=rect['y']+rect['height']*.3
        page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+70,y+24,steps=6);page.mouse.up()
        after=js('nativeLab.scene.info()')
        check('actual drag changes camera orientation',lambda:before['camera']['yaw']!=after['camera']['yaw'])
        check('looking retains scripted flight',lambda:after['camera']['flightActive'])
        check('camera drag emits no click weather',lambda:after['fieldCount']==before['fieldCount'])
        old=after['camera']['position'];page.mouse.wheel(0,120);page.wait_for_timeout(80);a=js('nativeLab.scene.info().camera.position');page.mouse.wheel(0,-120);page.wait_for_timeout(80);b=js('nativeLab.scene.info().camera.position')
        check('opposite wheel directions are reversible',lambda:a!=old and max(abs(x-y) for x,y in zip(b,old))<.002)
        js("nativeLab.scene.command({op:'key',key:'F1'});nativeLab.draw()")
        old=js('nativeLab.scene.info().camera');page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+100,y);page.mouse.up()
        check('modal prevents camera input',lambda:js('nativeLab.scene.info().camera')==old)
        js("nativeLab.scene.command({op:'key',key:'Escape'});nativeLab.draw()")
        load('work-graph')
        def clickNode(excluded=None):
            target=js("excluded=>{const f=nativeView.frame;for(let i=0;i<f.cells.length;i+=4){const id=f.cells[i+3];if((id>>>28)===1&&(id&0xfffffff)!==excluded)return {id:id&0xfffffff,x:(i/4)%f.width+.5,y:Math.floor(i/4/f.width)+.5,w:f.width,h:f.height};}return null;}",excluded)
            if not target:raise AssertionError('No visible target node')
            r=page.locator('#canvas').bounding_box();page.mouse.click(r['x']+target['x']/target['w']*r['width'],r['y']+target['y']/target['h']*r['height']);return target['id']
        first=clickNode();check('graph click selects actual node',lambda:js('nativeLab.scene.info().selection')==first)
        js('nativeLab.advance(220000);nativeLab.draw()');second=clickNode(first)
        check('graph retargets through open inspector',lambda:js('nativeLab.scene.info().selection')==second and second!=first)
        check('render does not mutate snapshot',lambda:js("(()=>{const a=nativeLab.scene.snapshot();nativeLab.draw();const b=nativeLab.scene.snapshot();return a.length===b.length&&a.every((v,i)=>v===b[i]);})()"))
        js('nativeLab.advance(1200000);nativeLab.draw()')
        page.locator('#canvas').screenshot(path=str(screens/'graph.png'))
        page.locator('#readability-panel summary').click()
        page.locator('#card-sha').fill('10')
        page.locator('#card-max').fill('56')
        page.locator('#card-detail').uncheck()
        beforeMeta=js('nativeLab.scene.info()')
        page.locator('#card-apply').click()
        check('native card configuration from actual controls',lambda:js('nativeLab.scene.info().nodes.every(n=>n.card.shaPrefix===10&&n.card.maxColumns===56&&!n.card.showDetail)'))
        check('metadata edit retains graph positions during motion',lambda:js('nativeLab.scene.info().nodes.map(n=>n.position)')==[n['position'] for n in beforeMeta['nodes']])
        check('SHA abbreviation leaves authoritative hashes complete',lambda:all(len(n['sha'])==64 for n in js('nativeLab.scene.info().nodes')))
        load('windows');js('nativeLab.advance(1100000);nativeLab.draw()')
        page.locator('#window-padding').fill('2')
        page.locator('#window-border').select_option('double')
        page.locator('#window-chrome').fill('4')
        page.locator('#readability-apply').click()
        check('native window treatment from actual controls',lambda:js("nativeLab.scene.info().windows.every(w=>w.readability.padding===2&&w.readability.chromeSize===4)"))
        check('camera-motion controls stay right or below visible demonstration without overlap',lambda:motionControlsClearOfCanvas(page))
        check('motion panel is collapsed by default',lambda:js("!document.querySelector('#motion-panel').open"))
        load('notifications')
        js('nativeLab.draw()')
        check('notification pop begins at full visibility',lambda:js("nativeLab.scene.info().messages.find(m=>m.id===40).state==='active'"))
        check('three duplicate telemetry messages coalesce natively',lambda:js("nativeLab.scene.info().messages.find(m=>m.id===50).occurrences===3"))
        def clickNoticeAction():
            target=js("(()=>{const f=nativeView.frame;for(let i=0;i<f.cells.length;i+=4){const id=f.cells[i+3];if((id>>>24)===0x63)return {x:(i/4)%f.width+.5,y:Math.floor(i/4/f.width)+.5,w:f.width,h:f.height};}return null;})()")
            if not target:raise AssertionError('Native notification has no visible action hit')
            page.locator('#canvas').scroll_into_view_if_needed()
            rect=page.locator('#canvas').bounding_box()
            page.mouse.click(rect['x']+target['x']/target['w']*rect['width'],rect['y']+target['y']/target['h']*rect['height'])
            return len(js('nativeLab.scene.info().intents'))==1
        check('actual native action click retains one intention',clickNoticeAction)
        check('intent has declared event and message identity',lambda:js("nativeLab.scene.info().intents[0].event==='/build/inspect' && nativeLab.scene.info().intents[0].messageId===40"))
        check('held render keeps retained action',lambda:js("(()=>{const a=nativeLab.scene.snapshot();nativeLab.draw();nativeLab.draw();return (()=>{const b=nativeLab.scene.snapshot();return a.every((v,i)=>v===b[i]);})()&&nativeLab.scene.info().intents.length===1})()"))
        page.locator('#draft').fill('Typing retains queued intentions.')
        check('local input preserves notification intention',lambda:js("nativeLab.scene.info().prompt.text==='Typing retains queued intentions.'&&nativeLab.scene.info().intents.length===1"))
        page.locator('#notification-panel summary').click()
        check('companion displays actual pending intent',lambda:'/build/inspect' in page.locator('#intent-log').inner_text())
        page.locator('#intents-ack').click()
        check('explicit acknowledgement clears intention',lambda:js('nativeLab.scene.info().intents.length===0'))
        page.locator('#notice-ack').click()
        check('important acknowledgement keeps complete source text',lambda:js("nativeLab.scene.info().messages.find(m=>m.id===40).acknowledged&&nativeLab.scene.info().messages.find(m=>m.id===40).text.includes('important record')"))
        page.locator('#notifications-repeat').click()
        check('repeat button increments existing record without restart',lambda:js("nativeLab.scene.info().messages.find(m=>m.id===50).occurrences===4"))
        page.locator('#canvas').screenshot(path=str(screens/'notifications.png'))
        load('pearl-curves');js('nativeLab.advance(2100000);nativeLab.draw()')
        check('Pearl curves have partial and full braille coverage',lambda:js("(()=>{const a=Array.from(nativeView.frame.cells).filter((v,i)=>i%4===0);return a.includes(0x28ff)&&new Set(a.filter(g=>g>0x2800&&g<0x28ff)).size>12})()"))
        check('Pearl circles have no block substitution',lambda:js("(()=>{const f=nativeView.frame;for(let i=0;i<f.cells.length;i+=4)if([2,3,4,8].some(id=>f.cells[i+3]===(0x30000000|id))&&f.cells[i]>=0x2580&&f.cells[i]<0x25a0)return false;return true})()"))
        page.locator('#braille-panel summary').click();page.locator('#plot-inner').fill('.82');page.locator('#plot-aspect').fill('2.2');page.locator('#plot-sweep').fill('300');page.locator('#plot-apply').click()
        check('Native plot parameters come from actual controls',lambda:js("nativeLab.scene.info().widgets.filter(w=>w.kind===9).every(w=>Math.abs(w.plot.innerRadius-.82)<1e-6&&w.plot.cellAspect===2.2&&w.plot.sweepAngle===300)"))
        page.locator('#plot-replay').click()
        check('Replay chart reveal starts empty at held time',lambda:js("(()=>{const f=nativeView.frame;for(let i=0;i<f.cells.length;i+=4)if([2,3,4,8].some(id=>f.cells[i+3]===(0x30000000|id))&&f.cells[i]>0x2800&&f.cells[i]<=0x28ff)return false;return true})()"))
        js('nativeLab.advance(4500000);nativeLab.draw()');page.locator('#canvas').screenshot(path=str(screens/'pearl-curves.png'))
        plotClock=js('nativeLab.scene.info().clock.timeUs')
        page.locator('#plot-sampling').select_option('cell');page.locator('#plot-apply').click()
        check('Full cells are an explicit opt-in',lambda:js("Array.from(nativeView.frame.cells).some((v,i)=>i%4===0&&v===0x2588)"))
        page.locator('#plot-sampling').select_option('braille');page.locator('#plot-apply').click()
        check('Braille restored without resetting document or clock',lambda:js("nativeLab.scene.info().widgets.filter(w=>w.kind>=6&&w.kind<=13).every(w=>w.plot.sampling==='braille')") and js('nativeLab.scene.info().clock.timeUs')==plotClock)
        load('leaf-anatomy');js('nativeLab.advance(700000);nativeLab.draw()')
        page.locator('#layer-panel summary').click()
        particlesBefore=js('nativeLab.scene.particles()');clockBefore=js('nativeLab.scene.info().clock.timeUs')
        page.locator('#layer-surface').fill('.2');page.locator('#layer-veins').fill('.8');page.locator('#layer-sampling').select_option('braille');page.locator('#layer-apply').click()
        check('leaf style controls execute native settings',lambda:js("nativeLab.scene.info().emitters.find(e=>e.id===1).surfaceAlpha===.2&&nativeLab.scene.info().emitters.find(e=>e.id===1).sampling==='braille'"))
        check('style edit cannot respawn particles or advance time',lambda:js('nativeLab.scene.particles()')==particlesBefore and js('nativeLab.scene.info().clock.timeUs')==clockBefore)
        page.locator('#layer-floor').select_option('cell');page.locator('#layer-floor-apply').click()
        check('floor choice preserves active weather identities',lambda:js('nativeLab.scene.particles()')==particlesBefore)
        page.locator('#layer-floor').select_option('half');page.locator('#layer-floor-apply').click()
        check('leaf anatomy has diverse partial dot patterns',lambda:js("new Set(Array.from(nativeView.frame.cells).filter((v,i)=>i%4===0&&v>0x2800&&v<0x28ff)).size>20"))
        page.locator('#canvas').screenshot(path=str(screens/'leaf-anatomy.png'))
        load('mixed-materials');js('nativeLab.advance(2200000);nativeLab.draw()')
        check('blocks half-blocks and braille coexist in one native frame',lambda:js("(()=>{const g=Array.from(nativeView.frame.cells).filter((v,i)=>i%4===0);return g.includes(0x2588)&&g.includes(0x2580)&&g.some(v=>v>0x2800&&v<=0x28ff)})()"))
        page.locator('#canvas').screenshot(path=str(screens/'mixed-materials.png'))
        load('weather-authoring');js('nativeLab.advance(1000000);nativeLab.draw()')
        check('nested weather recipe executes through current WASM emitter',lambda:js("(()=>{const e=nativeLab.scene.info().emitters.find(e=>e.id===9);return !!e&&e.rate===12&&nativeLab.scene.info().particles.born===12})()"))
        page.locator('#canvas').screenshot(path=str(screens/'weather-authoring.png'))
        load('condition-console');page.locator('#condition-panel summary').click()
        check('condition console registers native tree and event gate',lambda:js("nativeLab.scene.info().triggers.length===3&&nativeLab.scene.info().triggers[0].conditionNodes===6"))
        check('actual action click remains queued behind closed guard',lambda:clickNoticeAction() and js("nativeLab.scene.info().values['/demo/approved']===0"))
        check('event selector exposes the exact candidate payload',lambda:js("(()=>{const c=nativeLab.scene.info().triggers[0].intentCandidate;return c.id===1&&c.event==='/demo/approve'&&c.messageId===600&&c.actionId===1&&c.messageSequence===1&&c.value===7})()"))
        page.locator('#condition-heat').fill('60');page.locator('#condition-enabled').select_option('0');page.locator('#condition-set').click()
        check('batch guards never see intermediate input combinations',lambda:js("nativeLab.scene.info().values['/demo/approved']===0"))
        page.locator('#condition-enabled').select_option('1');page.locator('#condition-set').click()
        check('native ALL ANY guard writes selected action value exactly once',lambda:js("nativeLab.scene.info().values['/demo/approved']===7&&nativeLab.scene.info().intents.length===1&&nativeLab.scene.info().triggers[0].lastIntent===1"))
        check('action source and registered widget preserve accepted intent identity',lambda:js("(()=>{const i=nativeLab.scene.info(),r=i.triggers[0],w=i.widgets.find(w=>w.id===1);return r.valueSource==='intentValue'&&w.value===7&&r.lastIntentSource.id===1&&r.lastIntentSource.event==='/demo/approve'&&r.lastIntentSource.messageId===600&&r.lastIntentSource.actionId===1&&r.lastIntentSource.messageSequence===1&&r.lastIntentSource.value===7})()"))
        page.locator('#condition-set').click()
        check('repeated data commit does not duplicate accepted event',lambda:js("nativeLab.scene.info().values['/demo/approved']===7"))
        page.locator('#intents-ack').click()
        check('explicit acknowledgement clears retained source without changing accepted value',lambda:js("nativeLab.scene.info().intents.length===0&&nativeLab.scene.info().values['/demo/approved']===7&&nativeLab.scene.info().triggers[0].lastIntent===1&&nativeLab.scene.info().triggers[0].lastIntentSource===null"))
        page.locator('#condition-rearm').click()
        # A second intentional click gets a new identity after the first is acknowledged.
        clickNoticeAction()
        check('rearmed action emits a second independently gated identity',lambda:js("nativeLab.scene.info().values['/demo/approved']===7&&nativeLab.scene.info().intents.length===1&&nativeLab.scene.info().triggers[0].lastIntent===2&&nativeLab.scene.info().triggers[0].lastIntentSource.id===2&&nativeLab.scene.info().triggers[0].lastIntentSource.value===7"))
        heldClock=js('nativeLab.scene.info().clock.timeUs');page.locator('#draft').fill('Immediate input / one retained intention')
        check('held input remains immediate beside compound rules',lambda:js("nativeLab.scene.info().prompt.text==='Immediate input / one retained intention'&&nativeLab.scene.info().intents.length===1") and js('nativeLab.scene.info().clock.timeUs')==heldClock)
        check('conditions panel reflects authoritative values',lambda:'/demo/approved' in page.locator('#condition-state').inner_text())
        page.locator('#canvas').screenshot(path=str(screens/'condition-console.png'))
        for recipe in js('nativeLab.recipes.map(r=>r.id)'):
            def recipeCheck(recipe=recipe):
                load(recipe);js('nativeLab.advance(900000);nativeLab.draw()');return not page.locator('#error').inner_text()
            check('recipe '+recipe,recipeCheck)
            if recipe in ['autumn','rain','windows','instruments','status','notifications','leaf-anatomy','mixed-materials','condition-console']:
                page.locator('#canvas').screenshot(path=str(screens/(recipe+'.png')))
        for effect in js('nativeLab.scene.catalogue().map(e=>e.id)'):
            def effectCheck(effect=effect):
                js("id=>{document.getElementById('effect').value=id;nativeLab.selectEffect();nativeLab.hold(true);nativeLab.advance(900000);nativeLab.draw();}",effect)
                return not page.locator('#error').inner_text()
            check('effect '+effect,effectCheck)
        check('no browser exceptions',lambda:not errors);check('no network requests',lambda:not requests)
        version=browser.version;browser.close()
    result={'scope':'Exact shipped HTML via set_content, real Chromium keyboard/pointer/wheel events. Not physical Safari/GPU or historical optical acceptance.','htmlSha256':hashlib.sha256(html.read_bytes()).hexdigest(),'browser':version,'checks':records,'errors':errors,'requests':requests,'passed':all(r['status']=='PASS' for r in records)}
    (ROOT/'evidence/browser.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'checks':len(records),'passed':result['passed'],'failures':[r for r in records if r['status']!='PASS']},indent=2))
    return 0 if result['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
