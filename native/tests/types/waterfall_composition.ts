import type {NativeCommand} from '../../bindings/typescript/contracts.js';
const pipeline:NativeCommand={op:'batch',commands:[
 {op:'waterfall',channelSurfaceId:1,sheetSurfaceId:2,flowId:1,channelStage:'channel',sheetStage:'sheet',referenceFlux:2,drop:3},
 {op:'flow-thickness',surfaceId:1,width:4,speed:2,maxDepth:1,direction:[0,1,0]},
 {op:'flow-sink',surfaceId:3,flowId:1,fraction:.75,capacity:10,evaporationUs:0},
 {op:'flow-spray',flowId:1,emitterId:1,fraction:.25,particleVolume:.025},
 {op:'define',path:'/waterfall/flux',value:2,binding:{family:'flow',id:1,field:'flux'}}]};
// @ts-expect-error flow cannot be controlled by unrelated alpha bindings
const unrelated:NativeCommand={op:'define',path:'/flow',value:2,binding:{family:'flow',id:1,field:'alpha'}};
void [pipeline,unrelated];
