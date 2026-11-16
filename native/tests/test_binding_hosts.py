"""Binding ownership and actual framework integration, without terminal mocking of C."""
from pathlib import Path
import importlib.util
import sys
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene

class BindingOwnershipTests(unittest.TestCase):
    def test_python_ctypes_calls_are_serialized(self):
        with NativeScene() as scene:
            errors=[]
            def worker():
                try:
                    for _ in range(12):
                        scene.command({'op':'input','text':'a'})
                        frame=scene.render()
                        self.assertEqual(len(frame.bytes),frame.width*frame.height*16)
                        scene.snapshot()
                        scene.info()
                except Exception as error: errors.append(error)
            threads=[threading.Thread(target=worker) for _ in range(4)]
            for t in threads:t.start()
            for t in threads:t.join()
            self.assertEqual(errors,[])
            self.assertEqual(scene.info()['prompt']['text'],'a'*48)
    def test_batch_convenience_is_atomic(self):
        with NativeScene() as s:
            before=s.snapshot()
            with self.assertRaises(ValueError):s.batch([{'op':'input','text':'should roll back'},{'op':'unknown'}])
            self.assertEqual(before,s.snapshot())
    def test_schedule_convenience_is_native(self):
        with NativeScene() as s:
            s.schedule(1,8333,{'op':'input','text':'queued'})
            s.advance_to(8333)
            self.assertEqual(s.info()['prompt']['text'],'queued')

class PromptToolkitHostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:import prompt_toolkit
        except ImportError:raise unittest.SkipTest('prompt_toolkit not installed; framework gate must report BLOCKED')
        spec=importlib.util.spec_from_file_location('nocturne_prompt_host',ROOT/'hosts/python/prompt_toolkit_host.py')
        cls.host=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.host)
    def test_control_copies_cells_and_is_pure_at_stable_size(self):
        with NativeScene() as s:
            control=self.host.NativeControl(s);content=control.create_content(80,24)
            before=s.snapshot();content=control.create_content(80,24)
            self.assertEqual(before,s.snapshot())
            self.assertEqual(content.line_count,24)
            for i in range(24):self.assertEqual(sum(len(text) for _,text in content.get_line(i)),80)
    def test_width_fallback_does_not_shift_neighbor_cells(self):
        self.assertEqual(self.host.cell_symbol(ord('A')),'A')
        self.assertEqual(self.host.cell_symbol(0x0301),'\ufffd')
        self.assertEqual(self.host.cell_symbol(0x1f601),'\ufffd')
    def test_framework_construction_and_native_mouse_route(self):
        from prompt_toolkit.input import create_pipe_input
        from prompt_toolkit.output import DummyOutput
        from prompt_toolkit.mouse_events import MouseEvent,MouseEventType,MouseButton
        from prompt_toolkit.data_structures import Point
        with create_pipe_input() as input:
            host=self.host.FrameworkHost(input=input,output=DummyOutput())
            try:
                host.control.create_content(100,35)
                before=host.scene.info()['fieldCount']
                for phase,pos in [(MouseEventType.MOUSE_DOWN,Point(50,12)),(MouseEventType.MOUSE_MOVE,Point(59,15)),(MouseEventType.MOUSE_UP,Point(59,15))]:
                    host.control.mouse_handler(MouseEvent(pos,phase,MouseButton.LEFT,frozenset()))
                self.assertEqual(before,host.scene.info()['fieldCount'])
            finally:host.scene.close()
