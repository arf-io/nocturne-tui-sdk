import assert from 'node:assert/strict';
import {readFileSync, writeFileSync} from 'node:fs';
import {NativeScene} from '../bindings/typescript/native_scene.mjs';

const [requestPath, responsePath] = process.argv.slice(2);
if (!requestPath || !responsePath) throw new Error('usage: runner request.json response.json');
const request = JSON.parse(readFileSync(requestPath, 'utf8'));
if (!Array.isArray(request) || request.length !== 46) throw new Error('expected 46 RC2 studies');
const wasmBytes = readFileSync(new URL('../dist/nocturne_native.wasm', import.meta.url));

function packedWords(frame) {
  if (!(frame?.bytes instanceof Uint8Array) || frame.bytes.byteLength % 4 !== 0) {
    throw new Error('NativeScene returned a malformed packed frame');
  }
  return Array.from(new Uint32Array(
    frame.bytes.buffer, frame.bytes.byteOffset, frame.bytes.byteLength / 4,
  ));
}

async function replay(scene, commands, actions, sampleTimesUs, id) {
  for (const command of commands) scene.command(command);
  let nextAction = 0;
  const frames = [];
  for (const timeUs of sampleTimesUs) {
    while (nextAction < actions.length && actions[nextAction].timeUs <= timeUs) {
      const action = actions[nextAction++];
      scene.advanceTo(action.timeUs);
      scene.command(action.command);
    }
    scene.advanceTo(timeUs);
    const before = scene.snapshot();
    const words = packedWords(scene.render());
    assert.deepEqual(scene.snapshot(), before, `${id}@${timeUs}: render mutated retained state`);
    frames.push({id, timeUs, words});
  }
  assert.equal(nextAction, actions.length, `${id}: unconsumed timed actions`);
  return frames;
}

const output = [];
for (const study of request) {
  if (!study || typeof study.id !== 'string' || !Array.isArray(study.commands)
      || !Array.isArray(study.baselineCommands) || !Array.isArray(study.actions)
      || !Array.isArray(study.sampleTimesUs)) {
    throw new Error('malformed RC2 window study request');
  }
  const visible = await NativeScene.create(
    wasmBytes, 2030,
  );
  const baseline = await NativeScene.create(
    wasmBytes, 2030,
  );
  try {
    const visibleFrames = await replay(
      visible, study.commands, study.actions, study.sampleTimesUs, study.id,
    );
    const baselineFrames = await replay(
      baseline, study.baselineCommands, study.actions, study.sampleTimesUs, study.id,
    );
    for (let i = 0; i < visibleFrames.length; i++) {
      output.push({
        id: study.id,
        timeUs: study.sampleTimesUs[i],
        words: visibleFrames[i].words,
        baseline: baselineFrames[i].words,
      });
    }
  } finally {
    visible.close();
    baseline.close();
  }
}

writeFileSync(responsePath, JSON.stringify(output));
