#!/usr/bin/env python3
"""Current native/WASM replay. Compare every frame/state/metadata record, not images alone."""
from pathlib import Path
import argparse,subprocess,json,hashlib,time,shutil,sys
from cargo_example import buildExample
ROOT=Path(__file__).resolve().parents[1]

def surfacePlan():
    """Recorded public surface commands for the four actual shared-core runtimes."""
    particle={'op':'emitter','effect':'weather/autumn-drift','count':1,'runningTimeMs':0,
              'shape':'point','position':[1,0,0],'velocity':[-240,0,0],
              'extent':[0,0,0],'spread':[0,0,0],'gravity':[0,0,0],
              'wind':[0,0,0],'windVariation':[0,0,0],'drag':0,'lift':0,
              'flutterHz':0,'flutterAmount':0,'tumble':[0,0,0],
              'deposit':False,'collision':True,'birthFadeMs':0,
              'lifetimeMinMs':10000,'lifetimeMaxMs':10000,
              'sizeMin':.2,'sizeMax':.2,'colliders':{'surfaces':[1]}}
    wall={'a':[0,-10,-10],'b':[0,10,-10],'c':[0,0,10],'surfaceId':1,'alpha':.6}
    ramp={'a':[-10,-10,-10],'b':[10,10,-10],'c':[0,0,10],'surfaceId':2,'color':8956620}
    return [
        {'op':'reset','seed':61006},
        {'op':'resize','width':96,'height':36},
        {'op':'environment','stars':0,'style':'solid','sampling':'half'},
        {'op':'camera','position':[30,0,0],'yaw':-90,'pitch':0},
        {'op':'floor','enabled':False},
        {'op':'surface','id':1,'renderVisible':False,'restitution':.5,'friction':.25,
         'reentrainWindSpeed':0,'maxIndividual':1,'maxTiles':3,'retentionMs':500,
         'fadeMs':100,'wetnessGain':.4,'heatGain':.3},
        {'op':'surface','id':2,'restitution':.5,'friction':.25,'heatGain':.5},
        {'op':'mesh','sampling':'half','triangles':[wall,ramp]},
        {**particle,'id':1,'count':5,'deposit':True},
        {**particle,'id':2,'effect':'weather/silver-squall','position':[1,1,0],'count':2},
        {**particle,'id':3,'effect':'weather/thermal-cinders','position':[0,1,0],
         'velocity':[0,-240,120],'heat':0,'colliders':{'surfaces':[2]}},
        {'op':'time','timeUs':8333},
        {'op':'surface','id':1,'renderVisible':True,'heatColor':16746564},
        {'op':'surface','id':2,'collisionEnabled':False},
        {'op':'emitter-colliders','id':3,'colliders':{'floor':True,'surfaces':[1,2]}},
        {'op':'mesh','triangles':[{**wall,'a':[20,-10,-10],'b':[20,10,-10],'c':[20,0,10]},ramp]},
        {'op':'time','timeUs':208333},
        {'op':'stop','id':2,'style':'dissolve','tailMs':200},
        {'op':'clear-instance','id':1},
        {'op':'clear-surface','id':2,'scope':'response'},
        {'op':'time','timeUs':408333},
        {'op':'time','timeUs':508333},
        {'op':'mesh','sampling':'braille'},
        {'op':'clear-surface','id':1,'scope':'all'},
        {'op':'time','timeUs':1000000},
        {'op':'pause','paused':True},
        {'op':'input','text':'Surface contacts retain shared native state.'},
    ]

def cameraControlsPlan():
    """Compare real frames, serialized rig state and metadata in all four runtimes."""
    commands=[]
    for rig in ('orbit','head','dolly','crane','follow','spacecraft'):
        commands.extend([
            {'op':'reset','seed':9415}, {'op':'resize','width':80,'height':28},
            {'op':'environment','stars':80,'sampling':'braille'},
            {'op':'camera','position':[12,7,65],'yaw':-16,'pitch':-5,'roll':9},
            {'op':'node','id':31,'label':'follow target','position':[1,2,3]},
            {'op':'flight','steps':[{'kind':'cruise','durationMs':5000,'speed':10}]},
            {'op':'time','timeUs':1000000}])
        config={'op':'camera-controls','rig':rig}
        if rig=='orbit':config['anchor']=[1,2,3]
        elif rig=='crane':config['crane']={'pivot':[1,2,3],'boom':[11,5,62]}
        elif rig=='follow':config['follow']={'target':{'kind':'node','id':31},'offset':[11,5,62],'track':True}
        elif rig=='spacecraft':config['head']={'position':[1,2,3],'rotation':[10,20,5]}
        commands.extend([config,{'op':'camera-input','delta':[7,-3,2]},
                         {'op':'time','timeUs':1500000},
                         {'op':'camera-input','delta':[-2,1,0],'pan':True},
                         {'op':'camera-controls','inputAxes':{'z':{'action':'look-z','sensitivity':2,'invert':True}}},
                         {'op':'camera-input','delta':[0,0,3]},
                         {'op':'node','id':31,'position':[8,3,-2]},
                         {'op':'time','timeUs':2000000}])
        if rig=='follow':commands.extend([{'op':'camera-controls','mode':'orbit'},{'op':'camera-input','delta':[20,0,0]}])
        if rig=='spacecraft':commands.extend([
            {'op':'camera-controls','inputTarget':'body'},
            {'op':'camera-input','delta':[3,2,1]},
            {'op':'camera-controls','head':{'position':[0,0,0],'rotation':[0,0,0]}}])
        commands.append({'op':'camera-controls','enabled':False})
    return commands

def sceneArtClockPlan():
    """Original scene clocks coexist with the current camera and prompt contract."""
    commands=[]
    for name in ('pearl-cascade','copper-causeway','tidal-glass','silt'):
        commands.extend([
            {'op':'reset','seed':2030},
            {'op':'batch','commands':[
                {'op':'resize','width':80,'height':28},
                {'op':'environment','presentation':'canvas','stars':0,'style':'solid'},
                {'op':'floor','enabled':False,'visible':False},
                {'op':'prompt','active':False},
                {'op':'scene-art','scene':name,'width':80,'height':28,'timeMs':425}]},
            {'op':'time','timeUs':1000000},
            {'op':'scene-art','controls':{'travel':9.25}},
            {'op':'scene-art','timeMs':1700},
            {'op':'batch','commands':[
                {'op':'camera','position':[-55,35,90],'yaw':22,'pitch':-17,'roll':7},
                {'op':'environment','presentation':'workbench'},
                {'op':'prompt','active':True,'presentation':'framed'},
                {'op':'draft','text':'Original scene clock / 文 🪷','emitWeather':False}]},
            {'op':'scene-art','timeMs':None},
            {'op':'time','timeUs':2500000},
        ])
    return commands

def plan():
    out=[]
    for entry in json.loads((ROOT/'catalogue.json').read_text()):
        out.extend([{'op':'reset','seed':42},{'op':'resize','width':80,'height':28}])
        family=entry['contract'];name=entry['id']
        if family=='ParticleEmitter':out.append({'op':'emitter','id':1,'effect':name,'count':16,'runningTimeMs':0})
        elif family=='SurfaceField':out.append({'op':'field','effect':name,'x':30,'y':14,'lifeMs':2000})
        elif family=='TextTransition':out.append({'op':'text','id':1,'effect':name,'text':'Native contracts keep source text.','x':4,'y':10})
        else:out.extend([{'op':'camera','position':[0,8,40],'pitch':0},{'op':'window','id':1,'effect':name,'title':'Readable window','text':'Full source\nCamera-independent document.','position':[0,8,0]}])
        out.extend([{'op':'time','timeUs':250000},{'op':'time','timeUs':900000}])
    for recipe in json.loads((ROOT/'recipes.json').read_text()):
        out.append({'op':'reset','seed':2030});out.extend(recipe['commands']);out.append({'op':'time','timeUs':900000})
    out.extend([{'op':'reset'},{'op':'pause','paused':True},{'op':'input','text':'retained'},{'op':'key','ctrl':True,'key':'a'},{'op':'input','text':'first '},{'op':'prompt','mode':'grow'},{'op':'prompt','mode':'vim-full'},{'op':'prompt','mode':'marquee'},{'op':'key','ctrl':True,'key':'e'},{'op':'input','text':' last'}])
    out.extend([
        {'op':'reset','seed':2030},
        {'op':'batch','commands':[{'op':'define','path':'/wind','value':0},{'op':'input','text':'batch accepted'}]},
        {'op':'schedule','id':1,'atUs':10000,'command':{'op':'set','path':'/wind','value':4}},
        {'op':'time','timeUs':10000},{'op':'time','timeUs':16666},
        {'op':'area','id':1,'layout':'queue','gapMs':0},
        {'op':'status','id':1,'area':1,'text':'','durationMs':100},
        {'op':'status','id':2,'area':1,'text':'full retained message','durationMs':100,'priority':90},
        {'op':'time','timeUs':116666},{'op':'time','timeUs':216666},
        {'op':'emitter','id':1,'effect':'weather/autumn-drift','count':3,'runningTimeMs':100,'cycles':3,'gapMs':50,'shapeWeights':[0,1,0]},
        {'op':'time','timeUs':816666},{'op':'stop','id':1,'style':'dissolve','tailMs':200},
        {'op':'time','timeUs':1116666},
        {'op':'window','id':1,'title':'Retained document','text':'\n'.join('Line %d'%i for i in range(60)),'effect':'window-transition/origami'},
        {'op':'window-action','id':1,'action':'read'},{'op':'window-action','id':1,'action':'scroll','rows':20},
        {'op':'text','id':2,'text':'stable identity','effect':'text/prism-stitch','delayMs':100},
        {'op':'time','timeUs':1616666},{'op':'text','id':2,'text':'stable edited identity'},
        {'op':'accessibility','reducedMotion':True,'screenReader':True},
        {'op':'time','timeUs':1816666}
    ])
    # New public policies must execute through every binding, not only unit tests.
    out.extend([
        {'op':'reset','seed':19},
        {'op':'resize','width':120,'height':42},
        {'op':'camera','position':[0,10,130],'pitch':0,'yaw':0},
        {'op':'node','id':1,'label':'Project / all of the original name','kind':'Project','sha':'ab'*32,'position':[-25,14,0],'minColumns':20,'maxColumns':62,'padding':2,'shaPrefix':12},
        {'op':'node','id':2,'label':'Session\nNative contract qualification','kind':'Session','status':'running','detail':'Preserve the same document','position':[25,2,0],'minColumns':20,'maxColumns':60,'showDetail':False},
        {'op':'edge','from':1,'to':2,'kind':'contains'},
        {'op':'select','id':2,'durationMs':1800},
        {'op':'time','timeUs':300000},
        {'op':'node','id':1,'status':'updated without teleportation','shaPrefix':8,'showKind':False},
        {'op':'time','timeUs':700000},
        {'op':'select','id':1,'durationMs':1200},
        {'op':'time','timeUs':1000000},
        {'op':'node','id':1,'showSha':False,'showDetail':False,'maxColumns':70},
        {'op':'time','timeUs':2100000},
        {'op':'window','id':1,'title':'ATLAS / complete orchestration','text':'A readable full body row\nAnother complete row','position':[0,10,30],'width':55,'height':28,'padding':2,'border':'double','chromeSize':4,'fadeStartRatio':1,'fadeEndRatio':.25},
        {'op':'time','timeUs':3000000},
        {'op':'window-action','id':1,'action':'minimize','durationMs':900},
        {'op':'window','id':1,'title':'ATLAS / metadata edit keeps state'},
        {'op':'time','timeUs':3900000},
        {'op':'window-action','id':1,'action':'restore','durationMs':500},
        {'op':'time','timeUs':4400000},
        {'op':'window','id':1,'padding':1,'border':'heavy','chromeSize':5,'fadeStartRatio':1.2,'fadeEndRatio':.3},
        {'op':'window-action','id':1,'action':'read'},
        {'op':'pause','paused':True},
        {'op':'input','text':'Full local text remains immediate'}
    ])
    out.extend([
        {'op':'reset','seed':2060},
        {'op':'area','id':9,'x':4,'y':4,'width':70,'height':12,'layout':'queue','gapMs':100},
        {'op':'status','id':71,'area':9,'text':'Important decision','mode':'pop','durationMs':0,'important':True,
         'actions':[{'id':1,'label':'Inspect','event':'/review/inspect','value':71},{'id':2,'label':'Defer','event':'/review/defer','dismiss':True}]},
        {'op':'notification-action','id':71,'actionId':1},
        {'op':'notification-action','id':71,'actionId':1},
        {'op':'ack-intent','id':1},
        {'op':'status','id':72,'area':9,'text':'A repeated update','durationMs':1000,'key':'update','coalesce':'count'},
        {'op':'status','area':9,'text':'A repeated update','durationMs':1000,'key':'update','coalesce':'count'},
        {'op':'status','id':73,'area':9,'text':'Queued old detail','durationMs':900,'key':'detail','coalesce':'replace-queued'},
        {'op':'status','area':9,'text':'Queued complete new detail','durationMs':1100,'key':'detail','coalesce':'replace-queued'},
        {'op':'notification-action','id':71,'actionId':2},
        {'op':'ack-status','id':71},
        {'op':'purge-status','id':71},
        {'op':'time','timeUs':100000},
        {'op':'time','timeUs':1200000},
        {'op':'status','id':74,'area':9,'text':'','dwellPerCharacterMs':40,'minDurationMs':100,'maxDurationMs':1500,'mode':'fade'},
        {'op':'time','timeUs':3000000},
        {'op':'pause','paused':True},
        {'op':'input','text':'Held input survives pending intentions'},
        {'op':'ack-intent','id':2},
        {'op':'ack-intent','id':2},
        {'op':'material','id':2,'alpha':0,'blend':'multiply'},
        {'op':'area','id':9,'material':2},
        {'op':'status','id':75,'area':9,'text':'An opacity and blend treatment','mode':'pop','durationMs':0,'actions':[{'id':1,'label':'Visible later','event':'/later'}]},
        {'op':'material','id':2,'alpha':.5},
        {'op':'material','id':2,'alpha':1,'blend':'screen'},
    ])
    out.extend([{'op':'reset','seed':58},{'op':'environment','stars':0,'sampling':'braille'},{'op':'resize','width':96,'height':40}])
    for plotIndex,(kind,data) in enumerate([('pie',[9,1]),('donut',[4,3,2,1]),('line',[.2,.8,.4,.7]),('scatter',[0,.2,.5,.7,1,.4]),('edge',[0,0,.5,.9,1,.2]),('bars',[.32,.73,.48]),('progress',[]),('digits',[])]):
        out.extend([{'op':'widget','id':31,'kind':kind,'x':6,'y':5,'width':52,'height':19,'data':data,'value':.67 if kind=='progress' else 67,'sampling':'braille','revealMs':800,'replay':True},{'op':'time','timeUs':(plotIndex+1)*1000000}])
    out.extend([{'op':'widget','id':31,'kind':'donut','data':[3,4,5],'innerRadius':.84,'cellAspect':1.8,'startAngle':-90,'sweepAngle':270,'revealMs':1800,'replay':True},{'op':'time','timeUs':10000000}])
    for sampling in ['braille','cell','half','hybrid','inherit']:
        out.append({'op':'widget','id':31,'sampling':sampling})
    out.extend([{'op':'environment','sampling':'half'},{'op':'widget','id':31,'sampling':'braille'},{'op':'environment','sampling':'braille'}])
    # Compound values, retained notification identities and independent layer styles.
    out.extend([
        {'op':'reset','seed':2066},
        {'op':'define','path':'/heat','value':20},
        {'op':'define','path':'/enabled','value':1},
        {'op':'define','path':'/count','value':0},
        {'op':'trigger','id':1,'when':{'all':[{'path':'/heat','comparison':'above','value':50,'hysteresis':5},{'not':{'path':'/enabled','comparison':'equal','value':0}}]},'event':'/approve','target':'/count','action':'increment','value':1},
        {'op':'status','id':900,'text':'Guarded action','durationMs':0,'actions':[{'id':1,'label':'Inspect','event':'/approve'}]},
        {'op':'notification-action','id':900,'actionId':1},
        {'op':'batch','commands':[{'op':'set','path':'/heat','value':60},{'op':'set','path':'/enabled','value':0}]},
        {'op':'set','path':'/enabled','value':1},
        {'op':'set','path':'/heat','value':48},
        {'op':'ack-intent','id':1},
        {'op':'status','id':901,'text':'Next identity','durationMs':0,'actions':[{'id':1,'label':'Inspect again','event':'/approve'}]},
        {'op':'notification-action','id':901,'actionId':1},
        {'op':'trigger','id':2,'when':{'any':[{'path':'/heat','comparison':'between','min':10,'max':50},{'path':'/enabled','comparison':'not-equal','value':1}]},'target':'/count','action':'increment','value':10,'edge':'change','debounceMs':20,'cooldownMs':100},
        {'op':'set','path':'/heat','value':20},
        {'op':'time','timeUs':100000},
        {'op':'set','path':'/heat','value':70},
        {'op':'time','timeUs':300000},
        {'op':'emitter','id':1,'effect':'weather/autumn-drift','count':4,'position':[0,6,0],'sampling':'braille','surfaceAlpha':.12,'birthFadeMs':0},
        {'op':'floor','sampling':'half','visible':True,'alpha':.5},
        {'op':'time','timeUs':600000},
        {'op':'emitter-style','id':1,'sampling':'half','surfaceAlpha':.3,'veinContrast':.5},
        {'op':'floor','sampling':'cell'},
        {'op':'emitter-style','id':1,'sampling':'braille','surfaceAlpha':.1,'veinContrast':1},
        {'op':'mesh','sampling':'braille','triangles':[{'a':[-2,0,-4],'b':[2,0,-4],'c':[0,4,-4],'color':3296138,'alpha':.2}]},
        {'op':'time','timeUs':1000000},
        {'op':'pause','paused':True},
        {'op':'input','text':'Held text and retained events are independent.'},
    ])
    # Every new registered family and reversible mapping traverses all four
    # actual runtimes. No independently generated expected frames replace replay.
    out.extend([
        {'op':'reset','seed':947},
        {'op':'environment','stars':0,'style':'solid'},
        {'op':'widget','id':1,'kind':'button','x':8,'y':8,'width':42,'height':5,'text':'Selector replay','material':1,'alpha':.2},
        {'op':'define','path':'/load','value':25},
        {'op':'define','path':'/fault','value':0},
        {'op':'state-register','id':1,'path':'/replay/control','role':'control','target':{'family':'widget','id':1}},
        {'op':'style-rule','id':1,'selector':{'family':'widget','pathPrefix':'/replay','states':{'hover':True}},'style':{'material':2},'priority':10},
        {'op':'style-rule','id':2,'selector':{'family':'widget','role':'control'},'style':{'alpha':{'path':'/load','inputMin':0,'inputMax':100,'outputMin':.1,'outputMax':.9}}},
        {'op':'style-rule','id':3,'selector':{'family':'widget'},'style':{'material':3},'when':{'path':'/fault','comparison':'above','value':50,'hysteresis':5},'priority':20},
        {'op':'pointer','phase':'move','x':15,'y':10},
        {'op':'pointer','phase':'down','x':15,'y':10},
        {'op':'pointer','phase':'up','x':15,'y':10},
        {'op':'pointer','phase':'cancel','x':-1,'y':-1},
        {'op':'batch','commands':[{'op':'set','path':'/fault','value':60},{'op':'set','path':'/fault','value':48},{'op':'set','path':'/load','value':75}]},
        {'op':'set','path':'/fault','value':60},
        {'op':'set','path':'/fault','value':48},
        {'op':'widget','id':1,'material':3,'alpha':.4},
        {'op':'state-update','id':1,'active':False},
        {'op':'state-update','id':1,'active':True,'role':'control'},
        {'op':'remove-style-rule','id':3},
        {'op':'remove-style-rule','id':2},
        {'op':'remove-style-rule','id':1},
        {'op':'define','path':'/selected','value':0,'binding':{'family':'widget','id':1,'field':'selected'}},
        {'op':'trigger','id':5,'when':{'path':'/load','comparison':'above','value':50},'event':'/replay/select','target':'/selected','value':1},
        {'op':'status','id':77,'text':'Retained action drives appearance','durationMs':0,'actions':[{'id':1,'label':'Select','event':'/replay/select'}]},
        {'op':'notification-action','id':77,'actionId':1},
        {'op':'ack-intent','id':1},
        {'op':'style-rule','id':4,'selector':{'family':'widget','states':{'selected':True}},'style':{'backgroundMaterial':2,'sampling':'cell'}},
        {'op':'state-unregister','id':1},
        {'op':'window','id':1,'title':'Source window','text':'Retained document'},
        {'op':'emitter','id':1,'effect':'weather/autumn-drift','count':3,'position':[0,5,0],'birthFadeMs':0},
        {'op':'text','id':1,'text':'Native style','effect':'text/instant-ink','x':4,'y':4},
        {'op':'area','id':7,'x':60,'y':8,'width':35,'height':6},
        {'op':'indicator','id':7,'x':65,'y':20,'sequence':'abcd'},
        {'op':'node','id':7,'label':'Node color'},
        {'op':'mesh','triangles':[{'a':[0,0,0],'b':[4,0,0],'c':[2,3,0],'color':1122867,'alpha':.6}]},
    ])
    familyStyles=[('window',1,{'material':2,'alpha':.3}),('emitter',1,{'material':3,'surfaceAlpha':.4,'veinContrast':.6,'sampling':'braille'}),
                  ('text',1,{'material':3}),('area',7,{'alpha':.3,'material':3}),('indicator',7,{'material':3}),('node',7,{'color':16711935}),
                  ('floor',0,{'alpha':.4,'sampling':'cell'}),('mesh',0,{'alpha':.3,'sampling':'braille','color':8943462}),('prompt',0,{'alpha':.7})]
    for k,(family,targetId,style) in enumerate(familyStyles,10):
        out.append({'op':'state-register','id':k,'path':'/replay/'+family,'role':'visual','target':{'family':family,'id':targetId}})
        out.append({'op':'style-rule','id':k,'selector':{'family':family,'role':'visual'},'style':style})
    for family,targetId,field,value in [('window',1,'alpha',.6),('text',1,'material',2),('area',7,'material',2),('floor',0,'alpha',.1),('state',10,'active',0),('emitter',1,'windY',2)]:
        out.append({'op':'define','path':'/bound/'+family,'value':value,'binding':{'family':family,'id':targetId,'field':field}})
    out.extend([{'op':'time','timeUs':900000},{'op':'pause','paused':True},{'op':'input','text':'No lost input.'}])
    for k in range(10,19):out.append({'op':'remove-style-rule','id':k})
    out.extend(surfacePlan())
    out.extend([
        {'op':'reset','seed':771},
        {'op':'weather-author','schema':'nocturne.weather-authoring/v1','id':9,'effect':'weather/autumn-drift',
         'emission':{'count':24,'runningTimeMs':1000},
         'birth':{'shape':'line','position':[1,10,2],'extent':[4,0,0],'orientation':[45,90,-30],'velocity':[1,2,3],'spread':[.5,.2,.1]},
         'collision':{'enabled':False,'deposit':False}},
        {'op':'time','timeUs':500000},
        {'op':'pause','paused':True},
        {'op':'input','text':'Oriented birth, retained input.'},
        {'op':'clear','scope':'weather'},
        {'op':'emitter','id':9,'birthOrientation':[0,0,0],'count':0},
    ])
    out.extend([
        {'op':'reset','seed':791},
        {'op':'weather-author','schema':'nocturne.weather-authoring/v1','id':1,'effect':'weather/autumn-drift',
         'emission':{'count':100,'runningTimeMs':1000},
         'birth':{'shape':'sphere','distribution':'uniform','extent':[2,4,6],'orientation':[15,45,90]},
         'collision':{'enabled':False,'deposit':False}},
        {'op':'time','timeUs':500000},
        {'op':'time','timeUs':1000000},
    ])
    out.extend([
        {'op':'reset','seed':181},
        {'op':'floor','enabled':False},
        {'op':'surface','id':1,'restitution':1,'friction':0},
        {'op':'model-import','schema':'nocturne.model/v1','units':'centimeters','coordinates':'right-handed-y-up',
         'vertices':[[0,-1000,-1000],[0,1000,-1000],[0,0,1000]],
         'materials':[{'color':0x809caa,'alpha':.75}],
         'triangles':[{'indices':[0,1,2],'material':0,'surfaceId':1}]},
        {'op':'emitter','id':1,'count':1,'runningTimeMs':0,'shape':'point','position':[1,0,0],
         'velocity':[-240,0,0],'spread':[0,0,0],'gravity':[0,0,0],'wind':[0,0,0],
         'windVariation':[0,0,0],'drag':0,'lift':0,'flutterAmount':0,'collision':True,'deposit':False,'colliders':{'surfaces':[1]}},
        {'op':'time','timeUs':8333},
        {'op':'time','timeUs':100000},
    ])
    out.extend([
        {'op':'reset','seed':79},
        {'op':'weather-author','schema':'nocturne.weather-authoring/v1','id':1,'effect':'weather/autumn-drift',
         'emission':{'count':12,'runningTimeMs':1000},'birth':{'initialOrientation':[10,20,30],'angularVelocity':[30,-60,90]},
         'collision':{'enabled':False,'deposit':False}},
        {'op':'time','timeUs':500000},{'op':'time','timeUs':1000000},
    ])
    out.extend([
        {'op':'reset','seed':79},
        {'op':'emitter','id':1,'effect':'weather/thermal-cinders','count':3,'runningTimeMs':0,'collision':False,'deposit':False},
        {'op':'time','timeUs':500000},
        {'op':'stop','id':1,'style':'quench','tailMs':1000},
        {'op':'time','timeUs':750000},{'op':'time','timeUs':1500000},
    ])
    out.extend([
        {'op':'reset','seed':991},
        {'op':'emitter','id':1,'count':100000,'cycles':10000,'runningTimeMs':0,'gapMs':0,
         'lifetimeMinMs':10000,'lifetimeMaxMs':10000,'collision':False,'deposit':False},
        {'op':'time','timeUs':8333},
        {'op':'reset','seed':991},
        {'op':'emitter','id':1,'rate':1e-100,'runningTimeMs':0,'collision':False,'deposit':False},
        {'op':'time','timeUs':1000000},
    ])
    out.extend([
        {'op':'reset','seed':23},
        {'op':'emitter','id':1,'rate':4,'runningTimeMs':0,'lifetimeMinMs':5000,'lifetimeMaxMs':5000,'collision':False,'deposit':False},
        {'op':'time','timeUs':250000},{'op':'stop','id':1,'style':'drain'},
        {'op':'time','timeUs':1000000},{'op':'resume','id':1},{'op':'resume','id':1},
        {'op':'time','timeUs':1241666},{'op':'time','timeUs':1250000},
    ])
    out.extend([
        {'op':'cancel','id':1,'tailMs':500},
        {'op':'time','timeUs':1500000},{'op':'cancel','id':1},
        {'op':'time','timeUs':1750000},
    ])
    out.extend([
        {'op':'reset','seed':23},
        {'op':'emitter','id':1,'rate':4,'runningTimeMs':0,'lifetimeMinMs':5000,'lifetimeMaxMs':5000,'collision':False,'deposit':False},
        {'op':'time','timeUs':250000},{'op':'stop','id':1,'style':'drain'},
        {'op':'time','timeUs':1000000},{'op':'cancel','id':1,'tailMs':500},
        {'op':'time','timeUs':1250000},{'op':'time','timeUs':1500000},
    ])
    out.extend([
        {'op':'reset','seed':42},
        {'op':'draft','text':'Ae\u0301👩\u200d🔧🇺🇸Z','emitWeather':False},
        {'op':'key','key':'ArrowLeft','unit':'grapheme'},
        {'op':'key','key':'Backspace','unit':'grapheme'},
        {'op':'key','key':'Home','unit':'grapheme'},
        {'op':'key','key':'Delete','unit':'grapheme'},
        {'op':'key','key':'z','ctrl':True},
    ])
    # Normal-mode edits and undo must replay identically through every binding.
    for mode in ['vim-inline','vim-full']:
        for unit in ['scalar','grapheme']:
            for key,caret in [('x',1),('X',2),('D',1),('C',1),('s',1),('X',0)]:
                out.extend([{'op':'reset','seed':2030},
                            {'op':'prompt','mode':mode},
                            {'op':'draft','text':'éZ\nnext','caret':caret,'emitWeather':False},
                            {'op':'key','key':'Escape'},
                            {'op':'key','key':key,'unit':unit},
                            {'op':'key','key':'Escape'},
                            {'op':'key','key':'u'}])
    # Line motions/opening and subsequent input exercise actual adapter ownership.
    for mode in ['vim-inline','vim-full']:
        for unit in ['scalar','grapheme']:
            for key in ['0','^','$','I','A','o','O']:
                out.extend([{'op':'reset','seed':2030},
                            {'op':'prompt','mode':mode},
                            {'op':'draft','text':'ab\n  éXY\nlast','caret':7,'emitWeather':False},
                            {'op':'key','key':'Escape'},
                            {'op':'key','key':key,'unit':unit}])
                if key in ['I','A','o','O']:out.append({'op':'key','key':'Q'})
                out.extend([{'op':'key','key':'Escape'},{'op':'key','key':'u'}])
    out.extend([
        {'op':'reset','seed':2030},{'op':'pause','paused':True},
        {'op':'draft','text':'AB','caret':1,'emitWeather':False},
        {'op':'paste','text':'é\n日本'},{'op':'key','key':'z','ctrl':True},
        {'op':'key','key':'F1'},{'op':'paste','text':'blocked modal'},{'op':'key','key':'F1'},
        {'op':'window','id':1,'text':'reader'},{'op':'window-action','id':1,'action':'read'},
        {'op':'paste','text':'blocked reader'},
        {'op':'window-action','id':1,'action':'close','durationMs':1000},
        {'op':'paste','text':'released reader'},
        {'op':'prompt','mode':'vim-full'},{'op':'key','key':'Escape'},
        {'op':'paste','text':'blocked normal'},{'op':'key','key':'i'},
        {'op':'paste','text':'accepted insert'},{'op':'paste','text':''},
    ])
    # WORD motion destinations, including empty lines and cluster ends.
    for mode in ['vim-inline','vim-full']:
        for unit in ['scalar','grapheme']:
            for text,caret,key in [('ab.cd 日本語',0,'W'),('ab.cd 日本語',8,'B'),
                                   ('ab\n\ncd',0,'W'),('ab\n\ncd',4,'B'),
                                   ('ab\n\ncd',1,'E'),('éx y',0,'E'),
                                   ('x é',0,'E'),('a\n',0,'W')]:
                out.extend([{'op':'reset','seed':2030},
                            {'op':'prompt','mode':mode},
                            {'op':'draft','text':text,'caret':caret,'emitWeather':False},
                            {'op':'key','key':'Escape'},
                            {'op':'key','key':key,'unit':unit}])
    # Preserved reset retains Vim/editor history through every owned ABI.
    out.extend([{'op':'reset','seed':2030},
                {'op':'prompt','mode':'vim-full'},
                {'op':'draft','text':'é日本','caret':2,'emitWeather':False},
                {'op':'key','key':'i'},{'op':'paste','text':'X'},
                {'op':'key','key':'Escape'},
                {'op':'reset','seed':99,'preservePrompt':True},
                {'op':'key','key':'u'},
                {'op':'key','key':'F1'},
                {'op':'reset','seed':101,'preservePrompt':True},
                {'op':'paste','text':'blocked modal'},
                {'op':'key','key':'Escape'},
                {'op':'key','key':'i'},{'op':'paste','text':'accepted'},
                {'op':'reset','seed':2030}])
    # Actual grow/shrink/extreme-aspect/tiny frames in every owned runtime.
    out.append({'op':'reset','seed':2030})
    for width,height in [(400,24),(80,180),(320,120),(1024,512),(48,16),(1,1),(3,5),(65536,1),(160,48)]:
        out.append({'op':'resize','width':width,'height':height})
    out.append({'op':'environment','style':'contours'})
    out.append({'op':'resize','width':32768,'height':1})
    out.extend([{'op':'reset','seed':2030},
                {'op':'window','id':1,'title':'retained title','text':'retained document'},
                {'op':'draft','text':'abcdef','caret':3,'emitWeather':False}])
    for width,height in [(3,5),(1,1),(2,2),(4,6),(5,7),(160,48)]:
        out.append({'op':'resize','width':width,'height':height})
        out.append({'op':'key','key':'ArrowUp'})
        out.append({'op':'key','key':'ArrowDown'})
    out.extend(cameraControlsPlan())
    out.extend(sceneArtClockPlan())
    return out

def representativePlan():
    """Finite release replay; the exhaustive policy/recipe replay remains plan()."""
    out=surfacePlan()+cameraControlsPlan()+sceneArtClockPlan()
    out.extend([{'op':'reset','seed':9616},{'op':'resize','width':100,'height':36},
                {'op':'environment','stars':0,'sampling':'braille'},
                {'op':'floor','enabled':False,'visible':False}])
    kinds=('text','box','rule','button','item','cursor','progress','bars','pie','donut','scatter','line','digits','edge','checkbox','radio','select','scrollbar')
    for index,kind in enumerate(kinds,1):
        command={'op':'widget','id':index,'kind':kind,'x':2+((index-1)%5)*19,'y':3+((index-1)//5)*7,'width':18,'height':6,'text':kind}
        if kind in ('bars','pie','donut','scatter','line'):command.update(data=[.2,.5,.35,.8,.6,.95],sampling='braille')
        if kind in ('progress','digits','scrollbar'):command.update(value=65,min=0,max=100)
        out.extend([command,{'op':'time','timeUs':index*100000}])
    out.extend([{'op':'reset','seed':9616},{'op':'resize','width':100,'height':36},
                {'op':'prompt','active':True,'presentation':'framed'},
                {'op':'prompt-appearance','cursor':{'shape':'custom','glyph':'◆','color':'#a3cabe','secondaryColor':'#c7aed7','colorMode':'pulse','colorPeriodMs':1600,'blinkMs':600},'weather':{'style':'snow','paste':'burst'}},
                {'op':'draft','text':'界é 🪷','emitWeather':True},
                {'op':'time','timeUs':120000},
                {'op':'input','text':'x'*70000},
                {'op':'time','timeUs':360000}])
    return out

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--require-rust',action='store_true');parser.add_argument('--profile',choices=['exhaustive','rc2'],default='exhaustive');a=parser.parse_args()
    commands=representativePlan() if a.profile=='rc2' else plan();payload=''.join(json.dumps(c,separators=(',',':'))+'\n' for c in commands).encode();(ROOT/'evidence/plan.ndjson').write_bytes(payload)
    runners={'python':[sys.executable,str(ROOT/'scripts/replay.py')],'typescript':['node',str(ROOT/'scripts/replay.mjs')]}
    results={}
    if shutil.which('go'):
        r=subprocess.run(['go','build','-o',str(ROOT/'dist/go-replay'),'./cmd/replay'],cwd=ROOT/'bindings/go',capture_output=True,text=True)
        (ROOT/'evidence/go-build.log').write_text(r.stdout+r.stderr)
        if r.returncode:raise RuntimeError('Go replay build failed')
        runners['go']=[str(ROOT/'dist/go-replay')]
    else:results['go']={'status':'BLOCKED','reason':'Go compiler unavailable'}
    if shutil.which('cargo'):
        try:
            executable=buildExample(ROOT/'bindings/rust/Cargo.toml','replay',ROOT/'evidence/rust-build.log',release=True)
            runners['rust']=[str(executable)]
        except (OSError,ValueError,subprocess.SubprocessError) as error:
            results['rust']={'status':'FAIL','reason':str(error)}
    else:results['rust']={'status':'BLOCKED','reason':'cargo/rustc unavailable; not replaced by another runtime'}
    baseline=None;mismatches=[]
    for language,argv in runners.items():
        start=time.monotonic();r=subprocess.run(argv,cwd=ROOT,input=payload,capture_output=True,timeout=900)
        (ROOT/'evidence'/f'parity-{language}.jsonl').write_bytes(r.stdout);(ROOT/'evidence'/f'parity-{language}.stderr').write_bytes(r.stderr)
        if r.returncode:results[language]={'status':'FAIL','exitCode':r.returncode};continue
        records=[json.loads(x) for x in r.stdout.splitlines()];results[language]={'status':'PASS','records':len(records),'seconds':round(time.monotonic()-start,3)}
        if len(records)!=len(commands):results[language]['status']='FAIL'
        if baseline is None:baseline=records
        else:
            for i,(left,right) in enumerate(zip(baseline,records)):
                for field in ['frame','state','metadata','motions']:
                    if left[field]!=right[field]:mismatches.append({'language':language,'index':i,'field':field,'command':commands[i]})
    result={'profile':a.profile,'scope':'Exact frame, snapshot, metadata and motions after each declared replay transaction.','commands':len(commands),'planSha256':hashlib.sha256(payload).hexdigest(),'results':results,'mismatches':mismatches,'fourRuntimePassed':all(results.get(k,{}).get('status')=='PASS' for k in ['python','typescript','go','rust']) and not mismatches}
    (ROOT/'evidence/parity.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({**result,'mismatches':mismatches[:4]},indent=2))
    if mismatches or any(v['status']=='FAIL' for v in results.values()) or(a.require_rust and not result['fourRuntimePassed']):raise SystemExit(2)
if __name__=='__main__':main()
