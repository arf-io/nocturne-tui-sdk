import type {PearlObservatorySession} from './pearl_observatory_stage.mjs';
export interface ObservatoryAudio {readonly active:{stream:MediaStream;context:AudioContext;session:PearlObservatorySession;timer:number}|null;stop():Promise<void>;attach(stream:MediaStream,source?:{prefix?:string;quality?:string;label?:string}):Promise<boolean>;start(kind:'microphone'|'display'):Promise<boolean>;}
export function createObservatoryAudio(callbacks:{session:()=>PearlObservatorySession|null;running?:()=>boolean;changed?:()=>void;error?:(failure:unknown)=>void}):ObservatoryAudio;
