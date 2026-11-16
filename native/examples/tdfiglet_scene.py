#!/usr/bin/env python3
"""Rasterize a local TDF font once and retain it as native colored cell art.

 python3 native/examples/tdfiglet_scene.py --binary /path/tdfiglet \
   --font /path/font.tdf --subfont 0 --output /new/output NOC
No font/binary is copied into the SDK. All animation is native after ingress.
"""
from pathlib import Path
import argparse,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent/'integrations'))
sys.path.insert(0,str(ROOT/'bindings/python'))
from tdfiglet_bridge import renderFont
from nocturne_native import NativeScene

def art_command(art,identity=1,x=3,y=5):
 cells=art['cells']
 if len(cells)!=art['width']*art['height']*4:raise ValueError('Malformed cell-art shape')
 return {'op':'cell-art','id':identity,'width':art['width'],'height':art['height'],'cells':[cells[i:i+3] for i in range(0,len(cells),4)],'x':x,'y':y,'layer':'overlay','alpha':1}

def baseline_commands(art):
 """Keep every source cell in bounds for the independent exact-color check."""
 return [{'op':'resize','width':max(100,art['width']+16),'height':max(40,art['height']+16)},
  {'op':'draft','text':'Native typography application / editable prompt','emitWeather':False},
  {'op':'indicator','id':1,'x':3,'y':max(32,art['height']+8),'sequence':'◐◓◑◒','stepMs':150},
  art_command(art)]

def build_cases(art):
 """Reuse one rasterization in isolated and composed public-command screens."""
 from screen_backdrop import world,application
 width=max(100,art['width']+16);height=max(40,art['height']+16)
 cases=[]
 for mode in ('isolated','application'):
  base=world()+application() if mode=='application' else [{'op':'prompt','active':False}]
  commands=base+[{'op':'resize','width':width,'height':height},art_command(art)]
  if mode=='application':commands.extend([{'op':'environment','style':'plasma'},
   {'op':'text','id':91,'text':'TDF / retained color typography','x':3,'y':art['height']+8,'effect':'text/ink-dissolve','durationMs':800}])
  actions=[{'timeUs':750000,'command':{'op':'cell-art','id':1,'alpha':.5,'x':7}},
   {'timeUs':1500000,'command':{'op':'cell-art','id':1,'alpha':0,'x':10}},
   {'timeUs':2000000,'command':{'op':'cell-art','id':1,'alpha':1,'x':3}}]
  cases.append({'id':'tdf-typography-'+mode,'mode':mode,'commands':commands,
   'demonstrates':{'feature':'tdf-color-typography'},'actions':actions,'autoActions':True,
   'sampleTimesUs':[0,750000,1500000,2000000],
   'cellArtSampleChecks':[{'timeUs':time,'id':1,'x':x,'y':5,'alpha':alpha,'width':art['width'],'height':art['height'],
     'cells':[art['cells'][i:i+3] for i in range(0,len(art['cells']),4)]}
    for time,x,alpha in [(0,3,1),(750000,7,.5),(1500000,10,0),(2000000,3,1)]]})
 return cases

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--binary',required=True,type=Path);p.add_argument('--font',required=True,type=Path);p.add_argument('--subfont',type=int,default=0);p.add_argument('--output',required=True,type=Path);p.add_argument('--mode',choices=['isolated','application','both'],default='application');p.add_argument('text');a=p.parse_args()
 art=renderFont(a.binary,a.font,a.subfont,a.text);command=art_command(art)
 commands=baseline_commands(art)
 a.output.mkdir(parents=True,exist_ok=False)
 (a.output/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
 (a.output/'cell-art.json').write_text(json.dumps(command,indent=2)+'\n')
 cases=[case for case in build_cases(art) if a.mode=='both' or case['mode']==a.mode]
 (a.output/'cases.json').write_text(json.dumps(cases,indent=2)+'\n')
 from gallery_cases import execute
 demonstrations=execute(cases)
 (a.output/'GALLERY-RESULTS.json').write_text(json.dumps({'scope':'Actual TDF rasterization reused in isolated/composed native scenes','fontSha256':hashlib.sha256(a.font.read_bytes()).hexdigest(),'cases':demonstrations},indent=2)+'\n')
 samples=[]
 with NativeScene() as s:
  for c in commands:s.command(c)
  checkpoint=s.snapshot();frame=s.render();originalFrame=frame.bytes;words=frame.words()
  for k,cell in enumerate(command['cells']):
   if cell[0]:
    actual=words[(command['y']+k//command['width'])*frame.width+command['x']+k%command['width']][:3]
    if actual!=tuple(cell):raise RuntimeError(f'Native color/scalar mismatch at {k}: {actual}, {cell}')
  for alpha,x in [(1,3),(.5,7),(0,10)]:
   s.command({'op':'cell-art','id':1,'alpha':alpha,'x':x});before=s.snapshot();frame=s.render()
   if before!=s.snapshot():raise RuntimeError('Render mutation')
   samples.append({'alpha':alpha,'x':x,'frameSha256':hashlib.sha256(frame.bytes).hexdigest()})
  s.restore(checkpoint)
  if s.render().bytes!=originalFrame:raise RuntimeError('Snapshot replay mismatch')
 result={'binarySha256':hashlib.sha256(a.binary.read_bytes()).hexdigest(),'fontSha256':hashlib.sha256(a.font.read_bytes()).hexdigest(),'subfont':a.subfont,'text':a.text,'width':art['width'],'height':art['height'],'exactNativeCells':True,'renderPure':True,'snapshotReplay':True,'samples':samples}
 (a.output/'RESULTS.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result))
if __name__=='__main__':main()
