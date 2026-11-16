import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
import {compositionDocument,exportComposition,importComposition,previewComposition,applyComposition} from './workshop_composition.mjs';

const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
const source=[{op:'input',text:'Composite draft'}];
const document=compositionDocument(source,2030);
source[0].text='Mutated host object';
assert.equal(document.commands[0].text,'Composite draft');
const loaded=importComposition(exportComposition(document));
assert.deepEqual(loaded,document);
const a=await previewComposition(wasm,document),b=await previewComposition(wasm,loaded);
assert.deepEqual(a.snapshot,b.snapshot);assert.deepEqual(a.frame,b.frame);
assert.equal(a.info.prompt.text,'Composite draft');
const scene=await NativeScene.create(wasm);
try{
 scene.command({op:'input',text:'Retained application draft'});
 const before=scene.snapshot();
 await previewComposition(wasm,document);assert.deepEqual(scene.snapshot(),before);
 const invalid=compositionDocument([{op:'input',text:'Must rollback'},{op:'unknown-workshop-command'}]);
 assert.throws(()=>applyComposition(scene,invalid));assert.deepEqual(scene.snapshot(),before);
 applyComposition(scene,document);assert.equal(scene.info().prompt.text,'Retained application draftComposite draft');
}finally{scene.close();}
for(const invalid of [null,{},'bad', {schema:'nocturne.composition.v1',seed:1,commands:null},
 {schema:'nocturne.composition.v1',seed:-1,commands:[]},
 {schema:'nocturne.composition.v1',seed:1,commands:[],unrecognised:true}]){
 assert.throws(()=>importComposition(JSON.stringify(invalid)));
}
assert.throws(()=>compositionDocument([{op:'camera',distance:Infinity}]));
assert.throws(()=>compositionDocument(source,1.5));
await assert.rejects(previewComposition(wasm,compositionDocument([{op:'unknown-workshop-command'}])));
console.log('PASS actual WASM composition roundtrip, independent preview, native atomic rejection and malformed documents');
