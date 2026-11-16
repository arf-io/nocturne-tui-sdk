#!/usr/bin/env node
/** Actual terminal host for the shared Observatory model. No shell or providers.
 * POSIX TTY input, dirty cells, immediate input commits, 60 Hz motion ceiling.
 */
import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';import {performance} from 'node:perf_hooks';import readline from 'node:readline';import net from 'node:net';import {PassThrough} from 'node:stream';
import {StudioEngine} from '../dist/typescript/studio.js';import {ObservatoryModel,ObservatoryRenderer,MotionClock,OBSERVATORY_SCENES,activateObservatory,editScratch,clamp} from '../dist/typescript/observatory.js';import {TerminalInputRouter} from './fleet_input.mjs';import {CellWriter} from './observatory_writer.mjs';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');const args=process.argv.slice(2),opts={};const HELP=`Nocturne Observatory / local terminal studies
node examples/observatory_terminal.mjs [options]
 --scene ID        chat, scope, warp, dag, spatial-menu, bbs, bbs-config,
                   windows, lynx, nano, pico, tmux, controls, sensors, logs, text
 --palette ID      smart-dark (default), copper, neon-dreams, etc.
 --fps N           Presentation ceiling 1..120 (default 60); time is unchanged
 --columns N       36..240; otherwise follow terminal geometry
 --rows N          18..100
 --snapshot MS     One explicit-time ANSI frame; no TTY needed
 --sensor-fd FD    Inherited NDJSON PIPE/socket; disables synthetic feed
 --config FILE     Exported options/palette JSON
 --no-demo         No synthetic measurements
 --read-mode       Hold motion; input/data remain live
 --help
Keys: Ctrl+Q exits, Ctrl+P holds motion, Ctrl+N next scene, Ctrl+K palette,
Tab/arrows select, Enter activate/store, Esc dismiss, PgUp/PgDn scroll,
Alt+arrows rotate camera; mouse selects; shift-click emits a nova.
No local input is executed or sent to a remote provider.
`;
for(let i=0;i<args.length;i++){const k=args[i];if(k==='--help'||k==='-h'){console.log(HELP);process.exit(0);}if(['--no-demo','--read-mode'].includes(k)){opts[k]=true;continue;}if(!['--scene','--palette','--fps','--columns','--rows','--snapshot','--sensor-fd','--config'].includes(k)||!args[i+1])throw Error('Unknown or missing option: '+k);opts[k]=args[++i];}
function number(k,fallback,lo,hi){const v=opts[k]===undefined?fallback:Number(opts[k]);if(!Number.isSafeInteger(v)||v<lo||v>hi)throw RangeError(k+' outside '+lo+'..'+hi);return v;}
const engine=await StudioEngine.create(fs.readFileSync(ROOT+'/dist/nocturne.wasm'),JSON.parse(fs.readFileSync(ROOT+'/studio.schema.json'))),model=new ObservatoryModel(),renderer=new ObservatoryRenderer(engine),clock=new MotionClock(number('--fps',60,1,120)),writer=new CellWriter(process.stdout);
const palettes=JSON.parse(fs.readFileSync(ROOT+'/palettes.json')).palettes;model.palette=palettes.find(p=>p.id===(opts['--palette']||'smart-dark'));if(!model.palette)throw Error('Unknown palette');model.configure({fps:clock.fps,motion:!opts['--read-mode']});if(opts['--config']){const c=JSON.parse(fs.readFileSync(opts['--config'],'utf8'));model.configure(c.options||c);if(c.palette)model.palette=c.palette;}model.setScene(opts['--scene']||'chat');model.simulation=!opts['--no-demo']&&opts['--sensor-fd']===undefined;
function resize(){model.resize(number('--columns',clamp(process.stdout.columns||136,36,240),36,240),number('--rows',clamp(process.stdout.rows||44,18,100),18,100));}
resize();clock.seek(number('--snapshot',4000,0,Number.MAX_SAFE_INTEGER),performance.now());model.setTime(clock.timeMs);model.demoData(0);let latest,selection=-1,source,closed=false;
function present(){latest=renderer.render(model);writer.present(latest.frame);}
function syncTime(){const now=performance.now();clock.setFps(model.options.fps);if(clock.paused===model.options.motion)clock.setPaused(!model.options.motion,now);model.setTime(clock.sample(now));return now;}
function act(fn){try{fn();syncTime();present();}catch(e){model.notice='INPUT: '+e.message;present();}}
if(opts['--snapshot']!==undefined){present();process.stdout.write('\x1b[0m\n');}else{
 if(!process.stdin.isTTY||!process.stdout.isTTY){console.error('TTY required; use --snapshot MS for redirected output.');process.exit(2);}
 const input=process.stdin,wasRaw=Boolean(input.isRaw),keys=new PassThrough();readline.emitKeypressEvents(keys);
 const router=new TerminalInputRouter(text=>keys.write(text),m=>{if(!m.down)return;act(()=>{if(m.button&64){model.scroll=Math.max(0,model.scroll+((m.button&1)?3:-3));return;}const hit=engine.hit(latest.nodes,m.x,m.y);if(hit)activateObservatory(model,hit.id);else model.emit(m.x,m.y,'*',(m.button&4)?'nova':model.options.weatherStyle);});},()=>keys.emit('keypress','',{name:'escape'}));
 input.setRawMode(true);input.resume();input.on('data',b=>router.push(b));process.stdout.write('\x1b[?1049h\x1b[?25l\x1b[?7l\x1b[?1000h\x1b[?1006h');
 const motionTimer=setInterval(()=>{try{if(clock.shouldPaint(performance.now())&&model.options.motion){model.setTime(clock.timeMs);present();}}catch(e){model.notice='RENDER: '+e.message;}},4);
 const dataTimer=setInterval(()=>{act(()=>{const now=syncTime();model.demoData(now);model.routeRates(now);});},50);
 function cleanup(code=0){if(closed)return;closed=true;clearInterval(motionTimer);clearInterval(dataTimer);if(source)source.destroy();router.dispose();keys.end();writer.dispose();input.setRawMode(wasRaw);input.pause();process.stdout.write('\x1b[0m\x1b[?1006l\x1b[?1000l\x1b[?7h\x1b[?25h\x1b[?1049l',()=>process.exit(code));setTimeout(()=>process.exit(code),350).unref();}
 process.on('SIGINT',()=>cleanup());process.on('SIGTERM',()=>cleanup());process.on('SIGHUP',()=>cleanup());process.stdout.on('resize',()=>act(resize));process.stdout.on('error',()=>cleanup(1));
 keys.on('keypress',(str,key={})=>{if(key.ctrl&&['q','c'].includes(key.name)){cleanup();return;}act(()=>{
  if(!model.showPalette&&['nano','pico'].includes(model.scene)&&!key.ctrl&&!key.meta){const actions={return:'insert',backspace:'backspace',delete:'delete',left:'left',right:'right',up:'up',down:'down',home:'home',end:'end'},a=actions[key.name];if(a||str&&[...str].length===1&&str!=='\t'){editScratch(model,a||'insert',key.name==='return'?'\n':a?'':str);return;}}
  const available=latest.semantics.filter(s=>!s.disabled);
  if(key.ctrl&&key.name==='p')model.configure({motion:!model.options.motion});
  else if(key.ctrl&&key.name==='n'){const i=OBSERVATORY_SCENES.findIndex(s=>s.id===model.scene);model.setScene(OBSERVATORY_SCENES[(i+1)%OBSERVATORY_SCENES.length].id);selection=-1;}
  else if(key.ctrl&&key.name==='k'){model.showPalette=!model.showPalette;model.paletteQuery='';selection=-1;}
  else if(key.name==='escape'){model.showPalette=false;selection=-1;}
  else if(key.meta&&['up','down','left','right'].includes(key.name)){model.configure({cameraYaw:clamp(model.options.cameraYaw+(key.name==='left'?-3:key.name==='right'?3:0),-180,180),cameraPitch:clamp(model.options.cameraPitch+(key.name==='up'?3:key.name==='down'?-3:0),-89,89)});}
  else if(['tab','up','down'].includes(key.name)){if(available.length){selection=(selection+(key.shift||key.name==='up'?-1:1)+available.length)%available.length;model.focusId=available[selection].id;model.selected=selection;model.notice='Selected: '+available[selection].label;}}
  else if(key.name==='return'){if(model.showPalette&&available.length)activateObservatory(model,available[Math.max(0,selection)].id);else if(selection>=0&&available[selection])activateObservatory(model,available[selection].id);else if(['nano','pico'].includes(model.scene)){model.editor=model.editor.slice(0,model.editorCursor)+'\n'+model.editor.slice(model.editorCursor);model.editorCursor++;}else model.send();selection=-1;}
  else if(key.name==='backspace'){if(model.showPalette)model.paletteQuery=[...model.paletteQuery].slice(0,-1).join('');else if(['nano','pico'].includes(model.scene)&&model.editorCursor){model.editor=model.editor.slice(0,model.editorCursor-1)+model.editor.slice(model.editorCursor);model.editorCursor--;}else model.backspace();}
  else if(key.name==='pageup'||key.name==='pagedown')model.scroll=Math.max(0,model.scroll+(key.name==='pageup'?5:-5));
  else if(key.name==='end')model.scroll=0;
  else if(!key.ctrl&&!key.meta&&str&&!str.startsWith('\x1b')){if(model.showPalette)model.paletteQuery=(model.paletteQuery+str).slice(0,64);else if(['nano','pico'].includes(model.scene)){if(model.editor.length+str.length>32768)throw Error('Scratch limit');model.editor=model.editor.slice(0,model.editorCursor)+str+model.editor.slice(model.editorCursor);model.editorCursor+=str.length;}else model.input(str);}
  model.revision++;
 });});
 if(opts['--sensor-fd']!==undefined){const fd=number('--sensor-fd',3,3,65535),stat=fs.fstatSync(fd);if(!stat.isFIFO()&&!stat.isSocket()){cleanup(2);throw Error('--sensor-fd requires a pipe/socket');}source=new net.Socket({fd,readable:true,writable:false});source.setEncoding('utf8');let buffer='',dropping=false;source.on('data',chunk=>{buffer+=chunk;let i;while((i=buffer.indexOf('\n'))>=0){const line=buffer.slice(0,i);buffer=buffer.slice(i+1);if(dropping){dropping=false;continue;}act(()=>{if(line.length>65536)throw Error('sensor record limit');if(!line.trim())return;const row=JSON.parse(line);row.atMs=performance.now();if(row.type==='waveform')model.ingestWaveform(row);else{model.ingest(row);model.sourceLabel=(row.quality==='measured'?'MEASURED':row.quality==='synthetic'?'SYNTHETIC':'EXTERNAL')+' / inherited sensor pipe';}});}if(buffer.length>65536){buffer='';dropping=true;model.notice='Sensor record dropped: over 64 KiB';}});source.on('error',e=>act(()=>{model.notice='SENSOR: '+e.message;}));source.on('end',()=>act(()=>{model.notice='Sensor source closed; retained values expire by TTL.';}));}
 present();
}
