import assert from 'node:assert/strict';
import {readFileSync, writeFileSync} from 'node:fs';
import {mkdir} from 'node:fs/promises';
import {dirname, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {NativeScene} from '../bindings/typescript/native_scene.mjs';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const requestPath=resolve(process.argv[2]);
const output=resolve(process.argv[3]);
const wasmPath=resolve(root,'dist/nocturne_native.wasm');

const request=JSON.parse(readFileSync(requestPath,'utf8'));
await mkdir(output,{recursive:true});

const scene=await NativeScene.create(readFileSync(wasmPath),2030);
const currentSchema=new DataView(scene.snapshot().buffer).getUint32(12,true);
assert.ok(currentSchema>=0x20261068,'retained Stage writer contract required');
try {
  let info=scene.infoComplete();
  assert.equal(info.contract.snapshotSchema,currentSchema,'WASM metadata disagrees with actual writer');
  assert.equal(info.contract.sourceSchema,currentSchema,'WASM state disagrees with actual writer');
  for(const command of request.commands)scene.command(command);
  scene.advanceTo(request.timeUs);
  const frame=scene.render();
  const bytes=Buffer.from(frame.bytes);
  const cellsFile='source-stage-cells.bin';
  writeFileSync(resolve(output,cellsFile),bytes);
  const snapshot=scene.snapshot();
  const invalidBefore=scene.snapshot();
  let invalidRejected=false;
  try { scene.command(request.invalidCommand); }
  catch { invalidRejected=true; }
  assert.ok(invalidRejected,'malformed Stage command must be rejected');
  assert.deepEqual(scene.snapshot(),invalidBefore,'malformed command must be atomic');
  scene.restore(snapshot);
  const replay=Buffer.from(scene.render().bytes);
  const snapshotReplayIdentical=replay.equals(bytes);
  assert.ok(snapshotReplayIdentical,'snapshot replay must preserve full frame bytes');
  info=scene.infoComplete();
  assert.equal(info.contract.snapshotSchema,currentSchema);
  assert.equal(info.contract.sourceSchema,currentSchema);
  const report={
    snapshotSchema:info.contract.snapshotSchema,
    sourceSchema:info.contract.sourceSchema,
    width:frame.width,
    height:frame.height,
    cellsFile,
    invalidRejected,
    snapshotReplayIdentical,
    sourceStageComponents:info.sourceStageComponents.length,
    sourceStageInfo:info.sourceStageComponents,
  };
  writeFileSync(resolve(output,'report.json'),JSON.stringify(report,null,2));
  console.log(`PASS schema-67 Stage WASM: ${frame.width}x${frame.height}, ${report.sourceStageComponents} retained components`);
} finally {
  scene.close();
}
