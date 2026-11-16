"""Reusable road authored as current ribbons, surfaces and one native path actor."""
from dataclasses import dataclass

@dataclass(frozen=True)
class RoadConfig:
    points:tuple=((0,0,0),(0,0,-10))
    road_surface_id:int=1
    edge_surface_id:int=2
    terrain_surface_id:int=3
    marking_surface_id:int=4
    actor_id:int=1
    target_family:str='camera'
    target_id:int=0
    width:float=4
    edge_width:float=.4
    marking_width:float=.08
    terrain_margin:float=10
    eye_height:float=1.7
    speed:float=2
    distance:float=0
    mode:str='clamp'
    road_color:int=0x303741
    edge_color:int=0x6880a2
    marking_color:int=0xefdca0
    terrain_color:int=0x324f3a
    alpha:float=1

def build_road_commands(c:RoadConfig=RoadConfig()):
    """Fresh owned authoring; native validation owns domains and atomic rollback."""
    points=[list(p) for p in c.points]
    edge=[[p[0],p[1]-.025,p[2]] for p in points]
    marking=[[p[0],p[1]+.005,p[2]] for p in points]
    travel=[[p[0],p[1]+c.eye_height,p[2]] for p in points]
    x0=min(p[0] for p in points)-c.terrain_margin
    x1=max(p[0] for p in points)+c.terrain_margin
    z0=min(p[2] for p in points)-c.terrain_margin
    z1=max(p[2] for p in points)+c.terrain_margin
    ground=min(p[1] for p in points)-.5
    return [
        {'op':'surface','id':c.road_surface_id,'wetnessDarkening':.6,'wetnessGain':1},
        {'op':'surface','id':c.edge_surface_id,'wetnessDarkening':.3},
        {'op':'surface','id':c.terrain_surface_id,'wetnessDarkening':.5},
        {'op':'surface','id':c.marking_surface_id,'collisionEnabled':False},
        {'op':'ribbon','append':True,'points':edge,'width':c.width+2*c.edge_width,
         'surfaceId':c.edge_surface_id,'color':c.edge_color,'alpha':c.alpha},
        {'op':'ribbon','append':True,'points':points,'width':c.width,
         'surfaceId':c.road_surface_id,'color':c.road_color,'alpha':c.alpha},
        {'op':'ribbon','append':True,'points':marking,'width':c.marking_width,
         'surfaceId':c.marking_surface_id,'color':c.marking_color,'alpha':c.alpha},
        {'op':'mesh','append':True,'triangles':[
            {'a':[x0,ground,z0],'b':[x0,ground,z1],'c':[x1,ground,z0],
             'surfaceId':c.terrain_surface_id,'color':c.terrain_color,'alpha':1},
            {'a':[x1,ground,z0],'b':[x0,ground,z1],'c':[x1,ground,z1],
             'surfaceId':c.terrain_surface_id,'color':c.terrain_color,'alpha':1}]},
        {'op':'path-travel','id':c.actor_id,'target':{'family':c.target_family,'id':c.target_id},
         'points':travel,'speed':c.speed,'distance':c.distance,'mode':c.mode},
    ]

def install_road(scene,config:RoadConfig=RoadConfig()):
    return scene.command({'op':'batch','commands':build_road_commands(config)})
