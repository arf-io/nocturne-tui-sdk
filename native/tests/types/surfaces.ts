/** Compile-time command shape checks; native validation owns bounds/references. */
import type {NativeCommand,ColliderSelection,SurfaceOptions,MeshTriangle} from '../../bindings/typescript/contracts.js';
const surface:SurfaceOptions={id:1,collisionEnabled:true,renderVisible:false,wetnessGain:.2,heatColor:0xff8844};
const collider:ColliderSelection={floor:false,surfaces:[1]};
const triangle:MeshTriangle={a:[0,0,0],b:[1,0,0],c:[0,1,0],surfaceId:1};
const commands:NativeCommand[]=[{op:'surface',...surface},{op:'mesh',triangles:[triangle]},
 {op:'emitter',id:1,colliders:collider},{op:'emitter-colliders',id:1,colliders:{floor:true}},
 {op:'clear-surface',id:1,scope:'response'}];
// @ts-expect-error Collider flags are booleans, not truthy numbers.
const invalidFlag:ColliderSelection={floor:1};
// @ts-expect-error Named-surface response has no universal unlimited overflow.
const invalidOverflow:SurfaceOptions={id:1,overflow:'unbounded'};
// @ts-expect-error Geometry is authored data, with no asset-loader callback.
const executableTriangle:MeshTriangle={a:[0,0,0],b:[1,0,0],c:[0,1,0],load:()=>null};
// @ts-expect-error Explicit clearing requires a declared bounded scope.
const invalidClear:NativeCommand={op:'clear-surface',id:1,scope:'everything-everywhere'};
void [commands,invalidFlag,invalidOverflow,executableTriangle,invalidClear];
const refined:NativeCommand={op:'mesh',subdivisions:4,triangles:[triangle]};
// @ts-expect-error Physical refinement has an integer numeric authoring field.
const badRefinement:NativeCommand={op:'mesh',subdivisions:'four',triangles:[triangle]};
void [refined,badRefinement];
const oceanCommands:NativeCommand[]=[
 {op:'surface-waves',surfaceId:1,waves:[[.2,.1,0,2,0]]},
 {op:'surface-foam',surfaceId:1,enabled:true,sourceRate:2,curvatureThreshold:.1,decay:1,impactGain:.001},
 {op:'clear-surface-foam',surfaceId:1},
 {op:'float-body',id:1,surfaceId:1,position:[0,0,0],mass:1000,radius:1},
 {op:'remove-float-body',id:1},
];
void oceanCommands;

const pathCommand:NativeCommand={op:'ribbon',points:[[0,0,0],[4,1,2]],widths:[1,2],surfaceId:1};
// @ts-expect-error Ribbon width forms are mutually exclusive.
const badPath:NativeCommand={op:'ribbon',points:[[0,0,0],[1,0,0]],width:1,widths:[1,1]};
void [pathCommand,badPath];

import type {NativeScene} from '../../bindings/typescript/native_scene.mjs';
declare const travelScene:NativeScene;
travelScene.pathSample([[0,0,0],[1,0,0]],3,{mode:'reverse'});

const retainedPath:NativeCommand={op:'path-travel',id:1,target:{family:'camera',id:0},points:[[0,0,0],[1,0,0]],speed:2};void retainedPath;

const composedMesh:NativeCommand={op:'mesh',append:true,triangles:[triangle]};void composedMesh;

const splineRibbon:NativeCommand={op:'ribbon',points:[[0,0,0],[1,0,0],[1,0,1]],interpolation:'catmull-rom',subdivisions:4};
// @ts-expect-error Native subdivisions require Catmull–Rom interpolation.
const linearSubdivision:NativeCommand={op:'ribbon',points:[[0,0,0],[1,0,0]],interpolation:'linear',subdivisions:4};
void [splineRibbon,linearSubdivision];

const hydraulicWidth:NativeCommand={op:'flow-thickness-settings',surfaceId:1,width:2};
const hydraulicSpeed:NativeCommand={op:'flow-thickness-settings',surfaceId:1,speed:3};
const hydraulicBoth:NativeCommand={op:'flow-thickness-settings',surfaceId:1,width:2,speed:3};
// @ts-expect-error Hydraulic edits require at least one retained setting.
const hydraulicEmpty:NativeCommand={op:'flow-thickness-settings',surfaceId:1};
// @ts-expect-error Envelope geometry is not editable through hydraulic settings.
const hydraulicEnvelope:NativeCommand={op:'flow-thickness-settings',surfaceId:1,width:2,maxDepth:4};

const carriedHeat:NativeCommand={op:'surface-water-transfer',fromTriangle:0,toTriangle:1,volume:2,heatCapacityPerVolume:10};
// @ts-expect-error Heat capacity is numeric; native validation also rejects nonnumeric input.
const invalidCarriedHeat:NativeCommand={op:'surface-water-transfer',fromTriangle:0,toTriangle:1,volume:2,heatCapacityPerVolume:'ten'};
void [carriedHeat,invalidCarriedHeat];

const hydraulicHeat:NativeCommand={op:"surface-water-link",id:1,fromTriangle:0,toTriangle:1,rate:1,heatCapacityPerVolume:10};void hydraulicHeat;

const latentHeat:NativeCommand={op:"surface-water-thermal",triangleIndex:0,latentHeatPerVolume:100};void latentHeat;

const materialHeat:NativeCommand={op:"material-thermal",id:1,temperature:500,capacity:10,contactFraction:.25,conductance:100};
const removeMaterialHeat:NativeCommand={op:"remove-material-thermal",id:1};void [materialHeat,removeMaterialHeat];
