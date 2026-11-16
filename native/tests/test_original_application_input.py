"""Public prompt-to-source-application integration; root owns active prompt wiring.

Selection remains additive: source weather uses the pre-edit scalar count while
current selection replacement supplies the resulting draft to the source painter.
"""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import gzip,json,os,subprocess,tempfile,unittest
from pathlib import Path
from native.tests import test_original_atelier_application_particles as particles
from native.tests import test_original_atelier_windows as windows
class OriginalApplicationInput(unittest.TestCase):
 setUpClass=classmethod(particles.AtelierApplicationParticles.setUpClass.__func__)
 tearDownClass=classmethod(particles.AtelierApplicationParticles.tearDownClass.__func__)
 def test_genuine_prior_application_snapshots_then_input_and_unchanged_draft(self):
  for name in ('window-application-schema69.bin.gz','original-camera-schema74.bin.gz','original-schema80-atelier-windows.snapshot.gz'):
   for op in ('input','draft'):
    with windows.NativeScene(5) as scene:
     scene.restore(gzip.decompress((windows.ROOT/'tests/fixtures'/name).read_bytes()));info=scene.info();frame=scene.render();old=info['prompt']['text'];new='🌙' if op=='input' else old;style=info['windowApplication']['weatherStyle'];time=info['clock']['timeUs']
     expected=self.page.evaluate("""r=>{const m=new MODULES.atelier.AtelierModel();m.resize(r.width,r.height);m.configure({weatherStyle:r.style});m.draft=r.old;m.setTime(r.time/1000);m[r.op==='input'?'input':'replaceDraft'](r.next);return m.events.map(({id,x,y,atMs,kind})=>({id,x,y,atMs,kind}))}""",dict(width=frame.width,height=frame.height,old=old,next=new,style=style,time=time,op=op))
     scene.command(dict(op=op,text=new));self.assertEqual(scene.info()['windowApplication']['events'],expected,(name,op));scene.render()
 def test_public_input_draft_source_events_and_frames(self):
  cases=[('input','','hello',None,True),('input','😀ab','🌑𐀀x',None,True),('input','a'*123,'b'*70,None,True),('input','abc','',None,True),('draft','abc','abc',None,True),('draft','','',None,True),('draft','abc','a',None,True),('draft','😀','ab',None,True),('draft','ab','😀',None,True),('draft','abcd','abX',None,True),('draft','😀ab','😀',None,True),('draft','','hello',None,False),('draft','abc','abc',None,False),('input','A😀BCD','🌙',(1,4),True)]
  captures=[]
  for style in ('embers','sparks','nova','rain','snow','ripples'):
   for index,(op,old,text,selection,emit) in enumerate(cases):
    final=text if op=='draft' else old+text if selection is None else old[:selection[0]]+text+old[selection[1]:]
    original=self.page.evaluate("""r=>{const m=new MODULES.atelier.AtelierModel();m.resize(136,44);m.setScene('windows');m.configure({weatherStyle:r.style});m.draft=r.old;m.setTime(1000);if(!r.emit)m.draft=r.text;else m[r.op==='input'?'input':'replaceDraft'](r.text);if(r.selection)m.draft=r.final;m.setTime(1175);return {events:m.events.map(({id,x,y,atMs,kind})=>({id,x,y,atMs,kind})),frame:Array.from(atelierApp.renderer.render(m).frame.cells)}}""",dict(op=op,old=old,text=text,selection=selection,final=final,style=style,emit=emit))
    commands=windows.commands(draft=old)+[dict(op='window-application',weatherStyle=style)]
    edits=[]
    if selection:edits.append(dict(op='select',anchor=selection[0],caret=selection[1]))
    edit=dict(op=op,text=text)
    if op=='draft':edit['emitWeather']=emit
    edits.append(edit)
    with windows.NativeScene(2030) as scene:
     for command in commands:scene.command(command)
     scene.advance_to(1000000)
     for command in edits:scene.command(command)
     info=scene.info();self.assertEqual(info['prompt']['text'],final);self.assertEqual(info['windowApplication']['events'],original['events'],(style,index,op,old,text))
     scene.advance_to(1175000);actual=list(memoryview(scene.render().bytes).cast('I'));expected=windows.map_hits(original['frame']);self.assertEqual(actual,expected,(style,index))
    captures.append(dict(name=style+'-'+str(index),commands=commands,edits=edits,expected=expected,events=original['events'],native=actual,original=original['frame']))
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'cases.json';p.write_text(json.dumps(captures));run=subprocess.run(['node',str(windows.ROOT/'tests/original_application_input_wasm.mjs'),str(windows.ROOT/'dist/nocturne_native.wasm'),str(p)],capture_output=True,text=True);self.assertEqual(run.returncode,0,run.stderr);results=json.loads(run.stdout)
  self.assertEqual(len(captures),len(results))
  for capture,result in zip(captures,results):self.assertEqual(result['frame'],capture['expected'],capture['name']);self.assertEqual(result['events'],capture['events'],capture['name']);capture['wasm']=result['frame']
  if os.environ.get('NOCTURNE_APPLICATION_INPUT_CAPTURE'):
   p=Path(os.environ['NOCTURNE_APPLICATION_INPUT_CAPTURE']);p.mkdir(parents=True,exist_ok=True);(p/'frames.json.gz').write_bytes(gzip.compress(json.dumps(captures,separators=(',',':')).encode(),mtime=0))
if __name__=='__main__':unittest.main()
