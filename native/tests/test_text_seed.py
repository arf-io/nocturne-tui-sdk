"""Real upper-half alphabet source contracts, authored before native extension."""
import ctypes as C,hashlib,json,struct,sys,unittest,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class TextSeed(unittest.TestCase):
    def scene(self):
        s=NativeScene(2030);self.addCleanup(s.close);return s
    def glyph(self,s,index):
        fn=s._lib.nrTextSample;fn.argtypes=[C.c_void_p,C.c_uint32,C.c_uint32,C.POINTER(C.c_int32),C.c_uint32];fn.restype=C.c_int
        out=(C.c_int32*8)();self.assertEqual(fn(s._context,1,index,out,8),0);return out[0]
    def test_original_uint32_seed_glyphs_both_families_phases_replay(self):
        f=json.loads((ROOT/'tests/fixtures/text-seed-reference.json').read_text());seen_tail=False
        for path,h in f['sources'].items():self.assertEqual(hashlib.sha256((ROOT.parent/path).read_bytes()).hexdigest(),h)
        for row in f['rows']:
            with self.subTest(id=row['id'],phase=row['phase'],seed=row['seed']):
                s=self.scene();s.command({'op':'text','id':1,'text':'NODE','effect':row['id'],'phase':row['phase'],**row['config']});initial=s.snapshot();frames=[]
                for us,expected in zip(f['times'],row['poses']):
                    s.advance_to(us);pure=s.snapshot();actual=[self.glyph(s,i) for i in range(4)];self.assertEqual(actual,expected)
                    seen_tail|=any(g>=0x480 for g in actual);frames.append(s.render().bytes);self.assertEqual(s.snapshot(),pure)
                final=s.snapshot();s.restore(initial)
                for us,frame in zip(f['times'],frames):s.advance_to(us);self.assertEqual(s.render().bytes,frame)
                self.assertEqual(s.snapshot(),final)
        self.assertTrue(seen_tail,'reference must actually exercise alphabet indices beyond127')
    def test_invalid_seed_is_atomic(self):
        s=self.scene();s.command({'op':'text','id':1,'text':'X','seed':42})
        for seed in (-1,4294967296,.5,True,'42'):
            pure=s.snapshot()
            with self.subTest(seed=seed),self.assertRaises(ValueError):s.command({'op':'text','id':1,'seed':seed})
            self.assertEqual(s.snapshot(),pure)
    def old64(self,s):
        d=bytearray(s.snapshot()[:13578952]);struct.pack_into('<I',d,12,0x20261064);struct.pack_into('<I',d,28,0x20261064);struct.pack_into('<I',d,16,len(d)-24);struct.pack_into('<I',d,20,zlib.crc32(d[24:]));return d
    def test_old64_rejects_nested_highseed_queue(self):
        s=self.scene();s.command({'op':'text','id':1,'text':'X','effect':'text/cipher-resolve','alphabet':'ABC'});frame=s.render().bytes;s.restore(self.old64(s));self.assertEqual(s.render().bytes,frame)
        s.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'batch','commands':[{'op':'text','id':1,'seed':4294967295}]}});bad=self.old64(s);pure=s.snapshot()
        with self.assertRaises(ValueError):s.restore(bad)
        self.assertEqual(s.snapshot(),pure)
