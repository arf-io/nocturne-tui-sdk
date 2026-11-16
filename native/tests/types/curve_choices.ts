import type {NativeCommand,Boundary,Easing} from '../../bindings/typescript/contracts.js';
const boundaries:Boundary[]=['clamp','loop','reverse','random','smooth-random'];
const easings:Easing[]=['linear','ease-in','ease-out','smooth','smoother','sine','step'];
const commands:NativeCommand[]=boundaries.flatMap(boundary=>easings.map(easing=>({op:'material',id:3,alpha:{initial:0,rate:1,min:0,max:1,boundary,easing},index:{initial:0,rate:1,min:0,max:1,boundary,easing}})));
// @ts-expect-error material easing is closed
const bad:NativeCommand={op:'material',id:3,alpha:{easing:'cubic'}};
void [commands,bad];
