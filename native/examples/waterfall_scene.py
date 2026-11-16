"""Reusable waterfall configuration compiled entirely to current native commands.

Install into a caller-owned scene, then drive config.control_path with normal
set/expression/timeline commands. Public IDs are explicit so applications can
reserve them and compose multiple waterfalls without replacing their geometry.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class WaterfallConfig:
    flow_id:int=1
    emitter_id:int=1
    channel_surface_id:int=1
    sheet_surface_id:int=2
    basin_surface_id:int=3
    control_path:str='/waterfall/flux'
    x:float=0
    z:float=0
    height:float=3
    width:float=4
    channel_length:float=6
    channel_speed:float=2
    sheet_speed:float=4
    max_depth:float=1
    flux:float=2
    reference_flux:float=2
    channel_delay_us:int=250000
    sheet_delay_us:int=250000
    tail_us:int=0
    spray_fraction:float=.25
    particle_volume:float=.025
    capacity:float=10
    evaporation_us:int=0
    water_color:int=0x65bad6
    basin_color:int=0x466675
    alpha:float=.8

def build_waterfall_commands(c:WaterfallConfig=WaterfallConfig()):
    """Return fresh owned command data; validation/rollback belongs to native C."""
    x,z,h=c.x,c.z,c.height
    left,right=x-c.width/2-2,x+c.width/2+2
    back,front=z-2,z+4
    commands=[
        {'op':'surface','id':c.channel_surface_id,'wetnessDarkening':.25},
        {'op':'surface','id':c.sheet_surface_id,'wetnessDarkening':.25},
        {'op':'surface','id':c.basin_surface_id,'restitution':0,'friction':.8,
         'settleSpeed':1,'wetnessGain':1,'wetnessDarkening':.6},
        {'op':'ribbon','append':True,'points':[[x,h,z-c.channel_length],[x,h,z]],
         'width':c.width,'surfaceId':c.channel_surface_id,'color':c.water_color,'alpha':c.alpha},
        {'op':'flow','id':c.flow_id,'flux':c.flux,'stages':[
            {'name':'channel','delayUs':c.channel_delay_us,'tailUs':c.tail_us},
            {'name':'sheet','delayUs':c.sheet_delay_us,'tailUs':c.tail_us}]},
        {'op':'waterfall','channelSurfaceId':c.channel_surface_id,'sheetSurfaceId':c.sheet_surface_id,
         'flowId':c.flow_id,'channelStage':'channel','sheetStage':'sheet',
         'referenceFlux':c.reference_flux,'drop':h,'color':c.water_color,'alpha':c.alpha},
        {'op':'mesh','append':True,'triangles':[
            {'a':[left,0,back],'b':[left,0,front],'c':[right,0,back],
             'surfaceId':c.basin_surface_id,'color':c.basin_color,'alpha':1},
            {'a':[right,0,back],'b':[left,0,front],'c':[right,0,front],
             'surfaceId':c.basin_surface_id,'color':c.basin_color,'alpha':1}]},
        {'op':'flow-thickness','surfaceId':c.channel_surface_id,'width':c.width,
         'speed':c.channel_speed,'maxDepth':c.max_depth,'direction':[0,1,0]},
        {'op':'flow-thickness','surfaceId':c.sheet_surface_id,'width':c.width,
         'speed':c.sheet_speed,'maxDepth':c.max_depth,'direction':[0,0,-1]},
        {'op':'surface-water','surfaceId':c.basin_surface_id,'capacity':c.capacity,
         'evaporationUs':c.evaporation_us},
        {'op':'emitter','id':c.emitter_id,'effect':'weather/rain-threads','count':0,
         'seed':73,'shape':'point','position':[x,h/2,z+.1],'extent':[0,0,0],
         'velocity':[0,-4,0],'spread':[.3,.1,.3],'gravity':[0,-9.8,0],
         'wind':[0,0,0],'windVariation':[0,0,0],'collision':True,'deposit':True,
         'colliders':{'floor':False,'surfaces':[c.basin_surface_id]},
         'lifetimeMinMs':5000,'lifetimeMaxMs':5000,'alpha':c.alpha},
        {'op':'flow-sink','surfaceId':c.basin_surface_id,'flowId':c.flow_id,
         'fraction':1-c.spray_fraction,'capacity':c.capacity,'evaporationUs':c.evaporation_us},
        {'op':'flow-spray','flowId':c.flow_id,'emitterId':c.emitter_id,
         'fraction':c.spray_fraction,'particleVolume':c.particle_volume},
        {'op':'define','path':c.control_path,'value':c.flux,
         'binding':{'family':'flow','id':c.flow_id,'field':'flux'}},
    ]
    return commands

def install_waterfall(scene, config:WaterfallConfig=WaterfallConfig()):
    """One native atomic transaction; no helper simulation or host callbacks."""
    return scene.command({'op':'batch','commands':build_waterfall_commands(config)})
