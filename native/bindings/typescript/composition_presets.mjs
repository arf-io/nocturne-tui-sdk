import {projectFromCommands,placeComponent,validateProject} from './composition_project.mjs';
/** Ready projects assembled from native renderers; factories never share mutable state. */
const C={paper:0xe4dfcf,muted:0x9aa9b5,mint:0x86d5c0,copper:0xe7ad73,navy:0x101a26,ink:0x0b121c};
const detail={waveHeight:358/256,wavelength:34,windAngle:22,crossSwell:.48,choppiness:.43,foam:.62,waveSpeed:1,joinRiver:1};
function element(kind,id,name,x,y,width,height,props={},appearance={}){
 const e=placeComponent(kind,id,x,y);e.name=name;e.geometry={x,y,width,height};e.props={...e.props,...props};e.appearance=appearance;return e;
}
const text=(id,label,x,y,width,color=C.paper)=>element('text',id,label,x,y,width,1,{text:label,padding:0,border:'none'},{foreground:color,background:C.navy});
const panel=(id,x,y,width,height)=>element('box',id,'Panel',x,y,width,height,{text:'',padding:0},{foreground:C.muted,background:C.navy,opacity:.92,border:'rounded'});
function world(scene,name,seed,timeUs=650000){
 const p=projectFromCommands([
  {op:'environment',presentation:'canvas',style:'solid',stars:0,background:C.ink,sampling:'braille'},
  {op:'scene-art',scene,width:120,height:40,timeMs:null,controls:{cameraX:-68,cameraY:scene==='pearl-cascade'?58:48,cameraZ:-96,yaw:35,pitch:-22,roll:0,fov:62,projection:1,span:scene==='pearl-cascade'?170:220,flow:1,travel:0,seed,redshift:.8,discTilt:12,detail:1,waterAlpha:.94,background:C.ink,sampling:1},detail},
  {op:'camera',profile:'original',navigation:'orbit',target:[0,0,0]}
 ],{name,seed,width:120,height:40,timeUs});
 p.background=C.ink;p.prompt={active:true,mode:'grow',minRows:2,maxRows:3,border:'rounded',padding:1,alpha:.92,text:'',appearance:{cursor:{shape:'bar',color:'#86d5c0',blinkMs:700,duty:.65},weather:{style:'ripples',intensity:.8,lifeMs:1400,speed:14,paste:'burst'}}};
 return p;
}
function signalDesk(){
 const p=world('pearl-cascade','Signal Desk',417);
 p.prompt.text='Send a message to the relay…';
 const chart=element('line',11,'Signal history',6,9,58,12,{text:'',padding:0,border:'none',data:[.12,.24,.18,.46,.37,.7,.58,.83,.72,.94,.65,.8],revealMs:1300},{foreground:C.mint,background:C.navy});
 const wait=element('stage-component',16,'Reception',6,32,55,1,{stageKind:'rule',text:'',style:8,fg:C.mint,bg:C.ink,bgOpacity:0,colorAnimation:1,hueBase:150,hueSpeed:24});
 const action=element('button',20,'Acknowledge',83,31,28,3,{text:'ACKNOWLEDGE',padding:0},{foreground:C.copper,background:C.navy,border:'rounded'});
 action.events.activate=[{op:'widget',id:20,active:true,text:'ACKNOWLEDGED'},{op:'widget',id:18,text:'RELAY ACKNOWLEDGED'},{op:'draft',text:'Acknowledged. Standing by.',emitWeather:true}];
 p.elements=[
  panel(1,2,1,116,4),text(2,'SIGNAL DESK',5,2,42,C.mint),text(3,'NORTH RELAY  /  07:42',82,2,32,C.muted),
  panel(4,3,6,64,25),text(5,'RECEIVED SIGNAL',6,7,58,C.muted),chart,
  element('bars',12,'Channel levels',6,23,58,6,{text:'',padding:0,border:'none',data:[.3,.65,.88,.52,.71,.92,.43,.68],revealMs:900},{foreground:C.copper,background:C.navy}),
  panel(6,77,6,38,23),text(7,'LINK QUALITY',81,7,30,C.muted),
  element('donut',13,'Link distribution',81,9,30,11,{text:'',padding:0,border:'none',data:[61,24,15],innerRadius:.63,revealMs:1500},{foreground:C.mint,background:C.navy}),
  element('digits',14,'Link score',87,20,18,4,{text:'',value:87,min:0,max:100,padding:0,border:'none'},{foreground:C.paper,background:C.navy}),
  text(18,'RECEIVING / CHANNEL 04',80,26,33,C.mint),wait,action
 ];
 p.timeline=[
  {timeUs:1400000,command:{op:'widget',id:11,data:[.3,.35,.52,.4,.68,.55,.83,.74,.91,.78,.63,.88],replay:true}},
  {timeUs:2500000,command:{op:'widget',id:12,data:[.44,.72,.92,.58,.81,.75,.56,.83],replay:true}},
  {timeUs:3200000,command:{op:'widget',id:11,data:[.22,.41,.38,.65,.54,.84,.7,.92,.66,.81,.74,.96],replay:true}}
 ];return validateProject(p);
}
function flightDeck(){
 const p=world('copper-causeway','Flight Deck',281,800000);
 p.commands.push(
  {op:'camera',profile:'original',position:[0,18,98],yaw:0,pitch:-7,roll:0,orthographic:false,fov:65,near:.1,far:20000,navigation:'fly'},
  {op:'environment',starProfile:'source',worldSeed:281,skyDensity:12,skyRadius:280,skyExposure:9000,trailMs:180,textLightness:.83,textChroma:.1},
  {op:'flight',profile:'original',steps:[{kind:'cruise',durationMs:8000,speed:8},{kind:'turn',durationMs:8000,speed:8,yaw:-28,bank:18},{kind:'climb',durationMs:6000,speed:6,pitch:12},{kind:'cruise',durationMs:10000,speed:6}]},
  {op:'camera-controls',rig:'spacecraft',mode:'fly',inputTarget:'head'}
 );
 p.prompt.text='Course correction…';p.prompt.appearance.weather={style:'sparks',intensity:1,lifeMs:1500,speed:16,paste:'each'};
 const brake=element('button',20,'Take control',6,30,30,3,{text:'TAKE CONTROL',padding:0},{foreground:C.copper,background:C.navy,border:'rounded'});
 brake.events.activate=[{op:'brake'},{op:'widget',id:20,active:true,text:'MANUAL CONTROL'},{op:'widget',id:6,text:'HEADING / MANUAL'},{op:'draft',text:'Manual control engaged.',emitWeather:true}];
 p.elements=[
  panel(1,2,1,116,4),text(2,'FLIGHT DECK',5,2,46,C.mint),text(3,'COPPER APPROACH  /  01',81,2,32,C.muted),
  panel(4,3,7,37,19),text(5,'NAVIGATION',6,8,30,C.muted),text(6,'HEADING / AUTOMATIC',6,11,30,C.mint),
  element('digits',7,'Cruise speed',7,14,26,5,{text:'',value:8,min:0,max:100,padding:0,border:'none'},{foreground:C.paper,background:C.navy}),
  text(8,'WORLD UNITS / SECOND',6,20,30,C.muted),
  element('progress',9,'Flight progress',6,23,30,1,{text:'',padding:0,border:'none',value:24,min:0,max:100},{foreground:C.copper,background:C.navy}),
  element('window',10,'Flight plan',72,7,42,18,{title:'ROUTE / COPPER',text:'01  CRUISE\n02  BANK LEFT\n03  CLIMB\n04  HOLD HEADING\n\nSECTOR 281\nDrag to look around.',alpha:.9,durationMs:700,effect:'window-transition/glass-dissolve',yaw:-6,padding:1},{foreground:C.mint}),
  element('indicator',11,'Navigation pulse',6,27,2,1,{stepMs:110},{foreground:C.mint}),
  text(12,'FLIGHT PLAN ACTIVE',10,27,30,C.mint),brake
 ];
 p.timeline=[{timeUs:1800000,command:{op:'widget',id:9,value:42}},{timeUs:4000000,command:{op:'widget',id:9,value:66}},{timeUs:8000000,command:{op:'widget',id:6,text:'HEADING / BANK LEFT'}}];
 return validateProject(p);
}
function tidalConsole(){
 const p=world('tidal-glass','Tidal Console',913,900000);
 p.commands.push({op:'layout',dimensions:2,mode:'layered'},{op:'camera',profile:'original',position:[0,34,120],yaw:0,pitch:-16,roll:0,orthographic:true,span:150});
 p.prompt.text='Describe the next survey…';p.prompt.appearance.weather.style='rain';
 const swell=element('button',20,'Winter swell',82,31,30,3,{text:'WINTER SWELL',padding:0},{foreground:C.copper,background:C.navy,border:'rounded'});
 swell.events.activate=[{op:'widget',id:20,active:true,text:'SWELL ACTIVE'},{op:'scene-art',detail:{waveHeight:3.1,wavelength:19,windAngle:42,crossSwell:.82,choppiness:.8,foam:.9,waveSpeed:1.25}},{op:'draft',text:'Winter swell survey.',emitWeather:true}];
 p.elements=[
  panel(1,2,1,116,4),text(2,'TIDAL CONSOLE',5,2,46,C.mint),text(3,'SURVEY 913  /  OPEN WATER',79,2,35,C.muted),
  panel(4,3,7,40,21),text(5,'SWELL ENERGY',6,8,34,C.muted),
  element('line',6,'Wave spectrum',6,11,34,10,{text:'',padding:0,border:'none',data:[.1,.22,.48,.78,.92,.69,.41,.27,.15],revealMs:1800},{foreground:C.mint,background:C.navy}),
  text(7,'WIND 22°   FOAM 62%',6,24,34,C.copper),
  element('graph-node',10,'Buoy A',66,7,20,4,{label:'BUOY A',detail:'',color:C.mint,padding:1}),
  element('graph-node',11,'Buoy B',97,12,20,4,{label:'BUOY B',detail:'',color:C.copper,padding:1}),
  element('window',12,'Survey log',69,22,42,8,{title:'SURVEY LOG',text:'A  North buoy online\nB  East buoy online\n\nCurrent: cross swell\nSampling: continuous',alpha:.88,yaw:-8,padding:1}),
  element('indicator',13,'Sampling pulse',6,31,2,1,{stepMs:90},{foreground:C.mint}),
  text(14,'SAMPLING THE SURFACE',10,31,40,C.mint),swell
 ];
 p.timeline=[{timeUs:0,command:{op:'edge',from:10,to:11,kind:'reference'}},{timeUs:1600000,command:{op:'widget',id:6,data:[.13,.29,.61,.87,.75,.53,.35,.18,.12],replay:true}}];
 return validateProject(p);
}
export const PROJECT_PRESETS=Object.freeze([
 Object.freeze({id:'signal-desk',name:'Signal Desk',create:signalDesk}),
 Object.freeze({id:'flight-deck',name:'Flight Deck',create:flightDeck}),
 Object.freeze({id:'tidal-console',name:'Tidal Console',create:tidalConsole})
]);
export function createPreset(id){
 const preset=PROJECT_PRESETS.find(p=>p.id===id);if(!preset)throw new RangeError('Unknown project preset: '+id);
 return preset.create();
}
