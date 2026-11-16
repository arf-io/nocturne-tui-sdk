"""Particle effects in standalone and application scenes."""
from screen_backdrop import world,application
def build_atelier_studies():
    cases=[]
    for profile,effect in [('embers','weather/copper-cinders'),('sparks','weather/livewire'),('nova','weather/fractured-sun'),('rain','weather/slantfall'),('snow','weather/crystalline-drift')]:
        for mode in ('isolated','application'):
            cases.append({'id':f'atelier-{profile}-{mode}','name':f'Atelier source / {profile} / {mode}',
              'subtitle':'Seeded analytic points, connected segments, trails and core/shockwave at a projected world emitter center.',
              'mode':mode,'profile':profile,'demonstrates':{'feature':'atelier-source','profile':profile},
              'commands':world()+(application() if mode=='application' else [])+[
                {'op':'camera','position':[0,0,40],'yaw':0,'pitch':0,'roll':0},
                {'op':'emitter','id':1,'effect':effect,'count':32,'runningTimeMs':0},
                {'op':'atelier-style','id':1,'seed':2030,'eventId':1,'lifeMs':4200,'count':64,'speed':20,'gravity':9,'rise':10,'drag':.22,'turbulence':1.3,'glitterHz':14,'trailMs':100,'branches':7,'jaggedness':2.2,'coreMs':280,'coreRadius':3,'ejecta':1,'shockwave':.4,'intensity':.8,'reducedMotion':False},
                {'op':'draft','text':'Atelier source draft','emitWeather':False}],
              'actions':[],'expectedPrompt':'Atelier source draft','sampleTimesUs':[0,90000,260000,520000,1000000,5000000],
              'rejectedCommands':[{'op':'atelier-style','id':1,'count':257},{'op':'atelier-style','id':65535}]})
    return cases
