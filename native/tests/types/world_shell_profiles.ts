import type {NativeMetadata} from '../../bindings/typescript/native_scene.mjs';
declare const info:NativeMetadata;
const shape:'clumpy-fibonacci'|'uniform-fibonacci'|undefined=info.emitters[0].worldShellProfile?.shape;
const active:boolean|undefined=info.emitters[0].worldShellProfile?.active;
void [shape,active];
