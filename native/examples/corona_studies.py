"""Source-derived Corona Flare composited in existing application scenes."""
from screen_backdrop import world,application
def build_corona_studies():
    cases=[]
    for sampling in ('cell','half'):
        for mode in ('isolated','application'):
            cases.append({'id':f'corona-{sampling}-{mode}','name':f'Corona Flare / {sampling} / {mode}',
              'subtitle':'Gaussian corona and timed core glyph phases at a camera-projected world emitter center.',
              'mode':mode,'sampling':sampling,'demonstrates':{'feature':'corona-source','sampling':sampling},
              'commands':world()+(application() if mode=='application' else [])+[
                {'op':'environment','sampling':sampling},
                {'op':'camera','position':[0,0,40],'yaw':0,'pitch':0,'roll':0},
                {'op':'emitter','id':1,'effect':'weather/corona-flare','count':32,'runningTimeMs':0,'position':[0,0,0]},
                {'op':'corona-style','id':1,'speed':12,'width':1.7,'intensity':.28,'durationMs':2400},
                {'op':'draft','text':'Accepted corona draft','emitWeather':False}],
              'actions':[],'expectedPrompt':'Accepted corona draft','sampleTimesUs':[0,199999,200000,430000,650000,1000000],
              'rejectedCommands':[{'op':'corona-style','id':1,'width':0},{'op':'corona-style','id':65535}]})
    return cases
