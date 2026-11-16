"""Extraction runner refuses the wrong release scope before executing payloads."""
import sys,tempfile,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from rc2_package import writeArchive
class RC2SDKCheck(unittest.TestCase):
 def test_wrong_profile_is_rejected_before_extraction(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);readme=root/'README.md';readme.write_text('SDK input fixture');archive=root/'sdk.zip'
   writeArchive(archive,{'README.md':readme},{'qualificationProfile':'exhaustive','build':'1.0.0-rc.2'})
   output=root/'check';result=subprocess.run([sys.executable,str(ROOT/'scripts/check_rc2_sdk.py'),'--archive',str(archive),'--output',str(output)],capture_output=True,text=True)
   self.assertNotEqual(result.returncode,0);self.assertIn('RC2',result.stdout+result.stderr);self.assertFalse((output/'extracted').exists())
if __name__=='__main__':unittest.main()


class ExtractionEnvironment(unittest.TestCase):
    """fresh-sdk-07: the extracted SDK's codegen test needs the bound TypeScript module."""
    def test_binds_the_typescript_module_beside_tsc_on_path_unless_already_set(self):
        import os
        from check_rc2_sdk import extraction_environment
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'node_modules/typescript/bin').mkdir(parents=True)
            (root / 'node_modules/typescript/lib').mkdir(parents=True)
            (root / 'node_modules/typescript/bin/tsc').write_text('#!/bin/sh\n'); os.chmod(root / 'node_modules/typescript/bin/tsc', 0o755)
            (root / 'node_modules/typescript/lib/typescript.js').write_text('')
            (root / 'bin').mkdir(); os.symlink(root / 'node_modules/typescript/bin/tsc', root / 'bin/tsc')
            env = extraction_environment({'PATH': str(root / 'bin'), 'LLVM_PROFILE_FILE': 'x', 'NOCTURNE_COVERAGE': '1'})
            self.assertEqual(env['NOCTURNE_TYPESCRIPT_MODULE'], str((root / 'node_modules/typescript/lib/typescript.js').resolve()))
            self.assertEqual(env['NOCTURNE_COVERAGE'], '0'); self.assertNotIn('LLVM_PROFILE_FILE', env)
            kept = extraction_environment({'PATH': str(root / 'bin'), 'NOCTURNE_TYPESCRIPT_MODULE': '/elsewhere/typescript.js'})
            self.assertEqual(kept['NOCTURNE_TYPESCRIPT_MODULE'], '/elsewhere/typescript.js')
            self.assertNotIn('NOCTURNE_TYPESCRIPT_MODULE', extraction_environment({'PATH': directory}))
