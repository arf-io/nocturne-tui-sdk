"""Real 43 original source geometry contracts before additive native mode."""
import ctypes as C,hashlib,json,struct,sys,unittest,zlib,os,subprocess,tempfile
from functools import lru_cache
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
@lru_cache(maxsize=1)
def source65_window_layout():
    # Test-constructed historical layout; source/header proof is retained in the fixture.
    old=json.loads((Path(__file__).parent/'fixtures/window-source65-layout.json').read_text())
    code='#include "internal.h"\n#include <stddef.h>\n#include <stdio.h>\nint main(void){printf("%u %zu %zu %zu %zu %zu %zu %zu %zu\\n",NR_STATE_SCHEMA,offsetof(State,legacyWindows),offsetof(State,windows),sizeof(Window),offsetof(State,legacyTextIdentities),offsetof(State,textIdentities),sizeof(TextIdentityRun),offsetof(State,legacyWindowSourceGeometry),(size_t)NR_MAX_WINDOWS);return 0;}\n'
    with tempfile.TemporaryDirectory(prefix='nocturne-source65-window-layout-') as tmp:
        path=Path(tmp);(path/'probe.c').write_text(code)
        subprocess.run([os.environ.get('CC','cc'),'-std=c11','-I'+str(ROOT/'include'),'-I'+str(ROOT/'src'),str(path/'probe.c'),'-o',str(path/'probe')],check=True,capture_output=True,text=True)
        values=list(map(int,subprocess.check_output([str(path/'probe')],text=True).split()))
    q=dict(zip(['schema','legacyWindows','windows','windowBytes','legacyIdentities','identities','identityBytes','source65Bytes','windowCount'],values))
    for current,historical in [('legacyWindows','windowsOffset'),('windowBytes','windowBytes'),('legacyIdentities','identitiesOffset'),('identityBytes','identityBytes'),('source65Bytes','stateBytes')]:
        if q[current]!=old[historical]:raise AssertionError('Actual current header disagrees with retained source65 layout')
    return old,q

class WindowSourceGeometry(unittest.TestCase):
    def scene(self):
        s=NativeScene(2030);self.addCleanup(s.close);return s
    def point(self,s,u,v,p):
        fn=s._lib.nrWindowSample;fn.argtypes=[C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint32,C.c_uint32,C.POINTER(C.c_int32),C.c_uint32];fn.restype=C.c_int
        words=(C.c_int32*5)();self.assertEqual(fn(s._context,1,round(u*1e6),round(v*1e6),round(p*1e6),words,5),0)
        return [words[0]/65536,words[1]/65536,words[2]/65536,words[3]/1e6]
    def test_all43_original_source_operators_interior_edges_highseed(self):
        ref=json.loads((ROOT/'tests/fixtures/window-source-reference.json').read_text());self.assertEqual(len({r['id'] for r in ref['rows']}),43)
        for path,h in ref['sources'].items():self.assertEqual(hashlib.sha256((ROOT.parent/path).read_bytes()).hexdigest(),h)
        for row in ref['rows']:
            with self.subTest(id=row['id'],seed=row['controls']['seed']):
                s=self.scene();s.command({'op':'window','id':1,'effect':row['id'],'sourceGeometry':True,**row['controls']});pure=s.snapshot()
                for sample in row['samples']:
                    actual=self.point(s,sample['u'],sample['v'],sample['p'])
                    for a,b in zip(actual,sample['expected']):self.assertAlmostEqual(a,b,delta=.0012)
                s.render();self.assertEqual(s.snapshot(),pure)
    def test_default_unchanged_false_restore_replay_and_visible_mode_change(self):
        s=self.scene();s.command({'op':'window','id':1,'effect':'window-transition/fragment-scatter','width':30,'height':20,'seed':42})
        baseline=self.point(s,.2,.3,.5);s.command({'op':'window','id':1,'sourceGeometry':False});self.assertEqual(self.point(s,.2,.3,.5),baseline)
        s.command({'op':'window','id':1,'sourceGeometry':True});self.assertNotEqual(self.point(s,.2,.3,.5),baseline);initial=s.snapshot()
        s.advance_to(123000);frame=s.render().bytes;final=s.snapshot();s.restore(initial);s.advance_to(123000);self.assertEqual(s.snapshot(),final);self.assertEqual(s.render().bytes,frame)
    def test_boolean_rejection_partial_edit_and_reset(self):
        s=self.scene();s.command({'op':'window','id':1,'sourceGeometry':True});s.command({'op':'window','id':1,'title':'Retained source flag'})
        self.assertTrue(next(w for w in s.info_complete()['windows'] if w['id']==1)['sourceGeometry'])
        for value in (1,'true',None):
            pure=s.snapshot()
            with self.subTest(value=value),self.assertRaises(ValueError):s.command({'op':'window','id':1,'sourceGeometry':value})
            self.assertEqual(s.snapshot(),pure)
        s.command({'op':'reset'});s.command({'op':'window','id':1});self.assertFalse(s.info_complete()['windows'][0]['sourceGeometry'])
    def old65(self,s):
        old,q=source65_window_layout();raw=s.snapshot()
        self.assertEqual(struct.unpack_from('<I',raw,12)[0],q['schema'])
        self.assertEqual(struct.unpack_from('<I',raw,28)[0],q['schema'])
        self.assertEqual(struct.unpack_from('<I',raw,16)[0],len(raw)-24)
        self.assertEqual(struct.unpack_from('<I',raw,20)[0],zlib.crc32(raw[24:]))
        d=bytearray(raw[:24+old['stateBytes']])
        # Source65 stored12windows and their body/title identities inside its prefix.
        # Current32window pools live in appended storage; a truncation alone loses them.
        count=old['windowCount'];size=q['windowBytes']
        d[24+q['legacyWindows']:24+q['legacyWindows']+count*size]=raw[24+q['windows']:24+q['windows']+count*size]
        size=q['identityBytes']
        for slot in range(count):
            for oldslot,newslot in [(1+slot,1+slot),(1+count+slot,1+q['windowCount']+slot)]:
                dest=24+q['legacyIdentities']+oldslot*size;source=24+q['identities']+newslot*size
                d[dest:dest+size]=raw[source:source+size]
        struct.pack_into('<I',d,12,old['schema']);struct.pack_into('<I',d,28,old['schema']);struct.pack_into('<I',d,16,len(d)-24);struct.pack_into('<I',d,20,zlib.crc32(d[24:]));return d
    def test_old65_and_nested_new_mode_queue_rejects(self):
        s=self.scene();s.command({'op':'window','id':1});point=self.point(s,.2,.3,.5);s.restore(self.old65(s));self.assertEqual(self.point(s,.2,.3,.5),point)
        s.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'batch','commands':[{'op':'window','id':1,'sourceGeometry':True}]}});bad=self.old65(s);pure=s.snapshot()
        with self.assertRaises(ValueError):s.restore(bad)
        self.assertEqual(s.snapshot(),pure)
    def test_single_cell_axes_are_finite_and_canonical(self):
        for W,H in ((1,1),(1,20),(30,1)):
            s=self.scene();s.command({'op':'window','id':1,'effect':'window-transition/silk-dissolve','width':W,'height':H,'sourceGeometry':True})
            for u,v in ((0,0),(.5,.5),(1,1)):
                actual=self.point(s,u,v,.5);expected=[0 if W==1 else (u-.5)*W,0 if H==1 else (.5-v)*H,0,.5]
                for a,b in zip(actual,expected):self.assertAlmostEqual(a,b,delta=.0012)
    def test_original_cell_clip_and_early_roll_thresholds(self):
        s=self.scene();s.command({'op':'window','id':1,'effect':'window-transition/pocket-left','width':30,'height':20,'sourceGeometry':True})
        self.assertEqual(self.point(s,.2,.3,.5)[3],0);self.assertEqual(self.point(s,.83,.3,.5)[3],1)
        s.command({'op':'window','id':1,'effect':'window-transition/reel-up'})
        self.assertEqual(self.point(s,.2,.3,.079999)[3],0);self.assertAlmostEqual(self.point(s,.2,.3,.08)[3],.32,delta=.00001)
    def test_schedule_partial_flag_and_closed_window_ownership(self):
        s=self.scene();s.command({'op':'window','id':1,'effect':'window-transition/fragment-scatter','sourceGeometry':True,'seed':42})
        old=self.point(s,.2,.3,.5)
        s.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'window','id':1,'title':'Scheduled retained geometry'}})
        self.assertEqual(self.point(s,.2,.3,.5),old);initial=s.snapshot();s.advance_to(500000)
        self.assertTrue(s.info_complete()['windows'][0]['sourceGeometry']);self.assertEqual(self.point(s,.2,.3,.5),old)
        final=s.snapshot();s.restore(initial);s.advance_to(500000);self.assertEqual(s.snapshot(),final)
        s.command({'op':'window-action','id':1,'action':'close'});s.command({'op':'window-action','id':1,'action':'restore'})
        self.assertTrue(s.info_complete()['windows'][0]['sourceGeometry'])
    def test_full_window_capacity_rejects_without_losing_flags(self):
        s=self.scene()
        for i in range(1,33):s.command({'op':'window','id':i,'sourceGeometry':bool(i%2)})
        pure=s.snapshot()
        with self.assertRaises(ValueError):s.command({'op':'window','id':33,'sourceGeometry':True})
        self.assertEqual(s.snapshot(),pure)
        for row in s.info_complete()['windows']:self.assertEqual(row['sourceGeometry'],bool(row['id']%2))
    def test_source_window_flags_do_not_validate_widget_slots(self):
        s=self.scene();s.command({'op':'window','id':1,'sourceGeometry':True})
        s.command({'op':'indicator','id':1,'x':4,'y':5,'sequence':'abcd','stepMs':100})
        self.assertTrue(s.info_complete()['windows'][0]['sourceGeometry']);pure=s.snapshot();s.render();self.assertEqual(s.snapshot(),pure)
