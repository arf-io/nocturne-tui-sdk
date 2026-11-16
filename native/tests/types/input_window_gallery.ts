import type {NativeCommand} from '../../bindings/typescript/contracts.js';
const key:NativeCommand={op:'key',key:'ArrowLeft',alt:true,meta:false,shift:true};
const pointer:NativeCommand={op:'pointer',phase:'move',x:2,y:2,button:2,alt:true,shift:false};
const transition:NativeCommand={op:'window-action',id:1,action:'restore',effect:'window-transition/origami',group:9};
const scroll:NativeCommand={op:'window-action',id:1,action:'scroll',rows:-2};
// @ts-expect-error pointer buttons are closed
const bad:NativeCommand={op:'pointer',x:0,y:0,button:3};
void [key,pointer,transition,scroll,bad];
