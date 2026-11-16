"""Actual archived Kinetic text sampler/putCell versus public current C SDK."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import json,os,subprocess,sys,tempfile,unittest,struct,hashlib,gzip
from pathlib import Path
from native.tests.historical_reference import load_rc2_workbench
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'));sys.path.insert(0,str(ROOT/'hosts/python'))
from nocturne_native import NativeScene
from atelier_application import TEXT_TRANSITIONS,atelier_text_command
EFFECTS=[k.split('/')[1] for k in TEXT_TRANSITIONS if k.startswith('kinetic/')]
class OriginalText(unittest.TestCase):
 def test_source_paint_lifecycle_and_historical_routes(self):
  with NativeScene(2030,library=os.environ.get('NOCTURNE_NATIVE_LIBRARY')) as scene:
   for effect in EFFECTS:
    command=atelier_text_command('N',f'kinetic/{effect}');self.assertEqual(command['phaseModel'],'source-paint');self.assertEqual(command['seed'],2030);self.assertTrue(command['alphabet'].endswith('+-*/!?'))
   command=atelier_text_command('NOCTURNE','kinetic/rain');scene.command(command);self.assertEqual(scene.info_complete()['textRuns'][0]['phaseModel'],'source-paint')
   scene.advance_to(425000);before=scene.snapshot();pose=scene.text_sample(1,0);frame=scene.render().bytes;self.assertEqual(scene.snapshot(),before)
   for patch in ({'phaseModel':'unknown'},{'phaseModel':3},{'effect':'weather/chrysanthemum','phaseModel':'source-paint'}):
    with self.assertRaises(ValueError):scene.command({'op':'text','id':1,**patch})
    self.assertEqual(scene.snapshot(),before)
   scene.command({'op':'text','id':1,'x':25});self.assertEqual(scene.text_sample(1,0)[:7],pose[:7]);self.assertEqual(scene.info_complete()['textRuns'][0]['phaseModel'],'source-paint')
   scene.restore(before);self.assertEqual(scene.render().bytes,frame)
   scene.advance_to(6000000);frame=scene.render().bytes
   scene.command({'op':'material','id':15,'channels':{'l':.64,'c':.15,'h':270},'scope':'characters','hueStep':9});self.assertTrue(scene.render().bytes!=frame,'visible source text responds to material palette update')
   scene.command({'op':'clear','scope':'text'});scene.command({'op':'text','id':1,'text':'N','effect':'text/ink-dissolve'});self.assertFalse(scene.info_complete()['textRuns'][0]['phaseModelExplicit'])
  sys.path.insert(0,str(ROOT/'examples'))
  from gallery_cases import build_cases
  textcases=[c for c in build_cases() if c.get('id','').startswith('study-text-') and c.get('demonstrates',{}).get('effect') in [TEXT_TRANSITIONS['kinetic/'+e] for e in EFFECTS]]
  self.assertEqual(len(textcases),36)
  for case in textcases:self.assertEqual(next(c for c in case['commands'] if c.get('op')=='text' and c.get('id')==1)['phaseModel'],'source-paint')
 def test_original_18_effects_both_phases_actual_frames(self):
  library=os.environ.get('NOCTURNE_NATIVE_LIBRARY');cases=[];actual=[]
  with tempfile.TemporaryDirectory(prefix='original-text-') as temp:
   tmp=Path(temp);original=tmp/'original.html';original.write_text(load_rc2_workbench())
   for effect in EFFECTS:
    for phase in ('reveal','hide'):
     for variant in (0,1):
      style=dict(textLightness=.83 if not variant else .71,textChroma=.1 if not variant else .18,hueOffset=0 if not variant else 103,hueStep=13 if not variant else -27,textHueSpeed=12 if not variant else -7,alpha=1 if not variant else .57)
      options=dict(effect=effect,phase=phase,seed=2030 if not variant else 4294967295,durationMs=1200,staggerMs=24,jitterMs=360,batchSize=1 if not variant else 3,distanceRows=18,scatterCols=5,speedVariation=.4,scrambleHz=24,alphabet=' ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+-*/!?',cycles=3,wind=1.3,overshoot=.2,easing='smooth' if not variant else 'sine',originX=24,originY=30,width=60,hueSpread=10)
      text='NØ✦aB' if not variant else 'A\nN✦\tZ'
      with NativeScene(2030,library=library) as scene,NativeScene(2030,library=library) as base:
       common_commands=({'op':'resize','width':96,'height':80},{'op':'prompt','active':False},{'op':'environment','stars':0,'presentation':'canvas'},{'op':'floor','visible':False})
       for target in (scene,base):
        for command in ({'op':'resize','width':96,'height':80},{'op':'prompt','active':False},{'op':'environment','stars':0,'presentation':'canvas'},{'op':'floor','visible':False}):target.command(command)
       material_command={'op':'material','id':2,'space':'oklch','scope':'characters','channels':{'l':style['textLightness'],'c':style['textChroma'],'h':{'initial':style['hueOffset'],'rate':style['textHueSpeed'],'min':0,'max':360,'boundary':'loop'}},'alpha':style['alpha'],'hueStep':style['hueStep']};scene.command(material_command)
       command={'op':'text','id':1,'text':text,'effect':TEXT_TRANSITIONS['kinetic/'+effect],'phase':'show' if phase=='reveal' else 'hide','phaseModel':'source-paint','x':24,'y':30,'width':60,'material':2,**{k:v for k,v in options.items() if k in ('seed','durationMs','staggerMs','jitterMs','batchSize','scrambleHz','alphabet','cycles','wind','overshoot','easing','hueSpread')},'distance':18,'scatter':5,'variation':.4}
       scene.command(command);initial=scene.snapshot()
       for ms in (0,425,1100,6000):
        scene.advance_to(ms*1000);base.advance_to(ms*1000);before=scene.snapshot();rendered=scene.render();self.assertEqual(scene.snapshot(),before)
        cases.append(dict(commands=[*common_commands,material_command,command],name=f'{effect}-{phase}-{variant}-{ms}',text=text,timeMs=ms,options=options,style=style,width=96,height=80,cells=list(struct.unpack('<'+'I'*(96*80*4),base.render().bytes))))
        actual.append(dict(cells=list(struct.unpack('<'+'I'*(96*80*4),rendered.bytes)),poses=[scene.text_sample(1,i) for i in range(len(text))]))
       final=scene.snapshot();scene.restore(initial);scene.advance_to(6000000);self.assertEqual(scene.snapshot(),final)
   request=tmp/'request.json';request.write_text(json.dumps(cases));r=subprocess.run(['node',str(ROOT/'tests/original_kinetic_text_oracle.mjs'),str(original),str(request)],capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stderr);expected=json.loads(r.stdout)
   run=subprocess.run(['node',str(ROOT/'tests/source_text_wasm.mjs'),str(ROOT/'dist/nocturne_native.wasm'),str(request)],capture_output=True,text=True)
   self.assertEqual(run.returncode,0,run.stderr);wasm_actual=json.loads(run.stdout)

   for c,got,want,wasm in zip(cases,actual,expected,wasm_actual):
    with self.subTest(case=c['name']):
     for p,q in zip(got['poses'],want['poses']):
      self.assertEqual(p[0],ord(q['glyph']));self.assertAlmostEqual(p[3]/65536,q['x'],delta=1/65536);self.assertAlmostEqual(p[4]/65536,q['y'],delta=1/65536);self.assertAlmostEqual(p[5]/1e6,q['opacity'],delta=1e-6);self.assertAlmostEqual(p[6]/1000,q['hue'],delta=.001)
     different=[i for i,(a,b) in enumerate(zip(got['cells'],want['cells'])) if a!=b];self.assertEqual(different,[],f'{c["name"]} {len(different)} different words: {[(i,got["cells"][i],want["cells"][i]) for i in different[:12]]}')
     self.assertEqual(wasm['cells'],want['cells'],c['name']+' WASM original-cell mismatch');self.assertEqual(wasm['poses'],[list(p) for p in got['poses']],c['name']+' WASM/native pose mismatch')
   if os.environ.get('NOCTURNE_TEXT_EVIDENCE'):
    directory=Path(os.environ['NOCTURNE_TEXT_EVIDENCE']);directory.mkdir(parents=True,exist_ok=True)
    payload=[dict(request=c,original=w,native=a,wasm=b) for c,w,a,b in zip(cases,expected,actual,wasm_actual)]
    raw=json.dumps(payload,separators=(',',':')).encode();(directory/'frames.json.gz').write_bytes(gzip.compress(raw,mtime=0))
    manifest=dict(frames=len(cases),poseSamples=sum(len(c['text']) for c in cases),exactNativeAndWasmCells=True,sourceHtmlSha256='375c4468c886728bc790b8d8cc3bdddc2a046532a4d792cde190f1b522a66385',archiveSha256=hashlib.sha256((directory/'frames.json.gz').read_bytes()).hexdigest())
    (directory/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

if __name__=='__main__':unittest.main()
