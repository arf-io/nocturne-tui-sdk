"""Current native contracts: public measurement, transition continuity, and status."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene

class ContractRefinementTests(unittest.TestCase):
    def setUp(self): self.scene=NativeScene(17)
    def tearDown(self): self.scene.close()
    def cmd(self,op,**kw):return self.scene.command({'op':op,**kw})
    def testGraphCardFieldsAreConfigurableAndNotDestructive(self):
        self.cmd('node',id=1,label='Full node name',kind='Request',status='review',sha='a'*64,detail='Complete notes',minColumns=20,maxColumns=88,padding=2,shaPrefix=12,showDetail=False)
        record=self.scene.info()['nodes'][0]
        self.assertEqual(record['sha'],'a'*64)
        self.assertEqual(record['detail'],'Complete notes')
        self.assertEqual(record['card']['shaPrefix'],12)
        self.assertFalse(record['card']['showDetail'])
        self.assertEqual(record['card']['padding'],2)
    def testMetadataUpdateDoesNotTeleportMovingNode(self):
        self.cmd('node',id=1,label='A',position=[-30,3,0]);self.cmd('node',id=2,label='B',position=[25,8,0])
        self.cmd('edge',**{'from':1,'to':2});self.cmd('select',id=2,durationMs=1800)
        self.scene.advance_to(300000)
        before=self.scene.info()['nodes'][0]['position']
        self.cmd('node',id=1,status='running')
        self.assertEqual(self.scene.info()['nodes'][0]['position'],before)
        self.scene.advance_to(1000000)
        self.assertNotEqual(self.scene.info()['nodes'][0]['position'],before)
    def testCardWidthMeasuresEachLineNotNewlineCount(self):
        self.cmd('node',id=1,label='A\nB\nC\nD',kind='',minColumns=8,maxColumns=100,padding=1,showKind=False,showSha=False)
        self.assertEqual(self.scene.info()['nodes'][0]['card']['width'],8)
    def testFullLabelNotQuestionMarkEllipsis(self):
        label='Complete contextual request name with all of its characters'
        self.cmd('camera',position=[0,8,100],yaw=0,pitch=0,orthographic=True,span=100)
        self.cmd('node',id=1,label=label,kind='',position=[0,8,0],minColumns=70,maxColumns=80,showKind=False,showSha=False)
        frame=self.scene.render();owned=''.join(chr(w[0]) for w in frame.words() if w[3]==0x10000001)
        self.assertIn(label,owned)
    def testMeasurementBoundsRejectAtomically(self):
        self.cmd('node',id=1,label='keep')
        before=self.scene.snapshot()
        for bad in [{'minColumns':80,'maxColumns':20},{'padding':8,'minColumns':8,'maxColumns':12},{'shaPrefix':130}]:
            with self.assertRaises(Exception):self.cmd('node',id=1,**bad)
            self.assertEqual(before,self.scene.snapshot())
    def testMetadataOnlyEditRetainsNodeLayoutDestination(self):
        self.cmd('node',id=1,label='Long complete name');self.cmd('layout',mode='radial',dimensions=3)
        self.scene.advance_to(400000);before=self.scene.info()['nodes'][0]['position']
        self.cmd('node',id=1,shaPrefix=9)
        self.assertEqual(before,self.scene.info()['nodes'][0]['position'])
    def testWindowDocumentMeasurementsPublic(self):
        self.cmd('window',id=1,text='Line one\nLine two',title='T',padding=2,border='double',fadeStartRatio=1.0,fadeEndRatio=.25,chromeSize=3)
        w=self.scene.info()['windows'][0]
        self.assertEqual(w['readability']['padding'],2)
        self.assertEqual(w['readability']['chromeSize'],3)
        self.assertEqual(w['text'],'Line one\nLine two')
    def testWindowFadeBoundsRejectAtomically(self):
        self.cmd('window',id=1,text='keep');before=self.scene.snapshot()
        with self.assertRaises(Exception):self.cmd('window',id=1,fadeStartRatio=.2,fadeEndRatio=.5)
        self.assertEqual(before,self.scene.snapshot())
    def testWindowMetadataEditRetainsMinimizedIntent(self):
        self.cmd('window',id=1,text='retained');self.cmd('window-action',id=1,action='minimize')
        self.scene.advance_to(900000);self.cmd('window',id=1,title='renamed')
        self.assertEqual(self.scene.info()['windows'][0]['visible'],0)


class DockReadabilityTests(unittest.TestCase):
    def testDockFitsOrdinaryCompleteTitle(self):
        with NativeScene(19) as scene:
            title='ATLAS / orchestration'
            scene.command({'op':'window','id':1,'title':title,'text':'complete document'})
            scene.command({'op':'window-action','id':1,'action':'minimize'})
            scene.advance_to(1000000)
            frame=scene.render()
            dock=''.join(chr(w[0]) for w in frame.words() if (w[3]&0xf0000000)==0x50000000)
            self.assertIn(title,dock)

if __name__=='__main__':unittest.main()
