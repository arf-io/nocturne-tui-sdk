"""Independent black/white mixing, endpoint identity and pure public binding."""
from pathlib import Path
import sys,unittest
from fractions import Fraction
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class CompositeSpaces(unittest.TestCase):
 def test_porter_duff_alpha_against_exact_rational_oracle_in_every_space(self):
  with NativeScene(42) as s:
   before=s.snapshot()
   for base_alpha,source_alpha in [(0,0),(0,65535),(65535,0),(65535,65535),(12345,45678),(32768,32768)]:
    b=Fraction(base_alpha,65535);a=Fraction(source_alpha,65535)
    # Coverage identities, independent of the renderer's color algebra.
    coverage=[a+b-a*b,0,a,b,a+b-a*b,a*b,a*b,a*(1-b),b*(1-a),b,a,a+b-2*a*b,a+b]
    for operation,alpha in enumerate(coverage):
     scaled=min(Fraction(1),max(Fraction(0),Fraction(alpha)))*65535+Fraction(1,2)
     expected=scaled.numerator//scaled.denominator
     for space in range(4):
      for blend in range(28):
       if blend==26:continue # Dissolve explicitly changes source coverage.
       with self.subTest(base=base_alpha,source=source_alpha,operation=operation,space=space,blend=blend):
        self.assertEqual(s.composite_in_space(0x204060,0xe08010,space,base_alpha,source_alpha,blend=blend,operation=operation)[1],expected)
   self.assertEqual(s.snapshot(),before)
 def test_all_space_midpoints_endpoints_and_purity(self):
  with NativeScene(42) as s:
   before=s.snapshot()
   for space,expected in enumerate([0x808080,0xbcbcbc,0x636363,0x636363]):
    self.assertEqual(s.composite_in_space(0,0xffffff,space,source_alpha=32768),(expected,65535))
    self.assertEqual(s.composite_in_space(0x123456,0xabcdef,space,source_alpha=0),(0x123456,65535))
    self.assertEqual(s.composite_in_space(0x123456,0xabcdef,space),(0xabcdef,65535))
   for invalid in [-1,4,True,.5]:
    with self.assertRaises(ValueError):s.composite_in_space(0,0xffffff,invalid)
   self.assertEqual(before,s.snapshot())
