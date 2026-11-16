"""Original32window publiccapacity and fullapplication oracle."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import copy,gzip,json,subprocess,tempfile,unittest
from pathlib import Path
from native.tests.presentation_copy_reference import assert_snapshot_presentation
from native.tests.test_rc2_window_application import OriginalWindowApplication,application_commands,rgb_cells,ROOT
from native.hosts.python.atelier_application import rc2_window_commands
from native.bindings.python.nocturne_native import NativeScene

class OriginalWindowCapacity(OriginalWindowApplication):
    # Reuse only the actualsourceoracle, not the inherited applicationtests.
    @staticmethod
    def authored():
        preset=json.loads((ROOT/'examples/rc2_window_presets.json').read_text())['scenes']['windows']
        items=[];commands=application_commands()
        for i in range(3,32):
            item={'id':f'original{i+1}','title':f'WINDOW {i+1} / original contract','content':f'DOCUMENT {i+1}\nNative retained source','x':-20+(i%8)*5,'y':-9+(i//8)*6,'z':20+i*.25,'width':18,'height':12,'yaw':0,'pitch':0,'roll':0,'shape':'rounded'}
            items.append(item);commands.extend(rc2_window_commands(item,source_index=i,native_id=i+1,palette=preset['palette'],options=preset['options'],appearance=preset['appearance'],waveform=preset['waveform']))
        # Source WindowManager.add retains the originally selected Pearl.
        commands.append({"op":"window","id":1})
        return items,commands

    def test_original32windows_native_and_wasm_fullframes(self):
        items,commands=self.authored()
        source=self.page.evaluate("""items=>{const m=new window.__rc2WindowComposition.KineticModel();m.setScene('windows');for(const item of items)m.spaceWindows.add(item);let rejected=false;try{m.spaceWindows.add({id:'overflow',title:'overflow'});}catch(e){rejected=true;}return{count:m.spaceWindows.list().length,rejected};}""",items)
        self.assertEqual(source,{'count':32,'rejected':True})
        with NativeScene(2030) as scene:
            for command in commands:scene.command(command)
            self.assertEqual(len(scene.info()['windows']),32)
            before=scene.snapshot()
            with self.assertRaises(ValueError):scene.command({'op':'window','id':33,'title':'overflow'})
            self.assertEqual(scene.snapshot(),before)
            for t in (0,1700000):
                scene.advance_to(t);self.assert_original(scene,'windows',t,extra_windows=items)
            saved=scene.snapshot();frame=scene.render().bytes
            scene.command({'op':'window-action','id':32,'action':'close'});scene.advance_to(3000000)
            self.assertEqual(scene.info()['windows'][-1]['visible'],0)
            scene.restore(saved);self.assertEqual(scene.render().bytes,frame)
        with tempfile.TemporaryDirectory() as d:
            request=Path(d)/'request.json';response=Path(d)/'response.json'
            request.write_text(json.dumps([{'id':'original32','commands':commands,'times':[0,1700000]}]))
            subprocess.run(['node',str(ROOT/'tests/rc2_window_application_wasm_runner.mjs'),str(request),str(response)],check=True)
            for f in json.loads(response.read_text()):self.assertEqual(rgb_cells(f['words']),rgb_cells(self.original('windows',f['timeUs'],extra_windows=items)['words']))

    def test_ordinary32window_textures_titles_and_snapshot(self):
        with NativeScene(2030) as scene:
            for i in range(1,33):
                scene.command({'op':'window','id':i,'title':f'TITLE {i}','text':f'BODY {i}','durationMs':0})
                scene.command({'op':'window-texture','id':i,'width':1,'height':1,'cells':[[65+i%26,0x99bbdd,0x112233]]})
            before=scene.snapshot();scene.render();self.assertEqual(scene.snapshot(),before)
            rows=scene.info_complete()['windows'];self.assertEqual(len(rows),32)
            self.assertEqual(rows[-1]['title'],'TITLE 32');self.assertEqual(rows[-1]['text'],'BODY 32')
            self.assertEqual(rows[-1]['texture']['cells'],[[71,0x99bbdd,0x112233]])
            scene.restore(before);self.assertEqual(scene.snapshot(),before)
            with self.assertRaises(ValueError):scene.command({'op':'window','id':33})
            self.assertEqual(scene.snapshot(),before)

    def test_actual72snapshot_from_independent_window_branch(self):
        fixture=ROOT/'tests/fixtures/window-capacity-schema72.bin.gz'
        expected=gzip.decompress((ROOT/'tests/fixtures/window-capacity-schema72.frame.bin.gz').read_bytes())
        with NativeScene(2030) as scene:
            scene.restore(gzip.decompress(fixture.read_bytes()))
            assert_snapshot_presentation(self,scene,expected)
            saved=scene.snapshot();scene.restore(saved);self.assertEqual(scene.snapshot(),saved)

    def test_actual69snapshot_preserves_fullframe_and_source_documents(self):
        fixture=ROOT/'tests/fixtures/window-application-schema69.bin.gz'
        expected=gzip.decompress((ROOT/'tests/fixtures/window-application-schema69-frame.bin.gz').read_bytes())
        with NativeScene(2030) as scene:
            scene.restore(gzip.decompress(fixture.read_bytes()));assert_snapshot_presentation(self,scene,expected)
            self.assertEqual([w['content']['label'] for w in scene.info()['windows']],['pearl','atlas','iris'])
            saved=scene.snapshot();scene.restore(saved);self.assertEqual(scene.snapshot(),saved)

# Avoid inheriting the complete independent application suite a secondtime.
for _name in tuple(vars(OriginalWindowApplication)):
    if _name.startswith('test_'):setattr(OriginalWindowCapacity,_name,None)
if __name__=='__main__':unittest.main()
