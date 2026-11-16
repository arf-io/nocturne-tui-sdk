"""Workbench landscapes with camera controls and animation clocks."""
from copy import deepcopy
DETAIL=dict(waveHeight=358/256,wavelength=34,windAngle=22,crossSwell=.48,choppiness=.43,foam=.62,waveSpeed=1,joinRiver=1)
def build_original_scenic_routes():
 cases=[]
 for scene,title,original in [('pearl-cascade','Pearl Cascade','waterfall'),('copper-causeway','Copper Causeway','tarmac'),('tidal-glass','Tidal Glass','ocean'),('silt','Silt','dunes')]:
  pearl=scene=='pearl-cascade'
  controls=dict(cameraX=-68,cameraY=58 if pearl else 48,cameraZ=-96,yaw=35,pitch=-22,roll=0,fov=62,projection=1,span=170 if pearl else 220,flow=1,travel=0,seed=2030,redshift=.8,discTilt=12,detail=1,waterAlpha=.94,background=0x101319,ink=0,accent=0,secondary=0,sampling=1)
  commands=[dict(op='resize',width=160,height=52),dict(op='environment',presentation='canvas',style='solid',stars=0,background=0x101319,sampling='braille'),dict(op='floor',enabled=False,visible=False),dict(op='prompt',active=False),dict(op='scene-art',scene=scene,width=160,height=52,timeMs=0,controls=controls,detail=deepcopy(DETAIL)),dict(op='camera',profile='original',navigation='orbit',target=[0,10 if pearl else 0,0]),dict(op='camera-controls',enabled=True,rig='orbit',mode='orbit',anchor=None)]
  cases.append(dict(id='original-'+scene,name=title,subtitle='Workbench spatial artwork / source controls and continuous motion',demo=True,mode='isolated',originalScenic=scene,viewport=dict(width=160,height=52),commands=commands,demonstrates=dict(feature='original-scenic',scene=scene),provenance=dict(release='Workbench RC2',component='Original '+title+' world painter and controls',sourceIdentity='scene:'+original,sourceSha256='ea65ec34887d5ee3d9d2a3c06bd9e2c557c4bee935db01b95d10b58fd8e430d0'),sampleTimesUs=[0,425000,1700000],actions=[dict(timeUs=t,command=dict(op='scene-art',timeMs=t//1000,controls=dict(travel=(t/1000000)*(100*.44704)))) for t in (425000,1700000)]))
 return cases
