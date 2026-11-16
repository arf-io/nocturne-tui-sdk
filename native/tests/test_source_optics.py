import math,struct,zlib,unittest
from nocturne_native import NativeScene
IDS=['silk-tide','satin-rings','opal-fronts','interference-tide']
BASE=dict(op='field',optics='source',x=10,y=5,width=1,speed=8,strength=.7,lifeMs=4000,seed=0)
def oracle(profile,t,x,y,continuous=False,rings=2):
 age=t/1e6;radius=0 if continuous else 16*age;fade=1 if continuous else 1-age/4;d=math.hypot(2*(x-10),4*(y-5));band=2
 if profile==0:
  peak=0
  for k in range(rings):
   r=radius-8*k
   if r<0:continue
   p=max(0,1-abs(d-r)/band);peak=max(peak,p*p*(3-2*p)/(1+.42*k))
  return peak*fade*fade*(3-2*fade)*.7
 if profile==1:return (math.exp(-((d-radius)/band)**2) if abs(d-radius)<=3*band else 0)*fade**2*.65*.7
 if profile==2:
  pixel=(math.floor(2*x+.5),math.floor(4*y+.5));hit=any(pixel==(math.floor(20+radius*math.cos(j*math.pi/48)+.5),math.floor(20+radius*math.sin(j*math.pi/48)+.5)) for j in range(96))
  return (fade**1.5*.7 if hit else 0)
 return max(0,1-abs(d-radius)/band)*fade**1.8*.35*.7
def old(b,schema):
 b=bytearray(b[:13497408]);struct.pack_into('<I',b,16,len(b)-24);struct.pack_into('<I',b,12,schema);struct.pack_into('<I',b,28,schema);struct.pack_into('<I',b,20,zlib.crc32(b[24:]));return b
class SourceOptics(unittest.TestCase):
 def test_all_four_independent_equations_and_purity(self):
  for profile,name in enumerate(IDS):
   for continuous in [False,True]:
    with self.subTest(name=name,continuous=continuous),NativeScene() as s:
     s.command({**BASE,'effect':'surface-field/'+name,'continuous':continuous})
     for t in [0,250000,1000000,2250000]:
      s.advance_to(t);before=s.snapshot()
      for x,y in [(10,5),(10.25,5),(12,5),(14,5),(18,5),(22,5),(10,8)]:self.assertAlmostEqual(s.field_sample(1,x,y)[0],oracle(profile,t,x,y,continuous),delta=2e-6)
      s.render();self.assertEqual(before,s.snapshot())
 def test_discrete_opal_geometric_ring_not_annulus(self):
  with NativeScene() as s:
   s.command({**BASE,'effect':'surface-field/opal-fronts'});s.advance_to(1000000);hits=misses=0
   for px in range(3,38):
    for py in range(3,38):
     expected=oracle(2,1000000,px/2,py/4);self.assertAlmostEqual(s.field_sample(1,px/2,py/4)[0],expected,delta=2e-6)
     if expected:hits+=1
     elif abs(math.hypot(px-20,py-20)-16)<1:misses+=1
   self.assertGreater(hits,60);self.assertGreater(misses,0)
 def test_default_preservation_and_old_snapshot_guards(self):
  for name in IDS:
   with NativeScene() as a,NativeScene() as b:
    c={**BASE,'effect':'surface-field/'+name};c.pop('optics');a.command(c);b.command({**c,'optics':'legacy'});self.assertEqual(a.render(),b.render());before=a.render();a.restore(old(a.snapshot(),0x20261048));self.assertEqual(before,a.render())
    a.command({**BASE,'effect':'surface-field/'+name});current=a.snapshot()
    for schema in [0x20261047,0x20261048]:
     with self.assertRaises(ValueError):a.restore(old(current,schema))
     self.assertEqual(current,a.snapshot())
 def test_negative_atomic_and_nested_pending_guard(self):
  with NativeScene() as s:
   for patch in [{'optics':'missing'},{'optics':True},{'effect':'surface-field/satin-rings','rings':3}]:
    before=s.snapshot()
    with self.assertRaises(ValueError):s.command({**BASE,**patch})
    self.assertEqual(before,s.snapshot())
   s.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'batch','commands':[BASE]}});b=s.snapshot()
   with self.assertRaises(ValueError):s.restore(old(b,0x20261048))
   self.assertEqual(b,s.snapshot());s.advance_to(1000000);end=s.snapshot();s.restore(b)
   for t in [250000,500000,750000,1000000]:s.advance_to(t)
   self.assertEqual(end,s.snapshot())
 def test_source_colors_and_radial_material_gradient(self):
  with NativeScene() as s:
   s.command({**BASE,'effect':'surface-field/silk-tide'});self.assertEqual(s.field_sample(1,10,5)[1],0x28304f)
   s.command({'op':'material','id':2,'space':'rgb','scope':'characters','gradient':[[1,0,0],[0,0,1]],'spacing':.125,'alpha':.5})
   s.command({**BASE,'effect':'surface-field/satin-rings','material':2});a=s.field_sample(2,10,5);b=s.field_sample(2,12,5);self.assertNotEqual(a[1],b[1]);self.assertAlmostEqual(a[0],oracle(1,0,10,5)*.5,delta=2e-6)
