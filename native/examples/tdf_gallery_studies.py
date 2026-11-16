"""Actual retained TDF rasterizations exposed through the normal native gallery."""
import json
from pathlib import Path
from tdfiglet_scene import build_cases

SPECIMENS=Path(__file__).with_name('tdf_specimens.json')

def build_tdf_gallery_studies():
 """The retained specimens as Gallery cases; none when the data is not in this tree (the public tree leaves it out)."""
 if not SPECIMENS.is_file():return []
 cases=[]
 for item in json.loads(SPECIMENS.read_text()):
  art={'width':item['width'],'height':item['height'],'cells':[word for cell in item['cells']for word in [*cell,0]]}
  for case in build_cases(art):
   case.update(id='original-tdf-'+str(item['subfont'])+'-'+case['mode'],name='TDF / '+item['label']+' / '+case['mode'],subtitle='Actual TheDraw font typography retained as native colored cell art.',demo=True,provenance={'release':'TDF renderer ingress','component':'Actual tdfiglet subfont '+str(item['subfont']),'fontSha256':item['fontSha256'],'formatterSha256':item['formatterSha256'],'sourceCommandsSha256':item['sourceCommandsSha256'],'sourceText':item['text']})
   cases.append(case)
 return cases
