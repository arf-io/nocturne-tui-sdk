"""Independent public-track edit oracles across material color spaces."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
SPACES={'oklch':'lch','oklab':'lab','hsl':'hsl','hsb':'hsv','rgb':'rgb','linear-rgb':'rgb','cmyk':'cmyk','indexed':'i'}
class MaterialTracks(unittest.TestCase):
 def test_every_track_field_matches_public_partial_track_edit(self):
  fields={'initial':.4,'rate':.2,'min':.1,'max':.9,'step':.2,'periodMs':1200,'boundary':2,'easing':4,'seed':4294967295}
  for base in ['alpha','index','channels.h']:
   for field,value in fields.items():
    with self.subTest(base=base,field=field),NativeScene(42) as s,NativeScene(42) as oracle:
     for scene in [s,oracle]:scene.command({'op':'material','id':2,'space':'hsl'})
     s.command({'op':'define','path':'/control','value':value,'binding':{'family':'material','id':2,'field':base+'.'+field}})
     authored=['clamp','loop','reverse','random','smooth-random'][value] if field=='boundary' else ['linear','ease-in','ease-out','smooth','smoother','sine','step'][value] if field=='easing' else value
     edit={field:authored};command={'op':'material','id':2}
     if base.startswith('channels.'):command['channels']={base[-1]:edit}
     else:command[base]=edit
     oracle.command(command);s.command({'op':'remove-value','path':'/control'});self.assertEqual(s.snapshot(),oracle.snapshot())
 def test_color_channel_resolution_and_ranges_match_all_spaces(self):
  for space,channels in SPACES.items():
   for channel in channels:
    with self.subTest(space=space,channel=channel),NativeScene(42) as s,NativeScene(42) as oracle:
     for scene in [s,oracle]:scene.command({'op':'material','id':2,'space':space,**({'colors':[0,0xffffff]} if space=='indexed' else {})})
     s.command({'op':'define','path':'/rate','value':.2,'binding':{'family':'material','id':2,'field':'channels.'+channel+'.rate'}})
     oracle.command({'op':'material','id':2,'channels':{channel:{'rate':.2}}});s.command({'op':'remove-value','path':'/rate'})
     self.assertEqual(s.snapshot(),oracle.snapshot());s.advance_to(1000000);oracle.advance_to(1000000)
     self.assertEqual(s.render().bytes,oracle.render().bytes)
 def test_bad_track_relationships_and_ranges_reject_atomically(self):
  with NativeScene(42) as s:
   s.command({'op':'material','id':2,'space':'hsl'})
   for field,value in [('alpha.min',2),('alpha.max',-.1),('index.min',9),('index.max',-1),('alpha.periodMs',0),('alpha.periodMs',.0005),('alpha.rate',10001),('alpha.seed',4294967296),('alpha.seed',.5),('channels.z.rate',1),('alpha.boundary',5),('alpha.easing',7)]:
    before=s.snapshot()
    with self.subTest(field=field),self.assertRaises(ValueError):s.command({'op':'define','path':'/bad','value':value,'binding':{'family':'material','id':2,'field':field}})
    self.assertEqual(before,s.snapshot())
if __name__=='__main__':unittest.main()
