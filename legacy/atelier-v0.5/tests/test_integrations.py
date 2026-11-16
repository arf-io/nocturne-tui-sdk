"""Interface/escape/host contracts. Specified before implementing these adapters."""
import unittest,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'bindings/python'),str(ROOT/'integrations')]
from tdfiglet_bridge import parseAnsi,commandFor
from afd_bridge import renderStatus,escapeTmux
from interaction import Dag,FocusModel,InputDecoder,KeyframeTrack
class IntegrationTests(unittest.TestCase):
 def testAnsiStyles(self):
  f=parseAnsi('\x1b[31mA\x1b[0mB\nC');self.assertEqual((f['width'],f['height']),(2,2));self.assertEqual(f['cells'][0],ord('A'));self.assertNotEqual(f['cells'][1],f['cells'][5])
 def testAnsiDiscardControls(self):
  f=parseAnsi('A\x1b]52;c;ZXhwbG9pdA==\x07B\x1b[2JC');self.assertEqual([f['cells'][i] for i in range(0,len(f['cells']),4)],[65,66,67])
 def testAnsiLimits(self):
  with self.assertRaises(ValueError):parseAnsi('x'*1000,maxWidth=20)
 def testSubprocessArgv(self):
  argv=commandFor('/usr/bin/tdfiglet','/tmp/a font.tdf',2,'hello; $(evil)',80);self.assertIsInstance(argv,list);self.assertIn('/tmp/a font.tdf',argv);self.assertEqual(argv[-1],'hello; $(evil)')
 def testTmuxEscape(self):
  self.assertEqual(escapeTmux('#(bad)%s'),'##(bad)%%s');self.assertNotIn('\x1b',escapeTmux('a\x1bb'))
 def testStatusDeterminism(self):
  a=renderStatus(2000,'smart-dark',40,'AFD #()');self.assertEqual(a,renderStatus(2000,'smart-dark',40,'AFD #()'));self.assertNotIn('\x1b',a);self.assertIn('##',a)
 def testDagParentsAndCycle(self):
  dag=Dag([1,2,3,4],[(1,3),(2,3),(3,4),(2,4)]);self.assertEqual(dag.parents(3),[1,2]);self.assertEqual(dag.ancestors(4),{1,2,3});self.assertEqual(dag.levels(),[[1,2],[3],[4]])
  with self.assertRaises(ValueError):Dag([1,2],[(1,2),(2,1)])
 def testFocusSkipsDisabledAndTrap(self):
  f=FocusModel([1,2,3],disabled={2});self.assertEqual(f.move(1),1);self.assertEqual(f.move(1),3);f.pushModal([9]);self.assertEqual(f.move(1),9);f.popModal();self.assertEqual(f.current,3)
 def testFragmentedInput(self):
  d=InputDecoder();self.assertEqual(d.feed(b'\x1b['),[]);self.assertEqual(d.feed(b'A'),[('key','up')]);self.assertEqual(d.feed('é'.encode()[:1]),[]);self.assertEqual(d.feed('é'.encode()[1:]),[('text','é')])
 def testMouse(self):
  d=InputDecoder();self.assertEqual(d.feed(b'\x1b[<0;12;4M'),[('mouse',(11,3,0))])
 def testPasteCannotInvokeActions(self):
  d=InputDecoder();self.assertEqual(d.feed(b'\x1b[200~x\x11\x03\x7f\x1b!\x1b[201~'),[('text','x'),('text','!')])
 def testKeyframe(self):
  t=KeyframeTrack([(0,0),(1000,1000),(2000,0)],easing=1);self.assertEqual(t.sample(0),0);self.assertEqual(t.sample(1000),1000);self.assertEqual(t.sample(3000),0);self.assertTrue(0<t.sample(500)<1000)
if __name__=='__main__':unittest.main()
