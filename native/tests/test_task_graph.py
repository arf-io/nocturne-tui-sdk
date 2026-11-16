"""Exercise the shipped task/work graph through the actual C-owned scene."""
from pathlib import Path
import json, os, sys, unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene

class TaskGraphTests(unittest.TestCase):
    def setUp(self):
        self.commands=[json.loads(line) for line in (ROOT/'examples/task_graph.ndjson').read_text().splitlines() if line]
        self.scene=NativeScene(2030,library=os.environ.get('NOCTURNE_TEST_LIBRARY'))
        for c in self.commands:self.scene.command(c)
        self.scene.advance_to(900000)
    def tearDown(self):
        if hasattr(self,'scene'):self.scene.close()
    def testSharedTaskIdentityAndFullMetadata(self):
        nodes=self.scene.info()['nodes'];ids=[n['id'] for n in nodes]
        self.assertEqual(len(ids),len(set(ids)))
        for c in self.commands:
            if c['op']=='node':
                node=next(n for n in nodes if n['id']==c['id'])
                self.assertEqual(node['label'],c['label']);self.assertEqual(node['sha'],c['sha'])
        # The reusable Action has two referring parents, not two cloned node records.
        edges=[c for c in self.commands if c['op']=='edge' and c['to']==7]
        self.assertEqual({c['from'] for c in edges},{4,5});self.assertEqual(ids.count(7),1)
    def testBothDimensionsRenderAndRetainDocument(self):
        self.scene.command({'op':'input','text':'retained graph note'})
        frames=[]
        for dims,stamp in [(2,1900000),(3,2900000)]:
            self.scene.command({'op':'layout','mode':'layered','dimensions':dims,'spacing':30})
            self.scene.advance_to(stamp)
            frame=self.scene.render();frames.append(frame.bytes)
            self.assertTrue(any(w[3]>>28==1 for w in frame.words()))
            self.assertEqual(self.scene.info()['prompt']['text'],'retained graph note')
        self.assertNotEqual(frames[0],frames[1])
    def testOwnedHitSelectsWithoutClickWeather(self):
        frame=self.scene.render();i,word=next((i,w) for i,w in enumerate(frame.words()) if w[3]>>28==1)
        before=self.scene.info()['fieldCount'];x=i%frame.width;y=i//frame.width
        for phase in ['down','up']:self.scene.command({'op':'pointer','phase':phase,'x':x,'y':y})
        self.assertEqual(self.scene.info()['selection'],word[3]&0xfffffff)
        self.assertEqual(self.scene.info()['fieldCount'],before)
    def testRenderAndMetadataEditPreserveCurrentPose(self):
        before=self.scene.snapshot();frame=self.scene.render();self.scene.info()
        self.assertEqual(self.scene.snapshot(),before)
        self.scene.command({'op':'select','id':7,'durationMs':1800})
        self.scene.advance_to(1100000)
        positions=[n['position'] for n in self.scene.info()['nodes']]
        self.scene.command({'op':'node','id':7,'status':'inspected','shaPrefix':8})
        self.assertEqual([n['position'] for n in self.scene.info()['nodes']],positions)
        self.assertEqual(self.scene.info()['nodes'][6]['sha'],next(c['sha'] for c in self.commands if c['op']=='node' and c['id']==7))
    def testFlatFramingShowsEveryTaskLabel(self):
        self.scene.command({'op':'camera','profile':'default','position':[0,8,162],'yaw':0,'pitch':0,'roll':0,'fov':64,'orthographic':False})
        self.scene.command({'op':'layout','dimensions':2,'mode':'layered','spacing':30})
        self.scene.advance_to(1900000)
        frame=self.scene.render();words=list(frame.words())
        screen='\n'.join(''.join(chr(w[0]) for w in words[y*frame.width:(y+1)*frame.width]) for y in range(frame.height))
        for c in self.commands:
            if c['op']=='node':self.assertIn(c['label'],screen)
    def testInspectorScrollStopsAtLastContentPage(self):
        self.scene.command({'op':'resize','width':80,'height':18})
        self.scene.command({'op':'select','id':7,'durationMs':1800})
        self.scene.command({'op':'inspector-scroll','rows':8192})
        info=self.scene.info();scroll=info['inspectorScroll']
        self.assertGreater(scroll,0)
        self.assertLess(scroll,8192)
        frame=self.scene.render();words=list(frame.words())
        panel=range(max(0,frame.width-37),frame.width)
        content=[]
        for y in range(4,min(frame.height,info.get('promptTop',frame.height))):
            row=''.join(chr(words[y*frame.width+x][0]) for x in panel)
            if row.strip(' ▀▄█╭╮╰╯│─'):
                content.append(row)
        self.assertTrue(content,'last inspector page must retain visible graph detail')

    def testInspectorWheelScrollStopsAtLastContentPage(self):
        self.scene.command({'op':'resize','width':80,'height':18})
        self.scene.command({'op':'select','id':7,'durationMs':1800})
        for _ in range(28):
            self.scene.command({'op':'wheel','x':78,'y':8,'delta':-100})
        scroll=self.scene.info()['inspectorScroll']
        self.assertGreater(scroll,0)
        self.assertLess(scroll,8192)

    def testInspectorPageDownDoesNotScrollPastShortContent(self):
        self.scene.command({'op':'select','id':7,'durationMs':1800})
        self.scene.command({'op':'key','key':'PageDown'})
        self.assertEqual(self.scene.info()['inspectorScroll'],0)
        frame=self.scene.render();words=list(frame.words())
        panel=range(max(0,frame.width-37),frame.width)
        text=''.join(chr(words[y*frame.width+x][0]) for y in range(frame.height) for x in panel)
        self.assertIn('Action: verify shared artifact',text)

    def testInspectorWheelOutsidePanelKeepsCameraOwnership(self):
        self.scene.command({'op':'resize','width':80,'height':18})
        self.scene.command({'op':'select','id':7,'durationMs':1800})
        before=self.scene.info()['camera']['position']
        self.scene.command({'op':'wheel','x':79,'y':8,'delta':1})
        info=self.scene.info()
        self.assertEqual(info['inspectorScroll'],0)
        self.assertNotEqual(info['camera']['position'],before)

    def testInspectorWheelBelowPanelKeepsCameraOwnership(self):
        self.scene.command({'op':'resize','width':80,'height':18})
        self.scene.command({'op':'select','id':7,'durationMs':1800})
        frame=self.scene.render()
        panelRows=[i//frame.width for i,w in enumerate(frame.words()) if i%frame.width==78 and w[3]==0x7fffffff]
        self.assertTrue(panelRows,'rendered inspector must own cells at its right edge')
        outsideY=max(panelRows)+1
        self.assertLess(outsideY,frame.height)
        before=self.scene.info()['camera']['position']
        self.scene.command({'op':'wheel','x':78,'y':outsideY,'delta':1})
        info=self.scene.info()
        self.assertEqual(info['inspectorScroll'],0)
        self.assertNotEqual(info['camera']['position'],before)

    def testInspectorRendersFullShaAcrossWrappedRows(self):
        self.scene.command({'op':'resize','width':80,'height':18})
        self.scene.command({'op':'select','id':7,'durationMs':1800})
        sha=next(n['sha'] for n in self.scene.info()['nodes'] if n['id']==7)
        frame=self.scene.render();words=list(frame.words())
        textRows=[]
        for y in range(4,frame.height):
            textRows.append(''.join(chr(words[y*frame.width+x][0]) for x in range(frame.width-35,frame.width-3)))
        self.assertIn(sha[:32],textRows)
        self.assertIn(sha[32:],textRows)

    def testGraphEvidenceSnapshotRoundTripRestoresSelectedInspector(self):
        self.scene.command({'op':'resize','width':80,'height':18})
        self.scene.command({'op':'select','id':7,'durationMs':1800})
        self.scene.command({'op':'inspector-scroll','rows':4})
        beforeInfo=self.scene.info()
        self.assertGreater(beforeInfo['inspectorScroll'],0)
        beforeNodes=[(n['id'],n['label'],n['sha']) for n in beforeInfo['nodes']]
        beforeFrame=self.scene.render().bytes
        snapshot=self.scene.snapshot()
        self.scene.command({'op':'reset'})
        self.assertEqual(self.scene.info()['nodes'],[])
        self.scene.restore(snapshot)
        afterInfo=self.scene.info()
        self.assertEqual([(n['id'],n['label'],n['sha']) for n in afterInfo['nodes']],beforeNodes)
        self.assertEqual(afterInfo['selection'],beforeInfo['selection'])
        self.assertEqual(afterInfo['inspectorScroll'],beforeInfo['inspectorScroll'])
        self.assertEqual(self.scene.render().bytes,beforeFrame)

    def testGalleryUsesExactStandaloneCommands(self):
        recipe=next(x for x in json.loads((ROOT/'recipes.json').read_text()) if x['id']=='task-graph')
        self.assertEqual(recipe['commands'],self.commands)

if __name__=='__main__':unittest.main()
