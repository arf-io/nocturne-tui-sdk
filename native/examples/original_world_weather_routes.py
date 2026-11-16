"""Select World, Studio, Thermal Observatory and Corona effects."""
import copy,math

def _placement(commands):
    # These ordinary catalogue cases have a one-line workbench prompt. Capture
    # the plane at creation; subsequent camera motion never reorients it.
    camera={'position':[0,0,45],'yaw':0,'pitch':0,'roll':0,'fov':60};height=40;active=True
    for command in commands:
        if command['op']=='camera':camera.update(command)
        elif command['op']=='resize':height=command['height']
        elif command['op']=='prompt' and 'active' in command:active=command['active']
    scene_height=max(6,height-(1 if active else 0)-3)
    yaw,pitch,roll=(math.radians(camera[k]) for k in ('yaw','pitch','roll'))
    cy,sy,cp,sp,cr,sr=math.cos(yaw),math.sin(yaw),math.cos(pitch),math.sin(pitch),math.cos(roll),math.sin(roll)
    forward=(sy*cp,sp,-cy*cp);a=(cy,0,sy);b=(-sy*sp,cp,cy*sp)
    right=[a[k]*cr+b[k]*sr for k in range(3)];up=[b[k]*cr-a[k]*sr for k in range(3)]
    unit=45*math.tan(math.radians(camera['fov']/2))/scene_height
    origin=[camera['position'][k]+forward[k]*45+up[k]*scene_height*.08*unit for k in range(3)]
    # Euler XYZ representation of the source's immutable right/up plane.
    ry=math.asin(max(-1,min(1,-right[2])))
    rx=math.atan2(up[2],-forward[2]);rz=math.atan2(right[1],right[0])
    return origin,[math.degrees(v) for v in (rx,ry,rz)],unit

def apply_original_world_weather_routes(cases,catalogue):
    by_id={case['id']:case for case in cases};additions=[]
    for entry in catalogue:
        source=entry.get('sourceIdentity') or ''
        if not source.startswith(('weather/world.','weather/thermal.','weather/studio.nova','weather/observatory.rain','weather/observatory.snow','weather/observatory.embers','weather/observatory.sparks','weather/observatory.nova')):continue
        for mode in ('isolated','application'):
            identity='study-'+entry['id'].replace('/','-')+'-'+mode;case=by_id[identity]
            if case.get('originalWorldWeatherRoute'):continue
            prior=copy.deepcopy(case);prior.update(id=identity+'-generic',name=case['name']+' / generic',demo=False);prior.pop('catalogueEffect',None);additions.append(prior)
            emitter=next(c for c in case['commands'] if c['op']=='emitter' and c['id']==1)
            origin,orientation,unit=_placement(case['commands']);emitter.update(alpha=1,count=0,runningTimeMs=0,position=origin)
            event_seed=((emitter['id']*2654435761)^2030)&0xffffffff
            if source.startswith('weather/world.'):
                style={'op':'world-style','id':1,'paint':'source','seed':event_seed,'lifeMs':5000,'count':160,'scale':.65,'gravity':8}
                if source=='weather/world.ripples':emitter['birthOrientation']=orientation;style['scale']=unit
            elif source.startswith('weather/thermal.'):
                style={'op':'thermal-style','id':1,'paint':'source','seed':event_seed,'lifeMs':6500}
            elif source=='weather/observatory.nova':
                style={'op':'corona-style','id':1,'paint':'source','speed':12,'width':1.7,'intensity':.51,'durationMs':3200}
            elif source.startswith('weather/observatory.'):
                style={'op':'observatory-style','id':1,'paint':'source','seed':emitter['id'],'speed':12,'intensity':.6,'durationMs':3200}
            else:
                style={'op':'studio-style','id':1,'paint':'source','seed':emitter['id'],'novaDurationMs':3600,'rippleSpeed':2304,'rippleOpacity':700,'rippleRings':3,'strength':1000}
            case['commands'].append(style);case.update(catalogueEffect=entry['id'],sourceIdentity=source,originalWorldWeatherRoute=True)
    return cases+additions
