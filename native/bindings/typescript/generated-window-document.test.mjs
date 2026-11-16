import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';

const wasm = readFileSync(new URL('../../dist/nocturne_native.wasm', import.meta.url));
const scene = await NativeScene.create(wasm);
try {
    scene.command({op:'window', id:1, title:'Window', text:'initial'});
    const text = 'x'.repeat(4095) + 'Z';
    scene.command({op:'window-content', id:1, text});
    assert.equal(text.length, 4096);
    assert.equal(scene.textRunSource(2, 1), text);
    scene.command({op:'window-content', id:1, text:''});
    assert.equal(scene.textRunSource(2, 1), '');
    assert.throws(() => scene.textRunSource(2, 65535));
} finally {
    scene.close();
}
console.log(JSON.stringify({runtime:'actual WASM', concern:'generated window document binding read', documentScalars:4096, empty:true, missingSourceRejected:true}));
