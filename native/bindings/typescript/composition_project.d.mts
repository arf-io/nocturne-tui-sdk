import type {NativeScene,NativeFrame,NativeMetadata} from './native_scene.mjs';
import type {NativeCommand} from './contracts.js';
export type ComponentKind='text'|'box'|'rule'|'button'|'item'|'cursor'|'progress'|'bars'|'pie'|'donut'|'scatter'|'line'|'digits'|'edge'|'checkbox'|'radio'|'select'|'scrollbar'|'window'|'emitter'|'field'|'text-transition'|'graph-node'|'area'|'indicator'|'mesh'|'surface'|'cell-art'|'stage-component';
export interface ProjectElement {id:number;kind:ComponentKind;name:string;geometry:{x:number;y:number;width:number;height:number};props:Record<string,unknown>;events:{activate:NativeCommand[]};appearance?:{foreground?:number;background?:number;opacity?:number;border?:'none'|'rounded'|'square'|'double'|'heavy'};}
export interface CompositionProject {schema:'nocturne.project.v1';name:string;seed:number;width:number;height:number;background:number;timeUs:number;initialPromptText?:string;final:NativeCommand[];timeline:Array<{timeUs:number;command:NativeCommand}>;commands:NativeCommand[];resources:{modelRecords?:string};prompt:{text:string;active?:boolean;appearance?:Record<string,unknown>;[key:string]:unknown};elements:ProjectElement[];}
export interface PreparedProject {project:CompositionProject;snapshot:Uint8Array;frame:NativeFrame;info:NativeMetadata;}
export interface ProjectPlan {seed:number;commands:NativeCommand[];timeline:Array<{timeUs:number;command:NativeCommand}>;modelRecords:string|null;interactions:Array<{id:number;owner:number;commands:NativeCommand[]}>;project:CompositionProject;}
export const COMPONENT_CATALOG:readonly {kind:ComponentKind;label:string;layer:'world'|'interface'}[];
export function createProject(options?:{seed?:number;width?:number;height?:number}):CompositionProject;
export function validateProject(value:unknown):CompositionProject;
export function placeComponent(kind:ComponentKind,id:number,x?:number,y?:number):ProjectElement;
export function exportProject(value:CompositionProject):string;
export function importProject(text:string):CompositionProject;
export function decodeProjectModel(text:string):Uint8Array;
export function projectPlan(value:CompositionProject):ProjectPlan;
export function prepareProject(validator:NativeScene,value:CompositionProject):PreparedProject;
export function adoptProject(scene:NativeScene,prepared:PreparedProject):CompositionProject;
export function insertProject(target:CompositionProject,incoming:CompositionProject):CompositionProject;
export function projectActivation(value:CompositionProject,id:number):NativeCommand|null;
export class ProjectHistory {constructor(project:CompositionProject,snapshot:Uint8Array);project:CompositionProject;snapshot:Uint8Array;readonly past:unknown[];readonly future:unknown[];readonly storageBytes:number;commit(project:CompositionProject,snapshot:Uint8Array):boolean;undo():{project:CompositionProject;snapshot:Uint8Array}|null;redo():{project:CompositionProject;snapshot:Uint8Array}|null;current():{project:CompositionProject;snapshot:Uint8Array};}
export function componentLayer(kind:ComponentKind):"world"|"interface";
export function componentOwner(kind:ComponentKind,id:number):number;
export function elementCommands(element:ProjectElement,project:CompositionProject):NativeCommand[];

export function projectFromCommands(commands:readonly NativeCommand[],options?:{seed?:number;width?:number;height?:number;name?:string;modelRecords?:string;timeUs?:number;timeline?:Array<{timeUs:number;command:NativeCommand}>}):CompositionProject;

export function componentAppearance(kind:ComponentKind):Array<"foreground"|"background"|"opacity"|"border">;

export function advanceProject(scene:NativeScene,timeline:Array<{timeUs:number;command:NativeCommand}>,state:{next:number},timeUs:number,budget?:number):number;
