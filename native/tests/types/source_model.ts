import type {NativeCommand} from '../../bindings/typescript/contracts.js';
import type {NativeScene} from '../../bindings/typescript/native_scene.mjs';
const commands:NativeCommand[]=[{op:'model-view',width:80,height:32,controls:{sampling:1,projection:0,cameraZ:-85}},{op:'remove-model-view'}];
declare const scene:NativeScene;scene.setModelRecords(new Uint8Array());const records:Uint8Array=scene.modelRecords();void commands;void records;
// @ts-expect-error model geometry is a direct resource upload, never a scene preset
const bad:NativeCommand={op:'model-view',scene:'silt'};
// @ts-expect-error original model sampling is half or braille
const badSampling:NativeCommand={op:'model-view',controls:{sampling:2}};

import {parseOBJ,modelRecordsFromTriangles} from '../../bindings/typescript/obj_model.mjs';
const asset=parseOBJ('v 0 0 0',{upAxis:'Z'});scene.setModelRecords(modelRecordsFromTriangles(asset.triangles));
// @ts-expect-error only original Y/Z axes are supported
parseOBJ('',{upAxis:'X'});
