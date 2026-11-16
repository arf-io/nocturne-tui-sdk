import fs from 'node:fs';
import vm from 'node:vm';
import crypto from 'node:crypto';
const html=fs.readFileSync(process.argv[2],'utf8');
if(crypto.createHash('sha256').update(html).digest('hex')!=='375c4468c886728bc790b8d8cc3bdddc2a046532a4d792cde190f1b522a66385')throw Error('original HTML identity');
function between(a,b){let start=html.indexOf(a);if(start<0)throw Error(a);let end=html.indexOf(b,start);if(end<0)throw Error(b);return html.slice(start,end);}
const helpers=between('const TAU = Math.PI * 2;','/** An explicit monotonic clock.');
const paint=between('const BRAILLE_BITS =','function createCamera(');
const particles=between('const DEFAULT_PARTICLE_OPTIONS =','return {DEFAULT_PARTICLE_OPTIONS,PARTICLE_CONTROLS,validateParticleOptions,sampleEmber,sampleWeather};');
const obs=between('class ObservatoryRenderer {','return {TAU,');
// The original Observatory closure's class is followed by other harmless function declarations.
const renderer=between('class KineticRenderer {','return {KineticRenderer,hitKinetic,activateKinetic};');
const data=JSON.parse(html.match(/const DATA=(\{.*?\});\s*(?:const|function)/s)[1]);
const bytes=Buffer.from(data.wasm,'base64');
if(crypto.createHash('sha256').update(bytes).digest('hex')!=='aa04c1705a5982b924d420971bfcbc7bbedd49f1ea527a9900531b61b0c92a09')throw Error('original WASM identity');
const {instance}=await WebAssembly.instantiate(bytes,{});
const wheel=Array.from({length:360},(_,h)=>instance.exports.nsOklchColor(830,1000,h*1000));
const context=vm.createContext({requests:JSON.parse(fs.readFileSync(process.argv[3],'utf8')),wheel});
vm.runInContext(helpers+paint+particles+obs+renderer+`
const renderer=new KineticRenderer({});renderer.base.wheel=wheel;
result=requests.map(c=>{
 const options=validateParticleOptions(c.options),sample=c.event?sampleWeather(c.event,c.timeMs,options):null;
 const frame={width:c.width,height:c.height,cells:Uint32Array.from(c.cells)};
 const count=renderer.weather(frame,{events:c.events||[c.event],motionMs:c.timeMs,particles:options},c.layer||{weatherIntensity:c.weight/2.6,novaStrength:1,novaRegularity:0});
 return {sample,count,cells:Array.from(frame.cells),wheel};
});`,context);
process.stdout.write(JSON.stringify(context.result));
