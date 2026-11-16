"""Operator regressions: filled braille leaves and subcell floor grid geometry."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
from pathlib import Path
import sys,unittest,hashlib,json,gzip
from native.tests.presentation_copy_reference import assert_current_chrome
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene

class BrailleFloorRegressions(unittest.TestCase):
 def scene(self):
  s=NativeScene(42);self.addCleanup(s.close)
  s.command(dict(op='resize',width=96,height=40))
  s.command(dict(op='environment',stars=0,style='solid',background=0x101010))
  return s
 def leaf(self,s,sampling):
  s.command(dict(op='camera',position=[0,6,30],yaw=0,pitch=0,orthographic=True,span=32))
  s.advance_to(500000);before=s.render().words()
  s.command(dict(op='emitter',id=1,effect='weather/autumn-drift',count=1,runningTimeMs=0,position=[0,6,0],extent=[0,0,0],velocity=[0,0,0],spread=[0,0,0],gravity=[0,0,0],wind=[0,0,0],windVariation=[0,0,0],drag=0,lift=0,tumble=[0,0,0],flutterHz=0,flutterAmount=0,sizeMin=6,sizeMax=6,deposit=False,collision=False,lifetimeMinMs=10000,lifetimeMaxMs=10000,birthFadeMs=0,veinContrast=0,surfaceAlpha=1,sampling=sampling))
  s.advance_to(1000000);after=s.render().words()
  return [(a,b)for i,(a,b)in enumerate(zip(before,after))if 2<=i//96<34 and a!=b]
 def test_filled_braille_leaf_retains_full_eight_dot_interiors(self):
  changed=self.leaf(self.scene(),'braille')
  self.assertGreater(len(changed),80)
  self.assertTrue(any(b[0]==0x28ff for a,b in changed),'Filled leaf interior must contain full eight-dot braille')
  self.assertFalse(any(b[0]==32 for a,b in changed),'A braille blade must not turn its filled interior into a flat background cell')
  self.assertTrue(all(0x2800<b[0]<=0x28ff for a,b in changed))
 def test_braille_leaf_gaps_retain_underlay_instead_of_its_own_blade_fill(self):
  changed=self.leaf(self.scene(),'braille')
  self.assertTrue(any(b[0]==0x28ff for a,b in changed))
  self.assertEqual([(i,hex(a[2]),hex(b[2])) for i,(a,b) in enumerate(changed) if a[2]!=b[2]],[],
                   'Braille gaps must show the underlying scene, including cells with blade plus outline/vein fragments')
 def test_floor_grid_behind_leaf_cannot_replace_its_eight_dot_interiors(self):
  s=self.scene();self.leaf(s,'braille')
  s.command(dict(op='camera',position=[0,18,35],pitch=-25,yaw=0))
  s.command(dict(op='floor',visible=False));without=s.render().words()
  s.command(dict(op='floor',visible=True,alpha=.4,sampling='braille'));saved=s.snapshot();particles=s.particles();with_floor=s.render().words()
  interior=[i for i,w in enumerate(without) if 2<=i//96<34 and w[0]==0x28ff]
  self.assertGreater(len(interior),10)
  self.assertEqual([(i,hex(with_floor[i][0])) for i in interior if with_floor[i][0]!=0x28ff],[],
                   'A farther floor grid cannot steal the foreground leaf coverage mask')
  self.assertTrue(all(max(abs((with_floor[i][1]>>k&255)-(with_floor[i][2]>>k&255)) for k in (0,8,16))>20 for i in interior),
                  'Eight-dot geometry must retain visible gaps, not nearly identical foreground/background fills')
  self.assertEqual(s.snapshot(),saved);self.assertEqual(s.particles(),particles)
 def test_settled_leaf_keeps_its_silhouette_over_the_floor_grid(self):
  s=self.scene();s.command(dict(op='camera',position=[0,18,35],pitch=-25,yaw=0,orthographic=True,span=32))
  s.command(dict(op='floor',enabled=True,visible=False,sampling='braille'));s.advance_to(500000)
  s.command(dict(op='emitter',id=2,effect='weather/autumn-drift',count=1,runningTimeMs=0,position=[0,1,0],extent=[0,0,0],velocity=[0,-10,0],spread=[0,0,0],gravity=[0,-20,0],wind=[0,0,0],windVariation=[0,0,0],drag=0,lift=0,tumble=[0,0,0],flutterHz=0,flutterAmount=0,sizeMin=6,sizeMax=6,deposit=True,collision=True,lifetimeMinMs=10000,lifetimeMaxMs=10000,birthFadeMs=0,veinContrast=1,surfaceAlpha=1,sampling='braille'))
  s.advance_to(1500000);deposits=s.info_complete()['deposits'];self.assertEqual(len(deposits),1)
  self.assertEqual(deposits[0]['normal'],[0,1,0]);self.assertAlmostEqual(deposits[0]['position'][1],.02)
  without=s.render().words();s.command(dict(op='floor',visible=True,alpha=.4));saved=s.snapshot();with_floor=s.render().words()
  marked=[i for i,w in enumerate(without) if 2<=i//96<34 and 0x2800<w[0]<=0x28ff]
  self.assertGreater(len(marked),80)
  self.assertEqual([(i,hex(without[i][0]),hex(with_floor[i][0])) for i in marked if without[i][0]!=with_floor[i][0]],[],
                   'Settled outline, stem and vein masks must not become floor-grid masks')
  self.assertEqual(s.info_complete()['deposits'],deposits);self.assertEqual(s.snapshot(),saved)
 def test_actual_canvas_keeps_leaf_dot_gaps_at_cell_boundaries(self):
  from playwright.sync_api import sync_playwright
  changed=self.leaf(self.scene(),'braille')
  module=(ROOT/'bindings/typescript/canvas_braille.mjs').read_text()
  with sync_playwright() as pw:
   browser=pw.chromium.launch(headless=True)
   try:
    page=browser.new_page();page.set_content('<canvas id="c"></canvas>')
    page.add_script_tag(type='module',content=module+'\nwindow.paintBraille=paintBraille;')
    page.wait_for_function('typeof window.paintBraille === "function"')
    pixels=page.evaluate('''rows=>{const c=document.querySelector('canvas');c.width=rows.length*20;c.height=40;const ctx=c.getContext('2d');const rgb=n=>'#'+n.toString(16).padStart(6,'0');for(let i=0;i<rows.length;i++){const w=rows[i][1];ctx.fillStyle=rgb(w[2]);ctx.fillRect(i*20,0,20,40);ctx.fillStyle=rgb(w[1]);window.paintBraille(ctx,w[0],i*20,0,20,40);}const gaps=rows.map((r,i)=>Array.from(ctx.getImageData(i*20+10,20,1,1).data));
const fullDots=rows.flatMap((r,i)=>{if(r[1][0]!==0x28ff)return[];const data=ctx.getImageData(i*20,0,20,40).data,fg=r[1][1],seen=new Uint8Array(800);let groups=0,ink=0;const isInk=n=>(data[n*4]<<16|data[n*4+1]<<8|data[n*4+2])===fg;for(let n=0;n<800;n++){if(!isInk(n))continue;ink++;if(seen[n])continue;groups++;const todo=[n];seen[n]=1;while(todo.length){const v=todo.pop();for(const q of [v%20?v-1:-1,v%20<19?v+1:-1,v-20,v+20])if(q>=0&&q<800&&!seen[q]&&isInk(q)){seen[q]=1;todo.push(q);}}}return[{groups,ink}];});return{gaps,fullDots};}''',changed)
    self.assertEqual(pixels['gaps'],[[(a[2]>>16)&255,(a[2]>>8)&255,a[2]&255,255] for a,b in changed],
                     'The real canvas painter must expose the unpainted underlay between braille dots')
    self.assertTrue(pixels['fullDots']);self.assertTrue(all(v==dict(groups=8,ink=128) for v in pixels['fullDots']),
                     'Each actual U+28FF cell must paint eight separated dot islands, never a filled rectangle')
   finally:browser.close()
 def test_explicit_cell_and_half_leaf_policies_remain_available(self):
  cell=self.leaf(self.scene(),'cell');half=self.leaf(self.scene(),'half')
  self.assertTrue(any(b[0]==32 for a,b in cell))
  self.assertTrue(any(b[0]==0x2580 for a,b in half))
 def case_frame(self,kind,sampling):
  s=self.scene()
  if kind=='leaf':self.leaf(s,sampling)
  else:
   s.command(dict(op='camera',position=[0,18,35],yaw=0,pitch=-25))
   s.command(dict(op='floor',visible=True,alpha=.4,sampling=sampling))
  return s.render()
 def test_original_nonbraille_leaf_and_floor_frames_are_unchanged(self):
  fixture=json.loads((ROOT/'tests/fixtures/braille-nonbraille-preservation.json').read_text())
  originals=gzip.decompress((ROOT/'tests/fixtures/braille-nonbraille-preservation.frames.gz').read_bytes())
  self.assertEqual(len(originals),61440*len(fixture['cases']))
  retained={(case['kind'],case['sampling']):originals[index*61440:(index+1)*61440] for index,case in enumerate(fixture['cases'])}
  for case in fixture['cases']:
   with self.subTest(kind=case['kind'],sampling=case['sampling']):
    original=retained[(case['kind'],case['sampling'])]
    self.assertEqual(hashlib.sha256(original).hexdigest(),case['sha256'])
    frame=self.case_frame(case['kind'],case['sampling'])
    if case['sampling']!='hybrid':
     assert_current_chrome(self,frame.bytes,original,frame.width,frame.height,'stage');continue
    # Operator directive 2026-11-01 (MIXED-LAYERS.md, Hybrid dictation): a hybrid object is encoded as
    # its dictated class and never mixed between braille and blocks. The retained hybrid frame (contrast
    # masks on the leaf outline, a floor of braille and half blocks) is superseded; its hash stays
    # verified above. The floor is now exactly the retained half frame; the leaf is the braille leaf.
    words=lambda data:[data[i:i+16] for i in range(0,len(data),16)]
    changed=[i for i,(a,b) in enumerate(zip(words(frame.bytes),words(original))) if a!=b and i//frame.width>=2]
    self.assertTrue(changed,'the superseded hybrid frame still renders')
    if case['kind']=='floor':
     assert_current_chrome(self,frame.bytes,retained[('floor','half')],frame.width,frame.height,'stage')
    else:self.assertEqual(frame.bytes,self.case_frame('leaf','braille').bytes)
 def test_braille_floor_retains_subcell_grid_lines_inside_filled_plane(self):
  s=self.scene();s.command(dict(op='camera',position=[0,18,35],yaw=0,pitch=-25))
  s.command(dict(op='floor',visible=True,alpha=.4,sampling='braille'))
  before=s.info_complete();particles=s.particles();f=s.render();words=f.words()
  interior=[words[y*96+x][0]for y in range(18,29)for x in range(20,76)]
  partial=[g for g in interior if 0x2800<g<0x28ff]
  self.assertGreater(len(partial),20,'The filled floor must not consume every grid-line dot mask')
  self.assertTrue(all(0x2800<g<=0x28ff for g in interior))
  s.command(dict(op='floor',sampling='half'));half=s.render().words()
  self.assertTrue(all(half[y*96+x][0]==0x2580 for y in range(18,29)for x in range(20,76)))
  self.assertEqual(s.info_complete()['camera'],before['camera'])
  self.assertEqual(s.particles(),particles)
  self.assertEqual(s.info_complete()['clock'],before['clock'])
if __name__=='__main__':unittest.main()
