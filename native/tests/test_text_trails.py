"""Real source trail API/renderer contracts authored before implementation."""
import ctypes as C,hashlib,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class TextTrails(unittest.TestCase):
    def scene(self):
        s=NativeScene(2030);self.addCleanup(s.close);return s
    def sample(self,s,index,trail):
        fn=s._lib.nrTextTrailSample;fn.argtypes=[C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint32,C.POINTER(C.c_int32),C.c_uint32];fn.restype=C.c_int
        out=(C.c_int32*8)();self.assertEqual(fn(s._context,1,index,trail,out,8),0);return list(out)
    def test_original_all5profiles_curves_phases_lengths_and_purity(self):
        ref=json.loads((ROOT/'tests/fixtures/text-trail-reference.json').read_text())
        for p,h in ref['sources'].items():self.assertEqual(hashlib.sha256((ROOT.parent/p).read_bytes()).hexdigest(),h)
        for row in ref['rows']:
            with self.subTest(id=row['id'],curve=row['easing'],phase=row['phase'],length=row['trailLength']):
                s=self.scene();s.command({'op':'text','id':1,'text':'NODE','x':0,'y':0,'effect':row['id'],'phase':row['phase'],**row['config']})
                for us,poses in zip(ref['times'],row['poses']):
                    s.advance_to(us);pure=s.snapshot();expected=[]
                    for index,pose in enumerate(poses):
                        for ordinal,trail in enumerate(pose['trail']):
                            words=self.sample(s,index,ordinal);self.assertGreater(words[0],0);self.assertEqual(words[1],ord(pose['glyph']));self.assertEqual(words[2],ordinal+1)
                            for a,b in zip((words[3]/65536,words[4]/65536,words[5]/1e6,words[6]/1000),(trail['x'],trail['y'],trail['opacity'],pose['hueDelta'])):self.assertAlmostEqual(a,b,delta=.0012)
                            expected.append([index,ordinal+1,ord(pose['glyph']),trail['x'],trail['y'],trail['opacity'],pose['hueDelta']])
                    run=next(r for r in s.info_complete()['textRuns'] if r['id']==1);self.assertEqual(run['trailCount'],len(expected));self.assertEqual(len(run['trails']),min(16,len(expected)))
                    for actual,want in zip(run['trails'],expected[:16]):
                        for a,b in zip(actual[:7],want):self.assertAlmostEqual(a,b,delta=.0012)
                    s.render();self.assertEqual(s.snapshot(),pure)
    def test_replay_local_reduced_motion_and_atomic_output_rejection(self):
        s=self.scene();s.command({'op':'text','id':1,'text':'NODE','effect':'text/prism-weave','easing':'back','trailLength':8,'durationMs':1000,'variation':0,'staggerMs':0});initial=s.snapshot()
        s.advance_to(400000);words=self.sample(s,0,0);frame=s.render().bytes;final=s.snapshot();s.restore(initial);s.advance_to(400000);self.assertEqual(self.sample(s,0,0),words);self.assertEqual(s.render().bytes,frame);self.assertEqual(s.snapshot(),final)
        fn=s._lib.nrTextTrailSample;out=(C.c_int32*8)(*([123]*8));pure=s.snapshot()
        for ident,index,trail,capacity in [(999,0,0,8),(1,4,0,8),(1,0,8,8),(1,0,0,7)]:self.assertEqual(fn(s._context,ident,index,trail,out,capacity),-1);self.assertEqual(list(out),[123]*8)
        self.assertEqual(s.snapshot(),pure)
        s.command({'op':'accessibility','reducedMotion':True});self.assertEqual(fn(s._context,1,0,0,out,8),-1);self.assertEqual(list(out),[123]*8)
        s.command({'op':'accessibility','reducedMotion':False});s.command({'op':'text','id':1,'local':True});self.assertEqual(fn(s._context,1,0,0,out,8),-1)
    def test_retained_identity_retarget_geometry_and_lifecycle(self):
        s=self.scene();s.command({'op':'text','id':1,'text':'NODE','effect':'text/skyfall-type','wind':1.3,'trailLength':8,'durationMs':1000,'variation':0,'staggerMs':0})
        s.advance_to(250000);before=self.sample(s,0,0);identity=before[0]
        s.command({'op':'text','id':1,'phase':'hide','effect':'text/comet-stitch'})
        after=self.sample(s,0,0);self.assertEqual(after[0],identity)
        # Retarget captures the main pose; trails retain its relative offset.
        fn=s._lib.nrTextSample;fn.argtypes=[C.c_void_p,C.c_uint32,C.c_uint32,C.POINTER(C.c_int32),C.c_uint32];fn.restype=C.c_int
        main=(C.c_int32*8)();self.assertEqual(fn(s._context,1,0,main,8),0)
        self.assertEqual(after[0],main[2]);self.assertEqual(after[1],main[0]);self.assertAlmostEqual(after[3]/65536,main[3]/65536-1.3*.15,delta=.0012)
        s.command({'op':'clear','scope':'text'});out=(C.c_int32*8)(*([321]*8));self.assertEqual(s._lib.nrTextTrailSample(s._context,1,0,0,out,8),-1);self.assertEqual(list(out),[321]*8)
        s.command({'op':'text','id':1,'text':'X','effect':'text/direct-ink'});self.assertEqual(s._lib.nrTextTrailSample(s._context,1,0,0,out,8),-1)
    def test_real_trail_glyph_paint_and_zero_length_frame_change(self):
        import math
        s=self.scene()
        for c in [{'op':'resize','width':100,'height':40},{'op':'prompt','active':False},{'op':'environment','stars':0},
          {'op':'text','id':1,'text':'N','x':45,'y':20,'effect':'text/comet-stitch','phase':'hide','trailLength':8,'durationMs':1000,'variation':0,'staggerMs':0,'wind':2,'distance':6,'scatter':3}]:s.command(c)
        s.advance_to(250000);trail=self.sample(s,0,7);self.assertGreater(trail[5],0);frame=s.render().bytes
        x,y=math.floor(trail[3]/65536+.5),math.floor(trail[4]/65536+.5);self.assertEqual(s.inspect_character_cell(x,y)['glyph'],ord('N'))
        s.command({'op':'text','id':1,'trailLength':0});self.assertNotEqual(s.render().bytes,frame)
    def test_misaligned_context_overlapping_outputs_and_owned_python_binding(self):
        s=self.scene();s.command({'op':'text','id':1,'text':'X','effect':'text/prism-weave','trailLength':1,'durationMs':1000,'variation':0});s.advance_to(250000);self.sample(s,0,0)
        fn=s._lib.nrTextTrailSample;raw=(C.c_ubyte*40)(*([0xa5]*40));unaligned=C.cast(C.addressof(raw)+1,C.POINTER(C.c_int32));pure=s.snapshot()
        self.assertEqual(fn(s._context,1,0,0,unaligned,8),-1);self.assertEqual(bytes(raw),bytes([0xa5]*40))
        overlap=C.cast(s._context,C.POINTER(C.c_int32));self.assertEqual(fn(s._context,1,0,0,overlap,8),-1);self.assertEqual(s.snapshot(),pure)
        owned=s.text_trail_sample(1,0,0);self.assertEqual(owned,self.sample(s,0,0));owned[0]=999;self.assertNotEqual(s.text_trail_sample(1,0,0)[0],999)
        for args in ((0,0,0),(1,-1,0),(1,0,-1),(True,0,0),(1,0,.5)):
            with self.subTest(args=args),self.assertRaises((ValueError,TypeError)):s.text_trail_sample(*args)
