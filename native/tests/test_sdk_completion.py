"""Current-contract regressions; assertions test behavior, not accepted screenshots."""
import json, sys, unittest, struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class CompletionTests(unittest.TestCase):
    def setUp(self): self.s=NativeScene(42)
    def tearDown(self): self.s.close()
    def cmd(self,op,**kw): return self.s.command(dict(op=op,**kw))
    def test_atomic_batch_success(self):
        self.cmd('batch',commands=[{'op':'define','path':'/a','value':1},{'op':'set','path':'/a','value':2},{'op':'input','text':'ink'}])
        self.assertEqual(self.s.info()['values']['/a'],2);self.assertEqual(self.s.info()['prompt']['text'],'ink')
    def test_atomic_batch_rollback(self):
        before=self.s.snapshot()
        with self.assertRaises(ValueError):self.cmd('batch',commands=[{'op':'input','text':'no'},{'op':'bad'}])
        self.assertEqual(before,self.s.snapshot())
    def test_batch_rejects_clock_and_nested(self):
        for child in [{'op':'time','timeUs':10},{'op':'reset'},{'op':'batch','commands':[]}]:
            with self.assertRaises(ValueError):self.cmd('batch',commands=[child])
    def test_rational_boundaries(self):
        for us,step in [(8332,0),(8333,1),(16665,1),(16666,2),(24999,2),(25000,3),(1000000,120)]:
            self.s.advance_to(us);self.assertEqual(self.s.info()['clock']['step'],step)
    def test_scheduled_boundary_and_order(self):
        self.cmd('define',path='/x',value=0)
        for ident,value in [(1,10),(2,20)]:self.cmd('schedule',id=ident,atUs=10000,command={'op':'set','path':'/x','value':value})
        self.s.advance_to(10000);self.assertEqual(self.s.info()['values']['/x'],0)
        self.s.advance_to(16666);self.assertEqual(self.s.info()['values']['/x'],20)
    def test_schedule_retained_in_snapshot(self):
        self.cmd('define',path='/x',value=0);self.cmd('schedule',id=1,atUs=10000,command={'op':'set','path':'/x','value':3})
        snap=self.s.snapshot();self.s.advance_to(100000);expected=self.s.snapshot();self.s.restore(snap);self.s.advance_to(100000)
        self.assertEqual(expected,self.s.snapshot())
    def test_schedule_cancel_and_atomic_invalid(self):
        self.cmd('define',path='/x',value=0);before=self.s.snapshot()
        with self.assertRaises(ValueError):self.cmd('schedule',id=1,atUs=10,command={'op':'set','path':'/missing','value':1})
        self.assertEqual(before,self.s.snapshot())
        self.cmd('schedule',id=1,atUs=10,command={'op':'set','path':'/x','value':1});self.cmd('cancel-schedule',id=1)
        self.s.advance_to(20000);self.assertEqual(self.s.info()['values']['/x'],0)
    def test_rain_identity_mapping(self):
        cat=json.loads((ROOT/'catalogue.json').read_text())
        for name in ['weather/slantfall','weather/storm-volume']:self.assertEqual(next(x['algorithm'] for x in cat if x['id']==name),1)
    def emitter(self,**kw):
        values=dict(id=1,effect='weather/autumn-drift',count=20,runningTimeMs=0,position=[0,8,0],extent=[3,2,3],collision=False,deposit=False,lifetimeMinMs=15000,lifetimeMaxMs=15000)
        values.update(kw);self.cmd('emitter',**values)
    def test_leaf_shape_weights_change_geometry_not_physics(self):
        self.emitter(shapeWeights=[1,0,0]);self.s.advance_to(500000);a=self.s.render();state=self.s.particles()
        self.cmd('reset',seed=42);self.emitter(shapeWeights=[0,0,1]);self.s.advance_to(500000)
        self.assertEqual(state,self.s.particles());self.assertNotEqual(a.bytes,self.s.render().bytes)
    def test_end_style_tail_bounded(self):
        for style in ['settle','dissolve','gust','quench','disperse']:
            self.cmd('reset',seed=42);self.emitter(**({'effect':'weather/thermal-cinders'} if style=='quench' else {}));self.s.advance_to(100000);self.cmd('stop',id=1,style=style,tailMs=200)
            self.s.advance_to(400000);self.assertEqual(self.s.info()['particles']['active'],0,style)
    def test_stop_idempotent(self):
        self.emitter();self.s.advance_to(100000);self.cmd('stop',id=1,style='dissolve',tailMs=200)
        self.s.advance_to(200000);self.cmd('stop',id=1,style='dissolve',tailMs=200);self.s.advance_to(310000)
        self.assertEqual(self.s.info()['particles']['active'],0)
    def test_repeat_count_and_identity(self):
        self.emitter(count=3,runningTimeMs=100,cycles=3,gapMs=50);self.s.advance_to(600000)
        self.assertEqual(self.s.info()['particles']['born'],9);ids=[p[0] for p in self.s.particles()];self.assertEqual(len(set(ids)),9)
    def test_continuous_rate(self):
        self.cmd('emitter',id=1,effect='weather/snowglobe',rate=12,runningTimeMs=0,collision=False,deposit=False)
        self.s.advance_to(1000000);self.assertEqual(self.s.info()['particles']['born'],12)
    def test_rate_and_count_rejected(self):
        with self.assertRaises(ValueError):self.cmd('emitter',id=1,rate=12,count=4)
    def test_clear_instance_preserves_deposits(self):
        self.emitter(count=3,position=[0,.1,0],extent=[0,0,0],velocity=[0,-3,0],collision=True,deposit=True)
        self.s.advance_to(200000);n=self.s.info()['particles']['deposited'];self.assertEqual(n,3)
        self.cmd('clear-instance',id=1);self.assertEqual(n,self.s.info()['particles']['deposited'])
        self.emitter(count=1);self.assertEqual(n,self.s.info()['particles']['deposited'])
    def test_scoped_deposit_clear(self):
        for ident in [1,2]:self.emitter(id=ident,count=3,position=[0,.1,0],extent=[0,0,0],velocity=[0,-3,0],collision=True,deposit=True)
        self.s.advance_to(200000);self.assertEqual(self.s.info()['particles']['deposited'],6)
        self.cmd('clear-deposits',emitterId=1);self.assertEqual(self.s.info()['particles']['deposited'],3)
    def test_invalid_deposit_configuration(self):
        with self.assertRaises(ValueError):self.emitter(collision=False,deposit=True)
        with self.assertRaises(ValueError):self.cmd('floor',overflow='merge-to-field',maxTiles=0)
    def test_priority_queue_dwell_and_recovery(self):
        self.cmd('area',id=1,layout='queue',width=40,height=3,padding=0,border='none',gapMs=0)
        self.cmd('status',id=1,area=1,text='first',durationMs=100,priority=1)
        self.cmd('status',id=2,area=1,text='later low',durationMs=100,priority=1)
        self.cmd('status',id=3,area=1,text='later high',durationMs=100,priority=90)
        self.s.advance_to(100000);msgs={m['id']:m for m in self.s.info()['messages']}
        self.assertEqual(msgs[3]['state'],'active');self.assertEqual(msgs[2]['state'],'queued');self.assertEqual(msgs[1]['state'],'expired')
        self.s.advance_to(200000);self.assertEqual({m['id']:m for m in self.s.info()['messages']}[2]['state'],'active')
    def test_status_missing_area_rejects(self):
        with self.assertRaises(ValueError):self.cmd('status',area=88,text='not lost')
    def test_blank_message_has_dwell(self):
        self.cmd('area',id=1,layout='queue',gapMs=0)
        self.cmd('status',id=1,area=1,text='',durationMs=100)
        self.cmd('status',id=2,area=1,text='after blank',durationMs=100)
        self.assertEqual(self.s.info()['messages'][0]['state'],'active');self.s.advance_to(100000)
        self.assertEqual(self.s.info()['messages'][1]['state'],'active')
    def test_status_ack_and_capacity(self):
        self.cmd('status',id=1,text='important',durationMs=0);self.cmd('dismiss',id=1)
        self.assertEqual(self.s.info()['messages'][0]['state'],'dismissed');self.cmd('purge-status',id=1)
        self.assertEqual(self.s.info()['messages'],[])
    def test_reader_retains_scroll_document(self):
        text='\n'.join('line %d'%i for i in range(100))
        self.cmd('window',id=1,title='Read me',text=text)
        self.cmd('window-action',id=1,action='read');self.s.advance_to(1000000)
        a=self.s.render();self.cmd('window-action',id=1,action='scroll',rows=20);b=self.s.render()
        self.assertNotEqual(a.bytes,b.bytes);w=self.s.info()['windows'][0];self.assertEqual(w['text'],text);self.assertEqual(w['scrollRow'],20)
    def test_accessibility_reduced_motion_input(self):
        self.cmd('accessibility',reducedMotion=True,screenReader=True);self.cmd('input',text='still readable');self.s.advance_to(500000)
        self.assertEqual(self.s.info()['prompt']['text'],'still readable');self.assertTrue(self.s.info()['accessibility']['reducedMotion'])
    def test_render_does_not_consume_status(self):
        self.cmd('status',text='held');before=self.s.snapshot()
        for _ in range(3):self.s.render()
        self.assertEqual(before,self.s.snapshot())
    def test_pending_info_complete(self):
        self.cmd('schedule',id=12,atUs=10000,command={'op':'input','text':'later'})
        self.assertEqual(self.s.info()['pending'][0]['id'],12)
