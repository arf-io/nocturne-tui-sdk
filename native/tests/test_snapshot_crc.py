"""Actual native CRC versus independent zlib; authored before optimization."""
import ctypes as C,os,sys,unittest,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class SnapshotCRC(unittest.TestCase):
    def setUp(self):
        self.scene=NativeScene(2030,library=os.environ.get('NOCTURNE_TEST_LIBRARY'));self.addCleanup(self.scene.close)
        self.fn=self.scene._lib.nrCrc;self.fn.argtypes=[C.c_void_p,C.c_uint32];self.fn.restype=C.c_uint32
    def test_all_byte_values_offsets_block_tails_and_large_corpus(self):
        corpus=bytes(range(256))*32;buffer=C.create_string_buffer(corpus)
        lengths=list(range(130))+[255,256,257,511,512,513,1023,1024,1025,4095,4096,4097]
        for offset in range(16):
            for length in lengths:
                with self.subTest(offset=offset,length=length):self.assertEqual(self.fn(C.addressof(buffer)+offset,length),zlib.crc32(corpus[offset:offset+length]))
        self.assertEqual(self.fn(None,0),0)
        golden=C.create_string_buffer(b'123456789');self.assertEqual(self.fn(golden,9),0xcbf43926)
        data=bytes(range(256))*53043;large=C.create_string_buffer(data);self.assertEqual(self.fn(large,len(data)),zlib.crc32(data))
    def test_actual_snapshot_wire_crc_restore_replay_and_atomic_corruption(self):
        s=self.scene;s.command({'op':'draft','text':'CRC é中','emitWeather':False});s.command({'op':'widget','id':1,'kind':'progress','value':1e-7});s.advance_to(250000)
        data=s.snapshot();self.assertEqual(int.from_bytes(data[20:24],'little'),zlib.crc32(data[24:]))
        frame=s.render().bytes;s.restore(data);self.assertEqual(s.snapshot(),data);self.assertEqual(s.render().bytes,frame)
        bad=bytearray(data);bad[-1]^=1
        with self.assertRaises(ValueError):s.restore(bad)
        self.assertEqual(s.snapshot(),data)
