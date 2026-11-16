"""Combine animated backgrounds, flight, windows, prompt weather and incoming text.
"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'hosts/python'))
from atelier_windows import atelier_window_application_commands
from atelier_application import atelier_text_command
SOURCE='01500ccd3106f40a7f0b3e21fe4a580f1e0666980e998930feaf94bff730aced'
WEATHER=('embers','sparks','nova','rain','snow','ripples')
def build_original_composition_studies():
 cases=[]
 for kind in WEATHER:
  commands=atelier_window_application_commands('genie',width=136,height=44)
  commands.extend([{'op':'prompt','active':True,'mode':'marquee','alpha':.22},
   {'op':'window-application','scene':'atelier-windows','backgroundStyle':'plasma','starSpeed':26,'trailMs':180,'travelYaw':22,'travelPitch':-8,'weatherStyle':kind,'novaRegularity':0}])
  commands.extend([{'op':'camera','profile':'original','navigation':'fly'},{'op':'environment','starProfile':'source','worldSeed':2030,'skyDensity':9,'skyRadius':280,'skyExposure':6500,'trailMs':100,'textLightness':.83,'textChroma':.1},{'op':'flight','profile':'original','cruise':{'speed':14,'heading':{'yaw':28,'pitch':12}}}])
  arrival=atelier_text_command('Incoming text / fade','atelier/fade',{'durationMs':1200,'staggerMs':0},identity=41,x=5,y=5,width=126)
  cases.append({'id':'original-composition-'+kind,'name':'Composition / '+kind,'subtitle':'Animated color background and Oblique Flight with windows, immediate prompt, typing weather and incoming text.','commands':commands,'viewport':{'width':136,'height':44},'demo':True,'autoActions':True,'inputWeather':kind,'demonstrates':{'feature':'original-composition','weatherStyle':kind},'provenance':{'release':'Atelier v0.5 components','component':'Assembled original Atelier layers and original analytical Oblique Flight/sky','componentSources':[{'component':'windows/background/input-weather/text-fade','htmlSha256':SOURCE},{'component':'Oblique Flight and world-sector star trails','htmlSha256':'375c4468c886728bc790b8d8cc3bdddc2a046532a4d792cde190f1b522a66385'}],'wholeSceneHistoricalParity':False},'sampleTimesUs':[0,500000,1100000,2500000], 'actions':[{'timeUs':500000,'command':arrival}]})
 return cases
