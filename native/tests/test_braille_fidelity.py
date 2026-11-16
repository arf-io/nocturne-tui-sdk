"""Subcell shape and stable-glyph regressions, independent of reference screenshots."""
import ctypes as C
import math
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bindings/python'))
from nocturne_native import NativeScene
DOTS = (1, 8, 2, 16, 4, 32, 64, 128)
BLOCKS = set(range(0x2580, 0x25a0))
class Cell(C.Structure):
    _fields_ = [(name,C.c_uint32) for name in ('glyph','foreground','background','id')]
class BrailleFidelity(unittest.TestCase):
    def scene(self):
        scene=NativeScene(seed=42);self.addCleanup(scene.close)
        scene.command({'op':'resize','width':96,'height':40})
        scene.command({'op':'environment','stars':0,'style':'solid','background':0x101010,'sampling':'braille'})
        return scene
    def widget(self,scene,kind='donut',**opts):
        config={'op':'widget','id':31,'kind':kind,'x':8,'y':5,'width':32,'height':14,'padding':0,'alpha':0,'data':[1]}
        config.update(opts);scene.command(config);return config
    def marks(self,scene):
        return [(i,word)for i,word in enumerate(scene.render().words())if word[3]==0x3000001f and word[0]!=32]
    def test_explicit_braille_scene_never_selects_half_blocks(self):
        s=self.scene();s.command({'op':'environment','stars':300})
        s.advance_to(900000)
        cells=s.render().words()
        self.assertFalse(any(g in BLOCKS for g,_,_,ident in cells if ident==0))
    def test_all_256_masks_keep_their_exact_braille_identity(self):
        s=self.scene();fn=s._lib.nrResolveSamples
        fn.argtypes=[C.POINTER(Cell),C.POINTER(C.c_uint32),C.POINTER(C.c_uint32),C.c_uint32,C.c_int]
        base=(C.c_uint32*8)(*[0x101010]*8)
        for mask in range(256):
            values=(C.c_uint32*8)(*[0xd9e8ed if mask&d else 0x101010 for d in DOTS])
            cell=Cell();fn(C.byref(cell),values,base,mask,2)
            self.assertEqual(cell.glyph,0x2800+mask if mask else 32,hex(mask))
            self.assertEqual(cell.background,0x101010)
    def test_geometry_encoding_is_not_a_luminance_threshold(self):
        s=self.scene();fn=s._lib.nrResolveSamples
        fn.argtypes=[C.POINTER(Cell),C.POINTER(C.c_uint32),C.POINTER(C.c_uint32),C.c_uint32,C.c_int]
        base=(C.c_uint32*8)(*[0xc0c0c0]*8)
        for color in (0xbfbfbf,0x101010,0xc1c1c1,0xe0c0c0):
            for mask in (1,7,85,255):
                pixels=(C.c_uint32*8)(*[color if mask&d else 0xc0c0c0 for d in DOTS]);cell=Cell()
                fn(C.byref(cell),pixels,base,mask,2);self.assertEqual(cell.glyph,0x2800+mask)
    def test_donut_uses_partial_and_full_eight_dot_cells(self):
        s=self.scene();self.widget(s);marks=self.marks(s)
        self.assertGreater(len(marks),40)
        glyphs={w[0]for _,w in marks}
        self.assertTrue(all(0x2800<g<=0x28ff for g in glyphs),glyphs)
        self.assertIn(0x28ff,glyphs)
        self.assertGreater(len(glyphs),12)
    def test_ring_matches_an_independent_subcell_circle_equation(self):
        s=self.scene();self.widget(s,innerRadius=.61,cellAspect=2)
        cells=s.render().words();iw,ih=32,14;radius=min(iw,ih*2)-.5
        for y in range(ih):
            for x in range(iw):
                expected=0
                for dy in range(4):
                    for dx in range(2):
                        vx=x*2+dx+.5-iw;vy=y*4+dy+.5-ih*2;r=math.hypot(vx,vy)
                        if radius*.61<=r<=radius:expected|=DOTS[dy*2+dx]
                g,_,_,ident=cells[(y+5)*96+x+8]
                observed=g-0x2800 if ident==0x3000001f and 0x2800<=g<=0x28ff else 0
                self.assertEqual(observed,expected,(x,y))
    def test_pie_sampling_is_per_dot_not_a_changed_full_block_glyph(self):
        s=self.scene();self.widget(s,'pie',data=[9,1]);glyphs={w[0]for _,w in self.marks(s)}
        self.assertIn(0x28ff,glyphs);self.assertGreater(len(glyphs),10)
        self.assertFalse(glyphs&BLOCKS)
    def test_empty_chart_has_no_geometric_hits(self):
        s=self.scene();self.widget(s,data=[0,0]);self.assertEqual(self.marks(s),[])
        cells=s.render().words();self.assertNotEqual(cells[10*96+20][3],0x3000001f)
    def test_donut_hole_is_not_an_invisible_hit_rectangle(self):
        s=self.scene();self.widget(s,alpha=.3)
        self.assertNotEqual(s.render().words()[12*96+24][3],0x3000001f)
    def test_line_changes_within_a_single_text_row(self):
        s=self.scene();self.widget(s,'line',data=[.20,.20])
        a={i:w[0]for i,w in self.marks(s)}
        s.command({'op':'widget','id':31,'data':[.215,.215]})
        b={i:w[0]for i,w in self.marks(s)}
        self.assertNotEqual(a,b);self.assertTrue(all(0x2800<g<=0x28ff for g in b.values()))
    def test_single_line_sample_is_visible(self):
        s=self.scene();self.widget(s,'line',data=[.5]);self.assertTrue(self.marks(s))
    def test_scatter_and_edges_use_subcell_geometry(self):
        for kind,data in [('scatter',[0,.1,.5,.5,1,.9]),('edge',[0,0,.5,.9,1,.1])]:
            s=self.scene();self.widget(s,kind,data=data)
            self.assertTrue(self.marks(s));self.assertTrue(all(0x2800<w[0]<=0x28ff for _,w in self.marks(s)))
    def test_bars_and_progress_do_not_quantize_to_full_blocks(self):
        for kind,opts in [('bars',{'data':[.234,.68,.43]}),('progress',{'value':.671})]:
            s=self.scene();self.widget(s,kind,**opts)
            self.assertTrue(self.marks(s));self.assertFalse(any(w[0]in BLOCKS for _,w in self.marks(s)))
    def test_all_animation_ticks_keep_the_same_glyph_family(self):
        s=self.scene();self.widget(s,'pie',data=[3,2,4],revealMs=1000)
        counts=[]
        for tick in range(61):
            s.advance_to(tick*1000000//60);marks=self.marks(s)
            self.assertFalse(any(w[0]in BLOCKS for _,w in marks),(tick,marks[:2]))
            counts.append(sum((w[0]-0x2800).bit_count()for _,w in marks if 0x2800<=w[0]<=0x28ff))
        self.assertEqual(counts[0],0);self.assertGreater(counts[-1],100);self.assertEqual(counts,sorted(counts))
    def test_digits_keep_geometry_in_the_selected_sampler(self):
        s=self.scene();self.widget(s,'digits',value=88)
        self.assertTrue(self.marks(s));self.assertTrue(all(0x2800<w[0]<=0x28ff for _,w in self.marks(s)))
        s.command({'op':'widget','id':31,'sampling':'cell'})
        self.assertTrue(any(w[0]==0x2588 for _,w in self.marks(s)))
    def test_default_braille_pie_retains_weighted_sectors(self):
        s=self.scene();self.widget(s,'pie',width=70,height=29,data=[90,10])
        colors=[s.oklch(.72,.09,180),s.oklch(.72,.09,259)]
        counts=[sum((w[0]-0x2800).bit_count()for _,w in self.marks(s)if w[1]==col and 0x2800<=w[0]<=0x28ff)for col in colors]
        self.assertGreater(counts[0],counts[1]*7,counts);self.assertLess(counts[0],counts[1]*12,counts)
    def test_replay_and_reveal_state_do_not_depend_on_display_rate(self):
        a=self.scene();b=self.scene()
        for s in (a,b):self.widget(s,'donut',revealMs=1000)
        for tick in range(31):a.advance_to(tick*1000000//30);a.render()
        for tick in range(61):b.advance_to(tick*1000000//60);b.render()
        self.assertEqual(a.snapshot(),b.snapshot());self.assertEqual(a.render().bytes,b.render().bytes)
        a.command({'op':'widget','id':31,'replay':True});self.assertEqual(self.marks(a),[])
    def test_same_endpoint_reveal_does_not_restart_on_color_change(self):
        s=self.scene();self.widget(s,'pie',revealMs=1000);s.advance_to(500000)
        before=[(i,w[0])for i,w in self.marks(s)]
        s.command({'op':'widget','id':31,'material':3})
        self.assertEqual([(i,w[0])for i,w in self.marks(s)],before)
    def test_line_reveal_has_declared_subcell_sweep(self):
        s=self.scene();self.widget(s,'line',data=[.5,.5],revealMs=1000)
        self.assertEqual(self.marks(s),[]);s.advance_to(500000)
        count=sum((w[0]-0x2800).bit_count()for _,w in self.marks(s))
        s.advance_to(1000000)
        final=sum((w[0]-0x2800).bit_count()for _,w in self.marks(s))
        self.assertGreater(count,0);self.assertLess(count,final)
    def test_new_settings_are_rejected_on_inapplicable_widgets(self):
        s=self.scene()
        for kind,patch in [('text',{'sampling':'braille'}),('line',{'innerRadius':.4}),('bars',{'sweepAngle':90}),('button',{'revealMs':500})]:
            with self.assertRaises(ValueError):self.widget(s,kind,**patch)
    def test_repeated_samples_do_not_double_apply_opacity(self):
        a=self.scene();b=self.scene()
        for s,data in [(a,[.5,.5]),(b,[.5,.5,.5,.5])]:
            s.command({'op':'material','id':2,'alpha':.2});self.widget(s,'line',data=data)
        self.assertEqual(a.render().bytes,b.render().bytes)
    def test_all_weather_and_fields_avoid_block_fallback_at_sampled_ages(self):
        s=self.scene()
        for entry in s.catalogue():
            if entry['contract'] not in ['ParticleEmitter','SurfaceField']:continue
            s.command({'op':'reset','seed':42});s.command({'op':'resize','width':80,'height':28})
            s.command({'op':'environment','stars':0,'sampling':'braille'})
            if entry['contract']=='ParticleEmitter':s.command({'op':'emitter','id':1,'effect':entry['id'],'count':16,'runningTimeMs':0})
            else:s.command({'op':'field','effect':entry['id'],'x':30,'y':14,'lifeMs':2000})
            for us in [50000,350000,900000]:
                s.advance_to(us)
                self.assertFalse(any(g in BLOCKS for g,_,_,ident in s.render().words()if ident==0),(entry['id'],us))
    def test_explicit_cell_mode_still_available(self):
        s=self.scene();self.widget(s,'pie',sampling='cell')
        self.assertTrue(any(w[0]==0x2588 for _,w in self.marks(s)))
    def test_widget_braille_override_survives_global_half_mode(self):
        s=self.scene();s.command({'op':'environment','sampling':'half'});self.widget(s,sampling='braille')
        self.assertTrue(self.marks(s));self.assertTrue(all(0x2800<w[0]<=0x28ff for _,w in self.marks(s)))
    def test_invalid_plot_parameters_reject_atomically(self):
        s=self.scene();self.widget(s)
        for patch in ({'sampling':'oops'},{'cellAspect':0},{'innerRadius':1},{'sweepAngle':361},{'revealMs':-1}):
            before=s.snapshot()
            with self.assertRaises(ValueError):s.command({'op':'widget','id':31,**patch})
            self.assertEqual(s.snapshot(),before)
    def test_material_alpha_zero_does_not_leave_plot_hits(self):
        s=self.scene();s.command({'op':'material','id':2,'alpha':0});self.widget(s)
        self.assertEqual(self.marks(s),[])
    def test_clipping_and_snapshot_replay_preserve_plot(self):
        s=self.scene();self.widget(s,x=-4,y=8,width=40,revealMs=900);s.advance_to(400000)
        saved=s.snapshot();a=s.render().bytes;s.advance_to(1500000);s.restore(saved)
        self.assertEqual(s.render().bytes,a);self.assertEqual(s.snapshot(),saved)
    def test_readable_local_ink_remains_immediate_over_braille(self):
        s=self.scene();s.command({'op':'pause','paused':True});s.command({'op':'input','text':'readable'})
        self.assertEqual(s.info()['prompt']['text'],'readable')
        self.assertEqual(s.info()['clock']['timeUs'],0)
        self.assertEqual([g for g,fg,_,ident in s.render().words()if ident==0x40000000 and g in map(ord,'readable')],list(map(ord,'readable')))
if __name__=='__main__':unittest.main()
