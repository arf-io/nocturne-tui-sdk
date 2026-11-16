"""Explicitly regenerate golden fixtures after reviewing intended visual changes.

Do not run this as part of normal tests: expected hashes must remain independent
of the current renderer during regression checks.
"""
from pathlib import Path
import hashlib
import json
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne import Surface
presets=json.loads((ROOT/'presets.json').read_text())
fixtures=[]
for preset in presets:
    for time in [0,1201,6399]:
        fixture={'name':preset['id']+'-'+str(time),'values':{'width':84,'height':28,**preset['values']},'timeMs':time,'text':preset.get('text','Parity across bindings.')}
        for name in ['palette','starPalette']:
            if name in preset:fixture[name]=preset[name]
        fixtures.append(fixture)
fixtures.extend([
 {'name':'empty','values':{'width':0,'height':0},'timeMs':0,'text':''},
 {'name':'one-cell','values':{'width':1,'height':1,'layout':2},'timeMs':55,'text':'x'},
 {'name':'negative-origin','values':{'width':31,'height':14,'effect':5,'originX':-810,'originY':-91,'pixelMode':1},'timeMs':7316,'text':'origins'},
 {'name':'after-u32-time','values':{'width':45,'height':16,'effect':5,'colorMode':1,'layout':1},'timeMs':5000000017,'text':'long-running clock'},
 {'name':'full-hue-wheel','values':{'width':53,'height':17,'effect':5,'colorMode':1,'pixelMode':1,'stars':0},'timeMs':7733,'text':''},
 {'name':'custom-glyphs','values':{'width':51,'height':13,'densityPermille':600,'starFloorPermille':120},'timeMs':1527,'text':'','glyphs':['.','·','⠁','⋅'],'starPalette':['#BB99AA','#AABBAA']},
 {'name':'unsafe-demo-text','values':{'width':49,'height':18,'layout':1},'timeMs':331,'text':'a\u001b[31m\n世界'},
])
for fixture in fixtures:
    surface=Surface(**fixture['values'])
    if 'palette' in fixture:surface.setPalette(fixture['palette'])
    if 'starPalette' in fixture:surface.setStarPalette(fixture['starPalette'])
    if 'glyphs' in fixture:surface.setGlyphs(fixture['glyphs'])
    frame=surface.render(fixture['timeMs'],text=fixture['text'])
    fixture['sha256']=hashlib.sha256(frame.tobytes()).hexdigest()
(ROOT/'tests/fixtures.json').write_text(json.dumps(fixtures,indent=2,ensure_ascii=False)+'\n')
print('Wrote',len(fixtures),'reviewable golden fixtures')
