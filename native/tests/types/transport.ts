import type {NativeCommand} from '../../bindings/typescript/contracts.js';
const commands:NativeCommand[]=[
 {op:'flow',id:1,flux:2,stages:[{name:'channel',delayUs:1000,tailUs:500000}]},
 {op:'flow-rate',id:1,flux:0},
 {op:'flow-surface',surfaceId:1,flowId:1,stage:'channel',referenceFlux:2},
 {op:'flow-thickness',surfaceId:1,width:2,speed:2,maxDepth:1,direction:[0,1,0]},
 {op:'remove-flow-thickness',surfaceId:1},
 {op:'surface-foam-transport',surfaceId:1,velocity:[1,0]},
 {op:'flow-sink',surfaceId:1,flowId:1,fraction:.5,capacity:2},
 {op:'flow-spray',flowId:1,emitterId:1,fraction:.5,particleVolume:.01},
 {op:'waterfall',channelSurfaceId:1,sheetSurfaceId:2,flowId:1,channelStage:'channel',sheetStage:'sheet',referenceFlux:2,drop:4},
 {op:'surface-water',surfaceId:1,capacity:4},
 {op:'surface-water-transfer',fromTriangle:0,toTriangle:1,volume:.1},
 {op:'surface-water-link',id:1,fromTriangle:0,toTriangle:1,rate:2},
 {op:'surface-water-reemit',triangleIndex:0,emitterId:1,volume:.1},
 {op:'surface-thermal',triangleIndex:0,temperature:300,capacity:2},
 {op:'surface-thermal-link',id:1,fromTriangle:0,toTriangle:1,conductance:3},
 {op:'surface-thermal-transfer',fromTriangle:0,toTriangle:1,energy:10},
 {op:'surface-thermal-power',triangleIndex:0,power:4},
 {op:'cell-art',id:1,width:1,height:1,cells:[[65,0xffffff,0]]},
 {op:'paste',text:'é'},
 {op:'select',anchor:0,caret:2,unit:'grapheme'},
 {op:'select',id:1,durationMs:0},
];
// @ts-expect-error Selection namespaces cannot be combined.
const mixed:NativeCommand={op:'select',id:1,anchor:0};
// @ts-expect-error A flow creation must declare its stages.
const missingStages:NativeCommand={op:'flow',id:1,flux:1};
// @ts-expect-error A transfer names exact source and target cells.
const missingTarget:NativeCommand={op:'surface-thermal-transfer',fromTriangle:0,energy:10};
void [commands,mixed,missingStages,missingTarget];

// @ts-expect-error The extrusion requires a declared maximum depth.
const missingDepth:NativeCommand={op:"flow-thickness",surfaceId:1,width:2,speed:2};
void missingDepth;

const release:NativeCommand={op:'aggregate-reemit',tileIndex:0,count:2,velocity:[0,3,0]};
// @ts-expect-error Aggregate launch velocity is explicit.
const missingVelocity:NativeCommand={op:'aggregate-reemit',tileIndex:0,count:2};
// @ts-expect-error Launch velocity is a world-space triple.
const wrongVelocity:NativeCommand={op:'aggregate-reemit',tileIndex:0,count:2,velocity:[0,3]};
void [release,missingVelocity,wrongVelocity];
