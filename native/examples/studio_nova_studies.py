"""Integer Studio nova, isolated and within a layered application."""
from screen_backdrop import world,application
def build_studio_nova_studies():
    cases=[]
    for mode in ('isolated','application'):
        cases.append({'id':f'studio-nova-{mode}','name':f'Studio nova / {mode}','subtitle':'Integer glyph growth/contraction, Q8 concentric wavefronts and RGB palettes.',
          'mode':mode,'demonstrates':{'feature':'studio-nova'},'commands':world()+(application() if mode=='application' else [])+[
            {'op':'camera','position':[0,0,40],'yaw':0,'pitch':0,'roll':0},
            {'op':'emitter','id':1,'effect':'weather/pearl-bloom','position':[0,0,0],'count':1,'runningTimeMs':0},
            {'op':'studio-style','id':1,'seed':2030,'novaDurationMs':3600,'rippleSpeed':2560,'rippleWidth':384,'rippleOpacity':280,'rippleRings':2,'cellAspect':2000,'strength':850,'waveScale':6144,'glyphs':'·∙*✦✧','palette':[0x28304f,0x785c89,0x367876,0xae7357,0x504565],'starPalette':[0xb6a4c4,0x9fb9b0,0xc7bca7,0x9cacca,0xc6a0aa,0xadbdbb]},
            {'op':'draft','text':'Studio nova source draft','emitWeather':False}],
          'actions':[],'expectedPrompt':'Studio nova source draft','sampleTimesUs':[0,90000,432000,864000,1800000,3000000,3600000],
          'rejectedCommands':[{'op':'studio-style','id':1,'rippleWidth':15},{'op':'studio-style','id':65535}]})
    return cases
