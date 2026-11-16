#!/usr/bin/env python3
"""Public-command catalogue demonstrations, alone and in an application screen.

Generate cases for the existing WASM gallery, or execute actual native samples:
 python3 native/examples/gallery_cases.py --output /new/gallery --execute
Outputs are commands plus source-scoped frame/snapshot hashes, not art approvals.
"""
from pathlib import Path
import argparse,copy,fnmatch,hashlib,importlib,json,sys,math
ROOT=Path(__file__).resolve().parents[1]

def fixture_generators_left_out():
 """How many fixture generators this tree leaves out: the public tree counts them in PUBLIC-TREE-REPORT.json at its root
 (tools/release/export_public_tree.py), without naming them. A source tree has no such report and tolerates no absence."""
 report=ROOT.parent/'PUBLIC-TREE-REPORT.json'
 return json.loads(report.read_text())['fixtureGenerators']['count'] if report.is_file() else 0

def fixture_study(module):
 """The builder of one fixture generator (a synthetic study module), or a builder of nothing when this tree leaves the
 module out. Any other missing or broken import still fails."""
 try:return getattr(importlib.import_module(module),'build_'+module)
 except ModuleNotFoundError as error:
  if error.name!=module or not fixture_generators_left_out():raise
  return lambda:[]

def numeric_record_matches(actual,expected,tolerance=1e-9):
 """Numerical oracles require complete finite records, never truncated zip matches."""
 return (actual is not None and len(actual)==len(expected)
  and all(type(a) in (int,float) and type(b) in (int,float)
   and math.isfinite(a) and math.isfinite(b) and abs(a-b)<=tolerance
   for a,b in zip(actual,expected)))

def check_character_cells(scene,case,time):
 """Inspect an explicitly rendered frame without changing scene state."""
 allowed={'glyph','foreground','background','id','index','role','state','path'}
 for expected in case.get('expectedCharacterCells',[]):
  if not isinstance(expected,dict) or set(expected)-allowed-{'x','y','timeUs'} or not allowed.intersection(expected):
   raise ValueError(f"Invalid character-cell expectation: {case['id']}")
  for coordinate in ('x','y'):
   if type(expected.get(coordinate)) is not int:raise ValueError('Character-cell coordinates must be integers')
  if 'timeUs' in expected:
   if type(expected['timeUs']) is not int or expected['timeUs'] not in case['sampleTimesUs']:raise ValueError('Character-cell time must identify an authored sample')
   if expected['timeUs']!=time:continue
  actual=scene.inspect_character_cell(expected['x'],expected['y'])
  for field,value in expected.items():
   if field in ('x','y','timeUs'):continue
   required=str if field in ('role','state','path') else int
   if type(value) is not required:raise ValueError(f'Invalid character-cell {field} expectation')
   if field not in actual or type(actual[field]) is not required or actual[field]!=value:
    raise RuntimeError(f"{case['id']}: character cell ({expected['x']},{expected['y']}) {field}: {actual.get(field)!r} != {value!r}")

def action_json_matches(actual,expected):
 if isinstance(expected,dict):return isinstance(actual,dict) and actual.keys()==expected.keys() and all(action_json_matches(actual[k],v) for k,v in expected.items())
 if isinstance(expected,list):return isinstance(actual,list) and len(actual)==len(expected) and all(action_json_matches(a,b) for a,b in zip(actual,expected))
 return (type(actual) is type(expected) or type(actual) in (int,float) and type(expected) in (int,float)) and actual==expected

def action_record_matches(actual,expected):
 if isinstance(expected,dict):return isinstance(actual,dict) and all(k in actual and (action_json_matches(actual[k],v) if k=='payload' else action_record_matches(actual[k],v)) for k,v in expected.items())
 if isinstance(expected,list):return isinstance(actual,list) and len(actual)==len(expected) and all(action_record_matches(a,b) for a,b in zip(actual,expected))
 return type(actual) is type(expected) and actual==expected or type(actual) in (int,float) and type(expected) in (int,float) and actual==expected

def approximate_record_matches(actual,expected,tolerance):
 if isinstance(expected,dict):return isinstance(actual,dict) and all(k in actual and approximate_record_matches(actual[k],v,tolerance) for k,v in expected.items())
 if isinstance(expected,list):return isinstance(actual,list) and len(actual)==len(expected) and all(approximate_record_matches(a,b,tolerance) for a,b in zip(actual,expected))
 if type(expected) not in (int,float) or not math.isfinite(expected):raise ValueError('Invalid approximate action info leaf')
 return type(actual) in (int,float) and math.isfinite(actual) and abs(actual-expected)<=tolerance

def execute_action(scene,action,case_id,_depth=0):
 if 'hostSteps' in action:
  steps=action['hostSteps']
  if not isinstance(steps,list) or not 1<=len(steps)<=32 or _depth>=8 or any(not isinstance(step,dict) for step in steps):raise ValueError('Invalid ordered host steps')
  for step in steps:execute_action(scene,step,case_id,_depth+1)
 expected_error=action.get('expectedError')
 if expected_error is not None and (type(expected_error) is not str or not expected_error):raise ValueError('Nonempty expected error required')
 before=scene.snapshot() if action.get('unchanged') or expected_error else None
 if 'unchangedParticles' in action and type(action['unchangedParticles']) is not bool:raise ValueError('Invalid action particle preservation')
 particles_before=scene.particles() if action.get('unchangedParticles') else None
 targets_before={n['id']:n['targetPosition'] for n in scene.info_complete()['nodes']} if action.get('expectedNodeTargetsChanged') else None
 try:scene.command(action['command'])
 except ValueError as error:
  if not expected_error or expected_error not in str(error):raise
 else:
  if expected_error:raise RuntimeError(f"{case_id}: expected rejection")
 if before is not None and scene.snapshot()!=before:raise RuntimeError(f"{case_id}: action mutation")
 if particles_before is not None and scene.particles()!=particles_before:raise RuntimeError(f"{case_id}: action particle mutation")
 for sample in action.get('expectedParticleSamples',[]):
  if not isinstance(sample,dict) or set(sample)-{'emitterId','count','position','velocity','tolerance'} or type(sample.get('emitterId')) is not int or type(sample.get('count')) is not int or sample['count']<0:raise ValueError('Invalid action particle sample')
  tolerance=sample.get('tolerance',0)
  if type(tolerance) not in (int,float) or not math.isfinite(tolerance) or not 0<=tolerance<=.01:raise ValueError('Invalid action particle tolerance')
  for field in ('position','velocity'):
   if field in sample and (not isinstance(sample[field],list) or len(sample[field])!=3 or any(type(v) not in (int,float) or not math.isfinite(v) for v in sample[field])):raise ValueError('Invalid action particle vector')
  rows=[p for p in scene.particles() if p[1]==sample['emitterId']]
  if len(rows)!=sample['count']:raise RuntimeError(f"{case_id}: action particle count")
  for row in rows:
   for field,start in [('position',3),('velocity',6)]:
    if field in sample and not numeric_record_matches([v/65536 for v in row[start:start+3]],sample[field],tolerance):raise RuntimeError(f"{case_id}: action particle {field}")
 if 'expectedDockWindows' in action:
  expected=action['expectedDockWindows']
  if not isinstance(expected,list) or any(type(v) is not int or not 1<=v<=65535 for v in expected) or len(set(expected))!=len(expected):raise ValueError('Invalid action dock owners')
  before_dock=scene.snapshot();owners=sorted({w[3]&65535 for w in scene.render().words() if w[3]&0xffff0000==0x50000000})
  if owners!=sorted(expected):raise RuntimeError(f"{case_id}: action dock owners {owners}")
  if scene.snapshot()!=before_dock:raise RuntimeError(f"{case_id}: action dock query mutation")
 info=scene.info_complete()
 if targets_before is not None:
  expected=action['expectedNodeTargetsChanged']
  if not isinstance(expected,list) or not expected or any(type(v) is not int for v in expected) or len(set(expected))!=len(expected):raise ValueError('Invalid action node target expectation')
  after={n['id']:n['targetPosition'] for n in info['nodes']}
  if any(id not in after or id not in targets_before or after[id]==targets_before[id] for id in expected):raise RuntimeError(f"{case_id}: action node target unchanged")

 for name,expected in action.get('expectedCollections',{}).items():
  if name not in ('messages','intents','registeredStates') or not isinstance(expected,list):raise ValueError('Invalid expected retained collection')
  actual=info.get(name)
  if not isinstance(actual,list) or len(actual)!=len(expected) or len({e['id'] for e in expected})!=len(expected) or any(not action_record_matches(next((r for r in actual if r['id']==e['id']),None),e) for e in expected):raise RuntimeError(f"{case_id}: action collection {name}")
 for key,value in action.get('expectedPromptState',{}).items():
  if info['prompt'].get(key)!=value:raise RuntimeError(f"{case_id}: action prompt {key}: {info['prompt'].get(key)!r} != {value!r}")
 if 'expectedWindowState' in action:
  expected=action['expectedWindowState'];actual=next((w for w in info['windows'] if w['id']==expected['id']),None)
  if actual is None or any(actual.get(k)!=v for k,v in expected.items()):raise RuntimeError(f"{case_id}: action window")
 if 'expectedInputOwner' in action and info['inputOwner']!=action['expectedInputOwner']:raise RuntimeError(f"{case_id}: action input owner")
 if 'expectedSelectedText' in action and scene.selected_text()!=action['expectedSelectedText']:raise RuntimeError(f"{case_id}: action selected text")
 if 'expectedInfo' in action and not action_record_matches(info,action['expectedInfo']):raise RuntimeError(f"{case_id}: action info")
 if 'expectedApproxInfo' in action:
  tolerance=action.get('approxTolerance',1e-5)
  if type(tolerance) not in (int,float) or not math.isfinite(tolerance) or not 0<=tolerance<=.01:raise ValueError('Invalid approximate action info tolerance')
  if not approximate_record_matches(info,action['expectedApproxInfo'],tolerance):raise RuntimeError(f"{case_id}: action approximate info")
 if 'expectedCharacterCells' in action:
  before_cells=scene.snapshot();scene.render();check_character_cells(scene,{'id':case_id,'expectedCharacterCells':action['expectedCharacterCells'],'sampleTimesUs':[]},None)
  if scene.snapshot()!=before_cells:raise RuntimeError(f"{case_id}: action cell query mutation")

 methods={'flowThickness':'flow_thickness','surfaceTriangles':'surface_triangles','floatHull':'float_hull','surfaceFluid':'surface_fluid'}
 query_before=scene.snapshot() if action.get('expectedQueries') else None
 for query in action.get('expectedQueries',[]):
  if not isinstance(query,dict) or query.get('kind') not in methods or type(query.get('id')) is not int or set(query)-{'kind','id','equals','count','rows'} or sum(key in query for key in ('equals','count','rows'))!=1:raise ValueError('Invalid action query')
  actual=getattr(scene,methods[query['kind']])(query['id'])
  if 'rows' in query:
   expected=query['rows']
   if query['kind']!='surfaceTriangles' or not isinstance(expected,list) or any(not isinstance(row,list) or len(row)!=12 or any(type(v) not in (int,float) or not math.isfinite(v) for v in row) for row in expected):raise ValueError('Invalid action query rows')
   matches=isinstance(actual,list) and len(actual)==len(expected) and all(numeric_record_matches(a,e) for a,e in zip(actual,expected))
  elif 'count' in query:
   if query['kind']!='surfaceTriangles' or type(query['count']) is not int or query['count']<0:raise ValueError('Invalid action query count')
   matches=isinstance(actual,list) and len(actual)==query['count']
  else:
   expected=query['equals']
   if expected is not None and not isinstance(expected,list):raise ValueError('Invalid action query row')
   matches=actual is None if expected is None else numeric_record_matches(actual,expected)
  if not matches:raise RuntimeError(f"{case_id}: action query {query['kind']}")
 if query_before is not None and scene.snapshot()!=query_before:raise RuntimeError(f"{case_id}: action query mutation")


def build_cases():
 catalogue=json.loads((ROOT/'catalogue.json').read_text())
 recipes=json.loads((ROOT/'recipes.json').read_text())
 emitter=next(x for r in recipes for x in r['commands'] if x['op']=='emitter')
 cases=[]
 for entry in catalogue:
  family=entry['contract'];effect=entry['id']
  base=[{'op':'resize','width':100,'height':40}]
  if family=='ParticleEmitter':
   base += [{'op':'camera','position':[24,16,36],'yaw':-33,'pitch':-12,'fov':67}]
   target=copy.deepcopy(emitter);target.update(id=1,effect=effect,count=40,runningTimeMs=2000,lifetimeMinMs=3000,lifetimeMaxMs=4000)
  elif family=='SurfaceField':
   target={'op':'field','effect':effect,'x':50,'y':20,'lifeMs':7000,'strength':.68,'width':1.7,'speed':9}
  elif family=='TextTransition':
   target={'op':'text','id':1,'text':'Nocturne / source and motion','x':8,'y':12,'width':80,'effect':effect,'durationMs':1600}
   if entry.get('profile')==0:
    target.update(phaseModel='source-paint',material=15,seed=2030,alphabet=' ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+-*/!?')
    base.append({'op':'material','id':15,'space':'oklch','scope':'characters','channels':{'l':.83,'c':.1,'h':{'initial':0,'rate':12,'min':0,'max':360,'boundary':'loop'}},'hueStep':13,'alpha':1})
  elif family=='WindowTransition':
   target={'op':'window','id':1,'title':'Effect study','text':'Retained source\nIndependent transition\nNative timing','position':[0,4,0],'width':32,'height':14,'effect':effect}
  else:raise ValueError(f'Unmapped catalogue family: {family}')
  for mode in ('isolated','application'):
   commands=copy.deepcopy(base)
   if mode=='application':
    commands += [
     {'op':'material','id':2,'gradient':[[.78,.12,210],[.7,.15,310]],'alpha':.8},
     {'op':'window','id':90,'title':'Application / activity','text':'A complete screen composition\nBackdrop, content, prompt and activity\nEach layer has its own lifetime','position':[0,-4,-4],'width':40,'height':16,'material':2,'effect':'window-transition/ribbon-genie'},
     {'op':'text','id':90,'text':'NOCTURNE / operation console','x':4,'y':3,'width':90,'effect':'text/ink-dissolve','durationMs':700},
     {'op':'draft','text':'Type a command here','emitWeather':False},
     {'op':'indicator','id':90,'x':4,'y':34,'sequence':'◐◓◑◒','stepMs':150},
    ]
   commands.append(copy.deepcopy(target))
   cases.append({'id':f"study-{effect.replace('/','-')}-{mode}",'name':f"{entry['name']} / {mode}",'subtitle':'Public native commands; independent scene time and retained source.','mode':mode,'demonstrates':{'effect':effect,'contract':family},'commands':commands,'sampleTimesUs':[0,500000,2000000]})
 from world_shell_studies import build_world_shell_studies
 cases.extend(build_world_shell_studies())
 from world_nova_optics_studies import build_world_nova_optics_studies
 cases.extend(build_world_nova_optics_studies())
 from corona_studies import build_corona_studies
 cases.extend(build_corona_studies())
 from observatory_studies import build_observatory_studies
 cases.extend(build_observatory_studies())
 from rc2_window_studies import build_rc2_window_studies
 cases.extend(build_rc2_window_studies())
 from studio_nova_studies import build_studio_nova_studies
 cases.extend(build_studio_nova_studies())
 from world_shell_source_studies import build_world_shell_source_studies
 cases.extend(build_world_shell_source_studies())
 from thermal_studies import build_thermal_studies
 cases.extend(build_thermal_studies())
 from atelier_studies import build_atelier_studies
 cases.extend(build_atelier_studies())
 from kinetic_studies import build_kinetic_studies
 cases.extend(build_kinetic_studies())
 from original_gallery_routes import apply_original_gallery_routes
 from original_weather_routes import apply_original_weather_routes
 from original_world_weather_routes import apply_original_world_weather_routes
 from source_model_studies import build_source_model_studies
 from first_prompt_studies import build_first_prompt_studies
 from original_waiting_studies import build_original_waiting_studies
 from pearl_data_studies import build_pearl_data_studies
 from pearl_observatory_studies import build_pearl_observatory_studies
 from original_composition_studies import build_original_composition_studies
 from source_modal_studies import build_source_modal_studies
 from tdf_gallery_studies import build_tdf_gallery_studies
 from original_scenic_routes import build_original_scenic_routes
 from product_copy import public_recipe
 return [public_recipe(case) for case in apply_original_world_weather_routes(apply_original_weather_routes(apply_original_gallery_routes(cases,catalogue),catalogue),catalogue)+build_original_waiting_studies()+build_original_composition_studies()+build_tdf_gallery_studies()+build_first_prompt_studies()+build_source_model_studies()+build_pearl_data_studies()+build_pearl_observatory_studies()+build_source_modal_studies()+build_original_scenic_routes()]

def execute(cases):
 sys.path.insert(0,str(ROOT/'bindings/python'))
 from nocturne_native import NativeScene
 from source_model_studies import decode_model_records,verify_model_resource
 result=[]
 for case in cases:
  tolerance=case.get('expectedNumericTolerance',0)
  if not isinstance(tolerance,(int,float)) or not math.isfinite(tolerance) or not 0<=tolerance<=1e-6:raise ValueError('Invalid explicit expectation tolerance')
  def equal(actual,expected):
   if tolerance and type(actual) in (int,float) and type(expected) in (int,float):
    return math.isfinite(actual) and math.isclose(actual,expected,rel_tol=0,abs_tol=tolerance)
   if isinstance(actual,bool)!=isinstance(expected,bool):return False
   if isinstance(expected,dict):return isinstance(actual,dict) and actual.keys()==expected.keys() and all(equal(actual[key],value) for key,value in expected.items())
   if isinstance(expected,list):return isinstance(actual,list) and len(actual)==len(expected) and all(equal(a,b) for a,b in zip(actual,expected))
   return actual==expected
  records=decode_model_records(case)
  with NativeScene() as scene:
   if records is not None:scene.set_model_records(records)
   for command in case['commands']:
    try:scene.command(command)
    except ValueError as error:raise ValueError(f"{case['id']}: {command}: {error}") from error
   verify_model_resource(scene,case,records)
   start=scene.snapshot();samples=[]
   identityBefore=[scene.text_run_clusters(check['kind'],check['id']) for check in case.get('textIdentityChecks',[])]
   actions=sorted(case.get('actions',[]),key=lambda a:a['timeUs']);nextAction=0
   for time in case['sampleTimesUs']:
    while nextAction<len(actions) and actions[nextAction]['timeUs']<=time:
     action=actions[nextAction];scene.advance_to(action['timeUs']);scene.render();execute_action(scene,action,case['id']);nextAction+=1
    scene.advance_to(time);before=scene.snapshot();frame=scene.render()
    if "promptVisualExpected" in case and ([r[:5]+r[8:] for r in scene.prompt_visual_layout()]!=case["promptVisualExpected"] or scene.text_run_source(0,0)!=case["promptSourceExpected"]):raise RuntimeError(f"Independent prompt visual: {case['id']}")
    if "promptLayoutExpected" in case and ([r[:5] for r in scene.prompt_layout()]!=case["promptLayoutExpected"] or scene.text_run_source(0,0)!=case["promptSourceExpected"]):raise RuntimeError(f"Independent prompt layout: {case['id']}")
    check_character_cells(scene,case,time)
    for check in case.get('cellArtSampleChecks',[]):
     if check['timeUs']!=time:continue
     art=next((item for item in scene.info().get('cellArt',[]) if item['id']==check['id']),None)
     if check.get('present',True) is False:
      if art is not None:raise RuntimeError(f"Removed cell-art retained: {case['id']}")
      continue
     if art is None or any(art.get(field)!=check[field] for field in ('x','y','alpha')):raise RuntimeError(f"Retained cell-art animation: {case['id']}")
     for field in ('width','height','cells'):
      if field in check and art.get(field)!=check[field]:raise RuntimeError(f"Retained cell-art source {field}: {case['id']}")
    for check in case.get('waterSampleChecks',[]):
     expected=next(item for item in check['expected'] if item['timeUs']==time);water=next(item for item in scene.info()['surfaceWater'] if item['surfaceId']==check['surfaceId'])
     if abs(water['receivedVolume']-expected['received'])>1e-5 or abs(water['retainedVolume']-expected['retained'])>1e-5:raise RuntimeError(f"Authored water response: {case['id']}")
     balance=water['receivedVolume']+water['importedVolume']-water['retainedVolume']-water['evaporatedVolume']-water['exportedVolume']-water['transferredVolume']
     if abs(balance)>1e-5:raise RuntimeError(f"Authored water conservation: {case['id']}")
     for cell,wetness in zip(water['cells'],expected['wetness']):
      if abs(cell['wetness']-wetness)>1e-5:raise RuntimeError(f"Local water wetness: {case['id']}")
     if len(water['cells'])!=len(expected['wetness']):raise RuntimeError(f"Local water cell ownership: {case['id']}")
    for check in case.get('fluidSampleChecks',[]):
     expected=next(item for item in check['expected'] if item['timeUs']==time);row=scene.surface_fluid(check['surfaceId']);body=scene.float_body(check['bodyId'])
     for label,actual in [('record',row),('body',body)]:
      if actual is None or len(actual)!=len(expected[label]) or any(abs(a-b)>1e-5 for a,b in zip(actual,expected[label])):raise RuntimeError(f"Fluid {label} oracle: {case['id']}")
     metadata=next(item for item in scene.info()['surfaceFluids'] if item['surfaceId']==check['surfaceId'])
     if metadata['active']!=expected['active']:raise RuntimeError(f"Fluid lifecycle oracle: {case['id']}")
     for k in range(3):
      if abs(row[0]*row[1+k]-row[7+k]-row[10+k])>1e-5:raise RuntimeError(f"Fluid momentum balance: {case['id']}")
    for check in case.get('angularFluidChecks',[]):
     expected=next(item for item in check['expected'] if item['timeUs']==time)
     row=scene.surface_fluid_angular(check['surfaceId']);body=scene.float_hull(check['bodyId'])
     if row is None or body is None or len(row)!=12:raise RuntimeError(f"Angular record ownership: {case['id']}")
     if not numeric_record_matches(row,expected['record']) or not numeric_record_matches(body[4:7],expected['bodyOmega']):raise RuntimeError(f"Independent angular exchange: {case['id']}")
     if abs(2*body[5]+row[0]*row[2]-2)>1e-9 or abs(body[5]**2+.5*row[0]*row[2]**2+row[10]-1)>1e-9:raise RuntimeError(f"Angular momentum/energy ledger: {case['id']}")
    for check in case.get('surfacePoseChecks',[]):
     expected=next(item for item in check['expected'] if item['timeUs']==time)
     triangles=scene.surface_triangles(check['surfaceId'])
     if len(triangles)!=1 or not numeric_record_matches(triangles[0][1:10],expected['vertices']):raise RuntimeError(f"Independent pivot/world rotation: {case['id']}")
    for check in case.get('hullSampleChecks',[]):
     expected=next(item for item in check['expected'] if item['timeUs']==time)
     for label,row in [('pose',scene.float_hull(check['id'])),('body',scene.float_body(check['id']))]:
      if row is None or len(row)!=len(expected[label]) or any(abs(a-b)>1e-5 for a,b in zip(row,expected[label])):raise RuntimeError(f"Hull {label} oracle: {case['id']}")
    for expected in case.get('refinedFieldChecks',[]):
     if expected['timeUs']!=time:continue
     rows=scene.surface_triangles(1);area=0;energy=0
     for row in rows:
      a,b,c=[row[k:k+3] for k in [1,4,7]];u=[b[k]-a[k] for k in range(3)];v=[c[k]-a[k] for k in range(3)];cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];area+=math.sqrt(sum(x*x for x in cross))/2;energy+=scene.thermal_sample(int(row[0]))[1]
     if len(rows)!=expected['triangleCount'] or abs(area-expected['totalArea'])>1e-8 or abs(energy-expected['totalThermalEnergy'])>1e-5:raise RuntimeError(f"Independent refined field geometry/energy: {case['id']}")
    for expected in case.get('areaGeometryChecks',[]):
     if not numeric_record_matches(scene.area_geometry(expected['id']),expected['row']):raise RuntimeError(f"Independent area geometry: {case['id']}")
    for expected in case.get('areaMessageChecks',[]):
     if expected['timeUs']!=time:continue
     message=next((m for m in scene.info()['messages'] if m['id']==expected['id']),None)
     if message is None or any(message[field]!=expected[field] for field in ['state','startUs','text']):raise RuntimeError(f"Independent area message epoch/source: {case['id']}")
    for expected in case.get('colorFieldChecks',[]):
     if expected['timeUs']!=time:continue
     row=scene.field_sample(expected['id'],expected['x'],expected['y'])
     if expected.get('present') is False:
      if row is not None:raise RuntimeError(f"Removed color field: {case['id']}")
      continue
     if row is None or abs(row[0]-expected['intensity'])>2e-6 or not numeric_record_matches(row[2:],expected['center']):raise RuntimeError(f"Independent color field: {case['id']}")
     if 'color' in expected:
      tolerance=expected.get('colorTolerance',0)
      if not isinstance(tolerance,int) or not 0<=tolerance<=2 or any(abs(((int(row[1])>>shift)&255)-((expected['color']>>shift)&255))>tolerance for shift in [0,8,16]):raise RuntimeError(f"Independent color field color: {case['id']}")
    for expected in case.get('aggregateChecks',[]):
     if expected['timeUs']!=time:continue
     info=scene.info()
     if info['aggregateReemittedCount']!=expected['reemittedCount'] or sum(r['count'] for r in info['aggregateMaterials'])!=expected['retainedCount'] or info['particles']['born']!=expected['births']:raise RuntimeError(f"Independent aggregate count: {case['id']}")
    for expected in case.get('materialHeatChecks',[]):
     if expected['timeUs']!=time:continue
     ledger=scene.info().get('materialThermal')
     if ledger is None:raise RuntimeError(f"Missing material heat ledger: {case['id']}")
     for field in ['initialEnergy','liveEnergy','importedEnergy','transferredEnergy','exportedEnergy']:
      if abs(ledger[field]-expected[field])>1e-5:raise RuntimeError(f"Independent material heat ledger: {case['id']} / {field}")
     if abs(ledger['initialEnergy']+ledger['importedEnergy']-ledger['liveEnergy']-ledger['transferredEnergy']-ledger['exportedEnergy'])>1e-5:raise RuntimeError(f"Conserved material heat ledger: {case['id']}")
     for collection,label in [('particles','particleCount'),('deposits','depositCount'),('aggregates','aggregateCount')]:
      if len(ledger[collection])!=expected[label]:raise RuntimeError(f"Owned material heat ledger: {case['id']} / {collection}")
    for check in case.get('thermalSampleChecks',[]):
     expected=next(item for item in check['expected'] if item['timeUs']==time);row=scene.thermal_sample(check['triangleIndex'])
     if row is None or abs(row[0]-expected['temperature'])>1e-5:raise RuntimeError(f"Thermal response oracle: {case['id']}")
     if abs(row[1]-(row[2]+row[3]+row[4]+row[5]-row[6]))>1e-5:raise RuntimeError(f"Thermal energy conservation: {case['id']}")
     if 'evaporatedEnergy' in expected:
      cell=next(item for item in scene.info()['surfaceThermal']['cells'] if item['triangleIndex']==check['triangleIndex'])
      if abs(cell['evaporatedEnergy']-expected['evaporatedEnergy'])>1e-5:raise RuntimeError(f"Thermal evaporation energy oracle: {case['id']}")
     if row[8]!=expected['power'] or row[9]!=expected['ambientTemperature']:raise RuntimeError(f"Thermal settings: {case['id']}")
    for check in case.get('flowThicknessChecks',[]):
     settings=check
     for change in check.get('settingsTimeline',[]):
      if change['timeUs']<=time:settings=change
     values=scene.flow_thickness(check['surfaceId']);geometry=scene.surface_triangles(check['surfaceId'])
     if values is None or abs(values[1]-values[0]/(settings['width']*settings['speed']))>1e-10:raise RuntimeError(f"Flow depth oracle: {case['id']}")
     if geometry and 'direction' in check:
      projections=[sum(row[offset+k]*check['direction'][k] for k in range(3)) for row in geometry for offset in (1,4,7)]
      if abs(max(projections)-min(projections)-values[1])>1e-10:raise RuntimeError(f"Sampled geometry thickness: {case['id']}")
     if (len(geometry)>0)!=(values[1]>0):raise RuntimeError(f"Flow geometry lifecycle: {case['id']}")
     if values[3:5]!=[settings['width'],settings['speed']]:raise RuntimeError(f"Flow dimensions: {case['id']}")

    if scene.snapshot()!=before:raise RuntimeError(f"Render mutation: {case['id']}")
    samples.append({'timeUs':time,'frameSha256':hashlib.sha256(frame.bytes).hexdigest(),'snapshotSha256':hashlib.sha256(before).hexdigest()})
   final=scene.snapshot()
   for check,old in zip(case.get('textIdentityChecks',[]),identityBefore):
    rows=scene.text_run_clusters(check['kind'],check['id'])
    if len(rows)!=check['clusters'] or scene.text_run_source(check['kind'],check['id'])!=check['source']:raise RuntimeError(f"Cluster source mapping: {case['id']}")
    if rows[0][0]!=old[0][0] or rows[-1][0]!=old[-1][0] or rows[0][3]!=old[0][3]:raise RuntimeError(f"Cluster persistence: {case['id']}")
    if rows[2][0] in {row[0] for row in old}:raise RuntimeError(f"Inserted cluster reused identity: {case['id']}")
    if scene.snapshot()!=final:raise RuntimeError('Cluster query mutated source')

   if case.get('foamTransportChecks'):
    check=case['foamTransportChecks'];rows=scene.surface_foam_transport(check['surfaceId'])
    for row in rows:
     if abs(row[2]+row[5]-row[1]-row[3]-row[4]-row[6])>1e-8*(1+row[2]+row[5]+row[6]):raise RuntimeError(f"Foam cell balance: {case['id']}")
    if abs(sum(row[5]-row[6] for row in rows))>1e-8*(1+sum(row[5]+row[6] for row in rows)):raise RuntimeError(f"Foam transport conservation: {case['id']}")
    transferred=sum(row[5] for row in rows)
    if (transferred>0)!=check['mustTransfer']:raise RuntimeError(f"Foam transport motion: {case['id']}")
    if scene.snapshot()!=final:raise RuntimeError('Foam query mutated source')
   if case.get('ledgerChecks'):
    from ledger_checks import check_ledgers
    check_ledgers(scene.info(),case['ledgerChecks'])
    if scene.snapshot()!=final:raise RuntimeError('Ledger query mutated source')
   if 'expectedPrompt' in case and scene.info()['prompt']['text']!=case['expectedPrompt']:raise RuntimeError(f"Input source mismatch: {case['id']}")
   if 'expectedValuePaths' in case:
    if sorted(scene.info()['values'])!=case['expectedValuePaths']:raise RuntimeError(f"Value lifetime mismatch: {case['id']}")
   if case.get('expectedCounts'):
    info=scene.info()
    for field,count in case['expectedCounts'].items():
     if len(info[field])!=count:raise RuntimeError(f"Retained consumer lifetime mismatch: {case['id']}")
   if case.get('expectedIntentIds'):
    if [i['id'] for i in scene.info()['intents']]!=case['expectedIntentIds']:raise RuntimeError(f"Intention retention mismatch: {case['id']}")
   if case.get('expectedColors'):
    frame=scene.render();words=frame.words()
    for expected in case['expectedColors']:
     if words[expected['y']*frame.width+expected['x']][1]!=expected['foreground']:raise RuntimeError(f"Bound color mismatch: {case['id']}")
   if case.get('expectedValues'):
    values=scene.info()['values']
    for path,value in case['expectedValues'].items():
     if path not in values or not equal(values[path],value):raise RuntimeError(f"Bound value mismatch: {case['id']}")
   if case.get('expectedCamera'):
    camera=scene.info()['camera']
    for field,value in case['expectedCamera'].items():
     if camera.get(field)!=value:raise RuntimeError(f"Bound camera mismatch: {case['id']}")
   def subset(actual,expected):
    return isinstance(actual,dict) and all(key in actual and (subset(actual[key],value) if isinstance(value,dict) else equal(actual[key],value)) for key,value in expected.items())
   for collection in ('Widgets','Windows','Areas'):
    if case.get('expected'+collection):
     entries=scene.info()[collection.lower()]
     for expected in case['expected'+collection]:
      if not any(subset(entry,expected) for entry in entries):raise RuntimeError(f"Retained {collection.lower()} update mismatch: {case['id']}")
     if scene.snapshot()!=final:raise RuntimeError('Component metadata query mutated source')
   if case.get('expectedOwners'):
    ownerWords=scene.render().words()
    for expected in case['expectedOwners']:
     if sum(cell[3]==expected['semanticId'] for cell in ownerWords)<expected['minCells']:raise RuntimeError(f"Missing rendered component owner: {case['id']}")
   if case.get('expectedCells'):
    checkedFrame=scene.render();words=checkedFrame.words()
    for expected in case['expectedCells']:
     cell=words[expected['y']*checkedFrame.width+expected['x']]
     if cell[0]!=expected['glyph'] or cell[3]!=expected['semanticId']:raise RuntimeError(f"Interaction cell mismatch: {case['id']}")
   scene.restore(start)
   for action in actions:
    if action['timeUs']<=case['sampleTimesUs'][-1]:scene.advance_to(action['timeUs']);scene.render();execute_action(scene,action,case['id'])
   scene.advance_to(case['sampleTimesUs'][-1])
   if scene.snapshot()!=final:raise RuntimeError(f"Replay mismatch: {case['id']}")
   result.append({'id':case['id'],'samples':samples,'renderPure':True,'partitionReplay':True,'ledgerChecks':case.get('ledgerChecks',[])})
 return result

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--execute',action='store_true');parser.add_argument('--feature',action='append',help='Feature/effect glob; repeat to select several studies');args=parser.parse_args()
 cases=build_cases()
 if args.feature:cases=[c for c in cases if any(fnmatch.fnmatch(c['demonstrates'].get('feature',c['demonstrates'].get('effect','')),pattern) for pattern in args.feature)]
 if not cases:parser.error('No studies match the requested feature')
 args.output.mkdir(parents=True,exist_ok=False)
 (args.output/'cases.json').write_text(json.dumps(cases,indent=2,ensure_ascii=False)+'\n')
 if args.execute:
  result=execute(cases)
  (args.output/'RESULTS.json').write_text(json.dumps({'scope':'Catalogue and screen-mode demonstrations; complete option coverage and artistic acceptance remain separate.','librarySha256':hashlib.sha256((ROOT/'dist'/('libnocturne_native.dylib' if sys.platform=='darwin' else 'libnocturne_native.so')).read_bytes()).hexdigest(),'cases':result},indent=2)+'\n')
 print(f'{len(cases)} cases written to {args.output}')
if __name__=='__main__':main()
