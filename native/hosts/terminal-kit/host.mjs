/** Terminal Kit owns the terminal; C/WASM owns all scene state and geometry.
 * Exports below are host-local test seams, not additions to the native SDK API.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { StringDecoder } from 'node:string_decoder';
import kit from 'terminal-kit';
import wcwidth from 'wcwidth';
import {negotiateHostShortcuts} from './shortcut-profile.mjs';
import { NativeScene } from '../../bindings/typescript/native_scene.mjs';

const PASTE_START=Buffer.from('\x1b[200~'),PASTE_END=Buffer.from('\x1b[201~');

/** Blit one owned native frame into real ScreenBufferHD; never advance scene state.
 * Invalid/truncated frame dimensions throw before writes. Unsupported-width scalars
 * display U+FFFD; the native frame and retained document stay untouched.
 */
export function blitFrame(buffer,f){
 if(!Number.isInteger(f.width)||!Number.isInteger(f.height)||f.width<0||f.height<0||
    f.width>buffer.width||f.height>buffer.height||f.bytes.byteLength!==f.width*f.height*16)throw Error('Invalid native frame bounds');
 const view=new DataView(f.bytes.buffer,f.bytes.byteOffset,f.bytes.byteLength);
 const rgb=v=>({r:v>>>16&255,g:v>>>8&255,b:v&255,a:255});
 for(let y=0;y<f.height;y++)for(let x=0;x<f.width;x++){
  const i=(y*f.width+x)*16,g=view.getUint32(i,true),fg=view.getUint32(i+4,true),bg=view.getUint32(i+8,true);
  let ch=g<=0x10ffff?String.fromCodePoint(g):'�';if(g<32||g===127||wcwidth(ch)!==1)ch='�';
  buffer.put({x,y,attr:{color:rgb(fg),bgColor:rgb(bg)}},ch);
 }
}

/** Translate Terminal Kit mouse events into the unchanged native pointer/wheel API.
 * Coordinates become zero-based exactly once. Unrecognized names return null.
 */
export function mouseCommand(name,data){
 const x=data.x-1,y=data.y-1;
 if(name==='MOUSE_WHEEL_UP'||name==='MOUSE_WHEEL_DOWN')return {op:'wheel',x,y,delta:name==='MOUSE_WHEEL_UP'?1:-1,shift:!!data.shift};
 const moving=name==='MOUSE_MOTION'||name==='MOUSE_DRAG';
 if(!moving&&!name.includes('PRESSED')&&!name.includes('RELEASED'))return null;
 return {op:'pointer',x,y,phase:name.includes('RELEASED')?'up':moving?'move':'down',
  button:name.includes('RIGHT')||data.right?2:name.includes('MIDDLE')||moving&&(data.code&3)===1?1:0,shift:!!data.shift,alt:!!data.alt};
}

/** Separate standard bracketed paste from the real terminal key parser.
 * feed(Buffer) accepts fragmented delimiters/UTF-8; ordinary bytes go to onBytes,
 * completed paste goes once to onPaste. Paste controls are data, not shortcuts.
 * flush() resolves an isolated Escape and rejects an unfinished paste. close()
 * drops parser scratch. There is no timer/terminal/framework emulation here.
 */
export function createPasteDecoder(onBytes,onPaste){
 let pending=Buffer.alloc(0),pasting=false,closed=false,pasteBytes=0,pasteChunks=[];
 const utf8=new StringDecoder('utf8');
 const ordinary=b=>{const text=utf8.write(b);if(text)onBytes(Buffer.from(text));};
 return {
  get waiting(){return !pasting&&pending.length>0},
  feed(data){
   if(closed)return;
   pending=Buffer.concat([pending,data]);
   while(pending.length&&!closed){
    if(pasting){
     const end=pending.indexOf(PASTE_END);
     if(end<0){
      let suffix=0;for(let n=1;n<PASTE_END.length&&n<=pending.length;n++)if(pending.subarray(pending.length-n).equals(PASTE_END.subarray(0,n)))suffix=n;
      const body=pending.subarray(0,pending.length-suffix);if(body.length){pasteChunks.push(body);pasteBytes+=body.length;}
      // Only a possible delimiter suffix is concatenated with the next input.
      // Retained body chunks are joined once, avoiding quadratic large pastes.
      pending=pending.subarray(pending.length-suffix);return;
     }
     if(end){pasteChunks.push(pending.subarray(0,end));pasteBytes+=end;}
     const text=new TextDecoder('utf-8',{fatal:true}).decode(Buffer.concat(pasteChunks,pasteBytes));
     pending=pending.subarray(end+PASTE_END.length);pasting=false;pasteChunks=[];pasteBytes=0;onPaste(text);
    }else{
     const start=pending.indexOf(PASTE_START);
     if(start>=0){if(start)ordinary(pending.subarray(0,start));pending=pending.subarray(start+PASTE_START.length);pasting=true;continue}
     let keep=0;
     for(let n=1;n<PASTE_START.length&&n<=pending.length;n++)if(pending.subarray(pending.length-n).equals(PASTE_START.subarray(0,n)))keep=n;
     const end=pending.length-keep;if(end)ordinary(pending.subarray(0,end));pending=pending.subarray(end);return;
    }
   }
  },
  flush(){if(pasting)throw Error('unterminated bracketed paste');if(pending.length)ordinary(pending);pending=Buffer.alloc(0)},
  close(){closed=true;pending=Buffer.alloc(0);pasteChunks=[];pasteBytes=0}
 };
}

/** Run the actual host lifecycle, settling only after independent cleanup attempts.
 * Normal CLI supplies no options. Tests may supply a real NativeScene and bounded
 * observers/failure hooks; these are never native commands or a remote protocol.
 * The host owns and closes its scene. Errors reject after terminal restoration.
 */
export async function startHost(options={}){
 const term=kit.terminal;
 if(!process.stdin.isTTY||!process.stdout.isTTY)throw Error('An interactive terminal is required');
 const scene=options.scene??await NativeScene.create(fs.readFileSync(fileURLToPath(new URL('../../dist/nocturne_native.wasm',import.meta.url))));
 let shortcutProfile;
 let buffer,paused=!!options.paused,logical=0,last=performance.now(),timer,escapeTimer,closed=false,terminalEntered=false;
 let resolveDone,rejectDone;const done=new Promise((resolve,reject)=>{resolveDone=resolve;rejectDone=reject});
 // A setup hook may fail before this function returns the promise to its caller.
 done.catch(()=>{});
 const observe=event=>options.observe?.(event,scene,buffer?{width:buffer.width,height:buffer.height}:null);
 const paint=()=>{if(closed||!buffer)return;blitFrame(buffer,scene.render());if(buffer.height>1){buffer.put({x:0,y:buffer.height-1},shortcutProfile.hints.padEnd(buffer.width).slice(0,buffer.width))}buffer.draw({delta:true})};
 const command=value=>{if(closed)return;scene.command(value);paint();observe(value.op)};
 const resize=()=>{const width=Math.max(1,term.width),height=Math.max(1,term.height);scene.command({op:'resize',width,height:Math.max(1,height-1)});buffer=new kit.ScreenBufferHD({dst:term,width,height});paint();observe('resize')};
 const guarded=fn=>(...args)=>{if(closed)return;try{fn(...args)}catch(e){close(e)}};
 let paste;
 function close(error){
  if(closed)return;closed=true;clearInterval(timer);clearTimeout(escapeTimer);paste?.close();
  const failures=error?[error]:[];const attempt=fn=>{try{fn()}catch(e){failures.push(e)}};
  term.removeListener('resize',onResize);term.removeListener('key',onKey);term.removeListener('mouse',onMouse);term.removeListener('terminal',onTerminal);
  process.stdin.removeListener('data',onData);
  process.removeListener('SIGINT',onSignal);process.removeListener('SIGTERM',onSignal);
  process.removeListener('uncaughtException',onUncaught);process.removeListener('unhandledRejection',onUncaught);process.removeListener('exit',onExit);
  if(terminalEntered){
   // Terminal Kit 3.1.4 grabInput(false) intentionally does NOT disable SGR mouse.
   // An output failure must not skip raw-mode restoration or the remaining modes.
   attempt(()=>term.grabInput(false));attempt(()=>process.stdin.setRawMode(false));attempt(()=>process.stdin.pause());
   attempt(()=>term.mouseSGR(false));attempt(()=>term.raw('\x1b[?2004l'));attempt(()=>term.focusEvent(false));
   attempt(()=>term.styleReset());attempt(()=>term.hideCursor(false));attempt(()=>term.fullscreen(false));
  }
  attempt(()=>observe('exit'));attempt(()=>scene.close());
  if(failures.length)rejectDone(failures.length===1?failures[0]:new AggregateError(failures,'Host/cleanup failure'));else resolveDone();
 }
 const onResize=guarded(resize);
 const onKey=guarded((name,matches,data)=>{
  options.beforeEvent?.('key',name,scene);
  if(name==='CTRL_C'){close();return}
  const action=shortcutProfile.bindings.get(name);
  if(action===1){close();return}
  if(action===2){paused=!paused;last=performance.now();command({op:'pause',paused});return}
  if(action===3||action===4){command({op:'key',key:action===3?'F1':'F6'});return}
  if(shortcutProfile.managed.has(name))return; // reserved chords never become document text
  const keys={UP:'ArrowUp',DOWN:'ArrowDown',LEFT:'ArrowLeft',RIGHT:'ArrowRight',HOME:'Home',END:'End',BACKSPACE:'Backspace',DELETE:'Delete',ESCAPE:'Escape',PAGE_UP:'PageUp',PAGE_DOWN:'PageDown'};
  if(keys[name])command({op:'key',key:keys[name]});else if(['CTRL_A','CTRL_E','CTRL_Z'].includes(name))command({op:'key',key:name.slice(-1).toLowerCase(),ctrl:true});else if(name==='ENTER')command({op:'key',key:'Enter'});else if(data?.isCharacter)command({op:'key',key:name});
 });
 const onMouse=guarded((name,data)=>{const value=mouseCommand(name,data);if(value)command(value)});
 const onTerminal=guarded(name=>{if(name==='FOCUS_OUT')command({op:'pointer',phase:'cancel',x:-1,y:-1})});
 const onData=guarded(data=>{
  clearTimeout(escapeTimer);paste.feed(data);
  if(paste.waiting)escapeTimer=setTimeout(guarded(()=>paste.flush()),40);
 });
 const onSignal=()=>close();const onUncaught=e=>close(e instanceof Error?e:Error(String(e)));const onExit=()=>close();
 process.once('SIGINT',onSignal);process.once('SIGTERM',onSignal);process.once('exit',onExit);
 process.once('uncaughtException',onUncaught);process.once('unhandledRejection',onUncaught);
 try{
  shortcutProfile=negotiateHostShortcuts(scene,options.reservedShortcuts??[]);
  terminalEntered=true;term.fullscreen(true);term.hideCursor(true);term.grabInput({mouse:'motion',focus:true});
  term.raw('\x1b[?2004h');
  // Actual stdin still supplies every byte. Filter only bracketed-paste framing;
  // all ordinary key/mouse input is parsed by the pinned Terminal Kit instance.
  paste=createPasteDecoder(b=>{if(!closed)term.onStdin(b)},text=>command({op:'input',text}));
  process.stdin.removeListener('data',term.onStdin);process.stdin.on('data',onData);
  await options.afterEnter?.(term,scene);
  if(closed)return done;
  if(!options.scene)scene.command({op:'emitter',id:1,effect:'weather/autumn-drift',count:240,runningTimeMs:20000});
  if(paused)scene.command({op:'pause',paused:true});resize();
  term.on('resize',onResize);term.on('key',onKey);term.on('mouse',onMouse);term.on('terminal',onTerminal);
  observe('ready');
  timer=setInterval(guarded(()=>{const now=performance.now();if(!paused){logical+=(now-last)*1000;scene.command({op:'time',timeUs:Math.floor(logical),budget:240})}last=now;paint();observe('tick')}),1000/60);
 }catch(e){close(e)}
 return done;
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 try{
  const reservedShortcuts=[];for(let i=2;i<process.argv.length;i++){if(process.argv[i]!=='--reserve-shortcut'||!process.argv[i+1])throw Error('Usage: host.mjs [--reserve-shortcut CTRL_Q]');reservedShortcuts.push(process.argv[++i]);}
  await startHost({reservedShortcuts})
 }catch(error){console.error(error);process.exitCode=1}
}
