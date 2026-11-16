import type {NativeScene} from '../../bindings/typescript/native_scene.mjs';
declare const scene:NativeScene;
const scripts:Array<[number,number,string]>=scene.scriptRuns('office سلام');
const lines:number[][]=scene.bidiLines('office سلام',[7,11],2);
// @ts-expect-error Script tags are strings, not encoded native words.
const encoded:Array<[number,number,number]>=scene.scriptRuns('office');
// @ts-expect-error Explicit line ends use Unicode scalar offsets.
scene.bidiLines('office',['6']);
// @ts-expect-error Native text readers accept Unicode strings.
scene.scriptRuns([97]);
void [scripts,lines,encoded];
const vertices:readonly (readonly [number,number,number])[]=[[0,0,0],[1,0,0],[0,1,0],[0,0,1]];
const faces:readonly (readonly [number,number,number])[]=[[0,2,1],[0,1,3],[0,3,2],[1,2,3]];
const immersion:number[]=scene.hullImmersionPlane(vertices,faces,[0,.5,0],[0,1,0]);
const wrench:number[]=scene.hullBuoyancyPlane(vertices,faces,[0,.5,0],[0,1,0],{density:48,gravity:1,mass:7,centerOfMass:[0,0,0]});
// @ts-expect-error Wrench calculations require an explicit center of mass.
scene.hullBuoyancyPlane(vertices,faces,[0,.5,0],[0,1,0],{density:48,gravity:1,mass:7});
void [immersion,wrench];
const exchange:number[]=scene.fluidDragExchange(2,3,4,.5,[1,0,0],[0,0,0]);
// @ts-expect-error Velocity inputs must be complete XYZ triples.
scene.fluidDragExchange(2,3,4,.5,[1,0],[0,0,0]);
void exchange;
const angular:number[]=scene.angularDragExchange([2,4,8],[3,5,7],[4,0,2],.5,[5,-2,1],[-1,3,0]);
// @ts-expect-error Angular exchange requires explicit inertia XYZ triples.
scene.angularDragExchange(2,[3,5,7],[4,0,2],.5,[5,-2,1],[-1,3,0]);
void angular;
const angularMetadata=scene.info().surfaceFluidAngular?.[0];
const exports:number|undefined=angularMetadata?.history.exports;
const recordPresent:boolean|undefined=angularMetadata?.recordPresent;
const world:'world'=scene.info().contract.queryContracts.nrSurfaceFluidAngular.frame;
void [exports,recordPresent,world];
