/** Nocturne Spatial Atelier: direct controls, graph layout, typography, kinetic
 * weather and recoverable shaped windows. Host owns clocks, input and output.
 * These high-level modules are TypeScript; the shared native/WASM kernel still
 * supplies cells, widgets, OKLCh conversion and frame composition.
 */
import {safeCellCodepoint} from './cell_profile.js';
import {StudioEngine,StudioFrame,StudioNode} from './studio.js';
import {ObservatoryModel,ObservatoryRenderer,ObservatoryFrame,OBSERVATORY_SCENES,ObservatoryOptions,RateTimeline,clamp,finite,randomAt,smooth,rgb,mixColor,putCell,putDot,drawSegment,PaletteSpec,activateObservatory} from './observatory.js';
import {CameraRig,Graph,GraphLayout,GraphLayoutJob,LayoutOptions,DEFAULT_LAYOUT_OPTIONS,layoutGraph,layoutOptions,validateGraph,idHash} from './spatial.js';
import {TextPlayer,TextOptions,DEFAULT_TEXT_OPTIONS,sampleText,textDuration,textOptions} from './text_fx.js';
import {ParticleOptions,DEFAULT_PARTICLE_OPTIONS,particleOptions,sampleBurst} from './particles.js';
import {ManagedWindow,WindowManager,WindowOptions,WindowShape,WindowAction,windowMask,warpWindowCell} from './window_fx.js';
export const ATELIER_VERSION='0.5.0';
export const ATELIER_SCENES:{id:string;name:string;detail?:string}[]=[{id:'warp',name:'Oblique Hyperlane',detail:'Fly, look, strafe, brake. The camera is yours.'},{id:'dag',name:'Graph Observatory',detail:'Automatic 2D / 3D layout with shared node identity.'},{id:'weather',name:'Electrical Garden',detail:'Nova ejecta, electrical forks, rising and falling embers.'},{id:'text',name:'Typography Foundry',detail:'Reveal / conceal with independent per-character choreography.'},{id:'windows',name:'Impossible Windows',detail:'Spatial glass, shaped surfaces, large tools and a recovery dock.'},{id:'museum',name:'Motion Cabinet',detail:'A shelf of original text and window compositions.'},...OBSERVATORY_SCENES.filter(s=>!['warp','dag','windows','text'].includes(s.id))];
export const DEFAULT_GRAPH:Graph={nodes:[{id:'operator',label:'OPERATOR'},{id:'planner',label:'ATLAS / PLAN'},{id:'research',label:'IRIS / EVIDENCE'},{id:'memory',label:'MEMORY'},{id:'tools',label:'TOOLCHAIN'},{id:'evidence',label:'SOURCES'},{id:'synthesis',label:'PEARL / SYNTHESIS'},{id:'archive',label:'ARCHIVE'}],edges:[['operator','planner'],['operator','research'],['planner','memory'],['planner','tools'],['research','tools'],['research','evidence'],['memory','synthesis'],['tools','synthesis'],['evidence','synthesis'],['synthesis','archive'],['memory','archive']].map(([source,target])=>({source,target}))};
export class AtelierModel extends ObservatoryModel {
 readonly camera=new CameraRig();workspace=new WindowManager();layout:GraphLayout;graph:Graph=validateGraph(DEFAULT_GRAPH);layoutConfig:LayoutOptions=layoutOptions();layoutJob:GraphLayoutJob|null=null;layoutSerial=0;private layoutFrom:GraphLayout|null=null;private layoutAt=0;
 selectedNode='synthesis';textValue='THE TERMINAL IS A PLACE, NOT A PRINT OUT';textConfig:TextOptions=textOptions();textPlayer:TextPlayer;particleConfig:ParticleOptions=particleOptions();textPhase:'show'|'hide'='show';textStarted=0;
 private lastTimelineEdit=0;
 private forkTimelines():void{if(this.motionMs<this.lastTimelineEdit){for(const timeline of [this.travel,this.warpTravel,this.orbit,this.orbit2,this.flightX,this.flightY,this.flightZ])timeline.fork(this.motionMs);}this.lastTimelineEdit=this.motionMs;}
 override routeRates(atMs:number):void{this.forkTimelines();super.routeRates(atMs);}
 recipe='hyperlane';flightSpeed=5;private flightX=new RateTimeline(0);private flightY=new RateTimeline(0);private flightZ=new RateTimeline(5);layoutBusy=false;cameraMode:'orbit'|'look'='look';windowMotion='show';
 constructor(){super();this.layout=layoutGraph(this.graph);this.textPlayer=new TextPlayer(this.textValue,this.textConfig);this.textPlayer.show(0);
  this.workspace.add({title:'PEARL / SIGNAL',x:5,y:9,width:52,height:23,shape:'rounded'});this.workspace.add({title:'ATLAS / OPS',x:54,y:15,width:56,height:21,shape:'hexagon',depth:5});this.workspace.add({title:'IRIS / ARCHIVE',x:86,y:7,width:42,height:18,shape:'ellipse',depth:14});this.workspace.focus(1);
  this.scene='warp';this.configure({backgroundStyle:'warp',brightness:.12,starDensity:.024,starCount:1100,trailMs:180,travelYaw:22,travelPitch:-8,weatherStyle:'sparks',novaRegularity:0});this.camera.distance=38;this.setVelocity(18);
 }
 override configure(patch:Record<string,unknown>):void{if(this.flightX)this.forkTimelines();super.configure(patch);if(this.flightX&&('travelYaw' in patch||'travelPitch' in patch||'starSpeed'in patch)){if('starSpeed'in patch)this.flightSpeed=this.options.starSpeed;this.updateFlight();}}
 private updateFlight():void{this.forkTimelines();const yaw=this.options.travelYaw*Math.PI/180,pitch=this.options.travelPitch*Math.PI/180,v=this.flightSpeed;this.flightX.set(this.motionMs,Math.sin(yaw)*Math.cos(pitch)*v);this.flightY.set(this.motionMs,Math.sin(pitch)*v);this.flightZ.set(this.motionMs,Math.cos(yaw)*Math.cos(pitch)*v);}
 setVelocity(speed:number):void{this.flightSpeed=finite(speed,-40,40,'flight velocity');this.updateFlight();this.revision++;}
 flightPosition(){return {x:this.flightX.at(this.motionMs),y:this.flightY.at(this.motionMs),z:this.flightZ.at(this.motionMs)};}
 aimTravel():void{this.configure({travelYaw:this.camera.yaw,travelPitch:this.camera.pitch});this.notice='Travel direction now follows the camera. Looking elsewhere does not silently turn the ship.';}
 override setScene(scene:string):void{if(!ATELIER_SCENES.some(s=>s.id===scene))throw new RangeError('Unknown Atelier scene');this.scene=scene;this.cameraMode=scene==='warp'?'look':'orbit';this.camera.reset();
  if(scene==='dag')this.frameGraph();if(scene==='windows'){this.camera.distance=this.width/(2*Math.tan(this.camera.fov*Math.PI/360));this.configure({backgroundStyle:'double-axis',brightness:.16});}
  if(scene==='warp')this.configure({backgroundStyle:'warp'});else if(this.options.backgroundStyle==='warp')this.configure({backgroundStyle:'double-axis'});
  this.selected=0;this.focusId=0;this.notice=ATELIER_SCENES.find(s=>s.id===scene)!.detail??'Interactive original study';this.revision++;
 }
 override resize(w:number,h:number):void{const old=this.width;super.resize(w,h);this.workspace.viewport={width:w,height:h};if(this.scene==='windows'&&old)this.camera.distance*=w/old;}
 cameraCommand(command:string,amount=1):void{finite(amount,-1000,1000,'camera amount');const rotate=(x:number,y:number)=>this.cameraMode==='look'?this.camera.look(x,y):this.camera.orbit(x,y);
  const commands:Record<string,()=>void>={left:()=>rotate(-5*amount,0),right:()=>rotate(5*amount,0),up:()=>rotate(0,5*amount),down:()=>rotate(0,-5*amount),'pan-left':()=>this.camera.pan(-amount,0),'pan-right':()=>this.camera.pan(amount,0),'pan-up':()=>this.camera.pan(0,amount),'pan-down':()=>this.camera.pan(0,-amount),forward:()=>this.camera.pan(0,0,amount),back:()=>this.camera.pan(0,0,-amount),'zoom-in':()=>this.camera.dolly(.9**amount),'zoom-out':()=>this.camera.dolly((1/.9)**amount),'roll-left':()=>{this.camera.roll=clamp(this.camera.roll-5*amount,-180,180);},'roll-right':()=>{this.camera.roll=clamp(this.camera.roll+5*amount,-180,180);},reset:()=>{this.camera.reset();if(this.scene==='dag')this.frameGraph();if(this.scene==='windows')this.camera.distance=this.width/(2*Math.tan(this.camera.fov*Math.PI/360));},frame:()=>{if(this.scene==='dag')this.frameGraph();else this.cameraCommand('reset');},xy:()=>{this.camera.yaw=0;this.camera.pitch=0;this.camera.roll=0;},xz:()=>{this.camera.yaw=0;this.camera.pitch=85;this.camera.roll=0;},yz:()=>{this.camera.yaw=90;this.camera.pitch=0;this.camera.roll=0;},brake:()=>this.setVelocity(0),aim:()=>this.aimTravel()};if(!commands[command])throw new RangeError('Unknown camera command');commands[command]();this.revision++;
 }
 frameGraph():void{this.camera.fit(this.layout.bounds,Math.max(36,this.width-34),Math.max(14,this.height-14));}
 beginLayout(patch:Partial<LayoutOptions>={},graph:Graph=this.graph):number{const next=layoutOptions({...this.layoutConfig,...patch}),job=new GraphLayoutJob(graph,next);this.layoutConfig=next;this.graph=validateGraph(graph);this.layoutJob=job;this.layoutSerial++;this.layoutBusy=!job.done;if(job.done)this.commitLayout();this.revision++;return this.layoutSerial;}
 stepLayout(serial=this.layoutSerial,budget=8):boolean{if(serial!==this.layoutSerial||!this.layoutJob)return true;if(this.layoutJob.step(budget)){this.commitLayout();return true;}this.revision++;return false;}
 private commitLayout():void{if(!this.layoutJob)return;this.layoutFrom=this.layout;this.layout=this.layoutJob.result();this.layoutAt=this.motionMs;this.layoutJob=null;this.layoutBusy=false;if(!this.layout.nodes.some(n=>n.id===this.selectedNode))this.selectedNode=this.layout.nodes[0]?.id??'';this.frameGraph();this.notice=`${this.layout.nodes.length} nodes / ${this.layout.edges.length} edges / ${this.layout.options.dimensions}D ${this.layout.options.algorithm}. ${this.layout.warnings.join(' ')}`;this.revision++;}
 graphPositions():GraphLayout['nodes']{const p=smooth((this.motionMs-this.layoutAt)/650);if(!this.layoutFrom||p===1)return this.layout.nodes;const prev=new Map(this.layoutFrom.nodes.map(n=>[n.id,n]));return this.layout.nodes.map(n=>{const a=prev.get(n.id);return a?{...n,x:a.x+(n.x-a.x)*p,y:a.y+(n.y-a.y)*p,z:a.z+(n.z-a.z)*p}:n;});}
 configureText(patch:Partial<TextOptions>):void{const next=textOptions({...this.textConfig,...patch});this.textConfig=next;this.textPlayer.configure(next,this.motionMs);this.revision++;}
 playText(phase:'show'|'hide',restart=false):void{if(restart)this.textPlayer=new TextPlayer(this.textValue,this.textConfig);this.textPhase=phase;this.textStarted=this.motionMs;this.textPlayer[phase](this.motionMs);this.revision++;}
 setDisplayText(text:string):void{if(typeof text!=='string'||[...text].length>2048)throw new RangeError('Display text is bounded to 2048 scalars');this.textValue=text;this.textPlayer=new TextPlayer(text,this.textConfig);this.playText('show',true);}
 configureParticles(patch:Partial<ParticleOptions>):void{this.particleConfig=particleOptions({...this.particleConfig,...patch});this.revision++;}
 windowConfigure(patch:Partial<WindowOptions>):void{this.workspace.configure(patch);const w=this.workspace.get(this.workspace.selected);for(const k of ['shape','depth','yaw','pitch','roll'] as const)if(k in patch)(w as unknown as Record<string,unknown>)[k]=patch[k];this.revision++;}
 /** Preserve local notes/edit buffers when applying visual settings. This is
  * not provider/session restoration and does not copy hardware subscriptions. */
 preserveLocalContent(previous:AtelierModel):void{this.draft=previous.draft;this.messages=previous.messages.map(m=>({...m}));this.editor=previous.editor;this.editorCursor=previous.editorCursor;this.scroll=previous.scroll;this.serial=Math.max(this.serial,...this.messages.map(m=>m.id));this.revealThroughMs=Math.max(previous.revealThroughMs,...this.messages.map(m=>m.atMs));}
 override exportState():Record<string,unknown>{return {...super.exportState(),version:5,build:ATELIER_VERSION,camera:this.camera.snapshot(),cameraMode:this.cameraMode,flightSpeed:this.flightSpeed,graph:this.graph,layout:this.layout,textConfig:this.textConfig,textValue:this.textValue,particleConfig:this.particleConfig,windowOptions:this.workspace.options,windows:this.workspace.windows};}
}
export interface AtelierFrame extends ObservatoryFrame {windowHits:{id:number;action:string;x:number;y:number;width:number;height:number}[];visibleNodes:number}
function textCell(frame:StudioFrame,x:number,y:number,value:string,color:number,alpha=1,id=0):void{[...value].forEach((c,i)=>putCell(frame,x+i,y,c.codePointAt(0)!,color,alpha,id));}
function bgCell(f:StudioFrame,x:number,y:number,color:number,alpha=1,id=0){x=Math.floor(x);y=Math.floor(y);if(x<0||y<0||x>=f.width||y>=f.height)return;const i=(y*f.width+x)*4;f.cells[i]=32;f.cells[i+2]=mixColor(f.cells[i+2],color,alpha);f.cells[i+1]=color;f.cells[i+3]=id;}
export type WindowBodyPainter=(body:StudioFrame,timeMs:number,window:Readonly<ManagedWindow>)=>void;
export class AtelierRenderer {
 private bodyPainters=new Map<number,WindowBodyPainter>();
 /** Attach application-owned body content. The callback receives a fresh owned
  * cell surface below the chrome, with inherited colors and explicit time.
  * Do not mutate model state or read a wall clock while painting. Custom hit
  * IDs >=100000 are available to the host's action dispatcher. */
 setWindowPainter(id:number,painter:WindowBodyPainter|null):void{if(!Number.isInteger(id)||id<1||id>12)throw new RangeError('Window ID 1..12');if(painter===null)this.bodyPainters.delete(id);else if(typeof painter==='function')this.bodyPainters.set(id,painter);else throw new TypeError('Window painter function required');}

 readonly base:ObservatoryRenderer;private heatColors=new Map<string,number>();
 private heatColor(kind:string,heat:number):number{const h=Math.round(clamp(heat,0,1)*127),key=kind+':'+h;if(!this.heatColors.has(key)){const q=h/127,c=kind==='embers'?this.engine.oklch(Math.round(520+q*340),1600,Math.round((20+q*42)*1000)):kind==='sparks'?this.engine.oklch(Math.round(690+q*270),600,245000):this.engine.oklch(Math.round(570+q*370),900,Math.round((35+q*45)*1000));this.heatColors.set(key,c);}return this.heatColors.get(key)!;}
 constructor(readonly engine:StudioEngine){this.base=new ObservatoryRenderer(engine);}
 private stars(f:StudioFrame,m:AtelierModel,o:ObservatoryOptions){const glyphs=[...o.starGlyphs];for(let y=4;y<f.height-6;y++)for(let x=0;x<f.width;x++){const seed=idHash(x+':'+y);if(randomAt(seed,0)>o.starDensity)continue;const period=3+randomAt(seed,2)*6,p=(m.motionMs/1000/period+randomAt(seed,3))%1,alpha=Math.sin(p*Math.PI)**8*.7;putCell(f,x,y,glyphs[seed%glyphs.length].codePointAt(0)!,this.base.ink(seed%360),alpha);}}
 private warp(f:StudioFrame,m:AtelierModel,o:ObservatoryOptions):number{
  const project=m.camera.projector(f.width,f.height),offset=m.flightPosition(),eye=m.camera.position(),wrap=(v:number)=>((v%100)+100)%100-50,yaw=o.travelYaw*Math.PI/180,pitch=o.travelPitch*Math.PI/180,expo=m.flightSpeed*o.trailMs/1000,dir={x:Math.sin(yaw)*Math.cos(pitch),y:Math.sin(pitch),z:Math.cos(yaw)*Math.cos(pitch)};let drawn=0;
  for(let j=0;j<o.starCount;j++){const p={x:wrap(randomAt(6141,j*3)*100-offset.x-eye.x)+eye.x,y:wrap(randomAt(6141,j*3+1)*100-offset.y-eye.y)+eye.y,z:wrap(randomAt(6141,j*3+2)*100-offset.z-eye.z)+eye.z};const a=project(p),b=project({x:p.x+dir.x*expo,y:p.y+dir.y*expo,z:p.z+dir.z*expo});if(!a||a.x<0||a.x>=f.width||a.y<4||a.y>=f.height-7)continue;const c=this.base.ink(185+randomAt(741,j)*145),alpha=clamp(1-a.z/100,.28,1);if(b&&o.trailMs>0)drawSegment(f,a.x,a.y,b.x,b.y,c,alpha);else putDot(f,a.x*2,a.y*4,c,alpha);if(a.z<6)putCell(f,a.x,a.y,0x2219,c,alpha);drawn++;}return drawn;
 }
 private particles(f:StudioFrame,m:AtelierModel):number{
  const o=m.particleConfig,events=m.events.filter(e=>e.atMs<=m.motionMs&&m.motionMs-e.atMs<o.lifeMs).slice(-16);const cadence=m.options.novaRegularity;if(cadence>0){const period=60000/cadence,k=Math.floor(m.motionMs/period);for(let i=Math.max(1,k-1);i<=k;i++)if(m.motionMs-i*period<o.lifeMs)events.push({id:900000+i,kind:'nova',x:10+randomAt(1,i)*(f.width-20),y:8+randomAt(3,i)*(f.height-20),atMs:i*period,glyph:'✹'});}
  for(const event of events){const b=sampleBurst(event,m.motionMs,o);for(const g of b.glows){const r=Math.min(120,g.radius),c=this.engine.oklch(Math.round(660+g.heat*280),700,Math.round((25+g.heat*45)*1000));for(let y=Math.max(4,Math.floor(g.y-r/2-2));y<Math.min(f.height-7,g.y+r/2+2);y++)for(let x=Math.max(0,Math.floor(g.x-r-2));x<Math.min(f.width,g.x+r+2);x++){const d=Math.hypot(x-g.x,(y-g.y)*2),q=g.ring?Math.exp(-(((d-r)/1.1)**2)):Math.exp(-d*d/Math.max(.1,r*r)),i=(y*f.width+x)*4;f.cells[i+2]=mixColor(f.cells[i+2],c,q*g.alpha);if(f.cells[i]===0x2580)f.cells[i+1]=mixColor(f.cells[i+1],c,q*g.alpha);}}
   const color=(heat:number)=>this.heatColor(event.kind,heat);
   for(const p of b.segments)drawSegment(f,p.x1,p.y1,p.x2,p.y2,color(p.heat),p.alpha);
   for(const p of b.points)if(p.y>=4&&p.y<f.height-7)putCell(f,p.x,p.y,p.glyph.codePointAt(0)!,color(p.heat),p.alpha);
  }return events.length;
 }
 private graph(f:StudioFrame,m:AtelierModel,semantics:AtelierFrame['semantics']):number{
  const w=f.width,h=f.height,pw=w>=100?w-34:w-6,ph=h-15,ox=3,oy=6,points=m.graphPositions(),projected=new Map<string,{x:number;y:number;z:number;scale:number}>();
  const project=m.camera.projector(pw,ph);for(const n of points){const p=project(n);if(p)projected.set(n.id,{...p,x:p.x+ox,y:p.y+oy});}
  const highlight=new Set(m.graph.edges.filter(e=>e.source===m.selectedNode||e.target===m.selectedNode).map(e=>e.source+'\0'+e.target));
  for(const e of m.graph.edges){const a=projected.get(e.source),b=projected.get(e.target);if(!a||!b)continue;const hot=highlight.has(e.source+'\0'+e.target),color=this.base.ink(hot?55:205);drawSegment(f,a.x,a.y,b.x,b.y,color,hot?.85:.29);const t=(m.motionMs/1800+randomAt(idHash(e.source+e.target),1))%1;putDot(f,(a.x+(b.x-a.x)*t)*2,(a.y+(b.y-a.y)*t)*4,color,hot?1:.55);}
  let visible=0;const ns:StudioNode[]=[];for(const n of [...points].sort((a,b)=>(projected.get(b.id)?.z??0)-(projected.get(a.id)?.z??0))){const p=projected.get(n.id),index=m.layout.nodes.findIndex(v=>v.id===n.id),id=5000+index;semantics.push({id,label:`${n.label} / ${m.graph.edges.filter(e=>e.target===n.id).length} parents`});if(!p||p.x<ox||p.x>=ox+pw||p.y<oy+1||p.y>=oy+ph-1)continue;visible++;const hot=n.id===m.selectedNode,width=Math.max(5,Math.min(24,Math.round(n.width*p.scale)+3)),x=Math.round(p.x-width/2),y=Math.round(p.y-1),a=Math.round(clamp(1-p.z/250,.5,1)*1000);
   ns.push({kind:'box',id,x,y,width,height:3,text:'',fg:this.base.ink(hot?55:190),bg:hot?0x322d3e:0x171d27,bgOpacity:920,fgOpacity:a,style:hot?2:0});ns.push({kind:'text',id,x:x+1,y:y+1,width:width-2,height:1,text:n.label.length>width-2?n.label.slice(0,Math.max(1,width-3))+'~':n.label,fg:this.base.ink(hot?55:210),fgOpacity:1000});
  }
  const painted=this.engine.paint(f,m.motionMs,ns);f.cells.set(painted.cells);
  if(w>=100){const x=w-28;for(let y=6;y<h-9;y++)bgCell(f,x-1,y,0x10121c,.95);textCell(f,x,7,'NODE INSPECTOR',this.base.ink(290));textCell(f,x,9,m.selectedNode.slice(0,25),this.base.ink(60));const parents=m.graph.edges.filter(e=>e.target===m.selectedNode).map(e=>e.source);textCell(f,x,12,`${parents.length} PARENTS`,this.base.ink(185));parents.slice(0,7).forEach((v,i)=>textCell(f,x,14+i,('← '+v).slice(0,26),this.base.ink(210)));textCell(f,x,h-14,`${m.layout.options.dimensions}D ${m.layout.options.algorithm}`,this.base.ink(60));textCell(f,x,h-12,`${m.layout.cycles.length} CYCLIC GROUPS`,this.base.ink(310));}
  return visible;
 }
 private spatialMenu(f:StudioFrame,m:AtelierModel,semantics:AtelierFrame['semantics']):number{
  const items=[['Pearl Scope','scope'],['Agent Chat','chat'],['Graph Observatory','dag'],['Impossible Windows','windows'],['Typography','text'],['Oblique Hyperlane','warp']];let count=0;
  for(let i=0;i<items.length;i++){const angle=i*Math.PI*2/items.length,p=m.camera.project({x:Math.sin(angle)*18,y:Math.cos(angle)*9,z:Math.cos(angle)*12},f.width,f.height-12);const id=23000+i;semantics.push({id,label:items[i][0]});if(!p)continue;const x=Math.round(p.x-9),y=Math.round(p.y+5);if(x<0||x+19>=f.width||y<5||y+3>=f.height-8)continue;const hot=m.focusId===id,nodes:StudioNode[]=[{kind:'box',id,x,y,width:20,height:3,style:hot?2:0,fg:this.base.ink(55+i*40),bg:hot?0x313345:0x161b26,bgOpacity:900},{kind:'text',id,x:x+1,y:y+1,width:18,height:1,text:items[i][0].slice(0,18),fg:this.base.ink(55+i*40)}];const frame=this.engine.paint(f,m.motionMs,nodes);f.cells.set(frame.cells);count++;}return count;
 }
 private typography(f:StudioFrame,m:AtelierModel,museum=false){
  const top=7,width=f.width-10;if(museum){const studies=[['PRISM WEAVE','prism-weave'],['COMET STITCH','comet-stitch'],['INK TIDE','ink-tide'],['CONSTELLATION','constellation'],['ZIPPER SKY','zipper'],['FLIPBOARD','flipboard']];studies.forEach(([label,effect],i)=>{const col=i%2,row=Math.floor(i/2),x=5+col*Math.floor(width/2),y=top+row*9;this.paintText(f,label,sampleText(label,'show',m.motionMs%6500,{...m.textConfig,effect:effect as TextOptions['effect'],durationMs:1600,staggerMs:40,travelRows:4,spreadColumns:5}),x,y+4,m);textCell(f,x,y,`${String(i+1).padStart(2,'0')} / ${effect}`,this.base.ink(210),.55);});return;}
  textCell(f,5,7,`${m.textConfig.effect.toUpperCase()} / ${m.textPhase.toUpperCase()} / ${textDuration(m.textValue,m.textConfig)} ms total`.slice(0,width),this.base.ink(200),.65);
  const poses=m.textPlayer.sample(m.motionMs),x0=Math.max(5,Math.floor((f.width-Math.min(width,[...m.textValue].length))/2));this.paintText(f,m.textValue,poses,x0,Math.floor(f.height*.5),m);
  textCell(f,5,f.height-13,'DISPLAY CONTENT (unmodified):',this.base.ink(200),.5);textCell(f,5,f.height-11,m.textValue.slice(0,width),rgb(m.palette.ink),.8);
 }
 private paintText(f:StudioFrame,text:string,poses:ReturnType<typeof sampleText>,x0:number,y0:number,m:AtelierModel){const wrap=Math.max(10,f.width-10);for(const p of poses){const row=Math.floor(p.index/wrap),tx=p.x-p.index+(p.index%wrap),ty=p.y+row*3;for(const t of p.trail)if(y0+t.y+row*3>=5&&y0+t.y+row*3<f.height-8)putCell(f,x0+(t.x-p.index+p.index%wrap),y0+t.y+row*3,0xb7,this.base.ink(p.index*m.options.hueStep+p.hueDelta),t.opacity);if(p.opacity>0&&y0+ty>=5&&y0+ty<f.height-8)putCell(f,x0+tx,y0+ty,p.glyph.codePointAt(0)!,this.base.ink(m.options.hueOffset+p.index*m.options.hueStep+m.motionMs*m.options.textHueSpeed/1000+p.hueDelta),p.opacity);}}
 private windows(f:StudioFrame,m:AtelierModel,semantics:AtelierFrame['semantics']):AtelierFrame['windowHits']{
  const manager=m.workspace,o=manager.options,hits:AtelierFrame['windowHits']=[],project=m.camera.projector(f.width,f.height);
  // Far windows first; z-order is a painter's ordering of planar surfaces, not
  // a general solid-geometry depth buffer for intersecting window planes.
  const ordered=[...manager.windows].sort((a,b)=>b.depth-a.depth||a.stack-b.stack);
  for(const window of ordered){const state=manager.sample(window.id,m.motionMs);if(state.visibility<=0)continue;const width=Math.max(30,Math.round(state.width)),height=Math.max(8,Math.round(state.height)),local:StudioFrame={width,height,cells:new Uint32Array(width*height*4)},bodyId=10000+window.id*10;
   for(let y=0;y<height;y++)for(let x=0;x<width;x++){const i=(y*width+x)*4;local.cells[i]=32;local.cells[i+1]=rgb(m.palette.ink);local.cells[i+2]=mixColor(rgb(m.palette.background),this.base.ink(235+window.id*35),.07+y/height*.035);local.cells[i+3]=bodyId;}
   const all=manager.controls(window.id),side=o.chrome==='mac'||o.chrome==='custom'&&o.customSide==='left';for(const tool of all){const x=side?tool.x:Math.max(1,width-1-o.toolWidth*4)+all.indexOf(tool)*o.toolWidth,actionIndex=['minimize','maximize','fade','close'].indexOf(tool.action),id=bodyId+actionIndex+1;for(let y=0;y<tool.height;y++)for(let xx=x;xx<x+tool.width;xx++){bgCell(local,xx,y,tool.color,.22,id);}textCell(local,x+Math.floor(tool.width/2),Math.floor(tool.height/2),tool.glyph,tool.color,1,id);semantics.push({id,label:`${window.title}: ${tool.action}`});}
   textCell(local,Math.max(2,Math.floor(width*.16)),o.toolHeight+1,(window.title+(manager.selected===window.id?' / FOCUSED':'')).slice(0,Math.floor(width*.68)),this.base.ink(190));
   for(let x=2;x<width-2;x++)textCell(local,x,o.toolHeight+3,'─',this.base.ink(230+x*2),.5,bodyId);
   if(window.id===1){for(let k=0;k<width-8;k++){const phase=k*.22+m.motionMs*.0013,y=o.toolHeight+8+Math.sin(phase)*2+Math.sin(k*.67-phase*.6);putDot(local,(4+k)*2,y*4,this.base.ink(170+k*2),.88,bodyId);}textCell(local,4,height-4,'PEARL / 60 Hz PRESENTATION',this.base.ink(180),.9,bodyId);}
   else{['SOURCE     STATE        RATE','atlas      running      67/s','iris       evidence     12/s','pearl      synthesis    49/s',' Shared parents / one identity'].slice(0,Math.max(0,height-9)).forEach((s,i)=>textCell(local,3,o.toolHeight+6+i,s.slice(0,width-6),this.base.ink(190+i*17),.85,bodyId));}
   const painter=this.bodyPainters.get(window.id);if(painter){const bx=2,by=o.toolHeight+5,bw=width-4,bh=Math.max(1,height-by-2),body:StudioFrame={width:bw,height:bh,cells:new Uint32Array(bw*bh*4)};for(let yy=0;yy<bh;yy++)for(let xx=0;xx<bw;xx++){const from=((yy+by)*width+xx+bx)*4,to=(yy*bw+xx)*4;body.cells.set(local.cells.slice(from,from+4),to);body.cells[to]=32;body.cells[to+3]=bodyId;}painter(body,m.motionMs,window);if(body.width!==bw||body.height!==bh||!(body.cells instanceof Uint32Array)||body.cells.length!==bw*bh*4)throw new RangeError('Window painter changed the surface geometry');for(let yy=0;yy<bh;yy++)for(let xx=0;xx<bw;xx++)local.cells.set(body.cells.subarray((yy*bw+xx)*4,(yy*bw+xx+1)*4),((yy+by)*width+xx+bx)*4);}
   const rads=(v:number)=>v*Math.PI/180,cy=Math.cos(rads(state.yaw)),sy=Math.sin(rads(state.yaw)),cp=Math.cos(rads(state.pitch)),sp=Math.sin(rads(state.pitch)),cr=Math.cos(rads(state.roll)),sr=Math.sin(rads(state.roll));
   const map=(u:number,v:number)=>{const rolledV=v<o.toolHeight?v:o.toolHeight+(v-o.toolHeight)*state.bodyScale;const a=warpWindowCell(u,rolledV,width,height,state.visibility,o.effect,o);if(!a)return null;let dx=a.x-width/2,dy=-(a.y-height/2)*2,dz=0;[dx,dz]=[dx*cy+dz*sy,-dx*sy+dz*cy];[dy,dz]=[dy*cp-dz*sp,dy*sp+dz*cp];[dx,dy]=[dx*cr-dy*sr,dx*sr+dy*cr];const center={x:state.x+width/2-f.width/2,y:(f.height/2-state.y-height/2)*2,z:state.depth};const p=project({x:center.x+dx,y:center.y+dy,z:center.z+dz});if(p&&o.effect==='genie'){const index=manager.windows.findIndex(w=>w.id===window.id),dockX=3+(index+.5)*(f.width-6)/manager.windows.length,dockY=f.height-6,anchor=project({x:state.x+width/2-f.width/2,y:(f.height/2-state.y-height)*2,z:state.depth});if(anchor){p.x+=(dockX-anchor.x)*(1-state.visibility);p.y+=(dockY-anchor.y)*(1-state.visibility);}}return p?{...p,alpha:a.alpha}:null;};
   const glyphs:{x:number;y:number;glyph:number;fg:number;alpha:number;id:number}[]=[];
   for(let y=0;y<height;y++)for(let x=0;x<width;x++){
    // The tool strip remains a floating full-width strip for nonrectangular
    // bodies. It is deliberately not clipped out by an ellipse/diamond corner.
    if(state.bodyScale<.015&&y>=o.toolHeight)continue;
    if(y>=o.toolHeight&&!windowMask(window.shape,(x+.5)/width,(y+.5)/height,o.polygon))continue;
    const pos=map(x+.5,y+.5);if(!pos||pos.y<4||pos.y>=f.height-7||pos.x<-3||pos.x>=f.width+3)continue;const i=(y*width+x)*4,id=local.cells[i+3]||bodyId;const alpha=state.alpha*o.opacity*pos.alpha;
    const a=map(x+1.5,y+1.5),sx=a?Math.min(5,Math.abs(a.x-pos.x)):1,syy=a?Math.min(4,Math.abs(a.y-pos.y)):1;for(let yy=Math.floor(pos.y-syy/2+1e-7);yy<=Math.max(Math.floor(pos.y-syy/2+1e-7),Math.ceil(pos.y+syy/2-1e-7)-1);yy++)for(let xx=Math.floor(pos.x-sx/2+1e-7);xx<=Math.max(Math.floor(pos.x-sx/2+1e-7),Math.ceil(pos.x+sx/2-1e-7)-1);xx++){if(yy<4||yy>=f.height-7)continue;bgCell(f,xx,yy,local.cells[i+2],alpha,id);}
    if(local.cells[i]!==32)glyphs.push({x:pos.x,y:pos.y,glyph:local.cells[i],fg:local.cells[i+1],alpha:state.alpha*pos.alpha,id});
   }
   for(const g of glyphs)putCell(f,g.x,g.y,g.glyph,g.fg,g.alpha,g.id);
   semantics.push({id:bodyId,label:`Focus or drag ${window.title}`});
  }
  const tasks=manager.tasks(),slot=Math.max(12,Math.floor((f.width-6)/tasks.length));tasks.forEach((task,i)=>{const x=3+i*slot,y=f.height-7,id=19000+task.id;for(let yy=y;yy<y+2;yy++)for(let xx=x;xx<Math.min(f.width-2,x+slot-1);xx++)bgCell(f,xx,yy,task.selected?0x34464b:0x222230,.97,id);textCell(f,x+1,y,`${task.mode==='normal'?'▣':'▱'} ${task.title}`.slice(0,slot-3),this.base.ink(task.mode==='normal'?185:55),1,id);textCell(f,x+1,y+1,task.mode==='normal'?'FOCUS / RESTORE':task.mode.toUpperCase()+' / RESTORE',this.base.ink(280),.65,id);semantics.push({id,label:`Restore ${task.title} (${task.mode})`});hits.push({id,action:'restore',x,y,width:slot-1,height:2});});return hits;
 }
 render(m:AtelierModel):AtelierFrame{
  const custom=['warp','dag','weather','text','windows','museum','spatial-menu'].includes(m.scene);if(!custom){const out=this.base.render(m);for(let i=0;i<out.frame.cells.length;i+=4)out.frame.cells[i]=safeCellCodepoint(out.frame.cells[i]);return {...out,windowHits:[],visibleNodes:0};}
  const o=m.effective(),f=this.base.background(m,o),semantics:AtelierFrame['semantics']=[],nodes:StudioNode[]=[];let drawnStars=0,visibleNodes=0,windowHits:AtelierFrame['windowHits']=[];
  if(m.scene==='warp')drawnStars=this.warp(f,m,o);else this.stars(f,m,o);const activeWeather=this.particles(f,m);
  if(m.scene==='dag')visibleNodes=this.graph(f,m,semantics);if(m.scene==='spatial-menu')visibleNodes=this.spatialMenu(f,m,semantics);
  if(m.scene==='text'||m.scene==='museum')this.typography(f,m,m.scene==='museum');
  if(m.scene==='windows')windowHits=this.windows(f,m,semantics);
  if(m.scene==='warp'){textCell(f,4,7,'OBLIQUE HYPERLANE',this.base.ink(180));textCell(f,4,9,'DRAG = LOOK     SHIFT+DRAG = STRAFE     WHEEL = MOVE',this.base.ink(245),.72);textCell(f,4,11,`TRAVEL ${m.flightSpeed.toFixed(1)} u/s    HEADING ${o.travelYaw.toFixed(0)}°    ELEVATION ${o.travelPitch.toFixed(0)}°`,this.base.ink(55),.9);const c=m.camera.snapshot();textCell(f,4,f.height-12,`LOOK ${c.yaw.toFixed(0)}° / ${c.pitch.toFixed(0)}°   ROLL ${c.roll.toFixed(0)}°   ${drawnStars} VISIBLE STARS`,this.base.ink(200),.65);}
  if(m.scene==='weather'){textCell(f,5,7,'ELECTRICAL GARDEN / CLICK TO IGNITE',this.base.ink(60));textCell(f,5,9,'Nova = hot core + spokes + ejecta. Sparks = forks. Embers = lift + gravity.',this.base.ink(205),.65);const labels=['nova','sparks','embers'];labels.forEach((label,i)=>{const x=10+i*Math.floor((f.width-20)/3),y=f.height-13,id=22000+i;textCell(f,x,y,'[ '+label.toUpperCase()+' ]',this.base.ink(40+i*95),1,id);semantics.push({id,label:'Trigger '+label});});}
  // Stable, opaque header and local-input plane are drawn last. No reveal path
  // may delay or substitute characters in this draft, even during transitions.
  for(let y=0;y<4;y++)for(let x=0;x<f.width;x++)bgCell(f,x,y,0x0d0f17,1);for(let y=f.height-5;y<f.height;y++)for(let x=0;x<f.width;x++)bgCell(f,x,y,0x10131d,1);
  textCell(f,2,1,'NOCTURNE / SPATIAL ATELIER',this.base.ink(180));if(f.width>100)textCell(f,f.width-54,1,`v${ATELIER_VERSION}   ${Math.round(o.fps)} FPS TARGET   OKLCh`,this.base.ink(285),.85);textCell(f,2,3,(m.notice||ATELIER_SCENES.find(s=>s.id===m.scene)?.detail||'').slice(0,f.width-4),this.base.ink(210),.65);
  const draft=[...m.draft].slice(-Math.max(1,f.width-10));textCell(f,3,f.height-4,'>',this.base.ink(185));draft.forEach((c,i)=>putCell(f,5+i,f.height-4,c.codePointAt(0)!,o.typedColor?this.base.ink(i*o.hueStep+o.hueOffset):rgb(m.palette.ink),1));putCell(f,5+draft.length,f.height-4,0x258f,this.base.ink(180),1);
  textCell(f,3,f.height-2,'INPUT IS IMMEDIATE  /  SPACE pause on stage  /  H home  /  ? controls'.slice(0,f.width-6),this.base.ink(215),.52);
  for(let i=0;i<f.cells.length;i+=4)f.cells[i]=safeCellCodepoint(f.cells[i]);return {frame:f,nodes,semantics,drawnStars,activeWeather,windowHits,visibleNodes};
 }
}
/** Shared activation route for terminal hit IDs and browser companion controls. */
export function activateAtelier(m:AtelierModel,id:number):void{
 if(id>=23000&&id<23006){m.setScene(['scope','chat','dag','windows','text','warp'][id-23000]);return;}
 if(id>=19000&&id<19100){m.workspace.restore(id-19000,m.motionMs);m.revision++;return;}
 if(id>=10000&&id<10200){const wid=Math.floor((id-10000)/10),tool=(id-10000)%10;if(tool>=1&&tool<=4)m.workspace.action(wid,(['minimize','maximize','fade','close'] as WindowAction[])[tool-1],m.motionMs);else m.workspace.focus(wid);m.revision++;return;}
 if(id>=5000&&id<5256&&m.scene==='dag'){m.selectedNode=m.layout.nodes[id-5000]?.id??m.selectedNode;m.revision++;return;}
 if(id>=22000&&id<22003){const kind=['nova','sparks','embers'][id-22000];m.emit(m.width*.5,m.height*.44,'·',kind);m.revision++;return;}
 activateObservatory(m,id);
}
