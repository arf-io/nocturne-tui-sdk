#!/usr/bin/env node
/** Spatial Atelier terminal host. Runs the same cells and model as the gallery.
 * Owns TTY modes, clocks, bounded writer, input routing and cooperative layout.
 * It never executes typed content or connects to a provider. */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {performance} from 'node:perf_hooks';
import readline from 'node:readline';
import {PassThrough} from 'node:stream';
import {StudioEngine} from '../dist/typescript/studio.js';
import {AtelierModel,AtelierRenderer,ATELIER_SCENES,activateAtelier} from '../dist/typescript/atelier.js';
import {loadAtelierSettings} from '../dist/typescript/atelier_settings.js';
import {MotionClock,clamp,editScratch} from '../dist/typescript/observatory.js';
import {TEXT_EFFECTS} from '../dist/typescript/text_fx.js';
import {WINDOW_EFFECTS} from '../dist/typescript/window_fx.js';
import {TerminalInputRouter} from './fleet_input.mjs';
import {CellWriter} from './observatory_writer.mjs';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const HELP=`Nocturne Spatial Atelier 0.5 / actual terminal renderer
node examples/atelier_terminal.mjs [options]
  --scene ID       warp (Oblique Hyperlane), dag, weather, text, windows,
                   museum, spatial-menu, chat, scope, bbs, ...
  --palette ID     smart-dark, copper, stellar, neon-dreams, ...
  --fps N          1..120 presentation ceiling, default 60
  --columns N      36..240; default follows terminal
  --rows N         18..100; default follows terminal
  --settings FILE  v5 visual settings exported by the gallery
  --graph FILE     {nodes:[...],edges:[...]} graph JSON, limit 1 MiB
  --layout KIND    layered, force, radial
  --dimensions N   2 or 3
  --snapshot MS    One explicit-time ANSI frame, no TTY required
  --read-mode      Hold decorative motion, not typing or interaction
  --no-demo        Disable synthetic telemetry
  --help

Ctrl+G: visible camera/action console. Click its named buttons, or Tab + Enter.
Alt+arrows look/orbit. Alt+W/S move forward/back; Alt+A/D strafe;
Alt+Q/E roll; Alt+H resets; Alt+M toggles look/orbit; Alt+Space brakes.
Ctrl+P pause. Ctrl+N next scene. Ctrl+K palette. Ctrl+R reveal text.
Ctrl+U conceal text. Ctrl+E next text effect. Ctrl+O next window effect.
Ctrl+B nova. Ctrl+L arrange graph. Escape closes console. Ctrl+Q exits.
Click cell controls / dock. Drag a window body; drag elsewhere to orbit/look.
Shift+drag pans. Wheel moves; Shift+wheel zooms. Local typing stays immediate.
All data is local/demo. This is NOT a shell interpreter or an agent connection.
`;
const args=process.argv.slice(2),opts={};
for(let i=0;i<args.length;i++){
 const key=args[i];if(key==='--help'||key==='-h'){console.log(HELP);process.exit(0);}
 if(['--read-mode','--no-demo'].includes(key)){opts[key]=true;continue;}
 if(!['--scene','--palette','--fps','--columns','--rows','--settings','--graph','--layout','--dimensions','--snapshot'].includes(key)||!args[i+1])throw Error('Unknown/missing option '+key);
 opts[key]=args[++i];
}
const number=(key,fallback,lo,hi)=>{const n=opts[key]===undefined?fallback:Number(opts[key]);if(!Number.isSafeInteger(n)||n<lo||n>hi)throw new RangeError(key+' requires '+lo+'..'+hi);return n;};
const readJson=file=>{if(fs.statSync(file).size>1048576)throw new RangeError('JSON limit 1 MiB');return JSON.parse(fs.readFileSync(file,'utf8'));};
const engine=await StudioEngine.create(fs.readFileSync(ROOT+'/dist/nocturne.wasm'),readJson(ROOT+'/studio.schema.json'));
const model=opts['--settings']?loadAtelierSettings(readJson(opts['--settings'])):new AtelierModel();
const renderer=new AtelierRenderer(engine),clock=new MotionClock(number('--fps',model.options.fps,1,120)),writer=new CellWriter(process.stdout);
const palettes=readJson(ROOT+'/palettes.json').palettes;
if(opts['--palette']){const p=palettes.find(p=>p.id===opts['--palette']);if(!p)throw Error('Unknown palette');model.palette=p;}
function resize(){model.resize(number('--columns',clamp(process.stdout.columns||136,36,240),36,240),number('--rows',clamp(process.stdout.rows||44,18,100),18,100));}
resize();if(opts['--scene'])model.setScene(opts['--scene']);
if(opts['--graph']||opts['--layout']||opts['--dimensions']){model.setScene('dag');model.beginLayout({algorithm:opts['--layout']||'layered',dimensions:number('--dimensions',3,2,3)},opts['--graph']?readJson(opts['--graph']):model.graph);while(!model.stepLayout( model.layoutSerial,8)){};}
model.simulation=!opts['--no-demo'];model.configure({fps:clock.fps,motion:!opts['--read-mode']});
let consoleOpen=false,latest=null,selection=-1,drag=null,closed=false;
const commands=[
 ['Look left',()=>model.cameraCommand('left')],['Look up',()=>model.cameraCommand('up')],['Look right',()=>model.cameraCommand('right')],
 ['Strafe left',()=>model.cameraCommand('pan-left')],['Look down',()=>model.cameraCommand('down')],['Strafe right',()=>model.cameraCommand('pan-right')],
 ['Forward',()=>model.cameraCommand('forward')],['Back',()=>model.cameraCommand('back')],['Home / frame',()=>model.cameraCommand('reset')],
 ['Zoom in',()=>model.cameraCommand('zoom-in')],['Zoom out',()=>model.cameraCommand('zoom-out')],['Look / orbit',()=>{model.cameraMode=model.cameraMode==='look'?'orbit':'look';}],
 ['Speed -',()=>model.setVelocity(clamp(model.flightSpeed-2,-40,40))],['BRAKE',()=>model.setVelocity(0)],['Speed +',()=>model.setVelocity(clamp(model.flightSpeed+2,-40,40))],
 ['Aim travel',()=>model.aimTravel()],['Arrange 2D',()=>model.beginLayout({dimensions:2})],['Arrange 3D',()=>model.beginLayout({dimensions:3})],
 ['Reveal text',()=>model.playText('show',true)],['Conceal text',()=>model.playText('hide')],['Ignite nova',()=>model.emit(model.width*.5,model.height*.45,'*','nova')],
 ['Minimize',()=>model.workspace.hide(model.workspace.selected,model.motionMs)],['Restore',()=>model.workspace.restore(model.workspace.selected,model.motionMs)],['Roll body',()=>model.workspace.toggleRoll(model.workspace.selected,model.motionMs)],
 ['Maximize',()=>model.workspace.action(model.workspace.selected,'maximize',model.motionMs)],['Fade / unfade',()=>model.workspace.action(model.workspace.selected,'fade',model.motionMs)],['Close to dock',()=>model.workspace.hide(model.workspace.selected,model.motionMs,true)],
];
function overlay(out){
 const f=out.frame,nodes=[];for(let i=0;i<Math.min(f.width,78);i++){const text='CTRL+G CONTROLS  |  ALT+ARROWS CAMERA  |  CTRL+N SCENE  |  CTRL+Q EXIT';if(i>=text.length)break;const k=i*4;f.cells[k]=text.codePointAt(i);f.cells[k+1]=0xbedacb;f.cells[k+2]=0x0d0f17;f.cells[k+3]=0;}
 if(!consoleOpen)return out;
 const width=Math.min(f.width-4,62),height=Math.min(f.height-8,22),x=Math.max(2,f.width-width-2),y=4,columns=width<48?2:3,cellW=Math.floor((width-4)/columns),visible=Math.min(commands.length,Math.floor((height-4)/2)*columns);
 nodes.push({kind:'box',x,y,width,height,bg:0x111521,fg:0x9caccf,bgOpacity:980,fgOpacity:1000,text:'CAMERA / ACTION CONSOLE',style:1});
 const semantics=[];
 for(let i=0;i<visible;i++){const id=24000+i,xx=x+2+(i%columns)*cellW,yy=y+2+Math.floor(i/columns)*2;nodes.push({kind:'button',id,x:xx,y:yy,width:cellW-1,height:2,text:commands[i][0],fg:0xd7d0c5,bg:i===selection?0x365057:0x272c3d,bgOpacity:1000,state:i===selection?1:0});semantics.push({id,label:commands[i][0]});}
 out.frame=engine.paint(f,model.motionMs,nodes);out.semantics=semantics;return out;
}
function present(){latest=overlay(renderer.render(model));writer.present(latest.frame);}
function syncTime(){const now=performance.now();clock.setFps(model.options.fps);if(clock.paused===model.options.motion)clock.setPaused(!model.options.motion,now);model.setTime(clock.sample(now));return now;}
function act(fn){try{syncTime();fn();model.revision++;present();}catch(error){model.notice='INPUT: '+error.message;present();}}
function activate(id){if(id>=24000&&id<24000+commands.length){commands[id-24000][1]();model.notice='ACTION: '+commands[id-24000][0];}else activateAtelier(model,id);}
clock.seek(number('--snapshot',0,0,Number.MAX_SAFE_INTEGER),performance.now());model.setTime(clock.timeMs);model.demoData(0);
if(opts['--snapshot']!==undefined){present();writer.dispose();process.stdout.write('\x1b[0m\n');}
else{
 if(!process.stdin.isTTY||!process.stdout.isTTY){console.error('A TTY is required. Use --snapshot MS for redirected output.');process.exit(2);}
 const input=process.stdin,wasRaw=Boolean(input.isRaw),keys=new PassThrough();readline.emitKeypressEvents(keys);
 const hit=(x,y)=>x>=0&&y>=0&&x<latest.frame.width&&y<latest.frame.height?latest.frame.cells[(Math.floor(y)*latest.frame.width+Math.floor(x))*4+3]:0;
 const router=new TerminalInputRouter(text=>keys.write(text),mouse=>{
  act(()=>{
   if(mouse.button&64){model.cameraCommand(mouse.button&4?(mouse.button&1?'zoom-out':'zoom-in'):(mouse.button&1?'back':'forward'));return;}
   if(!mouse.down){drag=null;return;}
   const id=hit(mouse.x,mouse.y),move=Boolean(mouse.button&32);
   if(move&&drag){const dx=mouse.x-drag.x,dy=mouse.y-drag.y;if(drag.window){const w=model.workspace.get(drag.window);w.x=clamp(w.x+dx,-w.width+12,model.width-12);w.y=clamp(w.y+dy,4,model.height-10);}else if(mouse.button&4)model.camera.pan(-dx*.3,dy*.6);else if(model.cameraMode==='look')model.camera.look(-dx*1.6,-dy*1.7);else model.camera.orbit(-dx*1.6,-dy*1.7);drag.x=mouse.x;drag.y=mouse.y;return;}
   if(move)return;
   if(id){activate(id);if(model.scene==='windows'&&id>=10010&&id<10200&&(id-10000)%10===0)drag={x:mouse.x,y:mouse.y,window:Math.floor((id-10000)/10)};}
   else if(['warp','dag','windows','spatial-menu'].includes(model.scene))drag={x:mouse.x,y:mouse.y,window:0};
   else model.emit(mouse.x,mouse.y,'*',mouse.button&4?'nova':model.options.weatherStyle);
  });
 },()=>keys.emit('keypress','',{name:'escape'}));
 input.setRawMode(true);input.resume();input.on('data',chunk=>router.push(chunk));
 process.stdout.write('\x1b[?1049h\x1b[?25l\x1b[?7l\x1b[?1002h\x1b[?1006h');
 const motionTimer=setInterval(()=>{try{if(model.layoutBusy){if(model.stepLayout(model.layoutSerial,6))present();}if(clock.shouldPaint(performance.now())&&model.options.motion){model.setTime(clock.timeMs);present();}}catch(e){model.notice='RENDER: '+e.message;}},4);
 const dataTimer=setInterval(()=>{if(model.simulation&&!['warp','dag','weather','text','windows','museum','spatial-menu'].includes(model.scene))act(()=>model.demoData(performance.now()));},80);
 function cleanup(code=0){if(closed)return;closed=true;clearInterval(motionTimer);clearInterval(dataTimer);router.dispose();keys.end();writer.dispose();input.setRawMode(wasRaw);input.pause();process.stdout.write('\x1b[0m\x1b[?1006l\x1b[?1002l\x1b[?7h\x1b[?25h\x1b[?1049l',()=>process.exit(code));setTimeout(()=>process.exit(code),400).unref();}
 for(const signal of ['SIGINT','SIGTERM','SIGHUP'])process.on(signal,()=>cleanup());process.stdout.on('error',()=>cleanup(1));process.stdout.on('resize',()=>act(resize));
 keys.on('keypress',(str,key={})=>{
  if(key.ctrl&&['q','c'].includes(key.name)){cleanup();return;}
  act(()=>{
   if(key.ctrl){
    if(key.name==='p')model.configure({motion:!model.options.motion});
    else if(key.name==='g'){consoleOpen=!consoleOpen;selection=-1;}
    else if(key.name==='n'){const i=ATELIER_SCENES.findIndex(s=>s.id===model.scene);model.setScene(ATELIER_SCENES[(i+1)%ATELIER_SCENES.length].id);selection=-1;}
    else if(key.name==='k'){const i=palettes.findIndex(p=>p.id===model.palette.id);model.palette=palettes[(i+1)%palettes.length];}
    else if(key.name==='r')model.playText('show',true);
    else if(key.name==='u')model.playText('hide');
    else if(key.name==='e'){const i=TEXT_EFFECTS.indexOf(model.textConfig.effect);model.configureText({effect:TEXT_EFFECTS[(i+1)%TEXT_EFFECTS.length]});model.playText('show',true);}
    else if(key.name==='o'){const i=WINDOW_EFFECTS.indexOf(model.workspace.options.effect);model.windowConfigure({effect:WINDOW_EFFECTS[(i+1)%WINDOW_EFFECTS.length]});model.notice='WINDOW EFFECT: '+model.workspace.options.effect;}
    else if(key.name==='b')model.emit(model.width*.5,model.height*.4,'*','nova');
    else if(key.name==='l')model.beginLayout({dimensions:model.layoutConfig.dimensions===2?3:2});
    return;
   }
   if(key.meta){const map={left:'left',right:'right',up:'up',down:'down',w:'forward',s:'back',a:'pan-left',d:'pan-right',q:'roll-left',e:'roll-right',h:'reset',space:'brake'};if(map[key.name])model.cameraCommand(map[key.name]);else if(key.name==='m')model.cameraMode=model.cameraMode==='look'?'orbit':'look';return;}
   if(key.name==='escape'){consoleOpen=false;selection=-1;drag=null;return;}
   if(!consoleOpen&&['nano','pico'].includes(model.scene)){const actions={return:'insert',backspace:'backspace',delete:'delete',left:'left',right:'right',up:'up',down:'down',home:'home',end:'end'};if(actions[key.name]||str&&[...str].length===1&&str!=='\t'){editScratch(model,actions[key.name]||'insert',key.name==='return'?'\n':actions[key.name]?'':str);return;}}
   const available=latest.semantics.filter(s=>!s.disabled);
   if(['tab','up','down'].includes(key.name)&&available.length){selection=(selection+(key.shift||key.name==='up'?-1:1)+available.length)%available.length;model.focusId=available[selection].id;model.notice='FOCUS: '+available[selection].label;if(model.scene==='dag'&&!consoleOpen)activateAtelier(model,model.focusId);}
   else if(key.name==='return'){if(selection>=0&&available[selection])activate(available[selection].id);else model.send();selection=-1;}
   else if(key.name==='backspace')model.backspace();
   else if(key.name==='pageup'||key.name==='pagedown')model.scroll=Math.max(0,model.scroll+(key.name==='pageup'?5:-5));
   else if(key.name==='end')model.scroll=0;
   else if(str&&!str.startsWith('\x1b'))model.input(str);
  });
 });
 present();
}
