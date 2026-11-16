import type {NativeCommand} from '../../bindings/typescript/contracts.js';
const model:NativeCommand={op:'model-import',schema:'nocturne.model/v1',units:'meters',coordinates:'right-handed-y-up',vertices:[[0,0,0],[1,0,0],[0,0,1]],materials:[{color:0x42b8bc}],triangles:[{indices:[0,1,2],material:0,surfaceId:1}]};
const ribbon:NativeCommand={op:'ribbon',points:[[0,0,0],[1,0,0]],surfaceId:1,sampling:'braille'};
const pointer:NativeCommand={op:'trigger',id:1,source:'/go',target:'/out',expression:{path:'/task',pointer:'/a~1b'}};
// @ts-expect-error sampling is closed
const bad:NativeCommand={op:'ribbon',points:[[0,0,0],[1,0,0]],sampling:'unsupported'};
void [model,ribbon,pointer,bad];
