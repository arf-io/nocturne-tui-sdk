#!/usr/bin/env python3
"""Exercise source recovery, DOM focus and IME transactions in real Chromium."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import platform
import shutil
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / 'Nocturne-Test-Harness.html'


class BrowserAccessibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(headless=True,
            executable_path=os.environ.get('CHROMIUM') or shutil.which('chromium') or shutil.which('google-chrome'),
            args=['--no-sandbox'])
        cls.browserVersion = cls.browser.version

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def setUp(self):
        self.page = self.browser.new_page(viewport={'width': 1280, 'height': 1000})
        self.errors = []
        self.requests = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.on('request', lambda request: self.requests.append(request.url))
        self.page.set_content(HTML.read_text())
        self.page.wait_for_function('window.nativeLab !== undefined', timeout=30000)
        self.page.set_default_timeout(10000)
        self.load('silk')

    def tearDown(self):
        self.page.close()
        self.assertEqual(self.errors, [], 'Browser JavaScript exceptions')
        self.assertEqual(self.requests, [], 'Standalone gallery initiated network requests')

    def evaluate(self, script, argument=None):
        return self.page.evaluate(script, argument)

    def load(self, identifier):
        self.evaluate("id=>{nativeLab.load(nativeLab.recipes.find(r=>r.id===id));nativeLab.hold();nativeLab.draw();}", identifier)

    def info(self):
        return self.evaluate('nativeLab.scene.info()')

    def test_retained_reader_uses_native_run_source_after_retarget(self):
        self.evaluate("""() => {
          const s=nativeLab.scene;s.command({op:'reset',seed:2030});
          s.command({op:'draft',text:'é日本',emitWeather:false});
          s.command({op:'text',id:41,text:'👩‍🔧'});
          s.command({op:'window',id:7,title:'עברית',text:'A\\n中'});
          nativeLab.hold();window.runReads=[];
          const original=s.textRunSource.bind(s);
          s.textRunSource=(kind,id)=>{runReads.push([kind,id]);return original(kind,id);};
          window.beforeRunReader=s.snapshot();nativeLab.draw();
        }""")
        content=self.page.locator('#readable').input_value()
        for source in ['é日本','👩‍🔧','עברית','A\n中']:self.assertIn(source,content)
        reads=self.evaluate('runReads')
        for key in [[0,0],[1,41],[2,7],[3,7]]:self.assertIn(key,reads)
        self.assertTrue(self.evaluate('nativeLab.scene.snapshot().every((v,i)=>v===beforeRunReader[i])'))
        self.evaluate("() => {nativeLab.scene.command({op:'text',id:41,text:'Updated é'});nativeLab.draw();}")
        self.assertIn('Updated é',self.page.locator('#readable').input_value())

    def test_opt_in_complete_metadata_recovers_over_capacity_source_without_state_change(self):
        self.assertEqual(self.page.locator('#metadata-recover').count(), 1,
                         'An explicit complete metadata recovery control is required')
        self.evaluate("""() => {
          const s=nativeLab.scene;s.command({op:'reset',seed:8128});
          s.command({op:'pause',paused:true});const text='🙂'.repeat(2048);
          for(let id=1;id<=24;id++)s.command({op:'text',id,text});
          for(let id=1;id<=12;id++)s.command({op:'window',id,title:`Retained ${id}`,text,position:[0,0,16000]});
          s.command({op:'draft',text:'界'.repeat(250001),emitWeather:false});
          nativeLab.draw();window.beforeCompleteMetadata=s.snapshot();window.beforeCompleteFrame=s.render().bytes.slice();
        }""")
        self.assertGreater(self.evaluate('''()=>{const s=nativeLab.scene;
            const status=s.exports.nrInfoPage(s.context,0,0,0,s.particleBuffer,4);
            if(status!==1)throw Error('Metadata size probe failed');
            return new Uint32Array(s.exports.memory.buffer,s.particleBuffer,4)[0];}'''), 1048576)
        self.assertEqual(self.info(), {'error': 'metadata capacity exceeded'})
        self.page.locator('#metadata-recover').click()
        record=json.loads(self.page.locator('#metadata-complete').input_value())
        self.assertEqual(len(record['textRuns']),24)
        self.assertEqual(len(record['windows']),12)
        self.assertTrue(all(x['text']=='🙂'*2048 for x in record['textRuns']+record['windows']))
        self.assertTrue(record['prompt']['text']=='界'*250001, 'complete reader lost large prompt source')
        self.assertIn('Frozen',self.page.locator('#metadata-recovery-status').inner_text())
        self.assertTrue(self.evaluate('nativeLab.scene.snapshot().every((x,i)=>x===beforeCompleteMetadata[i])'))
        self.assertTrue(self.evaluate('nativeLab.scene.render().bytes.every((x,i)=>x===beforeCompleteFrame[i])'))
        self.assertEqual(self.info(), {'error': 'metadata capacity exceeded'})
        with self.page.expect_download() as download:
            self.page.locator('#metadata-download').click()
        saved=json.loads(Path(download.value.path()).read_text())
        self.assertEqual(saved,record)
        self.assertEqual(self.info(), {'error': 'metadata capacity exceeded'})

    def test_canvas_respects_vim_subset_and_keeps_companion_draft_current(self):
        self.page.locator('#draft').fill('')
        self.page.locator('#prompt-mode').select_option('vim-full')
        canvas = self.page.locator('#canvas')
        canvas.focus()
        canvas.press('x')
        self.assertEqual(self.info()['prompt']['text'], '')
        self.assertEqual(self.page.locator('#error').inner_text(), '')
        canvas.press('q')
        self.assertIn('Unsupported Vim command', self.page.locator('#error').inner_text())
        canvas.press('i')
        canvas.press('A')
        canvas.press('B')
        canvas.press('Backspace')
        self.assertEqual(self.info()['prompt']['text'], 'A')
        self.assertEqual(self.page.locator('#draft').input_value(), 'A')
        canvas.press('Control+z')
        self.assertEqual(self.page.locator('#draft').input_value(), 'AB')
        canvas.press('Escape')
        canvas.press('h')
        self.assertEqual(self.info()['prompt']['text'], 'AB')
        self.assertEqual(self.info()['prompt']['caret'], 1)

    def test_canvas_modal_does_not_insert_into_invisible_prompt(self):
        self.page.locator('#draft').fill('accepted')
        canvas = self.page.locator('#canvas')
        canvas.focus()
        canvas.press('F1')
        before = self.info()['prompt']
        canvas.press('Q')
        self.assertEqual(self.info()['prompt'], before)
        canvas.press('Escape')
        canvas.press('End')
        canvas.press('Enter')
        self.assertEqual(self.info()['prompt']['text'], 'accepted\n')

    def test_real_browser_ime_preedit_is_not_committed_and_final_text_commits_once(self):
        draft = self.page.locator('#draft')
        draft.fill('base ')
        draft.press('End')
        before = self.info()
        session = self.page.context.new_cdp_session(self.page)
        try:
            session.send('Input.imeSetComposition', {'text': 'に', 'selectionStart': 1, 'selectionEnd': 1})
            self.assertEqual(draft.input_value(), 'base に')
            self.assertEqual(self.info()['prompt'], before['prompt'])
            session.send('Input.imeSetComposition', {'text': '日本', 'selectionStart': 2, 'selectionEnd': 2})
            self.assertEqual(self.info()['fieldCount'], before['fieldCount'])
            session.send('Input.insertText', {'text': '日本'})
            self.assertEqual(self.info()['prompt']['text'], 'base 日本')
            self.assertEqual(self.info()['prompt']['revision'], before['prompt']['revision'] + 1)
            self.assertEqual(self.info()['fieldCount'], before['fieldCount'] + 2)
        finally:
            session.detach()

    def test_preedit_control_shortcuts_cannot_move_accepted_document_caret(self):
        draft = self.page.locator('#draft')
        draft.fill('accepted ')
        draft.press('End')
        before = self.info()['prompt']
        session = self.page.context.new_cdp_session(self.page)
        try:
            session.send('Input.imeSetComposition', {'text': '仮', 'selectionStart': 1, 'selectionEnd': 1})
            for key in ['a', 'e']:
                draft.dispatch_event('keydown', {'key': key, 'ctrlKey': True, 'isComposing': True})
                self.assertEqual(self.info()['prompt'], before)
                self.assertEqual(draft.input_value(), 'accepted 仮')
            session.send('Input.imeSetComposition', {'text': '', 'selectionStart': 0, 'selectionEnd': 0})
            self.assertEqual(self.info()['prompt'], before)
        finally:
            session.detach()

    def test_preedit_survives_resize_and_other_input_target_cannot_edit_source(self):
        draft = self.page.locator('#draft')
        draft.fill('accepted ')
        draft.press('End')
        before = self.info()
        session = self.page.context.new_cdp_session(self.page)
        try:
            session.send('Input.imeSetComposition', {'text': '仮', 'selectionStart': 1, 'selectionEnd': 1})
            self.page.set_viewport_size({'width': 1000, 'height': 800})
            self.evaluate("document.getElementById('columns').value=72;document.getElementById('rows').value=28;document.getElementById('resize').click()")
            self.assertEqual(self.info()['prompt'], before['prompt'])
            self.assertEqual(draft.input_value(), 'accepted 仮')
            # A redirected target may lack the browser isComposing flag.
            self.page.locator('#canvas').dispatch_event('keydown', {'key': 'X', 'isComposing': False})
            self.assertEqual(self.info()['prompt'], before['prompt'])
            session.send('Input.insertText', {'text': '確'})
            after = self.info()
            self.assertEqual(after['prompt']['text'], 'accepted 確')
            self.assertEqual(after['prompt']['revision'], before['prompt']['revision'] + 1)
            self.assertEqual(after['fieldCount'], before['fieldCount'] + 1)
        finally:
            session.detach()

    def test_actual_focus_transfer_finishes_composition_without_duplicate_commit(self):
        draft = self.page.locator('#draft')
        draft.fill('accepted ')
        draft.press('End')
        before = self.info()
        session = self.page.context.new_cdp_session(self.page)
        try:
            session.send('Input.imeSetComposition', {'text': '確', 'selectionStart': 1, 'selectionEnd': 1})
            self.page.locator('#canvas').focus()
            after = self.info()
            self.assertEqual(after['prompt']['text'], 'accepted 確')
            self.assertEqual(after['prompt']['revision'], before['prompt']['revision'] + 1)
            self.assertEqual(after['fieldCount'], before['fieldCount'] + 1)
            self.page.locator('#canvas').press('X')
            self.assertEqual(self.info()['prompt']['text'], 'accepted 確X')
            self.assertEqual(draft.input_value(), 'accepted 確X')
        finally:
            session.detach()

    def test_ime_replacement_of_selected_source_commits_once(self):
        draft = self.page.locator('#draft')
        draft.fill('A旧B')
        self.evaluate("document.getElementById('draft').setSelectionRange(1,2)")
        before = self.info()
        session = self.page.context.new_cdp_session(self.page)
        try:
            session.send('Input.imeSetComposition', {'text': '仮', 'selectionStart': 1, 'selectionEnd': 1})
            self.assertEqual(self.info()['prompt'], before['prompt'])
            session.send('Input.insertText', {'text': '新'})
            after = self.info()
            self.assertEqual(after['prompt']['text'], 'A新B')
            self.assertEqual(after['prompt']['caret'], 2)
            self.assertEqual(after['prompt']['revision'], before['prompt']['revision'] + 1)
            self.assertEqual(after['fieldCount'], before['fieldCount'] + 1)
        finally:
            session.detach()

    def clipboard(self, kind, text=''):
        return self.evaluate("""([kind,text])=>{const data=new DataTransfer();data.setData('text/plain',text);document.getElementById('canvas').dispatchEvent(new ClipboardEvent(kind,{clipboardData:data,bubbles:true,cancelable:true}));return data.getData('text/plain');}""", [kind,text])

    def test_textarea_selection_updates_native_without_document_edit(self):
        self.page.locator('#draft').fill('A👩‍🔧éZ')
        before=self.info()
        self.evaluate("""()=>{const d=document.getElementById('draft');d.setSelectionRange(1,6,'backward');d.dispatchEvent(new Event('select'));}""")
        after=self.info()
        self.assertEqual((after['prompt']['anchor'],after['prompt']['caret']),(4,1))
        self.assertEqual(after['prompt']['revision'],before['prompt']['revision'])
        self.assertEqual(self.clipboard('copy'),'👩‍🔧')
        self.page.locator('#canvas').press('ArrowRight')
        self.assertEqual(self.evaluate("[document.getElementById('draft').selectionStart,document.getElementById('draft').selectionEnd]"),[6,6])

    def test_preedit_selection_is_not_native_selection(self):
        self.page.locator('#draft').fill('AB')
        before=self.info()
        self.evaluate("""()=>{const d=document.getElementById('draft');d.dispatchEvent(new CompositionEvent('compositionstart'));d.value='A未B';d.setSelectionRange(1,2);d.dispatchEvent(new Event('select'));}""")
        self.assertEqual(self.info(),before)

    def test_canvas_command_a_selects_all_native_source(self):
        self.page.locator('#draft').fill('é日本')
        self.page.locator('#canvas').press('Meta+a')
        p=self.info()['prompt'];self.assertEqual((p['anchor'],p['caret']),(0,4))
        self.clipboard('paste','X');self.assertEqual(self.info()['prompt']['text'],'X')

    def test_native_selection_copy_cut_and_undo(self):
        self.page.locator('#draft').fill('Aé日本Z')
        self.evaluate("nativeLab.scene.command({op:'select',anchor:1,caret:5,unit:'grapheme'})")
        before=self.info()
        self.assertEqual(self.clipboard('copy'),'é日本')
        self.assertEqual(self.info(),before)
        self.assertEqual(self.clipboard('cut'),'é日本')
        self.assertEqual(self.info()['prompt']['text'],'AZ')
        self.evaluate("nativeLab.scene.command({op:'key',key:'z',ctrl:true})")
        self.assertEqual(self.info()['prompt']['text'],'Aé日本Z')

    def test_canvas_clipboard_paste_is_one_atomic_accepted_input(self):
        self.page.locator('#draft').fill('AB')
        self.evaluate("nativeLab.scene.command({op:'key',key:'a',ctrl:true})")
        before = self.info()
        self.clipboard('paste', 'é\n日本')
        after = self.info()
        self.assertEqual(after['prompt']['text'], 'é\n日本AB')
        self.assertEqual(after['prompt']['caret'], 5)
        self.assertEqual(after['prompt']['revision'], before['prompt']['revision'] + 1)
        self.assertEqual(after['fieldCount'], before['fieldCount'] + 4)
        self.assertEqual(self.page.locator('#draft').input_value(), 'é\n日本AB')
        self.evaluate('window.copyBefore=nativeLab.scene.snapshot()')
        self.assertEqual(self.clipboard('copy'), 'é\n日本AB')
        self.assertTrue(self.evaluate('nativeLab.scene.snapshot().every((v,i)=>v===copyBefore[i])'))

    def test_canvas_paste_keeps_modal_ownership_and_accepts_large_unicode(self):
        self.page.locator('#draft').fill('accepted')
        self.page.locator('#canvas').press('F1')
        before = self.info()['prompt']
        self.clipboard('paste', 'hidden')
        self.assertEqual(self.info()['prompt'], before)
        self.page.locator('#canvas').press('Escape')
        before = self.info()['prompt']
        self.evaluate('window.pasteBefore=nativeLab.scene.snapshot()')
        large = 'A界é🙂' * 14001
        self.assertGreater(len(large), 65536)
        self.clipboard('paste', large)
        after = self.info()['prompt']
        expected = before['text'][:before['caret']] + large + before['text'][before['caret']:]
        self.assertTrue(after['text'] == expected, 'large Unicode paste source differs')
        self.assertEqual(after['caret'], before['caret'] + len(large))
        self.assertEqual(after['revision'], before['revision'] + 1)
        self.assertTrue(self.page.locator('#draft').input_value() == expected)
        self.assertTrue(self.evaluate("expected=>nativeLab.scene.textRunSource(0,0)===expected", expected))
        self.evaluate('window.pasteAccepted=nativeLab.scene.snapshot();window.pasteFrame=nativeLab.scene.render().bytes.slice();nativeLab.draw()')
        self.assertTrue(self.evaluate('nativeLab.scene.snapshot().every((v,i)=>v===pasteAccepted[i])'))
        self.assertTrue(self.evaluate('nativeLab.scene.render().bytes.every((v,i)=>v===pasteFrame[i])'))
        self.page.locator('#canvas').press('Control+z')
        undone = self.info()['prompt']
        self.assertEqual((undone['text'],undone['caret']), (before['text'],before['caret']))
        self.page.locator('#canvas').press('Control+Shift+z')
        self.assertTrue(self.info()['prompt']['text'] == expected, 'one redo must restore the whole paste')
        self.evaluate('nativeLab.scene.restore(pasteAccepted);nativeLab.draw()')
        self.assertTrue(self.evaluate('nativeLab.scene.snapshot().every((v,i)=>v===pasteAccepted[i])'))
        self.assertTrue(self.evaluate('nativeLab.scene.render().bytes.every((v,i)=>v===pasteFrame[i])'))
        self.assertTrue(self.info()['prompt']['text'] == expected)
        self.assertTrue(self.page.locator('#draft').input_value() == expected)

    def test_canvas_paste_respects_vim_insert_ownership(self):
        self.page.locator('#draft').fill('AB')
        self.page.locator('#prompt-mode').select_option('vim-full')
        before = self.info()['prompt']
        self.clipboard('paste', 'X')
        self.assertEqual(self.info()['prompt'], before)
        self.page.locator('#canvas').press('i')
        self.clipboard('paste', 'X')
        self.assertEqual(self.info()['prompt']['text'], 'ABX')

    def test_canvas_clipboard_cannot_steal_active_preedit(self):
        draft = self.page.locator('#draft')
        draft.fill('accepted ')
        draft.press('End')
        before = self.info()['prompt']
        session = self.page.context.new_cdp_session(self.page)
        try:
            session.send('Input.imeSetComposition', {'text': '仮', 'selectionStart': 1, 'selectionEnd': 1})
            self.clipboard('paste', 'X')
            self.assertEqual(self.info()['prompt'], before)
            self.assertEqual(draft.input_value(), 'accepted 仮')
            session.send('Input.insertText', {'text': '確'})
            self.assertEqual(self.info()['prompt']['text'], 'accepted 確')
        finally:
            session.detach()

    def test_paste_uses_reader_target_ownership_during_close_fade(self):
        self.page.locator('#draft').fill('accepted')
        self.evaluate("()=>{nativeLab.scene.command({op:'window',id:77,text:'reader'});nativeLab.scene.command({op:'window-action',id:77,action:'read'});nativeLab.draw();}")
        self.assertEqual(self.info()['inputOwner'], 'reader')
        before = self.info()['prompt']
        self.clipboard('paste', 'X')
        self.assertEqual(self.info()['prompt'], before)
        self.evaluate("nativeLab.scene.command({op:'window-action',id:77,action:'close',durationMs:1000})")
        self.assertEqual(self.info()['inputOwner'], 'prompt')
        self.assertGreater(next(w for w in self.info()['windows'] if w['id'] == 77)['visible'], 0)
        self.clipboard('paste', 'X')
        self.assertEqual(self.info()['prompt']['text'], 'acceptedX')

    def test_cancelled_ime_composition_preserves_accepted_source_and_snapshot(self):
        draft = self.page.locator('#draft')
        draft.fill('accepted 🙂')
        draft.press('End')
        self.evaluate('window.imeSnapshotBefore = nativeLab.scene.snapshot()')
        session = self.page.context.new_cdp_session(self.page)
        try:
            session.send('Input.imeSetComposition', {'text': '仮', 'selectionStart': 1, 'selectionEnd': 1})
            session.send('Input.imeSetComposition', {'text': '', 'selectionStart': 0, 'selectionEnd': 0})
            self.assertEqual(draft.input_value(), 'accepted 🙂')
            self.assertTrue(self.evaluate('(()=>{const current=nativeLab.scene.snapshot();return current.length===imeSnapshotBefore.length&&current.every((value,index)=>value===imeSnapshotBefore[index])})()'))
        finally:
            session.detach()

    def test_reduced_motion_control_survives_scene_changes(self):
        control = self.page.locator('#reduced-motion')
        control.check()
        self.assertTrue(self.info()['accessibility']['reducedMotion'])
        self.assertTrue(self.info()['clock']['paused'])
        self.evaluate("nativeLab.load(nativeLab.recipes.find(r=>r.id==='autumn'));nativeLab.draw()")
        self.assertTrue(control.is_checked())
        self.assertTrue(self.info()['accessibility']['reducedMotion'])
        self.assertTrue(self.info()['clock']['paused'])
        self.page.locator('#draft').fill('Immediate while reduced')
        self.assertEqual(self.info()['prompt']['text'], 'Immediate while reduced')

    def test_system_reduced_motion_is_honored_on_initial_load(self):
        page = self.browser.new_page(reduced_motion='reduce')
        try:
            page.set_content(HTML.read_text())
            page.wait_for_function('window.nativeLab !== undefined', timeout=30000)
            info = page.evaluate('nativeLab.scene.info()')
            self.assertTrue(info['accessibility']['reducedMotion'])
            self.assertTrue(info['clock']['paused'])
        finally:
            page.close()

    def test_visible_keyboard_recovery_list_contains_every_retained_window(self):
        self.evaluate("()=>{for(let id=1;id<=12;id++){nativeLab.scene.command({op:'window',id,title:'Window '+id,text:'Retained '+id,position:[0,0,16000]});nativeLab.scene.command({op:'window-action',id,action:'close',durationMs:0});}nativeLab.draw();}")
        picker = self.page.locator('#recovery-window')
        self.assertEqual(picker.locator('option').count(), 12)
        picker.select_option('12')
        button = self.page.locator('#recovery-open')
        button.focus()
        button.press('Enter')
        self.assertEqual(self.info()['selectedWindow'], 12)
        self.assertTrue(self.info()['windows'][-1]['reader'])
        self.page.locator('#recovery-next').press('Enter')
        self.assertEqual(self.info()['selectedWindow'], 1)
        self.page.locator('#reader-exit').press('Enter')
        self.assertFalse(self.info()['windows'][0]['reader'])

    def test_read_all_contains_hidden_transition_action_and_selected_node_sources(self):
        self.evaluate("()=>{nativeLab.scene.command({op:'text',id:7,text:'Hidden é 界 🙂 אבג <b>source</b>',phase:'hide'});nativeLab.scene.command({op:'node',id:7,label:'Chosen node',kind:'ApprovalRecord',status:'Blocked',detail:'Complete reason'});nativeLab.scene.command({op:'select',id:7});nativeLab.scene.command({op:'status',id:700,text:'Approval needed',important:true,durationMs:0,actions:[{id:3,label:'Approve readable request',event:'/app/approve'}]});nativeLab.draw();}")
        self.page.locator('#read-all').click()
        self.assertEqual(self.evaluate('document.activeElement.id'), 'readable')
        source = self.page.locator('#readable').input_value()
        for text in ['Hidden é 界 🙂 אבג <b>source</b>', 'Chosen node', 'ApprovalRecord', 'Complete reason', 'Approval needed', 'Approve readable request']:
            self.assertIn(text, source)
        self.assertIn('Chosen node', self.page.locator('#selection-summary').inner_text())
        self.assertEqual(self.page.locator('#semantic-records b').count(), 0)

    def test_aggregate_metadata_refusal_is_visible_and_checkpoint_reader_stay_available(self):
        self.evaluate("""()=>{
            nativeLab.scene.command({op:'reset'});nativeLab.hold();
            for(let id=1;id<=24;id++)nativeLab.scene.command({op:'text',id,text:'🙂'.repeat(2048)});
            for(let id=1;id<=12;id++)nativeLab.scene.command({op:'window',id,title:'Retained '+id,text:'🙂'.repeat(2048),position:[0,0,16000]});
            nativeLab.scene.command({op:'draft',text:'界'.repeat(250001),emitWeather:false});
            window.capacitySnapshot = nativeLab.scene.snapshot();
            window.capacityFrame = nativeLab.scene.render().bytes.slice();
            nativeLab.draw();
        }""")
        self.assertGreater(self.evaluate('''()=>{const s=nativeLab.scene;
            const status=s.exports.nrInfoPage(s.context,0,0,0,s.particleBuffer,4);
            if(status!==1)throw Error('Metadata size probe failed');
            return new Uint32Array(s.exports.memory.buffer,s.particleBuffer,4)[0];}'''), 1048576)
        self.assertIn('metadata capacity exceeded', self.page.locator('#error').inner_text())
        self.assertEqual(json.loads(self.page.locator('#metadata').text_content()),
                         {'error': 'metadata capacity exceeded'})
        self.assertEqual(self.page.locator('#readable').get_attribute('aria-invalid'), 'true')
        self.assertIn('checkpoint', self.page.locator('#readable').input_value())
        self.assertEqual(self.page.locator('#semantic-records button').count(), 0)
        self.assertTrue(self.evaluate('(()=>{const current=nativeLab.scene.snapshot();return current.length===capacitySnapshot.length&&current.every((v,i)=>v===capacitySnapshot[i])})()'))
        self.assertTrue(self.evaluate('nativeLab.scene.render().bytes.every((v,i)=>v===capacityFrame[i])'))
        self.page.locator('#save').evaluate("element=>{element.closest('details').open=true}")
        with self.page.expect_download() as download:
            self.page.locator('#save').click()
        self.assertEqual(download.value.suggested_filename, 'nocturne-native.nrstate')
        self.assertEqual(Path(download.value.path()).stat().st_size,
                         self.evaluate('capacitySnapshot.length'))
        self.page.locator('#recovery-next').click()
        self.assertTrue(self.evaluate('Array.from(nativeView.frame.cells).some((v,i)=>i%4===3&&v===0x20000001)'))
        self.evaluate("nativeLab.scene.command({op:'clear',scope:'text'});nativeLab.draw()")
        self.assertNotIn('error', self.info())
        self.assertTrue(self.info()['prompt']['text']=='界'*250001)
        self.assertNotEqual(self.page.locator('#readable').get_attribute('aria-invalid'), 'true')
        self.assertIn('Retained 12', self.page.locator('#readable').input_value())
        self.page.locator('#restore').click()
        self.assertTrue(self.evaluate('(()=>{const current=nativeLab.scene.snapshot();return current.length===capacitySnapshot.length&&current.every((v,i)=>v===capacitySnapshot[i])})()'))
        self.assertTrue(self.evaluate('nativeLab.scene.render().bytes.every((v,i)=>v===capacityFrame[i])'))
        self.assertIn('metadata capacity exceeded', self.page.locator('#error').inner_text())

    def test_dom_notification_action_has_keyboard_access_and_only_records_intention(self):
        self.load('notifications')
        action = self.page.locator('#semantic-records button[data-message-id="40"]').first
        action.focus()
        self.evaluate('nativeLab.draw();nativeLab.draw();nativeLab.draw()')
        self.assertEqual(self.evaluate('document.activeElement.dataset.messageId'), '40')
        action.press('Enter')
        info = self.info()
        self.assertEqual(len(info['intents']), 1)
        self.assertEqual(info['intents'][0]['messageId'], 40)
        self.assertEqual(info['intents'][0]['event'], '/build/inspect')
        self.assertTrue(action.is_disabled())
        self.assertEqual(self.evaluate('document.activeElement.dataset.messageId'), '40')
        self.assertTrue(any(m['id'] == 40 and m['text'] for m in info['messages']))

    def test_canvas_has_a_named_escape_to_dom_and_error_is_announced(self):
        canvas = self.page.locator('#canvas')
        self.assertTrue(canvas.get_attribute('aria-describedby'))
        canvas.focus()
        canvas.press('Tab')
        self.assertNotEqual(self.evaluate('document.activeElement.id'), 'canvas')
        self.page.locator('#config').evaluate("element=>{element.closest('details').open=true}")
        self.page.locator('#config').fill('{"op":"invalid-accessibility-operation"}')
        self.page.locator('#execute').click()
        error = self.page.locator('#error')
        self.assertEqual(error.get_attribute('role'), 'alert')
        self.assertTrue(error.inner_text())
        self.assertEqual(error.get_attribute('aria-atomic'), 'true')

    def test_canvas_scalar_fallback_is_visible_and_cannot_paint_neighbor_cells(self):
        results = self.evaluate("""()=>{
            nativeLab.scene.command({op:'reset'});
            nativeLab.hold();
            nativeLab.scene.command({op:'environment',style:'solid',background:0x102030,stars:0});
            nativeLab.scene.command({op:'prompt',active:false});
            const canvas=document.getElementById('canvas'),context=canvas.getContext('2d');
            function patch(text){
                nativeLab.scene.command({op:'widget',id:99,kind:'text',text,x:10,y:5,width:1,height:1,padding:0,border:'none',alpha:1});
                const before=nativeLab.scene.snapshot();nativeLab.draw();
                const after=nativeLab.scene.snapshot();
                return {cell:Array.from(context.getImageData(100,100,10,20).data),
                        outer:Array.from(context.getImageData(90,100,40,20).data),
                        source:nativeLab.scene.info().widgets.find(w=>w.id===99).text,
                        pure:before.every((v,i)=>v===after[i])};
            }
            const empty=patch(' '),replacement=patch('\ufffd'),rows=[];
            for(const glyph of ['\\u0301','\\u200d','\\u202e','\\ufe0f']){
                const got=patch(glyph);rows.push({glyph,source:got.source,pure:got.pure,
                    replacement:got.cell.every((v,i)=>v===replacement.cell[i])});
            }
            for(const glyph of ['界','🙂']){
                const got=patch(glyph),outside=[];
                for(let row=0;row<20;row++)for(let x=0;x<40;x++)if(x<10||x>=20)
                    for(let channel=0;channel<4;channel++)outside.push((row*40+x)*4+channel);
                rows.push({glyph,source:got.source,pure:got.pure,
                    neighborsUntouched:outside.every(i=>got.outer[i]===empty.outer[i])});
            }
            return rows;
        }""")
        for row in results:
            with self.subTest(glyph=repr(row['glyph'])):
                self.assertEqual(row['source'], row['glyph'])
                self.assertTrue(row['pure'])
                if 'replacement' in row:
                    self.assertTrue(row['replacement'], 'Unsupported scalar must display visible U+FFFD')
                if 'neighborsUntouched' in row:
                    self.assertTrue(row['neighborsUntouched'], 'Scalar ink escaped its owned canvas cell')


class ReceiptResult(unittest.TextTestResult):
    def __init__(self, *arguments, **keywords):
        super().__init__(*arguments, **keywords)
        self.records = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.records.append({'test': test.id(), 'status': 'PASS'})

    def addFailure(self, test, error):
        super().addFailure(test, error)
        self.records.append({'test': test.id(), 'status': 'FAIL', 'reason': self._exc_info_to_string(error, test)})

    def addError(self, test, error):
        super().addError(test, error)
        self.records.append({'test': test.id(), 'status': 'ERROR', 'reason': self._exc_info_to_string(error, test)})

    def addSubTest(self, test, subtest, error):
        super().addSubTest(test, subtest, error)
        if error is not None:
            self.records.append({'test': subtest.id(), 'status': 'FAIL',
                                 'reason': self._exc_info_to_string(error, subtest)})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt', type=Path, default=ROOT / 'evidence/browser-accessibility.json')
    arguments = parser.parse_args()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(BrowserAccessibilityTests)
    result = unittest.TextTestRunner(verbosity=2, resultclass=ReceiptResult).run(suite)
    receipt = {'schema': 'nocturne.browser-accessibility.v1',
               'baselineCommit': 'c7deb564c70b3f778d538fbed115d71ad49879e2',
               'scope': 'Exact compiled gallery in Chromium. Actual browser keyboard, focus, DOM, native WASM and CDP IME composition. No operating-system IME or assistive-technology acceptance.',
               'platform': platform.platform(), 'python': sys.version,
               'browser': getattr(BrowserAccessibilityTests, 'browserVersion', None),
               'htmlSha256': hashlib.sha256(HTML.read_bytes()).hexdigest(),
               'scriptSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'argv': sys.argv, 'cwd': str(Path.cwd()),
               'environment': {key: os.environ.get(key) for key in ['CHROMIUM', 'PYTHONPATH']},
               'testsRun': result.testsRun, 'checks': result.records,
               'passed': result.wasSuccessful() and result.testsRun == suite.countTestCases()}
    # unittest consumes its suite while running; the explicit class count is stable.
    receipt['passed'] = result.wasSuccessful() and result.testsRun == len(unittest.defaultTestLoader.getTestCaseNames(BrowserAccessibilityTests))
    arguments.receipt.parent.mkdir(parents=True, exist_ok=True)
    arguments.receipt.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'passed': receipt['passed'], 'testsRun': result.testsRun, 'receipt': str(arguments.receipt)}))
    return 0 if receipt['passed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
