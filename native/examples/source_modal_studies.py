"""Modal layouts and controller actions."""
import gzip,json,copy,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'hosts/python'))
from atelier_windows import atelier_window_application_commands
def build_source_modal_studies():
 oracle=json.loads(gzip.decompress((ROOT/'tests/fixtures/source-modal/COMPOSED.json.gz').read_bytes()))
 def base():return [{'op':'resize','width':100,'height':40},{'op':'environment','presentation':'canvas','stars':0,'background':0x214365},{'op':'floor','enabled':False,'visible':False},{'op':'prompt','active':False}]
 def push(entry,context='modal'):return {'op':'source-modal','action':'push','entry':{k:v for k,v in entry.items() if k!='returnContext'},'context':context,'workspace':'windows'}
 def nodes(row):return [dict(op='source-stage-component',id=60000+i,legacyFlags=node.get('id',0),**{k:v for k,v in node.items() if k!='id'}) for i,node in enumerate(row['nodes'])]
 def case(id,title,commands,**extra):return {'id':'source-modal-'+id,'name':'Modal / '+title,'subtitle':'Workbench modal composition and native stack ownership.','viewport':{'width':100,'height':40},'commands':commands,'demonstrates':{'feature':'source-modal'},'demo':True,'mode':'isolated','sampleTimesUs':[0,140000,400000],'provenance':{'release':'Workbench / Black Hole','component':'Original modal '+title,'sourceSha256':'ea6cfebbbeb684fba58a07d87d8073788c6331fb12fd8925b0af7c5a29cf6192'},**extra}
 cases=[];kinds=list(dict.fromkeys(row['kind'] for row in oracle['rows']))
 for kind in kinds:
  rows=[r for r in oracle['rows'] if r['kind']==kind];row=rows[0];commands=base()+[push(row['entry'],row['context'])]+nodes(row)+[{'op':'source-modal','action':'associate','componentIds':[60000+i for i in range(len(row['nodes']))],'boxId':60000}]
  cases.append(case(kind,kind,commands,originalKind=kind,actions=[{'timeUs':r['time']*1000,'command':{'op':'batch','commands':nodes(r)}} for r in rows[1:]]))
 entry={'id':'same','kind':'center','title':'Stack','body':'Escape dismisses one layer.','atMs':0,'dismissible':True}
 nested=base()+[push(entry,'commands'),{'op':'source-modal','action':'edit','context':'commands','query':'restored query','selected':3,'workspace':'windows'}]+[push(entry,'modal') for _ in range(7)]
 cases.append(case('eight-layers','eight retained layers',nested,expectedSourceModal={'depth':8}))
 pair=base()+[push(entry,'commands'),{'op':'source-modal','action':'edit','query':'restored query','selected':3},push(entry,'modal')]
 cases.append(case('dismiss','restore one context',pair,actions=[{'timeUs':140000,'command':{'op':'source-modal','action':'dismiss'}}],expectedSourceModal={'depth':1,'context':'commands','query':'restored query','selected':3}))
 cases.append(case('clear','clear the active stack',pair,actions=[{'timeUs':140000,'command':{'op':'source-modal','action':'clear'}}],expectedSourceModal={'depth':0}))
 cases.append(case('nondismissible','retain a nondismissible layer',base()+[push({**entry,'dismissible':False})],actions=[{'timeUs':140000,'command':{'op':'source-modal','action':'dismiss'}}],expectedSourceModal={'depth':1}))
 applications=[]
 for original in cases:
  item=copy.deepcopy(original);item['id']+='-application';item['mode']='application';item['name']+=' / Atelier application';item['subtitle']='Modal controls over the Atelier window application.';item.pop('originalKind',None);item['commands']=atelier_window_application_commands('genie',width=100,height=40)+item['commands'][4:];item['provenance']['wholeSceneHistoricalParity']=False;applications.append(item)
 return cases+applications
