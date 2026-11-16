"""Real browser acceptance for workshop composition ownership and validation."""
from pathlib import Path
import argparse
import json
import hashlib
import traceback
from playwright.sync_api import sync_playwright

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--gallery',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    metadata=json.loads((Path(__file__).resolve().parents[1]/'web/workshop_fields.json').read_text())
    result={'passed':False,'runtime':'actual Chromium','checks':[],'pageErrors':[]}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True)
            page=browser.new_page();page.on('pageerror',lambda e:result['pageErrors'].append(str(e)))
            page.set_content(a.gallery.read_text());page.wait_for_function('window.nativeLab !== undefined')
            page.evaluate('nativeLab.hold()')
            page.locator('#workshop-panel').evaluate('(e)=>e.open=true')
            contract=Path(__file__).resolve().parents[1]/'bindings/typescript/contracts.ts'
            assert metadata['sourceSha256']==hashlib.sha256(contract.read_bytes()).hexdigest(), 'Workshop metadata differs from current NativeCommand'
            embedded,_=json.JSONDecoder().raw_decode(a.gallery.read_text().split('const workshopMetadata=',1)[1])
            assert embedded==metadata, 'Embedded workshop metadata differs from source inventory'
            actual=page.locator('#workshop-operation option').evaluate_all('(options)=>options.map(option=>option.value)')
            assert actual==metadata['operations'], 'Workshop operation identities differ from current inventory'
            result['checks'].append('All current public operations and parameter metadata exposed')
            for operation in metadata['operations']:
                page.get_by_label('Command operation',exact=True).select_option(operation)
                expected=[row['field'] for row in metadata['fields'] if row['op']==operation]
                actual=page.locator('#workshop-fields input').evaluate_all('(inputs)=>inputs.map(input=>input.dataset.workshopField)')
                assert actual==expected, 'Workshop parameter identities differ for '+operation
            result['checks'].append('Every operation exposes all its indexed parameter controls')
            loading=page.evaluate('''async()=>{
              const button=document.getElementById('workshop-validate');
              const pending=button.onclick();
              const busy=button.disabled&&button.getAttribute('aria-busy')==='true';
              await pending;
              return {busy,enabled:!button.disabled,status:document.getElementById('workshop-status').textContent};
            }''')
            assert loading['busy'] and loading['enabled'] and 'Composition valid' in loading['status']
            result['checks'].append('Empty composition validates with stable busy/success states')
            stale=page.evaluate('''async()=>{
              const editor=document.getElementById('workshop-document'),preview=document.getElementById('workshop-preview');
              const previous=preview.textContent;
              editor.value=JSON.stringify({schema:'nocturne.composition.v1',seed:2030,commands:[{op:'input',text:'Old pending draft'}]});
              const pending=document.getElementById('workshop-validate').onclick();
              editor.value=JSON.stringify({schema:'nocturne.composition.v1',seed:2030,commands:[]});
              editor.dispatchEvent(new Event('input',{bubbles:true}));await pending;
              return {unchanged:preview.textContent===previous,status:document.getElementById('workshop-status').textContent};
            }''')
            assert stale['unchanged'] and 'Document changed' in stale['status']
            result['checks'].append('Editing during actual WASM validation rejects stale preview and clears pending feedback')
            page.get_by_label('Command operation',exact=True).select_option('input')
            page.locator('[data-workshop-field="text"]').fill('"Workshop draft"')
            page.get_by_role('button',name='Add command',exact=True).click()
            page.evaluate('()=>{window.workshopSourceSnapshot=nativeLab.scene.snapshot();}')
            page.get_by_role('button',name='Validate composition',exact=True).click()
            page.wait_for_function("document.getElementById('workshop-status').textContent.includes('Composition valid')")
            assert page.evaluate('()=>{const now=nativeLab.scene.snapshot(),before=window.workshopSourceSnapshot;return now.length===before.length&&now.every((value,index)=>value===before[index]);}')
            result['checks'].append('Independent actual WASM preview preserves active application')
            with page.expect_download() as download:
                page.get_by_role('button',name='Export composition',exact=True).click()
            exported=a.output/'composition.json';download.value.save_as(str(exported))
            original=json.loads(exported.read_text())
            page.locator('#workshop-file').set_input_files(str(exported))
            page.wait_for_function("document.getElementById('workshop-status').textContent.includes('Composition imported')")
            assert json.loads(page.get_by_label('Composition document',exact=True).input_value())==original
            result['checks'].append('Browser export/import retains exact seeded command document')
            page.get_by_role('button',name='Apply composition',exact=True).click()
            assert page.evaluate('nativeLab.scene.info().prompt.text').endswith('Workshop draft')
            result['checks'].append('Native application receives authored input')
            page.evaluate('()=>{window.workshopSourceSnapshot=nativeLab.scene.snapshot();}')
            invalid={'schema':'nocturne.composition.v1','seed':2030,'commands':[{'op':'input','text':'rollback'},{'op':'unknown-workshop-command'}]}
            page.get_by_label('Composition document',exact=True).fill(json.dumps(invalid))
            page.get_by_role('button',name='Apply composition',exact=True).click()
            assert page.evaluate('()=>{const now=nativeLab.scene.snapshot(),before=window.workshopSourceSnapshot;return now.length===before.length&&now.every((value,index)=>value===before[index]);}')
            assert json.loads(page.get_by_label('Composition document',exact=True).input_value())==invalid
            assert page.get_by_label('Composition document',exact=True).get_attribute('aria-invalid')=='true'
            result['checks'].append('Native batch rejection preserves application and entered document')
            page.set_viewport_size({'width':390,'height':844})
            page.get_by_label('Command operation',exact=True).focus()
            page.keyboard.press('ArrowDown');page.keyboard.press('Tab')
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path=str(a.output/'workshop-narrow.png'),full_page=True)
            result['checks'].append('Keyboard controls and narrow viewport')
            page.get_by_label('Command operation',exact=True).select_option('input')
            field=page.locator('[data-workshop-field="text"]');field.fill('not-json')
            editor=page.get_by_label('Composition document',exact=True).input_value()
            page.get_by_role('button',name='Add command',exact=True).click()
            assert field.get_attribute('aria-invalid')=='true'
            assert 'workshop-status' in field.get_attribute('aria-describedby').split()
            assert field.evaluate('(e)=>document.activeElement===e')
            assert page.get_by_label('Composition document',exact=True).input_value()==editor
            result['checks'].append('Invalid parameter retains document and focuses described field error')
            page.locator('#workshop-document').fill(json.dumps({'schema':'nocturne.composition.v1','seed':2030,'commands':[]}))
            page.get_by_label('Command operation',exact=True).select_option('flow')
            for field,value in {'id':1,'flux':2,'stages[].name':['channel','sheet'],'stages[].delayUs':[250000,500000],'stages[].tailUs':[0,0]}.items():
                page.locator('[data-workshop-field="'+field+'"]').fill(json.dumps(value))
            page.get_by_role('button',name='Add command',exact=True).click()
            flow=json.loads(page.locator('#workshop-document').input_value())['commands'][0]
            assert flow['stages']==[{'name':'channel','delayUs':250000,'tailUs':0},{'name':'sheet','delayUs':500000,'tailUs':0}]
            assert 'stages[]' not in flow
            page.evaluate('window.arrayFieldBefore=nativeLab.scene.snapshot()')
            page.get_by_role('button',name='Validate composition',exact=True).click()
            page.wait_for_function("document.getElementById('workshop-status').textContent.includes('Composition valid')")
            assert page.evaluate('nativeLab.scene.snapshot().every((value,index)=>value===window.arrayFieldBefore[index])')
            result['checks'].append('Array field controls construct actual native flow stages and independent preview preserves application')
            preserved=page.locator('#workshop-document').input_value();arrayField=page.locator('[data-workshop-field="stages[].name"]')
            arrayField.fill('"not-an-array"');page.get_by_role('button',name='Add command',exact=True).click()
            assert page.locator('#workshop-document').input_value()==preserved
            assert arrayField.get_attribute('aria-invalid')=='true'
            assert arrayField.evaluate('(element)=>element===document.activeElement')
            result['checks'].append('Invalid array value rejects without changing document and retains described field focus')
            browser.close()
        assert not result['pageErrors'];result['passed']=True
    except Exception as error:
        result['error']=type(error).__name__+': '+str(error);result['traceback']=traceback.format_exc();print(result['traceback'])
    (a.output/'RESULTS.json').write_text(json.dumps(result,indent=2)+'\n')
    return 0 if result['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
