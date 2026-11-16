import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const scene=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
try{
 const before=scene.snapshot();
 for(const [source,expected] of [['hello world',[6,11]],['A\r\nB',[3,4]],['',[0]],['你好',[1,2]],['1,234.5',[7]],['A\u2060B',[3]],['A\u00a0B',[3]],['🇦🇧🇨🇩',[2,4]],['👩‍🚀',[3]]]){
  const owned=scene.lineBreaks(source);assert.deepEqual(owned,expected);owned[0]=999;assert.deepEqual(scene.lineBreaks(source),expected);
 }
 const mandatory=[[2,0],[5,1],[7,1],[8,1]];
 const details=scene.lineBreakDetails('A B\r\nC\u2028D');assert.deepEqual(details,mandatory);details[0][0]=999;assert.deepEqual(scene.lineBreakDetails('A B\r\nC\u2028D'),mandatory);assert.deepEqual(scene.lineBreakDetails(''),[[0,1]]);
 assert.throws(()=>scene.lineBreakDetails('\ud800'));assert.throws(()=>scene.lineBreakDetails('A'.repeat(2049)));
 assert.throws(()=>scene.lineBreaks('\ud800'));assert.throws(()=>scene.lineBreaks('A'.repeat(2049)));assert.deepEqual(scene.snapshot(),before);
}finally{scene.close();}
console.log('PASS candidate owned scalar line-break binding references');
