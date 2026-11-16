import type {NativeCommand} from '../../bindings/typescript/contracts.js';
const wind:NativeCommand={op:'define',path:'/garden/windX',value:.4,binding:{family:'emitter',id:1,field:'wind.x'}};
const heat:NativeCommand={op:'define',path:'/garden/heat',value:.25,binding:{family:'emitter',id:3,field:'heat'}};
const surface:NativeCommand={op:'surface',id:1,wetnessDarkening:.5,heatTintStrength:.4,retentionMs:20000,fadeMs:5000};
// @ts-expect-error vector components use supported axes
const bad:NativeCommand={op:'define',path:'/wind',value:1,binding:{family:'emitter',id:1,field:'wind.w'}};
void [wind,heat,surface,bad];
