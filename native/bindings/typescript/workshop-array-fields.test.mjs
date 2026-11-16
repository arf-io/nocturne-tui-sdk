import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {assignCompositionField,compositionDocument,previewComposition} from './workshop_composition.mjs';
let flow={op:'flow',id:1,flux:2};
flow=assignCompositionField(flow,'stages[].name',['channel','sheet']);
flow=assignCompositionField(flow,'stages[].delayUs',[250000,500000]);
flow=assignCompositionField(flow,'stages[].tailUs',[0,0]);
assert.deepEqual(flow.stages,[{name:'channel',delayUs:250000,tailUs:0},{name:'sheet',delayUs:500000,tailUs:0}]);
assert.equal(flow['stages[]'],undefined);
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
const result=await previewComposition(wasm,compositionDocument([flow]));
assert.equal(result.info.flows.length,1);
const original={op:'status',actions:[{id:1,label:'Inspect',event:'/inspect'}]};
const edited=assignCompositionField(original,'actions[].value',[3]);assert.equal(edited.actions[0].value,3);assert.equal(original.actions[0].value,undefined);
const nested=assignCompositionField({op:'batch'},'commands[].stages[].name',[['one','two'],['three']]);
assert.deepEqual(nested.commands,[{stages:[{name:'one'},{name:'two'}]},{stages:[{name:'three'}]}]);
for(const [command,path,value] of [[flow,'stages[].name','bad'],[flow,'stages[].name',['one']],
 [{op:'flow',stages:3},'stages[].name',['one']],[{op:'input'},'__proto__.polluted',true],
 [{op:'input'},'constructor.value',true]])assert.throws(()=>assignCompositionField(command,path,value));
assert.equal({}.polluted,undefined);
console.log('PASS actual WASM array command, nested construction, owned edits and invalid/prototype rejection');
