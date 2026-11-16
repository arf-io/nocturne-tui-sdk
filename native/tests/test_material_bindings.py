"""Color-space-aware bindings with independent RGB expectations and rollback."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
SPACES={'oklch':{'l':.7,'c':.1,'h':180},'oklab':{'l':.7,'a':.1,'b':.1},'hsl':{'h':0,'s':1,'l':.5},'hsb':{'h':0,'s':1,'v':1},'rgb':{'r':.2,'g':.4,'b':.6},'linear-rgb':{'r':.2,'g':.4,'b':.6},'cmyk':{'c':.1,'m':.2,'y':.3,'k':.4},'indexed':{'i':0}}
def setup(s,space,channels):
 s.command({'op':'material','id':2,'space':space,'channels':channels,'alpha':1,**({'colors':[0xff0000,0x00ff00,0x0000ff]} if space=='indexed' else {})})
 s.command({'op':'widget','id':1,'kind':'text','x':2,'y':2,'height':1,'text':'A','alpha':0,'material':2})
def foreground(s):
 frame=s.render();return frame.words()[2*frame.width+2][1]
class MaterialBindings(unittest.TestCase):
 def test_hsl_lightness_changes_lightness_not_hue(self):
  with NativeScene() as s:
   setup(s,'hsl',SPACES['hsl']);s.command({'op':'define','path':'/light','value':.25,'binding':{'family':'material','id':2,'field':'lightness'}})
   self.assertEqual(foreground(s),0x800000)
 def test_every_native_channel_matches_explicit_authoring(self):
  for space,channels in SPACES.items():
   for field in channels:
    target=120 if field=='h' else 1 if field=='i' else .25
    with self.subTest(space=space,field=field),NativeScene(42) as actual,NativeScene(42) as reference:
     for s in (actual,reference):setup(s,space,channels)
     actual.command({'op':'define','path':'/channel','value':target,'binding':{'family':'material','id':2,'field':'channels.'+field}})
     reference.command({'op':'material','id':2,'channels':{field:target}})
     self.assertEqual(actual.render().bytes,reference.render().bytes)
 def test_rgb_and_indexed_have_independent_expected_colors(self):
  for space,field,value,color in [('rgb','channels.r',1,0xff6699),('indexed','channels.i',1,0x00ff00),('hsb','brightness',.5,0x800000)]:
   with self.subTest(space=space),NativeScene() as s:
    setup(s,space,SPACES[space]);s.command({'op':'define','path':'/color','value':value,'binding':{'family':'material','id':2,'field':field}});self.assertEqual(foreground(s),color)
 def test_incompatible_channels_aliases_and_ranges_are_atomic(self):
  for space,field,value in [('rgb','hue',.5),('rgb','lightness',.5),('oklab','hue',.5),('hsb','lightness',.5),('hsl','channels.r',.5),('oklch','channels.c',.6),('oklab','channels.a',-.6),('rgb','channels.r',1.1),('indexed','channels.i',65)]:
   with self.subTest(space=space,field=field),NativeScene() as s:
    setup(s,space,SPACES[space]);before=s.snapshot()
    with self.assertRaises(ValueError):s.command({'op':'define','path':'/bad','value':value,'binding':{'family':'material','id':2,'field':field}})
    self.assertEqual(s.snapshot(),before)
 def test_gradient_index_replay_and_source_purity(self):
  with NativeScene() as s:
   s.command({'op':'material','id':2,'space':'rgb','gradient':[[1,0,0],[0,1,0]],'alpha':1});s.command({'op':'widget','id':1,'kind':'text','x':2,'y':2,'height':1,'text':'A','alpha':0,'material':2})
   s.command({'op':'define','path':'/gradient','value':0,'binding':{'family':'material','id':2,'field':'index'}});s.command({'op':'set','path':'/gradient','value':.5});saved=s.snapshot();self.assertEqual(foreground(s),0x00ff00);self.assertEqual(s.snapshot(),saved)
   s.command({'op':'set','path':'/gradient','value':0});s.restore(saved);self.assertEqual(foreground(s),0x00ff00)
if __name__=='__main__':unittest.main()
