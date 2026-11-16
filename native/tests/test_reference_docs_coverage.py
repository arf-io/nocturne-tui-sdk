"""Every native catalogue identity is documented with the commands that accept it,
their parameters, defaults and domains, and examples the native engine itself confirms."""
import ctypes,hashlib,importlib.util,json,re,sys,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CURRENT=ROOT.parent/'docs/current'
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene

spec=importlib.util.spec_from_file_location('reference_docs',ROOT/'scripts/build_reference_docs.py')
docs=importlib.util.module_from_spec(spec);spec.loader.exec_module(docs)

LIBRARY=ROOT/'dist'/('libnocturne_native.dylib' if sys.platform=='darwin' else 'libnocturne_native.so')

def require_library():
 """Examples are confirmed by the real native library; without it the check is blocked, not passed."""
 if not LIBRARY.is_file():raise AssertionError('BLOCKED: '+str(LIBRARY)+' is not built; run sh build-native.sh')
def load(path):return json.loads(Path(path).read_text())
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def flat(value,prefix=''):
 """Flatten nested objects to dotted field paths; arrays stay whole values."""
 out={}
 for key,item in value.items():
  path=prefix+key
  if isinstance(item,dict):out.update(flat(item,path+'.'))
  else:out[path]=item
 return out

def readback(info,family):
 """Readback values by command field path; microsecond readbacks answer millisecond fields."""
 values=flat(info[FAMILY_READBACK[family]][0])
 values.update({key[:-2]+'Ms':value/1000 for key,value in list(values.items()) if key.endswith('Us') and isinstance(value,(int,float))})
 return values

# The effect field of each native command validates one catalogue family (commands.c effect(...,family)).
FAMILY_COMMANDS={0:('emitter','weather-author'),1:('field',),2:('text',),3:('window','window-action')}
FAMILY_READBACK={0:'emitters',1:'fields',2:'textRuns',3:'windows'}
# Guidance states a numeric maximum for these parameters; the examples show it accepted and one beyond it refused.
MAXIMUM_PROBES={'emitter':'count','text':'durationMs','window':'durationMs'}
# weather-author group members that take another emitter field name (commands.c weatherAuthorProjection).
ALIASES={'collision.enabled':'collision','birth.orientation':'birthOrientation'}
# A default quoted from the guidance, or projected from it onto weather-author, is one JSON value or a backticked name unless
# it is classified here. These state it in words: the exact text, and how the engine proves it (prove_stated_default).
STATED_IN_WORDS={
 'emitter.id':'Required','weather-author.id':'Required',
 'emitter.angularVelocity':'Unauthored','emitter.initialOrientation':'Unauthored',
 'weather-author.birth.angularVelocity':'Unauthored','weather-author.birth.initialOrientation':'Unauthored',
 'emitter.colliders':'Default floor selection',
 'emitter.seed':'Hash of scene seed XOR emitter ID','weather-author.emission.seed':'Hash of scene seed XOR emitter ID',
 'emitter.startTimeUs':'Current scene time','weather-author.emission.startTimeUs':'Current scene time',
 'window.position':'Slot-dependent arrangement','window.seed':'Scene seed','window.text':'Empty','window.title':'Empty'}
WORDS={
 'Required':'the command without the field is refused with the diagnostic in REQUIRED, and accepted when the field is named',
 'Unauthored':'info reads back authoredMotion 0 without the field, and 1 when the field is named',
 'Default floor selection':'info reads back colliders {"floor":true,"surfaces":[]} without the field, and the floor deselected when that is named',
 'Hash of scene seed XOR emitter ID':'the command without the field leaves the snapshot of naming nrHash(scene seed XOR emitter id), in two scenes with two ids',
 'Current scene time':'the command without the field leaves the snapshot of naming the clock that info reads back, at two scene times',
 'Slot-dependent arrangement':'the command without the field leaves the snapshot of naming the position that info reads back, for windows in two slots with different positions',
 'Scene seed':'the command without the field leaves the snapshot of naming the scene seed, in two scenes',
 'Empty':'the command without the field leaves the snapshot of naming the empty string'}
REQUIRED={'emitter.id':'Emitter id required','weather-author.id':'Weather author requires id and effect'}
# These state one value for each source field of their guidance row, in that order: "8000,14000" is lifetimeMinMs 8000 and
# lifetimeMaxMs 14000. Each is proven as the literal value at its own position.
STATED_PER_SOURCE_FIELD={'emitter.lifetimeMinMs','emitter.lifetimeMaxMs','emitter.sizeMin','emitter.sizeMax',
 'weather-author.lifecycle.lifetimeMinMs','weather-author.lifecycle.lifetimeMaxMs','weather-author.particle.sizeMin','weather-author.particle.sizeMax',
 'window.anchorX','window.anchorY','window.fadeStartRatio','window.fadeEndRatio','window.width','window.height','window.minColumns','window.maxColumns'}
# collision false is refused while deposit is true ("Deposition requires collision"), so collision is observed with deposit false.
STATED_WITH={'emitter.collision':{'deposit':False},'weather-author.collision.enabled':{'collision.deposit':False}}
# A free name the guidance states as a default, and other names the engine accepts for it.
OTHER_NAMES={'window.shape':['ellipse','rounded']}

def named(commands,field,value):
 """The command list with field, a dotted path within the last command, set to value."""
 last=json.loads(json.dumps(commands[-1]));node=last;keys=field.split('.')
 for key in keys[:-1]:node=node.setdefault(key,{})
 node[keys[-1]]=value;return commands[:-1]+[last]
def without(commands,field):
 """The command list with field, a dotted path within the last command, removed."""
 last=json.loads(json.dumps(commands[-1]));node=last;keys=field.split('.')
 for key in keys[:-1]:node=node.get(key,{})
 node.pop(keys[-1],None);return commands[:-1]+[last]
def stated_literal(text):
 """A default stated as one JSON value or a backticked name, as a one-item tuple; None for any other text."""
 code=text[1:-1] if len(text)>2 and text[0]==text[-1]=='`' else None
 try:return (json.loads(text if code is None else code),)
 except ValueError:return None if code is None else (code,)

class CatalogueCoverage(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.catalogue=load(ROOT/'catalogue.json')
  cls.registry=load(CURRENT/'components.json')
  cls.section=cls.registry.get('catalogue',{})
  cls.entries={x['id']:x for x in cls.section.get('entries',[])}
  cls.inventory=load(CURRENT/'command-inventory.json')
  cls.guidance=load(CURRENT/'command-help.json')
  cls.manifest=load(CURRENT/'manifest.json')
 def fields(self,op):return [x for x in self.inventory['fields'] if x['op']==op]

 def test_every_catalogue_id_has_an_entry(self):
  missing=[x['id'] for x in self.catalogue if x['id'] not in self.entries]
  self.assertEqual(missing,[],str(len(missing))+' of '+str(len(self.catalogue))+' catalogue ids are missing from docs/current/components.json: '+', '.join(missing))
  self.assertEqual(len(self.section['entries']),len(self.catalogue))
  self.assertEqual(len(self.entries),len(self.section['entries']))
 def test_entry_identity_matches_the_catalogue(self):
  for row in self.catalogue:
   with self.subTest(id=row['id']):
    entry=self.entries.get(row['id'],{})
    for key in ['id','name','family','contract','profile','algorithm','sourceIdentity','visualAcceptance']:
     self.assertIn(key,entry);self.assertEqual(entry.get(key),row[key],key)
    self.assertEqual(entry.get('commands'),list(FAMILY_COMMANDS[row['family']]))
 def test_the_atlas_of_captured_components_is_unchanged_and_the_pages_validate(self):
  atlas=self.registry['components']
  self.assertEqual(len(atlas),49)
  self.assertFalse({x['id'] for x in atlas}&{x['id'] for x in self.catalogue})
  self.assertTrue(all(x['states'] for x in atlas))
  names=[p.name for p in docs.validate(CURRENT)]
  for page in ['Catalogue.md','Catalogue-Weather.md','Catalogue-Surface-Fields.md','Catalogue-Text.md','Catalogue-Windows.md']:self.assertIn(page,names)
 def test_every_command_that_names_an_effect_is_covered(self):
  accepting={x['op'] for x in self.inventory['fields'] if x['field']=='effect'}
  covered={op for ops in FAMILY_COMMANDS.values() for op in ops}
  self.assertEqual(accepting,covered)
  self.assertEqual({x['family']:tuple(x['commands']) for x in self.section.get('families',[])},FAMILY_COMMANDS)
  self.assertEqual(set(self.section.get('commands',{})),covered)

 def test_parameter_tables_join_the_inventory_and_the_guidance(self):
  sources=self.section.get('sources',{})
  self.assertEqual(sources.get('catalogue'),digest(ROOT/'catalogue.json'))
  self.assertEqual(sources.get('commandInventory'),digest(CURRENT/'command-inventory.json'))
  self.assertEqual(sources.get('commandHelp'),digest(CURRENT/'command-help.json'))
  for op in {op for ops in FAMILY_COMMANDS.values() for op in ops}:
   with self.subTest(op=op):
    table=self.section.get('commands',{}).get(op,[])
    expected=self.fields(op)
    self.assertEqual([x.get('field') for x in table],[x['field'] for x in expected])
    for record,row in zip(table,expected):
     name=op+'.'+row['field']
     self.assertEqual(record['types'],row['types'],name);self.assertEqual(record['choices'],row['choices'],name)
     for key in ['default','defaultLabel','defaultSource','domain','domainSource']:self.assertIn(key,record,name)
     help=self.guidance['parameters'].get(name)
     if help and help['default'] is not None:
      self.assertEqual((record['default'],record['defaultLabel'],record['defaultSource']),(help['default'],help['defaultLabel'],'command-help'),name)
     if help and help['description']:
      self.assertEqual((record['domain'],record['domainSource']),(help['description'],'command-help'),name)
     if record['default'] is None:self.assertEqual(record['defaultSource'],'unresolved',name)
     if record['domain'] is None:self.assertEqual(record['domainSource'],'unresolved',name)
     if record['domain'] is not None:self.assertTrue(record['domain'].strip(),name)
 def test_weather_author_parameters_are_the_emitter_parameters_they_project_onto(self):
  emitter={x['field']:x for x in self.section.get('commands',{}).get('emitter',[])}
  aliases={'collision.enabled':'collision','birth.orientation':'birthOrientation'}
  projected=0
  expected=[x['field'] for x in self.fields('weather-author') if '.' in x['field']]
  for record in self.section.get('commands',{}).get('weather-author',[]):
   field=record['field']
   if '.' not in field:continue
   target=aliases.get(field,field.split('.',1)[1])
   self.assertIn(target,emitter,field);projected+=1
   for key in ['default','defaultLabel','domain']:self.assertEqual(record[key],emitter[target][key],field+' '+key)
   self.assertIn(record['defaultSource'],['projection','unresolved']);self.assertIn(record['domainSource'],['projection','unresolved'])
  self.assertEqual(projected,len(expected))
 def test_unresolved_parameters_are_listed_exactly(self):
  gaps=self.section.get('gaps',{})
  for key in ['default','domain']:
   expected=sorted(op+'.'+x['field'] for op,table in self.section.get('commands',{}).items() for x in table if x[key] is None)
   self.assertEqual(gaps.get(key),expected,key)
   # Every parameter has a default and a domain from the guidance, a projection, the declared type or the native library.
   # No domain is exempt as the full representational type: each one the guidance omits has a native bound.
   self.assertEqual(gaps.get(key),[],str(len(gaps.get(key) or []))+' parameters have no stated '+key+': '+', '.join(gaps.get(key) or []))
 def test_the_guide_and_the_release_notes_state_only_the_catalogue_gap_counts(self):
  """The reference guide and the unreleased changelog section name no count of parameters without a stated default or
  domain other than the length of catalogue.gaps, the list the catalogue pages are rendered from."""
  gaps=self.section['gaps']
  current=(ROOT.parent/'CHANGELOG.md').read_text().split('\n# ',1)[0]
  counts=re.compile(r'(\d+)(?: command)?(?: parameters?| fields?)?(?: still)?(?: have| has)? no stated (default|domain)')
  for document,text in (('docs/current/README.md',(CURRENT/'README.md').read_text()),('the first section of CHANGELOG.md',current)):
   for count,key in counts.findall(text):
    with self.subTest(document=document,key=key):
     self.assertEqual(int(count),len(gaps[key]),document+' says '+count+' parameters have no stated '+key+'; catalogue.gaps lists '+str(len(gaps[key])))
 def test_no_page_prints_a_parameter_without_a_default_or_domain(self):
  """No parameter row prints "not stated" as its default, domain or basis, and the catalogue lists no parameter without them."""
  pages=docs.catalogue_pages(self.section)
  for name,text in pages.items():
   with self.subTest(page=name):
    rows=[line for line in (CURRENT/name).read_text().splitlines() if line.startswith('| `') and line.count(' | ')==4]
    if name!='Catalogue.md':self.assertGreater(len(rows),0,name+' has no parameter table')
    for row in rows:self.assertNotIn('not stated',' | '.join(row.split(' | ')[2:]),row)
  self.assertNotIn('## Parameters without a default or domain',pages['Catalogue.md'],'the catalogue lists no parameter without a default or domain, so it has no section for them')
 def check_citations(self,evidence,name):
  """A citation names the native statement at its file and line; the evidence proves it, the citation locates it."""
  citations=evidence.get('cite',[])
  self.assertTrue(citations,name+' cites no native statement')
  for cite in citations:
   lines=(ROOT.parent/cite['path']).read_text().splitlines()
   self.assertLessEqual(cite['line'],len(lines),name)
   self.assertIn(cite['text'],lines[cite['line']-1],name+': '+cite['path']+':'+str(cite['line'])+' no longer holds the cited statement; regenerate with --update-catalogue')
 def test_a_citation_is_located_inside_its_handler(self):
  """A statement is cited inside its handler's block, not in a later handler that repeats it; a statement that is not there is
  an error, not a guess."""
  [cite]=docs.cite('window','w->anchorX=.5;')
  lines=(ROOT.parent/cite['path']).read_text().splitlines()
  start,end=(next(i for i,x in enumerate(lines) if anchor in x)+1 for anchor in ['if(!strcmp(op,"window")) {','if(!strcmp(op,"window-action")) {'])
  self.assertEqual(cite['path'],'native/src/commands.c');self.assertIn('w->anchorX=.5;',lines[cite['line']-1])
  self.assertTrue(start<cite['line']<end,'the window handler, not the window-action or gather handler that repeat the statement')
  with self.assertRaises(ValueError):docs.cite('window','no such statement;')
  with self.assertRaises(ValueError):docs.cite('unknown handler','w->anchorX=.5;')
 def test_every_default_the_guidance_does_not_state_is_proven_by_the_engine(self):
  """Every default is proven by the engine, whatever its basis; none passes because it is quoted. A default that is not
  quoted from the guidance or projected from the emitter is read back from the engine, or observed: the command that omits
  the field leaves a byte-identical document to the command naming the default, and another accepted value changes the
  document, or the omission itself is refused and the default is required. Each of those cites its native statement.
  A default quoted from the guidance or projected onto weather-author is observed in the same way (prove_stated_default),
  and an observed default reads back from info after the minimal command (prove_read_back_default)."""
  require_library()
  allowed={'command-help','projection','engine-readback','engine-omission','engine-required','engine-info','engine-conditional'};states={};proven=0;checked=[]
  # The observation each engine basis states: applied when omitted, refused when omitted, read back from info, or refused when
  # omitted under the condition its default names.
  observation={'engine-omission':'omitted','engine-required':'refused','engine-info':'readback','engine-conditional':'refused'}
  with NativeScene() as scene:
   nrHash=scene._lib.nrHash;nrHash.restype=ctypes.c_uint32;nrHash.argtypes=[ctypes.c_uint32]
   def state(commands):
    key=json.dumps(commands,sort_keys=True)
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
   for op,table in self.section['commands'].items():
    for record in table:
     name=op+'.'+record['field']
     with self.subTest(parameter=name):
      self.assertIn(record['defaultSource'],allowed,name+' has no default from the guidance, a projection or the engine')
      if record['defaultSource'] in ('command-help','projection'):self.prove_stated_default(state,info,nrHash,op,record)
      elif record['defaultSource']=='engine-readback':self.prove_read_back_default(info,op,record)
      else:
       evidence=record.get('defaultEvidence',{});self.check_citations(evidence,name);proven+=1
       self.assertTrue(evidence.get(observation[record['defaultSource']]),name+' records no '+observation[record['defaultSource']]+' observation for its basis '+record['defaultSource'])
       # An edited row omits the field when editing an existing resource: it keeps the value the resource already has.
       for row in evidence.get('omitted',[])+evidence.get('edited',[]):
        base=state(row['commands']);self.assertFalse(base.startswith('refused'),name+': '+base)
        self.assertEqual(state(named(row['commands'],row['field'],row['value'])),base,name+' = '+json.dumps(row['value'])+' is not what the engine applies when it is omitted')
        other=state(named(row['commands'],row['field'],row['other']))
        self.assertFalse(other.startswith('refused'),name+': '+other)
        self.assertNotEqual(other,base,name+': '+json.dumps(row['other'])+' leaves the same document, so the equality proves nothing')
       for row in evidence.get('refused',[]):
        self.assertEqual(state(row['commands']),'refused: '+row['diagnostic'],name)
        self.assertFalse(state(row['accepted']).startswith('refused'),name+' is refused even when it is named')
       for row in evidence.get('readback',[]):
        live=info(row['commands']);self.assertEqual(flat(live[row['family']][0] if row['family'] else live).get(row['path'],'absent'),row['value'],name)
       if record['defaultSource']=='engine-required':self.assertEqual((record['default'],bool(evidence.get('refused'))),('required',True),name)
       else:self.assertTrue(record['default'].strip() and record['default']!='required',name)
      checked.append(name)
  # The parameters without guidance are each proven; none may pass by recording nothing.
  self.assertGreater(proven,0,'no default is proven by the engine')
  # Every default of every parameter was proven by its basis; no parameter was passed over.
  self.assertEqual(checked,[op+'.'+x['field'] for op,table in self.section['commands'].items() for x in table])
 def test_the_defaults_stated_in_words_or_per_source_field_are_classified_exactly(self):
  """Every quoted or projected default that is not one value is classified, and every classified name is such a default, so
  that a classification cannot go stale when a row is renamed, removed or given another basis."""
  stated={op+'.'+x['field']:x['default'] for op,table in self.section['commands'].items() for x in table if x['defaultSource'] in ('command-help','projection')}
  self.assertEqual(sorted(name for name,text in stated.items() if stated_literal(text) is None),sorted(set(STATED_IN_WORDS)|STATED_PER_SOURCE_FIELD))
  self.assertFalse(set(STATED_IN_WORDS)&STATED_PER_SOURCE_FIELD)
  self.assertEqual({name:stated[name] for name in STATED_IN_WORDS},STATED_IN_WORDS)
  self.assertLessEqual(set(STATED_IN_WORDS.values()),set(WORDS));self.assertEqual(set(REQUIRED),{x for x,text in STATED_IN_WORDS.items() if text=='Required'})
 def stated_subject(self,op):
  """The minimal command for the identity that a quoted or projected default describes. The emitter guidance describes the
  base autumn-leaf configuration (native/docs/manual/WEATHER-AND-EMITTERS.md) and emitterDefaults (commands.c) overrides
  some of it for other algorithms, so every weather row is observed with the first leaf identity of the catalogue
  (algorithm 0), and a window row with the first window identity."""
  family=next(family for family,ops in FAMILY_COMMANDS.items() if op in ops)
  identity=next(x['id'] for x in self.catalogue if x['family']==family and (family!=0 or x['algorithm']==0))
  return docs.command_for(op,identity),family
 def assert_applied_when_omitted(self,state,commands,field,value,others,name):
  """The commands omit field. Naming value leaves the same snapshot, and naming one of others changes it."""
  base=state(commands);self.assertFalse(base.startswith('refused'),name+': '+base)
  self.assertEqual(state(named(commands,field,value)),base,name+' = '+json.dumps(value)+' is not what the engine applies when it is omitted')
  changed=next((x for x in others if not state(named(commands,field,x)).startswith('refused') and state(named(commands,field,x))!=base),None)
  self.assertIsNotNone(changed,name+': no other accepted value of '+json.dumps(others)+' changes the document, so the equality proves nothing')
 def prove_stated_default(self,state,info,nrHash,op,record):
  """A default quoted from the guidance or projected onto weather-author is what the engine applies when the field is
  omitted. A literal value, or the value at the field's position when the guidance states one per source field, leaves the
  snapshot of the command that omits the field when named, and another accepted value changes it. A default stated in words
  is proven as WORDS says."""
  field=record['field'];name=op+'.'+field;text=record['default'];subject,family=self.stated_subject(op)
  row=next(x for x in self.fields(op) if x['field']==field);base=without(subject,field)
  for key,value in STATED_WITH.get(name,{}).items():base=named(base,key,value)
  if name in STATED_IN_WORDS:
   self.assertEqual(text,STATED_IN_WORDS[name],name+' is classified as stated in other words');self.assertIn(text,WORDS)
   if text=='Required':
    self.assertEqual(state(base),'refused: '+REQUIRED[name],name+' is stated as required');self.assertFalse(state(subject).startswith('refused'),name+' is refused even when it is named')
   elif text=='Unauthored':
    self.assertEqual(info(base)[FAMILY_READBACK[family]][0]['authoredMotion'],0,name)
    self.assertEqual(info(named(base,field,[0,0,0]))[FAMILY_READBACK[family]][0]['authoredMotion'],1,name+': naming it authors no motion, so the readback proves nothing')
   elif text=='Default floor selection':
    self.assertEqual(info(base)[FAMILY_READBACK[family]][0]['colliders'],{'floor':True,'surfaces':[]},name)
    self.assertEqual(info(named(named(base,'deposit',False),field,{'floor':False,'surfaces':[]}))[FAMILY_READBACK[family]][0]['colliders'],{'floor':False,'surfaces':[]},name+': the readback does not follow the selection')
   elif text=='Hash of scene seed XOR emitter ID':
    for seed,ident in ((2030,1),(4242,7)):
     value=nrHash(seed^ident);self.assert_applied_when_omitted(state,[{'op':'reset','seed':seed}]+named(base,'id',ident),field,value,[value^1],name)
   elif text=='Current scene time':
    clocks=[]
    for setup in ([],[{'op':'time','timeUs':250000}]):
     now=info(setup)['clock']['timeUs'];clocks.append(now);self.assert_applied_when_omitted(state,setup+base,field,now,[now+1000],name)
    self.assertEqual(len(set(clocks)),2,name+' is observed at one scene time only')
   elif text=='Slot-dependent arrangement':
    positions=[]
    for setup in ([],[{'op':'window','id':2}]):
     position=next(x for x in info(setup+base)[FAMILY_READBACK[family]] if x['id']==subject[-1]['id'])['position'];positions.append(position)
     self.assert_applied_when_omitted(state,setup+base,field,position,[[position[0]+1]+position[1:]],name)
    self.assertNotEqual(positions[0],positions[1],name+' reads back the same position in two slots')
   elif text=='Scene seed':
    for seed in (2030,4242):self.assert_applied_when_omitted(state,[{'op':'reset','seed':seed}]+base,field,seed,[seed+1],name)
   else:self.assert_applied_when_omitted(state,base,field,'',['a'],name)
   return
  if name in STATED_PER_SOURCE_FIELD:
   source=ALIASES.get(field,field.split('.')[-1]) if op=='weather-author' else field
   help=self.guidance['parameters'][('emitter' if op=='weather-author' else op)+'.'+source];parts=text.split(',')
   self.assertGreater(len(help['sourceFields']),1,name);self.assertEqual(len(parts),len(help['sourceFields']),name)
   value=json.loads(parts[help['sourceFields'].index(source)])
  else:
   literal=stated_literal(text);self.assertIsNotNone(literal,name+' states "'+text+'", which is neither one value nor classified')
   value=literal[0]
  if isinstance(value,bool):others=[not value]
  elif row['choices']:others=[x for x in row['choices'] if x!=value]
  elif isinstance(value,(int,float)):others=[value+1,value-1,value+.5,value/2]
  elif isinstance(value,list):others=[[value[0]+step]+value[1:] for step in (1,-1,.5)]+[[value[0]/2]+value[1:]]
  elif field=='effect':others=[x['id'] for x in self.catalogue if x['family']==family and x['id']!=value][:3]
  else:others=OTHER_NAMES.get(name,[])
  self.assert_applied_when_omitted(state,base,field,value,others,name)
 def prove_read_back_default(self,info,op,record):
  """An observed default reads back from info after the minimal command of the first identity whose entry lists no other
  starting value for it."""
  family=next(family for family,ops in FAMILY_COMMANDS.items() if op in ops)
  entry=next(x for x in self.section['entries'] if x['family']==family and record['field'] not in x['startingValues'])
  example=next(x for x in entry['examples']['positive'] if x['op']==op)['commands']
  self.assertEqual(readback(info(example),family).get(record['field']),json.loads(record['default']),op+'.'+record['field'])
 def test_text_defaults_hold_for_every_identity_of_its_profile(self):
  """The defaults a new text run receives are applied for every identity, at the value its catalogue profile selects."""
  require_library()
  table=self.section['commands']['text'];values={0:{},1:{}}
  for record in table:
   if record['defaultSource']!='engine-omission':continue
   rows=[x for x in record['defaultEvidence'].get('omitted',[]) if len(x['commands'])==1 and set(x['commands'][0])=={'op','id','effect'}]
   if not rows:continue
   keyed={x.get('profile'):x['value'] for x in rows}
   for profile in (0,1):
    self.assertTrue(profile in keyed or None in keyed,record['field']+' has no observed value for profile '+str(profile))
    values[profile][record['field']]=keyed.get(profile,keyed.get(None))
  self.assertGreaterEqual(len(values[0]),21,'the defaults of a new text run are not observed')
  self.assertTrue(any(values[0][x]!=values[1][x] for x in values[0]),'no default differs by profile, yet the pages state profile values')
  with NativeScene() as scene:
   def state(command):
    scene.command({'op':'reset','seed':2030});scene.command(command);return hashlib.sha256(scene.snapshot()).hexdigest()
   for row in [x for x in self.catalogue if x['family']==2]:
    with self.subTest(id=row['id'],profile=row['profile']):
     minimal={'op':'text','id':1,'effect':row['id']}
     self.assertEqual(state({**minimal,**values[row['profile']]}),state(minimal),'naming every observed default changes the document of '+row['id'])
 def test_domains_the_guidance_does_not_state_are_observed_from_accepted_and_refused_commands(self):
  """A domain that is not quoted from the guidance, declared by the type or the catalogue, or observed as a numeric interval
  is shown by accepted commands at its edges and refused commands beyond them, each with the exact native diagnostic."""
  require_library()
  allowed={'command-help','projection','inventory','catalogue','engine-refusals','engine-probes'};probed=0
  with NativeScene() as scene:
   for op,table in self.section['commands'].items():
    for record in table:
     name=op+'.'+record['field']
     with self.subTest(parameter=name):
      self.assertIn(record['domainSource'],allowed,name+' has no domain from the guidance, the declared type, the catalogue or the engine')
      if record['domainSource']!='engine-probes':continue
      evidence=record.get('domainEvidence',{});self.check_citations(evidence,name);probed+=1
      probes=evidence.get('probes',[])
      self.assertTrue(any(x['diagnostic'] is None for x in probes),name+' has no accepted probe')
      self.assertTrue(any(x['diagnostic'] for x in probes),name+' has no refused probe')
      for probe in probes:
       scene.command({'op':'reset','seed':2030})
       for setup in probe['commands'][:-1]:scene.command(setup)
       if probe['diagnostic'] is None:
        try:result=scene.command(probe['commands'][-1])
        except ValueError as error:self.fail(name+': '+probe['label']+' is documented as accepted but refused: '+str(error))
        self.assertEqual(result,0,name+': '+probe['label']);continue
       before=scene.snapshot()
       with self.assertRaises(ValueError,msg=name+': '+probe['label']) as refused:scene.command(probe['commands'][-1])
       self.assertEqual(str(refused.exception),probe['diagnostic'],name+': '+probe['label'])
       self.assertEqual(scene.snapshot(),before,name+': '+probe['label']+': a refused command must leave the document unchanged')
      # An observed interval is the pair of its edge probes: accepted at low and high, refused just beyond, in the domain text.
      edges=[x for x in probes if 'path' in x];intervals=evidence.get('intervals',[])
      self.assertEqual(len(edges),4*len(intervals),name+': each observed interval has four edge probes')
      for number,interval in enumerate(intervals):
       low,below,high,above=edges[4*number:4*number+4]
       for probe in (low,below,high,above):
        node=probe['commands'][-1]
        for key in probe['path']:node=node[key]
        self.assertEqual(node,probe['value'],name+': '+probe['label']+' does not name the value it records')
       self.assertEqual((low['value'],high['value'],low['diagnostic'],high['diagnostic']),(interval['low'],interval['high'],None,None),name)
       self.assertTrue(below['diagnostic'] and above['diagnostic'] and below['value']<low['value'] and above['value']>high['value'],name)
       if interval['lattice']=='integer':self.assertEqual((below['value'],above['value']),(low['value']-1,high['value']+1),name)
       self.assertIn(docs.compact(interval['low'])+' to '+docs.compact(interval['high']),record['domain'],name)
  self.assertGreater(probed,0,'no domain is observed from probes')

 def test_a_citation_is_the_only_occurrence_of_its_statement_inside_the_handler(self):
  """A statement is cited where it occurs once between its handler's anchor and the end of the block that the anchor opens
  or encloses. A statement repeated there, or found only past that block, is an error, not its first match."""
  with self.assertRaises(ValueError):docs.cite('window-action','DUR("durationMs",w->durationUs,60000000,1000);')
  with self.assertRaises(ValueError):docs.cite('window','CHECK(i>=0,"Window not found");')
  with self.assertRaises(ValueError):docs.cite('presentation-valid','return seen == 0x0fu;')
  [cite]=docs.cite('window-action-transition','DUR("durationMs",w->durationUs,60000000,1000);')
  lines=(ROOT.parent/cite['path']).read_text().splitlines()
  fade=next(number for number,line in enumerate(lines) if 'if(action==15){DUR("durationMs"' in line)+1
  following=next(number for number,line in enumerate(lines) if 'if(!strcmp(op,"window-action")) {' in line)+1
  self.assertTrue(fade<cite['line'],'the statement that every transition action reads, not the fade branch before it')
  self.assertIn('DUR("durationMs",w->durationUs,60000000,1000);',lines[cite['line']-1]);self.assertGreater(fade,following)
  record=next(x for x in self.section['commands']['window-action'] if x['field']=='durationMs')
  self.assertEqual([x['line'] for x in record['defaultEvidence']['cite']],[cite['line']],'window-action.durationMs cites the fade branch')
 def test_polygon_and_glyph_domains_state_the_engine_rule_with_probes_at_its_edges(self):
  """window.polygon states the shoelace bound of commands.c, and window.customGlyphs the scalars that
  window_source_presentation.c refuses and the comma that separates the glyphs, each with probes on both sides."""
  window={x['field']:x for x in self.section['commands']['window']}
  polygon,glyphs=window['polygon'],window['customGlyphs']
  for text in ('shoelace sum','1e-8'):self.assertIn(text,polygon['domain'])
  self.assertNotIn('nonzero area',polygon['domain'])
  for text in ('U+0000 to U+001F','U+007F to U+009F','comma'):self.assertIn(text,glyphs['domain'])
  def shoelace(points):return sum(points[k][0]*points[(k+1)%len(points)][1]-points[(k+1)%len(points)][0]*points[k][1] for k in range(len(points)))
  shapes=[(x['commands'][-1]['polygon'],x['diagnostic']) for x in polygon['domainEvidence']['probes']]
  degenerate=[points for points,diagnostic in shapes if diagnostic=='Degenerate polygon']
  self.assertIn([[0,0],[1,1],[1,0],[0,1]],degenerate,'a bow-tie whose lobes cancel is refused')
  self.assertTrue(any(0<abs(shoelace(points))<1e-8 for points in degenerate),'a sliver just under the bound is refused')
  self.assertTrue(any(diagnostic is None and 1e-8<abs(shoelace(points))<2e-8 for points,diagnostic in shapes),'a sliver just over the bound is accepted')
  self.assertTrue(any(diagnostic is None and shoelace(points)<0 for points,diagnostic in shapes),'a clockwise outline is accepted')
  self.assertTrue(all(abs(shoelace(points))<=1e-8 for points in degenerate))
  values={x['commands'][-1]['customGlyphs']:x['diagnostic'] for x in glyphs['domainEvidence']['probes']}
  for refused in ('\u001f,b,c,d','\u007f,b,c,d','\u009f,b,c,d','a,,,c,d'):self.assertTrue(values.get(refused),repr(refused)+' is not shown refused')
  for accepted in (' ,b,c,d','~,b,c,d','\u00a0,b,c,d'):self.assertIn(accepted,values);self.assertIsNone(values[accepted],repr(accepted))
 def test_a_default_with_the_basis_applied_when_omitted_has_an_omission_observation(self):
  """The family pages say that a default with the basis applied when omitted left byte-identical snapshots omitted and
  named. A default shown only by an info readback, or by a refusal under the condition it names, has a basis of its own."""
  for op,table in self.section['commands'].items():
   for record in table:
    if record['defaultSource']=='engine-omission':
     with self.subTest(parameter=op+'.'+record['field']):self.assertTrue(record['defaultEvidence'].get('omitted'),op+'.'+record['field']+' records no omission')
  surface=next(x for x in self.section['commands']['field'] if x['field']=='surface')
  polygon=next(x for x in self.section['commands']['window'] if x['field']=='polygon')
  self.assertEqual((surface['defaultSource'],bool(surface['defaultEvidence'].get('readback'))),('engine-info',True))
  self.assertEqual((polygon['defaultSource'],bool(polygon['defaultEvidence'].get('refused'))),('engine-conditional',True))
  rows={line.split(' | ')[0]:line for name in ('Catalogue-Surface-Fields.md','Catalogue-Windows.md') for line in (CURRENT/name).read_text().splitlines() if line.startswith('| `surface` |') or line.startswith('| `polygon` |')}
  self.assertIn('read back from info',rows['| `surface`']);self.assertNotIn('applied when omitted',rows['| `surface`'])
  self.assertIn('refused when omitted under a condition',rows['| `polygon`']);self.assertNotIn('applied when omitted',rows['| `polygon`'])
 def test_field_seed_with_source_paint_is_observed_apart_from_the_scene_seed_and_a_first_field(self):
  """The paint-source clause of field.seed is the field id for algorithms 0 and 1 and the constant 2030 otherwise. One scene
  with seed 2030 and a first field cannot tell those from the scene seed or a constant 1, so another scene is recorded."""
  record=next(x for x in self.section['commands']['field'] if x['field']=='seed')
  algorithm={x['id']:x['algorithm'] for x in self.catalogue}
  apart=[x for x in record['defaultEvidence']['omitted'] if x['commands'][-1].get('paint')=='source' and x['commands'][0].get('op')=='reset'
   and x['commands'][0]['seed']!=2030 and sum(1 for command in x['commands'] if command['op']=='field')>1]
  self.assertTrue(any(algorithm[x['commands'][-1]['effect']]<2 and x['value']==sum(1 for command in x['commands'] if command['op']=='field') for x in apart),'the field id, not a constant 1')
  self.assertTrue(any(algorithm[x['commands'][-1]['effect']]>=2 and x['value']==2030 for x in apart),'the constant 2030, not the scene seed')
 def test_every_component_has_accepted_and_refused_examples(self):
  for row in self.catalogue:
   with self.subTest(id=row['id']):
    examples=self.entries.get(row['id'],{}).get('examples',{})
    positive,rejected=examples.get('positive',[]),examples.get('rejected',[])
    ops=list(FAMILY_COMMANDS[row['family']]);probe=MAXIMUM_PROBES.get(ops[0])
    self.assertEqual([x['op'] for x in positive],ops+([ops[0]] if probe else []))
    for op,example in zip(ops,positive):self.assertEqual(example['label'],'Minimal '+op+' command')
    self.assertEqual(len(rejected),2+bool(probe))
    if probe:
     text=self.guidance['parameters'][ops[0]+'.'+probe]['description'];maximum=int(re.search(r'(?:\.\.|\u2013)(\d+)',text)[1])
     self.assertEqual(positive[-1]['commands'][-1][probe],maximum);self.assertEqual(rejected[-1]['commands'][-1][probe],maximum+1)
    for example in positive+rejected:
     self.assertTrue(example['label']);self.assertTrue(example['commands'])
     self.assertIn(row['id'],json.dumps(example['commands'][-1]))
    for example in rejected:self.assertTrue(example['diagnostic'].strip())
 def test_examples_replay_against_the_native_engine(self):
  require_library()
  unchanged=set();replayed=0
  with NativeScene() as scene:
   for row in self.catalogue:
    for kind in ['positive','rejected']:
     for example in self.entries.get(row['id'],{}).get('examples',{}).get(kind,[]):
      replayed+=1
      with self.subTest(id=row['id'],kind=kind,label=example['label']):
       scene.command({'op':'reset','seed':2030})
       for setup in example['commands'][:-1]:scene.command(setup)
       if kind=='positive':
        self.assertEqual(scene.command(example['commands'][-1]),0)
       else:
        # Snapshots are 30 MB: prove the document is left unchanged for each family's first identity.
        before=scene.snapshot() if (row['family'],example['label']) not in unchanged else None
        with self.assertRaises(ValueError) as refused:scene.command(example['commands'][-1])
        self.assertEqual(str(refused.exception),example['diagnostic'])
        if before is not None:
         self.assertEqual(scene.snapshot(),before,'a refused command must leave the document unchanged');unchanged.add((row['family'],example['label']))
  # A document without examples must not pass by replaying nothing.
  self.assertEqual(replayed,sum(len(FAMILY_COMMANDS[row['family']])+2+2*bool(MAXIMUM_PROBES.get(FAMILY_COMMANDS[row['family']][0])) for row in self.catalogue))
 def unguided_numeric_fields(self):
  """Numeric scalars of the effect-naming commands for which the guidance gives no domain."""
  return [(x['op'],x['field']) for x in self.inventory['fields'] if x['op'] in ('field','window','window-action') and x['field']!='id' and '.' not in x['field']
   and not x['choices'] and x['types'][0].startswith('number') and not (self.guidance['parameters'].get(x['op']+'.'+x['field']) or {}).get('description')]
 def test_unguided_numeric_fields_have_domains_observed_from_refusals(self):
  targets=self.unguided_numeric_fields()
  self.assertGreaterEqual(len(targets),25)
  for op,field in targets:
   with self.subTest(parameter=op+'.'+field):
    record=next((x for x in self.section.get('commands',{}).get(op,[]) if x['field']==field),{})
    self.assertEqual(record.get('domainSource'),'engine-refusals')
    edges=record.get('domainEdges',{})
    self.assertIn(edges.get('lattice'),['integer','real'])
    for side in ['low','high']:
     if edges.get(side):self.assertEqual(sorted(edges[side]),['accepted','diagnostic','refused'])
    self.assertTrue(edges.get('low') or edges.get('high'))
 def test_observed_domains_hold_for_every_identity_of_the_family(self):
  require_library()
  checked=0
  with NativeScene() as scene:
   for op,table in self.section.get('commands',{}).items():
    owners=[x for x in self.entries.values() if op in x['commands']]
    for record in table:
     edges=record.get('domainEdges')
     if not edges:continue
     for number,entry in enumerate(owners):
      template=next(x for x in entry['examples']['positive'] if x['op']==op)['commands']
      checked+=1
      with self.subTest(parameter=op+'.'+record['field'],id=entry['id']):
       scene.command({'op':'reset','seed':2030})
       for setup in template[:-1]:scene.command(setup)
       def probe(value):return {**template[-1],**edges['with'],record['field']:value}
       for side in ['low','high']:
        if not edges.get(side):continue
        before=scene.snapshot() if number==0 else None
        with self.assertRaises(ValueError) as refused:scene.command(probe(edges[side]['refused']))
        self.assertEqual(str(refused.exception),edges[side]['diagnostic'])
        if before is not None:self.assertEqual(scene.snapshot(),before)
       for side in ['low','high']:
        if edges.get(side):self.assertEqual(scene.command(probe(edges[side]['accepted'])),0)
  # Every unguided numeric field is probed on every identity that its command accepts; none may be skipped.
  self.assertEqual(checked,sum(1 for op,field in self.unguided_numeric_fields() for row in self.catalogue if op in FAMILY_COMMANDS[row['family']]))
 def test_starting_values_match_what_the_engine_reads_back(self):
  require_library()
  primary={0:'emitter',1:'field',2:'text',3:'window'}
  with NativeScene() as scene:
   for row in self.catalogue:
    entry=self.entries.get(row['id'],{});op=primary[row['family']]
    with self.subTest(id=row['id']):
     scene.command({'op':'reset','seed':2030})
     scene.command(entry['examples']['positive'][0]['commands'][-1])
     live=readback(scene.info_complete(),row['family'])
     for path,value in entry.get('startingValues',{}).items():self.assertEqual(live.get(path),value,path)
     for record in self.section['commands'][op]:
      if record['defaultSource']!='engine-readback' or record['field'] in entry.get('startingValues',{}):continue
      self.assertEqual(live.get(record['field']),json.loads(record['default']),record['field'])
 def test_a_readback_is_matched_to_a_finite_choice_field_by_membership(self):
  """A literal union such as "show" | "hide" names no primitive type, so membership in the choices decides; true is not the number 1."""
  declared={'phase':{'types':['"show"','"hide"','undefined'],'choices':['show','hide']},'tier':{'types':['0','1','undefined'],'choices':[0,1]},
   'flag':{'types':['boolean','undefined'],'choices':[False,True]},'count':{'types':['number','undefined'],'choices':[]}}
  self.assertEqual(docs.mapped_readback({'phase':'show','tier':1.0,'flag':True,'count':3,'other':'ignored'},declared),{'phase':'show','tier':1,'flag':True,'count':3})
  self.assertEqual(docs.mapped_readback({'phase':'spin','tier':True,'flag':1,'count':'3'},declared),{})
 def test_a_choice_the_engine_reads_back_for_every_identity_has_an_observed_default(self):
  """A finite-choice parameter that reads back one of its choices, identically in two scenes, for every identity of its family is not listed as having no default."""
  require_library()
  primary={0:'emitter',1:'field',2:'text',3:'window'};stable={}
  with NativeScene() as scene:
   for row in self.catalogue:
    views=[]
    for seed,size in [(2030,None),(4242,(100,30))]:
     scene.command({'op':'reset','seed':seed})
     if size:scene.command({'op':'resize','width':size[0],'height':size[1]})
     scene.command(self.entries[row['id']]['examples']['positive'][0]['commands'][-1])
     views.append(readback(scene.info_complete(),row['family']))
    stable[row['id']]={path:value for path,value in views[0].items() if views[1].get(path)==value}
  def declared(value,choices):return any(value==x and isinstance(value,bool)==isinstance(x,bool) for x in choices)
  observable=[]
  for family,op in primary.items():
   members=[row['id'] for row in self.catalogue if row['family']==family]
   for row in self.fields(op):
    if row['choices'] and all(declared(stable[identity].get(row['field']),row['choices']) for identity in members):observable.append(op+'.'+row['field'])
  self.assertLessEqual({'field.optics','field.paint','text.phase','text.phaseModel'},set(observable),'these read back a declared choice for every identity')
  for name in observable:
   op,field=name.split('.',1)
   with self.subTest(parameter=name):
    record=next(x for x in self.section['commands'][op] if x['field']==field)
    self.assertIsNotNone(record['default'],name+' reads back a declared choice for every identity but is documented as having no default')
 def test_regeneration_reproduces_the_committed_catalogue(self):
  require_library()
  observed=docs.observe_catalogue(self.catalogue,self.inventory,self.guidance)
  observed['domains']={op+'.'+x['field']:x['domainEdges'] for op,table in self.section['commands'].items() for x in table if 'domainEdges' in x}
  # Engine observations are replayed by their own tests; citations are located again in the current native sources.
  observed['defaults']={op+'.'+x['field']:{k:v for k,v in x['defaultEvidence'].items() if k!='cite'} for op,table in self.section['commands'].items() for x in table if 'defaultEvidence' in x}
  observed['probes']={op+'.'+x['field']:{k:v for k,v in x['domainEvidence'].items() if k!='cite'} for op,table in self.section['commands'].items() for x in table if 'domainEvidence' in x}
  self.assertEqual(docs.catalogue_reference(self.catalogue,self.inventory,self.guidance,observed,self.sources()),self.section)
 def sources(self):
  return {'catalogue':digest(ROOT/'catalogue.json'),'commandInventory':digest(CURRENT/'command-inventory.json'),'commandHelp':digest(CURRENT/'command-help.json')}

 def test_pages_are_rendered_from_the_json_and_name_every_component(self):
  """The committed pages are the catalogue section rendered under the committed nullification contract
  (native/docs/NULLIFICATION.md). The renderer documents every catalogue identity; the committed pages document
  every identity the operator did not nullify, and list each nullified one in the ledger instead."""
  decisions=docs.contract_decisions(ROOT/'contract/NULLIFICATION.json');nullified=[x['key'] for x in decisions if x['scope']=='current-identity']
  complete=docs.catalogue_pages(self.section,[]);pages=docs.catalogue_pages(self.section,nullified)
  for rendered in (complete,pages):
   self.assertEqual(set(rendered),{'Catalogue.md','Catalogue-Weather.md','Catalogue-Surface-Fields.md','Catalogue-Text.md','Catalogue-Windows.md'})
  for name,text in pages.items():
   self.assertEqual((CURRENT/name).read_text(),text,name);self.assertIn(name,self.manifest['pages'])
  def documented(rendered,row):
   index=rendered['Catalogue.md'];entry=self.entries[row['id']]
   page=rendered[{0:'Catalogue-Weather.md',1:'Catalogue-Surface-Fields.md',2:'Catalogue-Text.md',3:'Catalogue-Windows.md'}[row['family']]]
   section=page.split('### '+row['id']+'\n',1)[1].split('\n### ',1)[0]
   self.assertIn('| Name | '+row['name']+' |',section);self.assertIn('| Profile | '+str(row['profile'])+' |',section)
   self.assertNotIn('Visual acceptance',section)
   self.assertIn('| Source identity | '+('none recorded' if row['sourceIdentity'] is None else '`'+row['sourceIdentity']+'`')+' |',section)
   self.assertIn('`'+row['id']+'`',index)
   for op in FAMILY_COMMANDS[row['family']]:
    # The entry leads to the table of parameters, defaults and domains of each command that accepts it.
    self.assertIn('[`'+op+'`](#parameters-of-'+op+')',section);self.assertIn('\n## Parameters of '+op+'\n',page)
   for example in entry['examples']['rejected']:self.assertIn(example['diagnostic'],section)
  ledger=(CURRENT/docs.NULLIFICATION_PAGE).read_text() if nullified else None
  for row in self.catalogue:
   with self.subTest(id=row['id']):
    documented(complete,row)
    if row['id'] not in nullified:documented(pages,row);continue
    page=pages[{0:'Catalogue-Weather.md',1:'Catalogue-Surface-Fields.md',2:'Catalogue-Text.md',3:'Catalogue-Windows.md'}[row['family']]]
    self.assertNotIn('\n### '+row['id']+'\n',page);self.assertNotIn('| [`'+row['id']+'`](',pages['Catalogue.md'])
    self.assertNotIn('#'+docs.slug(row['id'])+')',pages['Catalogue.md'])
    self.assertIn('| `'+row['id']+'` | ',ledger,'a nullified identity is listed in the nullification ledger')
  self.assertEqual(docs.NULLIFICATION_PAGE in self.manifest['pages'],bool(decisions),'the manifest lists the ledger while the contract has a decision it records')
 def test_pages_are_in_the_reference_manifest_and_the_guide_links_them(self):
  for page in ['Catalogue.md','Catalogue-Weather.md','Catalogue-Surface-Fields.md','Catalogue-Text.md','Catalogue-Windows.md']:self.assertIn(page,self.manifest['pages'])
  self.assertIn('](Catalogue.md)',(CURRENT/'Components.md').read_text())
  self.assertIn('](Catalogue.md)',(CURRENT/'README.md').read_text())

if __name__=='__main__':unittest.main()
