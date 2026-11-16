import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const s=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
try{
 for(const c of [{op:'node',id:1,pinned:true,position:[1,2,3]},{op:'node',id:2},{op:'edge',from:1,to:2,kind:'depends'}])s.command(c);
 const before=s.snapshot(),info=s.infoComplete();
 assert.deepEqual(info.graph,{dimensions:3,layoutMode:'layered',lastLayoutUnresolvedNodes:0,layoutProfile:'measured',sourceLayout:null,edges:[{from:1,to:2,kind:'depends'}]});
 assert.ok(info.contract.features.includes('graph-readback'));assert.equal(info.nodes[0].pinned,true);assert.deepEqual(info.nodes[0].targetPosition,[1,2,3]);
 info.graph.edges[0].kind='changed';info.nodes[0].targetPosition[0]=999;
 const again=s.infoComplete();assert.equal(again.graph.edges[0].kind,'depends');assert.deepEqual(again.nodes[0].targetPosition,[1,2,3]);
 s.render();assert.deepEqual(before,s.snapshot());
 console.log('PASS actual WASM graph readback, ownership and snapshot purity');
}finally{s.close();}
