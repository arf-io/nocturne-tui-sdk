import fs from 'node:fs';
const bytes=fs.readFileSync(process.argv[2]),module=new WebAssembly.Module(bytes);
if(WebAssembly.Module.imports(module).length)throw Error('source weather WASM has imports');
const n=new WebAssembly.Instance(module,{}).exports;
const requests=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
const fields='count lifeMs launchSpeed gravity drag wind flickerHz trailMs branches arcSegments arcJitter coreMs shockwave explosionForce seed brightness emberSpread arcReach'.split(' ');
const defaults=[52,5000,12,8,.65,1.2,18,90,5,10,1.2,260,0,48,2030,.85,5,17],kinds=['embers','sparks','nova','rain','snow','ripples'];
function put(Type,values){const ptr=n.nrAlloc(values.length*Type.BYTES_PER_ELEMENT);new Type(n.memory.buffer,ptr,values.length).set(values);return ptr;}
const result=requests.map(c=>{
 const o=Object.fromEntries(fields.map((k,i)=>[k,defaults[i]]));Object.assign(o,c.options);
 const opts=put(Float64Array,fields.map(k=>o[k])),glyphs=Array.from(o.glyphs||'·∙⋅*+⠁⠂⠄',ch=>ch.codePointAt(0)),gp=put(Uint32Array,glyphs);
 const wheel=put(Uint32Array,c.wheel),cells=put(Uint32Array,c.cells);let rc,sample=null;
 if(c.event){const e=c.event,ev=put(Float64Array,[e.id,e.x,e.y,e.atMs,c.timeMs]),sp=n.nrAlloc(4096*8);
  rc=n.nrSourceWeatherProbe(kinds.indexOf(e.kind),ev,opts,gp,glyphs.length,c.weight,wheel,c.width,c.height,cells,sp);
  const header=Array.from(new Float64Array(n.memory.buffer,sp,5));sample=Array.from(new Float64Array(n.memory.buffer,sp,5+6*header[0]+7*header[1]));
 }else{const es=c.events,ev=put(Float64Array,es.length?es.flatMap(e=>[e.id,e.x,e.y,e.atMs]):[0]),ks=put(Uint32Array,es.length?es.map(e=>kinds.indexOf(e.kind)):[0]),l=c.layer,lp=put(Float64Array,[l.weatherIntensity,l.novaStrength,l.novaRegularity]);
  rc=n.nrSourceWeatherLayerProbe(ks,ev,es.length,c.timeMs,opts,gp,glyphs.length,lp,wheel,c.width,c.height,cells);
 }
 return {rc,cells:Array.from(new Uint32Array(n.memory.buffer,cells,c.cells.length)),sample};
});
process.stdout.write(JSON.stringify(result));
