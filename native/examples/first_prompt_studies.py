"""Prompt palettes, animation and layout presets."""
import copy,json
from pathlib import Path
PRESETS=Path(__file__).with_name('first-prompt-original-presets.json')
def build_first_prompt_studies():
 cases=[]
 for preset in json.loads(PRESETS.read_text()):
  source={'op':'prompt-source','values':copy.deepcopy(preset['values'])}
  for key in ['palette','starPalette','glyphs']:
   if key in preset:source[key]=[int(value.lstrip('#'),16)if isinstance(value,str)else value for value in preset[key]]
  text=preset.get('text','leave room for wonder.')
  cases.append({'id':'first-prompt-'+preset['id'],'name':'Prompt / '+preset['name'],'subtitle':preset['description'],'demo':True,'viewport':{'width':96,'height':40},'commands':[{'op':'resize','width':96,'height':40},source,{'op':'draft','text':text,'emitWeather':False}],'firstPromptPreset':copy.deepcopy(source),'demonstrates':{'feature':'first-prompt-source','preset':preset['id']},'provenance':{'release':'Nocturne v0.1','sourceCommit':'7dccd5ec04a6b6cb81c67e765bae4c23954a6b0a','kernelSha256':'11911d3466a9fe9a29c5c2672089c7a24fa6a288bf02296eb13aa1ffcae32302'},'sampleTimesUs':[0,100000,1200000,2400000]})
 return cases
