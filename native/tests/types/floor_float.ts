import type {NativeCommand} from '../../bindings/typescript/contracts.js';
const floor:NativeCommand={op:'floor',sampling:'hybrid',friction:.8,settleSpeed:30,reentrainWindSpeed:10,overflow:'merge-to-field',maxTiles:4,evaporation:.1,cellSize:2};
const body:NativeCommand={op:'float-body',id:1,surfaceId:1,fluidDensity:800,visible:false};
const hull:NativeCommand={op:'float-hull',id:1,vertices:[[0,0,0]],faces:[[0,0,0]],inertia:[100,100,100],orientation:[0,1,0,0]};
// @ts-expect-error floor overflow policy is closed
const bad:NativeCommand={op:'floor',overflow:'unbounded'};
void [floor,body,hull,bad];
