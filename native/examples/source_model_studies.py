"""OBJ model geometry and gallery resource validation."""
import base64,hashlib,json
from pathlib import Path

def build_source_model_studies():
 case=json.loads(Path(__file__).with_name('orbital-loom-model.json').read_text())
 records=decode_model_records(case)
 if hashlib.sha256(records).hexdigest()!=case['provenance']['recordsSha256']:raise ValueError('Model resource hash differs')
 return [case]

def decode_model_records(case):
 if 'modelRecords'not in case:return None
 text=case['modelRecords']
 if not isinstance(text,str):raise ValueError('Model resource must be canonical base64')
 try:records=base64.b64decode(text,validate=True)
 except Exception as error:raise ValueError('Model resource must be canonical base64')from error
 if base64.b64encode(records).decode()!=text or len(records)%40:raise ValueError('Model resource must be canonical aligned base64')
 pending=list(case['commands'])
 while pending:
  command=pending.pop()
  if command.get('op')=='reset':raise ValueError('Model resource recipe cannot reset its resource')
  if command.get('op')=='batch':pending.extend(command.get('commands',[]))
 return records

def verify_model_resource(scene,case,records):
 if records is None:return
 if scene.model_records()!=records:raise RuntimeError('Gallery model resource differs')
 minimum=case.get('modelVisibleMinCells')
 if minimum is None:return
 if isinstance(minimum,bool)or not isinstance(minimum,int)or minimum<1:raise ValueError('Invalid model raster minimum')
 saved=scene.snapshot();full=scene.render().bytes
 try:
  for sample in [b'',records[:256*40]]:
   scene.set_model_records(sample);other=scene.render().bytes
   changed=sum(full[i:i+12]!=other[i:i+12]for i in range(0,len(full),16))
   if changed<minimum:raise RuntimeError('Gallery full model raster missing')
 finally:scene.restore(saved)
 if scene.snapshot()!=saved:raise RuntimeError('Gallery model verification restore differs')
