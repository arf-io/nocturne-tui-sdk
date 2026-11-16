"""Closed nested weather-authoring compiler parity and rejection contracts."""
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene

SCHEMA='nocturne.weather-authoring/v1'

class WeatherAuthoring(unittest.TestCase):
 def scene(self,seed=2030):return NativeScene(seed)
 def nested(self,**patch):
  value={'op':'weather-author','schema':SCHEMA,'id':1,'effect':'weather/silver-squall'}
  value.update(patch);return value
 def test_default_authoring_matches_flat_effect_defaults(self):
  with self.scene() as nested,self.scene() as flat:
   nested.command(self.nested())
   flat.command({'op':'emitter','id':1,'effect':'weather/silver-squall'})
   self.assertEqual(nested.snapshot(),flat.snapshot())
   nested.advance_to(500000);flat.advance_to(500000)
   self.assertEqual(nested.snapshot(),flat.snapshot())
   self.assertEqual(nested.particles(),flat.particles())
   self.assertEqual(nested.render().bytes,flat.render().bytes)
 def test_every_supported_leaf_maps_to_existing_flat_emitter_field(self):
  emission={'seed':31,'rate':5,'runningTimeMs':1000,'startTimeUs':0,'cycles':1,'gapMs':0,'schedule':'uniform'}
  birth={'shape':'box','position':[1,10,2],'extent':[2,1,2],'velocity':[0,-2,0],'spread':[0,.5,0]}
  forces={'gravity':[0,-9,0],'wind':[1,0,0],'windVariation':[.2,0,.2],'drag':.1,'lift':.2,'flutterHz':1,'flutterAmount':.1,'tumble':[0,0,0],'heat':1,'windScale':1,'windPeriodSeconds':1}
  particle={'shapeWeights':[1,0,0],'sizeMin':.1,'sizeMax':.2,'material':2,'alpha':.7,'radius':1,'topology':1,'trailMs':10,'birthFadeMs':5,'deathFadeMs':10,'coreMs':2,'nearDistance':.1,'farDistance':100,'farFadeDistance':1,'veinContrast':.5,'curl':.2,'backTint':.1,'twoSided':True,'sampling':'braille','surfaceAlpha':.5}
  collision={'enabled':False,'deposit':False}
  lifecycle={'lifetimeMinMs':1000,'lifetimeMaxMs':2000,'endStyle':'drain','tailMs':0}
  nested_cfg=self.nested(effect='weather/autumn-drift',emission=emission,birth=birth,forces=forces,particle=particle,collision=collision,lifecycle=lifecycle)
  flat_cfg={'op':'emitter','id':1,'effect':'weather/autumn-drift',**emission,**birth,**forces,**particle,'collision':False,'deposit':False,**lifecycle}
  with self.scene() as nested,self.scene() as flat:
   nested.command(nested_cfg);flat.command(flat_cfg)
   self.assertEqual(nested.snapshot(),flat.snapshot())

 def test_real_autumn_deposition_matches_flat_emitter(self):
  nested_cfg=self.nested(id=3,effect='weather/autumn-drift',
   emission={'seed':44,'count':3,'runningTimeMs':0},
   birth={'position':[0,.1,0],'extent':[0,0,0],'velocity':[0,-3,0],'spread':[0,0,0]},
   forces={'gravity':[0,-9,0],'wind':[0,0,0],'windVariation':[0,0,0]},
   collision={'enabled':True,'deposit':True},
   lifecycle={'lifetimeMinMs':10000,'lifetimeMaxMs':10000})
  flat_cfg={'op':'emitter','id':3,'effect':'weather/autumn-drift','seed':44,'count':3,'runningTimeMs':0,
   'position':[0,.1,0],'extent':[0,0,0],'velocity':[0,-3,0],'spread':[0,0,0],
   'gravity':[0,-9,0],'wind':[0,0,0],'windVariation':[0,0,0],
   'collision':True,'deposit':True,'lifetimeMinMs':10000,'lifetimeMaxMs':10000}
  with self.scene(9) as nested,self.scene(9) as flat:
   nested.command({'op':'floor','height':0,'enabled':True,'maxIndividual':20})
   flat.command({'op':'floor','height':0,'enabled':True,'maxIndividual':20})
   nested.command(nested_cfg);flat.command(flat_cfg)
   self.assertEqual(nested.snapshot(),flat.snapshot())
   nested.advance_to(200000);flat.advance_to(200000)
   self.assertEqual(nested.info()['particles']['deposited'],3)
   self.assertEqual(nested.snapshot(),flat.snapshot())
   self.assertEqual(nested.particles(),flat.particles())
 def test_real_nondepositing_rate_matches_flat_emitter(self):
  nested_cfg=self.nested(effect='weather/silver-squall',
   emission={'rate':12,'runningTimeMs':1000},
   birth={'position':[0,10,0],'extent':[1,1,1]},
   forces={'wind':[0,0,0]},
   collision={'enabled':False,'deposit':False})
  flat_cfg={'op':'emitter','id':1,'effect':'weather/silver-squall','rate':12,'runningTimeMs':1000,
   'position':[0,10,0],'extent':[1,1,1],'wind':[0,0,0], 'collision':False,'deposit':False}
  with self.scene() as nested,self.scene() as flat:
   nested.command(nested_cfg);flat.command(flat_cfg)
   nested.advance_to(1000000);flat.advance_to(1000000)
   self.assertEqual(nested.info()['particles']['born'],12)
   self.assertEqual(nested.snapshot(),flat.snapshot())
   self.assertEqual(nested.particles(),flat.particles())
 def test_seed_and_clock_boundaries_match_flat_without_roundtrip(self):
  nested_cfg=self.nested(emission={'seed':4294967295,'count':100000,'runningTimeMs':0,'startTimeUs':86400000000})
  flat_cfg={'op':'emitter','id':1,'effect':'weather/silver-squall','seed':4294967295,'count':100000,'runningTimeMs':0,'startTimeUs':86400000000}
  with self.scene() as nested,self.scene() as flat:
   nested.command(nested_cfg);flat.command(flat_cfg)
   self.assertEqual(nested.snapshot(),flat.snapshot())
   for patch in ({'seed':4294967296},{'startTimeUs':86400000001}):
    before=nested.snapshot()
    bad=self.nested(emission={'count':1,'runningTimeMs':0,**patch})
    with self.assertRaises(ValueError):nested.command(bad)
    self.assertEqual(before,nested.snapshot())
 def test_group_mapping_unknowns_types_and_conflicts_reject_atomically(self):
  with self.scene() as s:
   before=s.snapshot()
   invalid=(
    self.nested(schema='nocturne.weather-authoring/v2'),
    self.nested(emission={'count':2,'mystery':1}),
    self.nested(birth={'drag':1}),
    self.nested(forces=[0,0,0]),
    self.nested(emission={'count':2,'rate':12}),
    self.nested(collision={'enabled':False,'deposit':True}),
    self.nested(particle={'sizeMin':.5,'sizeMax':.1}),
   )
   for config in invalid:
    with self.subTest(config=config),self.assertRaises(ValueError):s.command(config)
    self.assertEqual(before,s.snapshot())
 def test_duplicate_keys_reject_before_mutation(self):
  raw=(b'{"op":"weather-author","schema":"nocturne.weather-authoring/v1","id":1,'
       b'"effect":"weather/silver-squall","emission":{"count":1,"count":2}}')
  with self.scene() as s:
   before=s.snapshot()
   with self.assertRaises(ValueError):s.command_raw(raw)
   self.assertEqual(before,s.snapshot())
  raw=(b'{"op":"weather-author","op":"emitter","schema":"nocturne.weather-authoring/v1",'
       b'"id":1,"effect":"weather/silver-squall"}')
  with self.scene() as s:
   before=s.snapshot()
   with self.assertRaises(ValueError):s.command_raw(raw)
   self.assertEqual(before,s.snapshot())
 def test_nested_command_failure_rolls_back_real_batch(self):
  with self.scene() as s:
   s.command({'op':'define','path':'/sentinel','value':4})
   before=s.snapshot()
   batch={'op':'batch','commands':[{'op':'set','path':'/sentinel','value':9},
    self.nested(forces={'gravity':[0,-999,0]})]}
   with self.assertRaises(ValueError):s.command(batch)
   self.assertEqual(before,s.snapshot())
 def test_parser_size_depth_and_token_limits_are_not_truncated(self):
  with self.scene() as s:
   before=s.snapshot()
   root=b'{"op":"weather-author","schema":"nocturne.weather-authoring/v1","id":1,"effect":"weather/silver-squall"}'
   exactly= root + b' '*(65536-len(root))
   s.command_raw(exactly)
   self.assertNotEqual(before,s.snapshot())
   before=s.snapshot()
   with self.assertRaises(ValueError):s.command_raw(root+b' ')
   self.assertEqual(before,s.snapshot())
   deep=(b'{"op":"weather-author","schema":"nocturne.weather-authoring/v1","id":1,"effect":"weather/silver-squall","extra":'+b'['*25+b'0'+b']'*25+b'}')
   with self.assertRaises(ValueError):s.command_raw(deep)
   self.assertEqual(before,s.snapshot())
   many=(b'{"op":"weather-author","schema":"nocturne.weather-authoring/v1","id":1,"effect":"weather/silver-squall","extra":['+b','.join([b'0']*8200)+b']}')
   with self.assertRaises(ValueError):s.command_raw(many)
   self.assertEqual(before,s.snapshot())
 def test_flat_emitter_remains_accepted(self):
  with self.scene() as s:
   s.command({'op':'emitter','id':1,'effect':'weather/autumn-drift','count':3,'runningTimeMs':0})
   self.assertEqual(s.info()['emitters'][0]['id'],1)

if __name__=='__main__':unittest.main()
