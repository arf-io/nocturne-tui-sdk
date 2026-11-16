# WASM and TypeScript reference

`native_scene.mjs` wraps the import-free WASM core. `native_scene.d.mts` declares copied frame and query types; `contracts.ts` declares native commands. [Web integration](Web.md) covers canvas, DOM, input and accessibility.

## Runnable Node example

Run `node docs/current/examples/panel.mjs` from the SDK root. The program reads [panel.json](examples/panel.json), updates a value and restores a checkpoint.

```javascript
import {readFile} from 'node:fs/promises';
import {NativeScene} from '../../../native/bindings/typescript/native_scene.mjs';
const wasm = await readFile(new URL('../../../native/dist/nocturne_native.wasm', import.meta.url));
const scene = await NativeScene.create(wasm, 2030);
try {
  scene.command(JSON.parse(await readFile(new URL('./panel.json', import.meta.url), 'utf8')));
  scene.advanceTo(500_000);
  const frame = scene.render();
  const checkpoint = scene.snapshot();
  scene.command({op:'widget', id:1, value:0.8});
  scene.restore(checkpoint);
  console.log(frame.width, frame.height, frame.bytes.length);
} finally { scene.close(); }
```

`NativeScene.create(bytes,seed)` is asynchronous. `command` is synchronous and throws on rejection. `advanceTo` drains the native target; `render` returns width, height, byte and cell arrays. `infoComplete` assembles the full metadata stream. `close` releases binding allocations. Do not retain WASM heap views across memory growth.

## Type checking

Import `NativeCommand` from the SDK contract and annotate authoring values. Runtime validation remains authoritative for imported JSON. The shared project exporter writes executable TypeScript and JavaScript from the same normalized project used by Gallery.

## Runtime contract

Commands are native transactions. Rejection preserves authoritative state; catch-up pending means more work remains. Serialize operations on one scene. The binding returns copied frames, snapshots and complete metadata. Supply integer microseconds; rendering does not advance time.

The binding grows prompt, model, modal and render storage. Resource IDs and bounded emitter/window/node pools retain their declared native domains; those are separate from document length. Keep the core and binding from a compatible SDK. Use complete metadata when source exceeds ordinary readback capacity.

![Progress component](images/widget-progress-default.png)

## Public method index

The shipped binding declares the following methods. Geometry, text and resource query names correspond to the [C declarations](C.md).

- `static create(bytes:BufferSource,seed?:number):Promise<NativeScene>;`
- `command(command:NativeCommand):number;`
- `advanceTo(timeUs:number):void;`
- `render():NativeFrame;`
- `info():NativeMetadata;`
- `infoComplete(maxBytes?:number|null):NativeMetadata;`
- `setModelRecords(records:Uint8Array):void;`
- `modelRecords():Uint8Array;`
- `snapshot():Uint8Array;`
- `restore(bytes:Uint8Array):void;`
- `particles():number[][];`
- `scriptRuns(text:string):Array<[number,number,string]>;`
- `bidiLines(text:string,ends:number[],direction?:number):number[][];`
- `lineBreaks(text:string):number[];`
- `lineBreakDetails(text:string):[number,number][];`
- `graphemeBoundaries(text:string):number[];`
- `graphemeWidths(text:string,ambiguous?:1|2):[number,number,number][];`
- `negotiateShortcuts(actions:number[],candidates:number[][],host:number[][]):number[][];`
- `textRunClusters(kind:number,id:number):number[][];`
- `textRunSource(kind:number,id:number):string;`
- `textRunLayout(kind:number,id:number,columns:number,ambiguous?:number):number[][];`
- `textRunHit(kind:number,id:number,columns:number,column:number,row:number,ambiguous?:number):number;`
- `textRunClip(kind:number,id:number,columns:number,x:number,y:number,width:number,height:number,ambiguous?:number):number[][];`
- `bidiVisual(text:string,direction?:number):number[][];`
- `surfaceFoam(id:number):number[][];`
- `surfaceFoamTransport(id:number):number[][];`
- `promptLayout():number[][];`
- `promptVisualLayout():number[][];`
- `areaGeometry(id:number):number[]|null;`
- `fieldSample(id:number,x:number,y:number):number[]|null;`
- `thermalSample(triangleIndex:number):number[]|null;`
- `hullImmersion(vertices:readonly (readonly [number,number,number])[],faces:readonly (readonly [number,number,number])[],height:number):number[];`
- `hullImmersionPlane(vertices:readonly (readonly [number,number,number])[],faces:readonly (readonly [number,number,number])[],point:readonly [number,number,number],normal:readonly [number,number,number]):number[];`
- `fluidDragExchange(bodyMass:number,waterMass:number,conductance:number,seconds:number,bodyVelocity:readonly [number,number,number],waterVelocity:readonly [number,number,number]):number[];`
- `angularDragExchange(bodyInertia:readonly [number,number,number],waterInertia:readonly [number,number,number],conductance:readonly [number,number,number],seconds:number,bodyOmega:readonly [number,number,number],waterOmega:readonly [number,number,number]):number[];`
- `hullBuoyancyPlane(vertices:readonly (readonly [number,number,number])[],faces:readonly (readonly [number,number,number])[],point:readonly [number,number,number],normal:readonly [number,number,number],options:{density:number;gravity:number;mass:number;centerOfMass:readonly [number,number,number]}):number[];`
- `waterSample(triangleIndex:number):number[]|null;`
- `flowThickness(id:number):number[]|null;`
- `surfaceTriangles(id:number):number[][];`
- `floatBody(id:number):number[]|null;`
- `floatHull(id:number):number[]|null;`
- `surfaceFluid(id:number):number[]|null;`
- `surfaceFluidAngular(id:number):number[]|null;`
- `hullMeshImmersion(vertices:readonly (readonly [number,number,number])[],faces:readonly (readonly [number,number,number])[],water:readonly (readonly [number,number,number,number,number,number,number,number,number])[]):number[];`
- `surfaceWaveSample(id:number,x:number,z:number):number[];`
- `pathSample(points:readonly (readonly [number,number,number])[],distance:number,options?:{closed?:boolean;mode?:'clamp'|'loop'|'reverse'}):number[];`
- `waveSample(waves:number[][],x:number,z:number,seconds:number):number[];`
- `documentLayout(text:string,columns:number,direction?:number,ambiguous?:number):number[][];`
- `documentBoundaries(text:string):number[];`
- `documentHit(text:string,columns:number,column:number,row:number,direction?:number,ambiguous?:number):number;`
- `documentCaret(text:string,columns:number,offset:number,affinity?:number,direction?:number,ambiguous?:number):number[];`
- `bidiLayout(text:string,columns:number,direction?:number,ambiguous?:number):number[][];`
- `bidiHit(text:string,columns:number,column:number,row:number,direction?:number,ambiguous?:number):number;`
- `bidiCaret(text:string,columns:number,offset:number,affinity?:number,direction?:number,ambiguous?:number):number[];`
- `selectedText():string|null;`
- `graphemeHit(text:string,columns:number,column:number,row:number,ambiguous?:1|2):number;`
- `graphemeLayout(text:string,columns:number,ambiguous?:1|2):[number,number,number,number,number][];`
- `particleMotions():number[][];`
- `textSample(id:number,index:number):number[];`
- `textClusterSample(id:number,index:number):number[];`
- `textTrailSample(id:number,index:number,trailIndex:number):number[];`
- `windowSample(id:number,u:number,v:number,visibility:number):number[];`
- `batch(commands:readonly SceneEdit[]):number;`
- `schedule(id:number,atUs:number,command:SceneEdit):number;`
- `cancelScheduled(id:number):number;`
- `close():void;`
- `sourceStageOklch(lightness:number,chroma:number,hue:number):number;`
- `sourceStageTween(from:number,to:number,elapsedMs:number,durationMs:number,easing?:0|1|2|3):number;`
- `sourceStageInkOpacity(ageMs:number,fadeMs:number,rowQ8:number,bandQ8:number,topMinimum:number):number;`
- `sourceStageHit(x:number,y:number):{id:number;item:number}|null;`
- `catalogue():{id:string;name:string;contract:string}[];`
- `oklch(l:number,c:number,h:number):number;`
- `composite(base:number,source:number,baseAlpha?:number,sourceAlpha?:number,blend?:number,operation?:number,seed?:number):{rgb:number;alpha:number};`
- `compositeInSpace(base:number,source:number,space:0|1|2|3,baseAlpha?:number,sourceAlpha?:number,blend?:number,operation?:number,seed?:number):{rgb:number;alpha:number};`
- `inspectCharacterCell(x:number,y:number):CharacterCellInfo;`

[Common command field reference](Commands.md).
