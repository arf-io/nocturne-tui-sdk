import fs from 'node:fs';
import vm from 'node:vm';
import crypto from 'node:crypto';
const html=fs.readFileSync(process.argv[2],'utf8');
if(crypto.createHash('sha256').update(html).digest('hex')!=='375c4468c886728bc790b8d8cc3bdddc2a046532a4d792cde190f1b522a66385')throw Error('Original HTML identity');
function between(a,b){let start=html.indexOf(a),end=html.indexOf(b,start);if(start<0||end<0)throw Error(a);return html.slice(start,end);}
const helpers=between('const TAU = Math.PI * 2;','/** An explicit monotonic clock.');
const paint=between('const BRAILLE_BITS =','function createCamera(');
const world=between('const SKY_LIMITS =','/** Art-directed inverse-square')+between('function sampleWorldEvent(','return {SKY_LIMITS,seededUnit,softStep,distanceInk,Projector,WorldStarfield,WORLD_WEATHER,sampleWorldEvent};');
const engine=between('const STUDIO_KINDS =','return {STUDIO_KINDS,StudioEngine};');
const projector=between('class Projector {','/** Deterministic infinite tiling');
const camera=between('const radians =','/** Project to terminal cells');
const painter=between('class EffectPainter {','return {EffectPainter};');
const data=JSON.parse(html.match(/const DATA=(\{.*?\});\s*(?:const|function)/s)[1]);
const bytes=Buffer.from(data.wasm,'base64');
if(crypto.createHash('sha256').update(bytes).digest('hex')!=='aa04c1705a5982b924d420971bfcbc7bbedd49f1ea527a9900531b61b0c92a09')throw Error('Original WASM identity');
const {instance}=await WebAssembly.instantiate(bytes,{});
const wheel=Array.from({length:360},(_,h)=>instance.exports.nsOklchColor(830,1000,h*1000));
instance.exports.nsStageInit();
const context=vm.createContext({requests:JSON.parse(fs.readFileSync(process.argv[3],'utf8')),wheel,native:instance.exports,schema:data.schema});
vm.runInContext("const StudioEngine=(()=>{"+engine+";return StudioEngine;})();"+helpers+paint+world+camera+projector+painter+`
const engine=new StudioEngine(native,schema),actualSample=sampleWorldEvent;
function rotate(v,degrees){const [x,y,z]=degrees.map(a=>a*Math.PI/180);let q={x:v.x,y:v.y*Math.cos(x)-v.z*Math.sin(x),z:v.y*Math.sin(x)+v.z*Math.cos(x)};q={x:q.x*Math.cos(y)+q.z*Math.sin(y),y:q.y,z:-q.x*Math.sin(y)+q.z*Math.cos(y)};return {x:q.x*Math.cos(z)-q.y*Math.sin(z),y:q.x*Math.sin(z)+q.y*Math.cos(z),z:-q.z};}
result=requests.map(c=>{
 const frame={width:c.width,height:c.height,cells:Uint32Array.from(c.cells)},o=c.options;
 const camera={...c.camera,z:-c.camera.z,fov:2*Math.atan(c.width/(2*c.height)*Math.tan(c.camera.fov*Math.PI/360))*180/Math.PI};
 const p=new Projector(camera,c.width,c.height),event={id:1,backend:'world',kind:c.kind,seed:o.seed??2030,lifeMs:o.lifeMs??5000,atMs:0,space:'world',origin:{x:c.origin[0],y:c.origin[1],z:-c.origin[2]},right:rotate({x:1,y:0,z:0},c.orientation),up:rotate({x:0,y:1,z:0},c.orientation),unitsPerCell:o.scale??1,particles:{gravity:o.gravity??2.6}};
 // The actual application fixes count=160/scale=.65. This adapter passes the
 // retained public authored controls at the sampler input boundary only.
 sampleWorldEvent=(e,t,n,g)=>actualSample({...e,scale:o.scale??1},t,o.count??64,g);
 const painter=Object.create(EffectPainter.prototype);painter.engine=engine;
 const model={camera:{snapshot:()=>camera},effectShelf:{events:[event]},motionMs:c.timeMs,effective:()=>({})};
 painter.paint(frame,model,h=>wheel[((Math.round(h)%360)+360)%360]);
 const projected=[];
 if(c.kind!=='ripples')for(const q of sampleWorldEvent({...event,position:event.origin},c.timeMs,0,event.particles.gravity)){if(!q.previous)continue;const a=p.project(q.previous),b=p.project(q);if(a&&b)projected.push([a.x,a.y,a.z,b.x,b.y,b.z]);}
 return {cells:Array.from(frame.cells),projected};
});`,context);
process.stdout.write(JSON.stringify(context.result));
