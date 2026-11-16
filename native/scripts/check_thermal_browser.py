"""Real Boolean consumer tables and production gallery actions."""
import argparse,json,os,subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--gallery',type=Path,default=ROOT/'Nocturne-Test-Harness.html');args=parser.parse_args()
    cases=json.loads((ROOT/'examples/thermal-scenes.json').read_text())
    report={'runtime':'actual Chromium','scope':'Production recipe load/draw/autoActions from fresh public SDK baseline; host preferences excluded',
      'expectedCaseIds':[c['id'] for c in cases],'cases':[],'pageErrors':[],'complete':False,'passed':False}
    def persist():
        args.output.parent.mkdir(parents=True,exist_ok=True);p=args.output.with_suffix('.tmp')
        p.write_text(json.dumps(report,indent=2)+'\n');p.replace(args.output)
    persist()
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=os.environ.get('CHROMIUM'))
        page=browser.new_page();page.on('pageerror',lambda e:report['pageErrors'].append(str(e)))
        page.set_content(args.gallery.read_text());page.wait_for_function('window.nativeLab !== undefined');page.evaluate('nativeLab.hold()')
        if args.gallery!=ROOT/'Nocturne-Test-Harness.html':
            ids=set(page.evaluate('nativeLab.recipes.map(r=>r.id)'));assert all(c['id'] in ids for c in cases)
        oracle=(ROOT.parent/'bindings/continuity/effect-catalog.js').read_text()
        oracle=oracle[oracle.index('export function sampleThermal'):].replace('export function','function')
        prefix="const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));function randomAt(seed,index){let v=(seed^Math.imul(index+1,0x9e3779b9))>>>0;v=Math.imul(v^(v>>>16),0x7feb352d)>>>0;v=Math.imul(v^(v>>>15),0x846ca68b)>>>0;return ((v^(v>>>16))>>>0)/4294967296;}"
        helpers=prefix+oracle+''.join((ROOT/'scripts'/name).read_text().replace('export function','function').replace("import {sampleThermal} from '../../bindings/continuity/effect-catalog.js';",'') for name in ['resource_ownership_checks.mjs','thermal_checks.mjs'])
        page.add_script_tag(content='(()=>{'+helpers+'window.thermalChecks={equalBytes,heldAutomaticExpected,checkThermal,runThermal};})();')
        for case in cases:
            try:
                row=page.evaluate("""recipe=>{
                  const s=nativeLab.scene,{equalBytes,heldAutomaticExpected,checkThermal,runThermal}=thermalChecks;
                  const load=()=>{nativeLab.load(recipe);nativeLab.hold();s.command({op:'reset',seed:2030});for(const c of recipe.commands)s.command(c);};
                  load();const initial=s.snapshot(),manual=runThermal(s,recipe,equalBytes);
                  const final=s.snapshot(),frame=s.render().bytes,finalHeld=heldAutomaticExpected(s);nativeLab.draw();
                  if(!equalBytes(final,s.snapshot()))throw Error('Draw purity');
                  for(const command of recipe.rejectedCommands){let rejected=false;try{s.command(command);}catch{rejected=true;}
                    if(!rejected||!equalBytes(final,s.snapshot()))throw Error('Atomic rejection');}
                  s.restore(initial);const replay=runThermal(s,recipe,equalBytes);
                  if(!equalBytes(final,s.snapshot())||manual.frames.some((f,i)=>!equalBytes(f,replay.frames[i])))throw Error('Replay');
                  load();nativeLab.advance(6500000);checkThermal(s,recipe,6500000);
                  if(!equalBytes(finalHeld,s.snapshot())||!equalBytes(frame,s.render().bytes))throw Error('Product clock source/frame');
                  return {id:recipe.id,status:'PASS',samples:recipe.sampleTimesUs.length,rejections:recipe.rejectedCommands.length};
                }""",case)
            except Exception as e:row={'id':case['id'],'status':'FAIL','error':str(e)}
            report['cases'].append(row);persist();print(case['id']+': '+row['status'],flush=True)
        browser.close()
    report['complete']=len(report['cases'])==len(cases)
    report['passed']=report['complete'] and not report['pageErrors'] and all(c['status']=='PASS' for c in report['cases']);persist()
    return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
