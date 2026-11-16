import fs from 'node:fs';
import vm from 'node:vm';
import crypto from 'node:crypto';
const html=fs.readFileSync(process.argv[2],'utf8');
if(crypto.createHash('sha256').update(html).digest('hex')!=='375c4468c886728bc790b8d8cc3bdddc2a046532a4d792cde190f1b522a66385')throw Error('Original HTML identity');
function between(a,b){let start=html.indexOf(a),end=html.indexOf(b,start);if(start<0||end<0)throw Error(a);return html.slice(start,end);}
const helpers=between('const TAU = Math.PI * 2;','/** An explicit monotonic clock.');
const paint=between('const BRAILLE_BITS =','function createCamera(');
const engine=between('const STUDIO_KINDS =','return {STUDIO_KINDS,StudioEngine};');
const controls=between('const nc =','/** Atomic options normalization');
const colors=between('function rgbToOklch','const BRAILLE_BITS');
const observatory=between('class ObservatoryRenderer {','const ORBITAL_NODES');
const painter=between('class EffectPainter {','return {EffectPainter};');
const data=JSON.parse(html.match(/const DATA=(\{.*?\});\s*(?:const|function)/s)[1]);
const bytes=Buffer.from(data.wasm,'base64');
if(crypto.createHash('sha256').update(bytes).digest('hex')!=='aa04c1705a5982b924d420971bfcbc7bbedd49f1ea527a9900531b61b0c92a09')throw Error('Original WASM identity');
const {instance}=await WebAssembly.instantiate(bytes,{});
const wheel=Array.from({length:360},(_,h)=>instance.exports.nsOklchColor(830,1000,h*1000));
instance.exports.nsStageInit();
const context=vm.createContext({requests:JSON.parse(fs.readFileSync(process.argv[3],'utf8')),native:instance.exports,schema:data.schema,palette:data.palettes[0]});
vm.runInContext("const StudioEngine=(()=>{"+engine+";return StudioEngine;})();"+helpers+paint+controls+colors+observatory+painter+`
const engine=new StudioEngine(native,schema),original=new ObservatoryRenderer(engine),layer=original.paintWeatherLayer.bind(original);
result=requests.map(c=>{
 const frame={width:c.width,height:c.height,cells:Uint32Array.from(c.cells)},o=c.options;
 original.paintWeatherLayer=(f,m,options)=>layer(f,m,{...options,weatherSpeed:o.speed??12,weatherIntensity:o.intensity??.5});
 const event={backend:'observatory',kind:c.kind,id:o.seed??2030,lifeMs:o.durationMs??2400,atMs:0,space:'screen',origin:{x:c.center[0],y:c.center[1]}};
 EffectPainter.prototype.local.call({original},frame,{motionMs:c.timeMs,palette,effective:()=>({...DEFAULT_OBSERVATORY_OPTIONS})},null,event,()=>0);
 return {cells:Array.from(frame.cells)};
});`,context);
process.stdout.write(JSON.stringify(context.result));
