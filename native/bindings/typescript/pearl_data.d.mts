export interface StudioDataSnapshot {elapsedMs:number;motionMs:number;nextMs:number;dataCount:number;value:number;fromValue:number;changedMs:number;displayValue:number;playing:boolean;prompt:string;}
export function studioTween(from:number,to:number,elapsedMs:number,durationMs?:number):number;
export class StudioDataSource {constructor();elapsedMs:number;motionMs:number;nextMs:number;dataCount:number;value:number;fromValue:number;changedMs:number;playing:boolean;prompt:string;advanceTo(elapsedMs:number,options?:{playing?:boolean;onCommit?:(snapshot:StudioDataSnapshot)=>void}):StudioDataSnapshot;setValue(value:number):StudioDataSnapshot;promptCommit(text:string):StudioDataSnapshot;snapshot():StudioDataSnapshot;}
export interface ObservatorySample {dataMs:number;waveform:number[];reference:number[];bus:{source:string;value:number;atMs:number;quality:'synthetic'}[];quality:'synthetic';}
export function observatorySample(dataMs:number):ObservatorySample;
