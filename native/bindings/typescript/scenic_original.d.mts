import type {NativeScene} from './native_scene.mjs';
import type {SceneArtName,SceneArtDetailControls} from './contracts.js';
export type OriginalScenicName=Exclude<SceneArtName,'red-shift'>;
export interface ScenicRatePatch {landscapeSpeed?:number;waterFlow?:number;}
export interface ScenicRateRow {atMs:number;position:number;rate:number;}
export interface ScenicClockSnapshot {version:1;scene:OriginalScenicName;landscapeSpeed:number;waterFlow:number;surface:ScenicRateRow[];water:ScenicRateRow[];}
export class ScenicOriginalClock {constructor(name:OriginalScenicName);scene:OriginalScenicName;landscapeSpeed:number;waterFlow:number;configure(timeMs:number,patch:ScenicRatePatch):void;sample(timeMs:number):{op:'scene-art';timeMs:number;controls:{flow:number;travel:number}};snapshot():ScenicClockSnapshot;static fromSnapshot(snapshot:ScenicClockSnapshot):ScenicOriginalClock;}
export class ScenicOriginalSession {constructor(scene:NativeScene,name:OriginalScenicName);clock:ScenicOriginalClock;commit():void;advanceTo(timeUs:number,budget?:number):number;configure(patch:ScenicRatePatch):void;checkpoint():{version:1;clock:ScenicClockSnapshot;native:Uint8Array};restore(snapshot:{version:1;clock:ScenicClockSnapshot;native:Uint8Array}):void;}
export const SCENIC_PRESETS:Readonly<Record<'moonlight'|'winter-swell',Readonly<SceneArtDetailControls>>>;
export const SCENIC_WORLD_FIELDS:readonly {name:string;index:number;min:number;max:number;scale:number;default:number}[];
export const SCENIC_DETAIL_FIELDS:typeof SCENIC_WORLD_FIELDS;
