import fs from 'node:fs';import vm from 'node:vm';import crypto from 'node:crypto';
const html=fs.readFileSync(process.argv[2],'utf8');
if(crypto.createHash('sha256').update(html).digest('hex')!=='375c4468c886728bc790b8d8cc3bdddc2a046532a4d792cde190f1b522a66385')throw Error('original HTML identity');
function between(a,b){const i=html.indexOf(a),j=html.indexOf(b,i);if(i<0||j<0)throw Error(a);return html.slice(i,j);}
const helpers=between('const TAU = Math.PI * 2;','/** An explicit monotonic clock.');
const paint=between('const BRAILLE_BITS =','function createCamera(');
const particles=between('const DEFAULT_PARTICLE_OPTIONS =','return {DEFAULT_PARTICLE_OPTIONS,PARTICLE_CONTROLS,validateParticleOptions,sampleEmber,sampleWeather};');
const obs=between('class ObservatoryRenderer {','return {TAU,');
const kinetic=between('class KineticRenderer {','return {KineticRenderer,hitKinetic,activateKinetic};');
const atelier=between('const ATELIER_BURST_DEFAULTS =','return {ATELIER_BURST_DEFAULTS,ATELIER_BURST_RANGES,atelierBurstOptions,sampleAtelierBurst};');
const painter=between('class EffectPainter {','return {EffectPainter};');
const engine=between('const STUDIO_KINDS =','return {STUDIO_KINDS,StudioEngine};');
const data=JSON.parse(html.match(/const DATA=(\{.*?\});\s*(?:const|function)/s)[1]);const bytes=Buffer.from(data.wasm,'base64');
if(crypto.createHash('sha256').update(bytes).digest('hex')!=='aa04c1705a5982b924d420971bfcbc7bbedd49f1ea527a9900531b61b0c92a09')throw Error('original WASM identity');
const native=(await WebAssembly.instantiate(bytes,{})).instance.exports;native.nsStageInit();
const wheel=Array.from({length:360},(_,h)=>native.nsOklchColor(830,1000,h*1000));
const context=vm.createContext({requests:JSON.parse(fs.readFileSync(process.argv[3],'utf8')),wheel,native,schema:data.schema});
vm.runInContext('const StudioEngine=(()=>{'+engine+';return StudioEngine;})();'+helpers+paint+particles+obs+kinetic+atelier+painter+`
const engine=new StudioEngine(native,schema),renderer=new EffectPainter(engine);
// Same actual original weather methods with the exact original WASM color wheel.
// Palette setup is already executed above; no substitute weather/geometry renderer.
renderer.original.wheel=wheel;renderer.kinetic.base.wheel=wheel;
renderer.original.paintWeatherLayer=(f,m,o)=>renderer.original.weather(f,m,o);
renderer.kinetic.paintWeatherLayer=(f,m,o)=>renderer.kinetic.weather(f,m,o);
const defaults=engine.defaults.bind(engine),render=engine.render.bind(engine),sampleAtelier=sampleAtelierBurst;
result=requests.map(c=>{
 const controls=c.controls||{};
 engine.defaults=o=>defaults({...o,...(controls.speed===undefined?{}:{rippleSpeed:Math.round(controls.speed*256)}),...(controls.width===undefined?{}:{rippleWidth:Math.round(controls.width*256)}),...(controls.rings===undefined?{}:{rippleRings:controls.rings})});
 engine.render=(cfg,t,nodes,events)=>render(cfg,t,nodes,events.map(e=>({...e,strength:Math.round((controls.strength??1)*1000)})));
 renderer.original.paintWeatherLayer=(f,m,o)=>renderer.original.weather(f,m,{...o,weatherIntensity:controls.strength??.6});
 sampleAtelierBurst=(e,t,o)=>sampleAtelier(e,t,{...o,speed:controls.speed??20,intensity:controls.strength??.8});
 const frame={width:c.width,height:c.height,cells:Uint32Array.from(c.cells)};
 const e={backend:c.backend,kind:'ripples',id:c.eventId,seed:c.seed,lifeMs:c.lifeMs,atMs:0,space:'screen',origin:{x:c.x,y:c.y},particles:validateParticleOptions({lifeMs:c.lifeMs,seed:c.seed,explosionForce:controls.speed??48,brightness:controls.strength??.85})};
 renderer.local(frame,{motionMs:c.timeMs,effective:()=>({weatherSpeed:controls.speed??12})},null,e,h=>wheel[((Math.round(h)%360)+360)%360]);
 return {cells:Array.from(frame.cells)};
});`,context);
process.stdout.write(JSON.stringify(context.result));
