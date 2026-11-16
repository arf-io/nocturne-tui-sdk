"""Original Atelier windows expressed as current native SDK commands."""
import math
from atelier_application import SPATIAL_WINDOW_EFFECTS

def atelier_window_application_commands(effect='genie',width=136,height=44,style=None,draft=''):
    if 'atelier/'+effect not in SPATIAL_WINDOW_EFFECTS: raise ValueError('Unknown original Atelier window effect')
    commands=[{'op':'resize','width':width,'height':height},{'op':'environment','stars':0,'presentation':'canvas'},{'op':'floor','visible':False},{'op':'prompt','active':False},{'op':'draft','text':draft,'emitWeather':False},{'op':'camera','profile':'original','position':[0,0,width/(2*math.tan(68*math.pi/360))],'target':[0,0,0],'yaw':0,'pitch':0,'roll':0,'fov':68,'near':.2,'far':20000}]
    specs=[('PEARL / SIGNAL',5,9,52,23,'rounded',0),('ATLAS / OPS',54,15,56,21,'hexagon',5),('IRIS / ARCHIVE',86,7,42,18,'ellipse',14)]
    for index,(title,x,y,w,h,shape,depth) in enumerate(specs):
        identity=index+1
        commands.extend([{'op':'window','id':identity,'title':title,'shape':shape,'effect':SPATIAL_WINDOW_EFFECTS['atelier/'+effect],'position':[x+w/2-width/2,(height/2-y-h/2)*2,-depth],'width':w,'height':h*2,'durationMs':0,'alpha':.88,'overshoot':.18,'scatter':24,'bend':9,'seed':6001},{'op':'window-content','id':identity,'profile':'atelier','label':'w'+str(identity),'sourceIndex':index,'brightness':.16,**(style or {})},{'op':'window','id':identity,'durationMs':950}])
    commands.extend([{'op':'window-action','id':1,'action':'restore','durationMs':0},{'op':'window','id':1,'durationMs':950},{'op':'window-application','paletteWindowId':1,'scene':'atelier-windows','starDensity':.024,'novaRegularity':0}])
    return commands
