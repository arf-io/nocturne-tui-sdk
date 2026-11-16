#!/usr/bin/env python3
"""Capture every declared component state from the actual gallery and native core."""
from pathlib import Path
import argparse,base64,gzip,hashlib,json,os,re,shutil,sys
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'native/bindings/python'))
from nocturne_native import NativeScene

def sha(data):return hashlib.sha256(data).hexdigest()
def label(path):
 try:return Path(path).resolve().relative_to(ROOT).as_posix()
 except ValueError:return Path(path).name
def capture(gallery,registry,output,library,only=None):
 gallery=Path(gallery);registry=Path(registry);output=Path(output);library=Path(library)
 manifest=json.loads(registry.read_text());components=manifest['components']
 if len({x['id'] for x in components})!=len(components):raise ValueError('Duplicate component identity')
 inputs=[gallery,registry,library,ROOT/'native/dist/nocturne_native.wasm'];sources={label(p):sha(p.read_bytes()) for p in inputs}
 output.mkdir(parents=True,exist_ok=True);records=[];imageNames={};errors=[]
 with NativeScene(library=library) as native,sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
  page.on('pageerror',lambda e:errors.append(str(e)));page.goto(gallery.resolve().as_uri());page.wait_for_function('window.nativeLab && window.nativeView');page.evaluate('nativeLab.hold()')
  for component in components:
   if only and component['id'] not in only:continue
   for state in component['states']:
    request={'component':component['id'],'state':state}
    result=page.evaluate(r"""async request=>{
      const {state}=request;nativeLab.hold();nativeLab.scene.command({op:'reset',seed:2030});
      document.querySelector('#prompt-mode').value='marquee';document.querySelector('#prompt-alpha').value='0.22';document.querySelector('#palette').value='';
      if(state.projectId){
        const select=document.querySelector('#scenes'),value='project:'+state.projectId;
        if(![...select.options].some(o=>o.value===value))throw Error('Missing reference project '+state.projectId);
        select.value=value;select.dispatchEvent(new Event('change',{bubbles:true}));
      }else{
        let recipe=state.recipeId?nativeLab.example(state.recipeId):{id:'reference-'+request.component,name:request.component,subtitle:'',commands:state.commands,viewport:{width:80,height:24}};
        if(!recipe)throw Error('Missing reference recipe '+state.recipeId);
        recipe={...recipe,viewport:recipe.viewport??{width:160,height:52}};nativeLab.load(recipe);
      }
      nativeLab.hold();
      if(state.timeUs){nativeLab.scene.command({op:'pause',paused:false});nativeLab.advance(state.timeUs);nativeLab.hold();}
      nativeLab.draw();const frame=nativeView.frame,info=nativeLab.scene.infoComplete();
      const b64=bytes=>{let s='';for(let i=0;i<bytes.length;i+=32768)s+=String.fromCharCode(...bytes.subarray(i,i+32768));return btoa(s);};
      const snapshot=nativeLab.scene.snapshot();
      const snapshotSha256=[...new Uint8Array(await crypto.subtle.digest('SHA-256',snapshot))].map(x=>x.toString(16).padStart(2,'0')).join('');
      const compressed=new Uint8Array(await new Response(new Blob([snapshot]).stream().pipeThrough(new CompressionStream('gzip'))).arrayBuffer());
      return {png:document.querySelector('#canvas').toDataURL('image/png').split(',')[1],cells:b64(frame.bytes),snapshot:b64(compressed),snapshotBytes:snapshot.length,snapshotSha256,width:frame.width,height:frame.height,timeUs:info.clock.timeUs,build:info.build,schema:info.contract.snapshotSchema};
    }""",request)
    png=base64.b64decode(result.pop('png'));cells=base64.b64decode(result.pop('cells'));snapshot=gzip.decompress(base64.b64decode(result.pop('snapshot')))
    if len(snapshot)!=result['snapshotBytes'] or sha(snapshot)!=result['snapshotSha256']:raise AssertionError('Snapshot transport differs')
    native.restore(snapshot);nativeCells=native.render().bytes
    if cells!=nativeCells:raise AssertionError('Native/WASM cells differ: '+component['id']+'/'+state['id'])
    digest=sha(png);name=imageNames.setdefault(digest,component['id']+'-'+state['id']+'.png')
    if not (output/name).exists() or sha((output/name).read_bytes())!=digest:(output/name).write_bytes(png)
    records.append({'component':component['id'],'state':state['id'],'label':state['label'],'request':state,'image':name,'pngSha256':digest,'cellSha256':sha(cells),'nativeCellSha256':sha(nativeCells),'nativeWasmEqual':True,**result})
    print(component['id']+'/'+state['id'],flush=True)
  browser.close()
 if errors:raise RuntimeError('Browser errors: '+repr(errors))
 for p in inputs:
  if sha(p.read_bytes())!=sources[label(p)]:raise RuntimeError('Runtime or capture source changed: '+label(p))
 report={'schema':'nocturne.reference-captures.v1','scope':'Actual finite component/state captures; native snapshot replay equals WASM cells for every listed image. No exhaustive parameter or temporal claim.','sources':sources,'captureCount':len(records),'uniqueImages':len(imageNames),'captures':records,'pageErrors':errors}
 (output/'CAPTURES.json').write_text(json.dumps(report,indent=2)+'\n');return report

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--gallery',type=Path,default=ROOT/'native/Nocturne-RC4-Source-Build.html');p.add_argument('--registry',type=Path,default=ROOT/'docs/current/components.json');p.add_argument('--output',type=Path,default=ROOT/'docs/current/images');p.add_argument('--library',type=Path,default=ROOT/'native/dist/libnocturne_native.dylib' if sys.platform=='darwin' else ROOT/'native/dist/libnocturne_native.so');p.add_argument('--only');a=p.parse_args()
 result=capture(a.gallery,a.registry,a.output,a.library,set(a.only.split(',')) if a.only else None);print(json.dumps({'captures':result['captureCount'],'uniqueImages':result['uniqueImages']}))
if __name__=='__main__':main()
