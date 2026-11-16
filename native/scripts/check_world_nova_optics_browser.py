#!/usr/bin/env python3
"""Actual Chromium world nova optics oracles and product autoAction sequences."""
import argparse,json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    results=[];errors=[]
    with sync_playwright() as pw:
        b=pw.chromium.launch(headless=True,executable_path=os.environ.get('CHROMIUM'))
        page=b.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content((ROOT/'Nocturne-Test-Harness.html').read_text())
        page.wait_for_function('window.nativeLab !== undefined');page.evaluate('nativeLab.hold()')
        ids=page.evaluate("nativeLab.recipes.filter(r=>r.id.startsWith('world-nova-optics-')).map(r=>r.id)")
        assert len(ids)==2
        assert len(ids)==2, ids
        for id in ids:
            results.append(page.evaluate("""id=>{
                const recipe=nativeLab.recipes.find(r=>r.id===id),s=nativeLab.scene;
                const load=()=>{nativeLab.load(recipe);nativeLab.hold();for(const c of recipe.commands)if(c.op==='draft'||c.op==='resize'||c.op==='pause')s.command(c);s.command({op:'pause',paused:false});};
                const matches=(a,e)=>e!==null&&typeof e==='object'&&!Array.isArray(e)?a!==null&&typeof a==='object'&&Object.entries(e).every(([k,v])=>matches(a[k],v)):Array.isArray(e)?Array.isArray(a)&&a.length===e.length&&e.every((v,i)=>matches(a[i],v)):a===e;
                const check=action=>{const info=s.info();if(action.expectedInfo&&!matches(info,action.expectedInfo))throw Error(id+' action info '+JSON.stringify(action.expectedInfo));
                    if(action.expectedApproxInfo){const tol=action.approxTolerance??1e-5;const near=(a,e)=>Array.isArray(e)?Array.isArray(a)&&a.length===e.length&&e.every((v,i)=>near(a[i],v)):e&&typeof e==='object'?a&&typeof a==='object'&&Object.entries(e).every(([k,v])=>near(a[k],v)):typeof e==='number'&&Number.isFinite(a)&&Math.abs(a-e)<=tol;if(!near(info,action.expectedApproxInfo))throw Error('approximate info');}
                    const beforeQuery=s.snapshot();for(const q of action.expectedQueries||[]){const actual=s[q.kind](q.id);if(q.rows&&!matches(actual,q.rows))throw Error('triangle rows');}
                    if(action.expectedCharacterCells){s.render();for(const expected of action.expectedCharacterCells){const actual=s.inspectCharacterCell(expected.x,expected.y);for(const [k,v] of Object.entries(expected))if(k!=='x'&&k!=='y'&&actual[k]!==v)throw Error('character cell '+k);}}
                    const afterQuery=s.snapshot();if(!beforeQuery.every((v,i)=>v===afterQuery[i]))throw Error('query mutation');
                    for(const [k,v] of Object.entries(action.expectedPromptState||{}))if(info.prompt[k]!==v)throw Error('prompt '+k);
                    if(action.expectedInputOwner&&info.inputOwner!==action.expectedInputOwner)throw Error('input owner');
                    if(action.expectedDockWindows){const cells=s.render().cells,owners=new Set();for(let i=3;i<cells.length;i+=4)if((cells[i]&0xffff0000)===0x50000000)owners.add(cells[i]&65535);if(JSON.stringify([...owners].sort((a,b)=>a-b))!==JSON.stringify([...action.expectedDockWindows].sort((a,b)=>a-b)))throw Error('dock membership');}
                };
                load();let commands=0,rejections=0;
                const manual=action=>{for(const step of action.hostSteps||[])manual(step);const before=s.snapshot(),targets=action.expectedNodeTargetsChanged?new Map(s.info().nodes.map(n=>[n.id,n.targetPosition])):null;let failure=null;try{s.command(action.command);}catch(e){failure=e;}
                    if(action.expectedError){if(!failure||!String(failure.message).includes(action.expectedError))throw Error('expected rejection');rejections++;}else if(failure)throw failure;
                    if(action.expectedError||action.unchanged){const after=s.snapshot();if(!before.every((v,i)=>v===after[i]))throw Error('action mutation');}
                    if(targets)for(const id of action.expectedNodeTargetsChanged){const n=s.info().nodes.find(n=>n.id===id);if(!n||JSON.stringify(n.targetPosition)===JSON.stringify(targets.get(id)))throw Error('unchanged target');}check(action);const pure=s.snapshot();nativeLab.draw();const after=s.snapshot();if(!pure.every((v,i)=>v===after[i]))throw Error('render mutation');commands++;
                };
                for(const action of recipe.actions){s.advanceTo(action.timeUs);nativeLab.draw();manual(action);}
                const authored=new Map(),record=a=>{for(const step of a.hostSteps||[])record(step);authored.set(a.command,a);};recipe.actions.forEach(record);
                const original=s.command.bind(s),trace=[];s.command=command=>{const action=authored.get(command);if(!action)return original(command);
                    const targets=action.expectedNodeTargetsChanged?new Map(s.info().nodes.map(n=>[n.id,n.targetPosition])):null;let result,error=null;try{result=original(command);}catch(e){error=e;}
                    trace.push({command:JSON.parse(JSON.stringify(command)),rejected:!!error,error:error?String(error.message):null});
                    if(action.expectedError){if(!error||!String(error.message).includes(action.expectedError))throw Error('automatic expected rejection');}else if(error)throw error;
                    if(targets)for(const id of action.expectedNodeTargetsChanged){const n=s.info().nodes.find(n=>n.id===id);if(!n||JSON.stringify(n.targetPosition)===JSON.stringify(targets.get(id)))throw Error('unchanged automatic target');}check(action);if(error)throw error;return result;
                };
                try{load();let time=0;for(const action of recipe.actions){nativeLab.advance(action.timeUs-time);time=action.timeUs;check(action);}}finally{s.command=original;}
                if(trace.length!==commands||trace.filter(r=>r.rejected).length!==rejections)throw Error('automatic primitive trace membership');
                return {id,manualCommands:commands,manualRejections:rejections,autoActions:recipe.actions.length,autoCommands:trace.length,autoRejections:trace.filter(r=>r.rejected).length,autoTrace:trace,passed:true};
            }""",id))
        assert not errors;b.close()
    a.output.write_text(json.dumps({'runtime':'actual Chromium','cases':results,'pageErrors':errors,'passed':True},indent=2)+'\n')
    print('PASS actual Chromium2 world nova optical workflows, manual primitive steps and product autoActions')
if __name__=='__main__':main()
