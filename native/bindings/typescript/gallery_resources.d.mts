import type {NativeCommand} from './contracts.js';
import type {NativeScene} from './native_scene.mjs';
/** Explicit imported source geometry, encoded in canonical aligned base64. */
export interface GalleryModelStudy {commands:readonly NativeCommand[];modelRecords?:string;modelVisibleMinCells?:number;}
/** Decode before touching native state; null means this recipe has no resource. */
export function decodeGalleryModel(study:GalleryModelStudy):Uint8Array|null;
/** Verify owned bytes and optional visible full-model raster; restore the saved state. */
export function verifyGalleryModel(scene:NativeScene,study:GalleryModelStudy,records:Uint8Array|null):void;
