from pathlib import Path
import importlib.util,sys,unittest
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'));sys.path.insert(0,str(ROOT/'hosts/python'))
from nocturne_native import NativeScene
from prompt_toolkit_host import FrameworkHost
spec=importlib.util.spec_from_file_location('scene_terminal',ROOT/'examples/terminal.py');terminal=importlib.util.module_from_spec(spec);spec.loader.exec_module(terminal)
class SceneDocument(unittest.TestCase):
 def hosts(self):
  for cls in [terminal.Host,FrameworkHost]:
   scene=NativeScene();self.addCleanup(scene.close);host=cls.__new__(cls);host.scene=scene;host.recipes=[dict(id='next',commands=[dict(op='draft',text='recipe document',caret=3,emitWeather=False)])];host.current=0;host.document_loaded=True
   host.args=SimpleNamespace(seed=2030);host.paused=True;host.size=lambda:(80,24);host.seed=2030;host.reduced_motion=False;host.control=SimpleNamespace(viewport=None,unicode_view=None)
   yield host
 def testSceneSwitchPreservesUnicodeAndInteriorCaret(self):
  for host in self.hosts():
   host.scene.command(dict(op='draft',text='é\n日本',caret=2,emitWeather=False));host.load('next');prompt=host.scene.info()['prompt'];self.assertEqual((prompt['text'],prompt['caret']),('é\n日本',2))
 def testAcceptedEmptyDocumentOverridesSceneDemonstration(self):
  for host in self.hosts():
   host.scene.command(dict(op='draft',text='',caret=0,emitWeather=False));host.load('next');prompt=host.scene.info()['prompt'];self.assertEqual((prompt['text'],prompt['caret']),('',0))
 def testSceneSwitchRetainsModeRevisionAndUndo(self):
  for host in self.hosts():
   host.recipes[0]['commands'].insert(0,dict(op='prompt',mode='grow'))
   host.scene.command(dict(op='prompt',mode='vim-full'));host.scene.command(dict(op='draft',text='é日本',caret=2,emitWeather=False));host.scene.command(dict(op='key',key='i'));host.scene.command(dict(op='paste',text='X'));host.scene.command(dict(op='key',key='Escape'));before=host.scene.info()['prompt']
   host.load('next');after=host.scene.info()['prompt']
   for key in ['text','caret','mode','vimMode','revision']:self.assertEqual(after[key],before[key],key)
   host.scene.command(dict(op='key',key='u'));prompt=host.scene.info()['prompt'];self.assertEqual((prompt['text'],prompt['caret']),('é日本',2))
 def testInitialSceneMayAuthorDemonstrationDocument(self):
  for host in self.hosts():
   host.document_loaded=False;host.load('next');prompt=host.scene.info()['prompt'];self.assertEqual((prompt['text'],prompt['caret']),('recipe document',3))
if __name__=='__main__':unittest.main()
