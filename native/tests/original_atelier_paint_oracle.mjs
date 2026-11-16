import fs from 'node:fs';
import vm from 'node:vm';
import crypto from 'node:crypto';
const html=fs.readFileSync(process.argv[2],'utf8');
if(crypto.createHash('sha256').update(html).digest('hex')!=='375c4468c886728bc790b8d8cc3bdddc2a046532a4d792cde190f1b522a66385')throw Error('Original HTML identity');
function between(a,b){let start=html.indexOf(a),end=html.indexOf(b,start);if(start<0||end<0)throw Error(a);return html.slice(start,end);}
const helpers=between('const TAU = Math.PI * 2;','/** An explicit monotonic clock.');
const paint=between('const BRAILLE_BITS =','function createCamera(');
const atelier=between('const ATELIER_BURST_DEFAULTS =','return {ATELIER_BURST_DEFAULTS,ATELIER_BURST_RANGES,atelierBurstOptions,sampleAtelierBurst};');
const painter=between('class EffectPainter {','return {EffectPainter};');
const data=JSON.parse(html.match(/const DATA=(\{.*?\});\s*(?:const|function)/s)[1]);
const bytes=Buffer.from(data.wasm,'base64');
if(crypto.createHash('sha256').update(bytes).digest('hex')!=='aa04c1705a5982b924d420971bfcbc7bbedd49f1ea527a9900531b61b0c92a09')throw Error('Original WASM identity');
const {instance}=await WebAssembly.instantiate(bytes,{});
const wheel=Array.from({length:360},(_,h)=>instance.exports.nsOklchColor(830,1000,h*1000));
const context=vm.createContext({requests:JSON.parse(fs.readFileSync(process.argv[3],'utf8')),wheel});
vm.runInContext(helpers+paint+atelier+painter+`
const originalSampler=sampleAtelierBurst;
result=requests.map(c=>{
 const frame={width:c.width,height:c.height,cells:Uint32Array.from(c.cells)};
 const options={...c.options};delete options.eventId;delete options.paint;
 sampleAtelierBurst=(e,t,o)=>originalSampler({...e,id:c.options.eventId??1},t,{...o,...options});
 const event={backend:'atelier',kind:c.kind,seed:c.options.seed??4711,lifeMs:c.options.lifeMs??4200,atMs:0,space:'screen',origin:{x:c.center[0],y:c.center[1]}};
 EffectPainter.prototype.local.call({},frame,{motionMs:c.timeMs,effective:()=>({})},null,event,h=>wheel[((Math.round(h)%360)+360)%360]);
 return {cells:Array.from(frame.cells)};
});`,context);
process.stdout.write(JSON.stringify(context.result));
