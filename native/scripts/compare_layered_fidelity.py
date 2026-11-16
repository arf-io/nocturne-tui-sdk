#!/usr/bin/env python3
"""Record a matched baseline/current native cell and Chromium raster comparison.

The baseline is an explicit SDK ZIP with a checked manifest. No compiler or font
is redistributed. Only commands accepted by BOTH contracts are used. These images
are visual evidence for coverage repair, not an artistic approval of every port.
"""
from pathlib import Path
import argparse,base64,hashlib,json,os,shutil,sys,tempfile,zipfile
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
from release_archive import verifyArchive

def digest(data):return hashlib.sha256(data).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('baseline',type=Path);p.add_argument('--output',type=Path,default=ROOT/'evidence/layered-fidelity');a=p.parse_args()
    manifest=verifyArchive(a.baseline);a.output.mkdir(parents=True,exist_ok=True)
    recipe=next(r for r in json.loads((ROOT/'recipes.json').read_text())if r['id']=='leaf-anatomy')
    commands=[]
    for c in recipe['commands']:
        c=dict(c)
        if c['op'] in ('emitter','floor'):c.pop('sampling',None);c.pop('surfaceAlpha',None)
        if c['op']=='environment':c['sampling']='braille'
        commands.append(c)
    commands=[{'op':'resize','width':160,'height':48},*commands,{'op':'time','timeUs':900000}]
    with tempfile.TemporaryDirectory(prefix='nocturne-baseline-') as temp:
        lib=Path(temp)/'baseline.so'
        with zipfile.ZipFile(a.baseline) as z:lib.write_bytes(z.read('nocturne-sdk/native/dist/libnocturne_native.so'))
        frames={}
        for name,library in [('before',lib),('after',None)]:
            with NativeScene(2030,library=library)as scene:
                for command in commands:scene.command(command)
                frame=scene.render();frames[name]=frame
        script="""({raw,width,height})=>{
            const bytes=Uint8Array.from(atob(raw),c=>c.charCodeAt(0)),words=new Uint32Array(bytes.buffer);
            const cv=document.querySelector('canvas'),ctx=cv.getContext('2d');cv.width=width*10;cv.height=height*20;
            const col=n=>'#'+n.toString(16).padStart(6,'0');ctx.font='16px "DejaVu Sans Mono", monospace';ctx.textBaseline='middle';
            for(let i=0;i<words.length;i+=4){const cell=i/4,x=cell%width*10,y=Math.floor(cell/width)*20;ctx.fillStyle=col(words[i+2]);ctx.fillRect(x,y,10,20);}
            for(let i=0;i<words.length;i+=4){const g=words[i];if(g===0||g===32)continue;const cell=i/4,x=cell%width*10,y=Math.floor(cell/width)*20;ctx.fillStyle=col(words[i+1]);if(g===0x2580)ctx.fillRect(x,y,10,10);else if(g===0x2584)ctx.fillRect(x,y+10,10,10);else ctx.fillText(String.fromCodePoint(g),x,y+11);}
        }"""
        report={'scope':'Matched current/baseline native geometry and identical browser raster at 900000 us; not whole historical artistic acceptance.','baselineArchive':a.baseline.name,'baselineSha256':digest(a.baseline.read_bytes()),'baselineCommit':manifest['sourceCommit'],'baselineLibrarySha256':digest(lib.read_bytes()),'commands':commands,'cases':{}}
        with sync_playwright()as pw:
            browser=pw.chromium.launch(headless=True,executable_path=os.environ.get('CHROMIUM')or shutil.which('chromium'),args=['--no-sandbox']);page=browser.new_page(viewport={'width':1620,'height':980},device_scale_factor=1)
            page.set_content('<html><body style="margin:0"><canvas></canvas></body></html>')
            for name,frame in frames.items():
                path=a.output/(name+'-matched-anatomy');path.with_suffix('.cells').write_bytes(frame.bytes)
                page.evaluate(script,{'raw':base64.b64encode(frame.bytes).decode(),'width':frame.width,'height':frame.height});page.locator('canvas').screenshot(path=str(path.with_suffix('.png')))
                glyphs=[word[0]for word in frame.words()];patterns=set(g for g in glyphs if 0x2800<g<0x28ff)
                report['cases'][name]={'cellsSha256':digest(frame.bytes),'pngSha256':digest(path.with_suffix('.png').read_bytes()),'width':frame.width*10,'height':frame.height*20,'partialBraillePatterns':len(patterns),'fullBrailleCells':glyphs.count(0x28ff),'partialBrailleCells':sum(0x2800<g<0x28ff for g in glyphs)}
            report['browser']=browser.version;browser.close()
        (a.output/'MATCHED-COMPARISON.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['cases'],indent=2))
if __name__=='__main__':main()
