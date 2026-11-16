"""Real compiler-produced binary dependency boundary; no mocked tools/binaries."""
import json,os,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import package_contracts
from toolchain import discover
class SDKShippingCore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.temp.cleanup)
        cls.root=Path(cls.temp.name).resolve();cc=discover()['wasmCC']
        if not cc:raise RuntimeError('Actual clang required for shipping binary boundary tests')
        cls.artifacts={};cls.compilerExecutions=[]
        for kind,source,extra in (
            ('pure','int arithmetic(int x){return x+1;}',[]),
            ('strings','#include <string.h>\nint strings(const char*a,const char*b){return strncmp(a,b,3)+(strrchr(a,46)!=0);}',[]),
            ('coverage','int arithmetic(int x){return x+1;}',['-fprofile-instr-generate','-fcoverage-mapping']),
            ('file_io','#include <stdio.h>\nint write_file(void){FILE*f=fopen("boundary.txt","w");return f?fclose(f):-1;}',[])):
            path=cls.root/(kind+'.c');path.write_text(source);library=cls.root/(kind+('.dylib' if sys.platform=='darwin' else '.so'))
            argv=[cc,'-std=c11','-O1','-fPIC','-dynamiclib' if sys.platform=='darwin' else '-shared',*extra,str(path),'-o',str(library)]
            subprocess.run(argv,capture_output=True,text=True,check=True);cls.compilerExecutions.append(argv);cls.artifacts[kind]=library
    def test_real_pure_binary_accepted_and_instrumented_host_dependent_rejected(self):
        report=package_contracts.validateShippingCore(self.artifacts['pure'])
        self.assertEqual(report['errors'],[]);self.assertFalse(report['instrumented'])
        self.assertEqual(package_contracts.validateShippingCore(self.artifacts['strings'])['errors'],[])
        for name in ('coverage','file_io'):
            with self.subTest(name=name),self.assertRaises(ValueError):package_contracts.validateShippingCore(self.artifacts[name])
    def test_invalid_binary_and_symlink_rejected(self):
        invalid=self.root/'invalid.so';invalid.write_bytes(b'not a native binary')
        with self.assertRaises(ValueError):package_contracts.validateShippingCore(invalid)
        link=self.root/'link.so';link.symlink_to(self.artifacts['pure'])
        with self.assertRaises(ValueError):package_contracts.validateShippingCore(link)
    def test_actual_sdk_pure_library_matches_active_core_state_and_frames(self):
        sys.path.insert(0,str(ROOT/'bindings/python'))
        from nocturne_native import NativeScene
        name='libnocturne_native.dylib' if sys.platform=='darwin' else 'libnocturne_native.so'
        primary=ROOT/'dist'/name
        pure=primary.parent/'dependency-audit'/name if os.environ.get('NOCTURNE_COVERAGE')=='1' else primary
        self.assertTrue(pure.is_file(),'Actual built shipping core required')
        self.assertEqual(package_contracts.validateShippingCore(pure)['errors'],[])
        with NativeScene(2030,library=pure) as shipping,NativeScene(2030,library=primary) as active:
            for scene in (shipping,active):
                scene.command({'op':'draft','text':'Owned source é中','emitWeather':False})
                scene.command({'op':'widget','id':1,'kind':'progress','value':1e-7})
                scene.advance_to(250000)
            self.assertEqual(shipping.snapshot(),active.snapshot())
            self.assertEqual(shipping.render().bytes,active.render().bytes)
            self.assertEqual(shipping.info_complete()['contract'],active.info_complete()['contract'])

    @unittest.skipUnless(sys.platform == 'darwin', 'Mach-O relocation contract')
    def test_actual_macos_sdk_consumer_loads_relocated_library(self):
        name = 'libnocturne_native.dylib'
        primary = ROOT / 'dist' / name
        pure = primary.parent / 'dependency-audit' / name if os.environ.get('NOCTURNE_COVERAGE') == '1' else primary
        identity = subprocess.run(['/usr/bin/otool', '-D', str(pure)], capture_output=True, text=True, check=True)
        self.assertEqual(identity.stdout.splitlines()[1].strip(), '@rpath/' + name)
        with tempfile.TemporaryDirectory(prefix='nocturne-sdk-relocation-') as directory:
            folder = Path(directory).resolve()
            authored = folder / 'authored'; libraries = authored / 'lib'; libraries.mkdir(parents=True)
            shutil.copy2(pure, libraries / name)
            cc = discover()['cc']
            subprocess.run([cc, '-std=c11', '-I' + str(ROOT / 'include'), str(ROOT / 'examples/native_smoke.c'),
                            '-L' + str(libraries), '-lnocturne_native', '-Wl,-rpath,@executable_path/lib',
                            '-o', str(authored / 'consumer')], capture_output=True, text=True, check=True)
            moved = folder / 'relocated'; authored.rename(moved)
            environment = dict(os.environ, DYLD_PRINT_LIBRARIES='1')
            environment.pop('DYLD_LIBRARY_PATH', None)
            result = subprocess.run([str(moved / 'consumer')], env=environment, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn(str(moved / 'lib' / name), result.stderr)
            self.assertNotIn(str(pure), result.stderr)
            self.assertEqual(json.loads(result.stdout)['build'], json.loads((ROOT.parent/'RELEASE.json').read_text())['build'])
