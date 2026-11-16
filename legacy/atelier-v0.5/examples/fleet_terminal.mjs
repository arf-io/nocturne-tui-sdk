#!/usr/bin/env node
/** Pearl Fleet terminal host. Same controller, layouts and WASM as the browser.
 * Usage: node examples/fleet_terminal.mjs [--agent atlas] [--palette smart-dark]
 * No shell execution or provider connection. --data-fd replaces demo input with
 * NDJSON Fleet events; --commands-fd writes explicit outbound command records.
 */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import readline from 'node:readline';
import net from 'node:net';
import {PassThrough} from 'node:stream';
import {TerminalInputRouter} from './fleet_input.mjs';
import {performance} from 'node:perf_hooks';
import {StudioEngine} from '../dist/typescript/studio.js';
import {FleetController,FleetModel,createDemoFleet,DEMO_AGENTS} from '../dist/typescript/fleet.js';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const args=process.argv.slice(2),options={};
const HELP=`Pearl Fleet / Nocturne
node examples/fleet_terminal.mjs [options]
  --agent ID          Open this agent's workspace on startup
  --palette ID        One of palettes.json (default smart-dark)
  --columns N         Fixed columns; default live terminal width
  --rows N            Fixed rows; default live terminal height
  --fps N             Motion presentation ceiling 1..120 (default 60)
  --dense             Dense roster instead of cards
  --read-mode         Full-opacity text and no decorative motion
  --snapshot MS       Print a deterministic ANSI frame and exit
  --scene-out FILE    Write the normalized scene JSON and exit
  --agents FILE       AgentSpec[] JSON (1..32, for external data)
  --data-fd FD        Inherited NDJSON pipe/socket; disables simulation
  --commands-fd FD    Caller-owned outbound JSON descriptor
  --help              Show this help
Keys: Tab / arrows select, Enter opens, Esc returns, Ctrl+P holds motion,
Ctrl+F pauses demo feed, Ctrl+D density, Ctrl+R reading mode, Ctrl+Q exits.
In a workspace, type to edit its local draft; Enter queues it. PgUp/PgDn/End
control transcript history. SGR mouse clicks and wheel work in the pane.
No hook is installed in your shell or tmux configuration.
`;
for(let i=0;i<args.length;i++){
 const key=args[i];if(key==='--help'||key==='-h'){console.log(HELP);process.exit(0);}
 if(['--dense','--read-mode'].includes(key)){options[key]=true;continue;}
 if(!['--agent','--palette','--columns','--rows','--snapshot','--scene-out','--agents','--data-fd','--commands-fd','--fps'].includes(key)||i+1>=args.length){console.error('Invalid option: '+key+'\n'+HELP);process.exit(2);}options[key]=args[++i];
}
function numberOption(name,fallback,min,max){const n=options[name]===undefined?fallback:Number(options[name]);if(!Number.isSafeInteger(n)||n<min||n>max)throw new RangeError(name+' outside '+min+'..'+max);return n;}
const engine=await StudioEngine.create(new Uint8Array(fs.readFileSync(path.join(ROOT,'dist/nocturne.wasm'))),JSON.parse(fs.readFileSync(path.join(ROOT,'studio.schema.json'),'utf8')));
const external=options['--data-fd']!==undefined;
const specs=options['--agents']?JSON.parse(fs.readFileSync(options['--agents'],'utf8')):DEMO_AGENTS;
const model=external||options['--agents']?new FleetModel(specs):createDemoFleet();
const controller=new FleetController(engine,model,{dense:Boolean(options['--dense']),readMode:Boolean(options['--read-mode'])});
const presentationFps=numberOption('--fps',60,1,120);controller.setPresentationFps(presentationFps);
const palettes=JSON.parse(fs.readFileSync(path.join(ROOT,'palettes.json'),'utf8')).palettes,palette=palettes.find(p=>p.id===(options['--palette']||'smart-dark'));
if(!palette)throw new RangeError('Unknown palette');controller.config.palette=palette.colors;controller.config.values.baseColor=parseInt(palette.background.slice(1),16);controller.config.values.inkColor=parseInt(palette.ink.slice(1),16);
function resize(){controller.resize(numberOption('--columns',process.stdout.columns||144,0,512),numberOption('--rows',process.stdout.rows||48,0,256));}
resize();const initialTime=numberOption('--snapshot',2000,0,Number.MAX_SAFE_INTEGER);if(options['--snapshot']!==undefined){if(options['--agent'])controller.openAgent(options['--agent']);controller.setTime(initialTime);}else{controller.setTime(initialTime);if(options['--agent']){controller.openAgent(options['--agent']);controller.setTime(controller.motionMs+controller.options.expandMs);}}
/** Dirty-run output with bounded presentation backpressure. Model events are never
 * discarded when stdout is slow; only superseded, not-yet-written frames coalesce.
 */
class AnsiDiffWriter {
 constructor(stream){this.stream=stream;this.previous=null;this.pending=null;this.blocked=false;this.coalesced=0;stream.on('drain',()=>{this.blocked=false;if(this.pending){const f=this.pending;this.pending=null;this.present(f);}});}
 encode(frame){const old=this.previous,changedSize=!old||old.width!==frame.width||old.height!==frame.height;let out=changedSize?'\x1b[2J':'';let fg=-1,bg=-1;
  for(let y=0;y<frame.height;y++){let positioned=false;for(let x=0;x<frame.width;x++){const i=(y*frame.width+x)*4,changed=changedSize||frame.cells[i]!==old.cells[i]||frame.cells[i+1]!==old.cells[i+1]||frame.cells[i+2]!==old.cells[i+2];if(!changed){positioned=false;continue;}if(!positioned){out+=`\x1b[${y+1};${x+1}H`;positioned=true;}const f=frame.cells[i+1],b=frame.cells[i+2];if(f!==fg){out+=`\x1b[38;2;${f>>16};${f>>8&255};${f&255}m`;fg=f;}if(b!==bg){out+=`\x1b[48;2;${b>>16};${b>>8&255};${b&255}m`;bg=b;}const g=frame.cells[i];out+=g>=32&&g!==127?String.fromCodePoint(g):' ';}}
  this.previous=frame;return out+'\x1b[0m';
 }
 present(frame){if(this.blocked){if(this.pending)this.coalesced++;this.pending=frame;return;}this.blocked=!this.stream.write(this.encode(frame));}
}
const writer=new AnsiDiffWriter(process.stdout);
function render(){const s=controller.compose();writer.present(engine.render(s.config,s.timeMs,s.nodes,s.events));}
if(options['--scene-out']){fs.writeFileSync(options['--scene-out'],JSON.stringify(controller.compose(),null,2)+'\n');process.exit(0);}
if(options['--snapshot']!==undefined){render();process.stdout.write('\x1b[0m\n');}else{
 if(!process.stdin.isTTY||!process.stdout.isTTY){console.error('Interactive mode requires a TTY. Use --snapshot MS or --scene-out FILE.');process.exit(2);}
 let disposed=false,feed=true,sourceMs=10000,lastWall=performance.now(),motion=controller.motionMs,lastMotionPaint=lastWall;
 const input=process.stdin;const wasRaw=Boolean(input.isRaw);
 const outputFd=options['--commands-fd']===undefined?null:numberOption('--commands-fd',0,3,65535);
 const sinkStat=outputFd===null?null:fs.fstatSync(outputFd);
 const commandStream=outputFd===null?null:(sinkStat.isFIFO()||sinkStat.isSocket()?new net.Socket({fd:outputFd,readable:false,writable:true}):fs.createWriteStream('',{fd:outputFd,autoClose:false}));let commandsBlocked=false;
 function flushCommands(){if(!commandStream||commandsBlocked)return;const cmds=controller.drainCommands();for(const cmd of cmds)if(!commandStream.write(JSON.stringify(cmd)+'\n'))commandsBlocked=true;}
 if(commandStream){commandStream.on('drain',()=>{commandsBlocked=false;flushCommands();});commandStream.on('error',e=>{commandsBlocked=true;controller.inspection='COMMAND SINK ERROR: '+e.message;render();});}
 function transact(fn){try{fn();flushCommands();render();}catch(e){controller.inspection='INPUT ERROR: '+e.message;render();}}
 const keys=new PassThrough();readline.emitKeypressEvents(keys);
 const router=new TerminalInputRouter(text=>keys.write(text),m=>{if(m.down)transact(()=>m.button&64?controller.scroll((m.button&1)?-3:3):(m.button&3)===0?controller.click(m.x,m.y):undefined);},()=>keys.emit('keypress','',{name:'escape',sequence:'\x1b'}));
 input.on('data',bytes=>router.push(bytes));input.setRawMode(true);input.resume();process.stdout.write('\x1b[?1049h\x1b[?25l\x1b[?7l\x1b[?1000h\x1b[?1006h');
 const motionTimer=setInterval(()=>{const now=performance.now(),dt=Math.max(0,now-lastWall);lastWall=now;if(!controller.paused)motion+=dt;if(!controller.paused&&!controller.options.readMode&&!controller.options.reducedMotion&&now-lastMotionPaint>=1000/presentationFps){controller.setTime(Math.floor(motion));render();lastMotionPaint+=Math.floor((now-lastMotionPaint)/(1000/presentationFps))*(1000/presentationFps);}},8);
 const dataTimer=setInterval(()=>{if(model.demo&&feed){sourceMs+=80;transact(()=>controller.advanceDemo(sourceMs));}},80);
 let sourceStream=null;
 if(external){let buffer='',dropping=false;// Pipes must use libuv's nonblocking stream watcher, not a worker-thread
  // fs read which can prevent shutdown while the producer keeps its end open.
  sourceStream=new net.Socket({fd:numberOption('--data-fd',0,3,65535),readable:true,writable:false});sourceStream.setEncoding('utf8');
  sourceStream.on('data',chunk=>{buffer+=chunk;let index;while((index=buffer.indexOf('\n'))>=0){const line=buffer.slice(0,index);buffer=buffer.slice(index+1);if(dropping){dropping=false;continue;}if(line.length>65536){transact(()=>{throw new RangeError('event line exceeds 64 KiB');});continue;}if(line.trim())transact(()=>controller.ingest(JSON.parse(line)));}if(buffer.length>65536){buffer='';dropping=true;transact(()=>{throw new RangeError('event line exceeds 64 KiB');});}});
  sourceStream.on('end',()=>{controller.inspection='SOURCE CLOSED / retained data stays available';render();});sourceStream.on('error',e=>{controller.inspection='SOURCE ERROR: '+e.message;render();});
 }
 function cleanup(code=0){if(disposed)return;disposed=true;clearInterval(motionTimer);clearInterval(dataTimer);if(sourceStream)sourceStream.destroy();router.dispose();keys.end();input.setRawMode(wasRaw);input.pause();process.stdout.write('\x1b[0m\x1b[?1006l\x1b[?1000l\x1b[?7h\x1b[?25h\x1b[?1049l',()=>process.exit(code));setTimeout(()=>process.exit(code),300).unref();}
 keys.on('keypress',(str,key={})=>{
  const sequence=key.sequence||str||'',mouse=/^\x1b\[<(\d+);(\d+);(\d+)([Mm])$/.exec(sequence);
  if(mouse){const button=Number(mouse[1]),x=Number(mouse[2])-1,y=Number(mouse[3])-1;if(mouse[4]==='M')transact(()=>button&64?controller.scroll((button&1)?-3:3):controller.click(x,y));return;}
  if(key.ctrl&&['q','c'].includes(key.name)){cleanup();return;}
  if(key.ctrl&&key.name==='p'){transact(()=>controller.setPaused(!controller.paused));return;}
  if(key.ctrl&&key.name==='f'){feed=!feed;transact(()=>{controller.inspection=feed?'DEMO DATA RESUMED':'DEMO DATA HELD / motion independent';});return;}
  if(key.ctrl&&key.name==='d'){transact(()=>controller.configure({dense:!controller.options.dense}));return;}
  if(key.ctrl&&key.name==='r'){transact(()=>controller.configure({readMode:!controller.options.readMode}));return;}
  if(key.name==='tab'){transact(()=>controller.nextAgent(key.shift?-1:1));return;}
  if(key.name==='escape'){transact(()=>controller.closeAgent());return;}
  if(key.name==='pageup'||key.name==='pagedown'){transact(()=>controller.scroll(key.name==='pageup'?8:-8));return;}
  if(key.name==='end'){transact(()=>controller.liveTail());return;}
  if(key.name==='left'||key.name==='right'){transact(()=>controller.nextAgent(key.name==='right'?1:-1));return;}
  if(key.name==='return'){transact(()=>controller.opened?controller.send():controller.openAgent(controller.selectedId));return;}
  if(key.name==='backspace'){transact(()=>controller.setDraft(Array.from(controller.draft).slice(0,-1).join('')));return;}
  if(!key.ctrl&&!key.meta&&str&&Array.from(str).every(c=>c.codePointAt(0)>=32)){transact(()=>{if(!controller.opened)controller.openAgent(controller.selectedId);controller.setDraft(controller.draft+str);});}
 });
 process.stdout.on('resize',()=>transact(resize));for(const signal of ['SIGINT','SIGTERM','SIGHUP'])process.on(signal,()=>cleanup());process.on('uncaughtException',e=>{controller.inspection=String(e.message);cleanup(1);});render();
}
