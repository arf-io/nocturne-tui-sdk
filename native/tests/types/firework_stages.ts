import type {NativeCommand} from '../../bindings/typescript/contracts.js';
import type {NativeMetadata} from '../../bindings/typescript/native_scene.mjs';
const style:NativeCommand={op:'burst-style',id:1,coreMs:200,glitterHz:18,glitterDepth:.6,coreAlpha:1,residualMs:180,residualAlpha:1};
declare const metadata:NativeMetadata;
const row:readonly [number,number,number,number,number,number]=metadata.emitters[0].burstStages!.samples[0];
const limit:16=metadata.emitters[0].burstStages!.sampleLimit;
// @ts-expect-error burst style controls are finite numeric authoring, not flags
const bad:NativeCommand={op:'burst-style',id:1,glitterHz:true};
void [style,row,limit,bad];
