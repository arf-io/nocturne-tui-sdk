#!/usr/bin/env python3
"""Real embedded WASM application-area geometry, source, epoch and cell checks."""
from pathlib import Path
import argparse,hashlib,json,os
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();errors=[];records=[];html=ROOT/'Nocturne-Test-Harness.html'
 with sync_playwright() as playwright:
  browser=playwright.chromium.launch(headless=True,executable_path=os.environ.get('CHROMIUM'));page=browser.new_page(viewport={'width':1440,'height':1100});page.on('pageerror',lambda error:errors.append(str(error)));page.set_content(html.read_text());page.wait_for_function('window.nativeLab !== undefined');page.evaluate('nativeLab.hold()')
  ids=page.evaluate("nativeLab.recipes.filter(r=>r.demonstrates?.feature?.startsWith('application-area-')).map(r=>r.id)");assert len(ids)==38
  for id in ids:
   page.evaluate("id=>{nativeLab.load(nativeLab.recipes.find(r=>r.id===id));nativeLab.hold();}",id)
   result=page.evaluate("""id=>{const recipe=nativeLab.recipes.find(r=>r.id===id),s=nativeLab.scene;let samples=0;
    for(const t of recipe.sampleTimesUs){s.command({op:'pause',paused:false});s.advanceTo(t);s.command({op:'pause',paused:true});const before=s.snapshot();nativeLab.draw();
     for(const check of recipe.areaGeometryChecks){const row=s.areaGeometry(check.id);if(!row||row.length!==12||row.some((v,i)=>v!==check.row[i]))throw Error('area geometry '+id);}
     for(const check of recipe.areaMessageChecks.filter(c=>c.timeUs===t)){const m=s.info().messages.find(m=>m.id===check.id);if(!m||['state','startUs','text'].some(f=>m[f]!==check[f]))throw Error('area source/epoch '+id);}
     for(const check of recipe.expectedCharacterCells.filter(c=>c.timeUs===t)){const cell=s.inspectCharacterCell(check.x,check.y);if(cell.glyph!==check.glyph)throw Error('area cell '+id+' '+cell.glyph+' != '+check.glyph);}
     const after=s.snapshot();if(!before.every((v,i)=>v===after[i]))throw Error('render/query mutation');samples++;
    }return {id,samples};} """,id);records.append(result)
  assert not errors,errors;browser.close()
 result={'runtime':'actual Chromium embedded WASM gallery','htmlSha256':hashlib.sha256(html.read_bytes()).hexdigest(),'cases':records,'samples':sum(r['samples'] for r in records),'pageErrors':errors,'passed':True};args.output.write_text(json.dumps(result,indent=2)+'\n');print('PASS actual browser38 area scenes190 samples, independent geometry/source/queue/cells and pure composition')
if __name__=='__main__':main()
