"""Shared fixed-point OKLCh native fixtures. Never rewrite references in tests."""
import csv,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from studio import oklchColor,oklchLightness
class ObservatoryColorTests(unittest.TestCase):
 def testSharedCorpus(self):
  with (ROOT/'tests/observatory/color-fixtures.csv').open() as f:
   for row in csv.DictReader(f):
    v={k:int(x) for k,x in row.items()};result=oklchColor(v['lightness'],v['chroma'],v['hueMilliDegrees']);self.assertEqual(result,v['rgb']);self.assertEqual(oklchLightness(result),v['resultLightness'])
 def testInvalidScalars(self):
  for l,c,h in [(True,0,0),(1001,0,0),(0,-1,0),(0,4001,0),(0,0,2**31)]:
   with self.assertRaises(ValueError):oklchColor(l,c,h)
 def testHuePeriod(self):self.assertEqual(oklchColor(700,2500,270000),oklchColor(700,2500,-90000))
if __name__=='__main__':unittest.main()
