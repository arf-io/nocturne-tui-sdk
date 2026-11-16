"""Native condition trees, timing, and retained notification-event gates."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
from native.tests.current_writer_contract import current_schema, snapshot_size
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class CompoundConditions(unittest.TestCase):
 def setUp(self):
  self.s=NativeScene(2030)
  for path,value in [('/heat',20),('/enabled',1),('/pressure',10),('/out',0)]:self.cmd('define',path=path,value=value)
 def tearDown(self):self.s.close()
 def cmd(self,op,**kw):return self.s.command({'op':op,**kw})
 def leaf(self,path='/heat',comparison='above',**kw):return {'path':path,'comparison':comparison,**({'value':50}if not kw else kw)}
 def rule(self,**kw):
  args={'id':1,'when':self.leaf(), 'target':'/out','action':'increment','value':1};args.update(kw);return self.cmd('trigger',**args)
 def output(self):return self.s.info()['values']['/out']
 def set(self,path,value):self.cmd('set',path=path,value=value)
 def testAllAnyNotExecuteWithoutRuntimeShim(self):
  self.rule(when={'all':[self.leaf(),{'any':[self.leaf('/pressure','below',value=5),{'not':self.leaf('/enabled','equal',value=0)}]}]})
  self.set('/heat',60);self.assertEqual(self.output(),1)
  self.set('/heat',61);self.assertEqual(self.output(),1)
  self.set('/heat',20);self.set('/enabled',0);self.set('/heat',60);self.assertEqual(self.output(),1)
  self.set('/pressure',3);self.assertEqual(self.output(),2)
 def testInclusiveRangeAndComparators(self):
  for op,val,expect in [('equal',50,True),('not-equal',50,False),('at-least',50,True),('at-most',50,True),('above',50,False),('below',50,False)]:
   with NativeScene(42) as scene:
    scene.command({'op':'define','path':'/x','value':50});scene.command({'op':'define','path':'/out','value':0})
    scene.command({'op':'trigger','id':1,'when':self.leaf('/x',op,value=val),'target':'/out','value':1})
    scene.command({'op':'set','path':'/x','value':50})
    self.assertEqual(scene.info()['values']['/out'],int(expect),op)
  self.set('/heat',50);self.rule(when=self.leaf(comparison='between',min=20,max=40))
  self.set('/heat',40);self.assertEqual(self.output(),1)
 def testHysteresisLivesOnIndividualLeaf(self):
  self.rule(when={'all':[self.leaf(value=50,hysteresis=5),self.leaf('/enabled','equal',value=1)]})
  self.set('/heat',51);self.assertEqual(self.output(),1)
  self.set('/heat',48);self.assertEqual(self.output(),1)
  self.set('/heat',45);self.set('/heat',51);self.assertEqual(self.output(),2)
 def testFallingEdge(self):
  self.rule(edge='falling');self.set('/heat',60);self.assertEqual(self.output(),0)
  self.set('/heat',20);self.assertEqual(self.output(),1)
 def testChangeEdge(self):
  self.rule(edge='change');self.set('/heat',60);self.set('/heat',61);self.set('/heat',20);self.assertEqual(self.output(),2)
 def testCooldownIncludesFireAtTimeZero(self):
  self.rule(cooldownMs=1000);self.set('/heat',60);self.assertEqual(self.output(),1)
  self.set('/heat',20);self.set('/heat',60);self.assertEqual(self.output(),1)
  self.s.advance_to(1000000);self.assertEqual(self.output(),2)
 def testDebounceCancelsWhenConditionStopsHolding(self):
  self.rule(debounceMs=100);self.set('/heat',60);self.s.advance_to(50000);self.set('/heat',20)
  self.s.advance_to(200000);self.assertEqual(self.output(),0)
  self.set('/heat',60);self.s.advance_to(300000);self.assertEqual(self.output(),1)
 def testRenderCannotFireOrAdvanceConditions(self):
  self.rule(debounceMs=100);self.set('/heat',60);snap=self.s.snapshot()
  for _ in range(10):self.s.render();self.s.info()
  self.assertEqual(snap,self.s.snapshot());self.assertEqual(self.output(),0)
 def testSnapshotPreservesLeafAndPendingState(self):
  self.rule(debounceMs=100);self.set('/heat',60);self.s.advance_to(50000);snap=self.s.snapshot()
  self.s.advance_to(100000);a=self.s.snapshot();self.s.restore(snap);self.s.advance_to(100000);self.assertEqual(a,self.s.snapshot())
 def testInvalidTreesCannotPartiallyReplaceRules(self):
  self.rule();valid=self.s.snapshot()
  for tree in ({'all':[]},{'any':[]},{'not':[]},{'path':'/missing','value':2},{'path':'/heat','value':2,'unknown':1},{'all':[self.leaf()],'any':[self.leaf()]},{'path':'/heat','comparison':'between','min':4,'max':2},{'path':'/heat','comparison':'equal','value':2,'hysteresis':1}):
   with self.assertRaises(ValueError):self.rule(when=tree)
   self.assertEqual(valid,self.s.snapshot(),tree)
 def testTooDeepAndTooLargeRejected(self):
  deep=self.leaf()
  for _ in range(10):deep={'not':deep}
  for tree in (deep,{'all':[self.leaf()for _ in range(32)]}):
   with self.assertRaises(ValueError):self.rule(when=tree)
 def testScalarSyntaxUsesCurrentConditionImplementation(self):
  self.cmd('trigger',id=1,source='/heat',target='/out',comparison='above',threshold=50,value=3)
  self.set('/heat',70);self.assertEqual(self.output(),3)
  t=self.s.info()['triggers'][0];self.assertEqual(t['conditionNodes'],1)
 def testAmbiguousSourceAndTreeReject(self):
  with self.assertRaises(ValueError):self.rule(source='/heat')
 def testFailedTargetRollsBackWholeConditionState(self):
  self.cmd('define',path='/alpha',value=.5,binding={'family':'material','id':1,'field':'alpha'})
  self.rule(target='/alpha',value=2,action='set');snap=self.s.snapshot()
  with self.assertRaises(ValueError):self.set('/heat',90)
  self.assertEqual(snap,self.s.snapshot())
  self.cmd('input',text='retained');self.assertEqual(self.s.info()['prompt']['text'],'retained')
 def testTriggersObserveOnePreWriteSnapshot(self):
  self.rule();self.cmd('trigger',id=2,source='/out',target='/pressure',comparison='above',threshold=0,value=90)
  self.set('/heat',60);self.assertEqual(self.s.info()['values']['/pressure'],10)
  self.s.advance_to(8333);self.assertEqual(self.s.info()['values']['/pressure'],90)
 def notification(self,ident=1):
  self.cmd('status',id=ident,area=0,text='Approve',durationMs=0,actions=[{'id':1,'label':'Confirm','event':'/task/approved','value':7}]);self.cmd('notification-action',id=ident,actionId=1)
 def testEventGuardWaitsWithoutConsumingIntention(self):
  self.rule(event='/task/approved');self.notification();self.assertEqual(self.output(),0)
  self.set('/heat',60);self.assertEqual(self.output(),1)
  self.assertEqual(len(self.s.info()['intents']),1)
  self.s.advance_to(1000000);self.assertEqual(self.output(),1)
 def testEachRetainedEventFiresOncePerRule(self):
  self.rule(event='/task/approved',when=self.leaf('/enabled','equal',value=1))
  self.notification(1);self.notification(2);self.assertEqual(self.output(),2)
  self.set('/heat',99);self.assertEqual(self.output(),2)
  self.assertEqual([i['id']for i in self.s.info()['intents']],[1,2])
 def testIndependentRulesDoNotStealRetainedEvents(self):
  self.rule(event='/task/approved',when=self.leaf('/enabled','equal',value=1))
  self.rule(id=2,event='/task/approved',when=self.leaf('/enabled','equal',value=1))
  self.notification();self.assertEqual(self.output(),2);self.assertEqual(len(self.s.info()['intents']),1)
 def testAckBeforeDebounceCancelsPendingEvent(self):
  self.rule(event='/task/approved',debounceMs=100,when=self.leaf('/enabled','equal',value=1));self.notification()
  self.cmd('ack-intent',id=1);self.s.advance_to(200000);self.assertEqual(self.output(),0)
 def testEventSnapshotsDoNotReplayAcceptedAction(self):
  self.rule(event='/task/approved',when=self.leaf('/enabled','equal',value=1));self.notification();snap=self.s.snapshot()
  self.s.restore(snap);self.s.advance_to(500000);self.assertEqual(self.output(),1)
 def testEditingSameEventRuleCannotReplayPreviouslyAcceptedIntent(self):
  self.rule(event='/task/approved',when=self.leaf('/enabled','equal',value=1));self.notification()
  self.rule(event='/task/approved',when=self.leaf('/enabled','at-least',value=1),value=10)
  self.set('/heat',99);self.assertEqual(self.output(),1)
  self.notification(2);self.assertEqual(self.output(),11)
  self.assertEqual(self.s.info()['triggers'][0]['fireCount'],2)
 def testEventPathsAndAmbiguousEdgeReject(self):
  for patch in ({'event':'../bad'},{'event':'/x//y'},{'event':'/ok','edge':'falling'}):
   with self.assertRaises(ValueError):self.rule(**patch)
 def testBatchDoesNotTriggerOnAnIntermediateValueCombination(self):
  self.rule(when={'all':[self.leaf(),self.leaf('/enabled','equal',value=1)]})
  self.cmd('batch',commands=[{'op':'set','path':'/heat','value':60},{'op':'set','path':'/enabled','value':0}])
  self.assertEqual(self.output(),0)
  self.cmd('batch',commands=[{'op':'set','path':'/heat','value':60},{'op':'set','path':'/enabled','value':1}])
  self.assertEqual(self.output(),1)
 def testNonValueBatchCannotFireAVisualTriggerAgainstTyping(self):
  self.cmd('define',path='/alpha',value=.5,binding={'family':'material','id':1,'field':'alpha'})
  self.rule(when=self.leaf('/enabled','equal',value=1),target='/alpha',value=2)
  self.cmd('batch',commands=[{'op':'input','text':'still immediate'}])
  self.assertEqual(self.s.info()['prompt']['text'],'still immediate')
 def testLevelHonorsCooldownAtInitialTimestamp(self):
  self.rule(edge='level',cooldownMs=100);self.set('/heat',60)
  self.set('/heat',60);self.assertEqual(self.output(),1)
  self.s.advance_to(100000);self.assertEqual(self.output(),2)
 def intentRule(self, selector, **kw):
  args={'id':1,'when':selector,'target':'/out','action':'increment','value':1,'event':'/task/approved'};args.update(kw);return self.cmd('trigger',**args)
 def actionIntent(self, ident, event, value):
  self.cmd('status',id=ident,area=0,text='Action',durationMs=0,actions=[{'id':1,'label':'Confirm','event':event,'value':value}]);self.cmd('notification-action',id=ident,actionId=1)
 def testIntentValueReadsPayloadFromSameOldestEventCandidate(self):
  self.set('/enabled',0)
  self.intentRule({'all':[self.leaf('/enabled','equal',value=1),{'intentValue':{'comparison':'at-least','value':7}}]})
  self.actionIntent(1,'/unrelated',99);self.actionIntent(2,'/task/approved',7)
  self.assertEqual(self.output(),0)
  self.assertEqual([intent['id'] for intent in self.s.info()['intents']],[1,2])
  rule=self.s.info()['triggers'][0]
  self.assertEqual(rule['intentCandidate'],{'id':2,'event':'/task/approved','messageId':2,'actionId':1,'messageSequence':2,'atUs':0,'value':7})
  self.set('/enabled',1)
  self.assertEqual(self.output(),1)
 def testIntentValueClosedGuardWaitsAndMissingCandidateIsUnavailable(self):
  self.intentRule({'intentValue':{'comparison':'at-least','value':7}})
  self.cmd('set',path='/enabled',value=1)
  self.assertEqual(self.output(),0)
  self.assertIsNone(self.s.info()['triggers'][0]['intentCandidate'])
  self.actionIntent(1,'/task/approved',6)
  self.assertEqual(self.output(),0)
  self.assertEqual(len(self.s.info()['intents']),1)
  self.actionIntent(2,'/task/approved',7)
  self.assertEqual(self.output(),0)
  self.cmd('ack-intent',id=1)
  self.cmd('set',path='/enabled',value=1)
  self.assertEqual(self.output(),1)
 def testIntentValueComparatorsAndRangeBoundaries(self):
  cases=[('above',8,7,True),('below',6,7,True),('equal',7,7,True),('not-equal',8,7,True),('at-least',7,7,True),('at-most',7,7,True),('between',8,(6,8),True)]
  for index,(comparison,payload,bounds,expected) in enumerate(cases,1):
   event=f'/selector/{index}'
   leaf={'comparison':comparison}
   if comparison=='between':leaf.update(min=bounds[0],max=bounds[1])
   else:leaf['value']=bounds
   with self.subTest(comparison=comparison):
    self.intentRule({'intentValue':leaf},event=event)
    self.actionIntent(index,event,payload)
    self.assertEqual(self.output(),index)
 def testIntentValueParticipatesInAllAnyNotTree(self):
  self.intentRule({'any':[{'all':[self.leaf('/enabled','equal',value=1),{'intentValue':{'comparison':'between','min':6,'max':8}}]},{'not':self.leaf('/heat','above',value=50)}]})
  self.actionIntent(1,'/task/approved',7)
  self.assertEqual(self.output(),1)
 def testIntentValueSelectorRequiresEventAndRejectsMalformedLeavesAtomically(self):
  with self.assertRaises(ValueError):self.intentRule({'intentValue':{'comparison':'equal','value':0}},event='')
  valid=self.s.snapshot()
  for leaf in ({'intentValue':{'comparison':'equal','value':1,'extra':0}},{'intentValue':{'comparison':'unknown','value':1}},{'intentValue':{'comparison':'between','min':4,'max':2}},{'intentValue':{'comparison':'above','value':1,'hysteresis':2}}):
   with self.assertRaises(ValueError):self.intentRule(leaf)
   self.assertEqual(self.s.snapshot(),valid)
 def testIntentValuePendingDebounceSnapshotsAndReadsArePure(self):
  self.intentRule({'intentValue':{'comparison':'at-least','value':7}},debounceMs=100)
  self.actionIntent(1,'/task/approved',7)
  before=self.s.snapshot()
  self.assertTrue(self.s.info()['triggers'][0]['pending'])
  for _ in range(5):self.s.info();self.s.render()
  self.assertEqual(self.s.snapshot(),before)
  self.s.advance_to(100000);expected=self.s.snapshot()
  self.assertEqual(self.output(),1)
  self.s.restore(before);self.s.advance_to(100000)
  self.assertEqual(self.s.snapshot(),expected)
 def testPreviousSchemaRejectsIntentSelectorWithRecomputedChecksum(self):
  import zlib
  self.intentRule({'intentValue':{'comparison':'at-least','value':7}})
  hostile=bytearray(self.s.snapshot())
  hostile[12:16]=(0x20261002).to_bytes(4,'little')
  hostile[28:32]=(0x20261002).to_bytes(4,'little')
  hostile[20:24]=(zlib.crc32(hostile[24:])&0xffffffff).to_bytes(4,'little')
  before=self.s.snapshot()
  with self.assertRaises(ValueError):self.s.restore(bytes(hostile))
  self.assertEqual(self.s.snapshot(),before)
 def testLegacySnapshotFixtureLoadsAndPromotesWithoutMutatingInput(self):
  import gzip
  fixture=Path(__file__).parent/'fixtures/schema-20261002-retained-event-debounce.snapshot.gz'
  data=gzip.decompress(fixture.read_bytes());original=bytes(data)
  self.s.restore(data)
  self.assertEqual(data,original)
  info=self.s.info()
  self.assertEqual(info['values']['/out'],1)
  self.assertEqual(info['triggers'][0]['lastIntent'],1)
  self.assertEqual(info['triggers'][0]['fireCount'],1)
  self.assertTrue(info['triggers'][1]['pending'])
  emitted=self.s.snapshot()
  self.assertEqual(int.from_bytes(emitted[12:16],'little'),current_schema())
  self.s.advance_to(100000)
  self.assertEqual(self.s.info()['values']['/debounced'],1)
  self.s.restore(data)
  self.s.advance_to(100000)
  self.assertEqual(self.s.info()['values']['/debounced'],1)
  self.cmd('set',path='/enabled',value=1)
  self.assertEqual(self.s.info()['values']['/out'],1)
 def testUnknownSnapshotSchemaRefusesWithoutChangingCurrentState(self):
  data=bytearray(self.s.snapshot());data[12:16]=(0x202610ff).to_bytes(4,'little')
  before=self.s.snapshot()
  with self.assertRaises(ValueError):self.s.restore(bytes(data))
  self.assertEqual(self.s.snapshot(),before)
 def intentValueActionRule(self, target='/out', action='set', **kw):
  args={'id':1,'when':self.leaf('/enabled','equal',value=1),'target':target,'action':action,'event':'/task/approved','valueFrom':'intentValue'};args.update(kw);return self.cmd('trigger',**args)
 def testIntentValueActionUsesExactSameCandidateForGuardAndSet(self):
  self.set('/enabled',0)
  self.intentValueActionRule(when={'all':[self.leaf('/enabled','equal',value=1),{'intentValue':{'comparison':'at-least','value':7}}]})
  self.actionIntent(1,'/unrelated',99);self.actionIntent(2,'/task/approved',7)
  self.assertEqual(self.output(),0)
  self.assertEqual(self.s.info()['triggers'][0]['intentCandidate'],{'id':2,'event':'/task/approved','messageId':2,'actionId':1,'messageSequence':2,'atUs':0,'value':7})
  self.set('/enabled',1)
  self.assertEqual(self.output(),7)
  rule=self.s.info()['triggers'][0]
  self.assertEqual(rule['valueSource'],'intentValue')
  self.assertEqual(rule['lastIntent'],2)
  self.assertEqual(rule['lastIntentSource'],{'id':2,'event':'/task/approved','messageId':2,'actionId':1,'messageSequence':2,'atUs':0,'value':7})
  self.cmd('ack-intent',id=2)
  rule=self.s.info()['triggers'][0]
  self.assertEqual(rule['lastIntent'],2)
  self.assertIsNone(rule['lastIntentSource'])
 def testIntentValueActionIncrementUsesPayloadAndRetainsConstantActions(self):
  self.cmd('trigger',id=2,when=self.leaf('/enabled','equal',value=1),event='/task/increment',target='/out',action='increment',valueFrom='intentValue')
  self.actionIntent(1,'/task/increment',3)
  self.assertEqual(self.output(),3)
  self.assertEqual(self.s.info()['triggers'][0]['lastIntentSource']['value'],3)
  self.cmd('trigger',id=3,source='/enabled',target='/pressure',comparison='above',threshold=0,action='set',value=4)
  self.set('/enabled',1)
  self.assertEqual(self.s.info()['values']['/pressure'],4)
  self.assertEqual(self.s.info()['triggers'][1]['valueSource'],'constant')
 def testIntentValueActionDebounceAndExplicitAckKeepOwnership(self):
  self.set("/enabled",0)
  self.intentValueActionRule(debounceMs=100)
  self.actionIntent(1,"/task/approved",7)
  self.set("/enabled",1)
  self.assertEqual(self.output(),0)
  self.assertEqual(self.s.info()["triggers"][0]["pendingIntent"],1)
  self.s.advance_to(50000)
  self.cmd("ack-intent",id=1)
  self.assertEqual(self.output(),0)
  self.set("/enabled",0) # Cancellation is observed on the next evaluation.
  self.assertEqual(self.s.info()["triggers"][0]["pendingIntent"],0)
  self.actionIntent(2,"/task/approved",5)
  self.set("/enabled",1)
  self.s.advance_to(150000)
  self.assertEqual(self.output(),5)
  self.assertEqual(self.s.info()["triggers"][0]["lastIntent"],2)
 def testIntentValueActionSnapshotPreservesPendingCandidateAndSourceMode(self):
  self.set("/enabled",0)
  self.intentValueActionRule(debounceMs=100)
  self.actionIntent(1,"/task/approved",9)
  self.set("/enabled",1)
  before=self.s.snapshot()
  rule=self.s.info()["triggers"][0]
  self.assertTrue(rule["pending"])
  self.assertEqual(rule["pendingIntent"],1)
  self.assertEqual(rule["valueSource"],"intentValue")
  self.s.advance_to(100000);expected=self.s.snapshot()
  self.assertEqual(self.output(),9)
  self.s.restore(before)
  self.s.advance_to(100000)
  self.assertEqual(self.s.snapshot(),expected)
  self.assertEqual(self.output(),9)
 def testIntentValueActionRejectsAmbiguityAndMixedOperandsAtomically(self):
  self.rule(event='/task/approved')
  before=self.s.snapshot()
  invalid=({'event':''},{'value':1},{'valueFrom':'message.text'},{'action':'multiply'})
  for patch in invalid:
   with self.subTest(patch=patch),self.assertRaises(ValueError):self.intentValueActionRule(**patch)
   self.assertEqual(self.s.snapshot(),before)
 def testIntentValueActionBindingFailureRollsBackAndLeavesPriorIntent(self):
  self.cmd('material',id=2,channels={'h':180,'l':0.8,'c':0.12})
  self.cmd('define',path='/hue',value=180,binding={'family':'material','id':2,'field':'hue'})
  self.set('/enabled',0)
  self.intentValueActionRule(target='/hue')
  self.actionIntent(1,'/task/approved',400)
  before=self.s.snapshot()
  with self.assertRaises(ValueError):self.set('/enabled',1)
  self.assertEqual(self.s.snapshot(),before)
  info=self.s.info()
  self.assertEqual(info['values']['/hue'],180)
  self.assertEqual(info['triggers'][0]['lastIntent'],0)
  self.assertEqual(info['triggers'][0]['intentCandidate']['value'],400)
 def testFrozenSchema03SnapshotKeepsSelectorAndPromotesTo04(self):
  import gzip
  fixture=Path(__file__).parent/'fixtures/schema-20261003-retained-intent-selector.snapshot.gz'
  data=gzip.decompress(fixture.read_bytes());original=bytes(data)
  self.s.restore(data)
  self.assertEqual(data,original)
  info=self.s.info()
  self.assertEqual(info['values']['/out'],0)
  self.assertEqual(info['triggers'][0]['intentCandidate']['value'],7)
  emitted=self.s.snapshot()
  self.assertEqual(int.from_bytes(emitted[12:16],'little'),current_schema())
  self.set('/enabled',1)
  self.assertEqual(self.output(),42)
  self.assertEqual(self.s.info()['triggers'][0]['lastIntent'],1)
if __name__=='__main__':unittest.main()
