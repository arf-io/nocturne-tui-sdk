"""Embed the actual WASM renderer and assets into an offline playable gallery."""
from pathlib import Path
import base64,json,re
root=Path(__file__).resolve().parents[1]
data={'wasm':base64.b64encode((root/'dist/nocturne.wasm').read_bytes()).decode(),'schema':json.loads((root/'studio.schema.json').read_text()),'palettes':json.loads((root/'palettes.json').read_text())['palettes'],'scenes':json.loads((root/'studio.scenes.json').read_text())['scenes']}
js=(root/'dist/typescript/studio.js').read_text();js=re.sub(r'^export ', '',js,flags=re.M)
html=(root/'web/studio.template.html').read_text().replace('__STUDIO_DATA__',json.dumps(data,separators=(',',':')).replace('</','<\\/')).replace('__STUDIO_ENGINE__',js)
(root/'Nocturne-Studio.html').write_text(html)
print('Built',root/'Nocturne-Studio.html',len(html),'characters')
