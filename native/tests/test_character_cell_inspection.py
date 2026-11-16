"""Explicit-render owner inspection, stale frame rejection and pure copied data."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class CharacterCellInspection(unittest.TestCase):
 def test_explicit_render_metadata_staleness_and_purity(self):
  with NativeScene(42) as s:
   with self.assertRaises(RuntimeError):s.inspect_character_cell(0,0)
   s.command({'op':'character-region','region':{'id':'fragment','path':'/app/fragment','role':'user-text','state':'selected','cells':[0],'indices':[9]}})
   frame=s.render();before=s.snapshot();info=s.inspect_character_cell(0,0)
   self.assertEqual((info['role'],info['state'],info['path'],info['index']),('user-text','selected','/app/fragment',9))
   self.assertEqual(info['glyph'],int.from_bytes(frame.bytes[:4],'little'));self.assertEqual(info['id'],int.from_bytes(frame.bytes[12:16],'little'))
   for _ in range(4):self.assertEqual(s.inspect_character_cell(0,0),info)
   self.assertEqual(before,s.snapshot())
   with self.assertRaises(ValueError):s.inspect_character_cell(-1,0)
   with self.assertRaises(ValueError):s.command({'op':'character-rule','rule':{'id':''}})
   self.assertEqual(s.inspect_character_cell(0,0),info)
   s.command({'op':'pause','paused':True})
   with self.assertRaises(RuntimeError):s.inspect_character_cell(0,0)
   s.render();self.assertEqual(s.inspect_character_cell(0,0),info)
   s.restore(before)
   with self.assertRaises(RuntimeError):s.inspect_character_cell(0,0)
   s.render();self.assertEqual(s.inspect_character_cell(0,0),info)
