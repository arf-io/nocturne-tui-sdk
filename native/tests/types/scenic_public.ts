import type {
  NativeCommand, SceneArtControls, SceneArtDetailControls, SceneArtInfo,
  SceneArtOptions, ValueDefinition,
} from '../../bindings/typescript/contracts.js';
import type {NativeScene} from '../../bindings/typescript/native_scene.mjs';

const scenes: SceneArtOptions[] = [
  {scene:'pearl-cascade'},
  {scene:'tidal-glass',controls:{waterAlpha:0.55},detail:{waveHeight:2.0,foam:0.2}},
  {scene:'copper-causeway',width:120,height:40,controls:{travel:7,projection:1}},
  {scene:'silt',controls:{accent:8360827,seed:2030}},
  {scene:'red-shift',controls:{redshift:0.2,discTilt:12}},
];

const allSourceControls: Required<SceneArtControls> = {
  cameraX:-68,cameraY:48,cameraZ:-96,yaw:35,pitch:-22,roll:0,fov:62,
  projection:1,span:145,flow:1,travel:0,seed:2030,redshift:0.7,
  discTilt:12,detail:1,waterAlpha:0.94,background:1053726,ink:0,
  accent:0,secondary:0,sampling:1,
};
const allDetailControls: Required<SceneArtDetailControls> = {
  waveHeight:358/256,wavelength:34,windAngle:22,crossSwell:0.48,
  choppiness:0.43,foam:0.62,waveSpeed:1,joinRiver:1,
};
const activate: NativeCommand = {
  op:'scene-art',scene:'pearl-cascade',width:120,height:40,
  controls:allSourceControls,detail:allDetailControls,
};
const patch: NativeCommand = {op:'scene-art',controls:{cameraZ:-110},detail:{foam:0.3}};
const remove: NativeCommand = {op:'remove-scene-art'};
const workbench: NativeCommand = {op:'environment',presentation:'workbench'};
const canvas: NativeCommand = {op:'environment',presentation:'canvas'};
const presentationValue:ValueDefinition = {
  op:'define',path:'/environment/presentation',value:1,
  binding:{family:'environment',id:0,field:'presentation'},
};

const q24:SceneArtInfo['worldQ'] = [120,40,0,-17408,12288,-24576,8960,-5632,
  0,15872,1,37120,1000,0,2030,700,3072,1,940,1053726,0,0,0,1];
const q8:SceneArtInfo['detailQ'] = [358,8704,5632,480,430,620,1000,1];
const info:SceneArtInfo = {
  scene:'pearl-cascade',hasWorldDetail:true,timeMs:null,worldQ:q24,detailQ:q8,
  controls:{...allSourceControls,width:120,height:40,scene:0},detail:allDetailControls,
  effective:{timeMs:0,worldQ:q24,detailQ:q8,
    controls:{...allSourceControls,width:120,height:40,scene:0},
    detail:allDetailControls,width:120,height:40},
};
declare const scene:NativeScene;
const readback:SceneArtInfo|null = scene.info().sceneArt;
const presentationReadback:'workbench'|'canvas' = scene.info().environment.presentation;

// @ts-expect-error scene identities are a closed original family
const badScene:SceneArtOptions = {scene:'waterfall'};
// @ts-expect-error source authoring names are retained and closed
const badControl:SceneArtOptions = {scene:'silt',controls:{crest:2}};
// @ts-expect-error projection is the original binary selector
const badProjection:SceneArtOptions = {scene:'silt',controls:{projection:2}};
// @ts-expect-error detail control names are closed
const badDetail:SceneArtOptions = {scene:'tidal-glass',detail:{foamLevel:0.4}};
// @ts-expect-error canvas is a named public policy
const badPresentation:NativeCommand = {op:'environment',presentation:'fullscreen'};
// @ts-expect-error removal has no patch payload
const badRemove:NativeCommand = {op:'remove-scene-art',scene:'silt'};

void [scenes,allSourceControls,allDetailControls,activate,patch,remove,
  workbench,canvas,presentationValue,info,badScene,badControl,badProjection,badDetail,
  badPresentation,badRemove,readback,presentationReadback];
