"""Execute restored original layers together through the public native SDK."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'));sys.path.insert(0,str(ROOT/'examples'))
from nocturne_native import NativeScene
class OriginalComposedScenes(unittest.TestCase):
 def cases(self):
  from original_composition_studies import build_original_composition_studies
  return build_original_composition_studies()
 def scene(self,case):
  s=NativeScene(2030);self.addCleanup(s.close)
  for command in case['commands']:s.command(command)
  return s
 def test_real_composition_cases_expose_original_weather_and_layers(self):
  cases=self.cases();self.assertEqual({q['inputWeather']for q in cases},{'embers','sparks','nova','rain','snow','ripples'})
  for q in cases:
   self.assertEqual(q['demonstrates']['feature'],'original-composition')
   self.assertTrue(q['provenance']['componentSources'])
   s=self.scene(q);info=s.info_complete()
   self.assertIsNotNone(info['windowApplication']);self.assertGreaterEqual(len(info['windows']),3)
   s.command(dict(op='draft',text='Local input is immediate'));self.assertEqual(s.info()['prompt']['text'],'Local input is immediate')
   info=s.info_complete();self.assertEqual(info['windowApplication']['weatherStyle'],q['inputWeather'])
   self.assertGreater(len(info['windowApplication']['events']),0)
   self.assertEqual(info['windowApplication']['events'][-1]['kind'],q['inputWeather'])
 def test_original_incoming_fade_runs_over_live_composition_without_delaying_local_input(self):
  for case in self.cases():
   s=self.scene(case);s.command(dict(op='draft',text='Local text'))
   for action in case['actions']:
    if action['timeUs']>500000:break
    s.advance_to(action['timeUs']);s.command(action['command'])
   start=s.text_sample(41,0)[5];s.advance_to(1100000);middle=s.text_sample(41,0)[5];a=s.render().bytes;s.advance_to(2500000);end=s.text_sample(41,0)[5];b=s.render().bytes
   self.assertEqual(start,0);self.assertGreater(middle,start);self.assertEqual(end,1000000)
   self.assertNotEqual(a,b)
   # The arrival is actually visible in the uncovered source text band.
   words=s.render().words();self.assertEqual(''.join(chr(words[5*136+5+i][0])for i in range(29)),'Incoming text / original fade')
   self.assertTrue(any(word[3]&0xffff0000==0x20000000 for word in words),'real window cells remain')
   self.assertGreater(len({word[2]for word in words[:136*5]}),3,'animated background colors remain visible')
   self.assertEqual(s.info()['prompt']['text'],'Local text')
   before=s.snapshot();s.render();s.render();self.assertEqual(s.snapshot(),before)
if __name__=='__main__':unittest.main()
