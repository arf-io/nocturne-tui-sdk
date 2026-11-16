import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)),s=await NativeScene.create(wasm),r=await NativeScene.create(wasm);
try{
 for(const x of [s,r]){x.command({op:'resize',width:60,height:24});x.command({op:'prompt',active:false});x.command({op:'environment',stars:0});x.command({op:'area',id:1,x:5,y:4,width:10,height:5,padding:0,border:'none',alpha:0});x.command({op:'area',id:2,parent:1,x:8,y:1,width:10,height:5,padding:1,border:'double',alpha:0});}
 assert.deepEqual(s.areaGeometry(2),[13,5,10,5,13,5,2,4,15,7,6,1]);const before=s.snapshot();const owned=s.areaGeometry(2);owned[0]=-99;assert.equal(s.areaGeometry(2)[0],13);assert.deepEqual(s.snapshot(),before);assert.equal(s.areaGeometry(999),null);assert.throws(()=>s.areaGeometry(0));assert.throws(()=>s.areaGeometry(65536));
 for(const cursor of [false,true]){s.command({op:'indicator',id:1,area:2,x:3,y:1,sequence:'Z',cursor});assert.deepEqual(s.render().bytes,r.render().bytes);}
 s.command({op:'area',id:1,x:1000});r.command({op:'area',id:1,x:1000});assert.deepEqual(s.areaGeometry(1).slice(4,8),[60,4,0,5]);assert.deepEqual(s.render().bytes,r.render().bytes);
 s.command({op:'indicator',id:1,area:0,x:30,y:2,sequence:'Z',cursor:false});assert.equal(s.render().cells[(2*60+30)*4],90);assert.equal(s.info().contract.queryContracts.nrAreaGeometry.rowWords,12);
 console.log('PASS actual WASM owned nested geometry, independent clipping/content bounds, wait/cursor suppression and unowned behavior');
}finally{s.close();r.close();}
