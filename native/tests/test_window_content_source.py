"""RC2 generated window texture content parity against the pinned live runtime."""
from __future__ import annotations

import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import ctypes
import base64
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import tempfile
import unittest

from native.tests.historical_reference import load_rc2_workbench, RC2_HTML_SHA256, RC2_WASM_SHA256

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'src'
TESTS=ROOT/'tests'


class WindowContentSource(unittest.TestCase):
    original_cases_cache=None

    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='nr-window-content-source-')
        tmp=Path(cls.temp.name)
        cls.original=load_rc2_workbench()
        cls.assertHtmlHash=hashlib.sha256(cls.original.encode()).hexdigest()
        data_match=re.search(r'const DATA=(\{.*?\});\s*(?:const|function)',cls.original,re.S)
        if not data_match: raise AssertionError('pinned original DATA record missing')
        original_wasm=base64.b64decode(json.loads(data_match.group(1))['wasm'])
        if hashlib.sha256(original_wasm).hexdigest()!=RC2_WASM_SHA256:
            raise AssertionError('pinned original Stage WASM hash mismatch')
        cls.html=tmp/'original.html'
        cls.html.write_text(cls.original,encoding='utf-8')
        cls.native=tmp/('window_content.dylib' if platform.system()=='Darwin' else 'window_content.so')
        command=[os.environ.get('CC','cc'),'-std=c11','-O0','-fPIC','-ffunction-sections','-fdata-sections',
          '-I',str(SRC),'-I',str(ROOT/'include'),
          str(SRC/'window_content_source.c'),str(SRC/'window_texture_source.c'),
          str(SRC/'source_stage_components.c'),str(SRC/'source_material_sampler.c'),
          str(TESTS/'window_content_source_probe.c')]
        if platform.system()=='Darwin': command += ['-dynamiclib','-Wl,-dead_strip']
        else: command += ['-shared','-Wl,--gc-sections']
        command += ['-o',str(cls.native)]
        built=subprocess.run(command,capture_output=True,text=True)
        if built.returncode: raise AssertionError(built.stdout+built.stderr)
        cls.lib=ctypes.CDLL(str(cls.native))
        ptr=ctypes.POINTER(ctypes.c_uint32)
        cls.lib.nrWindowContentSourceProbe.argtypes=[ctypes.c_uint32,ctypes.c_uint32,ctypes.c_uint32,
          ptr,ctypes.c_uint32,ptr,ctypes.c_uint32,ptr,ctypes.c_uint32,ctypes.c_double,
          ctypes.c_uint32,ctypes.c_uint32,ctypes.c_uint32,ptr,ctypes.c_double,
          ctypes.POINTER(ctypes.c_double),ctypes.c_uint32,ptr]
        cls.lib.nrWindowContentSourceProbe.restype=ctypes.c_int
        cls.wasm=tmp/'window_content.wasm'
        clang=os.environ.get('WASM_CC') or shutil.which('clang')
        wasm_ld=shutil.which('wasm-ld')
        if not clang or not wasm_ld:
            raise AssertionError('clang and wasm-ld are required for import-free WASM parity')
        objects=[]
        sources=('window_content_source.c','window_texture_source.c','source_stage_components.c',
                 'source_material_sampler.c','wasm_mem.c')
        for name in sources:
            obj=tmp/(name+'.wasm.o')
            compile_command=[clang,'--target=wasm32','-std=c11','-O0','-ffp-contract=off',
              '-fno-fast-math','-fno-strict-aliasing','-Iinclude','-Isrc','-Ifreestanding',
              '-nostdlib','-ffreestanding','-fno-builtin','-c',str(SRC/name),'-o',str(obj)]
            compiled=subprocess.run(compile_command,cwd=ROOT,capture_output=True,text=True)
            if compiled.returncode: raise AssertionError(compiled.stdout+compiled.stderr)
            objects.append(str(obj))
        probe_obj=tmp/'window_content_source_probe.wasm.o'
        compiled=subprocess.run([clang,'--target=wasm32','-std=c11','-O0','-ffreestanding',
          '-fno-builtin','-Iinclude','-Isrc','-Ifreestanding','-nostdlib','-c',
          str(TESTS/'window_content_source_probe.c'),'-o',str(probe_obj)],cwd=ROOT,
          capture_output=True,text=True)
        if compiled.returncode: raise AssertionError(compiled.stdout+compiled.stderr)
        objects.append(str(probe_obj))
        linked=subprocess.run([wasm_ld,'--no-entry','--export-memory',
          '--export=nrWindowContentSourceProbe','--export=nrAlloc','--stack-first',
          '-z','stack-size=1048576','--initial-memory=16777216',*objects,'-o',str(cls.wasm)],
          cwd=ROOT,capture_output=True,text=True)
        if linked.returncode: raise AssertionError(linked.stdout+linked.stderr)

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def original_cases(self):
        from playwright.sync_api import sync_playwright
        marker='const painted = this.engine.paint(texture, m.motionMs, content), cols ='
        exposed='return {KineticRenderer,hitKinetic,activateKinetic};'
        self.assertEqual(self.original.count(marker),1)
        self.assertEqual(self.original.count(exposed),1)
        source=self.original.replace(exposed,
          'window.__nrWindowContentApi={KineticModel,KineticRenderer};'+exposed,1)
        capture=("window.__nrWindowContentCapture.push({width:tw,height:th,shape:WINDOW_SHAPES.indexOf(shape),"
          "title:Array.from(item.title,ch=>ch.codePointAt(0)),body:Array.from(item.content,ch=>ch.codePointAt(0)),"
          "label:Array.from((!shaped?`${item.id.toUpperCase()} / ${shape}`:''),ch=>ch.codePointAt(0)),"
          "clockMs:m.motionMs,ink:rgb(m.palette.ink),background:rgb(m.palette.background),accent:col,"
          "ramp:this.base.ramp.slice(),stopTotal:this.base.stopTotal,waveform:m.waveform.slice(),"
          "content:content.map(n=>({...n})),before:Array.from(texture.cells)});"
          "const painted = this.engine.paint(texture, m.motionMs, content);"
          "window.__nrWindowContentCapture[window.__nrWindowContentCapture.length-1].after=Array.from(painted.cells);"
          "const cols =")
        source=source.replace(marker,capture,1)
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,executable_path=os.environ.get('CHROMIUM') or
              shutil.which('chromium') or shutil.which('google-chrome') or shutil.which('chrome'),args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1500,'height':1000})
            errors=[]; page.on('pageerror',lambda err:errors.append(str(err)))
            page.set_content(source,wait_until='domcontentloaded',timeout=30000)
            page.wait_for_function('window.fieldGuide&&window.__nrWindowContentApi',timeout=30000)
            captures=page.evaluate("""() => {
              const api=window.__nrWindowContentApi,out=[];
              const shapes=['rectangle','rounded','ellipse','hexagon','diamond','capsule','ticket','squircle','petal','wave'];
              for(const shape of shapes){
                window.__nrWindowContentCapture=[];
                const m=new api.KineticModel();m.spaceWindows.windows=[];m.spaceWindows.selected='';
                m.waveform=Array.from({length:128},(_,i)=>Math.sin(i*.12)*.4);
                m.motionMs=1234;m.dataMs=1234;m.scene='windows';m.width=96;m.height=36;
                m.spaceWindows.add({id:'window.id',title:'Title 🌘',content:'SIGNS remain useful\\n\\nNext line',shape,x:0,y:0,z:0,width:30,height:16});
                new api.KineticRenderer(window.fieldGuide.engine).render(m,1234);
                out.push(window.__nrWindowContentCapture[0]);
                if(shape==='rectangle'){
                  const innerW=window.__nrWindowContentCapture[0].content.find(n=>n.kind==='text').width;
                  m.spaceWindows.get('window.id').content='A'.repeat(innerW-1)+'🌘Z\\n'+'B'.repeat(innerW)+'🜁C';
                  m.motionMs=Math.round(18000*window.__nrWindowContentCapture[0].stopTotal);
                  window.__nrWindowContentCapture=[];
                  new api.KineticRenderer(window.fieldGuide.engine).render(m,m.motionMs);
                  out.push(window.__nrWindowContentCapture[0]);
                }
              }
              return out;
            }""")
            browser.close()
        self.assertEqual(errors,[])
        return captures

    def setUp(self):
        if type(self).original_cases_cache is None:
            type(self).original_cases_cache=self.original_cases()

    @staticmethod
    def request_case(case):
        return {k:case[k] for k in ('width','height','shape','title','body','label','clockMs','ink','background','accent','ramp','stopTotal','waveform')}

    def call_native(self,request,initial=None):
        def arr(v): return (ctypes.c_uint32*max(1,len(v)))(*(v or [0]))
        title,body,label,ramp=map(arr,(request['title'],request['body'],request['label'],request['ramp']))
        wave=(ctypes.c_double*max(1,len(request['waveform'])))(*(request['waveform'] or [0]))
        cells0=initial or [0xdeadbeef]*(request['width']*request['height']*4)
        cells=arr(cells0)
        status=self.lib.nrWindowContentSourceProbe(request['width'],request['height'],request['shape'],
          title,len(request['title']),body,len(request['body']),label,len(request['label']),
          request['clockMs'],request['ink'],request['background'],request['accent'],ramp,
          request['stopTotal'],wave,len(request['waveform']),cells)
        return status,list(cells)[:len(cells0)]

    def call_wasm(self,request,initial=None):
        tmp=Path(self.temp.name)/'request.json'
        tmp.write_text(json.dumps({**request,'initial':initial}),encoding='utf-8')
        run=subprocess.run(['node',str(TESTS/'window_content_source_wasm_runner.mjs'),str(self.wasm),str(tmp)],
          capture_output=True,text=True,timeout=60)
        if run.returncode: raise AssertionError(run.stdout+run.stderr)
        return json.loads(run.stdout)

    def test_all_source_shapes_match_original_renderer_and_stage_wasm(self):
        self.assertEqual(self.assertHtmlHash,RC2_HTML_SHA256)
        cases=self.original_cases_cache
        self.assertEqual(len(cases),11)
        for case in cases:
            req=self.request_case(case)
            native_status,native_cells=self.call_native(req)
            self.assertEqual(native_status,0)
            self.assertEqual(native_cells,case['after'],f"native source texture shape {case['shape']}")
            wasm=self.call_wasm(req)
            self.assertEqual(wasm['status'],0)
            self.assertEqual(wasm['cells'],case['after'],f"WASM source texture shape {case['shape']}")
        self.assertEqual(RC2_WASM_SHA256,'aa04c1705a5982b924d420971bfcbc7bbedd49f1ea527a9900531b61b0c92a09')

    def test_invalid_inputs_reject_without_mutating_output(self):
        case=self.original_cases_cache[0]
        req=self.request_case(case)
        baseline=[0xa5a5a5a5]*(req['width']*req['height']*4)
        invalids=[]
        bad={**req,'waveform':req['waveform'][:-1]}; invalids.append(bad)
        bad={**req,'title':[0xd800]}; invalids.append(bad)
        bad={**req,'stopTotal':0.0}; invalids.append(bad)
        bad={**req,'shape':10}; invalids.append(bad)
        bad={**req,'width':0}; invalids.append(bad)
        for bad in invalids:
            status,cells=self.call_native(bad,baseline)
            self.assertEqual(status,-1); self.assertEqual(cells,baseline)
            wasm=self.call_wasm(bad,baseline)
            self.assertEqual(wasm['status'],-1); self.assertEqual(wasm['cells'],baseline)

    def test_capsule_uses_its_source_shaped_content_area(self):
        case=next(value for value in self.original_cases_cache if value['shape']==5)
        self.assertEqual(case['content'][0]['kind'],'text')
        self.assertNotEqual(case['content'][0]['x'],4)
        self.assertEqual(case['label'],[])
        request=self.request_case(case)
        status,cells=self.call_native(request)
        self.assertEqual(status,0); self.assertEqual(cells,case['after'])

    def test_safe_texture_width_can_exceed_4096_cells(self):
        request=self.request_case(self.original_cases_cache[0])
        request.update(width=5000,height=9)
        status,native=self.call_native(request)
        self.assertEqual(status,0)
        wasm=self.call_wasm(request)
        self.assertEqual(wasm['status'],0); self.assertEqual(wasm['cells'],native)

    def test_component_coordinate_rejection_preserves_entire_output(self):
        request=self.request_case(self.original_cases_cache[0])
        request.update(width=9,height=5000)
        sentinel=[0xa5a5a5a5]*(request['width']*request['height']*4)
        status,native=self.call_native(request,sentinel)
        self.assertEqual(status,-1); self.assertEqual(native,sentinel)
        wasm=self.call_wasm(request,sentinel)
        self.assertEqual(wasm['status'],-1); self.assertEqual(wasm['cells'],sentinel)


if __name__=='__main__': unittest.main()
