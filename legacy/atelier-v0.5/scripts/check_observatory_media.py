"""Verify opt-in capture lifecycle with a synthetic browser audio stream.
This tests software plumbing, NOT microphone hardware or system-loopback support.
"""
import json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
checks=[]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),headless=True,args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
 page=b.new_page(viewport={'width':1400,'height':1000});page.set_content((ROOT/'Nocturne-Observatory.html').read_text());page.wait_for_function('window.observatoryApp');page.evaluate('observatoryApp.setAuto(false)')
 page.evaluate('''async()=>{const context=new AudioContext(),osc=context.createOscillator(),gain=context.createGain(),destination=context.createMediaStreamDestination();gain.gain.value=.25;osc.frequency.value=440;osc.connect(gain).connect(destination);osc.start();await context.resume();window.fixture={context,stream:destination.stream,calls:0,empty:null};Object.defineProperty(navigator,'mediaDevices',{configurable:true,value:{getUserMedia:async()=>{fixture.calls++;return fixture.stream},getDisplayMedia:async()=>{fixture.calls++;fixture.empty=new MediaStream();return fixture.empty}}});}''')
 assert page.evaluate('fixture.calls')==0;checks.append('no capture API called on initialization')
 page.locator('#sensorsPanel').evaluate('(e)=>e.open=true');page.locator('#microphone').click();page.wait_for_function("observatoryApp.model.bus.samples.has('audio.input.rms')");rms=page.evaluate("observatoryApp.model.bus.samples.get('audio.input.rms').value");assert .05<rms<.4,rms;checks.append('explicit microphone action processes known synthetic sine stream')
 assert page.evaluate('observatoryApp.model.waveform.some(v=>Math.abs(v)>.05)');checks.append('analyser waveform reaches actual scope model')
 page.locator('#stopAudio').click();page.wait_for_function("fixture.stream.getTracks().every(t=>t.readyState==='ended')");checks.append('Stop closes every source track')
 page.locator('#sharedAudio').click();page.wait_for_function("document.getElementById('error').textContent.includes('no audio track')");checks.append('missing shared-output audio is reported, not fabricated')
 page.evaluate('fixture.context.close()');b.close()
report={'status':'PASS','count':len(checks),'checks':checks,'fixture':'Web Audio oscillator, no physical device','physicalAudioTested':False};(ROOT/'dist/observatory/media-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
