"""Embed compiled source and the real WASM cell renderer in a portable gallery.
No fonts, third-party runtime downloads, or image-generation substitutes.
"""
from pathlib import Path
import base64,json,re
ROOT=Path(__file__).resolve().parents[1]
data={'wasm':base64.b64encode((ROOT/'dist/nocturne.wasm').read_bytes()).decode(),'schema':json.loads((ROOT/'studio.schema.json').read_text()),'palettes':json.loads((ROOT/'palettes.json').read_text())['palettes'],'recipes':json.loads((ROOT/'observatory.recipes.json').read_text())['recipes']}
html=(ROOT/'web/observatory.template.html').read_text().replace('__OBS_DATA__',json.dumps(data,separators=(',',':')).replace('</','<\\/'))
for token,name,names in [('__STUDIO_ENGINE__','studio',['StudioEngine']),('__OBS_ENGINE__','observatory',['ObservatoryModel','ObservatoryRenderer','MotionClock','ModulationBus','OBSERVATORY_SCENES','OBSERVATORY_CONTROLS','BACKGROUND_STYLES','WEATHER_STYLES','MODULATION_TARGETS','activateObservatory','editScratch','validateOptions','hex','rgb','clamp'])]:
 js=(ROOT/f'dist/typescript/{name}.js').read_text();js=re.sub(r'^import .*?;\s*','',js,flags=re.M);js=re.sub(r'^export ','',js,flags=re.M)
 html=html.replace(token,'const {'+','.join(names)+'}=(()=>{\n'+js+'\nreturn {'+','.join(names)+'};\n})();')
(ROOT/'Nocturne-Observatory.html').write_text(html)
print('Built Nocturne-Observatory.html',len(html.encode()),'bytes')
