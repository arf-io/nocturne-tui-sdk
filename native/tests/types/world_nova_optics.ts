import type {NativeMetadata} from '../../bindings/typescript/native_scene.mjs';
declare const info:NativeMetadata;
const row:readonly [number,number,number,number,number,number,number,number]=info.emitters[0].novaOptics!.samples[0];
const limit:16=info.emitters[0].novaOptics!.sampleLimit;
void [row,limit];
