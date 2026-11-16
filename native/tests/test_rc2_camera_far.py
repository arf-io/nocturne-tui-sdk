"""Original camera far-plane domain through actual native/WASM interfaces."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import json
import struct
import subprocess
import sys
import unittest
import zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
from native.tests.historical_reference import load_rc2_workbench


class RC2CameraFar(unittest.TestCase):
    def test_actual_original_camera_default_and_far_domain(self):
        from playwright.sync_api import sync_playwright
        source=load_rc2_workbench()
        anchor='return {DEFAULT_CAMERA,wrapAngle,cameraBasis,projectSpatial,clipSpatialSegment,CameraRig,EditableRateTimeline,VectorTravel};'
        self.assertEqual(source.count(anchor),1)
        source=source.replace(anchor,'window.__sourceCamera={CameraRig};'+anchor,1)
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            try:
                page=browser.new_page();page.set_content(source,wait_until='domcontentloaded')
                page.wait_for_function('window.fieldGuide && window.__sourceCamera')
                result=page.evaluate('''()=>{const c=new window.__sourceCamera.CameraRig(),initial=c.snapshot();
                const accepted=[10000,100000,1000000].map(far=>{c.configure({far});return c.snapshot().far;});
                let rejects=false;try{c.configure({far:1000001});}catch(_){rejects=true;}
                return {initial:initial.far,accepted,rejects};}''')
                self.assertEqual(result,{'initial':100000,'accepted':[10000,100000,1000000],'rejects':True})
            finally:browser.close()

    def test_native_wasm_direct_bound_and_snapshot_domains_agree(self):
        rows=[]
        with NativeScene(2030) as s:
            s.command({'op':'define','path':'/far','value':500,'binding':{'family':'camera','field':'far'}})
            for value in [10000,100000,1000000]:
                s.command({'op':'camera','far':value});saved=s.snapshot()
                s.command({'op':'camera','far':500});s.restore(saved)
                self.assertEqual(s.info()['camera']['far'],value)
                s.command({'op':'set','path':'/far','value':value})
                frame=s.render().bytes;self.assertEqual(s.info()['camera']['far'],value)
                rows.append({'camera':s.info()['camera'],'words':list(struct.unpack('<'+'I'*(len(frame)//4),frame))})
        script='''import assert from 'node:assert/strict';import{readFileSync}from'node:fs';
        import{NativeScene}from MODULE;const s=await NativeScene.create(readFileSync(WASM),2030),rows=[];
        try{s.command({op:'define',path:'/far',value:500,binding:{family:'camera',field:'far'}});for(const value of [10000,100000,1000000]){s.command({op:'camera',far:value});const saved=s.snapshot();s.command({op:'camera',far:500});s.restore(saved);
        s.command({op:'set',path:'/far',value});const f=s.render();rows.push({camera:s.info().camera,words:Array.from(new Uint32Array(f.bytes.buffer,f.bytes.byteOffset,f.bytes.byteLength/4))});}
        for(const value of [1000001,0,-1]){const before=s.snapshot();assert.throws(()=>s.command({op:'camera',far:value}));assert.deepEqual(s.snapshot(),before);assert.throws(()=>s.command({op:'set',path:'/far',value}));assert.deepEqual(s.snapshot(),before);}
        console.log(JSON.stringify(rows));}finally{s.close();}'''
        script=script.replace('MODULE',json.dumps((ROOT/'bindings/typescript/native_scene.mjs').as_uri())).replace('WASM',json.dumps(str(ROOT/'dist/nocturne_native.wasm')))
        result=subprocess.run(['node','--input-type=module','-e',script],capture_output=True,text=True,timeout=45)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout),rows)

    def test_rejected_commands_bindings_and_invalid_snapshot_are_atomic(self):
        with NativeScene(2030) as s:
            s.command({'op':'camera','near':.1,'far':888888.875})
            saved=s.snapshot();needle=struct.pack('<d',888888.875)
            self.assertEqual(saved.count(needle),1)
            invalid=bytearray(saved);offset=saved.index(needle)
            struct.pack_into('<d',invalid,offset,1000001)
            struct.pack_into('<I',invalid,20,zlib.crc32(invalid[24:]))
            with self.assertRaises(ValueError):s.restore(invalid)
            self.assertEqual(s.snapshot(),saved)
            s.command({'op':'define','path':'/far','value':100000,'binding':{'family':'camera','field':'far'}})
            for value in [1000001,.1,0,-1,float('inf'),float('nan')]:
                for command in [{'op':'camera','far':value},{'op':'set','path':'/far','value':value}]:
                    with self.subTest(value=value,op=command['op']):
                        before=s.snapshot()
                        with self.assertRaises(ValueError):s.command(command)
                        self.assertEqual(s.snapshot(),before)


if __name__=='__main__':unittest.main()
