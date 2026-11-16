import {decodeGalleryModel,verifyGalleryModel} from '../../bindings/typescript/gallery_resources.mjs';
import {NativeScene} from '../../bindings/typescript/native_scene.mjs';
declare const scene: NativeScene;
const study={commands:[{op:'reset' as const}],modelRecords:'',modelVisibleMinCells:1};
const records:Uint8Array|null=decodeGalleryModel(study);
verifyGalleryModel(scene,study,records);
// @ts-expect-error resources are canonical base64 text, never an unowned numeric array
decodeGalleryModel({commands:[],modelRecords:[1,2,3]});
// @ts-expect-error raster minimum is a count
verifyGalleryModel(scene,{commands:[],modelVisibleMinCells:'many'},null);
// @ts-expect-error owned records are a typed byte buffer
verifyGalleryModel(scene,study,[0]);
