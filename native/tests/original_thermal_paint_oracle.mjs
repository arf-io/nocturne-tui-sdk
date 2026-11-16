import fs from 'node:fs';
import vm from 'node:vm';
import crypto from 'node:crypto';
const html=fs.readFileSync(process.argv[2],'utf8');
if(crypto.createHash('sha256').update(html).digest('hex')!=='375c4468c886728bc790b8d8cc3bdddc2a046532a4d792cde190f1b522a66385')throw Error('Original HTML identity');
function between(a,b){let start=html.indexOf(a),end=html.indexOf(b,start);if(start<0||end<0)throw Error(a);return html.slice(start,end);}
const helpers=between('const TAU = Math.PI * 2;','/** An explicit monotonic clock.');
const paint=between('const BRAILLE_BITS =','function createCamera(');
const thermal=between('function sampleThermal(','return {EFFECT_CATALOG,EffectShelf,sampleThermal};');
const projector=between('class Projector {','/** Deterministic infinite tiling');
const camera=between('const radians =','/** Project to terminal cells');
const painter=between('class EffectPainter {','return {EffectPainter};');
const data=JSON.parse(html.match(/const DATA=(\{.*?\});\s*(?:const|function)/s)[1]);
const bytes=Buffer.from(data.wasm,'base64');
if(crypto.createHash('sha256').update(bytes).digest('hex')!=='aa04c1705a5982b924d420971bfcbc7bbedd49f1ea527a9900531b61b0c92a09')throw Error('Original WASM identity');
const {instance}=await WebAssembly.instantiate(bytes,{});
const wheel=Array.from({length:360},(_,h)=>instance.exports.nsOklchColor(830,1000,h*1000));
const context=vm.createContext({requests:JSON.parse(fs.readFileSync(process.argv[3],'utf8')),wheel});
vm.runInContext(helpers+paint+thermal+camera+projector+painter+`
result=requests.map(c=>{
 const frame={width:c.width,height:c.height,cells:Uint32Array.from(c.cells)},o=c.options;
 const camera={...c.camera,z:-c.camera.z,fov:2*Math.atan(c.width/(2*c.height)*Math.tan(c.camera.fov*Math.PI/360))*180/Math.PI};
 const p=new Projector(camera,c.width,c.height),event={backend:'thermal',kind:c.kind,seed:o.seed??2030,lifeMs:o.lifeMs??6500,atMs:0,space:'world',origin:{x:c.origin[0],y:c.origin[1],z:-c.origin[2]}};
 EffectPainter.prototype.thermal.call({},frame,p,event,c.timeMs,h=>wheel[((Math.round(h)%360)+360)%360]);
 const geometry=sampleThermal(event.kind,event.seed,c.timeMs,event.lifeMs),projected=[];
 for(const line of geometry.segments){const a=p.project({x:event.origin.x+line.a.x,y:event.origin.y+line.a.y,z:event.origin.z+line.a.z}),b=p.project({x:event.origin.x+line.b.x,y:event.origin.y+line.b.y,z:event.origin.z+line.b.z});if(a&&b)projected.push([a.x,a.y,a.z,b.x,b.y,b.z]);}
 return {cells:Array.from(frame.cells),projected};
});`,context);
process.stdout.write(JSON.stringify(context.result));
