#!/usr/bin/env python3
"""Exercise the shipped task/work recipe through Chromium and the current C/WASM.

Inputs: freshly built gallery and local Chromium/Playwright. Writes task-graph.json
and actual canvas captures under native/evidence. Exits 0 only after all checks.
This uses native graph commands and real browser events, not a foreign controller.
Example: python3 native/scripts/check_task_graph.py
"""
from pathlib import Path
import base64, hashlib, json, os, shutil
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[1]


def main(evidence=None):
    """Run fixed-time browser graph assertions and return 0 (PASS) or 2 (FAIL)."""
    checks, errors, requests, captures = [], [], [], []
    html = ROOT/'Nocturne-Test-Harness.html'
    evidence=Path(evidence) if evidence is not None else ROOT/'evidence';evidence.mkdir(exist_ok=True)
    with sync_playwright() as playwright:
        executable=os.environ.get('CHROMIUM') or shutil.which('chromium') or shutil.which('google-chrome')
        browser=playwright.chromium.launch(headless=True,executable_path=executable,args=['--no-sandbox'])
        version=browser.version
        page=browser.new_page(viewport={'width':1500,'height':1150},device_scale_factor=1)
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.on('request',lambda request:requests.append(request.url))
        page.set_content(html.read_text());page.wait_for_function('window.nativeLab !== undefined',timeout=30000)
        def check(name, action):
            try:
                if not action():raise AssertionError(name)
                checks.append({'name':name,'status':'PASS'})
            except Exception as error:checks.append({'name':name,'status':'FAIL','reason':str(error)})
            print(checks[-1]['status'],name,flush=True)
        def info():return page.evaluate('nativeLab.scene.info()')
        def drawAt(stamp):page.evaluate('(t)=>{nativeLab.advance(t);nativeLab.draw();}',stamp)
        def visibleIds():
            return page.evaluate('''()=>{let f=nativeView.frame,s=new Set();for(let i=0;i<f.cells.length;i+=4)
                if((f.cells[i+3]>>>28)===1)s.add(f.cells[i+3]&0x0fffffff);return [...s].sort((a,b)=>a-b);}''')
        def nativeFrame():return bytes(page.evaluate('Array.from(nativeView.frame.bytes)'))
        def save(name):
            path=evidence/'screens'/f'task-graph-{name}.png';path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(base64.b64decode(page.evaluate("canvas.toDataURL('image/png').split(',')[1]")))
            captures.append({'path':str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        def pointFor(nodeId):
            point=page.evaluate('''id=>{let f=nativeView.frame,points=[];for(let i=0;i<f.cells.length;i+=4)
              if((f.cells[i+3]>>>28)===1&&(f.cells[i+3]&0xfffffff)===id)
                points.push([i/4%f.width,Math.floor(i/4/f.width)]);
              return points.length?points[Math.floor(points.length/2)]:null;}''',nodeId)
            if point is None:raise AssertionError(f'node {nodeId} has no visible hit surface')
            page.locator('#canvas').scroll_into_view_if_needed();r=page.locator('#canvas').bounding_box()
            dims=page.evaluate('[nativeView.frame.width,nativeView.frame.height]')
            return r['x']+(point[0]+.5)*r['width']/dims[0],r['y']+(point[1]+.5)*r['height']/dims[1]
        # Enter the same shipped recipe an operator opens from the gallery.
        page.get_by_label('Study',exact=True).select_option('task-graph')
        page.evaluate('nativeLab.hold();');drawAt(900000)
        check('visible Study selector opens the task graph with rotation disabled',lambda:page.locator('#scenes').input_value()=='task-graph' and page.locator('#title').inner_text()=='Task / Work Dependencies' and page.locator('#attract').get_attribute('aria-pressed')=='false')
        original=info();frame3=nativeFrame();save('3d')
        commands=[json.loads(l) for l in (ROOT/'examples/task_graph.ndjson').read_text().splitlines() if l]
        check('gallery runs exact standalone graph command file',lambda:page.evaluate("nativeLab.recipes.find(r=>r.id==='task-graph').commands")==commands)
        check('eight stable node identities have visible native hit surfaces',lambda:visibleIds()==list(range(1,9)))
        check('full original labels and hashes survive card abbreviation',lambda:all(
            next(n for n in original['nodes'] if n['id']==c['id'])['sha']==c['sha'] and
            next(n for n in original['nodes'] if n['id']==c['id'])['label']==c['label'] for c in commands if c['op']=='node'))
        check('shared action is one node referenced by two requests',lambda:sum(n['id']==7 for n in original['nodes'])==1 and
            {c['from'] for c in commands if c['op']=='edge' and c['to']==7}=={4,5})
        for selector in ('#camera-controls-panel','#camera-controls-panel > details.camera-pose'):
            panel=page.locator(selector)
            if panel.get_attribute('open') is None:panel.locator(':scope > summary').click()
        check('visible disclosure clicks expose both graph dimension controls',lambda:page.locator('#flat').is_visible() and page.locator('#spatial').is_visible())
        page.locator('#flat').click();drawAt(1900000);frame2=nativeFrame();save('2d')
        check('actual 2D control changes native graph projection',lambda:frame2!=frame3)
        check('2D view retains all eight native hit owners',lambda:visibleIds()==list(range(1,9)))
        check('switching dimensions preserves identities and complete metadata',lambda:[(n['id'],n['sha']) for n in info()['nodes']]==[(n['id'],n['sha']) for n in original['nodes']])
        page.locator('#spatial').click();drawAt(2900000)
        check('actual 3D control restores a distinct spatial view',lambda:nativeFrame()!=frame2)
        fields=info()['fieldCount'];first=visibleIds()[0];x,y=pointFor(first);page.mouse.click(x,y)
        check('actual card click selects native hit owner',lambda:info()['selection']==first)
        second=next(n for n in visibleIds() if n!=first);x,y=pointFor(second);page.mouse.click(x,y)
        check('inspector is nonmodal: another visible card remains clickable',lambda:info()['selection']==second)
        check('card clicks do not generate decorative click weather',lambda:info()['fieldCount']==fields)
        page.evaluate('window.graphCheckpoint=nativeLab.scene.snapshot();for(let i=0;i<4;i++){nativeLab.draw();nativeLab.scene.info();}')
        check('repeated render and inspect do not advance or mutate state',lambda:page.evaluate('nativeLab.scene.snapshot().every((x,i)=>x===graphCheckpoint[i])'))
        # A metadata update must retain the current interpolated pose.
        pose=[n['position'] for n in info()['nodes']]
        page.evaluate("nativeLab.scene.command({op:'node',id:7,status:'inspected',shaPrefix:8});nativeLab.draw();")
        check('live metadata edit retains node poses and full source hash',lambda:[n['position'] for n in info()['nodes']]==pose and next(n for n in info()['nodes'] if n['id']==7)['sha']==next(n for n in original['nodes'] if n['id']==7)['sha'])
        page.locator('#draft').fill('Task graph input remains immediate while motion is held.')
        check('real browser input commits while simulation is held',lambda:info()['prompt']['text']=='Task graph input remains immediate while motion is held.')
        # Reset recipe to a known unselected scene before exercising camera gestures.
        page.get_by_label('Study',exact=True).select_option('task-graph')
        page.evaluate('nativeLab.hold();');drawAt(900000)
        page.locator('#canvas').scroll_into_view_if_needed();r=page.locator('#canvas').bounding_box()
        camera=info()['camera'];fields=info()['fieldCount']
        page.mouse.move(r['x']+r['width']*.05,r['y']+r['height']*.4);page.mouse.down()
        page.mouse.move(r['x']+r['width']*.12,r['y']+r['height']*.45,steps=5);page.mouse.up()
        check('real pointer drag changes look orientation',lambda:info()['camera']!=camera)
        check('camera drag does not turn into click weather',lambda:info()['fieldCount']==fields)
        camera=info()['camera'];page.mouse.wheel(0,120)
        page.wait_for_function('(c)=>JSON.stringify(nativeLab.scene.info().camera)!==JSON.stringify(c)',arg=camera,timeout=3000)
        check('real wheel event changes camera position',lambda:info()['camera']['position']!=camera['position'])
        check('no page exceptions',lambda:not errors)
        check('no requests for fonts, network providers, or external assets',lambda:not requests)
        browser.close()
    result={'scope':'Current task/work recipe; real Chromium controls and C/WASM node ownership, 2D/3D and input. Not physical-platform or artistic acceptance.',
            'browser':version,'htmlSha256':hashlib.sha256(html.read_bytes()).hexdigest(),
            'wasmSha256':hashlib.sha256((ROOT/'dist/nocturne_native.wasm').read_bytes()).hexdigest(),
            'checks':checks,'captures':captures,'errors':errors,'requests':requests,
            'passed':all(c['status']=='PASS' for c in checks)}
    (evidence/'task-graph.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'checks':len(checks),'passed':result['passed']}),flush=True)
    return 0 if result['passed'] else 2

if __name__=='__main__':raise SystemExit(main())
