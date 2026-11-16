"""Native retained colored cell art, composition, atomic validation and replay."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
from native.tests.current_writer_contract import current_schema, snapshot_size
import struct,zlib,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
class CellArt(unittest.TestCase):
 def setUp(self):self.s=NativeScene();self.addCleanup(self.s.close)
 def test_exact_colors_alpha_update_and_purity(self):
  self.s.command(dict(op='cell-art',id=1,x=2,y=2,width=2,height=1,cells=[[65,0xff0000,0x0000ff],[0x2588,0x00ff00,0]],layer='overlay'))
  saved=self.s.snapshot();f=self.s.render();self.assertEqual(f.words()[2*f.width+2][:3],(65,0xff0000,0x0000ff));self.assertEqual(f.words()[2*f.width+3][:2],(0x2588,0x00ff00));self.assertEqual(self.s.snapshot(),saved)
  self.s.command(dict(op='cell-art',id=1,x=5,alpha=0));self.assertNotEqual(self.s.snapshot(),saved)
  self.s.restore(saved);self.assertEqual(self.s.render().bytes,f.bytes)
 def test_validation_and_lifetime(self):
  for cells in [[[65,0xff0000,0]],[[0xd800,0,0]],[[65,-1,0]],[[65,0,0,1]]]:
   saved=self.s.snapshot()
   with self.assertRaises(ValueError):self.s.command(dict(op='cell-art',id=1,width=2,height=1,cells=cells))
   self.assertEqual(saved,self.s.snapshot())
  self.s.command(dict(op='cell-art',id=1,width=1,height=1,cells=[[65,1,2]]));self.s.command(dict(op='remove-cell-art',id=1));self.s.command(dict(op='remove-cell-art',id=1))
 def test_schema30_promotion_and_corrupt_restore(self):
  self.s.command(dict(op='cell-art',id=1,width=1,height=1,cells=[[65,1,2]]));saved=self.s.snapshot()
  old=bytearray(saved[:24+5167936]);struct.pack_into('<I',old,12,0x20261030);struct.pack_into('<I',old,24+4,0x20261030);struct.pack_into('<I',old,16,5167936);struct.pack_into('<I',old,20,zlib.crc32(old[24:]));self.s.restore(old)
  self.assertNotIn('cellArt',self.s.info());self.assertEqual(int.from_bytes(self.s.snapshot()[12:16],'little'),current_schema())
  bad=bytearray(saved);struct.pack_into('<i',bad,24+5167936+8,2147483647);struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]));before=self.s.snapshot()
  with self.assertRaises(ValueError):self.s.restore(bad)
  self.assertEqual(before,self.s.snapshot())
 def test_scheduled_pose_and_resource_capacity(self):
  for id in range(1,5):self.s.command(dict(op='cell-art',id=id,width=1,height=1,cells=[[65,1,2]]))
  before=self.s.snapshot()
  with self.assertRaises(ValueError):self.s.command(dict(op='cell-art',id=5,width=1,height=1,cells=[[65,1,2]]))
  self.assertEqual(before,self.s.snapshot())
  self.s.command(dict(op='schedule',id=1,atUs=100000,command=dict(op='cell-art',id=1,x=10,alpha=.5)))
  start=self.s.snapshot();self.s.advance_to(200000);final=self.s.snapshot();self.assertEqual(self.s.info()['cellArt'][0]['x'],10)
  self.s.restore(start);self.s.advance_to(50000);self.s.advance_to(200000);self.assertEqual(final,self.s.snapshot())
 def test_complete_cell_capacity_and_transparent_padding(self):
  self.s.command(dict(op='cell-art',id=1,width=2048,height=1,cells=[[65,1,2]]*2048))
  self.assertEqual(len(self.s.info()['cellArt'][0]['cells']),2048)
  self.s.command(dict(op='remove-cell-art',id=1));before=self.s.render().bytes
  self.s.command(dict(op='cell-art',id=1,width=1,height=1,cells=[[0,0xffffff,0xffffff]],layer='overlay'))
  self.assertEqual(before,self.s.render().bytes)
 def test_layer_order_background_then_ui_then_overlay(self):
  self.s.command(dict(op='text',id=1,text='B',local=True,x=2,y=2))
  self.s.command(dict(op='cell-art',id=1,width=1,height=1,x=2,y=2,cells=[[65,1,2]],layer='background'))
  frame=self.s.render();self.assertEqual(frame.words()[2*frame.width+2][0],66)
  self.s.command(dict(op='cell-art',id=1,layer='overlay'));frame=self.s.render();self.assertEqual(frame.words()[2*frame.width+2][0],65)
if __name__=='__main__':unittest.main()
