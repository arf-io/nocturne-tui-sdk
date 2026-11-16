"""Actual gallery clock requests: complete explicit advance, and bounded live frames in the running loop."""
import os,unittest
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
HTML=Path(os.environ.get('NOCTURNE_GALLERY_ADVANCE_HTML',ROOT/'Nocturne-Test-Harness.html'))
LIVE_FRAME_BUDGET=24   # native/web/template.html: the fixed live frame budget for recipes without frameBudget
LOOP=r'''async([id,stallMs,after])=>{const recipe=nativeLab.recipes.find(r=>r.id===id),s=nativeLab.scene;if(!recipe)throw Error('missing '+id);
 nativeLab.load(recipe);const frame=()=>new Promise(resolve=>requestAnimationFrame(()=>resolve()));
 for(let i=0;i<600&&s.info().clock.timeUs<=300000;i++)await frame();
 const steps=[];let view=window.nativeView;Object.defineProperty(window,'nativeView',{configurable:true,get(){return view;},set(value){view=value;steps.push(s.info().clock.step);}});
 try{for(let i=0;i<10;i++)await frame();const stalled=steps.length,end=performance.now()+stallMs;while(performance.now()<end){}
  for(let i=0;i<after;i++)await frame();const deltas=steps.slice(1).map((v,i)=>v-steps[i]);
  return {budget:nativeLab.pacing().budget,frameBudget:recipe.frameBudget??null,steps,deltas,before:deltas.slice(0,stalled-1),afterStall:deltas.slice(stalled-1)};}
 finally{delete window.nativeView;window.nativeView=view;}}'''
class GalleryAdvance(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.pw=sync_playwright().start();cls.browser=cls.pw.chromium.launch(headless=True,executable_path=os.environ.get('CHROMIUM'))
 @classmethod
 def tearDownClass(cls):cls.browser.close();cls.pw.stop()
 def setUp(self):
  self.page=self.browser.new_page();self.errors=[];self.page.on('pageerror',lambda e:self.errors.append(str(e)));self.page.set_content(HTML.read_text());self.page.wait_for_function('window.nativeLab');self.page.evaluate("()=>{const r=nativeLab.recipes.find(r=>r.id==='observatory-rain-isolated');if(!r)throw Error('Original Observatory recipe missing');window.advanceRecipe=r;window.loadAdvanceBaseline=()=>{nativeLab.load(r);nativeLab.hold();nativeLab.scene.command({op:'reset',seed:2030});for(const c of r.commands)nativeLab.scene.command(c);};loadAdvanceBaseline();}")
 def tearDown(self):self.page.close()
 def test_explicit_advance_drains_more_than_one_native_budget(self):
  actual=self.page.evaluate("()=>{nativeLab.advance(6500000);const s=nativeLab.scene,clock=s.info().clock,actual=s.snapshot(),frame=s.render().bytes;loadAdvanceBaseline();s.advanceTo(6500000);s.command({op:'pause',paused:true});const direct=s.snapshot(),directFrame=s.render().bytes;const equal=(a,b)=>a.length===b.length&&a.every((v,i)=>v===b[i]);return {clock,snapshotEqual:equal(actual,direct),frameEqual:equal(frame,directFrame)};}")
  self.assertEqual(actual['clock']['timeUs'],6500000);self.assertEqual(actual['clock']['targetUs'],6500000);self.assertTrue(actual['clock']['paused']);self.assertTrue(actual['snapshotEqual']);self.assertTrue(actual['frameEqual']);self.assertFalse(self.errors)
 def test_live_frame_budget_still_returns_partial_and_retains_target(self):
  # budgetedTime() is the one bounded native call every painted frame makes (liveAdvance), at the
  # live budget: the recipe's frameBudget, else the fixed 24 steps.
  actual=self.page.evaluate("()=>{const code=nativeLab.budgetedTime(6500000);return {code,clock:nativeLab.scene.info().clock,budget:nativeLab.pacing().budget};}")
  self.assertEqual(actual['code'],1);self.assertGreater(actual['clock']['timeUs'],0);self.assertLess(actual['clock']['timeUs'],6500000);self.assertEqual(actual['budget'],LIVE_FRAME_BUDGET);self.assertEqual(actual['clock']['step'],LIVE_FRAME_BUDGET);self.assertEqual(actual['clock']['targetUs'],6500000);self.assertFalse(self.errors)
 def test_running_loop_advances_each_painted_frame_by_at_most_its_budget(self):
  # The production loop itself, not a helper: every painted frame advances at most nativeLab.pacing().budget
  # steps, the frame that absorbs a 1 s stall advances exactly one budget, and the scene keeps running.
  actual=self.page.evaluate(LOOP,['observatory-rain-isolated',1000,20])
  self.assertEqual(actual['budget'],LIVE_FRAME_BUDGET);self.assertGreater(sum(actual['before']),0)
  self.assertLessEqual(max(actual['deltas']),actual['budget'],actual['deltas']);self.assertEqual(max(actual['afterStall']),actual['budget'],actual['afterStall'])
  self.assertGreater(sum(actual['afterStall'][actual['afterStall'].index(actual['budget'])+1:]),0,actual['afterStall']);self.assertFalse(self.errors)
if __name__=='__main__':unittest.main()
