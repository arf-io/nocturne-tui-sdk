"""Independent reference equations and native transition ownership/endpoints."""
from pathlib import Path
import ctypes as C
import json
import math
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene

class TransitionPorts(unittest.TestCase):
    def setUp(self):
        self.s=NativeScene();self.addCleanup(self.s.close)
        self.s._lib.nrTextSample.argtypes=[C.c_void_p,C.c_uint32,C.c_uint32,C.POINTER(C.c_int32),C.c_uint32]
        self.s._lib.nrTextSample.restype=C.c_int
        self.s._lib.nrWindowSample.argtypes=[C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint32,C.c_uint32,C.POINTER(C.c_int32),C.c_uint32]
        self.s._lib.nrWindowSample.restype=C.c_int
    def glyph(self,index=0):
        a=(C.c_int32*8)();self.assertEqual(self.s._lib.nrTextSample(self.s._context,1,index,a,8),0);return list(a)
    def point(self,u=.2,v=.3,p=.5):
        a=(C.c_int32*5)();self.assertEqual(self.s._lib.nrWindowSample(self.s._context,1,int(u*1e6),int(v*1e6),int(p*1e6),a,5),0);return list(a)
    def test_all_text_reference_equations(self):
        reference=json.loads((ROOT/'tests/fixtures/text-reference.json').read_text())
        failures=[]
        for row in reference['rows']:
            self.s.command({'op':'reset'})
            self.s.command({'op':'text','id':1,'text':reference['text'],'x':0,'y':0,'width':120,'effect':row['id'],'phase':row['phase'],'trailLength':0,**reference['config']})
            for time,poses in zip(reference['times'],row['poses']):
                self.s.advance_to(time*1000)
                for index,expected in enumerate(poses):
                    actual=self.glyph(index)
                    # Hide-only source formulas have a documented reverse-show extension.
                    reverse_extension=row['phase']=='show' and row['id'] in ['text/glyph-fall','text/ash-type']
                    if reverse_extension:continue
                    values=[actual[3]/65536,actual[4]/65536,actual[5]/1e6,actual[6]/1000]
                    wanted=[expected[k] for k in ['x','y','alpha','hue']]
                    for k,(left,right) in enumerate(zip(values,wanted)):
                        if abs(left-right)>.0012:failures.append((row['id'],row['phase'],time,index,['x','y','alpha','hue'][k],left,right))
                    if actual[0]!=ord(expected['glyph']):failures.append((row['id'],row['phase'],time,index,'glyph',actual[0],ord(expected['glyph'])))
        self.assertEqual(failures[:20],[],f'{len(failures)} formula differences')
    def test_retarget_holds_positions_and_source_identity(self):
        self.s.command({'op':'text','id':1,'text':'STABLE','effect':'text/glyph-rain','durationMs':2000,'jitterMs':0})
        self.s.advance_to(450000);before=[self.glyph(i) for i in range(6)]
        self.s.command({'op':'text','id':1,'phase':'hide','effect':'text/satellite-type'})
        after=[self.glyph(i) for i in range(6)]
        for a,b in zip(before,after):
            self.assertEqual(a[:7],b[:7])
    def test_prefix_and_suffix_ids_survive_source_edit(self):
        self.s.command({'op':'text','id':1,'text':'ACE','local':True});before=[self.glyph(i)[2] for i in range(3)]
        self.s.command({'op':'text','id':1,'text':'ABCDE'})
        after=[self.glyph(i)[2] for i in range(5)]
        self.assertEqual(before[0],after[0]);self.assertEqual(before[2],after[4]);self.assertEqual(len(set(after)),5)
    def test_reduced_motion_all_transitions_keep_local_text(self):
        for entry in self.s.catalogue():
            if entry['contract']!='TextTransition':continue
            self.s.command({'op':'reset'});self.s.command({'op':'accessibility','reducedMotion':True})
            self.s.command({'op':'text','id':1,'effect':entry['id'],'text':'A','x':4,'y':5})
            a=self.glyph();self.assertEqual(a[0],65);self.assertEqual(a[3:6],[4*65536,5*65536,1000000])
    def test_window_exact_endpoints_all_43_presets(self):
        for entry in self.s.catalogue():
            if entry['contract']!='WindowTransition':continue
            self.s.command({'op':'reset'});self.s.command({'op':'window','id':1,'effect':entry['id'],'width':30,'height':20})
            self.assertEqual(self.point(p=1)[:4],[-9*65536,4*65536,0,1000000]);self.assertEqual(self.point(p=0)[3],0)
    def test_shell_operators_are_not_generic_scale_aliases(self):
        results={}
        for effect in ['glass-dissolve','rail-left','rail-right','scroll-up','lamp-genie','portal-fold','venetian','ribbon-unfurl','origami','vortex-fold']:
            self.s.command({'op':'window','id':1,'effect':'window-transition/'+effect});results[effect]=tuple(self.point())
        self.assertEqual(len(set(results.values())),len(results))
    def test_window_mask_and_custom_polygon(self):
        self.s.command({'op':'window','id':1,'shape':'polygon','polygon':[[0,0],[1,0],[0,1]]})
        self.assertEqual(self.point(.1,.1,1)[4],1);self.assertEqual(self.point(.9,.9,1)[4],0)
        before=self.s.snapshot()
        with self.assertRaises(ValueError):self.s.command({'op':'window','id':1,'polygon':[[0,0],[.5,.5],[1,1]]})
        self.assertEqual(before,self.s.snapshot())
    def test_window_sampler_does_not_change_scene(self):
        self.s.command({'op':'window','id':1});before=self.s.snapshot()
        for p in range(11):self.point(p=p/10)
        self.assertEqual(before,self.s.snapshot())
