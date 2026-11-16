import type {NativeCommand} from '../../bindings/typescript/contracts.js';
const road:NativeCommand={op:'ribbon',append:true,points:[[0,0,0],[0,0,-10]],width:4,surfaceId:1};
const travel:NativeCommand={op:'path-travel',id:1,target:{family:'camera',id:0},points:[[0,1.7,0],[0,1.7,-10]],speed:2,mode:'reverse'};
// @ts-expect-error camera is a singleton target
const bad:NativeCommand={op:'path-travel',id:2,target:{family:'camera',id:99},points:[[0,0,0],[1,0,0]]};
void [road,travel,bad];
