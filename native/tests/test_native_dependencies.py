"""Inspect real compiler output without hiding compiler-provided memory guards."""
from pathlib import Path
import ctypes
import json
import struct
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import dependencies


class NativeDependencyTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform == 'darwin', 'Mach-O dependency fixture')
    def testDarwinRealIoDependencyCannotDisappearFromAudit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'output.c'
            source.write_text('#include <stdio.h>\nint outputPayload(const char *s) { return puts(s); }\n')
            library = root / 'output.dylib'
            subprocess.run([shutil.which('cc'), '-dynamiclib', str(source), '-o', str(library)], check=True, capture_output=True)
            result = dependencies.inspectNativeSymbols(library)
            self.assertIn('puts', result['symbols'])
            self.assertIn('Unexpected linked function: puts', result['errors'])

    @unittest.skipUnless(sys.platform == 'darwin', 'Darwin compiler SDK selection')
    def testSdkMetadataUsesTheSelectedCompiler(self):
        cc = os.environ.get('CC') or shutil.which('cc')
        selected = dependencies.compilerSdkSettings(cc)
        self.assertEqual(selected.name, 'SDKSettings.json')
        self.assertTrue(selected.is_file())
        self.assertTrue((selected.parent / 'usr/include').is_dir())

    @unittest.skipUnless(sys.platform.startswith('linux'), 'ELF hardening fixture')
    def testRealHardenedMemoryFunctionsRemainNative(self):
        self.assertTrue(callable(getattr(dependencies, 'inspectNativeSymbols', None)))
        cc = os.environ.get('CC') or shutil.which('cc')
        self.assertTrue(cc, 'a real C compiler is required')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'memory.c'
            source.write_text('''#include <string.h>
#include <stddef.h>
unsigned copyPayload(const char *src, size_t count) {
    char bytes[32]; memcpy(bytes, src, count); return (unsigned char)bytes[count - 1];
}
unsigned movePayload(const char *src, size_t count) {
    char bytes[32]; memcpy(bytes, src, 32); memmove(bytes + 1, bytes, count);
    return (unsigned char)bytes[count];
}
''')
            library = root / 'memory.so'
            subprocess.run([cc, '-O2', '-fPIC', '-shared', '-D_FORTIFY_SOURCE=2',
                            '-fstack-protector-all', str(source), '-o', str(library)],
                           capture_output=True, text=True, check=True)
            result = dependencies.inspectNativeSymbols(library)
            self.assertIn('__memcpy_chk', result['symbols'])
            self.assertIn('__memmove_chk', result['symbols'])
            self.assertIn('__stack_chk_fail', result['symbols'])
            self.assertEqual(result['errors'], [])
            if '__stack_chk_guard' in result['symbols']:
                self.assertEqual(result['elfImportTypes']['__stack_chk_guard'],'OBJECT')
                self.assertIn('__stack_chk_guard',result['compilerCanaryData'])
            native = ctypes.CDLL(str(library))
            for name in ('copyPayload', 'movePayload'):
                function = getattr(native, name)
                function.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
                function.restype = ctypes.c_uint
                self.assertEqual(function(b'abcdefghijklmnopqrstuvwxyz012345', 4), ord('d'))

    @unittest.skipUnless(sys.platform.startswith('linux'), 'ELF dependency fixture')
    def testRealIoDependencyIsStillRejected(self):
        self.assertTrue(callable(getattr(dependencies, 'inspectNativeSymbols', None)))
        cc = os.environ.get('CC') or shutil.which('cc')
        self.assertTrue(cc, 'a real C compiler is required')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'output.c'
            source.write_text('#include <stdio.h>\nint outputPayload(const char *s) { return puts(s); }\n')
            library = root / 'output.so'
            subprocess.run([cc, '-O2', '-fPIC', '-shared', str(source), '-o', str(library)],
                           capture_output=True, text=True, check=True)
            result = dependencies.inspectNativeSymbols(library)
            self.assertIn('puts', result['symbols'])
            self.assertIn('Unexpected linked function: puts', result['errors'])


    @unittest.skipUnless(sys.platform.startswith('linux'), 'actual shipping ELF linkage')
    def testCurrentCoreRetainsMemoryOnlyImports(self):
        library = ROOT / 'dist/libnocturne_native.so'
        if os.environ.get('NOCTURNE_COVERAGE') == '1':
            library = library.parent / 'dependency-audit' / library.name
        self.assertTrue(library.is_file(), str(library))
        self.assertEqual(dependencies.inspectNativeSymbols(library)['errors'], [])

    @unittest.skipUnless(sys.platform.startswith('linux'), 'actual shipping ELF consumer')
    def testCurrentCoreLinksAndExecutesWithoutLibm(self):
        library = ROOT / 'dist/libnocturne_native.so'
        if os.environ.get('NOCTURNE_COVERAGE') == '1':
            library = library.parent / 'dependency-audit' / library.name
        self.assertTrue(library.is_file(), str(library))
        with tempfile.TemporaryDirectory(prefix='nocturne-elf-consumer-') as directory:
            folder = Path(directory); source = folder / 'consumer.c'; executable = folder / 'consumer'
            source.write_text('#include "nocturne_native.h"\nint main(void){return nrContextSize()>0?0:1;}\n')
            compiled = subprocess.run([os.environ.get('CC') or shutil.which('cc'), '-std=c11',
                '-I'+str(ROOT/'include'),str(source),str(library),
                '-Wl,-rpath,'+str(library.parent),'-o',str(executable)],capture_output=True,text=True)
            self.assertEqual(compiled.returncode,0,compiled.stdout+compiled.stderr)
            observed = subprocess.run([str(executable)],env={**os.environ,'PATH':''},capture_output=True,text=True)
            self.assertEqual(observed.returncode,0,observed.stdout+observed.stderr)

    @unittest.skipUnless(sys.platform.startswith('linux'), 'actual qualifier compiler variants')
    def testEveryQualifierNativeCompilerVariantPreservesOriginalHypotWithoutLibm(self):
        listed = subprocess.run([sys.executable,str(ROOT/'scripts/qualify.py'),'--strict','--list'],
            cwd=ROOT,capture_output=True,text=True,check=True)
        cases=json.loads(listed.stdout); variants={}
        for case in cases:
            argv=case['argv']
            if any(str(arg).endswith('/src/camera_original.c') for arg in argv):
                first=next(i for i,arg in enumerate(argv) if str(arg).endswith('.c') and '/src/' in str(arg))
                variants.setdefault(tuple(argv[:first]),[]).append(case['id'])
        self.assertGreaterEqual(len(variants),3)
        values=[[3,4,12],[1,1,1],[0,0,0],[-3,4,-12],[1e300,1e-300,2e300],
                [1e-300,-2e-300,3e-300],[5e-324,5e-324,0],[1,2e-16,3e-16]]
        oracle=subprocess.run(['node','-e',
            'const v=JSON.parse(process.argv[1]);console.log(JSON.stringify(v.map(x=>{let b=Buffer.alloc(8);b.writeDoubleLE(Math.hypot(...x));return b.toString("hex")})))',json.dumps(values)],
            capture_output=True,text=True,check=True)
        expected=json.loads(oracle.stdout)
        with tempfile.TemporaryDirectory(prefix='nocturne-original-hypot-') as directory:
            folder=Path(directory);source=folder/'probe.c'
            source.write_text('#include "original_math.h"\n#include <stdio.h>\n#include <stdlib.h>\nint main(int argc,char **argv){if(argc!=4)return 2;printf("%a\\n",nrOriginalHypot(strtod(argv[1],0),strtod(argv[2],0),strtod(argv[3],0)));return 0;}\n')
            for index,(prefix,ids) in enumerate(variants.items()):
                with self.subTest(cases=ids):
                    executable=folder/('probe-'+str(index))
                    compiled=subprocess.run([*prefix,'-ffunction-sections','-fdata-sections',
                        str(source),str(ROOT/'src/math.c'),'-Wl,--gc-sections','-o',str(executable)],
                        cwd=ROOT,capture_output=True,text=True)
                    self.assertEqual(compiled.returncode,0,compiled.stdout+compiled.stderr)
                    for numbers,bits in zip(values,expected):
                        result=subprocess.run([str(executable),*[str(x) for x in numbers]],capture_output=True,text=True,check=True)
                        actual=struct.pack('<d',float.fromhex(result.stdout.strip())).hex()
                        self.assertEqual(actual,bits,(numbers,ids,result.stdout))


    @unittest.skipUnless(sys.platform.startswith('linux'), 'real compiler memory alias')
    def testActualCompilerMemoryComparisonAliasRemainsNative(self):
        cc=os.environ.get('CC') or shutil.which('cc')
        with tempfile.TemporaryDirectory(prefix='nocturne-memory-alias-') as directory:
            folder=Path(directory);source=folder/'compare.c';library=folder/'compare.so'
            source.write_text('#include <string.h>\nint sameBytes(const char*a,const char*b,size_t n){return memcmp(a,b,n)==0;}\n')
            subprocess.run([cc,'-O2','-fPIC','-shared',str(source),'-o',str(library)],check=True,capture_output=True)
            inspected=dependencies.inspectNativeSymbols(library)
            self.assertTrue(set(inspected['symbols']) & {'memcmp','bcmp'},inspected)
            self.assertEqual(inspected['errors'],[])
            function=ctypes.CDLL(str(library)).sameBytes;function.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_size_t];function.restype=ctypes.c_int
            self.assertEqual(function(b'abc',b'abc',3),1)
            self.assertEqual(function(b'abc',b'abd',3),0)
            self.assertEqual(function(b'abc',b'abd',2),1)

    @unittest.skipUnless(sys.platform.startswith('linux'), 'ELF guard class rejection')
    def testFunctionNamedStackCanaryDataIsNotAccepted(self):
        cc=os.environ.get('CC') or shutil.which('cc')
        with tempfile.TemporaryDirectory(prefix='nocturne-hostile-guard-') as directory:
            folder=Path(directory);source=folder/'guard.c';library=folder/'guard.so'
            source.write_text('extern void __stack_chk_guard(void);void invokeGuard(void){__stack_chk_guard();}\n')
            subprocess.run([cc,'-O2','-fno-stack-protector','-fPIC','-shared',str(source),'-o',str(library)],check=True,capture_output=True)
            inspected=dependencies.inspectNativeSymbols(library)
            self.assertIn('__stack_chk_guard',inspected['symbols'])
            self.assertIn('Unexpected linked function: __stack_chk_guard',inspected['errors'])


if __name__ == '__main__':
    unittest.main()
