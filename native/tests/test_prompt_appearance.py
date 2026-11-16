"""Prompt appearance uses real native commands, rendering and snapshots."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import unittest,sys,struct,zlib,gzip,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
from native.tests.current_writer_contract import current_schema
class PromptAppearance(unittest.TestCase):
 def scene(self):
  s=NativeScene();s.command({'op':'resize','width':80,'height':28});s.command({'op':'environment','stars':0});s.command({'op':'prompt','active':True});return s
 def test_runtime_build_matches_release_identity(self):
  release=json.loads((ROOT.parent/'RELEASE.json').read_text())
  with self.scene() as scene:self.assertEqual(scene.info()['build'],release['build'])
 def test_custom_cursor_blink_color_and_snapshot(self):
  with self.scene() as s:
   s.command({'op':'prompt-appearance','cursor':{'shape':'custom','glyph':'◆','color':'#ee8844','blinkMs':800,'duty':.5,'colorMode':'fixed'}})
   s.command({'op':'draft','text':'abc','emitWeather':False});m=s.info()['prompt']['appearance'];self.assertEqual(m['cursor']['glyph'],'◆');self.assertEqual(m['cursor']['color'],'#ee8844')
   f=s.render();cells=list(struct.iter_unpack('<4I',f.bytes));self.assertEqual(sum(c[0]==0x25c6 and c[1]==0xee8844 for c in cells),1)
   saved=s.snapshot();self.assertEqual(s.render().bytes,f.bytes);self.assertEqual(s.snapshot(),saved)
   s.advance_to(500000);self.assertFalse(any(c[0]==0x25c6 for c in struct.iter_unpack('<4I',s.render().bytes)))
   s.restore(saved);self.assertEqual(s.render().bytes,f.bytes)
 def test_weather_ordinary_prompt_without_window_application(self):
  with self.scene() as s:
   s.command({'op':'prompt-appearance','weather':{'style':'snow','intensity':.8,'lifeMs':1800,'speed':8,'paste':'each'}})
   s.command({'op':'input','text':'a界'});info=s.info();self.assertFalse(info.get('windowApplication'));self.assertEqual(info['prompt']['text'],'a界');self.assertEqual(info['prompt']['appearance']['weather']['eventCount'],2)
   saved=s.snapshot();frame=s.render().bytes;s.advance_to(120000);self.assertNotEqual(s.render().bytes,frame);self.assertEqual(s.info()['prompt']['text'],'a界');s.restore(saved);self.assertEqual(s.render().bytes,frame)
   s.command({'op':'draft','text':'a界x','emitWeather':False});self.assertEqual(s.info()['prompt']['appearance']['weather']['eventCount'],2)
 def test_invalid_patch_is_atomic(self):
  with self.scene() as s:
   s.command({'op':'prompt-appearance','cursor':{'shape':'bar'}});before=s.snapshot()
   for q in [{'cursor':{'glyph':'ab'}},{'cursor':{'blinkMs':-1}},{'cursor':{'color':'red'}},{'weather':{'style':'hurricane'}},{'weather':{'lifeMs':0}},{'cursor':{'unknown':1}}]:
    with self.subTest(patch=q):
     with self.assertRaises(ValueError):s.command({'op':'prompt-appearance',**q})
     self.assertEqual(s.snapshot(),before)
 def test_source_and_framed_prompts_use_one_custom_cursor(self):
  for mode in ['source','framed','compact']:
   with self.subTest(mode=mode),self.scene() as s:
    if mode=='source':s.command({'op':'prompt-source','values':{'stars':0}})
    elif mode=='framed':s.command({'op':'prompt','presentation':'framed','active':True})
    s.command({'op':'prompt-appearance','cursor':{'shape':'custom','glyph':'◆','color':'#abcdef','blinkMs':0}});s.command({'op':'draft','text':'cursor','emitWeather':False})
    self.assertEqual(sum(c[0]==0x25c6 and c[1]==0xabcdef for c in struct.iter_unpack('<4I',s.render().bytes)),1)
 def test_window_application_uses_custom_caret_and_hides_it_during_blink(self):
  sys.path.insert(0,str(ROOT.parent))
  from native.tests.test_rc2_window_application import application_commands
  from native.tests.test_original_atelier_windows import commands as atelier_commands
  for scene_commands in [application_commands(),atelier_commands()]:
   with NativeScene(2030) as scene:
    for command in scene_commands:scene.command(command)
    scene.command({'op':'draft','text':'文abcdef','caret':2,'emitWeather':False})
    scene.command({'op':'prompt-appearance','cursor':{'shape':'custom','glyph':'◆','color':'#ee8844','blinkMs':800,'duty':.5}})
    frame=scene.render();cells=list(struct.iter_unpack('<4I',frame.bytes));at=(frame.height-4)*frame.width+7
    self.assertEqual(cells[at][:2],(0x25c6,0xee8844));self.assertEqual(sum(c[0]==0x25c6 and c[1]==0xee8844 for c in cells),1)
    saved=scene.snapshot();scene.advance_to(500000)
    self.assertFalse(any(c[0]==0x25c6 and c[1]==0xee8844 for c in struct.iter_unpack('<4I',scene.render().bytes)))
    scene.restore(saved);self.assertEqual(scene.render().bytes,frame.bytes)
 def test_weather_is_visible_on_all_prompt_presentations(self):
  for presentation in ['compact','framed','source']:
   with self.subTest(presentation=presentation),self.scene() as live,self.scene() as quiet:
    for scene in [live,quiet]:
     if presentation=='source':scene.command({'op':'prompt-source','values':{'stars':0}})
     elif presentation=='framed':scene.command({'op':'prompt','presentation':'framed','active':True})
     scene.command({'op':'prompt-appearance','weather':{'style':'snow','intensity':1,'speed':12}})
    live.command({'op':'draft','text':'snow','emitWeather':True});quiet.command({'op':'draft','text':'snow','emitWeather':False})
    live.advance_to(180000);quiet.advance_to(180000);self.assertNotEqual(hashlib.sha256(live.render().bytes).hexdigest(),hashlib.sha256(quiet.render().bytes).hexdigest())
 def test_genuine_schema95_migration_and_bad_cursor_footer(self):
  fixture=ROOT/'tests/fixtures/prompt-appearance/schema95';record=json.loads((fixture/'manifest.json').read_text());raw=gzip.decompress((fixture/'snapshot.gz').read_bytes());expected=gzip.decompress((fixture/'frame.gz').read_bytes())
  self.assertEqual(hashlib.sha256(raw).hexdigest(),record['snapshotSha256']);self.assertEqual(struct.unpack_from('<I',raw,12)[0],0x20261095)
  with self.scene() as s:
   s.restore(raw);self.assertEqual(s.info()['prompt']['text'],record['text']);self.assertEqual(s.info()['prompt']['appearance']['cursor']['shape'],'inherit');self.assertEqual(s.render().bytes,expected);self.assertEqual(struct.unpack_from('<I',s.snapshot(),12)[0],current_schema())
   s.command({'op':'prompt-appearance','cursor':{'shape':'custom','glyph':'◆'}});before=s.snapshot();bad=bytearray(before);struct.pack_into('<I',bad,24+30499744+4,999);struct.pack_into('<I',bad,20,zlib.crc32(bad[24:]))
   with self.assertRaises(ValueError):s.restore(bad)
   self.assertEqual(s.snapshot(),before)
 def test_every_explicit_weather_style_paints_visible_pixels(self):
  for style in ['embers','sparks','nova','rain','snow','ripples']:
   with self.subTest(style=style),self.scene() as scene:
    scene.command({'op':'prompt-appearance','weather':{'style':style,'intensity':1}})
    scene.command({'op':'input','text':style});scene.advance_to(150000)
    self.assertGreater(scene.info()['prompt']['appearance']['weather']['eventCount'],0)
    painted=hashlib.sha256(scene.render().bytes).hexdigest()
    scene.command({'op':'prompt-appearance','weather':{'style':'off'}})
    self.assertNotEqual(hashlib.sha256(scene.render().bytes).hexdigest(),painted)
 def test_paste_policy_uses_actual_origin_including_one_scalar(self):
  for text in ['🌿','界é']:
   for policy in ['off','burst','each']:
    with self.subTest(text=text,policy=policy),self.scene() as scene:
     scene.command({'op':'prompt-appearance','weather':{'style':'snow','paste':policy}})
     scene.command({'op':'paste','text':text})
     expected=0 if policy=='off' else 1 if policy=='burst' else len(text)
     self.assertEqual(scene.info()['prompt']['appearance']['weather']['eventCount'],expected)
     self.assertEqual(scene.info()['prompt']['text'],text)
     serial=scene.info()['prompt']['appearance']['weather']['eventSerial']
     scene.command({'op':'input','text':'a界'})
     self.assertEqual(scene.info()['prompt']['appearance']['weather']['eventSerial'],serial+2)
 def test_paste_policy_and_reduced_motion(self):
  with self.scene() as s:
   s.command({'op':'prompt-appearance','weather':{'style':'rain','paste':'burst'},'cursor':{'shape':'custom','glyph':'◆','color':'#ff0000','secondaryColor':'#0000ff','colorMode':'pulse','colorPeriodMs':1000,'blinkMs':0}})
   s.command({'op':'paste','text':'paste'});self.assertEqual(s.info()['prompt']['appearance']['weather']['eventCount'],1)
   frame=s.render().bytes;s.advance_to(250000);self.assertNotEqual(s.render().bytes,frame)
if __name__=='__main__':unittest.main()
