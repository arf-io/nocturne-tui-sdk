import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { gunzipSync } from 'node:zlib';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { NativeScene } from './native_scene.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const fixture = name => gunzipSync(readFileSync(resolve(here, '../../tests/fixtures', name)));
const wasm = readFileSync(resolve(here, '../../dist/nocturne_native.wasm'));
const schema = bytes => new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength).getUint32(12, true);
const expanded = fixture('schema-20261003-contracts7-registered-style.snapshot.gz');
assert.equal(schema(expanded), 0x20261003);
const scene = await NativeScene.create(wasm, 99);
try {
  const current=scene.info().contract;assert.equal(current.snapshotSchema,schema(scene.snapshot()));
  scene.restore(expanded);
  assert.equal(scene.info().registeredStates[0].path, '/lab/one');
  assert.equal(schema(scene.snapshot()),current.snapshotSchema);assert.equal(scene.info().contract.sourceSchema,current.snapshotSchema);assert.equal(scene.info().contract.snapshotCapacityBytes,scene.snapshot().length);
  const local = fixture('schema-20261004-intent-action.snapshot.gz');
  scene.restore(local);
  assert.equal(scene.info().triggers[0].valueSource, 'intentValue');
  assert.equal(schema(scene.snapshot()),current.snapshotSchema);assert.equal(scene.info().contract.sourceSchema,current.snapshotSchema);assert.equal(scene.info().contract.snapshotCapacityBytes,scene.snapshot().length);
  const wrongPair = expanded.slice();
  new DataView(wrongPair.buffer, wrongPair.byteOffset, wrongPair.byteLength).setUint32(12, 0x20261004, true);
  const preserved = scene.snapshot();
  const beforeFrame = scene.render().bytes.slice();
  assert.throws(() => scene.restore(wrongPair), /rejected|size/i);
  assert.deepEqual(scene.snapshot(), preserved, 'Wrong schema/size pair must preserve state');
  assert.deepEqual(scene.render().bytes, beforeFrame, 'Rejected import must preserve rendered content');
  assert.throws(() => scene.restore(preserved.slice(0, -1)), /rejected|size/i);
  assert.deepEqual(scene.snapshot(), preserved, 'Truncated snapshot must preserve state');
  scene.command({op:'input', text:'temporary edit'});
  scene.restore(preserved);
  assert.deepEqual(scene.snapshot(), preserved, 'Current promoted snapshot must roundtrip exactly');
  assert.deepEqual(scene.render().bytes, beforeFrame);
} finally { scene.close(); }
