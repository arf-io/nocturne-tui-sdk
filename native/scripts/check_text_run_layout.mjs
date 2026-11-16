import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {NativeScene} from '../bindings/typescript/native_scene.mjs';
const s=await NativeScene.create(readFileSync(new URL('../dist/nocturne_native.wasm',import.meta.url)),2030);
try {
 s.command({op:'text',id:41,text:'Aé中'});
 assert.equal(s.textRunSource(1,41),'Aé中');
 assert.deepEqual(s.textRunLayout(1,41,3),[[41,0,1,0,0,1,1],[41,1,3,1,0,1,1],[41,3,4,0,1,2,1]]);
 assert.equal(s.textRunHit(1,41,3,0,1),3);assert.equal(s.textRunHit(1,41,3,1,1),4);assert.throws(()=>s.textRunHit(1,999,8,0,0));
 assert.deepEqual(s.textRunClip(1,41,8,3,0,1,1),[[41,3,4,2,0,2,1,1,1]]);assert.deepEqual(s.textRunClip(1,41,8,0xffffffff,0,0xffffffff,1),[]);
 const saved=s.snapshot();const rows=s.textRunLayout(1,41,8);rows[0][0]=999;assert.equal(s.textRunLayout(1,41,8)[0][0],41);assert.deepEqual(s.snapshot(),saved);
 assert.throws(()=>s.textRunSource(1,999));assert.throws(()=>s.textRunLayout(1,41,0));assert.throws(()=>s.textRunSource(true,41));
 s.command({op:'text',id:41,text:'AéZ'});
 const old=s.textClusterSample(41,1);assert.deepEqual(old.slice(1,3),[1,3]);
 const checkpoint=s.snapshot();s.render();assert.deepEqual(s.snapshot(),checkpoint);
 s.command({op:'text',id:41,text:'AèZ'});assert.notEqual(s.textClusterSample(41,1)[0],old[0]);
 s.restore(checkpoint);assert.deepEqual(s.textClusterSample(41,1),old);
 assert.throws(()=>s.textClusterSample(41,3));assert.throws(()=>s.textClusterSample(true,0));
 console.log('PASS: WASM context text run source, stable identity, reflow, ownership, purity and rejection');
}finally{s.close();}
