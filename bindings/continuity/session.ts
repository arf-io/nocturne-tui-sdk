/** Versioned host-neutral RC API. The recovered artistic modules remain readable
 * JavaScript; this strict boundary supplies typed operations and runtime checks.
 * Neither this session nor the native World renderer opens a terminal or device. */
import {StudioEngine} from './studio.js';
import {WorldEngine} from './world.js';
import {RestorationModel} from './restoration-model.js';
import {RestorationRenderer} from './restoration-renderer.js';
import {activateBlackHole} from './black-hole-renderer.js';
import {applyRestorationConfiguration,exportRestorationConfiguration} from './restoration-config.js';
import {applyContinuityPreset} from './continuity-presets.js';
import {WORLD_DETAIL_FIELDS} from './world-detail-fields.js';
import {atelierTextOptions} from './atelier-text.js';
export interface CellFrame { width:number;height:number;cells:Uint32Array }
export interface WheelSample {deltaX?:number;deltaY?:number;deltaMode?:0|1|2;shiftKey?:boolean}
export type ContinuityCommand =
 | {op:'render'|'export'|'backspace'|'dismiss'|'clear-effects';payload?:Record<string,never>}
 | {op:'scene'|'preset'|'select-node';payload:{id:string}}
 | {op:'resize';payload:{width:number;height:number}}
 | {op:'time';payload:{timeMs:number}}
 | {op:'input';payload:{text:string}}
 | {op:'draft';payload:{text:string;caret?:number}}
 | {op:'caret';payload:{index:number}}
 | {op:'wheel';payload:WheelSample}
 | {op:'look';payload:{yaw:number;pitch:number;roll?:number}}
 | {op:'pan';payload:{right:number;up:number;forward?:number}}
 | {op:'navigate';payload:{action:string}}
 | {op:'move-window';payload:{id:number;dx:number;dy:number;forward?:number}}
 | {op:'mesh';payload:{text:string;name?:string;upAxis?:'Y'|'Z'}}
 | {op:'effect-play';payload:{id:string;space?:'screen'|'world';x?:number;y?:number}}
 | {op:'pointer';payload:{id:string;x:number;y:number;kind?:string}}
 | {op:'water';payload:Record<string,number>}
 | {op:'configure'|'material'|'camera'|'graph'|'import'|'atelier-text'|'window'|'action'|'effect'|'classic-effect';payload:Record<string,unknown>};
export interface SessionResult {frame:CellFrame;metadata:Record<string,unknown>}
/** Single-owner model and renderer. A native SceneBridge explicitly delegates to
 * this same class in its named Node worker. Calls are not thread safe. */
export class ContinuitySession {
    private constructor(public readonly model:RestorationModel,public readonly renderer:RestorationRenderer){}
    /** Inputs: caller-loaded WASM bytes and Studio schema. No file/network I/O.
     * Returns an independent session; rejects incompatible WASM/schema.
     * Example: await ContinuitySession.create(wasmBytes,studioSchema). */
    static async create(bytes:Uint8Array,schema:unknown):Promise<ContinuitySession>{
        const engine=await StudioEngine.create(bytes,schema), world=await WorldEngine.create(bytes);
        const m=new RestorationModel();m.configure({motion:false});m.simulation=false;
        return new ContinuitySession(m,new RestorationRenderer(engine,world));
    }
    /** Typed convenience API. Every edit renders immediately at the held motion
     * timestamp. Only time/configured presets change decorative state explicitly. */
    apply(command:ContinuityCommand):SessionResult {return this.dispatch(command.op,command.payload??{});}
    /** Runtime boundary for bounded JSON bridge requests. Invalid command/payload
     * throws; no string is evaluated or passed to a shell. Returned cells are owned.
     * Graph solving is completed synchronously here: use a worker for large graphs.
     * Example: session.dispatch('draft',{text:'visible now',caret:3}). */
    dispatch(op:string,payload:Record<string,any>={}):SessionResult{
        if(!payload||typeof payload!=='object'||Array.isArray(payload))throw new RangeError('Object payload required');
        const m=this.model;
        switch(op){
        case 'render':case 'export':break;
        case 'scene':m.setScene(payload.id);break;
        case 'preset':applyContinuityPreset(m,payload.id);break;
        case 'resize':m.resize(payload.width,payload.height);break;
        case 'time':if(!Number.isSafeInteger(payload.timeMs)||payload.timeMs<0)throw new RangeError('timeMs');m.setTime(payload.timeMs);break;
        case 'input':if(typeof payload.text!=='string'||payload.text.length>8192)throw new RangeError('input text');m.input(payload.text);break;
        case 'draft':m.replaceDraft(payload.text,payload.caret);break;
        case 'caret':m.setDraftCaret(payload.index);break;
        case 'backspace':m.backspace();break;
        case 'wheel':m.wheel(payload);break;
        case 'look':m.lookBy(payload.yaw,payload.pitch,payload.roll??0);break;
        case 'pan':m.panBy(payload.right,payload.up,payload.forward??0);break;
        case 'navigate':if(typeof payload.action!=='string')throw new RangeError('navigation action');m.navigate(payload.action);break;
        case 'move-window':m.moveWindowByScreen(payload.id,payload.dx,payload.dy,payload.forward??0);break;
        case 'mesh':if(typeof payload.text!=='string'||payload.text.length>4194304)throw new RangeError('OBJ text limit');m.loadMesh(payload.text,payload.name,payload.upAxis);break;
        case 'effect-play':m.playEffect(payload.id,payload.space,payload.x,payload.y);break;
        case 'clear-effects':m.effectShelf.clear();m.events=[];m.worldEvents=[];m.inkEvents=[];break;
        case 'pointer':m.emitPointer(payload.id,payload.x,payload.y,payload.kind);break;
        case 'water':{
            const next={...m.worldDetail};
            for(const [name,value] of Object.entries(payload)){
                const f=WORLD_DETAIL_FIELDS.find(f=>f.name===name);
                if(!f||typeof value!=='number'||!Number.isFinite(value)||value<f.min||value>f.max||(f.scale===1&&!Number.isInteger(value)))throw new RangeError('water '+name);
                (next as any)[name]=value;
            }m.worldDetail=next;break;
        }
        case 'configure':m.configure(payload);break;
        case 'material':m.configureBH(payload);break;
        case 'camera':m.camera.configure(payload);m.flight.anchor(m.camera.snapshot());break;
        case 'graph':m.loadGraph(payload);break;
        case 'select-node':m.selectGraph(payload.id);break;
        case 'dismiss':m.dismissModal();break;
        case 'classic-effect':if(!['nova','sparks','embers','ripples'].includes(payload.kind))throw new RangeError('classic kind');m.emitClassic(payload.kind);break;
        case 'effect':m.emit(payload.x??m.width/2,payload.y??m.height/2,'*',payload.kind);break;
        case 'atelier-text':
            if(!['show','hide'].includes(payload.phase??'show'))throw new RangeError('text phase');
            atelierTextOptions({...m.atelierPlayer.options,...(payload.options??{})});
            if(payload.text!==undefined)m.setText(payload.text);
            m.replayAtelier(payload.phase??'show',payload.options??{});m.setScene('text');break;
        case 'window':m.windowAction(payload.id,payload.action);break;
        case 'action':{
            const v=this.renderer.render(m);if(!Number.isInteger(payload.id)||!(v.actions as Record<number,unknown>)[payload.id])throw new RangeError('unknown rendered action');activateBlackHole(m,payload.id,v);break;
        }
        case 'import':applyRestorationConfiguration(m,payload);break;
        default:throw new RangeError('Unknown scene operation '+op);
        }
        while(m.layoutJob)m.stepLayout(128);
        const v=this.renderer.render(m);
        return {frame:v.frame,metadata:{version:1,edition:'0.9.0-rc.1',scene:m.scene,motionMs:m.motionMs,
            notice:m.notice,semantics:v.semantics,actions:v.actions,caret:m.draftCaret,impulses:m.inkEvents.length,
            ...(op==='export'?{configuration:exportRestorationConfiguration(m)}:{})}};
    }
}
export {RestorationModel as ContinuityModel,RestorationRenderer as ContinuityRenderer,WorldEngine};
