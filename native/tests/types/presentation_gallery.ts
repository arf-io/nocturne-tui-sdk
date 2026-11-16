import type {NativeCommand} from '../../bindings/typescript/contracts.js';
const text:NativeCommand={op:'text',id:1,text:'SDK',alphabet:'ABXYZ012',jitterMs:10,batchSize:3,cycles:2,delayMs:100,reverseOrder:true,trailLength:2};
const window:NativeCommand={op:'window',id:1,shape:'polygon',polygon:[[0,0],[1,0],[0,1]],yaw:12,pitch:8,roll:3,anchorX:.2,anchorY:.8,meshColumns:12,meshRows:10};
const move:NativeCommand={op:'window-action',id:1,action:'move',dx:2,dy:1,forward:-3};
// @ts-expect-error action names are closed
const bad:NativeCommand={op:'window-action',id:1,action:'unsupported'};
void [text,window,move,bad];
