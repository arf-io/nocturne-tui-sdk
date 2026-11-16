"""Distinct clumpy source nova and coherent pressure sphere in paired scenes."""
from screen_backdrop import world,application
DRAFT='Accepted draft survives distinct spatial shells'
def build_world_shell_studies():
    cases=[]
    for effect,shape in [('weather/ejecta-shell','clumpy-fibonacci'),('weather/pressure-shell','uniform-fibonacci')]:
        for mode in ('isolated','application'):
            actions=[{'timeUs':250000,'command':{'op':'pause','paused':False},'expectedInfo':{'emitters':[{'worldShellProfile':{'shape':shape,'active':True,'radiusAtBirth':2,'radialExpansionRate':8.4}}]}},
                     {'timeUs':500000,'command':{'op':'forces','id':1,'gravity':[0,-2,0]},'unchangedParticles':True},
                     {'timeUs':1000000,'command':{'op':'stop','id':1,'style':'drain'},'expectedInfo':{'emitters':[{'id':1,'phase':'draining'}]},'unchangedParticles':True},
                     {'timeUs':1500000,'command':{'op':'clear-instance','id':1},'expectedInfo':{'emitters':[]}}]
            for a in actions:a['expectedPromptState']={'text':DRAFT};a['expectedInputOwner']='prompt'
            cases.append({'id':f'world-shell-{shape}-{mode}','name':f'World shells / {shape} / {mode}','mode':mode,
                'subtitle':'Native world-space radial geometry, authored forces and retained application source.',
                'demonstrates':{'feature':'world-shell-'+shape},
                'commands':world()+(application() if mode=='application' else [])+[
                    {'op':'camera','position':[0,5,32],'yaw':0,'pitch':0},
                    {'op':'prompt','active':True},{'op':'draft','text':DRAFT,'emitWeather':False},
                    {'op':'emitter','id':1,'effect':effect,'seed':73,'count':64,'runningTimeMs':0,'position':[0,5,0],
                     'velocity':[0,0,0],'radius':2,'wind':[0,0,0],'windVariation':[0,0,0],
                     'lifetimeMinMs':5000,'lifetimeMaxMs':5000,'collision':False,'deposit':False}],
                'actions':actions,'autoActions':True,'expectedPrompt':DRAFT,'sampleTimesUs':[0,250000,500000,1000000,1500000,1600000]})
    return cases
