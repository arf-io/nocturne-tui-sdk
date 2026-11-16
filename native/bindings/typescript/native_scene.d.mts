import type {NativeCommand,SceneEdit,StatusRecord,NotificationIntent,RegisteredStateInfo,StyleRuleInfo,SurfaceInfo,GeometryInfo,SurfaceContactInfo,EventPayload,ValueDescriptor,CharacterRule,SceneArtInfo,EnvironmentPresentation} from './contracts.js';
export interface NativeFrame {width:number;height:number;bytes:Uint8Array;cells:Uint32Array;}
export interface CharacterCellInfo {glyph:number;foreground:number;background:number;id:number;index:number;role:string;state:string;path:string;}
export interface SurfaceWaveQueryContract {capacityUnit:'double';rowWords:6;alignmentBytes:8;ownedBindings:true;pure:true;presentReturn:1;invalidReturn:-1;contextOverlapAllowed:false;invalidOutputUnchanged:true;fields:string[];modeSelector:'surfaceFluidAngular[].pose';analyticMode:{coverage:'infinite-authored-wave-field';normalFrame:'world-unrotated';verticalVelocity:'wave-plus-reservoir-vertical-translation';laplacian:'analytic-authored-xz'};posedMode:{coverage:'topmost-world-facet';normalFrame:'world-upward';verticalVelocity:'material-world-y';laplacian:'within-facet-zero';equalHeightTie:'source-order';verticalFacet:'no-height';uncoveredReturn:-1};}
export interface LineBreakQueryContract {capacityUnit:'offset'|'row';rowWords:1|2;alignmentBytes:4;maxSourceScalars:2048;ownedBindings:true;pure:true;invalidReturn:-1;invalidOutputUnchanged:true;inputOutputAliasAllowed:true;nullOutputSizeProbe:true;profile:'unicode-17.0.0-uax14-55-default';offsetUnit:'unicode-scalar';endOfTextIncluded:true;fields:string[];mandatoryValues?:[0,1];}
export interface GraphEdgeInfo {from:number;to:number;kind:'contains'|'depends'|'parent'|'reference'|'produces'|'related';}
export interface SourceGraphLayoutInfo {seed:number;dimensions:2|3;mode:'layered'|'force'|'radial';iterations:number;sweeps:number;orientation:'LR'|'TB';nodeGap:number;layerGap:number;depthGap:number;repulsion:number;spring:number;linkLength:number;damping:number;timeStep:number;collision:number;nodeSizes:Array<{id:number;width:number;height:number}>;edgeWeights:Array<GraphEdgeInfo & {weight:number}>;}
export interface SourceSkyInfo {worldSeed:number;skyDensity:number;skyRadius:number;skyExposure:number;trailMs:number;textLightness:number;textChroma:number;}
export interface GraphInfo {layoutProfile:'source'|'measured';sourceLayout:SourceGraphLayoutInfo|null;dimensions:2|3;layoutMode:'layered'|'force'|'radial';lastLayoutUnresolvedNodes:number;edges:GraphEdgeInfo[];}
export interface GraphNodeInfo {id:number;label:string;detail:string;kind:string;status:string;sha:string;position:readonly [number,number,number];targetPosition:readonly [number,number,number];pinned:boolean;[key:string]:unknown;}
export interface NativeMetadata {
 emitters:Array<{id:number;effect:string;phase:'scheduled'|'emitting'|'draining'|'settled'|'terminal';novaOptics?:{sampleLimit:16;activeCapturedParticles:number;samples:Array<[number,number,number,number,number,number,number,number]>};worldShellProfile?:{shape:'clumpy-fibonacci'|'uniform-fibonacci';active:boolean;radiusAtBirth:number;radialExpansionRate:number};burstStages?:{sampleLimit:16;activeBurstParticles:number;glitterHz:number;glitterDepth:number;coreAlpha:number;coreUs:number;residualUs:number;residualAlpha:number;samples:Array<[number,number,number,number,number,number]>};[key:string]:unknown}>;
 electricalArcs:Array<{id:number;seed:number;material:number;startUs:number;speed:number;jitter:number;flicker:number;alpha:number;delayUs:number;holdUs:number;fadeUs:number;repeatUs:number;phase:'waiting'|'leader'|'hold'|'fade'|'finished';cycle:number;opacity:number;points:Array<{position:[number,number,number];parent:number}>;segments:Array<[number,number,number,number,number,number,number]>}>;
 graph:GraphInfo;nodes:GraphNodeInfo[];sourceSky:SourceSkyInfo|null;
 contract:{metadataProfile:'nocturne.metadata/v1';commandProfile:'nocturne.commands/v1';abiVersion:number;snapshotSchema:number;sourceSchema:number;snapshotCapacityBytes:number;bindingFamilies:string[];features:string[];queryContracts:{nrAreaGeometry:{capacityUnit:'double';rowWords:12;alignmentBytes:8;ownedBindings:true;pure:true;absentReturn:0;presentReturn:1;invalidReturn:-1;contextOverlapAllowed:false;coordinates:'screen-cells';fields:string[]};nrFieldSample:{capacityUnit:'double';rowWords:4;alignmentBytes:8;ownedBindings:true;pure:true;absentReturn:0;presentReturn:1;invalidReturn:-1;contextOverlapAllowed:false;coordinates:'screen-cells';fields:string[]};nrLineBreaks:LineBreakQueryContract;nrLineBreakDetails:LineBreakQueryContract;nrSurfaceWaveSample:SurfaceWaveQueryContract;nrSurfaceFluidAngular:{capacityUnit:'double';rowWords:12;alignmentBytes:8;ownedBindings:true;pure:true;absentReturn:0;presentReturn:1;invalidReturn:-1;contextOverlapAllowed:false;frame:'world';inertiaModel:'isotropic';fields:string[]};nrSurfaceFluid:{capacityUnit:'double';rowWords:15;alignmentBytes:8;ownedBindings:true;pure:true;absentReturn:0;presentReturn:1;invalidReturn:-1;contextOverlapAllowed:false;fields:string[];lifecycleProperty:'surfaceFluids[].active';stoppedRecordPresent:true};nrFloatHull:{capacityUnit:'double';rowWords:14;alignmentBytes:8;ownedBindings:true;pure:true;absentReturn:0;presentReturn:1;invalidReturn:-1;contextOverlapAllowed:false;fields:string[]};nrThermalSample:{capacityUnit:'double';rowWords:10;alignmentBytes:8;ownedBindings:true;pure:true;absentReturn:0;presentReturn:1;invalidReturn:-1;contextOverlapAllowed:false;fields:string[]};nrWaterSample:{capacityUnit:'double';rowWords:8;alignmentBytes:8;ownedBindings:true;pure:true;absentReturn:0;presentReturn:1;invalidReturn:-1;contextOverlapAllowed:false;fields:string[]}}};
 surfaceFluidAngular?:Array<{surfaceId:number;recordPresent:boolean;active:boolean;exported:boolean;inertia:number;omega:number[];initialMomentum:number[];bodyImpulse:number[];pose:{orientation:[number,number,number,number];pivot:[number,number,number]}|null;dissipatedEnergy:number;initialEnergy:number;history:{inertia:number;energy:number;momentum:number[];initialMomentum:number[];bodyImpulse:number[];initialEnergy:number;dissipatedEnergy:number;exports:number}}>;
 surfaceFluids?:Array<{surfaceId:number;active:boolean;exported:boolean;history:{mass:number;energy:number;momentum:number[];initialMomentum:number[];bodyImpulse:number[];initialEnergy:number;dissipatedEnergy:number;exports:number};mass:number;velocity:number[];offset:number[];initialMomentum:number[];bodyImpulse:number[];dissipatedEnergy:number;initialEnergy:number}>;
 widgets:import('./contracts.js').WidgetInfo[];
 sourceModal:import('./contracts.js').SourceModalInfo;
 sourceStage:import('./contracts.js').SourceStageInfo;
 observatoryOverlay:import('./contracts.js').ObservatoryOverlayInfo;
 sourceStageComponents:import('./contracts.js').SourceStageComponentInfo[];
 windows:import('./contracts.js').WindowInfo[];
 areas:import('./contracts.js').AreaInfo[];
 values:Record<string,EventPayload>;valueDescriptors:Record<string,ValueDescriptor>;valueTypes?:Record<string,'boolean'|'string'|'json'>;
 characterRules:CharacterRule[];
 characterRegions:import('./contracts.js').CharacterRegion[];
 cellArt?:Array<{id:number;width:number;height:number;x:number;y:number;alpha:number;layer:'background'|'overlay';cells:number[][]}>;
 thermalLinks?:Array<{id:number;fromTriangle:number;toTriangle:number;conductance:number;startUs:number}>;
 aggregateReemittedCount:number;
 aggregateMaterials:{tileIndex:number;count:number;emitterId:number;emitterGeneration:number;material:number;seed:number;emissionOrdinal:number;canReemit:boolean}[];
 materialThermal?:{initialEnergy:number;liveEnergy:number;importedEnergy:number;transferredEnergy:number;exportedEnergy:number;materials:ThermalCarrier[];particles:ThermalCarrier[];deposits:ThermalCarrier[];aggregates:ThermalCarrier[]};
 surfaceThermal?:{historicalLatentEnergy:number;exportedEnergy:number;historicalInitialEnergy:number;historicalAppliedEnergy:number;historicalEnvironmentEnergy:number;historicalImportedEnergy:number;historicalTransferredEnergy:number;cells:Array<{triangleIndex:number;temperature:number;energy:number;initialEnergy:number;appliedEnergy:number;environmentEnergy:number;importedEnergy:number;transferredEnergy:number;latentHeatPerVolume:number;evaporatedEnergy:number}>};
 waterLinks?:Array<{id:number;fromTriangle:number;toTriangle:number;rate:number;startUs:number;heatCapacityPerVolume?:number}>;
 surfaceWater?:Array<{surfaceId:number;receivedVolume:number;retainedVolume:number;evaporatedVolume:number;exportedVolume:number;importedVolume:number;transferredVolume:number;cells:Array<{triangleIndex:number;receivedVolume:number;retainedVolume:number;wetness:number;importedVolume:number;transferredVolume:number}>}>;
 flowSprays?:Array<{emitterId:number;flowId:number;receivedVolume:number;flowReceivedVolume:number;reentrainedVolume:number;emittedVolume:number;pendingVolume:number;liveVolume:number;expiredVolume:number;impactedVolume:number;exportedVolume:number;legacyUnresolvedVolume:number}>;
 flowSinks?:Array<{surfaceId:number;flowId:number;receivedVolume:number;retainedVolume:number;evaporatedVolume:number;wetness:number}>;
 flows?:Array<{id:number;flux:number;outletFlux:number;injectedVolume:number;deliveredVolume:number;storedVolume:number;stages:Array<{name:string;flux:number;deliveredVolume:number;storedVolume:number}>}>;
 namedRegisters?:Record<string,{text:string;linewise:boolean}>;
 vimRegister?:{text:string;linewise:boolean};build:string;registeredStates:RegisteredStateInfo[];styleRules:StyleRuleInfo[];messages:StatusRecord[];intents:NotificationIntent[];geometry:GeometryInfo;surfaces:SurfaceInfo[];contacts:SurfaceContactInfo[];clock:{timeUs:number;targetUs:number;step:number;paused:boolean};prompt:{firstPromptSource:null|{values:number[];palette:number[];starPalette:number[];glyphs:number[];visibleStart:number;visibleEnd:number;column:number;row:number;layer:{region:import('./contracts.js').PromptSourceRegion;bounds:{x:number;y:number;width:number;height:number}|null;z:'above';order:0;alpha:{fg:number;bg:number};frame:'visible'|'invisible'}};layout:'scalar'|'grapheme'|'bidi';direction:'ltr'|'rtl'|'auto';ambiguousWidth:1|2;text:string;caret:number;mode:number;revision:number;redoAvailable?:number};camera:{carrier:{position:import('./contracts.js').Vector3;yaw:number;pitch:number;roll:number};controls:import('./contracts.js').CameraControlsInfo;profile:'original'|'default';grabbed:number[]|null;target:number[];navigation:'orbit'|'fly'|'pan';position:number[];yaw:number;pitch:number;roll:number;near:number;far:number;fov:number;span:number;orthographic:boolean;flightActive:boolean};environment:{background:number;stars:number;starFar:number;sampling:string;style:string;presentation:EnvironmentPresentation;occlusionTint:number;occludedDots:import('./contracts.js').OccludedDots};sceneArt:SceneArtInfo|null;[key:string]:unknown;}
export class NativeScene {
 static create(bytes:BufferSource,seed?:number):Promise<NativeScene>;
 command(command:NativeCommand):number;
 advanceTo(timeUs:number):void;
 render():NativeFrame;
 info():NativeMetadata;
 /** Complete metadata recovery; no default cap. Optional positive u32 caller limit. */
 infoComplete(maxBytes?:number|null):NativeMetadata;
 setModelRecords(records:Uint8Array):void;
 modelRecords():Uint8Array;
 snapshot():Uint8Array;
 restore(bytes:Uint8Array):void;
 particles():number[][];
 scriptRuns(text:string):Array<[number,number,string]>;
 bidiLines(text:string,ends:number[],direction?:number):number[][];
 lineBreaks(text:string):number[];
 lineBreakDetails(text:string):[number,number][];
 graphemeBoundaries(text:string):number[];
 graphemeWidths(text:string,ambiguous?:1|2):[number,number,number][];
 negotiateShortcuts(actions:number[],candidates:number[][],host:number[][]):number[][];
 textRunClusters(kind:number,id:number):number[][];
 textRunSource(kind:number,id:number):string;
 textRunLayout(kind:number,id:number,columns:number,ambiguous?:number):number[][];
 textRunHit(kind:number,id:number,columns:number,column:number,row:number,ambiguous?:number):number;
 textRunClip(kind:number,id:number,columns:number,x:number,y:number,width:number,height:number,ambiguous?:number):number[][];
 bidiVisual(text:string,direction?:number):number[][];
 surfaceFoam(id:number):number[][];
 surfaceFoamTransport(id:number):number[][];
 promptLayout():number[][];
 promptVisualLayout():number[][];
 areaGeometry(id:number):number[]|null;
 fieldSample(id:number,x:number,y:number):number[]|null;
 thermalSample(triangleIndex:number):number[]|null;
 hullImmersion(vertices:readonly (readonly [number,number,number])[],faces:readonly (readonly [number,number,number])[],height:number):number[];
 hullImmersionPlane(vertices:readonly (readonly [number,number,number])[],faces:readonly (readonly [number,number,number])[],point:readonly [number,number,number],normal:readonly [number,number,number]):number[];
 fluidDragExchange(bodyMass:number,waterMass:number,conductance:number,seconds:number,bodyVelocity:readonly [number,number,number],waterVelocity:readonly [number,number,number]):number[];
 angularDragExchange(bodyInertia:readonly [number,number,number],waterInertia:readonly [number,number,number],conductance:readonly [number,number,number],seconds:number,bodyOmega:readonly [number,number,number],waterOmega:readonly [number,number,number]):number[];
 hullBuoyancyPlane(vertices:readonly (readonly [number,number,number])[],faces:readonly (readonly [number,number,number])[],point:readonly [number,number,number],normal:readonly [number,number,number],options:{density:number;gravity:number;mass:number;centerOfMass:readonly [number,number,number]}):number[];
 waterSample(triangleIndex:number):number[]|null;
 flowThickness(id:number):number[]|null;
 surfaceTriangles(id:number):number[][];
 floatBody(id:number):number[]|null;
 floatHull(id:number):number[]|null;
 surfaceFluid(id:number):number[]|null;
 surfaceFluidAngular(id:number):number[]|null;
 hullMeshImmersion(vertices:readonly (readonly [number,number,number])[],faces:readonly (readonly [number,number,number])[],water:readonly (readonly [number,number,number,number,number,number,number,number,number])[]):number[];
 surfaceWaveSample(id:number,x:number,z:number):number[];
 pathSample(points:readonly (readonly [number,number,number])[],distance:number,options?:{closed?:boolean;mode?:'clamp'|'loop'|'reverse'}):number[];
 waveSample(waves:number[][],x:number,z:number,seconds:number):number[];
 documentLayout(text:string,columns:number,direction?:number,ambiguous?:number):number[][];
 documentBoundaries(text:string):number[];
 documentHit(text:string,columns:number,column:number,row:number,direction?:number,ambiguous?:number):number;
 documentCaret(text:string,columns:number,offset:number,affinity?:number,direction?:number,ambiguous?:number):number[];
 bidiLayout(text:string,columns:number,direction?:number,ambiguous?:number):number[][];
 bidiHit(text:string,columns:number,column:number,row:number,direction?:number,ambiguous?:number):number;
 bidiCaret(text:string,columns:number,offset:number,affinity?:number,direction?:number,ambiguous?:number):number[];
 selectedText():string|null;
 graphemeHit(text:string,columns:number,column:number,row:number,ambiguous?:1|2):number;
 graphemeLayout(text:string,columns:number,ambiguous?:1|2):[number,number,number,number,number][];
 particleMotions():number[][];
 textSample(id:number,index:number):number[];
 textClusterSample(id:number,index:number):number[];
 textTrailSample(id:number,index:number,trailIndex:number):number[];
 windowSample(id:number,u:number,v:number,visibility:number):number[];
 batch(commands:readonly SceneEdit[]):number;
 schedule(id:number,atUs:number,command:SceneEdit):number;
 cancelScheduled(id:number):number;
 close():void;
 sourceStageOklch(lightness:number,chroma:number,hue:number):number;
 sourceStageTween(from:number,to:number,elapsedMs:number,durationMs:number,easing?:0|1|2|3):number;
 sourceStageInkOpacity(ageMs:number,fadeMs:number,rowQ8:number,bandQ8:number,topMinimum:number):number;
 sourceStageHit(x:number,y:number):{id:number;item:number}|null;
 catalogue():{id:string;name:string;contract:string}[];
 oklch(l:number,c:number,h:number):number;
 composite(base:number,source:number,baseAlpha?:number,sourceAlpha?:number,blend?:number,operation?:number,seed?:number):{rgb:number;alpha:number};
 compositeInSpace(base:number,source:number,space:0|1|2|3,baseAlpha?:number,sourceAlpha?:number,blend?:number,operation?:number,seed?:number):{rgb:number;alpha:number};
 inspectCharacterCell(x:number,y:number):CharacterCellInfo;
}

export interface ThermalCarrier{id:number;capacity:number;temperature:number;energy:number;contactFraction:number;conductance:number;}
