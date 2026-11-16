"""The backdrop and application frame the screen compositions share: world() is the flat-triangle scene and application()
the "Application / ..." window frame. The atelier, kinetic, corona, thermal, observatory, world shell, studio nova and TDF
studies are composed on them."""

def world():
 return [
  {'op':'resize','width':100,'height':40},
  {'op':'camera','position':[0,6,30],'yaw':0,'pitch':-8,'roll':0,'near':.1,'far':200,'fov':70,'span':40,'orthographic':False},
  {'op':'environment','background':0x0b1528,'stars':180,'starFar':130,'style':'solid'},
  {'op':'floor','height':-6,'visible':True,'enabled':False,'alpha':.45},
  {'op':'mesh','triangles':[{'a':[-8,-4,0],'b':[0,8,0],'c':[8,-4,0],'color':0x42b8bc,'alpha':.75},{'a':[-14,-3,-6],'b':[-10,6,-6],'c':[-6,-3,-6],'color':0xc586e1,'alpha':.6}]},
 ]

def application():
 return [
  {'op':'material','id':2,'gradient':[[.78,.12,205],[.68,.15,320]],'index':{'initial':0,'rate':.25,'min':0,'max':1,'boundary':'reverse'},'alpha':.75},
  {'op':'window','id':90,'title':'Application / mission control','text':'Shared world, camera and local controls\nLayered content remains readable\nPrompt source survives scene motion','position':[10,4,-4],'width':32,'height':15,'material':2,'effect':'window-transition/ribbon-genie'},
  {'op':'text','id':90,'text':'MISSION / OPERATION CONSOLE','x':4,'y':3,'effect':'text/ink-dissolve','durationMs':800},
  {'op':'prompt','active':True,'alpha':.22},
  {'op':'draft','text':'A retained application draft','emitWeather':False},
  {'op':'indicator','id':90,'x':4,'y':32,'sequence':'◐◓◑◒','stepMs':150},
 ]
