from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
import hashlib
import json
import subprocess
import sys
import tempfile
import threading
import unittest
import zipfile
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]

class NativeMediaSite(unittest.TestCase):
    def testInvalidCaptureNeverPublishesOrChangesExistingOutput(self):
        for failure in ['incomplete', 'escaped', 'symlink', 'hash', 'existing']:
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                media = root / 'media'
                media.mkdir()
                with zipfile.ZipFile(ROOT / 'native/evidence/scene-media-capture-20261012/waterfall-media.zip') as archive:
                    archive.extractall(media)
                manifest_path = media / 'MEDIA.json'
                capture = json.loads(manifest_path.read_text())
                record = capture['cases'][0]['samples'][0]['screenshot']
                output = root / 'site'
                if failure == 'incomplete':
                    capture['cases'][0]['complete'] = False
                elif failure in ['escaped', 'symlink']:
                    outside = root / 'outside.png'
                    outside.write_bytes((media / record['path']).read_bytes())
                    if failure == 'escaped':
                        record['path'] = '../outside.png'
                    else:
                        link = media / 'linked.png'
                        link.symlink_to(outside)
                        record['path'] = 'linked.png'
                elif failure == 'hash':
                    record['sha256'] = '0' * 64
                else:
                    output.mkdir()
                    (output / 'keep.txt').write_bytes(b'preserved output')
                manifest_path.write_text(json.dumps(capture))
                before = manifest_path.read_bytes()
                result = subprocess.run([
                    sys.executable, str(ROOT / 'native/scripts/build_media_site.py'),
                    '--media', str(media), '--output', str(output), '--inline-media',
                ], cwd=ROOT, capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(manifest_path.read_bytes(), before)
                if failure == 'existing':
                    self.assertEqual(list(output.iterdir()), [output / 'keep.txt'])
                    self.assertEqual((output / 'keep.txt').read_bytes(), b'preserved output')
                else:
                    self.assertFalse(output.exists())

    def testInlineDocumentKeepsExactVideoAndImageBytesInSupportedFormats(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);media=root/'media';media.mkdir()
            with zipfile.ZipFile(ROOT/'native/evidence/scene-media-capture-20261012/waterfall-media.zip') as z:z.extractall(media)
            output=root/'site';r=subprocess.run([sys.executable,str(ROOT/'native/scripts/build_media_site.py'),'--media',str(media),'--output',str(output),'--inline-media'],cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr+r.stdout);self.assertTrue(all(p.suffix in ['.html','.json'] for p in output.iterdir()))
            server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(output)));worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
            try:
                with sync_playwright() as pw:
                    browser=pw.chromium.launch();page=browser.new_page();page.goto(f'http://127.0.0.1:{server.server_port}/media.html');page.wait_for_function('mediaSite.ready')
                    self.assertTrue(page.evaluate('mediaSite.current.video.path.startsWith("data:video/webm;base64,")'))
                    page.locator('canvas').click(position={'x':525,'y':68});page.wait_for_function('mediaSite.videoFrames > 0')
                    with page.expect_download() as download:
                        page.evaluate('mediaSite.original("video")')
                    actual=Path(download.value.path()).read_bytes();record=json.loads((media/'MEDIA.json').read_text())['cases'][0]['video']
                    self.assertEqual(hashlib.sha256(actual).hexdigest(),record['sha256']);browser.close()
            finally:server.shutdown();server.server_close();worker.join()
    def testRealCaptureImportsNativeArtAndRejectsCorruptOriginal(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);media=root/'media';media.mkdir()
            with zipfile.ZipFile(ROOT/'native/evidence/scene-media-capture-20261012/waterfall-media.zip') as z:z.extractall(media)
            output=root/'site';r=subprocess.run([sys.executable,str(ROOT/'native/scripts/build_media_site.py'),'--media',str(media),'--output',str(output)],cwd=ROOT,capture_output=True,text=True,timeout=60)
            self.assertEqual(r.returncode,0,r.stderr+r.stdout)
            manifest=json.loads((output/'MANIFEST.json').read_text())
            for name,record in manifest['files'].items():self.assertEqual(hashlib.sha256((output/name).read_bytes()).hexdigest(),record['sha256'])
            server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(output)));worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
            try:
                with sync_playwright() as pw:
                    browser=pw.chromium.launch();page=browser.new_page(viewport={'width':1100,'height':1000});url=f'http://127.0.0.1:{server.server_port}/media.html';page.goto(url);page.wait_for_function('mediaSite.ready')
                    self.assertEqual(page.evaluate('mediaSite.scene.info().cellArt.length'),2)
                    self.assertTrue(page.evaluate('mediaSite.scene.info().cellArt.every(a=>a.width*a.height===1600)'))
                    self.assertTrue(page.evaluate('mediaSite.originalVerified'))
                    page.locator('#originals a').first.focus()
                    self.assertTrue(page.evaluate('mediaSite.scene.info().widgets.find(w=>w.id===8).selected'))
                    with page.expect_popup() as popup:
                        page.locator('canvas').click(position={'x':200,'y':858})
                    original=popup.value;original.wait_for_load_state();self.assertTrue(original.url.endswith('.png'));original.close()
                    page.locator('canvas').click(position={'x':525,'y':68})
                    page.wait_for_function('mediaSite.videoFrames > 0')
                    self.assertIn('Video',page.evaluate('mediaSite.scene.info().widgets.find(w=>w.id===7).text'))
                    page.keyboard.press(' ')
                    name=page.evaluate('mediaSite.current.samples[0].screenshot.path');(output/name).write_bytes(b'corrupt')
                    bad=browser.new_page();bad.goto(url);bad.wait_for_function('mediaSite.error !== null');self.assertIn('capture integrity',bad.locator('#status').text_content());browser.close()
            finally:server.shutdown();server.server_close();worker.join()
    def testRenamedNonMediaExtensionRejectsWithoutOutput(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);media=root/'media';media.mkdir()
            with zipfile.ZipFile(ROOT/'native/evidence/scene-media-capture-20261012/waterfall-media.zip') as z:z.extractall(media)
            path=media/'MEDIA.json';capture=json.loads(path.read_text());record=capture['cases'][0]['samples'][0]['screenshot'];source=media/record['path'];renamed=source.with_suffix('.txt');source.rename(renamed);record['path']=str(renamed.relative_to(media));path.write_text(json.dumps(capture))
            output=root/'site';r=subprocess.run([sys.executable,str(ROOT/'native/scripts/build_media_site.py'),'--media',str(media),'--output',str(output)],cwd=ROOT,capture_output=True,text=True)
            self.assertNotEqual(r.returncode,0);self.assertFalse(output.exists())

if __name__=='__main__':unittest.main()
