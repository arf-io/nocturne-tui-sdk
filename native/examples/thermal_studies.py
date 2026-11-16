"""World-space thermal treatments, alone and in application context."""
from screen_backdrop import world,application
def build_thermal_studies():
    cases=[]
    for profile,effect in [('embers','weather/thermal-cinders'),('leaves','weather/autumn-drift')]:
        for mode in ('isolated','application'):
            cases.append({'id':f'thermal-{profile}-{mode}','name':f'Thermal source / {profile} / {mode}',
              'subtitle':'Seeded world-space ember burnout/cinders and connected tumbling leaf silhouettes, projected per primitive.',
              'mode':mode,'profile':profile,'demonstrates':{'feature':'thermal-source','profile':profile},
              'commands':world()+(application() if mode=='application' else [])+[
                {'op':'camera','position':[0,10,45],'yaw':0,'pitch':0,'roll':0},
                {'op':'emitter','id':1,'effect':effect,'count':32,'runningTimeMs':0},
                {'op':'thermal-style','id':1,'seed':2030,'lifeMs':6500},
                {'op':'draft','text':'Thermal source draft','emitWeather':False}],
              'actions':[],'expectedPrompt':'Thermal source draft','sampleTimesUs':[0,90000,450000,1000000,3000000,6000000,6500000],
              'rejectedCommands':[{'op':'thermal-style','id':1,'lifeMs':199},{'op':'thermal-style','id':65535}]})
    return cases
