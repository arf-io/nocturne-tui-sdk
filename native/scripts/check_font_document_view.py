#!/usr/bin/env python3
"""Real native/font consuming examples and actual Chromium outline painting."""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=True)
    target=a.output/'gallery.html'
    subprocess.run([sys.executable,str(ROOT/'examples/font_document_screen.py'),
        '--library',os.environ['NOCTURNE_HARFBUZZ_LIBRARY'],
        '--font',os.environ['NOCTURNE_SHAPING_FONT'],'--output',str(target),
        '--evidence',str(a.output/'examples.json')],check=True)
    errors=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=os.environ.get('CHROMIUM'))
        page=browser.new_page(viewport={'width':1400,'height':1000})
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content(target.read_text())
        actual=page.evaluate("""()=>Array.from(document.querySelectorAll('article')).map(panel=>{
            const svg=panel.querySelector('svg[data-font-document]');
            const paths=Array.from(svg.querySelectorAll('path[data-identities]'));
            if(!paths.length||!paths.every(p=>p.getAttribute('d')&&p.getBoundingClientRect().width>0))throw Error('unpainted outline');
            return {id:panel.id,paths:paths.length,paintedBounds:svg.getBoundingClientRect().toJSON(),passed:true};
        })""")
        assert len(actual)==8 and not errors
        page.screenshot(path=str(a.output/'browser.png'),full_page=True)
        browser.close()
    report={'sourceCommit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'scope':'Actual native/HarfBuzz application view and Chromium SVG outline rendering; not full SDK qualification',
        'runtime':'real Chromium','cases':actual,'pageErrors':errors,'passed':True,
        'htmlSha256':hashlib.sha256(target.read_bytes()).hexdigest()}
    (a.output/'browser.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS real font document8examples, guarded native source interactions and actual Chromium outlines')

if __name__=='__main__':main()
