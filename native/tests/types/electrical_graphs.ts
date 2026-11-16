import type {NativeCommand} from '../../bindings/typescript/contracts.js';
import type {NativeMetadata} from '../../bindings/typescript/native_scene.mjs';
const command:NativeCommand={op:'electrical-arc',id:1,points:[{position:[0,0,0],parent:-1},{position:[1,2,3],parent:0}],speed:10,repeatMs:2000};
const remove:NativeCommand={op:'remove-electrical-arc',id:1};
declare const metadata:NativeMetadata;
const phase:'waiting'|'leader'|'hold'|'fade'|'finished'=metadata.electricalArcs[0].phase;
const row:readonly [number,number,number,number,number,number,number]=metadata.electricalArcs[0].segments[0];
// @ts-expect-error circuit authoring has no screen-only endpoint
const bad:NativeCommand={op:'electrical-arc',id:1,points:[{position:[1,2],parent:-1}]};
void [command,remove,phase,row,bad];
