"""Native selectors, safe mappings and reversible appearance; no renderer mocks."""
from pathlib import Path
import sys, unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bindings/python'))
from nocturne_native import NativeScene

class StateSelectors(unittest.TestCase):
    def setUp(self):
        self.s = NativeScene(2030)
        self.cmd('environment', stars=0, style='solid')
        self.cmd('widget', id=1, kind='button', x=5, y=5, width=25, height=3,
                 text='Select me', border='rounded', material=1, alpha=.2)
        self.cmd('widget', id=2, kind='button', x=38, y=5, width=25, height=3,
                 text='Neighbour', border='rounded', material=1, alpha=.2)
    def tearDown(self): self.s.close()
    def cmd(self, op, **kw): return self.s.command({'op': op, **kw})
    def register(self, id=1, path='/lab/one', role='control', family='widget', targetId=None, **kw):
        return self.cmd('state-register', id=id, path=path, role=role,
                        target={'family':family, 'id':id if targetId is None else targetId}, **kw)
    def rule(self, id=1, selector=None, style=None, **kw):
        return self.cmd('style-rule', id=id, selector=selector or {'family':'widget'},
                        style=style or {'material':2, 'alpha':.8}, **kw)
    def entry(self, id=1): return next(x for x in self.s.info()['registeredStates'] if x['id']==id)
    def pixels(self, id=1): return [w for w in self.s.render().words() if w[3]==0x30000000|id]
    def testRegisterResolvesActualAuthoredAppearance(self):
        self.register();q=self.entry()
        self.assertEqual(q['path'],'/lab/one');self.assertEqual(q['role'],'control')
        self.assertEqual(q['authored']['material'],1);self.assertEqual(q['effective']['alpha'],.2)
    def testRoleSelectsOnlyMatchingRegisteredTargets(self):
        self.register();self.register(2,'/lab/two','passive')
        neighbour=self.pixels(2);before=self.pixels()
        self.rule(selector={'family':'widget','role':'control'})
        self.assertNotEqual(before,self.pixels());self.assertEqual(neighbour,self.pixels(2))
        self.assertEqual(self.entry(2)['effective']['material'],1)
    def testUnregisteredNeighboursAreUntouched(self):
        self.register();before=self.pixels(2);self.rule();self.assertEqual(before,self.pixels(2))
    def testPrefixIsSegmentBoundedNotRawStringPrefix(self):
        self.register(path='/lab/a');self.register(2,'/laboratory/a')
        self.rule(selector={'family':'widget','pathPrefix':'/lab'})
        self.assertEqual(self.entry()['effective']['material'],2)
        self.assertEqual(self.entry(2)['effective']['material'],1)
    def testExactPathDoesNotMatchDescendants(self):
        self.register(path='/lab/a');self.register(2,'/lab/a/b')
        self.rule(selector={'family':'widget','path':'/lab/a'})
        self.assertEqual(self.entry(2)['effective']['alpha'],.2)
    def testRemovalRestoresCurrentBaseNotCreationSnapshot(self):
        self.register();self.rule()
        self.cmd('widget',id=1,material=3,alpha=.4)
        self.assertEqual(self.entry()['effective']['material'],2)
        self.assertEqual(self.entry()['authored']['material'],3)
        self.cmd('remove-style-rule',id=1)
        self.assertEqual(self.entry()['effective']['material'],3)
        self.assertEqual(self.entry()['effective']['alpha'],.4)
    def testHigherPriorityThenStableRegistrationOrderWinsPerProperty(self):
        self.register();self.rule(id=50,priority=10,style={'material':2})
        self.rule(id=2,priority=0,style={'material':3,'alpha':.5})
        self.assertEqual(self.entry()['effective'],{'material':2,'backgroundMaterial':-1,'alpha':.5,'sampling':-1})
        self.rule(id=3,priority=10,style={'material':3})
        self.rule(id=50,priority=10,style={'material':1})
        self.assertEqual(self.entry()['effective']['material'],3)
    def testSelectedStateTracksActualWidgetSelection(self):
        self.register();self.rule(selector={'family':'widget','states':{'selected':True}})
        self.assertEqual(self.entry()['effective']['material'],1)
        self.cmd('widget',id=1,selected=True);self.assertEqual(self.entry()['effective']['material'],2)
        self.cmd('widget',id=1,selected=False);self.assertEqual(self.entry()['effective']['material'],1)
    def testPassivePointerMovementUpdatesHoverWithoutCameraDrag(self):
        self.register();self.rule(selector={'family':'widget','states':{'hover':True}})
        camera=self.s.info()['camera'];self.cmd('pointer',phase='move',x=8,y=6)
        self.assertTrue(self.entry()['states']['hover']);self.assertEqual(self.entry()['effective']['material'],2)
        self.assertEqual(camera,self.s.info()['camera'])
        self.cmd('pointer',phase='move',x=1,y=1);self.assertFalse(self.entry()['states']['hover'])
    def testPointerPressUpAndCancelAreIndependentOfDragCapture(self):
        self.register();self.rule(selector={'family':'widget','states':{'pressed':True}})
        self.cmd('pointer',phase='down',x=8,y=6)
        self.assertTrue(self.entry()['states']['pressed']);self.assertEqual(self.entry()['effective']['material'],2)
        self.cmd('pointer',phase='up',x=8,y=6);self.assertFalse(self.entry()['states']['pressed'])
        self.cmd('pointer',phase='down',x=8,y=6);self.cmd('pointer',phase='cancel',x=-1,y=-1)
        self.assertFalse(self.entry()['states']['pressed']);self.assertFalse(self.entry()['states']['hover'])
    def testDisabledAndInactiveRegistrations(self):
        self.register();self.rule(selector={'family':'widget','states':{'disabled':True}})
        self.cmd('widget',id=1,enabled=False);self.assertEqual(self.entry()['effective']['material'],2)
        self.cmd('state-update',id=1,active=False);self.assertEqual(self.entry()['effective']['material'],1)
        self.assertFalse(self.entry()['states']['active'])
    def testClampedLiveValueMapHasNoSourceMutation(self):
        self.register();self.cmd('define',path='/load',value=50)
        self.rule(style={'alpha':{'path':'/load','inputMin':0,'inputMax':100,'outputMin':0,'outputMax':1}})
        for v,expected in [(50,.5),(-100,0),(1000,1),(25,.25)]:
            self.cmd('set',path='/load',value=v)
            self.assertEqual(self.entry()['effective']['alpha'],expected)
            self.assertEqual(self.entry()['authored']['alpha'],.2)
    def testDescendingOutputMap(self):
        self.register();self.cmd('define',path='/load',value=25)
        self.rule(style={'alpha':{'path':'/load','inputMin':0,'inputMax':100,'outputMin':1,'outputMax':0}})
        self.assertEqual(self.entry()['effective']['alpha'],.75)
    def testCompoundGuardAndSchmittRelease(self):
        self.register();self.cmd('define',path='/heat',value=20);self.cmd('define',path='/enabled',value=1)
        self.rule(when={'all':[{'path':'/heat','comparison':'above','value':50,'hysteresis':5},
                              {'not':{'path':'/enabled','comparison':'equal','value':0}}]})
        for value,mat in [(51,2),(48,2),(45,1),(49,1),(51,2)]:
            self.cmd('set',path='/heat',value=value);self.assertEqual(self.entry()['effective']['material'],mat)
    def testBatchGuardNeverLatchesTransientIntermediateValue(self):
        self.register();self.cmd('define',path='/heat',value=20)
        self.rule(when={'path':'/heat','comparison':'above','value':50,'hysteresis':5})
        self.s.batch([{'op':'set','path':'/heat','value':60},{'op':'set','path':'/heat','value':48}])
        self.assertEqual(self.entry()['effective']['material'],1)
    def testRenderAndInfoNeverChangeSnapshot(self):
        self.register();self.rule();saved=self.s.snapshot()
        for _ in range(8):self.s.render();self.s.info()
        self.assertEqual(saved,self.s.snapshot())
    def testSnapshotReplayRetainsRulesAndInteractionState(self):
        self.register();self.rule(selector={'family':'widget','states':{'hover':True}})
        self.cmd('pointer',phase='move',x=8,y=6);saved=self.s.snapshot();frame=self.s.render().bytes
        self.cmd('remove-style-rule',id=1);self.s.restore(saved)
        self.assertEqual(frame,self.s.render().bytes);self.assertTrue(self.entry()['states']['hover'])
    def testDuplicateRegistryPathAndTargetRejectAtomically(self):
        self.register();saved=self.s.snapshot()
        for id,path,target in [(2,'/lab/one',2),(2,'/lab/two',1)]:
            with self.assertRaises(ValueError):self.register(id,path,targetId=target)
            self.assertEqual(saved,self.s.snapshot())
    def testRegistryUpdatePreservesTargetAndChangesRole(self):
        self.register();self.rule(selector={'family':'widget','role':'alarm'})
        self.cmd('state-update',id=1,role='alarm')
        self.assertEqual(self.entry()['effective']['material'],2)
    def testUnregisterRemovesEffectWithoutDestroyingTarget(self):
        self.register();before=self.pixels();self.rule();self.cmd('state-unregister',id=1)
        self.assertEqual(before,self.pixels());self.assertEqual(self.s.info()['registeredStates'],[])
    def testMalformedRuleReplacementRollsBackIncludingRuleOrder(self):
        self.register();self.rule();saved=self.s.snapshot()
        invalid=[{'style':{'bogus':1}}, {'selector':{'family':'widget','unknown':True}},
                 {'selector':{'family':'widget','states':{'hover':'yes'}}},
                 {'selector':{'family':'widget','path':'/bad//path'}},
                 {'selector':{'family':'widget','path':'/lab','pathPrefix':'/lab'}},
                 {'style':{'alpha':2}}, {'style':{'material':16}}, {'style':{'sampling':'auto'}},
                 {'style':{'alpha':{'path':'/missing','inputMin':0,'inputMax':1,'outputMin':0,'outputMax':1}}},
                 {'when':{'all':[]}}]
        for patch in invalid:
            with self.assertRaises(ValueError):self.rule(**patch)
            self.assertEqual(saved,self.s.snapshot(),patch)
    def testMappingsRejectEmptyOrReversedInputIntervals(self):
        self.register();self.cmd('define',path='/x',value=1)
        for a,b in [(1,1),(2,1)]:
            with self.assertRaises(ValueError):self.rule(style={'alpha':{'path':'/x','inputMin':a,'inputMax':b,'outputMin':0,'outputMax':1}})
    def testInapplicableFamilyPropertiesReject(self):
        for family,style in [('text',{'alpha':.5}),('widget',{'surfaceAlpha':.5}),('node',{'sampling':'braille'}),('prompt',{'material':1})]:
            with self.assertRaises(ValueError):self.rule(selector={'family':family},style=style)
    def testDiscretePropertiesDoNotAcceptFloatingMaps(self):
        self.cmd('define',path='/x',value=1)
        for prop in ['sampling','material','color']:
            with self.assertRaises(ValueError):self.rule(style={prop:{'path':'/x','inputMin':0,'inputMax':1,'outputMin':0,'outputMax':1}})
    def testRuleCapacityIsExplicitAndRemovalFreesSlot(self):
        self.register()
        for i in range(1,33):self.rule(id=i)
        saved=self.s.snapshot()
        with self.assertRaises(ValueError):self.rule(id=33)
        self.assertEqual(saved,self.s.snapshot());self.cmd('remove-style-rule',id=7);self.rule(id=33)
    def testTargetMustExistWhenRegistered(self):
        with self.assertRaises(ValueError):self.register(targetId=999)
    def testEventDrivesAppearanceWithoutAcknowledgingIntent(self):
        self.register();self.cmd('define',path='/approved',value=0);self.cmd('define',path='/enabled',value=1)
        self.rule(style={'alpha':{'path':'/approved','inputMin':0,'inputMax':1,'outputMin':.2,'outputMax':.9}})
        self.cmd('trigger',id=1,source='/enabled',comparison='above',threshold=0,event='/approve',target='/approved',value=1)
        self.cmd('status',id=1,text='Inspect',durationMs=0,actions=[{'id':1,'label':'Inspect','event':'/approve'}])
        self.cmd('notification-action',id=1,actionId=1)
        self.assertEqual(self.entry()['effective']['alpha'],.9);self.assertEqual(len(self.s.info()['intents']),1)
    def testExtendedValueBindingsRemainAuthoredAndValidate(self):
        self.cmd('define',path='/selected',value=0,binding={'family':'widget','id':1,'field':'selected'})
        self.register();self.rule(selector={'family':'widget','states':{'selected':True}})
        self.cmd('set',path='/selected',value=1);self.assertEqual(self.entry()['effective']['material'],2)
        saved=self.s.snapshot()
        with self.assertRaises(ValueError):self.cmd('set',path='/selected',value=.5)
        self.assertEqual(saved,self.s.snapshot())
    def testMaterialAndAlphaBindingsDoNotRestartReveals(self):
        self.cmd('widget',id=1,kind='pie',data=[1],revealMs=1000)
        self.cmd('define',path='/alpha',value=.3,binding={'family':'widget','id':1,'field':'alpha'})
        self.s.advance_to(300000);at=self.s.info()['widgets'][0]['plot']['revealAtUs']
        self.cmd('set',path='/alpha',value=.9)
        self.assertEqual(at,self.s.info()['widgets'][0]['plot']['revealAtUs'])
    def testLeafAppearanceDoesNotAlterMotionOrDeposits(self):
        self.cmd('emitter',id=1,effect='weather/autumn-drift',count=8,runningTimeMs=0)
        self.register(family='emitter');self.s.advance_to(700000);saved=self.s.snapshot();particles=self.s.particles()
        self.rule(selector={'family':'emitter'},style={'material':3,'sampling':'half','surfaceAlpha':.8,'veinContrast':1})
        self.s.render();self.assertEqual(particles,self.s.particles());self.s.advance_to(1000000);later=self.s.particles()
        self.s.restore(saved);self.s.advance_to(1000000);self.assertEqual(later,self.s.particles())
    def testFloorAndMeshSamplingRemainIndependent(self):
        self.register(id=10,family='floor',targetId=0,path='/scene/floor')
        self.cmd('mesh',triangles=[{'a':[-1,1,0],'b':[1,1,0],'c':[0,2,0]}])
        self.register(id=11,family='mesh',targetId=0,path='/scene/mesh')
        self.rule(selector={'family':'floor'},style={'sampling':'cell','alpha':.7})
        self.assertEqual(self.entry(10)['effective']['sampling'],0)
        self.assertEqual(self.entry(11)['effective']['sampling'],1)
    def testOldRawSnapshotSchemaRejectsEvenWithValidStateCrc(self):
        import struct
        data=bytearray(self.s.snapshot());struct.pack_into('<I',data,12,0x20261002)
        with self.assertRaises(ValueError):self.s.restore(data)


    def testEveryAdvertisedTargetFamilyResolvesNativeProperties(self):
        components=[('window',{'op':'window','id':3,'title':'Kept','text':'body'}, {'material':2,'alpha':.6}),
                    ('text',{'op':'text','id':3,'text':'Retained','effect':'text/instant-ink'}, {'material':2}),
                    ('area',{'op':'area','id':3}, {'material':2,'alpha':.6}),
                    ('indicator',{'op':'indicator','id':3,'sequence':'abcd'}, {'material':2}),
                    ('node',{'op':'node','id':3,'label':'Retained'}, {'color':0x123456})]
        for family,command,style in components:
            self.s.command(command);self.register(id=3,family=family,path='/family/'+family)
            self.rule(selector={'family':family},style=style)
            for key,value in style.items():self.assertEqual(self.entry(3)['effective'][key],value)
            self.s.render();self.cmd('state-unregister',id=3);self.cmd('remove-style-rule',id=1)
        self.register(id=4,family='prompt',targetId=0,path='/family/prompt')
        self.rule(selector={'family':'prompt'},style={'alpha':.9})
        self.assertEqual(self.entry(4)['effective']['alpha'],.9)
    def testNewDirectBindingFamiliesRejectBadFieldsAndRanges(self):
        cases=[('window',{'op':'window','id':3},'alpha',.7),('text',{'op':'text','id':3,'text':'x'},'material',2),
               ('area',{'op':'area','id':3},'alpha',.8),('floor',None,'alpha',.4)]
        for family,command,field,value in cases:
            if command:self.s.command(command)
            target=0 if family=='floor' else 3
            self.cmd('define',path='/binding/'+family,value=value,binding={'family':family,'id':target,'field':field})
            saved=self.s.snapshot()
            with self.assertRaises(ValueError):self.cmd('set',path='/binding/'+family,value=999)
            self.assertEqual(saved,self.s.snapshot())
    def testRegistryActivationCanBeBoundToValues(self):
        self.register();self.rule()
        self.cmd('define',path='/activate',value=1,binding={'family':'state','id':1,'field':'active'})
        self.cmd('set',path='/activate',value=0);self.assertEqual(self.entry()['effective']['material'],1)
        self.cmd('set',path='/activate',value=1);self.assertEqual(self.entry()['effective']['material'],2)
    def testLeafOnlyRulesRejectMatchingNonLeafRegistrations(self):
        self.cmd('emitter',id=1,effect='weather/silver-squall',count=1)
        self.register(family='emitter');saved=self.s.snapshot()
        with self.assertRaises(ValueError):self.rule(selector={'family':'emitter'},style={'surfaceAlpha':.3})
        self.assertEqual(saved,self.s.snapshot())
    def testInactiveRuleStillRejectsFutureInapplicableTarget(self):
        self.rule(selector={'family':'emitter','role':'leaf'},style={'veinContrast':1},enabled=False)
        self.cmd('emitter',id=1,effect='weather/silver-squall',count=1);saved=self.s.snapshot()
        with self.assertRaises(ValueError):self.register(family='emitter',role='leaf')
        self.assertEqual(saved,self.s.snapshot())
    def testSelectorIdentityRangeIsFamilySpecific(self):
        for selector in [{'family':'widget','id':0},{'family':'floor','id':1},{'family':'prompt','id':1}]:
            with self.assertRaises(ValueError):self.rule(selector=selector,style={'alpha':.5})
    def testClearInstanceLeavesDormantRegistrationAndRecreationUsesId(self):
        self.cmd('emitter',id=1,effect='weather/autumn-drift',count=1)
        self.register(family='emitter');self.rule(selector={'family':'emitter'},style={'alpha':.5})
        self.cmd('clear-instance',id=1);self.assertFalse(self.entry()['exists'])
        self.cmd('emitter',id=1,effect='weather/autumn-drift',count=1)
        self.assertTrue(self.entry()['exists']);self.assertEqual(self.entry()['effective']['alpha'],.5)
    def testRootPrefixSelectsAllRegisteredPaths(self):
        self.register();self.register(2,'/other/two');self.rule(selector={'family':'widget','pathPrefix':'/'})
        self.assertEqual(self.entry(1)['effective']['material'],2);self.assertEqual(self.entry(2)['effective']['material'],2)
    def testFailedBatchDoesNotCommitStylesOrInput(self):
        self.register();saved=self.s.snapshot()
        with self.assertRaises(ValueError):self.s.batch([{'op':'input','text':'atomic'},
            {'op':'style-rule','id':1,'selector':{'family':'widget'},'style':{'alpha':2}}])
        self.assertEqual(saved,self.s.snapshot())
    def testRegistryCapacityCoversMultipleFamiliesAndFreesSlot(self):
        id=1
        for family,n in [('text',24),('area',16),('indicator',24)]:
            for target in range(1,n+1):
                self.cmd(family,id=target,**({'text':'x'} if family=='text' else {'sequence':'ab'} if family=='indicator' else {}))
                self.register(id=id,family=family,targetId=target,path='/capacity/'+family+'/'+str(target));id+=1
        saved=self.s.snapshot()
        with self.assertRaises(ValueError):self.register(id=65,family='floor',targetId=0,path='/floor')
        self.assertEqual(saved,self.s.snapshot());self.cmd('state-unregister',id=1)
        self.register(id=65,family='floor',targetId=0,path='/floor')

if __name__=='__main__':unittest.main()
