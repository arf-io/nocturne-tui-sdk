import importlib.util,pathlib,math,struct,unittest
ROOT=pathlib.Path(__file__).resolve().parents[2];spec=importlib.util.spec_from_file_location('audio',ROOT/'sensors/audio_sensors.py');audio=importlib.util.module_from_spec(spec);spec.loader.exec_module(audio)
class AudioTests(unittest.TestCase):
 def testKnownSignal(self):
  a=audio.blockFeatures(struct.pack('<512f',*([0,1,0,-1]*128)));self.assertAlmostEqual(a[0],math.sqrt(.5));self.assertEqual(a[1],1);self.assertEqual(len(a[2]),128)
 def testSilence(self):self.assertEqual(audio.blockFeatures(bytes(2048))[:2],(0,0))
 def testInvalidNeverBecomesSilence(self):
  with self.assertRaises(ValueError):audio.blockFeatures(b'bad')
  with self.assertRaises(ValueError):audio.blockFeatures(struct.pack('<2f',float('nan'),1))
if __name__=='__main__':unittest.main()
