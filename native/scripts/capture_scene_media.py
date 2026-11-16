"""Capture requested real gallery recipes; subset media is not full qualification."""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import math
import platform
import re
import time
from playwright.sync_api import sync_playwright

CAPTURE_PROTOCOL = "scene-clock-ownership-v2"

def sha(data):return hashlib.sha256(data).hexdigest()

def fileRecord(path,root):
    return {'path':str(path.relative_to(root)),'bytes':path.stat().st_size,'sha256':sha(path.read_bytes())}

def save(path,report):
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(report,indent=2)+'\n');temporary.replace(path)

def verifyCompleted(row,root,config):
    if config.get('protocol') != CAPTURE_PROTOCOL or row['recipe']['id'] != row['id']:
        raise ValueError('Completed capture protocol or recipe identity differs')
    _, targets, duration = captureTimeline(row['recipe'], config['seconds'], config['fps'], config.get('throughTimeline', False))
    if [sample.get('targetTimeUs') for sample in row['samples']] != sorted(targets):
        raise ValueError('Completed capture sample timeline differs')
    if config.get('throughTimeline') and row.get('captureDurationUs') != duration:
        raise ValueError('Completed capture duration differs')
    for sample in row['samples']:
        if (sample.get('recipeId') != row['id'] or type(sample.get('timeUs')) is not int
                or sample['timeUs'] != sample['targetTimeUs'] or sample.get('renderPure') is not True):
            raise ValueError('Completed capture scene identity or clock differs')
    records=[row['video']]+[sample['screenshot'] for sample in row['samples']]
    if not row['samples']:raise ValueError('Completed case has no samples')
    for record in records:
        path=(root/record['path']).resolve()
        if not path.is_relative_to(root):raise ValueError('Media path escapes output directory')
        if fileRecord(path,root)!=record:raise ValueError('Saved media custody mismatch')

def captureTimeline(recipe, seconds, fps, throughTimeline):
    duration = round(seconds * 1000000)
    declared = []
    if throughTimeline:
        declared = list(recipe.get('sampleTimesUs', []))
        declared += [action['timeUs'] for action in recipe.get('actions', [])]
        if any(type(clock) is not int or not 0 <= clock <= 86400000000 for clock in declared):
            raise ValueError('Declared timeline clocks must be integer microseconds within the scene range')
        duration = max([duration, *declared])
    steps = max(2, math.ceil(duration * fps / 1000000))
    grid = [round(index * duration / steps) for index in range(steps + 1)]
    samples = {grid[0], grid[steps // 2], grid[-1]}
    if throughTimeline:
        samples.update(declared)
    return sorted(set(grid) | set(declared)), samples, duration

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--gallery',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    selection=p.add_mutually_exclusive_group(required=True)
    selection.add_argument('--case',action='append',dest='cases')
    selection.add_argument('--case-file',type=Path,help='JSON array of exact gallery recipe IDs')
    selection.add_argument('--all',action='store_true',help='Capture every recipe in the supplied gallery')
    p.add_argument('--resume',action='store_true',help='Verify saved custody and resume this exact capture')
    p.add_argument('--through-timeline',action='store_true',help='Include declared recipe sample and action clocks')
    p.add_argument('--seconds',type=float,default=6);p.add_argument('--fps',type=int,default=15)
    a=p.parse_args()
    if not math.isfinite(a.seconds) or not 0<a.seconds<=86400 or a.fps<1:p.error('Positive duration within scene clock and positive FPS required')
    if a.case_file:
        try:a.cases=json.loads(a.case_file.read_text())
        except (OSError,ValueError) as error:p.error(f'Cannot read case file: {error}')
    if not a.all:
        if not isinstance(a.cases,list) or not a.cases or any(not isinstance(identity,str) or not identity for identity in a.cases):
            p.error('Case selection must be a nonempty array of nonempty string IDs')
        if len(set(a.cases))!=len(a.cases):p.error('Duplicate requested case IDs')
    out=a.output.resolve()
    if out.exists() and not a.resume:p.error('Output must be a new directory')
    if a.resume and not (out/'MEDIA.json').is_file():p.error('Resume requires an existing manifest')
    if not a.resume:out.mkdir(parents=True)
    started=time.monotonic();writable=not a.resume
    report={'schema':'nocturne.scene-media.v1','requestedCaseIds':a.cases,'cases':[],
            'complete':False,'passed':False,'scope':'Requested real gallery recipes, not every component/parameter or full SDK qualification',
            'platform':platform.platform(),'pageErrors':[]}
    manifest=out/'MEDIA.json'
    if writable:save(manifest,report)
    try:
        gallery=a.gallery.resolve(strict=True);html=gallery.read_bytes()
        embedded=[base64.b64decode(value) for value in re.findall(rb"atob\('([A-Za-z0-9+/=]+)'\)",html)]
        wasm=[data for data in embedded if data.startswith(b'\0asm')]
        if len(wasm)!=1:raise ValueError('One embedded WASM runtime required')
        report.update(gallerySha256=sha(html),wasmSha256=sha(wasm[0]))
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True)
            report['browserVersion']=browser.version
            try:
                discovery=browser.new_page();discovery.goto(gallery.as_uri());discovery.wait_for_function('window.nativeLab !== undefined')
                identities=discovery.evaluate('nativeLab.recipes.map(recipe=>recipe.id)');discovery.close()
                if a.all:
                    if not identities or any(not isinstance(identity,str) or not identity for identity in identities) or len(set(identities))!=len(identities):
                        raise ValueError('Complete gallery must have unique nonempty string case IDs')
                    a.cases=identities
                    report['requestedCaseIds']=identities
                if any(identities.count(identity)!=1 for identity in a.cases):raise ValueError('Missing or duplicate requested gallery case')
                report['galleryCaseCount']=len(identities)
                report['selection']='all' if a.all else 'file' if a.case_file else 'explicit'
                report['captureConfig']={'seconds':a.seconds,'fps':a.fps,'protocol':CAPTURE_PROTOCOL}
                if a.through_timeline:report['captureConfig']['throughTimeline']=True
                if a.resume:
                    previous=json.loads(manifest.read_text())
                    if previous.get('pageErrors'):raise ValueError('Browser errors require a fresh capture, not resume')
                    for key in ['schema','gallerySha256','wasmSha256','requestedCaseIds','captureConfig']:
                        if previous.get(key)!=report[key]:raise ValueError(f'Resume identity differs: {key}')
                    rows=previous['cases'];seen=set()
                    for row in rows:
                        if row['id'] not in a.cases or row['id'] in seen:raise ValueError('Invalid saved case identity')
                        seen.add(row['id'])
                        if row['complete']:verifyCompleted(row,out,report['captureConfig'])
                    attempts=previous.get('previousAttempts',[])+[row for row in rows if not row['complete']]
                    report['previousAttempts']=attempts
                    report['previousRuns']=previous.get('previousRuns',[])+[{'seconds':previous.get('seconds'),'pageErrors':previous.get('pageErrors',[]),'error':previous.get('error')}]
                    report['cases']=[row for row in rows if row['complete']]
                    writable=True
                save(manifest,report)
                for identity in a.cases:
                    if any(row['id']==identity and row['complete'] for row in report['cases']):continue
                    folder=out/('case-'+sha(identity.encode())[:16])
                    if folder.exists():folder=out/(folder.name+'-attempt-'+str(time.time_ns()))
                    folder.mkdir()
                    context=browser.new_context(viewport={'width':1280,'height':900},record_video_dir=str(folder/'video'),
                                                record_video_size={'width':1280,'height':900})
                    row={'id':identity,'samples':[],'complete':False};report['cases'].append(row);save(manifest,report)
                    page=context.new_page();video=page.video
                    page.on('pageerror',lambda error:report['pageErrors'].append(str(error)))
                    try:
                        page.goto(gallery.as_uri());page.wait_for_function('window.nativeLab !== undefined')
                        declared=page.locator('footer').get_attribute('data-wasm-sha256')
                        if declared!=report['wasmSha256']:raise ValueError('Declared WASM differs from embedded runtime')
                        row['recipe']=page.evaluate("""identity=>{
                          const selector=document.querySelector('#scenes');selector.value=identity;
                          selector.dispatchEvent(new Event('change',{bubbles:true}));nativeLab.hold();
                          if(selector.value!==identity||document.querySelector('#attract').getAttribute('aria-pressed')!=='false')throw Error('Capture selection did not hold requested scene');
                          return nativeLab.recipes.find(r=>r.id===identity);
                        }""",identity)
                        targets,sampleTargets,duration=captureTimeline(row['recipe'],a.seconds,a.fps,a.through_timeline)
                        if a.through_timeline:row['captureDurationUs']=duration
                        previous=0
                        for index,target in enumerate(targets):
                            page.evaluate("""({delta,target,identity})=>{
                              nativeLab.advance(delta);nativeLab.draw();
                              if(document.querySelector('#scenes').value!==identity||document.querySelector('#attract').getAttribute('aria-pressed')!=='false'||nativeLab.scene.info().clock.timeUs!==target)throw Error('Capture scene identity or clock differs from requested target');
                            }""",{'delta':target-previous,'target':target,'identity':identity});previous=target
                            if target in sampleTargets:
                                sample=page.evaluate('''async({target,identity})=>{
                                  const scene=nativeLab.scene,before=scene.snapshot();nativeLab.draw();
                                  const after=scene.snapshot();if(after.length!==before.length||!after.every((value,index)=>value===before[index]))throw Error('Capture draw changed source');
                                  const recipeId=document.querySelector('#scenes').value,timeUs=scene.info().clock.timeUs;
                                  if(recipeId!==identity||timeUs!==target||document.querySelector('#attract').getAttribute('aria-pressed')!=='false')throw Error('Capture sample identity or clock changed');
                                  const frame=scene.render(),digest=async bytes=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(value=>value.toString(16).padStart(2,'0')).join('');
                                  return {recipeId,targetTimeUs:target,timeUs,width:frame.width,height:frame.height,frameSha256:await digest(frame.bytes),snapshotSha256:await digest(after),renderPure:true};
                                }''',{'target':target,'identity':identity})
                                png=folder/f'frame-{index:06d}.png';page.locator('#canvas').screenshot(path=str(png));sample['screenshot']=fileRecord(png,out)
                                row['samples'].append(sample);save(manifest,report)
                            if index+1<len(targets):page.wait_for_timeout((targets[index+1]-target)/1000)
                    finally:context.close()
                    row['video']=fileRecord(Path(video.path()),out);row['complete']=True;save(manifest,report)
            finally:browser.close()
        report['complete']=len(report['cases'])==len(a.cases) and all(row['complete'] for row in report['cases'])
        report['passed']=report['complete'] and not report['pageErrors']
    except Exception as error:report['error']=str(error)
    finally:
        report['seconds']=round(time.monotonic()-started,3)
        if writable:save(manifest,report)
    print(json.dumps({'passed':report['passed'],'cases':len(report['cases']),'seconds':report['seconds']},indent=2))
    return 0 if report['passed'] else 2

if __name__=='__main__':raise SystemExit(main())
