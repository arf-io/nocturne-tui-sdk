"""Select native weather painting on the ordinary catalogue routes."""
import copy

def apply_original_weather_routes(cases,catalogue):
    by_id={case['id']:case for case in cases};additions=[]
    for entry in catalogue:
        source=entry.get('sourceIdentity') or ''
        if not entry['id'].startswith('weather/') or not source.startswith(('weather/kinetic.','weather/atelier.')):continue
        family='kinetic' if source.startswith('weather/kinetic.') else 'atelier'
        seed=2030 if family=='kinetic' else 4711
        for mode in ('isolated','application'):
            identity='study-'+entry['id'].replace('/','-')+'-'+mode
            case=by_id[identity];prior=copy.deepcopy(case)
            prior.update(id=identity+'-generic',name=case['name']+' / generic',demo=False)
            prior.pop('catalogueEffect',None);additions.append(prior)
            emitter=next(c for c in case['commands'] if c['op']=='emitter' and c['id']==1)
            emitter['alpha']=1
            case['commands'].append({'op':family+'-style','id':1,'paint':'source','seed':seed,'eventId':1 if family=='kinetic' else seed})
            case.update(catalogueEffect=entry['id'],sourceIdentity=source)
    return cases+additions
