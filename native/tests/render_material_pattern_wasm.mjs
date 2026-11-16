import fs from 'node:fs';
import {NativeScene} from '../bindings/typescript/native_scene.mjs';

const requests = JSON.parse(fs.readFileSync(0, 'utf8'));
const wasm = fs.readFileSync(new URL('../dist/nocturne_native.wasm', import.meta.url));
const results = [];
for (const request of requests) {
  const scene = await NativeScene.create(wasm, 2030);
  try {
    scene.command({op: 'resize', width: request.width, height: request.height});
    scene.command({op: 'material', id: 2, alpha: 1});
    scene.command(request.widget ?? {
      op: 'widget', id: 1, kind: 'box', x: request.x, y: request.y,
      width: request.panelWidth, height: request.panelHeight, padding: 0,
      border: 'none', alpha: 1, backgroundMaterial: 2,
    });
    scene.command({op: 'material', id: 2, pattern: request.pattern});
    if (request.timeMs) scene.advanceTo(request.timeMs * 1000);
    const frame = scene.render();
    results.push(Array.from({length: frame.width * frame.height}, (_, index) => {
      const at = index * 4;
      return [frame.cells[at], frame.cells[at + 1], frame.cells[at + 2], frame.cells[at + 3]];
    }));
  } finally {
    scene.close();
  }
}
process.stdout.write(JSON.stringify(results));
