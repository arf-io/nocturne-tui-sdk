/** Original OBJ geometry and authored vertex-lighting result. */
export interface ModelTriangle {vertices:number[];color:number}
export interface ImportedModel {version:1;name:string;vertexCount:number;triangles:ModelTriangle[];warnings:string[];originalBounds:{min:number[];max:number[]}}
export function parseOBJ(text:string,options?:{name?:string;size?:number;upAxis?:'Y'|'Z'}):ImportedModel;
/** Owned little-endian nine signed Q8 coordinates plus RGB per 40-byte record. */
export function modelRecordsFromTriangles(triangles:ModelTriangle[]):Uint8Array;
