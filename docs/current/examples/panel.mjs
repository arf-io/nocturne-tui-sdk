import {readFile} from 'node:fs/promises';
import {NativeScene} from '../../../native/bindings/typescript/native_scene.mjs';
const wasm = await readFile(new URL('../../../native/dist/nocturne_native.wasm', import.meta.url));
const scene = await NativeScene.create(wasm, 2030);
try {
  scene.command(JSON.parse(await readFile(new URL('./panel.json', import.meta.url), 'utf8')));
  scene.advanceTo(500_000);
  const frame = scene.render();
  const checkpoint = scene.snapshot();
  scene.command({op:'widget', id:1, value:0.8});
  scene.restore(checkpoint);
  console.log(frame.width, frame.height, frame.bytes.length);
} finally { scene.close(); }
