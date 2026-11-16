"""Checksum-correct hostile retained paint source and schema-31 promotion."""
from pathlib import Path
import gzip,struct,sys,unittest,zlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
BASE=24+7771360;STRIDE=4104
class CharacterRuleSnapshots(unittest.TestCase):
 def test_hostile_region_source_rejects_and_keeps_current_treatment(self):
  base=24+8296672
  with NativeScene(42) as s:
   s.command({'op':'character-region','region':{'id':'fragment','path':'/app/fragment','cells':[0],'indices':[9]}})
   s.command({'op':'character-rule','rule':{'id':'invert','selector':{'path':'/app/fragment'},'foregroundEffects':[{'type':'invert'}]}})
   good=s.snapshot();frame=s.render().bytes;length=struct.unpack_from('<i',good,base+4)[0]
   for fault in ['used','length','terminator','tail','unused','duplicate','json']:
    damaged=bytearray(good)
    if fault=='used':struct.pack_into('<i',damaged,base,2)
    elif fault=='length':struct.pack_into('<i',damaged,base+4,4096)
    elif fault=='terminator':damaged[base+8+length]=1
    elif fault=='tail':damaged[base+9+length]=1
    elif fault=='unused':damaged[base+STRIDE+8]=1
    elif fault=='duplicate':damaged[base+STRIDE:base+2*STRIDE]=good[base:base+STRIDE]
    else:damaged[base+8]=ord('[')
    with self.subTest(fault=fault):
     struct.pack_into('<I',damaged,20,zlib.crc32(damaged[24:]))
     with self.assertRaises(ValueError):s.restore(damaged)
     self.assertEqual(good,s.snapshot());self.assertEqual(frame,s.render().bytes)
 def test_malformed_source_slots_reject_without_changing_cache_or_state(self):
  with NativeScene(42) as s:
   s.command({'op':'character-rule','rule':{'id':'invert','foregroundEffects':[{'type':'invert'}]}})
   s.command({'op':'character-region','region':{'id':'fragment','path':'/app/fragment','cells':[0]}})
   good=s.snapshot();frame=s.render().bytes
   variants=[]
   damaged=bytearray(good);struct.pack_into('<i',damaged,BASE,2);variants.append(damaged)
   damaged=bytearray(good);struct.pack_into('<i',damaged,BASE+4,4096);variants.append(damaged)
   damaged=bytearray(good);length=struct.unpack_from('<i',good,BASE+4)[0];damaged[BASE+8+length]=1;variants.append(damaged)
   damaged=bytearray(good);damaged[BASE+8+length+1]=1;variants.append(damaged)
   damaged=bytearray(good);damaged[BASE+STRIDE+8]=1;variants.append(damaged)
   damaged=bytearray(good);damaged[BASE+STRIDE:BASE+2*STRIDE]=good[BASE:BASE+STRIDE];variants.append(damaged)
   damaged=bytearray(good);damaged[BASE+8]=ord('[');variants.append(damaged)
   for index,damaged in enumerate(variants):
    with self.subTest(index=index):
     struct.pack_into('<I',damaged,20,zlib.crc32(damaged[24:]))
     with self.assertRaises(ValueError):s.restore(damaged)
     self.assertEqual(good,s.snapshot());self.assertEqual(frame,s.render().bytes)
 def test_old_fixture_promotes_without_rules_or_cached_treatment(self):
  with NativeScene(42) as s:
   s.command({'op':'character-rule','rule':{'id':'invert','foregroundEffects':[{'type':'invert'}]}})
   s.command({'op':'character-region','region':{'id':'fragment','path':'/app/fragment','cells':[0]}})
   fixture=gzip.decompress((ROOT/'tests/fixtures/schema-20261031-before-trigger-formulas.snapshot.gz').read_bytes())
   s.restore(fixture);self.assertEqual(s.info()['characterRules'],[]);self.assertEqual(s.info()['characterRegions'],[])
   promoted=s.snapshot();s.render();self.assertEqual(promoted,s.snapshot())
   s.restore(promoted);self.assertEqual(promoted,s.snapshot())
