import fs from 'node:fs';
import vm from 'node:vm';
import crypto from 'node:crypto';
const html=fs.readFileSync(process.argv[2],'utf8');
if(crypto.createHash('sha256').update(html).digest('hex')!=='375c4468c886728bc790b8d8cc3bdddc2a046532a4d792cde190f1b522a66385')throw Error('Original HTML identity');
function between(a,b){let start=html.indexOf(a),end=html.indexOf(b,start);if(start<0||end<0)throw Error(a);return html.slice(start,end);}
const helpers=between('const TAU = Math.PI * 2;','/** An explicit monotonic clock.');
const paint=between('const BRAILLE_BITS =','function createCamera(');
const engine=between('const STUDIO_KINDS =','return {STUDIO_KINDS,StudioEngine};');
const painter=between('class EffectPainter {','return {EffectPainter};');
const data=JSON.parse(html.match(/const DATA=(\{.*?\});\s*(?:const|function)/s)[1]);
const bytes=Buffer.from(data.wasm,'base64');
if(crypto.createHash('sha256').update(bytes).digest('hex')!=='aa04c1705a5982b924d420971bfcbc7bbedd49f1ea527a9900531b61b0c92a09')throw Error('Original WASM identity');
const {instance}=await WebAssembly.instantiate(bytes,{});
const wheel=Array.from({length:360},(_,h)=>instance.exports.nsOklchColor(830,1000,h*1000));
instance.exports.nsStageInit();
const context=vm.createContext({requests:JSON.parse(fs.readFileSync(process.argv[3],'utf8')),native:instance.exports,schema:data.schema});
vm.runInContext("const StudioEngine=(()=>{"+engine+";return StudioEngine;})();"+helpers+paint+painter+`
const engine=new StudioEngine(native,schema);
const defaults=engine.defaults.bind(engine),render=engine.render.bind(engine);
result=requests.map(c=>{
 const frame={width:c.width,height:c.height,cells:Uint32Array.from(c.cells)},o=c.options;
 engine.defaults=overrides=>{
  const cfg=defaults({...overrides,novaDurationMs:o.novaDurationMs??3600,rippleSpeed:o.rippleSpeed??2560,rippleWidth:o.rippleWidth??384,rippleOpacity:o.rippleOpacity??280,rippleRings:o.rippleRings??2,cellAspect:o.cellAspect??2000,scale:o.waveScale??6144});
  if(o.palette)cfg.palette=o.palette;if(o.starPalette)cfg.starPalette=o.starPalette;if(o.glyphs)cfg.novaGlyphs=[...o.glyphs];return cfg;
 };
 engine.render=(cfg,t,nodes,events)=>render(cfg,t,nodes,events.map(e=>({...e,strength:o.strength??850})));
 const event={backend:'studio',kind:'nova',id:o.seed??2030,lifeMs:o.novaDurationMs??3600,atMs:0,space:'screen',origin:{x:c.center[0],y:c.center[1]}};
 EffectPainter.prototype.local.call({engine},frame,{motionMs:c.timeMs,effective:()=>({})},null,event,()=>0);
 return {cells:Array.from(frame.cells)};
});`,context);
process.stdout.write(JSON.stringify(context.result));
