import type {NativeMetadata} from '../../bindings/typescript/native_scene.mjs';
declare const info:NativeMetadata;
const dimensions:2|3=info.graph.dimensions;
const mode:'layered'|'force'|'radial'=info.graph.layoutMode;
const kind:'contains'|'depends'|'parent'|'reference'|'produces'|'related'=info.graph.edges[0].kind;
const pinned:boolean=info.nodes[0].pinned;
const target:readonly [number,number,number]=info.nodes[0].targetPosition;
// @ts-expect-error typed edge kind cannot be an unsupported relation
const bad:'unknown'=info.graph.edges[0].kind;
void [dimensions,mode,kind,pinned,target,bad];
