import type {NativeCommand,CameraControlsOptions,CameraControlsInfo} from '../../bindings/typescript/contracts.js';
import {NativeScene} from '../../bindings/typescript/native_scene.mjs';
declare const scene:NativeScene;
const config:CameraControlsOptions={enabled:true,rig:'spacecraft',mode:'fly',inputTarget:'head',inputAxes:{x:{action:'look-y',sensitivity:2.5,invert:true,enabled:true},y:{action:'pan-y',sensitivity:0,invert:false,enabled:false},z:{action:'orbit-z',sensitivity:1}},head:{position:[1,2,3],rotation:[10,20,30]},crane:{pivot:[0,1,0],boom:[0,10,20]},follow:{target:{kind:'node',id:1},offset:[0,4,12],track:true},anchor:[0,0,0]};
scene.command({op:'camera-controls',...config});
for(const rig of ['orbit','head','dolly','crane','follow','spacecraft'] as const)scene.command({op:'camera-controls',rig});
scene.command({op:'camera-controls',follow:{target:{kind:'point',point:[0,3,4]}},anchor:null});
scene.command({op:'camera-controls',enabled:false});
const command:NativeCommand={op:'camera-controls',inputAxes:{z:{action:'disabled'}}};scene.command(command);
const controls:CameraControlsInfo=scene.info().camera.controls;
const action:string=controls.inputAxes.z.action;const sensitivity:number=controls.inputAxes.x.sensitivity;const flag:boolean=controls.enabled;
void action;void sensitivity;void flag;
// @ts-expect-error unsupported camera rig
scene.command({op:'camera-controls',rig:'truck'});
// @ts-expect-error finite native axis action domain
scene.command({op:'camera-controls',inputAxes:{x:{action:'spin'}}});
// @ts-expect-error native input axes are x/y/z only
scene.command({op:'camera-controls',inputAxes:{w:{action:'orbit-x'}}});
// @ts-expect-error reset accepts no configuration fields
scene.command({op:'camera-controls',enabled:false,rig:'head'});
// @ts-expect-error native vector has exactly three components
scene.command({op:'camera-controls',head:{rotation:[1,2]}});
// @ts-expect-error node target requires ID
scene.command({op:'camera-controls',follow:{target:{kind:'node'}}});
// @ts-expect-error point target requires point, not a node ID
scene.command({op:'camera-controls',follow:{target:{kind:'point',id:1}}});
// @ts-expect-error input target domain
scene.command({op:'camera-controls',inputTarget:'world'});
// @ts-expect-error boolean inversion
scene.command({op:'camera-controls',inputAxes:{x:{invert:1}}});

scene.command({op:'camera-input',delta:[1,-2,3]});
scene.command({op:'camera-input',delta:[1,0,0],pan:true});
// @ts-expect-error delta is mandatory
scene.command({op:'camera-input'});
// @ts-expect-error delta has exactly three coordinates
scene.command({op:'camera-input',delta:[1,2]});
// @ts-expect-error pan is boolean
scene.command({op:'camera-input',delta:[0,0,0],pan:1});

const carrier:{position:readonly[number,number,number];yaw:number;pitch:number;roll:number}=scene.info().camera.carrier;
void carrier;
