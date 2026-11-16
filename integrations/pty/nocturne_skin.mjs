#!/usr/bin/env node
/** Experimental emulator-based PTY skin. Install @xterm/headless locally first.
 * Rendering themes the emulator buffer, never raw escape strings. The only
 * program executed is the argv after --, or the explicitly selected user shell.
 * This is NOT a security sandbox or a guarantee of arbitrary CLI compatibility.
 */
import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';import {createRequire} from 'node:module';import {spawn} from 'node:child_process';import {performance} from 'node:perf_hooks';
import {StudioEngine} from '../../dist/typescript/studio.js';import {ObservatoryModel,ObservatoryRenderer,MotionClock,clamp} from '../../dist/typescript/observatory.js';import {skinCell,rowAnsi} from './skin_core.mjs';
const DIR=path.dirname(fileURLToPath(import.meta.url)),ROOT=path.resolve(DIR,'../..'),require=createRequire(import.meta.url),argv=process.argv.slice(2),opts={};let command=[];
const HELP=`Nocturne optional PTY skin
  npm --prefix integrations/pty install
  node integrations/pty/nocturne_skin.mjs [options] -- PROGRAM [ARG...]
  node integrations/pty/nocturne_skin.mjs --palette smart-dark -- codex
  node integrations/pty/nocturne_skin.mjs --background warp -- claude
Options: --fps 60, --palette smart-dark, --background double-axis,
         --python python3, --recolor-default-text, --no-motion, --help
Without -- PROGRAM, uses $SHELL (or /bin/sh). Child runs as YOU, not sandboxed.
Prefix: Ctrl+] then q quit, p pause, t next palette, Ctrl+] literal prefix.
Only default child backgrounds are themed. Explicit RGB/indexed colors,
reverse-video highlights, hidden text, Unicode cell width and child echo policy
are preserved. No terminal clipboard, hyperlink or image escapes are forwarded.
Native Windows, terminal graphics, extended keyboard protocols, scrollback UI,
OSC palette mutation and actual Codex/Claude versions require separate testing.
`;
for(let i=0;i<argv.length;i++){const k=argv[i];if(k==='--'){command=argv.slice(i+1);break;}if(k==='--help'){console.log(HELP);process.exit(0);}if(['--recolor-default-text','--no-motion'].includes(k)){opts[k]=true;continue;}if(!['--fps','--palette','--background','--python'].includes(k)||argv[i+1]===undefined)throw Error('Unknown option '+k);opts[k]=argv[++i];}
if(!process.stdin.isTTY||!process.stdout.isTTY){console.error('An interactive TTY is required.');process.exit(2);}
let Terminal;try{({Terminal}=require('@xterm/headless'));}catch{console.error('Optional emulator dependency is not installed. Run: npm --prefix integrations/pty install');process.exit(2);}
if(!command.length)command=[process.env.SHELL||'/bin/sh'];const fps=Number(opts['--fps']||60);if(!Number.isInteger(fps)||fps<1||fps>120)throw Error('fps must be 1..120');
const engine=await StudioEngine.create(fs.readFileSync(ROOT+'/dist/nocturne.wasm'),JSON.parse(fs.readFileSync(ROOT+'/studio.schema.json'))),model=new ObservatoryModel(),renderer=new ObservatoryRenderer(engine),clock=new MotionClock(fps),palettes=JSON.parse(fs.readFileSync(ROOT+'/palettes.json')).palettes;
let paletteIndex=palettes.findIndex(p=>p.id===(opts['--palette']||'smart-dark'));if(paletteIndex<0)throw Error('Unknown palette');model.palette=palettes[paletteIndex];model.configure({fps,backgroundStyle:opts['--background']||'double-axis',brightness:.12,starDensity:.012,starCount:300,motion:!opts['--no-motion']});model.simulation=false;
function geometry(){return {cols:clamp(process.stdout.columns||100,36,240),rows:clamp(process.stdout.rows||32,18,100)};}
let {cols,rows}=geometry();model.resize(cols,rows);const terminal=new Terminal({cols,rows,allowProposedApi:true,scrollback:5000,convertEol:false});const child=spawn(opts['--python']||'python3',[DIR+'/pty_broker.py','--columns',String(cols),'--rows',String(rows),'--',...command],{stdio:['pipe','pipe','pipe']});
const input=process.stdin,wasRaw=Boolean(input.isRaw);let closed=false,stdoutBlocked=false,paintPending=false,previousRows=[],rawBuffer='',queuedBytes=0,prefix=false,cursorVisible=true,cursorShape=0,syncHeldAt=0,modeString='',parserTail=Promise.resolve(),returnedCode=0;const modes=new Set();clock.sample(performance.now());
function protocol(row){if(closed||child.stdin.destroyed)return;const accepted=child.stdin.write(JSON.stringify(row)+'\n');if(!accepted)input.pause();}
child.stdin.on('drain',()=>{if(!closed)input.resume();});child.stdin.on('error',()=>{});
terminal.onData(data=>protocol({type:'input',data:Buffer.from(data).toString('base64')}));
// Never forward clipboard, links, title changes, or graphics to the outer TTY.
for(const id of [0,1,2,8,52])terminal.parser.registerOscHandler(id,()=>true);
for(const final of ['h','l'])terminal.parser.registerCsiHandler({prefix:'?',final},params=>{const on=final==='h';for(const p of params){if(typeof p!=='number')continue;if(on)modes.add(p);else modes.delete(p);if(p===25)cursorVisible=on;if(p===2026)syncHeldAt=on?performance.now():0;}return false;});
terminal.parser.registerCsiHandler({intermediates:' ',final:'q'},params=>{cursorShape=clamp(Number(params[0]||0),0,6);return false;});
function mirrorModes(){let result='';for(const n of [1,9,1000,1002,1003,1004,1005,1006,1015,2004])result+=`\x1b[?${n}${modes.has(n)?'h':'l'}`;result+=modes.has(66)?'\x1b=':'\x1b>';return result;}
function paint(){if(closed)return;if(syncHeldAt&&performance.now()-syncHeldAt<1000){paintPending=true;return;}if(stdoutBlocked){paintPending=true;return;}paintPending=false;const surface=renderer.renderSurface(model),buffer=terminal.buffer.active,nextRows=[];let out='\x1b[?25l';
 for(let y=0;y<rows;y++){const line=buffer.getLine(buffer.baseY+y),cells=[];for(let x=0;x<cols;x++){const i=(y*cols+x)*4;cells.push(skinCell(line?.getCell(x),surface,i,{ink:parseInt(model.palette.ink.slice(1),16),background:parseInt(model.palette.background.slice(1),16),recolorDefault:!!opts['--recolor-default-text'],hueColor:renderer.ink(x*model.options.hueStep+model.motionMs*model.options.textHueSpeed/1000)}));}const row=rowAnsi(cells);nextRows.push(row);if(row!==previousRows[y])out+=`\x1b[${y+1};1H`+row;}
 previousRows=nextRows;const newModes=mirrorModes();if(newModes!==modeString){out+=newModes;modeString=newModes;}out+='\x1b[0m'+`\x1b[${clamp(buffer.cursorY+1,1,rows)};${clamp(buffer.cursorX+1,1,cols)}H`+`\x1b[${cursorShape} q`+(cursorVisible?'\x1b[?25h':'');stdoutBlocked=!process.stdout.write(out);
}
process.stdout.on('drain',()=>{stdoutBlocked=false;if(paintPending)paint();});
child.stdout.setEncoding('utf8');child.stdout.on('data',chunk=>{rawBuffer+=chunk;if(rawBuffer.length>262144){shutdown(1);return;}let pos;while((pos=rawBuffer.indexOf('\n'))>=0){const line=rawBuffer.slice(0,pos);rawBuffer=rawBuffer.slice(pos+1);let row;try{row=JSON.parse(line);}catch{shutdown(1);return;}
 if(row.type==='output'){const data=Buffer.from(row.data,'base64');queuedBytes+=data.length;if(queuedBytes>1048576)child.stdout.pause();terminal.write(new Uint8Array(data),()=>{queuedBytes-=data.length;if(queuedBytes<524288)child.stdout.resume();model.setTime(clock.sample(performance.now()));paint();});}
 else if(row.type==='exit'){returnedCode=row.code;terminal.write('',()=>shutdown(returnedCode));}
 else if(row.type==='error'){process.stderr.write('PTY protocol: '+String(row.message).replace(/[\x00-\x1f\x7f]/g,' ')+'\n');}
 }});
child.stderr.on('data',bytes=>{const msg=bytes.toString('utf8').replace(/[\x00-\x08\x0b-\x1f\x7f]/g,'');process.stderr.write(msg);});child.on('error',e=>{process.stderr.write('Unable to start PTY broker: '+e.message+'\n');shutdown(127);});child.on('close',code=>{if(!closed)setTimeout(()=>shutdown(returnedCode||code||0),30);});
input.setRawMode(true);input.resume();process.stdout.write('\x1b[?1049h\x1b[2J\x1b[?7l');
input.on('data',bytes=>{const forward=[];for(const b of bytes){if(prefix){prefix=false;if(b===113){shutdown(0);return;}if(b===112){model.configure({motion:!model.options.motion});clock.setPaused(!model.options.motion,performance.now());paint();continue;}if(b===116){paletteIndex=(paletteIndex+1)%palettes.length;model.palette=palettes[paletteIndex];paint();continue;}if(b===29){forward.push(29);continue;}forward.push(29,b);}else if(b===29)prefix=true;else forward.push(b);}if(forward.length)protocol({type:'input',data:Buffer.from(forward).toString('base64')});});
process.stdout.on('resize',()=>{({cols,rows}=geometry());model.resize(cols,rows);terminal.resize(cols,rows);protocol({type:'resize',columns:cols,rows});previousRows=[];paint();});
const timer=setInterval(()=>{if(clock.shouldPaint(performance.now())&&model.options.motion){model.setTime(clock.timeMs);paint();}},4);if(!model.options.motion)clock.setPaused(true,performance.now());paint();
function shutdown(code=0){if(closed)return;protocol({type:'close'});closed=true;clearInterval(timer);input.setRawMode(wasRaw);input.pause();child.stdin.end();setTimeout(()=>{if(child.exitCode===null)child.kill('SIGTERM');},150).unref();const reset='\x1b[0m\x1b[?1l\x1b>\x1b[?9l\x1b[?1000l\x1b[?1002l\x1b[?1003l\x1b[?1004l\x1b[?1005l\x1b[?1006l\x1b[?1015l\x1b[?2004l\x1b[0 q\x1b[?7h\x1b[?25h\x1b[?1049l';process.stdout.write(reset,()=>{setTimeout(()=>process.exit(code),180);});setTimeout(()=>process.exit(code),500).unref();}
for(const signal of ['SIGINT','SIGTERM','SIGHUP'])process.on(signal,()=>shutdown(128+(signal==='SIGINT'?2:signal==='SIGTERM'?15:1)));process.stdout.on('error',()=>shutdown(1));
