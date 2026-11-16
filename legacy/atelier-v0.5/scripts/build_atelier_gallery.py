#!/usr/bin/env python3
"""Bundle actual modules + WASM into a standalone gallery. No network or fonts.
Each module is isolated and destructures its real dependencies; exports remain
in a local module table. This is a narrow ES2020 bundler for our compiled files,
not a general JavaScript parser. Fail closed on unhandled module syntax.
"""
from pathlib import Path
import base64, json, re, subprocess
ROOT=Path(__file__).resolve().parents[1]
modules=['studio','observatory','cell_profile','spatial','text_fx','particles','window_fx','atelier','atelier_settings']
parts=['const MODULES={};']
for name in modules:
    js=(ROOT/f'dist/typescript/{name}.js').read_text()
    exports=re.findall(r'^export (?:class|function|const|let) (\w+)',js,re.M)
    js=re.sub(r'^import\s*\{([^}]+)\}\s*from [\'\"]\./([^\'\"]+)\.js[\'\"];',lambda m:'const {'+m.group(1)+'}=MODULES['+json.dumps(m.group(2))+'];',js,flags=re.M)
    js=re.sub(r'^export ','',js,flags=re.M)
    if re.search(r'^import |^export ',js,re.M):raise RuntimeError('Unhandled module declaration '+name)
    parts.append('MODULES['+json.dumps(name)+']=(()=>{\n'+js+'\nreturn {'+','.join(exports)+'};})();')
# Only host-facing imports are exposed globally; private names stay isolated.
imports={'studio':['StudioEngine'],'observatory':['MotionClock','OBSERVATORY_CONTROLS','BACKGROUND_STYLES','rgb','finite','clamp'],'spatial':['layoutOptions','validateGraph'],'text_fx':['TEXT_EFFECTS','TEXT_RANGES'],'particles':['PARTICLE_RANGES'],'window_fx':['WINDOW_EFFECTS','WINDOW_SHAPES','WINDOW_RANGES'],'atelier_settings':['exportAtelierSettings','loadAtelierSettings'],'atelier':['AtelierModel','AtelierRenderer','ATELIER_SCENES','activateAtelier','DEFAULT_GRAPH']}
for name,names in imports.items():parts.append('const {'+','.join(names)+'}=MODULES['+json.dumps(name)+'];')
try:build=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
except (FileNotFoundError,subprocess.CalledProcessError):build='source-archive'
data={'wasm':base64.b64encode((ROOT/'dist/nocturne.wasm').read_bytes()).decode(),'schema':json.loads((ROOT/'studio.schema.json').read_text()),'palettes':json.loads((ROOT/'palettes.json').read_text())['palettes'],'build':build}
html=(ROOT/'web/atelier.template.html').read_text().replace('__ATELIER_DATA__',json.dumps(data,separators=(',',':')).replace('</','<\\/')).replace('__ATELIER_MODULES__','\n'.join(parts))
(ROOT/'Nocturne-Spatial-Atelier.html').write_text(html)
(ROOT/'START-HERE.html').write_text(html)
print('Built Spatial Atelier:',len(html.encode()),'bytes')
