import type {CellArtCommand} from './contracts.js';
export interface FontPresentation {family:string|null;fileName:string|null;sha256:string|null;format:'OpenType/CFF'|'TrueType'|null;engine:'browser OpenType';byteLength?:number;}
export interface FontGallery {metadata():FontPresentation;canvasFont(size?:number):string;reset():FontPresentation;load(source:ArrayBuffer|ArrayBufferView,fileName?:string):Promise<(FontPresentation&{applied:true})|{applied:false}>;}
export function createFontGallery():FontGallery;
export function parseTdfCellArtImport(value:unknown):{op:'batch';commands:CellArtCommand[]};
