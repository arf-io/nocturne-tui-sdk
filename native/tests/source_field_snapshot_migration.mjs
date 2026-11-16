import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';import assert from 'node:assert/strict';
import {NativeScene} from '../bindings/typescript/native_scene.mjs';
const [folder,native,wasm]=process.argv.slice(2),s=await NativeScene.create(fs.readFileSync(wasm),2030);
const old=zlib.gunzipSync(fs.readFileSync(path.join(folder,'source86.snapshot.gz'))),frame=zlib.gunzipSync(fs.readFileSync(path.join(folder,'source86.frame.gz')));
s.restore(old);const saved=Buffer.from(s.snapshot());assert.deepEqual(saved,fs.readFileSync(native));assert.deepEqual(Buffer.from(s.render().bytes),frame);assert.deepEqual(Buffer.from(s.snapshot()),saved);assert.deepEqual(s.infoComplete().fields.map(v=>v.paint),['source','source','source','source']);s.restore(saved);assert.deepEqual(Buffer.from(s.render().bytes),frame);s.close();console.log(JSON.stringify({status:'PASS',snapshotBytes:saved.length}));
