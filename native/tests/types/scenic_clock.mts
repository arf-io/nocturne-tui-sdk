import type {NativeCommand,SceneArtInfo} from '../../bindings/typescript/contracts.js';
const clock:NativeCommand={op:'scene-art',scene:'pearl-cascade',timeMs:9007199254740991};
const global:NativeCommand={op:'scene-art',timeMs:null};
// @ts-expect-error clock is numeric milliseconds or null
const bad:NativeCommand={op:'scene-art',timeMs:'2000'};
// @ts-expect-error model view has no scenic clock override
const model:NativeCommand={op:'model-view',timeMs:2000};
declare const info:SceneArtInfo;
const authored:number|null=info.timeMs;
const effective:number=info.effective.timeMs;
void [clock,global,bad,model,authored,effective];
