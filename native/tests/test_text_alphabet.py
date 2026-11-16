"""Real upper-half alphabet source contracts, authored before native extension."""
import ctypes as C,hashlib,json,struct,sys,unittest,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class TextAlphabet(unittest.TestCase):
    def scene(self):
        s=NativeScene(2030);self.addCleanup(s.close);return s
    def glyph(self,s,index):
        fn=s._lib.nrTextSample;fn.argtypes=[C.c_void_p,C.c_uint32,C.c_uint32,C.POINTER(C.c_int32),C.c_uint32];fn.restype=C.c_int
        out=(C.c_int32*8)();self.assertEqual(fn(s._context,1,index,out,8),0);return out[0]
    def test_original_128_129_256_glyphs_both_families_phases_replay(self):
        f=json.loads((ROOT/'tests/fixtures/text-alphabet-reference.json').read_text());seen_tail=False
        for path,h in f['sources'].items():self.assertEqual(hashlib.sha256((ROOT.parent/path).read_bytes()).hexdigest(),h)
        for row in f['rows']:
            with self.subTest(id=row['id'],phase=row['phase'],size=row['size']):
                s=self.scene();s.command({'op':'text','id':1,'text':'NODE','effect':row['id'],'phase':row['phase'],**row['config']});initial=s.snapshot();frames=[]
                for us,expected in zip(f['times'],row['poses']):
                    s.advance_to(us);pure=s.snapshot();actual=[self.glyph(s,i) for i in range(4)];self.assertEqual(actual,expected)
                    seen_tail|=any(g>=0x480 for g in actual);frames.append(s.render().bytes);self.assertEqual(s.snapshot(),pure)
                final=s.snapshot();s.restore(initial)
                for us,frame in zip(f['times'],frames):s.advance_to(us);self.assertEqual(s.render().bytes,frame)
                self.assertEqual(s.snapshot(),final)
        self.assertTrue(seen_tail,'reference must actually exercise alphabet indices beyond127')
    def test_invalid_alphabet_is_atomic(self):
        s=self.scene();s.command({'op':'text','id':1,'text':'X','alphabet':'ABC'})
        for alphabet in ('','A'*257,'A\nB','A\x7fB','\ud800',True):
            pure=s.snapshot()
            with self.subTest(alphabet=repr(alphabet)),self.assertRaises((ValueError,UnicodeEncodeError)):s.command({'op':'text','id':1,'alphabet':alphabet})
            self.assertEqual(s.snapshot(),pure)
    def test_upper_half_retained_by_partial_edit_and_cleared_on_reuse(self):
        s=self.scene();alphabet=''.join(chr(0x400+i) for i in range(256))
        s.command({'op':'text','id':1,'text':'NODE','effect':'text/static-resolve','alphabet':alphabet,'durationMs':1000,'staggerMs':0,'variation':0,'seed':42})
        s.advance_to(137000);before=[self.glyph(s,i) for i in range(4)]
        s.command({'op':'text','id':1,'x':10});self.assertEqual([self.glyph(s,i) for i in range(4)],before)
        s.command({'op':'clear','scope':'text'});s.command({'op':'text','id':1,'text':'X','effect':'text/direct-ink','alphabet':'Z'});self.assertEqual(self.glyph(s,0),ord('X'))
    def old63(self,s):
        d=bytearray(s.snapshot()[:13566664]);struct.pack_into('<I',d,12,0x20261063);struct.pack_into('<I',d,28,0x20261063);struct.pack_into('<I',d,16,len(d)-24);struct.pack_into('<I',d,20,zlib.crc32(d[24:]));return d
    def test_old63_preserves_short_alphabet_rejects_nested_extended_queue(self):
        s=self.scene();s.command({'op':'text','id':1,'text':'X','effect':'text/cipher-resolve','alphabet':'ABC'});frame=s.render().bytes;s.restore(self.old63(s));self.assertEqual(s.render().bytes,frame)
        s.command({'op':'schedule','id':1,'atUs':500000,'command':{'op':'batch','commands':[{'op':'text','id':1,'alphabet':'A'*129}]}});bad=self.old63(s);pure=s.snapshot()
        with self.assertRaises(ValueError):s.restore(bad)
        self.assertEqual(s.snapshot(),pure)
