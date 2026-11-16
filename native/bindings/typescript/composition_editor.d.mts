import type {NativeScene} from './native_scene.mjs';
import type {NativeCommand} from './contracts.js';
import type {CompositionProject,ComponentKind} from './composition_project.mjs';
export interface CompositionEditor {
 recordCommand(command:NativeCommand):void;advanceTo(timeUs:number,budget?:number):number;document():CompositionProject;replace(project:CompositionProject):void;insert(project:CompositionProject):void;
 activate(id:number):boolean;detach():void;isActive():boolean;refresh():void;
 replaceCommands(commands:readonly NativeCommand[],options?:{seed?:number;width?:number;height?:number;name?:string;modelRecords?:string;timeUs?:number;timeline?:CompositionProject['timeline']}):void;
 insertCommands(commands:readonly NativeCommand[]):void;
 applyPrompt(appearance:Record<string,unknown>):void;add(kind:ComponentKind,x?:number,y?:number):void;undo():void;redo():void;
}
export function bindCompositionEditor(options:{scene:NativeScene;validator:NativeScene;canvas:HTMLCanvasElement;panel:HTMLElement;baseScenes?:Array<{id:string;name:string;project:()=>CompositionProject}>;modelResource?:()=>null|{name:string;modelRecords:string;width:number;height:number;seed:number;commands:NativeCommand[]};beforeAdopt?:()=>void;afterAdopt?:(project:CompositionProject)=>void;repaint?:()=>void;onError?:(error:unknown)=>void}):CompositionEditor;
