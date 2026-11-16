"""Retained paint source, independent cell oracle, replay and rejection contracts."""
from pathlib import Path
import struct,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
RULE={'id':'invert','selector':{'rect':{'x':2,'y':2,'width':4,'height':1}},'compositeSpace':'srgb','foregroundEffects':[{'type':'invert'}]}
class CharacterRules(unittest.TestCase):
 def test_region_replacement_keeps_overlap_order_and_reused_slot_order(self):
  with NativeScene(42) as s:
   s.command({'op':'resize','width':4,'height':2})
   for identity,path in [('first','/first'),('second','/second')]:
    s.command({'op':'character-region','region':{'id':identity,'path':path,'cells':[0],'indices':[9]}})
   s.render();self.assertEqual(s.inspect_character_cell(0,0)['path'],'/second')
   s.command({'op':'character-region','region':{'id':'first','path':'/replacement','cells':[0],'indices':[3]}})
   s.render();self.assertEqual(s.inspect_character_cell(0,0)['path'],'/second')
   s.command({'op':'remove-character-region','id':'first'})
   s.command({'op':'character-region','region':{'id':'reused','path':'/reused','cells':[0],'indices':[4]}})
   saved=s.snapshot();s.render();self.assertEqual(s.inspect_character_cell(0,0)['path'],'/second')
   s.command({'op':'remove-character-region','id':'second'});s.render()
   cell=s.inspect_character_cell(0,0);self.assertEqual((cell['path'],cell['index']),('/reused',4))
   s.restore(saved);s.render();self.assertEqual(s.inspect_character_cell(0,0)['path'],'/second')
 def test_region_cell_list_precedence_empty_lists_and_duplicate_positions(self):
  with NativeScene(42) as s:
   s.command({'op':'resize','width':4,'height':2})
   region={'id':'shape','path':'/shape','rect':{'x':0,'y':0,'width':4,'height':2},'cells':[],'indices':[]}
   s.command({'op':'character-region','region':region});s.render()
   self.assertNotEqual(s.inspect_character_cell(0,0)['path'],'/shape')
   s.command({'op':'character-region','region':{**region,'cells':[0,4294967295,0],'indices':[3,7,9]}})
   saved=s.snapshot();s.render();cell=s.inspect_character_cell(0,0)
   self.assertEqual((cell['path'],cell['index']),('/shape',9))
   self.assertNotEqual(s.inspect_character_cell(1,0)['path'],'/shape');self.assertEqual(s.snapshot(),saved)
 def test_scheduled_region_replacement_and_teardown_have_independent_frames(self):
  with NativeScene(42) as s,NativeScene(42) as oracle:
   for scene in [s,oracle]:scene.command({'op':'resize','width':8,'height':3})
   region={'id':'timed','path':'/app/timed','state':'selected','cells':[0],'indices':[7]}
   rule={'id':'timed','selector':{'path':'/app/timed','indices':[7]},'states':{'selected':{'foregroundEffects':[{'type':'invert'}]}}}
   for identity,time,command in [
    (1,500000,{'op':'batch','commands':[{'op':'character-region','region':region},{'op':'character-rule','rule':rule}]}),
    (2,1000000,{'op':'character-region','region':{**region,'cells':[1]}}),
    (3,1500000,{'op':'batch','commands':[{'op':'remove-character-rule','id':'timed'},{'op':'remove-character-region','id':'timed'}]})]:
    s.command({'op':'schedule','id':identity,'atUs':time,'command':command})
   start=s.snapshot();samples=[]
   for time in [0,499999,500000,999999,1000000,1499999,1500000,2000000]:
    s.advance_to(time);oracle.advance_to(time);expected=bytearray(oracle.render().bytes)
    if 500000<=time<1500000:
     offset=(0 if time<1000000 else 1)*16+4
     struct.pack_into('<I',expected,offset,struct.unpack_from('<I',expected,offset)[0]^0xffffff)
    source=s.snapshot();self.assertEqual(s.render().bytes,bytes(expected))
    if 500000<=time<1500000:
     cell=s.inspect_character_cell(0 if time<1000000 else 1,0)
     self.assertEqual((cell['path'],cell['state'],cell['index']),('/app/timed','selected',7))
    self.assertEqual(s.snapshot(),source);samples.append((time,source,bytes(expected)))
   self.assertEqual(s.info()['characterRules'],[]);self.assertEqual(s.info()['characterRegions'],[])
   s.restore(start)
   for time,source,expected in samples:
    s.advance_to(time);self.assertEqual(s.snapshot(),source);self.assertEqual(s.render().bytes,expected)
   final=s.snapshot();s.restore(start);s.advance_to(2000000);self.assertEqual(s.snapshot(),final)
 def test_equal_priority_unicode_ids_follow_historical_utf16_order(self):
  with NativeScene(42) as s:
   s.command({'op':'resize','width':4,'height':2})
   s.command({'op':'material','id':7,'space':'rgb','channels':{'r':1,'g':0,'b':0},'alpha':1})
   s.command({'op':'character-rule','rule':{'id':'\ue000','foregroundEffects':[{'type':'invert'}]}})
   s.command({'op':'character-rule','rule':{'id':'\U00010000','foreground':7,'compositeSpace':'srgb','protectLocalInk':False}})
   saved=s.snapshot();self.assertTrue(all(cell[1]==0x00ffff for cell in s.render().words()))
   self.assertEqual(s.snapshot(),saved);s.restore(saved)
   self.assertTrue(all(cell[1]==0x00ffff for cell in s.render().words()))
 def test_missing_material_suppresses_whole_patch_and_batch_creation_is_atomic(self):
  with NativeScene(42) as s:
   s.command({'op':'resize','width':4,'height':2})
   s.command({'op':'character-region','region':{'id':'selected','path':'/selected','state':'selected','cells':[0]}})
   baseline=s.render().bytes
   rule={'id':'deferred','foreground':7,'background':8,'foregroundEffects':[{'type':'invert'}],
    'compositeSpace':'srgb','protectLocalInk':False,'states':{'selected':{'enabled':False}}}
   s.command({'op':'character-rule','rule':rule})
   s.command({'op':'material','id':7,'space':'rgb','channels':{'r':1,'g':0,'b':0}})
   dormant=s.snapshot();self.assertEqual(s.render().bytes,baseline)
   material={'op':'material','id':8,'space':'rgb','channels':{'r':0,'g':0,'b':1}}
   with self.assertRaises(ValueError):s.command({'op':'batch','commands':[material,{'op':'character-rule','rule':{'id':''}}]})
   self.assertEqual(s.snapshot(),dormant);self.assertEqual(s.render().bytes,baseline)
   s.command(material);live=s.snapshot();frame=s.render().bytes
   self.assertEqual(frame[:16],baseline[:16])
   for offset in range(16,len(frame),16):
    self.assertEqual(struct.unpack_from('<II',frame,offset+4),(0x00ffff,0x0000ff))
    self.assertEqual(frame[offset:offset+4],baseline[offset:offset+4])
    self.assertEqual(frame[offset+12:offset+16],baseline[offset+12:offset+16])
   self.assertEqual(s.snapshot(),live);s.restore(dormant);self.assertEqual(s.render().bytes,baseline)
 def test_unavailable_material_reference_is_retained_dormant_until_creation(self):
  with NativeScene(42) as s:
   s.command({'op':'resize','width':4,'height':2})
   baseline=s.render().bytes
   rule={'id':'late-material','foreground':7,'protectLocalInk':False,'compositeSpace':'srgb'}
   s.command({'op':'character-rule','rule':rule});saved=s.snapshot()
   self.assertEqual(s.render().bytes,baseline)
   s.restore(saved);self.assertEqual(s.snapshot(),saved)
   self.assertEqual(s.info()['characterRules'],[rule]);self.assertEqual(s.render().bytes,baseline)
   s.command({'op':'material','id':7,'space':'rgb','channels':{'r':1,'g':0,'b':0},'alpha':1})
   live=s.snapshot();frame=s.render()
   self.assertTrue(all(cell[1]==0xff0000 for cell in frame.words()))
   self.assertEqual(s.snapshot(),live)
   s.restore(saved);self.assertEqual(s.render().bytes,baseline)
   self.assertEqual(s.info()['characterRules'],[rule])
 def test_duplicate_fields_and_nul_identity_reject_atomically(self):
  with NativeScene(42) as s:
   s.command({'op':'character-rule','rule':RULE});before=s.snapshot()
   malformed=[
    b'{"op":"character-rule","rule":{"id":"first","id":"second"}}',
    b'{"op":"character-rule","rule":{"id":"x","states":{"active":{},"active":{}}}}',
    b'{"op":"character-rule","rule":{"id":"x\\u0000hidden"}}',
    b'{"op":"character-region","region":{"id":"x","path":"/app/x\\u0000hidden"}}',
    b'{"op":"character-region","region":{"id":"x","path":"/app/x","state":"active\\u0000hidden"}}',
   ]
   for command in malformed:
    with self.subTest(command=command):
     with self.assertRaises(ValueError):s.command_raw(command)
     self.assertEqual(before,s.snapshot());self.assertEqual(s.info()['characterRules'],[RULE])
 def test_material_tracks_sample_region_indices_and_execution_clock(self):
  with NativeScene(42) as s:
   s.command({'op':'material','id':7,'space':'rgb','scope':'characters','channels':{'r':{'initial':0,'rate':1,'step':.1,'min':0,'max':1},'g':0,'b':0},'alpha':1})
   s.command({'op':'character-region','region':{'id':'indices','path':'/app/indices','cells':[0,1],'indices':[1,3]}})
   s.command({'op':'character-rule','rule':{'id':'sampled','selector':{'path':'/app/indices'},'foreground':7}})
   for time,reds in [(0,[26,77]),(500000,[153,204])]:
    s.advance_to(time);before=s.snapshot();frame=s.render().bytes
    for position,red in enumerate(reds):self.assertEqual(struct.unpack_from('<I',frame,position*16+4)[0],red<<16)
    self.assertEqual(before,s.snapshot())
   s.command({'op':'define','path':'/red','value':.2,'binding':{'family':'material','id':7,'field':'channels.r.initial'}})
   frame=s.render().bytes
   for position,red in enumerate([204,255]):self.assertEqual(struct.unpack_from('<I',frame,position*16+4)[0],red<<16)
 def test_scheduled_batch_installs_regions_and_rules_with_exact_replay(self):
  with NativeScene(42) as s,NativeScene(42) as oracle:
   region={'id':'timed','path':'/app/timed','cells':[0],'indices':[7]}
   rule={'id':'timed','selector':{'path':'/app/timed','indices':[7]},'foregroundEffects':[{'type':'invert'}]}
   s.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'batch','commands':[
    {'op':'character-region','region':region},{'op':'character-rule','rule':rule}]}})
   start=s.snapshot();s.advance_to(500000);oracle.advance_to(500000)
   expected=bytearray(oracle.render().bytes);struct.pack_into('<I',expected,4,struct.unpack_from('<I',expected,4)[0]^0xffffff)
   self.assertEqual(s.render().bytes,bytes(expected));self.assertEqual(s.info()['characterRegions'],[region])
   finish=s.snapshot();s.restore(start);s.advance_to(500000)
   self.assertEqual(finish,s.snapshot());self.assertEqual(s.render().bytes,bytes(expected))
 def test_rectangular_regions_reclip_after_resize_and_later_slots_override(self):
  with NativeScene(42) as s,NativeScene(42) as oracle:
   s.command({'op':'character-region','region':{'id':'under','path':'/app/under','rect':{'x':-1,'y':1,'width':5,'height':1}}})
   s.command({'op':'character-region','region':{'id':'over','path':'/app/over','rect':{'x':1,'y':1,'width':2,'height':1}}})
   s.command({'op':'character-rule','rule':{'id':'paint','selector':{'path':'/app/under','indices':[0,3]},'foregroundEffects':[{'type':'invert'}]}})
   for width,height in [(16,8),(3,8),(32,12)]:
    for scene in [s,oracle]:scene.command({'op':'resize','width':width,'height':height})
    baseline=oracle.render();expected=bytearray(baseline.bytes)
    for x in [0,3]:
     if x<width:
      offset=(width+x)*16+4;struct.pack_into('<I',expected,offset,struct.unpack_from('<I',expected,offset)[0]^0xffffff)
    before=s.snapshot();self.assertEqual(s.render().bytes,bytes(expected));self.assertEqual(before,s.snapshot())
 def test_explicit_region_indices_state_patch_and_restore(self):
  with NativeScene(42) as s:
   baseline=s.render();expected=bytearray(baseline.bytes)
   cells=[2*baseline.width+2,2*baseline.width+3]
   region={'id':'screen-fragment','path':'/app/fragment','role':'user-text','state':'selected','cells':cells,'indices':[7,9]}
   rule={'id':'fragment','selector':{'path':'/app/fragment','indices':[9]},'states':{'selected':{'foregroundEffects':[{'type':'invert'}]}}}
   s.command({'op':'character-region','region':region});s.command({'op':'character-rule','rule':rule})
   offset=cells[1]*16+4;struct.pack_into('<I',expected,offset,struct.unpack_from('<I',expected,offset)[0]^0xffffff)
   saved=s.snapshot();self.assertEqual(s.info()['characterRegions'],[region]);self.assertEqual(s.render().bytes,bytes(expected))
   self.assertEqual(saved,s.snapshot());s.command({'op':'remove-character-region','id':region['id']})
   self.assertEqual(s.render().bytes,baseline.bytes);s.restore(saved);self.assertEqual(s.render().bytes,bytes(expected))
   with self.assertRaises(ValueError):s.command({'op':'character-region','region':{**region,'indices':[7]}})
   self.assertEqual(saved,s.snapshot())
 def test_owned_source_metadata_independent_frame_oracle_and_restore(self):
  with NativeScene(42) as s:
   before=s.render();expected=bytearray(before.bytes)
   for x in range(2,6):
    offset=(2*before.width+x)*16
    foreground=struct.unpack_from('<I',expected,offset+4)[0]
    struct.pack_into('<I',expected,offset+4,foreground^0xffffff)
   s.command({'op':'character-rule','rule':RULE})
   saved=s.snapshot();self.assertEqual(s.info()['characterRules'],[RULE])
   self.assertEqual(s.render().bytes,bytes(expected));self.assertEqual(saved,s.snapshot())
   s.command({'op':'character-rule','rule':{'id':'invert','enabled':False}})
   self.assertEqual(s.render().bytes,before.bytes)
   s.restore(saved);self.assertEqual(s.render().bytes,bytes(expected));self.assertEqual(saved,s.snapshot())
   s.command({'op':'remove-character-rule','id':'invert'});s.command({'op':'remove-character-rule','id':'invert'})
   self.assertEqual(s.render().bytes,before.bytes);self.assertEqual(s.info()['characterRules'],[])
 def test_priority_and_string_id_order_are_independent_of_insertion(self):
  rules=[{'id':'z','priority':0,'foregroundEffects':[{'type':'invert'}]},
         {'id':'a','priority':0,'foregroundEffects':[{'type':'threshold','value':.2}]},
         {'id':'first','priority':-1,'foregroundEffects':[{'type':'contrast','value':0}]}]
  with NativeScene(42) as s,NativeScene(42) as other:
   for rule in rules:s.command({'op':'character-rule','rule':rule})
   for rule in reversed(rules):other.command({'op':'character-rule','rule':rule})
   self.assertEqual(s.render().bytes,other.render().bytes)
   painted=s.render().bytes
   for offset in range(4,len(painted),16):self.assertEqual(struct.unpack_from('<I',painted,offset)[0],0)
 def test_invalid_authoring_and_batch_rollback_preserve_registry(self):
  with NativeScene(42) as s:
   s.command({'op':'character-rule','rule':RULE});before=s.snapshot()
   for rule in [{'id':''},{'id':'bad','foreground':9999},{'id':'bad','foregroundEffects':[{'type':'gamma','value':0}]},
                {'id':'bad','states':{'active':{'priority':1}}},{'id':'bad','selector':{'indices':[-1]}}]:
    with self.subTest(rule=rule):
     with self.assertRaises(ValueError):s.command({'op':'character-rule','rule':rule})
     self.assertEqual(before,s.snapshot());self.assertEqual(s.info()['characterRules'],[RULE])
   with self.assertRaises(ValueError):s.command({'op':'batch','commands':[{'op':'remove-character-rule','id':'invert'},{'op':'character-rule','rule':{'id':''}}]})
   self.assertEqual(before,s.snapshot());self.assertEqual(s.info()['characterRules'],[RULE])
