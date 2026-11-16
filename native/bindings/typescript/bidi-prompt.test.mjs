import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const scene=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
try {
 scene.command({op:'prompt',layout:'bidi',direction:'auto',mode:'grow'});
 scene.command({op:'draft',text:'א́ב',emitWeather:false});
 const before=scene.snapshot(), rows=scene.promptVisualLayout();
 assert.deepEqual(rows.map(r=>r.slice(0,5)),[[2,3,0,0,1],[0,2,1,0,1]]);
 assert.deepEqual(rows.map(r=>r.slice(8)),[[1,0x5d1],[1,0x5d0]]);
 rows[0][0]=999;assert.equal(scene.promptVisualLayout()[0][0],2);
 assert.deepEqual(scene.snapshot(),before);
 const [x,y]=rows[0].slice(5,7);
 for(const phase of ['down','up'])scene.command({op:'pointer',phase,x,y});
 assert.equal(scene.info().prompt.caret,3);
 const stable=scene.snapshot();
 assert.throws(()=>scene.command({op:'prompt',direction:'invalid'}));
 assert.deepEqual(scene.snapshot(),stable);
 console.log('PASS real WASM bidi prompt order, source edges, owned rows and rejection');
} finally {scene.close();}
