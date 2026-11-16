import os,sys,unittest
from pathlib import Path
import xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'hosts/python'))
sys.path.insert(0,str(ROOT/'bindings/python'))
from font_shaper import HarfBuzzFont
from font_document_view import FontDocumentView
from nocturne_native import NativeScene
NS='{http://www.w3.org/2000/svg}'

class FontDocumentViewTests(unittest.TestCase):
    def setUp(self):
        self.font=HarfBuzzFont(Path(os.environ['NOCTURNE_SHAPING_FONT']).read_bytes(),
                               os.environ['NOCTURNE_HARFBUZZ_LIBRARY'])
        self.addCleanup(self.font.close)
        self.scene=NativeScene();self.addCleanup(self.scene.close)
        self.view=FontDocumentView([self.font],language={'Latn':'en','Arab':'ar','*':'und'})

    def present(self,text='office سلام é',**geometry):
        self.scene.command({'op':'draft','text':text,'emitWeather':False})
        return self.view.present(self.scene,host_epoch=7,width=520,height=240,**geometry)

    def test_positive_contextual_runs_match_real_engine_and_preserve_source(self):
        p=self.present();before=self.scene.snapshot()
        arabic=next(s for s in p.layout.segments if 'سلام' in s.run.source)
        reference=self.font.shape(arabic.run.source,direction='rtl',script='Arab',language='ar')
        self.assertEqual(arabic.run.glyphs,reference.glyphs)
        latin=next(s for s in p.layout.segments if 'office' in s.run.source)
        plain=self.font.shape(latin.run.source,direction='ltr',script='Latn',language='en',features=['liga=0'])
        self.assertLess(len(latin.run.glyphs),len(plain.glyphs))
        paths=E.fromstring(p.svg).findall('.//'+NS+'path')
        self.assertTrue(paths);self.assertTrue(all(path.attrib['d'] for path in paths))
        self.assertTrue(all(s.identities for s in p.layout.segments))
        self.assertEqual(self.scene.text_run_source(0,0),'office سلام é')
        self.assertEqual(self.scene.snapshot(),before)

    def test_positive_present_is_snapshot_pure_and_result_is_immutable(self):
        self.scene.command({'op':'draft','text':'office سلام','emitWeather':False})
        before=self.scene.snapshot();p=self.view.present(self.scene,host_epoch=7)
        self.assertEqual(self.scene.snapshot(),before)
        with self.assertRaises((AttributeError,TypeError)):p.svg='changed'
        again=self.view.present(self.scene,host_epoch=7)
        self.assertEqual(p.svg,again.svg);self.assertEqual(p.edges,again.edges)

    def test_positive_pointer_and_shift_selection_use_real_source_edges(self):
        p=self.present('abc xyz');edge=next(e for e in p.edges if e.offset==1)
        self.assertTrue(self.view.select_at(self.scene,p,edge.x,edge.baseline,host_epoch=7))
        self.assertEqual(self.scene.info()['prompt']['caret'],1)
        end=next(e for e in p.edges if e.offset==len(p.capture.source))
        self.assertTrue(self.view.select_at(self.scene,p,end.x,end.baseline,host_epoch=7,extend=True))
        self.assertEqual(self.scene.selected_text(),'bc xyz')
        selected=self.view.present(self.scene,host_epoch=7,width=520,height=240)
        self.assertTrue(E.fromstring(selected.svg).findall(NS+'g/'+NS+'rect'))

    def test_positive_vertical_and_line_edges_use_font_coordinates(self):
        p=self.present('abc\nxyz')
        self.scene.command({'op':'select','anchor':0,'caret':0})
        self.assertTrue(self.view.move(self.scene,p,'ArrowDown',host_epoch=7))
        self.assertEqual(self.scene.info()['prompt']['caret'],4)
        self.assertTrue(self.view.move(self.scene,p,'End',host_epoch=7))
        self.assertEqual(self.scene.info()['prompt']['caret'],7)
        self.assertTrue(self.view.move(self.scene,p,'Home',host_epoch=7))
        self.assertEqual(self.scene.info()['prompt']['caret'],4)

    def test_positive_unicode_pixel_wrapping_and_ligature_edges(self):
        p=self.present('office office office',font_size=80)
        self.assertGreater(len(p.layout.line_ends),1)
        for edge in p.edges:self.assertIn(edge.offset,self.scene.grapheme_boundaries(p.capture.source))
        ligature=next(g for s in p.layout.segments for g in s.run.glyphs if g.end-g.start>1)
        self.assertGreater(ligature.end-ligature.start,1)

    def test_positive_empty_document_boundary_without_fake_glyph(self):
        p=self.present('');self.assertEqual(p.layout.segments,())
        self.assertFalse(E.fromstring(p.svg).findall('.//'+NS+'path'))
        self.assertTrue(self.view.select_at(self.scene,p,8,48,host_epoch=7))
        self.assertEqual(self.scene.info()['prompt']['caret'],0)

    def test_negative_stale_source_epoch_scene_and_view_do_not_mutate(self):
        p=self.present('abc')
        self.scene.command({'op':'draft','text':'xyz','emitWeather':False})
        before=self.scene.snapshot()
        for epoch in [7,8]:
            self.assertFalse(self.view.select_at(self.scene,p,8,48,host_epoch=epoch))
            self.assertEqual(self.scene.snapshot(),before)
        with NativeScene() as other:
            self.assertFalse(self.view.select_at(other,p,8,48,host_epoch=7))
        otherView=FontDocumentView([self.font],language='und')
        self.assertFalse(otherView.select_at(self.scene,p,8,48,host_epoch=7))

    def test_negative_pointer_outside_viewport_rejected_atomically(self):
        p=self.present();before=self.scene.snapshot()
        for x,y in [(-1,48),(520,48),(8,-1),(8,240)]:
            self.assertFalse(self.view.select_at(self.scene,p,x,y,host_epoch=7))
        self.assertEqual(self.scene.snapshot(),before)

    def test_negative_epoch_alone_invalidates_identical_source_after_reset(self):
        p=self.present('abc')
        before=self.scene.snapshot()
        self.assertFalse(self.view.select_at(self.scene,p,8,48,host_epoch=8))
        self.assertEqual(self.scene.snapshot(),before)
        self.scene.command({'op':'reset'})
        self.scene.command({'op':'draft','text':'abc','emitWeather':False})
        before=self.scene.snapshot()
        self.assertFalse(self.view.select_at(self.scene,p,8,48,host_epoch=8))
        self.assertFalse(self.view.move(self.scene,p,'End',host_epoch=8))
        self.assertEqual(self.scene.snapshot(),before)

    def test_positive_rtl_pointer_span_edges_use_actual_font_advances(self):
        p=self.present('سلام')
        edge=next(e for e in p.edges if e.offset==len(p.capture.source))
        self.assertEqual(edge.level%2,1)
        self.assertTrue(self.view.select_at(self.scene,p,edge.x,edge.baseline,host_epoch=7))
        self.assertEqual(self.scene.info()['prompt']['caret'],len(p.capture.source))

    def test_negative_nonprompt_run_presents_but_never_dispatches_prompt_selection(self):
        self.scene.command({'op':'window','id':1,'title':'office سلام','text':'abc'})
        p=self.view.present(self.scene,kind=3,id=1,host_epoch=7)
        before=self.scene.snapshot()
        self.assertTrue(p.layout.segments)
        self.assertFalse(self.view.select_at(self.scene,p,8,48,host_epoch=7))
        self.assertEqual(self.scene.snapshot(),before)

    def test_negative_invalid_geometry_rejects_without_native_change(self):
        before=self.scene.snapshot()
        for patch in [{'width':0},{'height':float('nan')},{'font_size':True},
                      {'alpha':2},{'alignment':'invalid'},{'host_epoch':-1}]:
            with self.subTest(patch=patch),self.assertRaises((ValueError,TypeError)):
                self.view.present(self.scene,**({'host_epoch':7}|patch))
        self.assertEqual(self.scene.snapshot(),before)

    def test_negative_ligature_interior_move_does_not_invent_pixel_caret(self):
        p=self.present('office\nnext')
        self.scene.command({'op':'select','anchor':2,'caret':2})
        before=self.scene.snapshot()
        self.assertFalse(self.view.move(self.scene,p,'ArrowDown',host_epoch=7))
        self.assertEqual(self.scene.snapshot(),before)
