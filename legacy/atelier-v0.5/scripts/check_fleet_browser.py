#!/usr/bin/env python3
"""Exercise the actual self-contained Fleet HTML; no network or fixture updates."""
from pathlib import Path
import json, os
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
checks=[]
def check(name,condition):
    assert condition,name
    checks.append(name)
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),args=['--no-sandbox'])
    page=b.new_page(viewport={'width':1740,'height':1260},device_scale_factor=1)
    errors=[];network=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('request',lambda r:network.append(r.url))
    # This managed Chromium blocks file:// navigation. Execute the exact artifact
    # bytes with set_content, preserving its inline scripts/WASM without a server.
    page.set_content((ROOT/'Nocturne-Pearl-Fleet.html').read_text())
    page.wait_for_function('window.fleetApp && window.fleetMetrics')
    page.evaluate('fleetApp.stop(); fleetApp.step(6000)')
    check('8 keyboard-accessible agent buttons',page.locator('#agents button').count()==8)
    page.locator('[data-agent="prism"]').click()
    start=page.evaluate('fleetApp.controller.activeRect()')
    page.evaluate('fleetApp.step(6560)')
    check('agent click expands to final workspace',page.evaluate('JSON.stringify(fleetApp.controller.activeRect())===JSON.stringify(fleetApp.controller.workspaceRect())'))
    check('expansion is not an instant static swap',start!=page.evaluate('fleetApp.controller.activeRect()'))
    page.locator('#draft').fill('Remember this draft for PRISM')
    page.locator('[data-agent="atlas"]').click();page.evaluate('fleetApp.step(7120)')
    page.locator('[data-agent="prism"]').click();page.evaluate('fleetApp.step(7680)')
    check('agent-local drafts survive switching',page.locator('#draft').input_value()=='Remember this draft for PRISM')
    page.locator('#motion').click();before=page.evaluate('({...fleetMetrics})')
    page.locator('#draft').fill('paused event: visible now');page.locator('#send').click()
    after=page.evaluate('({...fleetMetrics})')
    check('input paints while motion is held',after['dataPaints']>before['dataPaints'] and after['motionMs']==before['motionMs'])
    page.evaluate('fleetApp.dataTick()');after2=page.evaluate('({...fleetMetrics})')
    check('telemetry commits while motion is held',after2['revision']>after['revision'] and after2['motionMs']==after['motionMs'])
    page.locator('#transcriptDetails summary').click()
    check('unfaded transcript retains submitted text','paused event: visible now' in page.locator('#transcript').inner_text())
    page.locator('#motion').click()
    page.evaluate('fleetApp.controller.scroll(8);fleetApp.paint()')
    anchor=page.evaluate('fleetApp.controller.visibleTranscript()[0]')
    page.evaluate("const c=fleetApp.controller,a=c.model.agent(c.selectedId);fleetApp.ingest({version:1,agentId:a.id,seq:a.lastSeq+1,atMs:15000,type:'message.start',payload:{messageId:'browser-new',role:'agent',text:'New text while reading history.\\nA second line.'}})")
    check('history anchor remains stable',page.evaluate('fleetApp.controller.visibleTranscript()[0]')==anchor)
    page.locator('#stage').focus();page.keyboard.press('End')
    check('End explicitly resumes live tail',page.evaluate('fleetMetrics.scrollOffset')==0)
    page.keyboard.press('Escape');page.evaluate('fleetApp.step(8300)')
    check('Escape restores fleet view',page.evaluate('!fleetApp.controller.hasWorkspace'))
    # Exercise the native cell click surface, not only companion DOM buttons.
    box=page.locator('#stage').bounding_box();rect=page.evaluate("fleetApp.controller.cardRect('forge')")
    page.mouse.click(box['x']+(rect['x']+3)*box['width']/144,box['y']+(rect['y']+2)*box['height']/48)
    page.evaluate('fleetApp.step(8860)')
    check('cell-native pointer hit selects FORGE',page.evaluate("fleetMetrics.selectedId==='forge' && fleetMetrics.opened"))
    page.locator('#readMode').check()
    check('reading mode retains transcript and removes top fade',page.evaluate("fleetApp.scene().nodes.filter(n=>n.id>=100000).every(n=>n.fgOpacity===1000)"))
    page.locator('#readMode').uncheck()
    palette_ids=page.locator('#palette option').evaluate_all('(nodes)=>nodes.map(n=>n.value)')
    for palette in palette_ids:page.evaluate('(id)=>fleetApp.setPalette(id)',palette)
    check('all 48 palettes render',len(palette_ids)==48)
    page.evaluate("fleetApp.setPalette('smart-dark')")
    for w,h in [(80,24),(120,26),(144,48),(240,100),(38,16)]:
        page.evaluate('([w,h])=>{fleetApp.controller.resize(w,h);fleetApp.step(10000);fleetApp.paint()}',[w,h])
        check(f'viewport {w}x{h}',page.evaluate('fleetApp.frame().cells.length')==w*h*4)
    check('no external requests',not network)
    check('no browser exceptions',not errors)
    b.close()
report={'suite':'Pearl Fleet browser','status':'PASS','checks':checks,'count':len(checks),'errors':errors,'externalRequests':network,'artifactLoad':'set_content of standalone HTML bytes (managed Chromium blocks file://)'}
(ROOT/'dist/fleet/browser-tests.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
