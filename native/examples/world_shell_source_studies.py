"""Nova and ripple shells with adjustable profiles."""
from screen_backdrop import world,application
def build_world_shell_source_studies():
    cases=[]
    for profile,effect in [('nova','weather/ejecta-shell'),('ripples','weather/pressure-shell')]:
        for seed in (2030,4294967295):
            for mode in ('isolated','application'):
                cases.append({'id':f'world-shell-source-{profile}-{seed}-{mode}',
                    'name':f'World / {profile} / seed {seed} / {mode}',
                    'subtitle':'Explicit opt-in source primitives; native shell physics remains available after style removal.',
                    'mode':mode,'profile':profile,'demonstrates':{'feature':'world-shell-source','profile':profile},
                    'commands':world()+(application() if mode=='application' else [])+[
                        {'op':'camera','position':[0,10,45],'yaw':0,'pitch':0,'roll':0},
                        {'op':'emitter','id':1,'effect':effect,'position':[0,0,0],'count':32,'runningTimeMs':0},
                        {'op':'world-style','id':1,'seed':seed,'lifeMs':5000,'count':64,'scale':1,'gravity':2.6},
                        {'op':'draft','text':'World source draft','emitWeather':False}],
                    'actions':[],'expectedPrompt':'World source draft','sampleTimesUs':[0,60000,120000,1000000,3000000,5000000],
                    'rejectedCommands':[{'op':'world-style','id':1,'lifeMs':199},{'op':'world-style','id':65535}]})
    return cases
