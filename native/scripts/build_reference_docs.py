#!/usr/bin/env python3
"""Validate canonical Markdown; build navigable HTML and PDFs from those bytes.

--update-commands regenerates the command reference from the compiler inventory and guidance.
--update-catalogue drives the built native library and regenerates the component catalogue pages."""
from pathlib import Path
import argparse,ast,hashlib,html,json,math,re,shutil,sys,textwrap
from urllib.parse import unquote,urlsplit
import xml.etree.ElementTree as ET

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def slug(text):return re.sub(r'[^\w -]','',text.lower()).replace(' ','-')
def inside(root,name):
 p=(root/name).resolve()
 if not p.is_relative_to(root.resolve()):raise ValueError('Reference path escapes root: '+name)
 return p

def validate(root):
 root=Path(root).resolve();m=json.loads((root/'manifest.json').read_text());names=m['pages']
 if m.get('schema')!='nocturne.reference.v1' or not names or len(names)!=len(set(names)):raise ValueError('Invalid reference manifest')
 pages=[inside(root,n) for n in names]
 for p in pages:
  if not p.is_file() or p.suffix!='.md':raise ValueError('Missing Markdown: '+str(p))
  text=p.read_text();fences=re.findall(r'^```([^\n]*)\n',text,re.M)
  if len(fences)%2:raise ValueError('Unclosed code fence: '+p.name)
  for lang,body in re.findall(r'^```([^\n]*)\n(.*?)^```\s*$',text,re.M|re.S):
   try:
    if lang.strip()=='json':json.loads(body)
    if lang.strip()=='python':ast.parse(body)
   except (ValueError,SyntaxError) as e:raise ValueError('Invalid '+lang+' example in '+p.name) from e
  for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',text):
   u=urlsplit(target)
   if u.scheme in ('https','http','mailto'):continue
   q=inside(root,str(p.parent.relative_to(root)/unquote(u.path))) if u.path else p
   if not q.is_file():raise ValueError('Missing reference '+target+' in '+p.name)
   if u.fragment and q.suffix=='.md':
    anchors=[slug(h) for h in re.findall(r'^#{1,6} (.+)$',q.read_text(),re.M)]
    if unquote(u.fragment) not in anchors:raise ValueError('Missing anchor '+target)
 capture=root/'images/CAPTURES.json'
 if capture.exists():
  for row in json.loads(capture.read_text())['captures']:
   image=inside(root/'images',row['image'])
   if not image.is_file() or sha(image)!=row['pngSha256']:raise ValueError('Capture image changed: '+row['image'])
 registry=root/'components.json'
 if registry.exists():
  if not capture.is_file():raise ValueError('Component captures are required')
  components=json.loads(registry.read_text())['components']
  expected=[(component['id'],state['id']) for component in components for state in component['states']]
  rows=json.loads(capture.read_text())['captures'];actual=[(row['component'],row['state']) for row in rows]
  if len(expected)!=len(set(expected)) or len(actual)!=len(set(actual)) or set(actual)!=set(expected):raise ValueError('Component capture coverage differs from registry')
  for row in rows:
   if row.get('nativeWasmEqual') is not True or not re.fullmatch('[0-9a-f]{64}',row.get('cellSha256','')) or row.get('cellSha256')!=row.get('nativeCellSha256'):raise ValueError('Native/WASM component evidence differs')
 for output,selected in m.get('pdfs',{}).items():
  if not output.endswith('.pdf') or Path(output).name!=output or not selected or any(n not in names for n in selected):raise ValueError('Invalid PDF group')
 return pages

def command_reference(inventory,guidance):
 if inventory['sourceSha256']!=guidance['sourceSha256']:raise ValueError('Command guidance contract hash differs')
 fields={row['op']+'.'+row['field']:row for row in inventory['fields']}
 if set(guidance['parameters'])-set(fields):raise ValueError('Command guidance names unknown fields')
 lines=['# Command reference','','Every command is a JSON object with an `op` field. The engine validates each value and the final state of the transaction. `undefined` means the property is optional and can be omitted; it is not a JSON value. Nested field paths describe the shape of an object, not dotted JSON keys. Where a type is abbreviated, the complete list of choices follows it. A `number` type does not accept every number: the engine also checks resource and relational rules.','','Use a `batch` for commands that must apply together. The [field index](command-inventory.json) lists the same operations and types. The [field guidance](command-help.json) gives defaults and descriptions. See the [SDK contract](Contract.md) for shared behavior.','']
 for op in inventory['operations']:
  lines+=['## '+op,'']
  for row in inventory['fields']:
   if row['op']!=op:continue
   typeText=' / '.join(row['types']);lines+=['- **`'+row['field']+'`**: ``'+typeText+'``']
   if '...' in typeText and row.get('choices'):
    choices=list(dict.fromkeys(json.dumps(value,ensure_ascii=False) for value in row['choices']))
    lines+=['','  Finite choices: '+', '.join('``'+value+'``' for value in choices)+'.']
   help=guidance['parameters'].get(op+'.'+row['field'])
   if help:
    label=help.get('defaultLabel') or 'Default';default=help.get('default');description=help.get('description','')
    if default is not None:lines+=['','  '+label+': '+str(default).rstrip('.')+'.']
    if description:lines+=['','  '+description]
  lines+=['']
 return '\n'.join(lines)

# Component catalogue: each native catalogue identity, the commands that accept it, their parameters,
# and examples the native library itself accepted or refused. Observation needs the built library;
# rendering and validation do not.
FAMILIES=[
 {'family':0,'name':'weather','contract':'ParticleEmitter','commands':['emitter','weather-author'],'page':'Catalogue-Weather.md','title':'Weather'},
 {'family':1,'name':'surface-field','contract':'SurfaceField','commands':['field'],'page':'Catalogue-Surface-Fields.md','title':'Surface field'},
 {'family':2,'name':'text','contract':'TextTransition','commands':['text'],'page':'Catalogue-Text.md','title':'Text transition'},
 {'family':3,'name':'window-transition','contract':'WindowTransition','commands':['window','window-action'],'page':'Catalogue-Windows.md','title':'Window transition'}]
READBACK={0:'emitters',1:'fields',2:'textRuns',3:'windows'}
ALIASES={'collision.enabled':'collision','birth.orientation':'birthOrientation'}
CHOICE_PROBES={'emitter':'shape','field':'optics','text':'phase','window':'border'}
NUMBER_PROBES={'emitter':'count','text':'durationMs','window':'durationMs'}
CONTEXTS=[(2030,None),(4242,(100,30))]
CATALOGUE_SCOPE='Every native catalogue identity, the commands that accept it and their parameters. Defaults and domains are quoted from the command guidance, projected from the emitter for weather-author, read back from the engine, observed from what the engine applies when a field is omitted, or observed from its refusals; each default and domain the guidance omits cites the native statement that applies it. Fields with none of these would be listed under gaps. Examples were run against the native library; this is not exhaustive parameter or visual qualification.'
# window-action reads these fields only under one action (commands.c window-action handler).
ACTIONS={'dx':'move','dy':'move','forward':'move','yaw':'rotate','pitch':'rotate','roll':'rotate','rows':'scroll'}

# Native handlers whose statements are cited: (source, a line fragment that occurs once and opens the handler).
REPOSITORY=Path(__file__).resolve().parents[2]
HANDLERS={'text':('native/src/commands.c','if(!strcmp(op,"text")) {'),'window':('native/src/commands.c','if(!strcmp(op,"window")) {'),
 'window-action':('native/src/commands.c','if(!strcmp(op,"window-action")) {'),'field':('native/src/commands.c','if(!strcmp(op,"field")) {'),
 'window-action-transition':('native/src/commands.c','double current=nrWindowVisibility(w,s->timeUs);'),
 'new-field':('native/src/commands.c','static int newField(State*s,double x,double y,int eff) {'),'weather-author':('native/src/commands.c','static int weatherAuthorProjection('),
 'presentation':('native/src/window_source_presentation.c','void nrWindowSourcePresentationDefaults('),
 'presentation-valid':('native/src/window_source_presentation.c','static int scalar_valid('),
 'presentation-validate':('native/src/window_source_presentation.c','int nrWindowSourcePresentationValid('),
 'order':('native/src/window_presentation.c','static int parse_order('),'glyphs':('native/src/window_presentation.c','static int parse_glyphs('),
 'colliders':('native/src/geometry.c','int nrConfigureColliders(')}
def C(handler,*statements):return [(handler,statement) for statement in statements]
def block_end(lines,start):
 """The last line of the block that line start opens, or of the block that encloses it when it opens none, by brace depth."""
 depth=0;opens=False
 for number in range(start,len(lines)):
  for character in lines[number]:
   if character=='{':depth+=1;opens=opens or number==start
   elif character=='}':depth-=1
  if depth<0 or (opens and depth==0):return number
 return len(lines)-1
def cite(handler,*statements):
 """Each statement at its one occurrence between the handler's anchor and the end of the block the anchor opens or encloses,
 as {path, line, text}. A missing anchor, or a statement that is missing or repeated in that span, is an error: a repeated
 statement needs a narrower anchor, so that the citation names the statement that governs."""
 if handler not in HANDLERS:raise ValueError('Unknown native handler: '+handler)
 path,anchor=HANDLERS[handler];lines=(REPOSITORY/path).read_text().splitlines()
 starts=[number for number,line in enumerate(lines) if anchor in line]
 if len(starts)!=1:raise ValueError('Native handler anchor is missing or repeated: '+anchor)
 end=block_end(lines,starts[0]);out=[]
 for text in statements:
  found=[number for number in range(starts[0],end+1) if text in lines[number]]
  if not found:raise ValueError('Native statement not found in the '+handler+' handler: '+text)
  if len(found)>1:raise ValueError('Native statement repeated in the '+handler+' handler at lines '+', '.join(str(x+1) for x in found)+': '+text)
  out.append({'path':path,'line':found[0]+1,'text':text})
 return out
def citations(pairs):return [x for handler,text in pairs for x in cite(handler,text)]

# Defaults the command guidance does not state, as the native handler applies them when the field is omitted. The citation
# names the statement; the engine proves the value: the command that omits the field and the command naming the value leave
# byte-identical documents, and another accepted value changes the document. value: one value in command units; profile:
# (catalogue profile 0, profile 1); rule: a value that depends on the scene or the resource, observed in the recorded contexts;
# required: the omission is refused; basis: engine-info for a default shown only by an info readback, engine-conditional for
# one shown by a refusal under the condition it names. Values come from the engine's readback where it has one (window
# presentation, the scene seed, field position, the selected window) and otherwise from the cited statement, and the engine's
# documents decide.
APPLIED={
 'text.effect':{'value':'text/ink-dissolve','cite':C('text','q->effect=nrEffectId("text/ink-dissolve");')},
 'text.x':{'value':8,'cite':C('text','q->x=8;')},'text.y':{'value':12,'cite':C('text','q->y=12;')},'text.width':{'value':100,'cite':C('text','q->width=100;')},
 'text.durationMs':{'value':1200,'cite':C('text','q->durationUs=1200000;')},'text.batchSize':{'value':1,'cite':C('text','q->batchSize=1;')},
 'text.material':{'value':2,'also':[({'phaseModel':'source-paint'},15)],'rule':'{0}; {1} for a new run with phaseModel "source-paint"','cite':C('text','q->material=2;','q->material=15;')},
 'text.easing':{'value':'smooth','cite':C('text','q->easing=3;','CHOICE("easing",q->easing,"linear ease-in ease-out smooth smoother sine step cubic back bounce");')},
 'text.delayMs':{'value':0,'cite':C('text','memset(q,0,sizeof(*q));')},'text.reverseOrder':{'value':False,'cite':C('text','memset(q,0,sizeof(*q));')},
 'text.randomOrder':{'value':False,'cite':C('text','memset(q,0,sizeof(*q));')},
 'text.staggerMs':{'profile':(24,28),'cite':C('text','q->staggerUs=profile?28000:24000;')},'text.jitterMs':{'profile':(360,0),'cite':C('text','q->jitterUs=profile?0:360000;')},
 'text.distance':{'profile':(18,13),'cite':C('text','q->distance=profile?13:18;')},'text.scatter':{'profile':(5,8),'cite':C('text','q->scatter=profile?8:5;')},
 'text.variation':{'profile':(.4,.55),'cite':C('text','q->variation=profile?.55:.4;')},'text.wind':{'profile':(1.3,2),'cite':C('text','q->wind=profile?2:1.3;')},
 'text.cycles':{'profile':(3,1.5),'cite':C('text','q->cycles=profile?1.5:3;')},'text.overshoot':{'profile':(.2,1.2),'cite':C('text','q->overshoot=profile?1.2:.2;')},
 'text.scrambleHz':{'profile':(24,18),'cite':C('text','q->scrambleHz=profile?18:24;')},'text.hueSpread':{'profile':(10,110),'cite':C('text','q->hueSpread=profile?110:10;')},
 'text.trailLength':{'profile':(0,2),'cite':C('text','q->trailLength=profile?2:0;')},
 'text.seed':{'rule':'The scene seed','cite':C('text','q->seed=s->seed;')},
 'text.id':{'required':True,'cite':C('text','CHECK(id,"Text id required");')},
 'window.id':{'required':True,'cite':C('window','CHECK(id,"Window id required");')},
 'window.polygon':{'rule':'none; shape "polygon" requires vertices','basis':'engine-conditional','cite':C('window','memset(w,0,sizeof(*w));','CHECK(w->shape!=11||w->polygonCount>=3,"Polygon shape requires polygon vertices");')},
 'window.chrome':{'presentation':'chrome','cite':C('presentation','options->chrome = NR_WINDOW_SOURCE_CHROME_MAC;')},
 'window.controlWidth':{'presentation':'controlWidth','cite':C('presentation','options->controlWidth = 10;')},
 'window.controlHeight':{'presentation':'controlHeight','cite':C('presentation','options->controlHeight = 3;')},
 'window.customSide':{'presentation':'customSide','cite':C('presentation','options->customSide = NR_WINDOW_SOURCE_SIDE_RIGHT;')},
 'window.customOrder':{'presentation':'customOrder','cite':C('presentation','options->customOrder[0] = NR_WINDOW_SOURCE_ACTION_MINIMIZE;','options->customOrder[3] = NR_WINDOW_SOURCE_ACTION_CLOSE;')},
 'window.customGlyphs':{'presentation':'customGlyphs','cite':C('presentation','options->customGlyphs[0] = 0x2212u;','options->customGlyphs[3] = 0x00d7u;')},
 'window.depthFade':{'presentation':'depthFade','cite':C('presentation','options->depthFade = .008;')},
 'window-action.action':{'value':'restore','cite':C('window-action','int action=0;','CHOICE("action",action,"restore minimize close maximize move rotate summon visit roll-up roll-down read scroll page-next page-prev background fade");')},
 **{'window-action.'+field:{'value':0,'with':{'action':'move'},'cite':C('window-action','double dx=0,dy=0,forward=0;')} for field in ('dx','dy','forward')},
 **{'window-action.'+field:{'value':0,'with':{'action':'rotate'},'cite':C('window-action','double yaw=0,pitch=0,roll=0;')} for field in ('yaw','pitch','roll')},
 'window-action.rows':{'value':0,'with':{'action':'scroll'},'cite':C('window-action','int rows=0;')},
 'window-action.durationMs':{'rule':"The window's current durationMs, unchanged",'cite':C('window-action-transition','DUR("durationMs",w->durationUs,60000000,1000);')},
 'window-action.group':{'rule':"The window's current group, unchanged",'cite':C('window-action','INT("group",w->group,0,65535);')},
 'window-action.effect':{'rule':"The window's current effect, unchanged",'cite':C('window-action','CHECK(effect(j,0,&w->effect,3),"Unknown transition");')},
 'window-action.id':{'rule':'The selected window, as info reports selectedWindow','cite':C('window-action','int id=s->selectedWindow;')},
 'field.effect':{'value':'surface-field/silk-tide','cite':C('field','int e=nrEffectId("surface-field/silk-tide");')},
 'field.x':{'rule':'Half the scene width','cite':C('field','double x=s->width*.5,y=s->height*.5;')},
 'field.y':{'rule':'Half the scene height','cite':C('field','double x=s->width*.5,y=s->height*.5;')},
 'field.seed':{'rule':'nrHash(scene seed XOR field id); with paint "source", the field id for algorithms 0 and 1 and 2030 otherwise','cite':C('new-field','f->seed=nrHash(s->seed^f->id);')+C('field','f->seed=a<2?f->id:2030;')},
 'field.surface':{'rule':'none; info reads back null','basis':'engine-info','cite':C('field','int r=nrField(j,0,"surface");')},
 **{'field.surface.'+field:{'required':True,'cite':C('field','"Declared field surface rectangle"')} for field in ('x','y','width','height')},
 'weather-author.schema':{'required':True,'cite':C('weather-author','return reject(c,"Unknown weather-author schema");')},
 'weather-author.effect':{'required':True,'cite':C('weather-author','if(id<0||eff<0)return reject(c,"Weather author requires id and effect");')},
 **{'weather-author.'+group:{'value':{},'rule':'{0}: each member takes the default in its own row','cite':C('weather-author','for(int g=0;g<6;g++)if(groups[g]>=0) {')} for group in ('emission','birth','forces','particle','collision','lifecycle')}}
LABELS={'text':'New-run default','window':'New-window default','window-action':'Applied when omitted','field':'Applied when omitted','weather-author':'Applied when omitted'}
# Another value of a group or of a presentation string that the engine accepts, to show that naming a value changes the document.
OTHERS={'weather-author.emission':[{'count':7}],'weather-author.birth':[{'spread':[0,0,0]}],'weather-author.forces':[{'drag':0}],'weather-author.particle':[{'alpha':.5}],
 'weather-author.collision':[{'enabled':False,'deposit':False},{'enabled':True,'deposit':True}],'weather-author.lifecycle':[{'tailMs':0}],
 'window.customOrder':['close,background,maximize,minimize'],'window.customGlyphs':['a,b,c,d']}
SIZED_CONTEXTS=[(2030,(160,48)),(4242,(100,30))]
SURFACE={'x':0,'y':0,'width':1,'height':1}

# Domains the guidance does not state. A numeric member is bounded from refusals alone; a structure is shown by the accepted
# and refused commands its cited validation separates. {0}, {1} are observed intervals, as "low to high".
PROBED={
 **{'field.surface.'+field:{'text':'Observed in a declared surface: numbers from {0}','lattice':'real','cite':C('field','number(j,r,"'+field+'",&q->'+field)} for field in ('x','y','width','height')},
 'field.velocity':{'text':'Observed: two numbers [x, y], x from {0} and y from {1}','lattice':'real','cite':C('field','"Field velocity has two axes"','q->vx>=-100&&q->vx<=100&&q->vy>=-100&&q->vy<=100')},
 'window.id':{'text':'Observed: integers from {0}','lattice':'integer','cite':C('window','INT("id",id,1,65535);')},
 'window-action.id':{'text':'Integers from 1 to 65535 that name an existing window','cite':C('window-action','INT("id",id,1,65535);','CHECK(i>=0,"Window not found");')},
 'window.polygon':{'text':'3 to 32 [u, v] points, each coordinate from 0 to 1, whose shoelace sum (twice the net signed area) exceeds 1e-8 in magnitude, so lobes of opposite winding cancel','cite':C('window','"Polygon requires 3..32 UV points"','"UV point requires two coordinates"','"UV coordinates must be normalized"','area+=w->polygon[k][0]*w->polygon[n][1]-w->polygon[n][0]*w->polygon[k][1];','CHECK(nrAbs(area)>1e-8,"Degenerate polygon");')},
 'window.customOrder':{'text':'Four comma-separated names: close, minimize, maximize and background, each exactly once','cite':C('order','return count == 4;')+C('presentation-validate','return seen == 0x0fu;')},
 'window.customGlyphs':{'text':'Four comma-separated single Unicode scalars, none from U+0000 to U+001F or U+007F to U+009F; the comma separates them and is never one of them','cite':C('glyphs',"if (i < count && decoded[i] != ',') {",'if (item >= 4 || scalarCount != 1) return 0;')+C('presentation-valid','if (scalar <= 0x1fu || (scalar >= 0x7fu && scalar <= 0x9fu)) return 0;')},
 'emitter.colliders.surfaces':{'text':'Up to 16 distinct integer surface IDs from 1 to 16, each naming an existing surface','cite':C('colliders','"Bounded collider surface array required"','"Invalid collider surface id"','"Collider surface does not exist"','"Duplicate collider surface id"')}}

def compact(value):return json.dumps(value,ensure_ascii=False,separators=(',',':'))
def plain(value):
 if isinstance(value,float) and value.is_integer():return int(value)
 return [plain(x) for x in value] if isinstance(value,list) else value
def flatten(value,prefix=''):
 out={}
 for key,item in value.items():
  if isinstance(item,dict):out.update(flatten(item,prefix+key+'.'))
  else:out[prefix+key]=item
 return out
def fits(value,types):
 text=' '.join(types)
 if isinstance(value,bool):return 'boolean' in text
 if isinstance(value,(int,float)):return 'number' in text
 if isinstance(value,str):return 'string' in text
 return isinstance(value,list) and ('[' in text or 'Vector3' in text)
def declared_value(value,field):
 """Whether a readback value is one the command field declares. A literal union such as "show" | "hide"
 names no primitive type, so a finite-choice field is matched by membership; true is not the number 1."""
 if field['choices']:return any(value==choice and isinstance(value,bool)==isinstance(choice,bool) for choice in field['choices'])
 return fits(value,field['types'])
def numeric_maximum(text):
 """Upper bound of the first `a..b` or `a-b` range in guidance text, else None."""
 found=re.search(r'(-?\d+(?:\.\d+)?)\s*(?:\.\.|\u2013)\s*(\d+(?:\.\d+)?)',text.replace('\u2212','-'))
 return plain(float(found[2])) if found else None
def command_for(op,identity):
 """The smallest accepted command sequence naming this identity; the last command is the subject."""
 if op=='weather-author':return [{'op':op,'schema':'nocturne.weather-authoring/v1','id':1,'effect':identity}]
 if op=='window-action':return [{'op':'window','id':1},{'op':op,'id':1,'action':'minimize','effect':identity}]
 return [{'op':op,'effect':identity}] if op=='field' else [{'op':op,'id':1,'effect':identity}]
def mapped_readback(record,fields):
 """Engine readback values that answer a declared command field: one of its choices, else a value of its type."""
 values=flatten(record)
 values.update({key[:-2]+'Ms':value/1000 for key,value in list(values.items()) if key.endswith('Us') and isinstance(value,(int,float)) and not isinstance(value,bool)})
 return {path:plain(value) for path,value in values.items() if path in fields and path not in ('id','effect') and declared_value(value,fields[path])}

def observe_catalogue(catalogue,inventory,guidance,library=None):
 """Drive the native library for every identity. Records accepted and refused commands with the
 exact diagnostic, and the starting values that read back identically under two scene contexts."""
 sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
 from nocturne_native import NativeScene
 families={f['family']:f for f in FAMILIES};declared={}
 for row in inventory['fields']:declared.setdefault(row['op'],{})[row['field']]=row
 observed={'examples':{},'readback':{}}
 with NativeScene(library=library) as scene:
  def start(seed=2030,size=None):
   scene.command({'op':'reset','seed':seed})
   if size:scene.command({'op':'resize','width':size[0],'height':size[1]})
  def run(commands):
   """Apply setup commands, then the subject. None when accepted, else the exact diagnostic."""
   start()
   for setup in commands[:-1]:scene.command(setup)
   try:scene.command(commands[-1])
   except ValueError as error:return str(error)
  for row in catalogue:
   family=families[row['family']];identity=row['id'];primary=family['commands'][0];positive=[];rejected=[]
   number=NUMBER_PROBES.get(primary);maximum=None
   if number:
    maximum=numeric_maximum(guidance['parameters'][primary+'.'+number]['description'])
    if maximum is None:raise ValueError('No stated maximum to probe: '+primary+'.'+number)
   for op in family['commands']:
    commands=command_for(op,identity)
    if run(commands) is not None:raise ValueError('The native library refused the minimal '+op+' command for '+identity)
    positive.append({'label':'Minimal '+op+' command','op':op,'commands':commands})
   if number:
    commands=[{**command_for(primary,identity)[0],number:maximum}]
    if run(commands) is not None:raise ValueError('The native library refused the stated maximum of '+number+' for '+identity)
    positive.append({'label':'Value at the stated maximum of '+number,'op':primary,'commands':commands})
   def refuse(label,op,commands):
    message=run(commands)
    if message is None:raise ValueError('The native library accepted a command documented as refused: '+label+' / '+identity)
    rejected.append({'label':label,'op':op,'commands':commands,'diagnostic':message})
   foreign=families[(row['family']+1)%len(families)]['commands'][0]
   refuse('Identity used on the '+foreign+' command of another family',foreign,command_for(foreign,identity))
   choice=CHOICE_PROBES[primary];unlisted='unlisted'
   if unlisted in declared[primary][choice]['choices'] or not declared[primary][choice]['choices']:raise ValueError('No finite choice to refuse: '+primary+'.'+choice)
   refuse('Value outside the finite choices of '+choice,primary,[{**command_for(primary,identity)[0],choice:unlisted}])
   if number:
    refuse('Value above the stated maximum of '+number,primary,[{**command_for(primary,identity)[0],number:maximum+1}])
   views=[]
   for seed,size in CONTEXTS:
    start(seed,size)
    for command in command_for(primary,identity):scene.command(command)
    views.append(mapped_readback(scene.info_complete()[READBACK[row['family']]][0],declared[primary]))
   observed['examples'][identity]={'positive':positive,'rejected':rejected}
   observed['readback'][identity]={path:value for path,value in views[0].items() if path in views[1] and views[1][path]==value}
 return observed

def observe_interval(refusal):
 """Edges of the accepted interval around an accepted anchor, found from refusals alone.
 refusal(value) is None when the engine accepts the value, else its exact diagnostic."""
 anchor=next((value for value in (1,10,0.5,2,3,4,5,6,8,100,0,0.1,0.05,0.01,20,50,1000,-1,-10,-100,3600,1000000) if refusal(value) is None),None)
 if anchor is None:return None
 integer=all(refusal(anchor+sign*step) is not None for step in (0.5,0.25,0.1,0.05,0.01,0.001) for sign in (1,-1))
 def edge(sign):
  good,distance=anchor,1
  while True:
   bad=anchor+sign*distance
   if abs(bad)>1e12:return None
   if refusal(bad) is not None:break
   good,distance=bad,distance*2
  while abs(bad-good)>1 if integer else (good+bad)/2 not in (good,bad):
   middle=(good+bad)//2 if integer else (good+bad)/2
   if refusal(middle) is None:good=middle
   else:bad=middle
  if integer:beyond=bad
  else:
   unit=10.0**(math.floor(math.log10(max(abs(good),1)))-6)
   while refusal(plain(round(good+sign*unit,9))) is None:unit*=10
   beyond=plain(round(good+sign*unit,9))
  return {'accepted':plain(good),'refused':beyond,'diagnostic':refusal(beyond)}
 return {'lattice':'integer' if integer else 'real','low':edge(-1),'high':edge(1)}

def domain_targets(inventory,guidance):
 """Numeric scalar fields the guidance gives no domain, on the commands this catalogue probes."""
 ops=[op for family in FAMILIES for op in family['commands'] if op!='weather-author']
 return [(row['op'],row['field']) for row in inventory['fields'] if row['op'] in ops and row['field']!='id' and '.' not in row['field'] and not row['choices']
  and row['types'][0].startswith('number') and not (guidance['parameters'].get(row['op']+'.'+row['field']) or {}).get('description')]

def observe_domains(catalogue,inventory,guidance,library=None):
 """The accepted interval of each unguided numeric field, from the engine's refusals with the
 minimal command for the first identity of the family plus that one field."""
 sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
 from nocturne_native import NativeScene
 owner={op:family['family'] for family in FAMILIES for op in family['commands']}
 first={family['family']:next(row['id'] for row in catalogue if row['family']==family['family']) for family in FAMILIES}
 domains={}
 with NativeScene(library=library) as scene:
  for op,field in domain_targets(inventory,guidance):
   extras={'action':ACTIONS[field]} if op=='window-action' and field in ACTIONS else {}
   commands=command_for(op,first[owner[op]])
   def refusal(value):
    scene.command({'op':'reset','seed':2030})
    for setup in commands[:-1]:scene.command(setup)
    try:scene.command({**commands[-1],**extras,field:value})
    except ValueError as error:return str(error)
   interval=observe_interval(refusal)
   if interval is None:raise ValueError('The native library accepted no value for '+op+'.'+field)
   domains[op+'.'+field]={'lattice':interval['lattice'],'with':extras,'low':interval['low'],'high':interval['high']}
 return domains

def interval_text(edges):
 unit='integers' if edges['lattice']=='integer' else 'numbers';low,high=edges['low'],edges['high']
 context=' with '+', '.join(key+' '+compact(value) for key,value in edges['with'].items()) if edges['with'] else ''
 span=unit+' from '+compact(low['accepted'])+' to '+compact(high['accepted']) if low and high else unit+' up to '+compact(high['accepted']) if high else unit+' from '+compact(low['accepted']) if low else 'any number up to 1e12 in magnitude'
 return 'Observed'+context+': '+span

def named(commands,field,value):
 """The command list with field, a dotted path within the last command, set to value."""
 last=json.loads(json.dumps(commands[-1]));node=last;keys=field.split('.')
 for key in keys[:-1]:node=node.setdefault(key,{})
 node[keys[-1]]=value;return commands[:-1]+[last]
def alternatives(name,row,value,members):
 """Values other than value to try, to show that naming a different value changes the document."""
 if name in OTHERS:return OTHERS[name]
 if isinstance(value,bool):return [not value]
 if row['choices']:return [x for x in row['choices'] if x!=value]
 if isinstance(value,(int,float)):return [plain(value+1),plain(value-1),plain(value+.5),plain(value/2)]
 if isinstance(value,str):return [x['id'] for family in FAMILIES if row['op'] in family['commands'] for x in members[family['family']] if x['id']!=value]
 return []
def presented(value,member):
 """A source presentation readback as the command takes it: names and glyphs are comma-separated strings."""
 if member=='customOrder':return ','.join(value)
 if member=='customGlyphs':return ','.join(chr(x) for x in value)
 return plain(value)

def observe_defaults(catalogue,inventory,guidance,library=None):
 """Engine evidence for each default in APPLIED: the command that omits the field and the command naming the value leave
 byte-identical snapshots and another accepted value changes the snapshot; a required field's omission is refused with the
 exact diagnostic and the command naming it is accepted. Observations use the first identity of the family; text defaults
 that depend on the catalogue profile use the first identity of each profile."""
 sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
 import ctypes
 from nocturne_native import NativeScene
 declared={row['op']+'.'+row['field']:row for row in inventory['fields']}
 members={family['family']:[row for row in catalogue if row['family']==family['family']] for family in FAMILIES}
 owner={op:family['family'] for family in FAMILIES for op in family['commands']}
 profiled={profile:next(row['id'] for row in members[2] if row['profile']==profile) for profile in (0,1)}
 contexts=[[{'op':'reset','seed':seed},{'op':'resize','width':size[0],'height':size[1]}] for seed,size in SIZED_CONTEXTS]
 found={};states={}
 with NativeScene(library=library) as scene:
  nrHash=scene._lib.nrHash;nrHash.restype=ctypes.c_uint32;nrHash.argtypes=[ctypes.c_uint32]
  def state(commands):
   """SHA-256 of the snapshot after the commands from a reset scene, else the refusal."""
   key=compact(commands)
   if key not in states:
    scene.command({'op':'reset','seed':2030})
    try:
     for command in commands:scene.command(command)
     states[key]=hashlib.sha256(scene.snapshot()).hexdigest()
    except ValueError as error:states[key]='refused: '+str(error)
   return states[key]
  def info(commands):
   scene.command({'op':'reset','seed':2030})
   for command in commands:scene.command(command)
   return scene.info_complete()
  def omitted(name,commands,value,kind='omitted',**extra):
   """kind 'omitted' records a default; 'edited' records that editing an existing resource without the field keeps its value."""
   field=name.split('.',1)[1];base=state(commands)
   if base.startswith('refused') or state(named(commands,field,value))!=base:raise ValueError('The native library does not apply '+compact(value)+' when '+name+' is omitted: '+base)
   for other in alternatives(name,declared[name],value,members):
    changed=state(named(commands,field,other))
    if not changed.startswith('refused') and changed!=base:
     found.setdefault(name,{}).setdefault(kind,[]).append({'commands':commands,'field':field,'value':value,'other':other,**extra});return
   raise ValueError('No other accepted value of '+name+' changes the document')
  def refused(name,commands,accepted):
   message=state(commands)
   if not message.startswith('refused: ') or state(accepted).startswith('refused'):raise ValueError('The native library does not refuse the omission of '+name)
   found.setdefault(name,{}).setdefault('refused',[]).append({'commands':commands,'diagnostic':message[len('refused: '):],'accepted':accepted})
  def readback(name,commands,family,path):
   record=info(commands);value=plain(flatten(record[family][0] if family else record).get(path,'absent'))
   found.setdefault(name,{}).setdefault('readback',[]).append({'commands':commands,'family':family,'path':path,'value':value});return value
  def subject(op,field='',**extra):
   """The minimal command for the first identity of the family, with extra fields and without the field itself."""
   commands=command_for(op,members[owner[op]][0]['id']);last={key:value for key,value in {**commands[-1],**extra}.items() if key!=field}
   return commands[:-1]+[last]
  for name,spec in APPLIED.items():
   op,field=name.split('.',1)
   if spec.get('required'):
    if op=='field':
     whole={'surface':SURFACE};part={'surface':{key:value for key,value in SURFACE.items() if key!=field.split('.')[1]}}
     refused(name,subject(op,**part),subject(op,**whole))
    else:refused(name,subject(op,field),subject(op))
   elif 'profile' in spec:
    for profile in (0,1):omitted(name,[{'op':'text','id':1,'effect':profiled[profile]}],spec['profile'][profile],profile=profile)
   elif 'presentation' in spec:
    # Presentation defaults exist once source presentation is enabled; both commands enable it.
    commands=subject(op,field,sourcePresentation=True)
    omitted(name,commands,presented(readback(name,commands,READBACK[3],'sourceOptions.'+spec['presentation']),spec['presentation']))
   elif 'value' in spec:
    omitted(name,subject(op,field,**spec.get('with',{})),spec['value'])
    for extra,value in spec.get('also',[]):omitted(name,subject(op,field,**extra),value)
  # Every text identity receives these defaults at the value of its catalogue profile: all named at once leave the same snapshot.
  for row in members[2]:
   minimal=[{'op':'text','id':1,'effect':row['id']}]
   values={name.split('.',1)[1]:x['value'] for name,evidence in found.items() if name.startswith('text.') for x in evidence.get('omitted',[])
    if len(x['commands'])==1 and set(x['commands'][0])=={'op','id','effect'} and x.get('profile',row['profile'])==row['profile']}
   if state(minimal)!=state([{**minimal[0],**values}]):raise ValueError('The new-run text defaults do not hold for '+row['id'])
  # Editing an existing run or window without a field keeps the value it has.
  omitted('text.durationMs',[{'op':'text','id':1,'effect':profiled[0],'durationMs':250},{'op':'text','id':1,'effect':profiled[0]}],250,'edited')
  omitted('window.chrome',[subject('window',chrome='windows')[0],subject('window')[0]],'windows','edited')
  # Defaults that depend on the scene or the resource, observed in two contexts each.
  for setup in contexts:
   omitted('text.seed',setup+subject('text','seed'),readback('text.seed',setup+subject('text'),READBACK[2],'seed'))
   for axis in ('x','y'):omitted('field.'+axis,setup+subject('field',axis),readback('field.'+axis,setup+subject('field'),READBACK[1],axis))
   omitted('field.seed',setup+subject('field','seed'),nrHash(setup[0]['seed']^info(setup+subject('field'))[READBACK[1]][0]['id']))
  for row in members[1]:omitted('field.seed',[{'op':'field','effect':row['id'],'paint':'source','optics':'source'}],1 if row['algorithm']<2 else 2030)
  # In another scene and as the second field, so that the field id is not a constant 1 and 2030 is not the scene seed.
  for row in (next(x for x in members[1] if x['algorithm']<2),next(x for x in members[1] if x['algorithm']>=2)):
   omitted('field.seed',[{'op':'reset','seed':4242},{'op':'field','effect':members[1][0]['id']},{'op':'field','effect':row['id'],'paint':'source','optics':'source'}],2 if row['algorithm']<2 else 2030)
  window=lambda **fields:{'op':'window','id':1,**fields}
  for setup in ([window()],[window(durationMs=250,group=7)]):
   live=info(setup)[READBACK[3]][0]
   omitted('window-action.durationMs',setup+subject('window-action','durationMs')[1:],plain(live['durationUs']/1000))
   omitted('window-action.group',setup+subject('window-action','group')[1:],live['group'])
  for row in members[3][:2]:omitted('window-action.effect',[window(effect=row['id']),{'op':'window-action','id':1,'action':'minimize'}],row['id'])
  for order in ((1,2),(2,1)):
   setup=[{'op':'window','id':ident} for ident in order]
   omitted('window-action.id',setup+subject('window-action','id')[1:],readback('window-action.id',setup,None,'selectedWindow'))
  refused('window.polygon',subject('window',shape='polygon'),subject('window',shape='polygon',polygon=[[0,0],[1,0],[0,1]]))
  readback('field.surface',subject('field'),READBACK[1],'surface')
 missing=sorted(set(APPLIED)-set(found))
 if missing:raise ValueError('No engine evidence for: '+', '.join(missing))
 return found

def polygon(count):
 """A regular polygon of count UV points inscribed in the unit square."""
 return [[plain(round(.5+.5*math.cos(2*math.pi*k/count),6)),plain(round(.5+.5*math.sin(2*math.pi*k/count),6))] for k in range(count)]
def observe_probes(catalogue,inventory,guidance,library=None):
 """Accepted and refused commands for each domain in PROBED, every refusal with the engine's exact diagnostic. A numeric
 member is bounded from refusals alone; a structure is probed at the cases its cited validation separates."""
 sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
 from nocturne_native import NativeScene
 members={family['family']:[row for row in catalogue if row['family']==family['family']] for family in FAMILIES}
 weather,field,window=(members[family][0]['id'] for family in (0,1,3))
 found={}
 with NativeScene(library=library) as scene:
  def refusal(commands):
   scene.command({'op':'reset','seed':2030})
   for setup in commands[:-1]:scene.command(setup)
   try:scene.command(commands[-1])
   except ValueError as error:return str(error)
  def probe(name,label,commands,refuse=False,edge=None):
   """edge: (path, value) of an interval edge probe, where path locates the value in the last command."""
   message=refusal(commands)
   if (message is not None)!=refuse:raise ValueError('The native library '+('accepted' if refuse else 'refused')+' '+name+' probe "'+label+'": '+str(message))
   found.setdefault(name,{}).setdefault('probes',[]).append({'label':label,'commands':commands,'diagnostic':message,**({'path':edge[0],'value':edge[1]} if edge else {})})
  def interval(name,build,path,axis=''):
   edges=observe_interval(lambda value:refusal(build(value)))
   if edges is None or not edges['low'] or not edges['high']:raise ValueError('No bounded interval observed for '+name)
   found.setdefault(name,{}).setdefault('intervals',[]).append({'lattice':edges['lattice'],'low':edges['low']['accepted'],'high':edges['high']['accepted']})
   for side,word in (('low','lowest'),('high','highest')):
    probe(name,(axis+' ' if axis else '')+word+' accepted value',build(edges[side]['accepted']),edge=(path,edges[side]['accepted']))
    probe(name,(axis+' ' if axis else '')+'beyond the '+word+' value',build(edges[side]['refused']),True,edge=(path,edges[side]['refused']))
  for member in SURFACE:interval('field.surface.'+member,lambda value:[{'op':'field','effect':field,'surface':{**SURFACE,member:value}}],['surface',member])
  for axis,index,build in (('x',0,lambda value:[{'op':'field','effect':field,'velocity':[value,0]}]),('y',1,lambda value:[{'op':'field','effect':field,'velocity':[0,value]}])):interval('field.velocity',build,['velocity',index],axis)
  for label,value in (('one number',[0]),('three numbers',[0,0,0])):probe('field.velocity',label,[{'op':'field','effect':field,'velocity':value}],True)
  interval('window.id',lambda value:[{'op':'window','id':value,'effect':window}],['id'])
  ids=[{'op':'window','id':1},{'op':'window','id':65535}]
  for label,ident,refuse in (('the lowest identity',1,False),('the highest identity',65535,False),('below the lowest',0,True),('above the highest',65536,True),('a fraction',1.5,True),('a window that does not exist',2,True)):
   probe('window-action.id',label,ids+[{'op':'window-action','id':ident,'action':'minimize','effect':window}],refuse)
  shapes=(('3 points',polygon(3),False),('32 points',polygon(32),False),('coordinates 0 and 1',[[0,0],[1,0],[1,1],[0,1]],False),('2 points',[[0,0],[1,1]],True),
   ('33 points',polygon(33),True),('a point with one coordinate',[[0,0],[1],[0,1]],True),('a coordinate above 1',[[0,0],[1.000001,0],[0,1]],True),
   ('a coordinate below 0',[[-0.000001,0],[1,0],[0,1]],True),('collinear points',[[0,0],[.5,.5],[1,1]],True),
   ('3 points wound clockwise',[[0,0],[0,1],[1,0]],False),('a bow-tie whose two lobes cancel',[[0,0],[1,1],[1,0],[0,1]],True),
   ('a sliver with shoelace sum 2^-26, above 1e-8',[[0,0],[2**-13,0],[0,2**-13]],False),('a sliver with shoelace sum 2^-27, below 1e-8',[[0,0],[2**-13,0],[0,2**-14]],True))
  for label,value,refuse in shapes:probe('window.polygon',label,[{'op':'window','id':1,'effect':window,'polygon':value}],refuse)
  for label,value,refuse in (('the source order','minimize,maximize,background,close',False),('another order of the four','close,background,maximize,minimize',False),
   ('three names','close,minimize,maximize',True),('five names','close,minimize,maximize,background,close',True),('a repeated name','close,close,maximize,minimize',True),('an unknown name','close,minimize,maximize,shade',True)):
   probe('window.customOrder',label,[{'op':'window','id':1,'effect':window,'customOrder':value}],refuse)
  for label,value,refuse in (('the source glyphs','−,□,◇,×',False),('four letters','a,b,c,d',False),('three glyphs','a,b,c',True),('five glyphs','a,b,c,d,e',True),
   ('an item of two scalars','ab,c,d,e',True),('a C0 control','\u0007,b,c,d',True),('a C1 control','\u0085,b,c,d',True),
   ('U+001F, the last C0 control','\u001f,b,c,d',True),('U+0020, after the C0 controls',' ,b,c,d',False),('U+007E, before DEL','~,b,c,d',False),
   ('U+007F, DEL','\u007f,b,c,d',True),('U+009F, the last C1 control','\u009f,b,c,d',True),('U+00A0, after the C1 controls','\u00a0,b,c,d',False),
   ('a comma as the second glyph','a,,,c,d',True)):
   probe('window.customGlyphs',label,[{'op':'window','id':1,'effect':window,'customGlyphs':value}],refuse)
  surfaces=lambda *ids:[{'op':'surface','id':ident} for ident in ids]
  emitter=lambda colliders:{'op':'emitter','id':1,'effect':weather,'colliders':colliders}
  for label,setup,colliders,refuse in (('no surface, with the floor',[],{'floor':True,'surfaces':[]},False),('one existing surface',surfaces(1),{'surfaces':[1]},False),
   ('all 16 surfaces',surfaces(*range(1,17)),{'surfaces':list(range(1,17))},False),('17 entries',surfaces(*range(1,17)),{'surfaces':list(range(1,17))+[1]},True),
   ('ID 0',surfaces(1),{'surfaces':[0]},True),('ID 17',surfaces(1),{'surfaces':[17]},True),('a fractional ID',surfaces(1),{'surfaces':[1.5]},True),
   ('a surface that does not exist',surfaces(1),{'surfaces':[2]},True),('a repeated ID',surfaces(1),{'surfaces':[1,1]},True)):
   probe('emitter.colliders.surfaces',label,setup+[emitter(colliders)],refuse)
 missing=sorted(set(PROBED)-set(found))
 if missing:raise ValueError('No engine probes for: '+', '.join(missing))
 return found

def applied_default(name,found):
 """The stated default, label, basis and evidence of an APPLIED field, composed from the engine's observations."""
 spec=APPLIED[name];op=name.split('.',1)[0];rows=found.get('omitted',[])
 evidence={'cite':citations(spec['cite']),**found}
 if spec.get('required'):return {'default':'required','defaultLabel':None,'defaultSource':'engine-required','defaultEvidence':evidence}
 def context(commands):
  if len(commands)<2 or commands[0].get('op')!='reset' or commands[1].get('op')!='resize':return None
  return 'with seed '+str(commands[0]['seed'])+' at '+str(commands[1]['width'])+'×'+str(commands[1]['height'])
 if 'profile' in spec:
  by={x['profile']:x['value'] for x in rows};default=compact(by[0])+' for profile 0, '+compact(by[1])+' for profile 1'
 elif 'rule' in spec and '{' in spec['rule']:default=spec['rule'].format(*[compact(x['value']) for x in rows])
 elif 'rule' in spec:
  seen=[compact(x['value'])+' '+context(x['commands']) for x in rows if context(x['commands'])]
  default=spec['rule']+(' (observed '+'; '.join(seen)+')' if seen else '')
 else:
  values={compact(x['value']) for x in rows}
  if len(values)!=1:raise ValueError('More than one applied value without a rule: '+name)
  default=values.pop()
 return {'default':default,'defaultLabel':'Source presentation default' if 'presentation' in spec else LABELS[op],'defaultSource':spec.get('basis','engine-omission'),'defaultEvidence':evidence}
def probed_domain(name,found):
 """The stated domain, basis and evidence of a PROBED field, composed from the engine's accepted and refused commands."""
 spec=PROBED[name];intervals=found.get('intervals',[])
 for edges in intervals:
  if edges['lattice']!=spec.get('lattice'):raise ValueError('The observed lattice of '+name+' is '+edges['lattice']+', not '+str(spec.get('lattice')))
 return {'domain':spec['text'].format(*[compact(x['low'])+' to '+compact(x['high']) for x in intervals]),'domainSource':'engine-probes','domainEvidence':{'cite':citations(spec['cite']),**found}}

def parameter_record(op,row,rows,guidance):
 help=guidance['parameters'].get(op+'.'+row['field'],{})
 default,domain=help.get('default'),help.get('description') or None
 record={'field':row['field'],'types':row['types'],'choices':row['choices'],
  'default':default,'defaultLabel':help.get('defaultLabel') if default is not None else None,'defaultSource':'command-help' if default is not None else 'unresolved',
  'domain':domain,'domainSource':'command-help' if domain else 'unresolved'}
 if domain is None:
  prefix=row['field']+'.';members=[x['field'][len(prefix):] for x in rows if x['field'].startswith(prefix) and '.' not in x['field'][len(prefix):]]
  if row['choices']:record['domain']='Boolean: true or false' if row['choices']==[False,True] else 'One of '+', '.join(compact(x) for x in row['choices'])
  elif members:record['domain']='Object with members '+', '.join(members)
  if record['domain']:record['domainSource']='inventory'
 return record

def catalogue_reference(catalogue,inventory,guidance,observed,sources):
 """Join the catalogue with the command inventory and guidance. Observed facts come from observe_catalogue."""
 families={f['family']:f for f in FAMILIES};fields={}
 for row in inventory['fields']:fields.setdefault(row['op'],[]).append(row)
 for row in catalogue:
  family=families[row['family']]
  if not row['id'].startswith(family['name']+'/') or row['contract']!=family['contract']:raise ValueError('Catalogue identity does not belong to its family: '+row['id'])
  if row['profile']!=int(row['sourceIdentity'] is not None and '/atelier/' in row['sourceIdentity']):raise ValueError('Catalogue profile differs from the Atelier source rule: '+row['id'])
  if row['id'] not in observed['examples'] or row['id'] not in observed['readback']:raise ValueError('Missing observation: '+row['id'])
 tables={op:[parameter_record(op,row,fields[op],guidance) for row in fields[op]] for family in FAMILIES for op in family['commands']}
 for key,edges in observed.get('domains',{}).items():
  op,field=key.split('.',1);record=next(x for x in tables[op] if x['field']==field)
  if record['domain'] is None:record['domain'],record['domainSource'],record['domainEdges']=interval_text(edges),'engine-refusals',edges
 starting={};baseline={}
 for family in FAMILIES:
  members=[row['id'] for row in catalogue if row['family']==family['family']];votes={}
  for identity in members:
   for path,value in observed['readback'][identity].items():votes.setdefault(path,{}).setdefault(compact(value),[]).append(identity)
  starting[family['family']]={}
  for path,values in votes.items():
   if sum(len(x) for x in values.values())==len(members):starting[family['family']][path]=json.loads(max(values,key=lambda x:len(values[x])))
  baseline[family['family']]=dict(starting[family['family']])
  for record in tables[family['commands'][0]]:
   if record['default'] is None and record['field'] in starting[family['family']]:
    record['default'],record['defaultLabel'],record['defaultSource']=compact(starting[family['family']][record['field']]),'Observed default','engine-readback'
   elif record['defaultSource']=='command-help':
    try:baseline[family['family']][record['field']]=json.loads(record['default'].strip('`'))
    except ValueError:pass
 for family in FAMILIES:
  for op in family['commands']:
   for record in tables[op]:
    if record['field']=='effect' and record['domain'] is None:
     record['domain'],record['domainSource']='A '+family['contract']+' identity from the catalogue, '+str(sum(1 for row in catalogue if row['family']==family['family']))+' identities','catalogue'
 emitter={x['field']:x for x in tables['emitter']}
 for record in tables['weather-author']:
  field=record['field']
  if '.' not in field and field not in ('id','effect'):continue
  source=emitter.get(ALIASES.get(field,field.split('.',1)[-1]))
  if source is None:raise ValueError('Weather-author field has no emitter field: '+field)
  # A default the engine is observed to apply on weather-author itself is not projected: weather-author requires the effect
  # that emitter defaults (commands.c weatherAuthorProjection), so the emitter's guidance default would be false here.
  applied='weather-author.'+field in APPLIED
  for key in ('domain',) if applied else ('default','domain'):
   if source[key] is not None:record[key],record[key+'Source']=source[key],'projection'
  if source['default'] is not None and not applied:record['defaultLabel']=source['defaultLabel']
 # What the guidance omits, from the engine: applied and required defaults, and domains from accepted and refused commands.
 for key,compose,blank in (('defaults',applied_default,'default'),('probes',probed_domain,'domain')):
  for name,found in observed.get(key,{}).items():
   op,field=name.split('.',1);record=next(x for x in tables[op] if x['field']==field)
   if record[blank] is None:record.update(compose(name,found))
 entries=[]
 for row in catalogue:
  family=families[row['family']];mode=baseline[row['family']]
  entries.append({'id':row['id'],'name':row['name'],'family':row['family'],'contract':row['contract'],'profile':row['profile'],'algorithm':row['algorithm'],
   'sourceIdentity':row['sourceIdentity'],'visualAcceptance':row['visualAcceptance'],'commands':list(family['commands']),
   'startingValues':{path:value for path,value in observed['readback'][row['id']].items() if path in mode and mode[path]!=value},
   'examples':observed['examples'][row['id']]})
 return {'schema':'nocturne.reference-catalogue.v1',
  'scope':CATALOGUE_SCOPE,
  'sources':sources,'families':[{'family':f['family'],'name':f['name'],'contract':f['contract'],'commands':list(f['commands'])} for f in FAMILIES],
  'commands':tables,'entries':entries,
  'gaps':{key:sorted(op+'.'+x['field'] for op,table in tables.items() for x in table if x[key] is None) for key in ('default','domain')}}

def table_cell(text):return str(text).replace('|','\\|').replace('\n',' ')
def codes(names):return ', '.join('`'+x+'`' for x in names)
def example_block(commands):return '```json\n'+compact(commands if len(commands)>1 else commands[0])+'\n```'
def basis(record):
 words={'command-help':'guidance','projection':'weather-author projection','engine-readback':'engine readback','inventory':'declared type','catalogue':'catalogue','engine-refusals':'refusal probes',
  'engine-omission':'applied when omitted','engine-required':'refused when omitted','engine-probes':'accepted and refused commands','unresolved':'not stated',
  'engine-info':'read back from info','engine-conditional':'refused when omitted under a condition'}
 def said(key):
  """The basis of a default or domain, with the native statements it cites as file:line."""
  evidence=record.get(key+'Evidence');where=list(dict.fromkeys(x['path'].rsplit('/',1)[-1]+':'+str(x['line']) for x in evidence['cite'])) if evidence else []
  return words[record[key+'Source']]+(' ('+', '.join('`'+x+'`' for x in where)+')' if where else '')
 default,domain=said('default'),said('domain')
 return default if default==domain else 'default: '+default+'; domain: '+domain

def catalogue_pages(section,nullified=()):
 """Markdown pages derived only from the catalogue section, without the identities the operator nullified.

 A nullified identity loses its index row and its family-page entry, and the index points to the nullification
 ledger. The parameter tables do not change: they state what the engine accepts, which still includes it."""
 families={f['family']:f for f in FAMILIES};gaps=section['gaps']
 nullified=list(dict.fromkeys(nullified));unknown=[x for x in nullified if x not in {e['id'] for e in section['entries']}]
 if unknown:raise ValueError('Nullified identity is not in the catalogue: '+', '.join(unknown))
 entries=[x for x in section['entries'] if x['id'] not in nullified];one=len(nullified)==1
 listed=('This catalogue lists all '+str(len(entries))+' native catalogue identities in four families.' if not nullified else
  'This catalogue lists '+str(len(entries))+' of the '+str(len(section['entries']))+' native catalogue identities in four families; '+
  ('the identity' if one else 'the '+str(len(nullified))+' identities')+' hidden by the contract '+('is' if one else 'are')+
  ' listed on the [nullification page]('+NULLIFICATION_PAGE+') instead.')
 note=['A hidden identity is omitted from these pages and from the Gallery. The core still accepts and renders it, so the parameter tables include it.',''] if nullified else []
 pages={'Catalogue.md':None}
 index=['# Component catalogue','',
  listed+' An identity is the value of the `effect` field of the commands listed for its family. Each family page lists the parameters of those commands with their defaults and domains, then one entry per identity with commands the library accepts and refuses. The [component atlas](Components.md) shows captured states of the visible components.','',
  'A source identity names the original effect an identity comes from. Profile is 1 when the source identity is under an Atelier source and 0 otherwise.','']+note+[
  '## Families','','| Family | Contract | Commands | Identities |','|---|---|---|---|']
 for family in FAMILIES:
  index.append('| ['+family['title']+']('+family['page']+') | `'+family['contract']+'` | '+codes(family['commands'])+' | '+str(sum(1 for x in entries if x['family']==family['family']))+' |')
 index+=['','## All identities','','| Identity | Name | Family | Profile |','|---|---|---|---|']
 for entry in entries:
  family=families[entry['family']];index.append('| [`'+entry['id']+'`]('+family['page']+'#'+slug(entry['id'])+') | '+table_cell(entry['name'])+' | '+family['title']+' | '+str(entry['profile'])+' |')
 if gaps['default'] or gaps['domain']:
  index+=['','## Parameters without a default or domain','']
  for key in ('default','domain'):
   if not gaps[key]:continue
   index+=['### Without a '+key,'']
   for op in sorted({x.split('.',1)[0] for x in gaps[key]}):
    names=[x.split('.',1)[1] for x in gaps[key] if x.split('.',1)[0]==op];index.append('- `'+op+'`, '+str(len(names))+' of '+str(len(section['commands'][op]))+': '+codes(names))
   index.append('')
 pages['Catalogue.md']='\n'.join(index)
 for family in FAMILIES:
  members=[x for x in entries if x['family']==family['family']];deviating=[x for x in members if x['startingValues']]
  lines=['# '+family['title']+' components','',
   str(len(members))+' identities with the native contract `'+family['contract']+'`. An identity is the value of the `effect` field of '+codes(family['commands'])+'. Back to the [catalogue](Catalogue.md).','',
   'Each default and domain comes from the command guidance, from values the engine reads back, or from commands the engine accepts and refuses. The Basis column says which.'+
   (' The engine reads back a different starting value for '+str(len(deviating))+' of these identities; each is listed in its entry.' if deviating else ''),'']
  sources={x['defaultSource'] for op in family['commands'] for x in section['commands'][op]}|{x['domainSource'] for op in family['commands'] for x in section['commands'][op]}
  observed=[];edited=[op+'.'+x['field'] for op in family['commands'] for x in section['commands'][op] if x.get('defaultEvidence',{}).get('edited')]
  if 'engine-readback' in sources:observed.append('An observed default is a value the engine reads back identically in two scenes that differ in seed and viewport size.')
  if 'engine-omission' in sources:
   observed.append('A default applied when omitted is the value the engine uses when the field is left out: the command without the field and the same command naming the value leave identical documents.'+
    (' A new-run or new-window default is what a new resource receives. Editing an existing one without the field keeps its current value for '+codes(edited)+'.' if edited else ''))
  if 'engine-required' in sources:observed.append('A required parameter is refused when omitted.')
  if 'engine-info' in sources:observed.append('A default read back from info is what info reports after the command without the field.')
  if 'engine-conditional' in sources:observed.append('A parameter refused when omitted under a condition is required whenever the condition in its Default column holds.')
  if 'engine-refusals' in sources or 'engine-probes' in sources:observed.append('An observed domain is the range the engine accepts: it accepts the edge values and refuses values just beyond them.')
  if observed:lines+=[' '.join(observed)+' A file and line in the Basis column point to the native statement that applies the default or checks the domain.','']
  for op in family['commands']:
   lines+=['## Parameters of '+op,'','| Parameter | Type | Default | Domain | Basis |','|---|---|---|---|---|']
   for record in section['commands'][op]:
    default='not stated' if record['default'] is None else (record['defaultLabel']+': ' if record['defaultLabel'] else '')+record['default']
    lines.append('| `'+record['field']+'` | '+table_cell(' / '.join(record['types']))+' | '+table_cell(default)+' | '+table_cell(record['domain'] or 'not stated')+' | '+basis(record)+' |')
   lines.append('')
  lines+=['## Components','']
  for entry in members:
   lines+=['### '+entry['id'],'','| Field | Value |','|---|---|','| Name | '+table_cell(entry['name'])+' |','| Contract | `'+entry['contract']+'` |','| Profile | '+str(entry['profile'])+' |','| Algorithm | '+str(entry['algorithm'])+' |',
    '| Source identity | '+('none recorded' if entry['sourceIdentity'] is None else '`'+entry['sourceIdentity']+'`')+' |','| Commands | '+', '.join('[`'+op+'`](#parameters-of-'+op+')' for op in entry['commands'])+' |','']
   if entry['startingValues']:
    lines+=['Starting values read back from the engine that differ from the default in the table above: '+', '.join('`'+path+'` = `'+compact(value)+'`' for path,value in entry['startingValues'].items())+'.','']
   lines+=['Accepted by the native library:','']
   for example in entry['examples']['positive']:lines+=['**'+example['label']+'**','',example_block(example['commands']),'']
   lines+=['Refused by the native library:','']
   for example in entry['examples']['rejected']:lines+=['**'+example['label']+'**','',example_block(example['commands']),'','Diagnostic: `'+example['diagnostic']+'`','']
  pages[family['page']]='\n'.join(lines)
 return {name:text.rstrip('\n')+'\n' for name,text in pages.items()}

# Nullification: the contract (native/contract/NULLIFICATION.json) hides catalogue identities and rendering
# outputs. native/scripts/nullification.py validates and resolves it; these pages are rendered from what it resolves.
NULLIFICATION_PAGE='Nullification.md'
def nullification():
 """native/scripts/nullification.py, the only reader of the operator's nullification contract."""
 here=str(Path(__file__).resolve().parent)
 if here not in sys.path:sys.path.insert(0,here)
 import nullification as module
 return module
def nullification_page(resolved):
 """The nullification page: every current-identity and rendering-output decision, or None when there is none."""
 identities=[x for x in resolved if x['scope']=='current-identity'];outputs=[x for x in resolved if x['scope']=='rendering-output']
 if not identities and not outputs:return None
 def code(text):return '`'+table_cell(text)+'`'
 text=nullification().markdown_text  # name and reason are free text from the review page
 lines=['# Nullification','',
  'The items below are hidden by the contract in `native/contract/NULLIFICATION.json`. A hidden catalogue effect is omitted from the [component catalogue](Catalogue.md) pages, and the Gallery omits every recipe and study that uses it, attract mode included. A hidden recipe is omitted from the Gallery.','',
  'The core still accepts and renders a hidden effect, and [components.json](components.json) still describes it. The parameter tables of the catalogue pages state the engine\'s domains, which include it, and the Gallery\'s effect picker, which lists the native catalogue, still offers it.','']
 if identities:
  lines+=['## Catalogue identities','','| Identity | Name | Recipes omitted | Reason |','|---|---|---|---|']
  for x in identities:
   recipes=x['strikes']['recipes']
   lines.append('| '+code(x['key'])+' | '+text(x['name'])+' | '+(', '.join(code(r) for r in recipes) if recipes else 'none')+' | '+text(x['reason'])+' |')
  lines.append('')
  lines+=['Recipes omitted are those of `native/recipes.json`. The Gallery studies generated from the catalogue that use the identity are omitted by the same rule when the Gallery is built.','']
  for x in identities:
   for op in x['retained']['engineDefaultFor']:
    lines+=[code(x['key'])+' is the engine default effect for `'+op+'` commands that omit `effect`. The core keeps applying it there.','']
 if outputs:
  lines+=['## Rendering outputs','','| Output | Name | Reason |','|---|---|---|']
  for x in outputs:lines.append('| '+code(x['key'])+' | '+text(x['name'])+' | '+text(x['reason'])+' |')
  lines.append('')
  if any(x['resolved']['kind']=='capture' for x in outputs):
   lines+=['A hidden capture is listed here only. The [component atlas](Components.md) and its registry are maintained by hand, so the capture and its image stay in the atlas until its state is removed from both and the atlas is recaptured.','']
 return '\n'.join(lines).rstrip('\n')+'\n'
def nullified_docs(root,resolved):
 """The reference files nullification decisions determine, as {name: text, or None for an absent file}.

 The catalogue pages are rendered from the complete engine-observed section of components.json without the nullified
 identities; components.json itself keeps every identity because it records what the engine accepts. The ledger
 exists only while there is a current-identity or rendering-output decision, and the manifest lists it after the
 catalogue pages only while it exists."""
 root=Path(root);section=json.loads((root/'components.json').read_text())['catalogue']
 out=dict(catalogue_pages(section,[x['key'] for x in resolved if x['scope']=='current-identity']))
 ledger=nullification_page(resolved);out[NULLIFICATION_PAGE]=ledger
 manifest=json.loads((root/'manifest.json').read_text());names=[x for x in manifest['pages'] if x!=NULLIFICATION_PAGE]
 if ledger is not None:names.insert(names.index('Catalogue-Windows.md')+1 if 'Catalogue-Windows.md' in names else len(names),NULLIFICATION_PAGE)
 manifest['pages']=names;out['manifest.json']=json.dumps(manifest,indent=2)+'\n'
 return out
def check_nullified_docs(root,resolved):
 """Refuse reference pages that lag the contract, naming each file that differs from what the decisions determine."""
 root=Path(root);stale=[]
 for name,text in nullified_docs(root,resolved).items():
  path=root/name
  if (path.read_text() if path.is_file() else None)!=text:stale.append(name)
 if stale:raise ValueError('Reference docs differ from the nullification contract: '+', '.join(stale)+'; run native/scripts/apply_nullification.py --apply')
def nullified_docs_writes(root,resolved):
 """The writes that take the reference pages to what the decisions determine, as [(name, text or None, interim)].

 After each write every link and anchor of the pages resolves and the manifest lists only present pages, so a run
 killed between two writes leaves valid pages. A new ledger comes first. Then an interim index that lists only the
 identities documented both by the family pages on disk and in the result: the index never links a section that a
 family page is about to drop or has not yet regained. Then the family pages, the final index and the manifest, and a
 withdrawn ledger last. The interim index is the final one when the decisions only strike, and the index on disk
 when they only withdraw."""
 root=Path(root);files=nullified_docs(root,resolved);ledger=files.pop(NULLIFICATION_PAGE);manifest=files.pop('manifest.json');index=files.pop('Catalogue.md')
 section=json.loads((root/'components.json').read_text())['catalogue'];struck={x['key'] for x in resolved if x['scope']=='current-identity'};documented=set()
 for family in FAMILIES:
  path=root/family['page']
  if path.is_file():documented|={line[4:] for line in path.read_text().split('\n') if line.startswith('### ')}
 interim=catalogue_pages(section,[x['id'] for x in section['entries'] if x['id'] in struck or x['id'] not in documented])['Catalogue.md']
 writes=([] if ledger is None else [(NULLIFICATION_PAGE,ledger,False)])+[('Catalogue.md',interim,True)]+[(name,text,False) for name,text in files.items()]
 writes+=[('Catalogue.md',index,False),('manifest.json',manifest,False)]
 if ledger is None:writes.append((NULLIFICATION_PAGE,None,False))
 return writes
def write_nullified_docs(root,resolved):
 """Write the files the decisions determine, in the order of nullified_docs_writes, skipping those already current."""
 root=Path(root)
 for name,text,_ in nullified_docs_writes(root,resolved):
  path=root/name
  if (path.read_text() if path.is_file() else None)==text:continue
  if text is None:path.unlink()
  else:path.write_text(text,encoding='utf-8')
def contract_decisions(path):
 """The current-identity and rendering-output decisions of the contract at path, resolved against this repository."""
 module=nullification()
 try:return module.load_contract(REPOSITORY,path)
 except module.NullificationError as error:raise SystemExit(str(error)) from None

CSS='body{max-width:1000px;margin:0 auto;padding:32px;color:#263138;background:#f7f5ef;font:17px/1.65 system-ui,sans-serif}nav{padding:18px;border-bottom:1px solid #b5c6c1;display:flex;gap:18px;flex-wrap:wrap}a{color:#176a62}h1,h2,h3{color:#244f4b;line-height:1.2}h1{font-size:38px}h2{margin-top:2em}pre{background:#10202b;color:#e3e8df;padding:18px;overflow:auto;border-radius:8px;font:13px/1.5 ui-monospace,monospace}code{font-family:ui-monospace,monospace}img{max-width:100%;height:auto;border:1px solid #aabcb8}table{border-collapse:collapse;width:100%;font-size:14px}td,th{border:1px solid #bdcbc6;padding:8px;text-align:left}th{background:#e1e9e2}footer{margin-top:40px;border-top:1px solid #bdcbc6;font-size:13px}'

def build(root,output):
 import markdown
 from reportlab.lib import colors
 from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
 from reportlab.lib.enums import TA_LEFT
 from reportlab.lib.utils import ImageReader
 from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Preformatted,Image,LongTable,TableStyle,KeepTogether
 root=Path(root).resolve();output=Path(output);pages=validate(root);m=json.loads((root/'manifest.json').read_text());output.mkdir(parents=True,exist_ok=True)
 if (root/'images').exists():shutil.copytree(root/'images',output/'images',dirs_exist_ok=True)
 for page in pages:
  for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',page.read_text()):
   u=urlsplit(target)
   if u.scheme or not u.path:continue
   asset=inside(root,str(page.parent.relative_to(root)/unquote(u.path)))
   if asset.suffix!='.md':
    destination=output/asset.relative_to(root);destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(asset,destination)
 class ReferencePDF(SimpleDocTemplate):
  def afterFlowable(self,flowable):
   if isinstance(flowable,Paragraph) and flowable.style.name in ('Heading1','Heading2','Heading3'):
    key='heading-'+str(getattr(self,'headingCount',0));self.headingCount=getattr(self,'headingCount',0)+1
    self.canv.bookmarkPage(key);self.canv.addOutlineEntry(flowable.getPlainText(),key,level=0,closed=False)
 styles=getSampleStyleSheet();styles['Normal'].fontSize=9.5;styles['Normal'].leading=14;styles['Normal'].spaceAfter=7
 for h in ['Heading1','Heading2','Heading3']:styles[h].textColor=colors.HexColor('#285650');styles[h].spaceBefore=15;styles[h].spaceAfter=8
 styles.add(ParagraphStyle('Cell',parent=styles['Normal'],fontSize=8,leading=11,spaceAfter=0))
 styles.add(ParagraphStyle('CodeSmall',fontName='Courier',fontSize=7,leading=9,textColor=colors.HexColor('#172f37'),spaceAfter=10))
 def md(text):return markdown.markdown(text,extensions=['fenced_code','tables','toc'],output_format='xhtml')
 def inline(element):
  s=ET.tostring(element,encoding='unicode');s=re.sub(r'^<[^>]+>|</[^>]+>$','',s)
  s=s.replace('<code>','<font name="Courier">').replace('</code>','</font>').replace('<strong>','<b>').replace('</strong>','</b>').replace('<em>','<i>').replace('</em>','</i>')
  s=re.sub(r'<a\s+href="([^"]+)"[^>]*>',lambda a:'<a href="'+a[1]+'">' if a[1].startswith(('http:','https:','mailto:')) else '<font color="#176a62">',s)
  # Local references stay readable and have live HTML counterparts; PDF chapter outlines provide navigation.
  s=re.sub(r'<font color="#176a62">(.*?)</a>',r'<font color="#176a62">\1</font>',s)
  return s
 def blocks(nodes):
  result=[]
  for el in nodes:
   tag=el.tag
   if tag in ('h1','h2','h3','h4'):
    result.append(Paragraph(inline(el),styles['Heading'+str(min(int(tag[1]),3))]))
   elif tag=='pre':
    content=''.join(el.itertext());lines=[]
    for line in content.splitlines():lines+=textwrap.wrap(line,102,replace_whitespace=False,drop_whitespace=False) or ['']
    result.append(Preformatted('\n'.join(lines),styles['CodeSmall']))
   elif tag in ('ul','ol'):
    for i,li in enumerate(el):result.append(Paragraph((str(i+1)+'. ' if tag=='ol' else '- ')+inline(li),styles['Normal']))
   elif tag=='table':
    rows=[]
    for tr in el.iter('tr'):rows.append([Paragraph(inline(c),styles['Cell']) for c in tr])
    if rows:
     table=LongTable(rows,colWidths=[492/len(rows[0])]*len(rows[0]),repeatRows=1,hAlign='LEFT');table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e3ede7')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#b8c9c2')),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));result+=[table,Spacer(1,9)]
   elif tag=='p' and el.find('img') is not None:
    for image in el.findall('img'):
     path=inside(root,unquote(image.attrib['src']));w,h=ImageReader(str(path)).getSize();scale=min(492/w,220/h)
     heading=[result.pop()] if result and isinstance(result[-1],Paragraph) and result[-1].style.name=='Heading3' else []
     result.append(KeepTogether(heading+[Image(str(path),w*scale,h*scale,hAlign='LEFT'),Paragraph(html.escape(image.attrib.get('alt','')),styles['Cell']),Spacer(1,10)]))
   elif tag=='hr':result.append(Spacer(1,12))
   else:result.append(Paragraph(inline(el),styles['Normal']))
  return result
 groups={'Nocturne-SDK-Reference.pdf':m['pages'],**m.get('pdfs',{})}
 nav=' '.join('<a href="'+p.with_suffix('.html').name+'">'+html.escape(p.stem.replace('-',' '))+'</a>' for p in pages)
 downloads=' '.join('<a href="'+html.escape(name,quote=True)+'">'+html.escape(Path(name).stem.replace('-',' '))+'</a>' for name in groups)
 for page in pages:
  body=md(page.read_text());body=re.sub(r'href="([^"#]+)\.md([^"]*)"',r'href="\1.html\2"',body)
  (output/page.with_suffix('.html').name).write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>'+html.escape(page.stem)+'</title><style>'+CSS+'</style><nav>'+nav+'</nav><details><summary>PDF downloads</summary><nav>'+downloads+'</nav></details><main>'+body+'</main><footer>Nocturne SDK Reference.</footer></html>')
 def footer(canvas,doc):
  canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#54706a'));canvas.drawString(51,30,m['title']);canvas.drawRightString(543,30,str(doc.page))
 for name,selected in groups.items():
  flow=[]
  for i,source in enumerate(selected):
   if i:flow.append(PageBreak())
   flow.extend(blocks(ET.fromstring('<root>'+md((root/source).read_text())+'</root>')))
  ReferencePDF(str(output/name),pagesize=(595,842),rightMargin=52,leftMargin=51,topMargin=45,bottomMargin=48,title=m['title'],author='Nocturne',pageCompression=1).build(flow,onFirstPage=footer,onLaterPages=footer)
 record={'schema':'nocturne.reference-build.v1','pageSources':m['pages'],'sources':{p.relative_to(root).as_posix():sha(p) for p in pages},'manifestSha256':sha(root/'manifest.json'),'sourceAssets':{p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob('*')) if p.is_file() and p.suffix!='.md' and not p.resolve().is_relative_to(output.resolve())},'outputs':{p.relative_to(output).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(output.rglob('*')) if p.is_file() and p.name!='BUILD.json'},'scope':'Rendered documentation; runtime verification is recorded separately.'}
 (output/'BUILD.json').write_text(json.dumps(record,indent=2)+'\n');return record

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2]/'docs/current');p.add_argument('--output',type=Path);p.add_argument('--check',action='store_true');p.add_argument('--update-commands',action='store_true');p.add_argument('--update-catalogue',action='store_true');p.add_argument('--library',type=Path)
 p.add_argument('--nullification',type=Path,default=REPOSITORY/'native/contract/NULLIFICATION.json',help='nullification contract whose decisions the catalogue pages and the nullification page apply')
 p.add_argument('--update-nullification',action='store_true',help='rewrite the catalogue pages, nullification page and manifest from components.json and the nullification contract; needs no library');a=p.parse_args()
 if a.update_commands:
  source=Path(__file__).resolve().parents[1]/'web';inventory=json.loads((source/'workshop_fields.json').read_text());guidance=json.loads((source/'workshop_help.json').read_text())
  (a.root/'Commands.md').write_text(command_reference(inventory,guidance));shutil.copyfile(source/'workshop_fields.json',a.root/'command-inventory.json');shutil.copyfile(source/'workshop_help.json',a.root/'command-help.json');print(json.dumps({'operations':len(inventory['operations']),'fields':len(inventory['fields']),'guidance':len(guidance['parameters'])}));return
 if a.update_nullification:
  resolved=contract_decisions(a.nullification);write_nullified_docs(a.root,resolved)
  print(json.dumps({'nullified':[x['key'] for x in resolved],'ledger':(a.root/NULLIFICATION_PAGE).is_file()}));return
 if a.update_catalogue:
  resolved=contract_decisions(a.nullification)
  catalogue_path=Path(__file__).resolve().parents[1]/'catalogue.json'
  catalogue=json.loads(catalogue_path.read_text());inventory=json.loads((a.root/'command-inventory.json').read_text());guidance=json.loads((a.root/'command-help.json').read_text())
  registry=json.loads((a.root/'components.json').read_text())
  observed=observe_catalogue(catalogue,inventory,guidance,a.library);observed['domains']=observe_domains(catalogue,inventory,guidance,a.library)
  observed['defaults']=observe_defaults(catalogue,inventory,guidance,a.library);observed['probes']=observe_probes(catalogue,inventory,guidance,a.library)
  registry['catalogue']=catalogue_reference(catalogue,inventory,guidance,observed,{'catalogue':sha(catalogue_path),'commandInventory':sha(a.root/'command-inventory.json'),'commandHelp':sha(a.root/'command-help.json')})
  (a.root/'components.json').write_text(json.dumps(registry,indent=2)+'\n')
  write_nullified_docs(a.root,resolved)
  print(json.dumps({'identities':len(registry['catalogue']['entries']),'gaps':{key:len(value) for key,value in registry['catalogue']['gaps'].items()}}));return
 if a.check:
  pages=validate(a.root);resolved=contract_decisions(a.nullification)
  try:check_nullified_docs(a.root,resolved)
  except ValueError as error:raise SystemExit(str(error)) from None
  print(json.dumps({'validated':[x.name for x in pages]}));return
 if a.output is None:p.error('--output is required for build')
 print(json.dumps(build(a.root,a.output),indent=2))
if __name__=='__main__':main()
