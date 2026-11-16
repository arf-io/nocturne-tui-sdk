"""Four source trajectories composed with world/application layers."""
from screen_backdrop import world,application
def build_observatory_studies():
    cases=[]
    for profile,effect in [('rain','weather/rain-threads'),('snow','weather/snow-dust'),('embers','weather/lantern-motes'),('sparks','weather/pinfire')]:
        for mode in ('isolated','application'):
            cases.append({'id':f'observatory-{profile}-{mode}','name':f'Observatory source / {profile} / {mode}',
              'subtitle':'Seeded scalar trajectories, glyphs and squared envelope at a camera-projected world emitter center.',
              'mode':mode,'profile':profile,'demonstrates':{'feature':'observatory-source','profile':profile},
              'commands':world()+(application() if mode=='application' else [])+[
                {'op':'camera','position':[0,0,40],'yaw':0,'pitch':0,'roll':0},
                {'op':'emitter','id':1,'effect':effect,'count':32,'runningTimeMs':0},
                {'op':'observatory-style','id':1,'seed':73,'speed':12,'intensity':.5,'durationMs':2400},
                {'op':'draft','text':'Observatory source draft','emitWeather':False}],
              'actions':[],'expectedPrompt':'Observatory source draft','sampleTimesUs':[0,250000,1000000,2400000],
              'rejectedCommands':[{'op':'observatory-style','id':1,'intensity':1.01},{'op':'observatory-style','id':65535}]})
    return cases
