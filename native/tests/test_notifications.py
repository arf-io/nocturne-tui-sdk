"""Native notification contract: explicit coalescing, retained intents, truthful timing."""
from pathlib import Path
import sys, unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bindings/python'))
from nocturne_native import NativeScene

class NotificationTests(unittest.TestCase):
    def setUp(self):
        self.s = NativeScene(18)
        self.cmd('environment', stars=0)
        self.cmd('prompt', active=False)
        self.cmd('area', id=1, x=4, y=4, width=65, height=12,
                 border='rounded', padding=1, layout='queue', gapMs=0)
    def tearDown(self): self.s.close()
    def cmd(self, op, **fields): return self.s.command({'op': op, **fields})
    def record(self, ident): return next(m for m in self.s.info()['messages'] if m['id']==ident)
    def notification(self, ident=1, **fields):
        options=dict(id=ident, area=1, text='Build needs review', durationMs=0,
                     actions=[{'id':1,'label':'Review','event':'/build/review'}])
        
        if 'dwellPerCharacterMs' in fields and 'durationMs' not in fields: options.pop('durationMs')
        options.update(fields); return self.cmd('status', **options)
    def testDefaultIdsAreUniqueWithoutChangingWeatherIds(self):
        self.cmd('status', id=1, text='existing')
        self.cmd('status', text='allocated')
        self.assertEqual(len({m['id'] for m in self.s.info()['messages']}), 2)
        self.cmd('field',x=3,y=3)
        self.assertEqual(self.s.info()['fields'][0]['id'],1)
    def testCountCoalescingKeepsDwellAndIdentity(self):
        self.notification(key='compile',coalesce='count',durationMs=1000)
        self.s.advance_to(300000)
        self.notification(2,key='compile',coalesce='count',durationMs=1000)
        m=self.record(1)
        self.assertEqual(m['occurrences'],2); self.assertEqual(m['startUs'],0)
        self.assertEqual(len(self.s.info()['messages']),1)
        self.s.advance_to(1000000); self.assertEqual(self.record(1)['state'],'expired')
    def testCountRejectsDifferentContentAtomically(self):
        self.notification(key='build',coalesce='count')
        before=self.s.snapshot()
        with self.assertRaises(ValueError):self.notification(2,key='build',coalesce='count',text='Different')
        self.assertEqual(before,self.s.snapshot())
    def testReplaceOnlyQueuedMessages(self):
        self.notification(key='job')
        self.notification(2,key='progress',text='10%',coalesce='replace-queued')
        self.notification(3,key='progress',text='20%',coalesce='replace-queued')
        self.assertEqual(self.record(1)['text'],'Build needs review')
        self.assertEqual(self.record(2)['text'],'20%')
        self.assertEqual(self.record(2)['replacements'],1)
        self.assertEqual(len(self.s.info()['messages']),2)
    def testCoalescingRequiresKey(self):
        for mode in ('count','replace-queued'):
            with self.assertRaises(ValueError):self.notification(coalesce=mode)
    def testImportantCannotBeReplacedOrPurgedUnacknowledged(self):
        self.notification(important=True)
        self.cmd('dismiss',id=1)
        with self.assertRaises(ValueError):self.cmd('purge-status',id=1)
        self.cmd('ack-status',id=1); self.cmd('purge-status',id=1)
        self.assertEqual(self.s.info()['messages'],[])
    def testImportantAndCoalescingRejected(self):
        for mode in ('count','replace-queued'):
            with self.assertRaises(ValueError):self.notification(important=True,key='x',coalesce=mode)
    def testActionsProduceIntentNotExternalEffect(self):
        self.notification()
        self.cmd('notification-action',id=1,actionId=1)
        intent=self.s.info()['intents'][0]
        self.assertEqual(intent['event'],'/build/review')
        self.assertEqual(intent['messageId'],1)
        self.assertEqual(intent['actionId'],1)
        self.assertEqual(self.record(1)['state'],'active')
    def testActionIsIdempotentUntilMessageExplicitlyReplaced(self):
        self.notification(); self.cmd('notification-action',id=1,actionId=1)
        before=self.s.snapshot(); self.cmd('notification-action',id=1,actionId=1)
        self.assertEqual(before,self.s.snapshot())
        self.cmd('ack-intent',id=1);self.cmd('notification-action',id=1,actionId=1)
        self.assertEqual(self.s.info()['intents'],[])
    def testActionButtonUsesCurrentHitMap(self):
        self.notification(); f=self.s.render()
        points=[(i%f.width,i//f.width) for i,w in enumerate(f.words()) if w[3]==0x63000004]
        self.assertTrue(points)
        x,y=points[len(points)//2]
        self.cmd('pointer',phase='down',x=x,y=y)
        self.cmd('pointer',phase='up',x=x,y=y)
        self.assertEqual(len(self.s.info()['intents']),1)
        self.assertFalse(self.s.info()['camera']['flightActive'])
        self.assertEqual(self.s.info()['fieldCount'],0)
    def testModalBlocksNotificationActions(self):
        self.notification(); f=self.s.render()
        points=[(i%f.width,i//f.width) for i,w in enumerate(f.words()) if w[3]==0x63000004]
        self.assertTrue(points);x,y=points[0]
        self.cmd('key',key='F1');self.cmd('pointer',phase='down',x=x,y=y)
        self.assertEqual(self.s.info()['intents'],[])
    def testSnapshotRetainsIntentsAndActionConsumption(self):
        self.notification();self.cmd('notification-action',id=1,actionId=1)
        snap=self.s.snapshot();self.cmd('ack-intent',id=1);self.s.restore(snap)
        self.assertEqual(self.s.snapshot(),snap);self.cmd('notification-action',id=1,actionId=1)
        self.assertEqual(len(self.s.info()['intents']),1)
    def testAckMissingIntentIsIdempotent(self):
        before=self.s.snapshot();self.cmd('ack-intent',id=77)
        self.assertEqual(before,self.s.snapshot())
    def testIntentsSurviveClearAndPurge(self):
        self.notification();self.cmd('notification-action',id=1,actionId=1)
        self.cmd('dismiss',id=1);self.cmd('purge-status',id=1);self.cmd('clear',scope='status')
        self.assertEqual(self.s.info()['intents'][0]['event'],'/build/review')
    def testInactiveActionRejected(self):
        self.notification();self.cmd('dismiss',id=1)
        with self.assertRaises(ValueError):self.cmd('notification-action',id=1,actionId=1)
    def testQueueFullDoesNotConsumeActionOrMessage(self):
        for i in range(1,18):
            self.notification(i,area=0,actions=[{'id':j,'label':f'A{j}','event':'/action'} for j in range(1,5)])
        for i in range(1,17):
            for j in range(1,5):self.cmd('notification-action',id=i,actionId=j)
        self.assertEqual(len(self.s.info()['intents']),64);before=self.s.snapshot()
        with self.assertRaises(ValueError):self.cmd('notification-action',id=17,actionId=1)
        self.assertEqual(before,self.s.snapshot())
        self.cmd('ack-intent',id=1);self.cmd('notification-action',id=17,actionId=1)
        self.assertEqual(self.s.info()['intents'][-1]['messageId'],17)
    def testDynamicDwellIsBoundedAndBlankStillExists(self):
        self.notification(text='abcdefghij',dwellPerCharacterMs=20,minDurationMs=100,maxDurationMs=500)
        self.assertEqual(self.record(1)['durationUs'],200000)
        self.notification(2,text='',dwellPerCharacterMs=20,minDurationMs=100,maxDurationMs=500)
        self.assertEqual(self.record(2)['durationUs'],100000)
    def testStaticDurationAndDynamicDurationAreExclusive(self):
        with self.assertRaises(ValueError):self.notification(dwellPerCharacterMs=20,minDurationMs=100,maxDurationMs=500,durationMs=100)
    def testBlankActionLabelRejected(self):
        with self.assertRaises(ValueError):self.notification(actions=[{'id':1,'label':'','event':'/retry'}])
    def testDuplicateActionIdsRejected(self):
        a={'id':1,'label':'Retry','event':'/retry'}
        with self.assertRaises(ValueError):self.notification(actions=[a,a])
    def testUnknownActionPropertyRejected(self):
        with self.assertRaises(ValueError):self.notification(actions=[{'id':1,'label':'Retry','event':'/retry','shell':'echo nope'}])
    def testEventPathRejectsAmbiguousSegments(self):
        for event in ('retry','//retry','/../retry','/retry/','/re try'):
            with self.assertRaises(ValueError):self.notification(actions=[{'id':1,'label':'Retry','event':event}])
    def testPopReallyPopsAtFullInk(self):
        self.cmd('area',id=2,x=5,y=20,width=20,height=4,padding=0,border='none',fadeMs=900,alpha=0)
        self.cmd('status',id=1,area=2,text='Pop',mode='pop',durationMs=1000)
        f=self.s.render();line=''.join(chr(w[0]) for w in f.words()[20*f.width:21*f.width])
        self.assertIn('Pop',line)
    def testZeroMaterialAlphaRemovesInkAndActionHits(self):
        self.cmd('material',id=2,alpha=0)
        self.cmd('area',id=1,material=2,border='none',alpha=0)
        self.notification(text='OPAQUEBUG')
        f=self.s.render()
        self.assertFalse(any((w[3]>>24)==0x63 for w in f.words()))
        row=f.words()[5*f.width:6*f.width]
        self.assertNotIn('OPAQUEBUG',''.join(chr(w[0]) for w in row))
        self.assertEqual(self.record(1)['text'],'OPAQUEBUG')
    def testHalfMaterialAlphaAffectsNotificationInk(self):
        self.cmd('material',id=2,alpha=1)
        self.cmd('area',id=1,material=2,border='none',alpha=0)
        self.notification(text='Q')
        full=self.s.render();a=full.words()[5*full.width+5][1]
        self.cmd('material',id=2,alpha=.5)
        half=self.s.render();b=half.words()[5*half.width+5][1]
        self.assertNotEqual(a,b)
    def testStatusMaterialBlendIsApplied(self):
        self.cmd('environment',background=0x889977)
        self.cmd('material',id=2,space='rgb',channels={'r':.3,'g':.8,'b':.4},alpha=1,blend='normal')
        self.cmd('area',id=1,material=2,border='none',alpha=0)
        self.notification(text='Q')
        f=self.s.render();normal=f.words()[5*f.width+5][1]
        self.cmd('material',id=2,blend='multiply')
        f=self.s.render();multiply=f.words()[5*f.width+5][1]
        self.assertNotEqual(normal,multiply)
    def testNotificationRenderingIsPure(self):
        self.notification();snap=self.s.snapshot()
        for _ in range(3):self.s.render()
        self.assertEqual(snap,self.s.snapshot())
    def testStatusAreaScalarCellsSourceSnapshotAndRenderedAction(self):
        # U+0301 is a separate scalar, not a precomposed accented e.
        message = 'Aé界e\u0301Z'
        label = 'Review é'
        event = '/status/scalar/review'
        self.cmd('resize', width=48, height=16)
        self.cmd('pause', paused=True)
        self.cmd('area', id=1, x=4, y=3, width=30, height=6,
                 border='none', padding=0, layout='direct', alpha=1)
        self.notification(37, text=message, x=0, y=0, mode='pop',
                          actions=[{'id':17, 'label':label, 'event':event, 'value':7}])
        source = self.record(37)
        self.assertEqual(source['text'], message)
        self.assertEqual(source['actions'][0]['label'], label)
        snapshot = self.s.snapshot()
        original_frame = None
        hit_id = 0x63000000 | (37 << 2)  # action slot zero, not action ID 17
        for phase in ('original', 'restored'):
            with self.subTest(phase=phase):
                self.assertEqual(self.s.snapshot(), snapshot)
                self.assertEqual(self.record(37), source)
                frame = self.s.render()  # Always emitted by the rebuilt C core.
                self.assertEqual((frame.width, frame.height), (48, 16))
                if original_frame is None:
                    original_frame = frame
                self.assertEqual(frame, original_frame)
                words = frame.words()
                self.assertEqual([words[3 * 48 + 4 + i][0] for i in range(6)],
                                 [0x41, 0xe9, 0x754c, 0x65, 0x301, 0x5a])
                self.assertEqual([words[3 * 48 + 4 + i][3] for i in range(7)], [0] * 7)
                self.assertEqual([words[5 * 48 + 5 + i][0] for i in range(len(label))],
                                 list(map(ord, label)))
                hits = [(i % 48, i // 48) for i, cell in enumerate(words) if cell[3] == hit_id]
                self.assertEqual(hits, [(x, y) for y in range(4, 7) for x in range(4, 16)])
                self.assertEqual(self.s.render(), frame)
                self.assertEqual(self.s.snapshot(), snapshot)
                self.assertEqual(self.record(37), source)
                # Pick the actual C-emitted accented action-label hit cell.
                x, y = next((x, y) for x, y in hits if words[y * 48 + x][0] == ord('é'))
                self.cmd('pointer', phase='down', x=x, y=y)
                self.cmd('pointer', phase='up', x=x, y=y)
                intents = self.s.info()['intents']
                self.assertEqual(len(intents), 1)
                self.assertEqual((intents[0]['messageId'], intents[0]['actionId'],
                                  intents[0]['event'], intents[0]['value']), (37, 17, event, 7))
                self.assertEqual(self.record(37)['text'], message)
                self.assertEqual(self.record(37)['actions'][0]['label'], label)
                self.assertEqual(frame, original_frame)  # Copied frame remains owned.
                self.cmd('clear', scope='status')
                self.assertEqual(self.s.info()['messages'], [])
                self.assertNotEqual(self.s.snapshot(), snapshot)
                self.s.restore(snapshot)
                self.assertEqual(self.s.snapshot(), snapshot)
                self.assertEqual(self.record(37), source)
                self.assertEqual(self.s.info()['intents'], [])
if __name__=='__main__':unittest.main()
