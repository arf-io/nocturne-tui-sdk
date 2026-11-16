import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { NativeScene } from './native_scene.mjs';

// Exercise the shipped binding against freshly rebuilt, import-free native WASM.
test('intentValue selects the oldest matching retained event and fires once', async () => {
  const wasm = readFileSync(new URL('../../dist/nocturne_native.wasm', import.meta.url));
  const scene = await NativeScene.create(wasm, 2030);
  const unrelated = {
    id: 1, event: '/parity/unrelated', messageId: 40, actionId: 3,
    messageSequence: 1, atUs: 100000, value: 7,
  };
  const matching = {
    id: 2, event: '/parity/approved', messageId: 600, actionId: 9,
    messageSequence: 2, atUs: 200000, value: 7,
  };
  const expectedQueue = [unrelated, matching];
  const checkState = fired => {
    const info = scene.info();
    assert.deepEqual(info.intents, expectedQueue, 'neither intent is implicitly acknowledged');
    assert.equal(info.triggers.length, 1);
    const rule = info.triggers[0];
    assert.equal(rule.id, 11);
    assert.equal(rule.conditionNodes, 3);
    assert.equal(rule.event, matching.event);
    assert.equal(rule.valueSource, 'constant');
    assert.equal(rule.pendingIntent, 0);
    assert.equal(info.values['/parity/enabled'], fired ? 1 : 0);
    // The action increments by constant 3, independently of the selector payload 7.
    assert.equal(info.values['/parity/out'], fired ? 13 : 10);
    assert.equal(rule.fireCount, fired ? 1 : 0);
    assert.equal(rule.lastIntent, fired ? matching.id : 0);
    assert.equal(rule.lastFireUs, fired ? 300000 : 0);
    assert.deepEqual(rule.intentCandidate, fired ? null : matching);
    assert.deepEqual(rule.lastIntentSource, fired ? matching : null);
  };
  const checkPure = fired => {
    const before = scene.snapshot();
    for (let index = 0; index < 3; index++) {
      checkState(fired);
      assert.deepEqual(scene.snapshot(), before, 'info must not mutate authoritative state');
      assert.ok(scene.render().bytes.length > 0, 'execute an actual native-WASM render');
      assert.deepEqual(scene.snapshot(), before, 'render must not mutate authoritative state');
    }
    checkState(fired);
  };

  try {
    scene.command({ op: 'define', path: '/parity/enabled', value: 0 });
    scene.command({ op: 'define', path: '/parity/out', value: 10 });
    scene.command({
      op: 'trigger', id: 11, event: '/parity/approved',
      when: { all: [
        { path: '/parity/enabled', comparison: 'equal', value: 1 },
        { intentValue: { comparison: 'at-least', value: 7 } },
      ] },
      target: '/parity/out', action: 'increment', value: 3,
    });
    const initial = scene.info();
    assert.equal(initial.triggers.length, 1);
    assert.equal(initial.triggers[0].intentCandidate, null);
    assert.deepEqual(initial.intents, []);
    scene.advanceTo(100000);
    scene.command({ op: 'status', id: 40, area: 0, text: 'Unrelated', durationMs: 0,
      actions: [{ id: 3, label: 'Confirm', event: '/parity/unrelated', value: 7 }] });
    scene.command({ op: 'notification-action', id: 40, actionId: 3 });
    scene.advanceTo(200000);
    scene.command({ op: 'status', id: 600, area: 0, text: 'Matching', durationMs: 0,
      actions: [{ id: 9, label: 'Confirm', event: '/parity/approved', value: 7 }] });
    scene.command({ op: 'notification-action', id: 600, actionId: 9 });
    checkPure(false);
    scene.advanceTo(300000);
    checkPure(false);
    scene.command({ op: 'set', path: '/parity/enabled', value: 1 });
    checkPure(true);
    scene.command({ op: 'set', path: '/parity/enabled', value: 1 });
    scene.advanceTo(400000);
    checkPure(true);
  } finally {
    scene.close();
  }
});
