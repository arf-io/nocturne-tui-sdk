"""Real event routing, native rejected typed references and legacy conditions."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class AppearanceEventContract(unittest.TestCase):
    def setup_scene(self,s):
        for c in [{'op':'widget','id':1,'kind':'text','text':'Owned source','alpha':.2},
            {'op':'state-register','id':21,'path':'/view','role':'control','target':{'family':'widget','id':1}},
            {'op':'define','path':'/ready','value':False},
            {'op':'define','path':'/level','value':0},
            {'op':'trigger','id':1,'target':'/ready','event':'/host/ready','whenExpression':True,'expression':{'intentPath':'/ready'}},
            {'op':'style-rule','id':1,'selector':{'family':'widget','id':1},'whenExpression':{'path':'/ready'},'style':{'alpha':.8}}]:s.command(c)
    def test_event_route_retains_source_purity_and_exact_replay(self):
        with NativeScene() as s:
            self.setup_scene(s);start=s.snapshot()
            def run():
                for ready,alpha in [(True,.8),(False,.2)]:
                    s.command({'op':'emit-intent','event':'/host/ready','payload':{'ready':ready}})
                    self.assertEqual(s.info_complete()['registeredStates'][0]['effective']['alpha'],alpha)
                    before=s.snapshot();s.render();s.info_complete();self.assertEqual(s.snapshot(),before)
            run();final=s.snapshot();frame=s.render().bytes;s.restore(start);run()
            self.assertEqual(s.snapshot(),final);self.assertEqual(s.render().bytes,frame)
    def test_nested_event_references_reject_but_literal_data_and_conditions_survive(self):
        with NativeScene() as s:
            self.setup_scene(s)
            for expression in [{'equal':[{'intentField':'value'},1]},
                {'if':{'condition':False,'then':{'intentPath':'/ready'},'else':True}},
                {'equal':[{'object':{'x':{'intentField':'id'}}},{'literal':{'x':1}}]}]:
                before=s.snapshot()
                with self.assertRaisesRegex(ValueError,'Invalid typed appearance guard'):
                    s.command({'op':'style-rule','id':2,'selector':{'family':'widget','id':1},'whenExpression':expression,'style':{'alpha':.8}})
                self.assertEqual(s.snapshot(),before)
            payload={'intentField':'id','intentPath':'/ready'}
            s.command({'op':'style-rule','id':2,'selector':{'family':'widget','id':1},'whenExpression':{'equal':[{'literal':payload},{'literal':payload}]},'style':{'alpha':.6}})
            s.advance_to(1);self.assertEqual(s.info_complete()['registeredStates'][0]['effective']['alpha'],.6)
            for condition in [{'intentValue':{'comparison':'above','value':0}},{'not':{'intentValue':{'comparison':'above','value':0}}}]:
                before=s.snapshot()
                with self.assertRaisesRegex(ValueError,'State invariant rejected'):
                    s.command({'op':'style-rule','id':2,'selector':{'family':'widget','id':1},'when':condition,'style':{'alpha':.6}})
                self.assertEqual(s.snapshot(),before)
            for condition,expected in [({'path':'/level','comparison':'above','value':0},.2),({'not':{'path':'/level','comparison':'above','value':0}},.6)]:
                s.command({'op':'style-rule','id':2,'selector':{'family':'widget','id':1},'when':condition,'style':{'alpha':.6}})
                s.advance_to(s.info_complete()['clock']['timeUs']+1)
                self.assertEqual(s.info_complete()['registeredStates'][0]['effective']['alpha'],expected)
