"""Animated rules and colored text boxes."""
SOURCE='05ea5072e343a050aeff472f6fc0bb1862ff99584a1408d438393ece498a92cb'
LABELS=('thin rule','heavy rule','double rule','soft dots','braille orbit','rising wave','arrows','alternating halves','dash chase','crossed lines','pulse dots','orbit dots')
def build_original_waiting_studies():
 commands=[{'op':'resize','width':120,'height':32},{'op':'environment','presentation':'canvas','stars':0,'style':'solid','background':0x11100e},{'op':'floor','visible':False},{'op':'prompt','active':False},
 {'op':'source-stage-component','id':1,'kind':'text','x':3,'y':1,'width':112,'height':1,'text':'STUDIO / PEARL  ·  RULE MOTION AND ANIMATED TEXT BOXES','fg':0x7fb8b2}]
 for style in range(12):commands.append({'op':'source-stage-component','id':style+2,'kind':'rule','x':4,'y':3+style,'width':28,'height':1,'style':style,'colorAnimation':1,'hueStep':17,'hueSpeed':24})
 commands.append({'op':'source-stage-component','id':14,'kind':'text','x':38,'y':3,'width':74,'height':12,'text':'\n'.join(str(i+1).rjust(2)+' / '+label for i,label in enumerate(LABELS)),'fg':0xbac3be})
 for style in range(4):
  x=3+style*28
  commands.extend([{'op':'source-stage-component','id':15+style,'kind':'box','x':x,'y':19,'width':26,'height':7,'style':style,'colorAnimation':1,'hueBase':style*70,'hueSpeed':24,'bgOpacity':180,'text':''},
   {'op':'source-stage-component','id':19+style,'kind':'text','x':x+2,'y':21,'width':22,'height':3,'text':'Text reveal.\nColor follows its own clock.','revealMs':35,'changedMs':0,'colorAnimation':1,'hueBase':style*70,'hueSpeed':24}])
 return [{'id':'original-waiting-and-textboxes','name':'Animated rules and text boxes','subtitle':'Twelve multi-character rule styles, animated perimeter color and progressive text reveal.','commands':commands,'demo':True,'viewport':{'width':120,'height':32},'demonstrates':{'feature':'original-waiting'},'sampleTimesUs':[0,150000,300000,450000,600000,2400000],'provenance':{'release':'Studio/Pearl v0.3','component':'Original rule, box and text primitives; assembled gallery','componentSources':[{'path':'src/studio_widgets.inc','sha256':SOURCE}],'wholeSceneHistoricalParity':False}}]
