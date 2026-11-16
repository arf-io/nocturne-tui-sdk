"""Build the self-contained Pearl Fleet gallery using the actual C/WASM renderer.
No network dependency or fonts are embedded. Run tsc and build.sh --wasm first.
"""
from pathlib import Path
import base64,json,re
ROOT=Path(__file__).resolve().parents[1]
data={'wasm':base64.b64encode((ROOT/'dist/nocturne.wasm').read_bytes()).decode(),'schema':json.loads((ROOT/'studio.schema.json').read_text()),'palettes':json.loads((ROOT/'palettes.json').read_text())['palettes']}
html=(ROOT/'web/fleet.template.html').read_text().replace('__FLEET_DATA__',json.dumps(data,separators=(',',':')).replace('</','<\\/'))
for token,name in [('__STUDIO_ENGINE__','studio'),('__FLEET_MODEL__','fleet-model'),('__FLEET_VIEW__','fleet-view'),('__FLEET_CONTROLLER__','fleet')]:
    js=(ROOT/f'dist/typescript/{name}.js').read_text()
    js=re.sub(r'^import .*?;\s*','',js,flags=re.M)
    js=re.sub(r'^export \* from .*?;\s*','',js,flags=re.M)
    js=re.sub(r'^export ','',js,flags=re.M)
    exports={'studio':['StudioEngine'],'fleet-model':['FleetModel','TranscriptViewport','FLEET_LIMITS','checkedInt','createDemoFleet','DEMO_NOTES','demoMetrics'],'fleet-view':['composeFleet'],'fleet':['FleetController','DEFAULT_FLEET_OPTIONS']}[name]
    names=','.join(exports)
    html=html.replace(token,'const {'+names+'}=(()=>{\n'+js+'\nreturn {'+names+'};\n})();')
(ROOT/'Nocturne-Pearl-Fleet.html').write_text(html)
print('Built Nocturne-Pearl-Fleet.html:',len(html.encode()),'bytes')
