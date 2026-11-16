import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const s=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)),42);
const tokenNumber=24+5958112+8+8+4096+24;
const bits=value=>{const b=new ArrayBuffer(8),v=new DataView(b);v.setFloat64(0,value,true);return v.getBigUint64(0,true);};
const cached=()=>{const b=s.snapshot();return new DataView(b.buffer,b.byteOffset,b.byteLength).getBigUint64(tokenNumber,true);};
const raw=text=>{const b=new TextEncoder().encode(text);assert.ok(b.length<=65536);new Uint8Array(s.exports.memory.buffer,s.input,b.length).set(b);if(s.exports.nrCommand(s.context,s.input,b.length)<0)throw Error(s.string(s.exports.nrError(s.context)));};
try{
 s.command({op:'define',path:'/json',type:'json',value:0});
 const samples=['0','-0','0.1','0.3','9007199254740993','1e100','1e-100','1e-101','5e-324','-5e-324','1e-1000',
  '1.00000000000000011102230246251565404236316680908203125',
  '1.00000000000000011102230246251565404236316680908203125001',
  '0.'+'0'.repeat(1500)+'1e1501','1'+'0'.repeat(1500)+'e-1500','0e9999999999','-0e-9999999999','1e-9999999999'];
 for(const sample of samples){raw('{"op":"set","path":"/json","value":'+sample+'}');assert.equal(cached(),bits(Number(sample)),sample.slice(0,80));}
 for(const [numerator,denominator] of [[1,3],[1,10],[2,7],[-1,10],[900719,7]]){
  s.command({op:'set',path:'/json',expression:{divide:[numerator,denominator]}});
  assert.equal(cached(),bits(numerator/denominator));assert.equal(bits(s.info().values['/json']),bits(numerator/denominator));
  const before=s.snapshot();s.render();assert.deepEqual(s.snapshot(),before);s.restore(before);assert.deepEqual(s.snapshot(),before);
 }
 s.command({op:'set',path:'/json',expression:{negate:0}});assert.equal(cached(),bits(-0));assert.equal(bits(s.info().values['/json']),bits(-0));
 s.command({op:'define',path:'/number',value:0});s.command({op:'set',path:'/number',expression:{divide:[1,3]}});assert.equal(bits(s.info().values['/number']),bits(1/3));
 s.command({op:'set',path:'/json',expression:{object:{fraction:{divide:[1,3]},values:{array:[{path:'/number'},{add:[1,2]}]}}}});
 assert.deepEqual(s.info().values['/json'],{fraction:1/3,values:[1/3,3]});
 for(const sample of ['1e101','-1e101','01','1.','1e','+1','NaN','Infinity']){const before=s.snapshot();assert.throws(()=>raw('{"op":"set","path":"/json","value":'+sample+'}'));assert.deepEqual(s.snapshot(),before);}
 console.log(JSON.stringify({runtime:'actual WASM',independentDecimalOracle:'V8 Number',decimalSamples:samples.length,computedJsonBits:true,exactValueMetadata:true,structuredNumbers:true,atomicFaults:true,renderPure:true,snapshotReplay:true}));
}finally{s.close();}
