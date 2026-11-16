"""Particle effects in standalone and application scenes."""
from screen_backdrop import world,application
def build_kinetic_studies():
    cases=[]
    for profile,effect in [('embers','weather/hearth-spray'),('sparks','weather/branchlight'),('nova','weather/chrysanthemum'),('rain','weather/wire-rain'),('snow','weather/pearl-flurry')]:
        for mode in ('isolated','application'):
            cases.append({'id':f'kinetic-{profile}-{mode}','name':f'Kinetic source / {profile} / {mode}',
              'subtitle':'Seeded analytic points, connected segments, trails and core/shockwave at a projected world emitter center.',
              'mode':mode,'profile':profile,'demonstrates':{'feature':'kinetic-source','profile':profile},
              'commands':world()+(application() if mode=='application' else [])+[
                {'op':'camera','position':[0,0,40],'yaw':0,'pitch':0,'roll':0},
                {'op':'emitter','id':1,'effect':effect,'count':32,'runningTimeMs':0},
                {'op':'kinetic-style','id':1,'seed':2030,'eventId':1,'shockwave':.4},
                {'op':'draft','text':'Kinetic source draft','emitWeather':False}],
              'actions':[],'expectedPrompt':'Kinetic source draft','sampleTimesUs':[0,90000,260000,520000,1000000,5000000],
              'rejectedCommands':[{'op':'kinetic-style','id':1,'count':0},{'op':'kinetic-style','id':65535}]})
    return cases
