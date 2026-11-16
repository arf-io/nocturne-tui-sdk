from pathlib import Path
import hashlib
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest

ROOT=Path(__file__).resolve().parents[2]

class SceneMediaResume(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.gallery=self.root/'gallery.html';self.output=self.root/'media'
        subprocess.run([sys.executable,str(ROOT/'native/scripts/build_gallery.py'),'--output',str(self.gallery)],cwd=ROOT,check=True,capture_output=True)
    def tearDown(self):self.temp.cleanup()
    def command(self,*extra):
        return [sys.executable,str(ROOT/'native/scripts/capture_scene_media.py'),'--gallery',str(self.gallery),
            '--output',str(self.output),'--case','autumn','--seconds','0.2','--fps','10',*extra]
    def runCapture(self,*extra):
        return subprocess.run(self.command(*extra),cwd=ROOT,capture_output=True,text=True,timeout=60)
    def testCompletedResumePreservesFilesAndRejectsCorruption(self):
        result=self.runCapture();self.assertEqual(result.returncode,0,result.stderr)
        paths=[p for p in self.output.rglob('*') if p.is_file() and p.name!='MEDIA.json']
        before={str(p): (p.stat().st_mtime_ns,hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths}
        result=self.runCapture('--resume');self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(before,{str(p):(p.stat().st_mtime_ns,hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths})
        manifest=(self.output/'MEDIA.json').read_bytes();paths[0].write_bytes(b'corrupt')
        result=self.runCapture('--resume');self.assertNotEqual(result.returncode,0)
        self.assertEqual((self.output/'MEDIA.json').read_bytes(),manifest)
    def testChangedSourceRejectsWithoutChangingManifest(self):
        self.assertEqual(self.runCapture().returncode,0)
        before=(self.output/'MEDIA.json').read_bytes();self.gallery.write_bytes(self.gallery.read_bytes()+b'\n<!-- altered -->')
        self.assertNotEqual(self.runCapture('--resume').returncode,0)
        self.assertEqual((self.output/'MEDIA.json').read_bytes(),before)
    def testActualBrowserErrorCannotBecomePassingResume(self):
        self.gallery.write_bytes(self.gallery.read_bytes()+b'<script>throw Error("resume browser fault")</script>')
        self.assertNotEqual(self.runCapture().returncode,0)
        report=json.loads((self.output/'MEDIA.json').read_text());self.assertTrue(report['pageErrors'])
        before=(self.output/'MEDIA.json').read_bytes()
        self.assertNotEqual(self.runCapture('--resume').returncode,0)
        self.assertEqual((self.output/'MEDIA.json').read_bytes(),before)
    def testRealInterruptedProcessResumesAndPreservesPartialFiles(self):
        process=subprocess.Popen(self.command(),cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
        deadline=time.monotonic()+30;partial=[]
        while time.monotonic()<deadline and process.poll() is None:
            partial=list(self.output.rglob('*.png'))
            if partial:break
            time.sleep(.02)
        try:
            self.assertTrue(partial,'Real process did not produce a partial screenshot')
            os.killpg(process.pid,signal.SIGTERM);process.communicate(timeout=10)
            before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in partial}
            result=self.runCapture('--resume');self.assertEqual(result.returncode,0,result.stderr+result.stdout)
            self.assertEqual(before,{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in partial})
            report=json.loads((self.output/'MEDIA.json').read_text())
            self.assertTrue(report['passed']);self.assertTrue(report['previousAttempts'])
            self.assertTrue(report['cases'][0]['complete'])
        finally:
            if process.poll() is None:os.killpg(process.pid,signal.SIGTERM);process.communicate(timeout=10)

if __name__=='__main__':unittest.main()
