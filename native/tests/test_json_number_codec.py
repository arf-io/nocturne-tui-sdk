"""Independent IEEE-754 oracles for decimal input and computed JSON results."""
from pathlib import Path
import sys,unittest,struct,decimal,math,random
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
# Authored schema-32 typed footer; layout assertions must confirm this at the API gate.
TOKEN_NUMBER=24+5958112+8+8+4096+24
class JsonNumberCodec(unittest.TestCase):
 def setUp(self):self.s=NativeScene(42);self.addCleanup(self.s.close)
 def command(self,op,**kw):self.s.command({'op':op,**kw})
 def cached_number(self):return struct.unpack_from('<d',self.s.snapshot(),TOKEN_NUMBER)[0]
 def test_decimal_input_matches_independent_correct_rounding(self):
  self.command('define',path='/json',type='json',value=0)
  samples=['0','-0','0.1','0.2','0.3','1.2345678901234567','9007199254740991','9007199254740993',
   '1e100','1e-100','-1e-100','1e-101','5e-324','-5e-324','1e-1000','0.'+'0'*323+'5',
   '0.1000000000000000055511151231257827021181583404541015625',
   '1.00000000000000011102230246251565404236316680908203125',
   '1.00000000000000011102230246251565404236316680908203125001']
  with decimal.localcontext() as context:
   context.prec=1600
   samples.extend(format(decimal.Decimal.from_float(x),'f') for x in [sys.float_info.min,sys.float_info.min/2,5e-324,0.1,1e-100,1e100])
  for sample in samples:
   with self.subTest(sample=sample[:80]):
    self.s.command_raw(('{"op":"set","path":"/json","value":'+sample+'}').encode())
    self.assertEqual(struct.pack('<d',self.cached_number()),struct.pack('<d',float(decimal.Decimal(sample))))
 def test_computed_numbers_serialize_without_precision_loss(self):
  self.command('define',path='/json',type='json',value={})
  for numerator,denominator in [(1,3),(1,10),(2,7),(-1,10),(900719,7),(1,1000000)]:
   with self.subTest(numerator=numerator,denominator=denominator):
    expression={'divide':[numerator,denominator]}
    self.command('set',path='/json',expression=expression)
    expected=numerator/denominator
    self.assertEqual(struct.pack('<d',self.cached_number()),struct.pack('<d',expected))
    self.assertEqual(struct.pack('<d',self.s.info()['values']['/json']),struct.pack('<d',expected))
    saved=self.s.snapshot();self.s.restore(saved);self.assertEqual(saved,self.s.snapshot())
 def test_numbers_can_be_constructed_in_arrays_and_objects(self):
  self.command('define',path='/json',type='json',value={});self.command('define',path='/source',value=.1)
  self.command('set',path='/json',expression={'object':{'fraction':{'divide':[1,3]},'values':{'array':[{'path':'/source'},{'add':[1,2]}]}}})
  self.assertEqual(self.s.info()['values']['/json'],{'fraction':1/3,'values':[.1,3]})
 def test_numeric_value_metadata_preserves_computed_bits(self):
  self.command('define',path='/number',value=0)
  for numerator,denominator in [(1,3),(1,10),(2,7),(-1,10)]:
   self.command('set',path='/number',expression={'divide':[numerator,denominator]})
   self.assertEqual(struct.pack('<d',self.s.info()['values']['/number']),struct.pack('<d',numerator/denominator))
 def test_midpoints_subnormals_and_adjacent_binary_values(self):
  self.command('define',path='/json',type='json',value=0)
  values=[5e-324,sys.float_info.min,1e-100,.1,1.0,65536.0,1e12]
  with decimal.localcontext() as context:
   context.prec=1800
   for value in values:
    following=math.nextafter(value,math.inf)
    midpoint=(decimal.Decimal.from_float(value)+decimal.Decimal.from_float(following))/2
    for sample in [format(midpoint,'f'),format(midpoint+decimal.Decimal('1e-1201'),'f')]:
     with self.subTest(value=value):
      self.s.command_raw(('{"op":"set","path":"/json","value":'+sample+'}').encode())
      self.assertEqual(struct.pack('<d',self.cached_number()),struct.pack('<d',float(decimal.Decimal(sample))))
 def test_invalid_numeric_tokens_and_range_reject_without_mutation(self):
  self.command('define',path='/json',type='json',value=0)
  for sample in ['1e101','-1e101','01','1.','1e','+1','NaN','Infinity']:
   before=self.s.snapshot()
   with self.subTest(sample=sample),self.assertRaises(ValueError):self.s.command_raw(('{"op":"set","path":"/json","value":'+sample+'}').encode())
   self.assertEqual(before,self.s.snapshot())
 def test_normalized_significands_and_extreme_exponents(self):
  self.command('define',path='/json',type='json',value=0)
  for sample in ['0.'+'0'*1500+'1e1501','1'+'0'*1500+'e-1500','0e9999999999','-0e-9999999999','1e-9999999999']:
   self.s.command_raw(('{"op":"set","path":"/json","value":'+sample+'}').encode())
   expected=-0.0 if sample.startswith('-') else 0.0 if sample.startswith('0e') or sample.startswith('1e-') else 1.0
   self.assertEqual(struct.pack('<d',self.cached_number()),struct.pack('<d',expected))
 def test_random_binary_values_use_independent_decimal_reference(self):
  self.command('define',path='/json',type='json',value=0);generator=random.Random(42);accepted=0
  while accepted<200:
   value=struct.unpack('<d',struct.pack('<Q',generator.getrandbits(64)))[0]
   if not math.isfinite(value) or abs(value)>1e100:continue
   sample=format(decimal.Decimal.from_float(value),'f')
   self.s.command_raw(('{"op":"set","path":"/json","value":'+sample+'}').encode())
   self.assertEqual(struct.pack('<d',self.cached_number()),struct.pack('<d',value));accepted+=1
 def test_computed_negative_zero_survives_metadata_and_import(self):
  self.command('define',path='/json',type='json',value=0)
  self.command('set',path='/json',expression={'negate':0})
  self.assertEqual(struct.pack('<d',self.cached_number()),struct.pack('<d',-0.0))
  self.assertEqual(struct.pack('<d',self.s.info()['values']['/json']),struct.pack('<d',-0.0))
  saved=self.s.snapshot();self.s.restore(saved);self.assertEqual(saved,self.s.snapshot())
if __name__=='__main__':unittest.main()
