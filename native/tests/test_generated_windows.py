"""Actual RC2 whole-window compositor versus retained public C/WASM windows."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import json
import os
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
from native.tests.historical_reference import load_rc2_workbench

WAVE=[((i%17)-8)/10 for i in range(128)]
BASE=[{'op':'resize','width':120,'height':64},
      {'op':'environment','presentation':'canvas','style':'solid','background':0x112233,'stars':0},
      {'op':'prompt','active':False},{'op':'floor','enabled':False,'visible':False},
      {'op':'camera','position':[0,0,60],'yaw':0,'pitch':0,'roll':0,'fov':70,'near':.1,'far':1000}]
WINDOW={'op':'window','id':1,'title':'Original window','text':'Shared document.\nSecond line.',
        'position':[0,0,0],'width':48,'height':30,'alpha':1,'durationMs':0,
        'effect':'window-transition/glass-dissolve','sourceGeometry':True}
CONTENT={'op':'window-content','id':1,'label':'source.1','sourceIndex':0,'waveform':WAVE}

class GeneratedWindows(unittest.TestCase):
    def scene(self,attach=True):
        s=NativeScene(2030);self.addCleanup(s.close)
        for cmd in BASE:s.command(cmd)
        if attach:s.command(WINDOW);s.command(CONTENT)
        return s

    def row(self,s):return s.info_complete()['windows'][0]

    def test_full_document_reader_replay_removal_and_raw_texture_collision(self):
        s=self.scene();base=s.snapshot();text='x'*4095+'Z'
        s.command({'op':'window-content','id':1,'text':text})
        self.assertEqual(self.row(s)['content']['text'],text)
        self.assertEqual(self.row(s)['text'],text)
        self.assertEqual(s.text_run_source(2,1),text)
        saved=s.snapshot();frame=s.render().bytes;self.assertEqual(s.snapshot(),saved)
        s.command({'op':'window-action','id':1,'action':'read'})
        s.command({'op':'window-action','id':1,'action':'scroll','rows':2048})
        self.assertIn(ord('Z'),[cell[0] for cell in s.render().words()])
        before=s.snapshot()
        with self.assertRaises(ValueError):s.command({'op':'window-texture','id':1,'width':1,'height':1})
        self.assertEqual(s.snapshot(),before)
        s.restore(saved);self.assertEqual(s.render().bytes,frame)
        s.command({'op':'remove-window-content','id':1})
        self.assertIsNone(self.row(s)['content'])
        self.assertEqual(self.row(s)['text'],WINDOW['text'])
        s.command({'op':'window-texture','id':1,'width':1,'height':1})
        before=s.snapshot()
        with self.assertRaises(ValueError):s.command(CONTENT)
        self.assertEqual(s.snapshot(),before)
        s.restore(base);self.assertEqual(self.row(s)['content']['label'],'source.1')

    def test_invalid_generated_options_are_atomic_and_source_domain_is_retained(self):
        s=self.scene()
        invalid=[{'label':''},{'label':'has space'},{'label':'x'*65},{'sourceIndex':-1},
                 {'sourceIndex':.5},{'colors':[]},{'colors':[0x1000000]},
                 {'stopWidths':[0]},{'stopWidths':[1]*33},{'lockLightness':1},
                 {'waveform':[0]*127},{'waveform':[True]*128},{'text':'x'*4097},
                 {'text':'😀'*2049},{'brightness':1.01},{'unknown':True}]
        for patch in invalid:
            with self.subTest(patch=list(patch)):
                before=s.snapshot()
                with self.assertRaises(ValueError):s.command({'op':'window-content','id':1,**patch})
                self.assertEqual(s.snapshot(),before)
        s.command({'op':'window-content','id':1,'text':'😀'*2048,'colors':[0x345678],
                   'stopWidths':[.05,16],'brightness':0,'lockLightness':False})
        self.assertEqual(self.row(s)['content']['text'],'😀'*2048)
        before=s.snapshot()
        with self.assertRaises(ValueError):s.command({'op':'window','id':1,'shape':'cloud'})
        self.assertEqual(s.snapshot(),before)
        s.command({'op':'reset'});s.command(WINDOW);self.assertIsNone(self.row(s)['content'])

    def test_attachment_preserves_an_active_opening_transition(self):
        s=self.scene(False);s.command({**WINDOW,'durationMs':600})
        s.advance_to(150000);before=self.row(s)['visible'];s.command(CONTENT)
        self.assertAlmostEqual(self.row(s)['content']['visibility'],before,places=6)
        s.advance_to(600000)
        self.assertEqual(self.row(s)['content']['visibility'],1)
        self.assertTrue(any(c[3]==0x20000001 for c in s.render().words()))

    def test_reader_gather_and_summon_restore_generated_visibility(self):
        s=self.scene()
        for restore in ({'op':'window-action','id':1,'action':'read'},
                        {'op':'gather'},
                        {'op':'window-action','id':1,'action':'summon'}):
            s.command({'op':'window-action','id':1,'action':'minimize','durationMs':0})
            self.assertEqual(self.row(s)['content']['visibility'],0)
            s.command(restore)
            self.assertEqual(self.row(s)['content']['visibility'],1)
            self.assertEqual(self.row(s)['content']['text'],WINDOW['text'])

    def test_generated_windows_preserve_all_scenic_command_identities(self):
        s=self.scene()
        for scene in ('pearl-cascade','tidal-glass','copper-causeway','red-shift','silt'):
            s.command({'op':'scene-art','scene':scene})
            self.assertEqual(s.info_complete()['sceneArt']['scene'],scene)
            self.assertEqual(self.row(s)['content']['label'],'source.1')
        before=s.snapshot()
        with self.assertRaises(ValueError):s.command({'op':'scene-art','scene':'missing'})
        self.assertEqual(s.snapshot(),before)
        s.command({'op':'remove-scene-art'});self.assertIsNone(s.info_complete()['sceneArt'])

    def test_schema67_promotion_and_pending_source_command_rejection(self):
        s=self.scene(False);s.command(WINDOW)
        def old67():
            from native.tests.constructed_legacy_snapshot import construct_legacy_snapshot
            return construct_legacy_snapshot(s.snapshot(),0x20261067,14121280)
        old=old67();s.command(CONTENT);s.restore(old);self.assertIsNone(self.row(s)['content'])
        s.command({'op':'schedule','id':1,'atUs':1000000,'command':{'op':'batch','commands':[CONTENT]}})
        before=s.snapshot()
        with self.assertRaises(ValueError):s.restore(old67())
        self.assertEqual(s.snapshot(),before)

    def test_actual_original_complete_window_cells_across_shapes_camera_and_transitions(self):
        from playwright.sync_api import sync_playwright
        source=load_rc2_workbench();anchor='return {KineticRenderer,hitKinetic,activateKinetic};'
        self.assertEqual(source.count(anchor),1)
        source=source.replace(anchor,'window.__generatedWindow={KineticRenderer,WindowManager,CameraRig,KineticModel,ObservatoryRenderer,DEFAULT_OBSERVATORY_OPTIONS};'+anchor,1)
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
            page=browser.new_page();page.set_content(source,wait_until='domcontentloaded')
            page.wait_for_function('window.fieldGuide && window.__generatedWindow')
            cases=[{}, {'shape':'ellipse'}, {'shape':'diamond'},
                   {'yaw':25,'pitch':17,'roll':13,'camera':[3,2,60,8,-5,7]},
                   {'alpha':.63,'time':1234},
                   {'action':'maximize','time':425,'durationMs':850},
                   {'action':'minimize','time':425,'durationMs':850},
                   {'action':'roll-up','time':850,'durationMs':850}]
            for case_index,case in enumerate(cases):
                with self.subTest(case=case):
                    s=self.scene(False)
                    camera=case.get('camera',[0,0,60,0,0,0])
                    s.command({'op':'camera','position':camera[:3],'yaw':camera[3],'pitch':camera[4],'roll':camera[5]})
                    window={**WINDOW,**{k:v for k,v in case.items() if k in ('shape','yaw','pitch','roll','alpha')}}
                    s.command(window)
                    # The oracle is the original windows() compositor, which accepts
                    # a caller-owned background. Keep the SDK's separately tested
                    # dock in that shared background; compare every resulting cell.
                    s.command({'op':'window-action','id':1,'action':'minimize','durationMs':0})
                    baseline=[v for cell in s.render().words() for v in cell]
                    s.command({'op':'window-action','id':1,'action':'restore','durationMs':0})
                    s.command(CONTENT)
                    if 'action' in case:s.command({'op':'window-action','id':1,'action':case['action'],'durationMs':case['durationMs']})
                    s.advance_to(case.get('time',0)*1000)
                    clock=s.info_complete()['clock']['timeUs']/1000
                    actual=[v for cell in s.render().words() for v in cell]
                    expected=page.evaluate('''input=>{
                      const a=window.__generatedWindow,e=window.fieldGuide.engine;
                      const manager=new a.WindowManager();
                      manager.configure({effect:'fade',durationMs:input.case.durationMs??0,opacity:input.window.alpha,depthFade:0});
                      manager.add({id:'source.1',title:input.window.title,content:input.window.text,
                        x:0,y:0,z:0,width:48,height:30,shape:input.case.shape??'rectangle',
                        yaw:input.case.yaw??0,pitch:input.case.pitch??0,roll:input.case.roll??0});
                      if(input.case.action)manager.act('source.1',input.case.action==='roll-up'?'roll':input.case.action,0);
                      const camera={x:input.camera[0],y:input.camera[1],z:-input.camera[2],yaw:input.camera[3],pitch:input.camera[4],roll:input.camera[5],fov:70,near:.1,far:1000};
                      const palette={colors:['#647795','#af88bb','#69a9a5','#b89477','#73709f'],background:'#101319',ink:'#dfd8cc'};
                      const renderer=new a.KineticRenderer(e);renderer.base.prepare(palette,a.DEFAULT_OBSERVATORY_OPTIONS);
                      const frame={width:120,height:64,cells:Uint32Array.from(input.baseline)};
                      const model=new a.KineticModel();model.spaceWindows=manager;model.camera=new a.CameraRig(camera);model.motionMs=input.time;model.palette=palette;model.waveform=input.wave;
                      renderer.windows(frame,model,{});
                      for(let i=3;i<frame.cells.length;i+=4)if(frame.cells[i]===15000)frame.cells[i]=0x20000001;
                      return Array.from(frame.cells);
                    }''',{'case':case,'window':window,'camera':camera,'baseline':baseline,'time':clock,'wave':WAVE})
                    if capture_dir:=os.environ.get('NOCTURNE_WINDOW_CAPTURE_DIR'):
                        destination=Path(capture_dir);destination.mkdir(parents=True,exist_ok=True)
                        (destination/f'case-{case_index:02}.json').write_text(json.dumps({
                            'case':case,'clockMs':clock,'width':120,'height':64,
                            'original':expected,'current':actual},separators=(',',':')))
                    differences=[(i//4%120,i//4//120,i%4,a,b) for i,(a,b) in enumerate(zip(actual,expected)) if a!=b]
                    self.assertEqual(len(actual),len(expected))
                    self.assertEqual(len(differences),0,f'{len(differences)} differing words (x,y,channel,current,original): {differences[:12]}')

            browser.close()

    def test_current_wasm_frames_metadata_and_reversible_maximize_match_native(self):
        commands=BASE+[WINDOW,CONTENT]
        actions=[{'command':{'op':'window-action','id':1,'action':'maximize','durationMs':850},'time':425000},
                 {'command':{'op':'window-action','id':1,'action':'maximize'},'time':850000},
                 {'command':{'op':'window-content','id':1,'colors':[0x204060,0xccaabb],'stopWidths':[.2,3],'text':'Changed document'},'time':1000000},
                 {'command':{'op':'window-action','id':1,'action':'restore'},'time':2000000}]
        s=self.scene();frames=[]
        for item in actions:
            s.command(item['command']);s.advance_to(item['time']);before=s.snapshot()
            frames.append({'words':[v for cell in s.render().words() for v in cell],'content':self.row(s)['content']})
            self.assertEqual(s.snapshot(),before)
        with tempfile.TemporaryDirectory() as tmp:
            request,response=Path(tmp)/'request.json',Path(tmp)/'response.json'
            request.write_text(json.dumps({'commands':commands,'actions':actions}))
            subprocess.run(['node',str(ROOT/'tests/generated_windows_wasm_runner.mjs'),str(request),str(response)],check=True,timeout=90)
            wasm=json.loads(response.read_text());self.assertEqual(len(wasm),len(frames))
            for actual,expected in zip(wasm,frames):
                self.assertEqual(actual['content'],expected['content'])
                differences=[(i,a,b) for i,(a,b) in enumerate(zip(actual['words'],expected['words'])) if a!=b]
                self.assertEqual(len(actual['words']),len(expected['words']))
                self.assertEqual(len(differences),0,f'{len(differences)} WASM/native word differences: {differences[:12]}')
