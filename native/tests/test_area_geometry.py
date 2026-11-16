"""Real native application geometry and owned indicator clipping regressions."""
import ctypes as C,unittest
from nocturne_native import NativeScene
def resolve(areas,id,viewport=(60,24)):
 chain=[];at=id
 while at:
  a=areas[at];chain.append(a);at=a.get('parent',0)
 x=y=0;left=top=0;right,bottom=viewport
 for a in reversed(chain):
  x+=a.get('x',0);sy=a.get('y',0);y+=viewport[1]+sy if sy<0 else sy;w=a['width'];h=a['height'];left=max(left,x);top=max(top,y);right=min(right,x+w);bottom=min(bottom,y+h)
 pad=a.get('padding',0)+(a.get('border','none')!='none');cx=max(0,min(viewport[0],left));cy=max(0,min(viewport[1],top));ex=max(0,min(viewport[0],right));ey=max(0,min(viewport[1],bottom));return [x,y,w,h,cx,cy,max(0,ex-cx),max(0,ey-cy),x+pad,y+pad,max(0,w-2*pad),max(0,h-2*pad)]
class AreaGeometry(unittest.TestCase):
 def setup_scene(self,s):
  for c in [{'op':'resize','width':60,'height':24},{'op':'environment','stars':0},{'op':'prompt','active':False},{'op':'material','id':2,'space':'rgb','channels':{'r':1,'g':1,'b':1},'alpha':1}]:s.command(c)
 def area(self,s,**kw):s.command({'op':'area','border':'none','padding':0,'alpha':0,**kw})
 def test_independent_nested_clipping_negative_anchor_large_coordinates_and_content(self):
  cases=[{1:{'id':1,'x':-3,'y':-8,'width':40,'height':7}}, {1:{'id':1,'x':8,'y':3,'width':16,'height':10},2:{'id':2,'parent':1,'x':10,'y':5,'width':20,'height':12}}, {1:{'id':1,'x':2147483647,'y':0,'width':2147483647,'height':10},2:{'id':2,'parent':1,'x':2147483647,'y':1,'width':40,'height':8}}, {1:{'id':1,'x':3,'y':2,'width':30,'height':18},2:{'id':2,'parent':1,'x':2,'y':-4,'width':10,'height':6}}]
  for areas in cases:
   with self.subTest(areas=areas),NativeScene() as s:
    self.setup_scene(s)
    for id,a in areas.items():self.area(s,**a)
    before=s.snapshot()
    for id in areas:self.assertEqual(s.area_geometry(id),resolve(areas,id))
    s.render();self.assertEqual(s.snapshot(),before)
 def test_all_borders_padding_empty_content_and_hide_empty_geometry(self):
  for border in ['none','rounded','square','double','heavy']:
   for pad in [0,2,8]:
    with self.subTest(border=border,pad=pad),NativeScene() as s:
     self.setup_scene(s);a={'id':1,'x':4,'y':5,'width':14,'height':8,'border':border,'padding':pad,'hideEmpty':True};self.area(s,**a);self.assertEqual(s.area_geometry(1),resolve({1:a},1));self.assertEqual(s.info()['areas'][0]['hideEmpty'],True)
 def test_wait_and_cursor_cannot_escape_owner_ancestors_offscreen_or_missing_owner(self):
  for cursor in [False,True]:
   for owner in ['outside-own','outside-parent','offscreen','missing']:
    with self.subTest(cursor=cursor,owner=owner),NativeScene() as s,NativeScene() as oracle:
     for scene in [s,oracle]:
      self.setup_scene(scene)
      if owner!='missing':self.area(scene,id=1,x=5 if owner!='offscreen' else 1000,y=4,width=10,height=5)
      if owner=='outside-parent':self.area(scene,id=2,parent=1,x=8,y=0,width=10,height=5)
     id=2 if owner=='outside-parent' else 1;x=12 if owner=='outside-own' else 3 if owner=='outside-parent' else 2
     s.command({'op':'indicator','id':1,'area':id,'x':x,'y':1,'sequence':'Z','cursor':cursor});self.assertEqual(s.render().bytes,oracle.render().bytes)
 def test_owned_and_unowned_inside_indicators_keep_glyph_index_and_purity(self):
  with NativeScene() as s:
   self.setup_scene(s);self.area(s,id=1,x=5,y=4,width=10,height=5);s.command({'op':'indicator','id':1,'area':1,'x':2,'y':1,'sequence':'AB','stepMs':100});s.command({'op':'indicator','id':2,'x':40,'y':3,'sequence':'Z'})
   for t,glyph in [(0,'A'),(150000,'B')]:
    s.advance_to(t);before=s.snapshot();f=s.render();self.assertEqual(f.words()[5*f.width+7][0],ord(glyph));self.assertEqual(f.words()[3*f.width+40][0],ord('Z'));self.assertEqual(s.snapshot(),before)
 def test_bound_geometry_schedule_and_partition_replay(self):
  with NativeScene() as s:
   self.setup_scene(s);self.area(s,id=1,x=5,y=4,width=10,height=5);self.area(s,id=2,parent=1,x=2,y=1,width=12,height=6);s.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'define','path':'/width','value':20,'binding':{'family':'area','id':1,'field':'width'}}});start=s.snapshot();s.advance_to(1000000);done=s.snapshot();self.assertEqual(s.area_geometry(2),[7,5,12,6,7,5,12,4,7,5,12,6]);s.restore(start)
   for t in [100000,499999,500000,700000,1000000]:s.advance_to(t)
   self.assertEqual(s.snapshot(),done)
 def test_real_C_negative_memory_boundaries_and_owned_discovery(self):
  with NativeScene() as s:
   self.setup_scene(s);self.area(s,id=1,x=5,y=4,width=10,height=5);fn=s._lib.nrAreaGeometry;fn.argtypes=[C.c_void_p,C.c_uint32,C.c_void_p,C.c_uint32];fn.restype=C.c_int;out=(C.c_double*12)(*([99]*12));before=s.snapshot()
   for id,ptr,capacity in [(0,out,12),(65536,out,12),(1,out,11),(1,C.byref(out,1),12),(1,s._context,12)]:self.assertEqual(fn(s._context,id,ptr,capacity),-1);self.assertEqual(list(out),[99]*12)
   self.assertEqual(fn(s._context,999,out,12),0);self.assertEqual(list(out),[99]*12);self.assertEqual(s.snapshot(),before);row=s.area_geometry(1);row[0]=-99;self.assertEqual(s.area_geometry(1)[0],5);self.assertEqual(s.info()['contract']['queryContracts']['nrAreaGeometry']['rowWords'],12)
if __name__=='__main__':unittest.main()
