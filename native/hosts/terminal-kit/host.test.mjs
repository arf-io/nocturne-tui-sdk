import './capacity.test.mjs';
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import kit from 'terminal-kit';
import {NativeScene} from '../../bindings/typescript/native_scene.mjs';
import {blitFrame,createPasteDecoder,mouseCommand} from './host.mjs';

test('real ScreenBufferHD retains glyph/RGB/profile and owned bytes',()=>{
 const bytes=new Uint8Array(3*16),v=new DataView(bytes.buffer);
 [[0x2801,0xabcdef,0x123456,99],[0x754c,0x012345,0x667788,55],[0x1b,0xffffff,0,1]].forEach((c,i)=>c.forEach((x,j)=>v.setUint32(i*16+j*4,x,true)));
 const before=bytes.slice(),b=new kit.ScreenBufferHD({width:3,height:1});
 blitFrame(b,{width:3,height:1,bytes});
 assert.equal(b.get({x:0,y:0}).char,'⠁');assert.equal(b.get({x:1,y:0}).char,'�');assert.equal(b.get({x:2,y:0}).char,'�');
 assert.equal(b.get({x:0,y:0}).attr.color.r,0xab);assert.equal(b.get({x:0,y:0}).attr.bgColor.b,0x56);assert.deepEqual(bytes,before);
});
test('actual native render/blit does not mutate a snapshot',async()=>{
 const s=await NativeScene.create(fs.readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
 try{s.command({op:'resize',width:80,height:24});s.command({op:'input',text:'kept é界'});const before=s.snapshot();const f=s.render();blitFrame(new kit.ScreenBufferHD({width:80,height:24}),f);assert.deepEqual(s.snapshot(),before);assert.equal(s.info().prompt.text,'kept é界');}finally{s.close()}
});
test('fragmented bracketed paste keeps Unicode and command-looking bytes as data',()=>{
 const normal=[],pastes=[];const p=createPasteDecoder(b=>normal.push(Buffer.from(b)),s=>pastes.push(s));
 for(const b of Buffer.from('abc\x1b[200~é\x11\t"\\\x1b[201~xyz'))p.feed(Buffer.from([b]));
 p.flush();p.close();assert.equal(Buffer.concat(normal).toString(),'abcxyz');assert.deepEqual(pastes,['é\x11\t"\\']);
});
test('plain Escape is flushed, unterminated paste rejects and large paste remains data',()=>{
 const a=[];let p=createPasteDecoder(b=>a.push(Buffer.from(b)),()=>{});p.feed(Buffer.from('\x1b'));p.flush();assert.equal(Buffer.concat(a).toString(),'\x1b');p.close();
 p=createPasteDecoder(()=>{},()=>{});p.feed(Buffer.from('\x1b[200~pending'));assert.throws(()=>p.flush(),/unterminated/);p.close();
 const large=[];p=createPasteDecoder(()=>assert.fail('paste leaked'),text=>large.push(text));p.feed(Buffer.from('\x1b[200~'+'x'.repeat(65537)));p.feed(Buffer.from('\x1b[201~'));assert.deepEqual(large,['x'.repeat(65537)]);p.close();
});
test('Terminal Kit left/right drag names preserve native move phase',()=>{
 assert.deepEqual(mouseCommand('MOUSE_DRAG',{x:4,y:8,left:true,code:32}),{op:'pointer',x:3,y:7,phase:'move',button:0,shift:false,alt:false});
 assert.equal(mouseCommand('MOUSE_DRAG',{x:4,y:8,right:true,code:34}).button,2);
 assert.equal(mouseCommand('MOUSE_RIGHT_BUTTON_RELEASED',{x:4,y:8}).phase,'up');
 assert.equal(mouseCommand('MOUSE_WHEEL_DOWN',{x:4,y:8}).delta,-1);
});
test('paste command-looking C0 reaches native validation, which rejects atomically',async()=>{
 const s=await NativeScene.create(fs.readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
 try{
  s.command({op:'input',text:'retained'});const before=s.snapshot();
  const p=createPasteDecoder(()=>assert.fail('paste became a keyboard shortcut'),text=>s.command({op:'input',text}));
  assert.throws(()=>p.feed(Buffer.from('\x1b[200~\x11\x1b[201~')),/State invariant rejected/);
  assert.deepEqual(s.snapshot(),before);assert.equal(s.info().prompt.text,'retained');p.close();
 }finally{s.close()}
});


test('C/WASM StatusArea scalar cells, source, snapshot and rendered action survive ScreenBufferHD', async()=>{
 const message='Aé界e\u0301Z',label='Review é',event='/status/scalar/review';
 const hitId=(0x63000000 | (37<<2))>>>0; // slot zero, not public action ID 17
 const s=await NativeScene.create(fs.readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
 try{
  for(const command of [
   {op:'resize',width:48,height:16}, {op:'environment',stars:0},
   {op:'prompt',active:false}, {op:'pause',paused:true},
   {op:'area',id:1,x:4,y:3,width:30,height:6,border:'none',padding:0,layout:'direct',alpha:1},
   {op:'status',id:37,area:1,text:message,x:0,y:0,mode:'pop',durationMs:0,
    actions:[{id:17,label,event,value:7}]},
  ]) s.command(command);
  const record=()=>{const messages=s.info().messages;assert.equal(messages.length,1);assert.equal(messages[0].id,37);return messages[0]};
  const source=record(),snapshot=s.snapshot();
  assert.equal(source.text,message);assert.equal(source.actions[0].label,label);
  let original;
  for(const phase of ['original','restored']){
   assert.deepEqual(s.snapshot(),snapshot);assert.deepEqual(record(),source);
   const f=s.render(); // All bytes originate in the rebuilt C/WASM notification.
   assert.deepEqual([f.width,f.height,f.bytes.length],[48,16,48*16*16]);
   original??=f.bytes.slice();assert.deepEqual(f.bytes,original);
   const view=new DataView(f.bytes.buffer,f.bytes.byteOffset,f.bytes.byteLength);
   const word=(x,y,field)=>view.getUint32((y*48+x)*16+field*4,true);
   [0x41,0xe9,0x754c,0x65,0x301,0x5a].forEach((g,i)=>{
    assert.equal(word(4+i,3,0),g,`${phase}: native scalar cell ${i}`);
    assert.equal(word(4+i,3,3),0);
   });
   Array.from(label).forEach((g,i)=>assert.equal(word(5+i,5,0),g.codePointAt(0)));
   const hits=[],expected=[];
   for(let y=0;y<16;y++)for(let x=0;x<48;x++)if(word(x,y,3)===hitId)hits.push([x,y]);
   for(let y=4;y<7;y++)for(let x=4;x<16;x++)expected.push([x,y]);
   assert.deepEqual(hits,expected,`${phase}: semantic action cells shifted`);
   const buffer=new kit.ScreenBufferHD({width:48,height:16});
   for(let repeat=0;repeat<2;repeat++){
    blitFrame(buffer,f);
    ['A','é','\uFFFD','e','\uFFFD','Z'].forEach((g,i)=>
     assert.equal(buffer.get({x:4+i,y:3}).char,g,`${phase}: display cell ${i}`));
    for(const x of [3,10])assert.equal(buffer.get({x,y:3}).char,String.fromCodePoint(word(x,3,0)),`neighbor ${x} shifted`);
    Array.from(label).forEach((g,i)=>assert.equal(buffer.get({x:5+i,y:5}).char,g,'action label shifted'));
    assert.deepEqual(f.bytes,original);assert.deepEqual(s.snapshot(),snapshot);assert.deepEqual(record(),source);
   }
   assert.deepEqual(s.render().bytes,original);assert.deepEqual(s.snapshot(),snapshot);
   // Feed Terminal Kit coordinates translated from an actual native hit cell.
   const [x,y]=hits.find(([x,y])=>word(x,y,0)==='é'.codePointAt(0));
   s.command(mouseCommand('MOUSE_LEFT_BUTTON_PRESSED',{x:x+1,y:y+1}));
   s.command(mouseCommand('MOUSE_LEFT_BUTTON_RELEASED',{x:x+1,y:y+1}));
   const intents=s.info().intents;assert.equal(intents.length,1);
   assert.deepEqual([intents[0].messageId,intents[0].actionId,intents[0].event,intents[0].value],[37,17,event,7]);
   assert.equal(record().text,message);assert.equal(record().actions[0].label,label);
   assert.deepEqual(f.bytes,original);
   s.command({op:'clear',scope:'status'});assert.deepEqual(s.info().messages,[]);
   assert.notDeepEqual(s.snapshot(),snapshot);
   s.restore(snapshot);assert.deepEqual(s.snapshot(),snapshot);assert.deepEqual(record(),source);assert.deepEqual(s.info().intents,[]);
  }
 }finally{s.close()}
});

test('native negotiated Terminal Kit reservations, handlers and visible hints',async()=>{
 const {negotiateHostShortcuts}=await import('./shortcut-profile.mjs');
 const scene=await NativeScene.create(fs.readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
 try{
  const before=scene.snapshot();const profile=negotiateHostShortcuts(scene,['CTRL_Q','CTRL_P','F1','F6']);
  assert.equal(profile.bindings.get('ALT_Q'),1);assert.equal(profile.bindings.get('ALT_P'),2);assert.equal(profile.bindings.get('F7'),3);assert.equal(profile.bindings.get('F8'),4);
  for(const reserved of ['CTRL_Q','CTRL_P','F1','F6']){assert.equal(profile.bindings.has(reserved),false);assert.equal(profile.managed.has(reserved),true);}
  assert.ok(profile.hints.includes('Quit: ALT_Q'));assert.ok(profile.hints.includes('Help: F7'));assert.deepEqual(scene.snapshot(),before);
  const absent=negotiateHostShortcuts(scene,['CTRL_Q','ALT_Q']);assert.ok(absent.hints.includes('Quit: unassigned'));assert.ok(![...absent.bindings.values()].includes(1));
  assert.throws(()=>negotiateHostShortcuts(scene,['CTRL_C']));
 }finally{scene.close()}
});
