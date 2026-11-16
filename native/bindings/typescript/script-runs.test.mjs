import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const scene=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
try {
 const before=scene.snapshot(),expected=[[0,3,'Latn'],[3,10,'Arab']];
 const contract=scene.info().contract;
 assert.ok(contract.features.includes('script-itemization'));assert.ok(contract.features.includes('explicit-bidi-lines'));
 assert.deepEqual(contract.queryContracts.nrScriptRuns.fields,['start','end','iso15924TagBigEndian']);assert.equal(contract.queryContracts.nrScriptRuns.profile,'nr-script-grapheme-v1');
 assert.equal(contract.queryContracts.nrBidiClusterLines.fullParagraphResolution,true);assert.equal(contract.queryContracts.nrBidiClusterLines.widthUnit,'terminalCellAnnotation');assert.equal(contract.queryContracts.nrBidiClusterLines.rowWords,7);
 const rows=scene.scriptRuns('a\u0301 العربية');assert.deepEqual(rows,expected);
 assert.deepEqual(scene.scriptRuns('アー'),[[0,2,'Kana']]);assert.deepEqual(rows,expected);
 rows[0][2]='Zyyy';assert.deepEqual(scene.scriptRuns('a\u0301 العربية'),expected);
 assert.deepEqual(scene.scriptRuns('👩\u200d🔧'),[[0,3,'Zyyy']]);assert.deepEqual(scene.scriptRuns(''),[]);
 const lines=scene.bidiLines('אב ab ',[3,6]);assert.deepEqual(lines.map(r=>r[0]),[2,1,0,5,3,4]);assert.deepEqual(lines.map(r=>r[5]),[1,1,1,1,2,2]);
 lines[0][0]=999;assert.equal(scene.bidiLines('אב ab ',[3,6])[0][0],2);
 assert.throws(()=>scene.bidiLines('a\u0301b',[1,3]));assert.throws(()=>scene.bidiLines('a\nb',[3]));assert.deepEqual(scene.bidiLines('',[]),[]);
 assert.throws(()=>scene.scriptRuns('\ud800'));assert.throws(()=>scene.scriptRuns('a'.repeat(2049)));
 const input=scene.input,output=scene.checkpoint;
 new Uint32Array(scene.exports.memory.buffer,input,2).set([97,0x5d0]);
 new Uint32Array(scene.exports.memory.buffer,output,6).fill(777);
 assert.equal(scene.exports.nrScriptRuns(input,2,output,1),-1);
 assert.deepEqual(Array.from(new Uint32Array(scene.exports.memory.buffer,output,6)),Array(6).fill(777));
 assert.equal(scene.exports.nrScriptRuns(input,2,input,2),2);
 assert.deepEqual(Array.from(new Uint32Array(scene.exports.memory.buffer,input,6)),[0,1,0x4c61746e,1,2,0x48656272]);
 assert.deepEqual(scene.snapshot(),before);
} finally {scene.close();}
console.log('PASS owned script runs, scalar offsets, whole graphemes and atomic output');
