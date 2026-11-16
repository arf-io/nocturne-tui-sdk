"""Reusable named leaf garden built solely from current native command vocabulary."""
from dataclasses import dataclass
@dataclass(frozen=True)
class GardenConfig:
    surface_id:int=1
    leaf_id:int=1
    rain_id:int=2
    ember_id:int=3
    leaf_material:int=7
    rain_material:int=8
    ember_material:int=9
    wind_path:str='/garden/windX'
    heat_path:str='/garden/heat'
    x:float=0
    z:float=0
    width:float=12
    depth:float=12
    height:float=3
    leaf_count:int=24
    rain_count:int=8
    ember_count:int=2
    wind_x:float=.4
    wind_variation:float=.2
    heat:float=.25
    retention_ms:float=20000
    fade_ms:float=5000

def build_garden_commands(c:GardenConfig=GardenConfig()):
    left,right=c.x-c.width/2,c.x+c.width/2
    back,front=c.z-c.depth/2,c.z+c.depth/2
    colliders={'floor':False,'surfaces':[c.surface_id]}
    shared={'runningTimeMs':500,'gravity':[0,-6,0],'wind':[0,0,0],
            'windVariation':[0,0,0],'lift':0,'collision':True,'deposit':True,
            'colliders':colliders,'lifetimeMinMs':10000,'lifetimeMaxMs':10000}
    return [
        {'op':'material','id':c.leaf_material,'gradient':[[.65,.16,45],[.55,.13,95],[.72,.15,25]],'alpha':1},
        {'op':'material','id':c.rain_material,'gradient':[[.72,.08,225],[.9,.04,200]],'alpha':.65},
        {'op':'material','id':c.ember_material,'gradient':[[.75,.18,40],[.55,.19,20]],'alpha':1},
        {'op':'surface','id':c.surface_id,'restitution':0,'friction':.9,'settleSpeed':30,
         'retentionMs':c.retention_ms,'fadeMs':c.fade_ms,'wetnessGain':1,'evaporation':.1,
         'heatGain':1,'cooling':.1,'wetnessDarkening':.5,'heatTintStrength':.4,'heatColor':0xf18145},
        {'op':'mesh','append':True,'triangles':[
            {'a':[left,0,back],'b':[left,0,front],'c':[right,0,back],'surfaceId':c.surface_id,'color':0x466b47,'alpha':1},
            {'a':[right,0,back],'b':[left,0,front],'c':[right,0,front],'surfaceId':c.surface_id,'color':0x466b47,'alpha':1}]},
        {'op':'emitter','id':c.leaf_id,'effect':'weather/autumn-drift','seed':73,'count':c.leaf_count,
         **shared,'shape':'box','position':[c.x,c.height,c.z],'extent':[c.width/3,.25,c.depth/3],
         'velocity':[0,0,0],'spread':[.1,.1,.1],'drag':.35,
         'wind':[c.wind_x,0,0],'windVariation':[c.wind_variation,0,c.wind_variation],
         'material':c.leaf_material,'twoSided':True,'veinContrast':.7,'surfaceAlpha':.8},
        {'op':'emitter','id':c.rain_id,'effect':'weather/rain-threads','seed':74,'count':c.rain_count,
         **shared,'shape':'box','position':[c.x,c.height+1,c.z],'extent':[c.width/3,0,c.depth/3],
         'velocity':[0,-6,0],'spread':[.1,0,.1],'drag':0,'material':c.rain_material},
        {'op':'emitter','id':c.ember_id,'effect':'weather/thermal-cinders','seed':75,'count':c.ember_count,
         **shared,'shape':'point','position':[c.x,.2,c.z],'extent':[0,0,0],
         'velocity':[0,-4,0],'spread':[.1,0,.1],'drag':.1,'heat':c.heat,'radius':1.5,'material':c.ember_material},
        {'op':'define','path':c.wind_path,'value':c.wind_x,'binding':{'family':'emitter','id':c.leaf_id,'field':'wind.x'}},
        {'op':'define','path':c.heat_path,'value':c.heat,'binding':{'family':'emitter','id':c.ember_id,'field':'heat'}},
    ]
def install_garden(scene,config:GardenConfig=GardenConfig()):
    return scene.command({'op':'batch','commands':build_garden_commands(config)})
