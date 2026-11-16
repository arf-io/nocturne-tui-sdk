"""One-time naming/provenance transformation; no historical engine is imported."""
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
ledger=json.loads((root/'port-ledger.json').read_text())
entries=[]
for e in ledger['entries']:
    name=e['newId'];family={'ParticleEmitter':0,'SurfaceField':1,'TextTransition':2,'WindowTransition':3}[e['nativeContract']]
    old=e['oldId'].split('/')[-1].split('.')[-1]
    if family==0:
        alg={'leaves':0,'rain':1,'snow':2,'embers':3,'nova':4,'firework':4,'sparks':6,'ripples':5}[old]
        if name in ['weather/ejecta-shell','weather/pressure-shell']:alg=5
    elif family==1:alg=['silk-tide','satin-rings','opal-fronts','interference-tide'].index(name.split('/')[-1])
    elif family==2:
        suffix=e['oldId'].split('/')[-1];alg={'immediate':0,'instant':0,'fade':1,'rain':2,'scramble':3,'flipboard':4,'sweep-left':5,'sweep-right':6,'marquee':7,'orbit':8,'constellation':9,'prism-stitch':10,'gravity-loom':11,'scanline':12,'elastic':13,'typewriter':14,'curtain':15,'fall':16,'ash':17,'lift':18,'iris':19,'prism-weave':20,'ink-tide':21,'comet-stitch':22,'fold':23,'zipper':24}.get(suffix,1)
    else:
        suffix=e['oldId'].split('/')[-1];alg={'fade':0,'bounce':1,'genie':2,'roll-up':3,'roll-down':4,'drawer-left':5,'drawer-right':6,'drawer-top':7,'drawer-bottom':8,'center':9,'top-left':10,'top-right':11,'bottom-left':12,'bottom-right':13,'iris':14,'explode':15,'explosion':15,'accordion':16,'portal':17,'orbital-bloom':18,'venetian':19,'ribbon-unfurl':20,'origami':21,'vortex':22,'ribbon':23,'petal':24,'gravity-well':25,'expand-center':9,'expand-nw':10,'expand-ne':11,'expand-sw':12,'expand-se':13,'circle':14,'ribbon-unspool':23,'petal-bloom':24}.get(suffix,9)
    entries.append({'id':name,'name':e['displayName'],'contract':e['nativeContract'],'family':family,'algorithm':alg,'visualAcceptance':'pending','sourceIdentity':e['oldId'],'profile':int('/atelier/' in e['oldId'])})
entries.extend([{'id':'weather/silver-squall','name':'Silver Squall','contract':'ParticleEmitter','family':0,'algorithm':1,'visualAcceptance':'pending','sourceIdentity':None,'profile':0},{'id':'weather/snowglobe','name':'Snowglobe','contract':'ParticleEmitter','family':0,'algorithm':2,'visualAcceptance':'pending','sourceIdentity':None,'profile':0}])
(root/'catalogue.json').write_text(json.dumps(entries,indent=2)+'\n')
public=[{k:v for k,v in e.items() if k not in ['family','sourceIdentity','algorithm','profile']} for e in entries]
(root/'src/catalog.inc').write_text('/* Current native effect identities; no historical runtime imports. */\nstatic const char CATALOGUE[]='+json.dumps(json.dumps(public,separators=(',',':')))+';\nstatic const struct {const char*id;int family,algorithm,profile;} EFFECTS[]={\n'+''.join('{'+json.dumps(e['id'])+','+str(e['family'])+','+str(e['algorithm'])+','+str(e['profile'])+'},\n' for e in entries)+'};\n')
print(len(entries),'catalogue identities; all visual acceptance pending')
