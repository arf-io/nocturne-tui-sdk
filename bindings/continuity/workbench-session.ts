import {applyWorkbenchConfiguration,exportWorkbenchConfiguration} from './workbench-config.js';
import {TextActor,validateTextOptions} from './kinetic-text.js';
import {applyContinuityPreset} from './continuity-presets.js';
import {WORLD_DETAIL_FIELDS} from './world-detail-fields.js';
import {atelierTextOptions} from './atelier-text.js';
import {validateDecoration,paintStyled} from './styles.js';
import type {ContinuityCommand, SessionResult} from './session.js';
import {WorkbenchModel,WorkbenchRenderer,activateWorkbench,beginWorkbenchPointer,workbenchPointerIntent} from './workbench.js';
import {StudioEngine} from './studio.js';
import {WorldEngine} from './world.js';
/** Versioned host-neutral RC API. The recovered artistic modules remain readable
 * JavaScript; this strict boundary supplies typed operations and runtime checks.
 * Neither this session nor the native World renderer opens a terminal or device. */
/** Single-owner model and renderer. A native SceneBridge explicitly delegates to
 * this same class in its named Node worker. Calls are not thread safe. */
export type WorkbenchCommand = ContinuityCommand
 | {op:'prompt-config'|'prompt-restore'|'decoration'|'change-style'|'particle-options'|'window-options'|'text-options'|'style-demo'|'node-demo';payload:Record<string,any>}
 | {op:'prompt-snapshot';payload?:Record<string,never>}
 | {op:'prompt-mode';payload:{mode:'marquee'|'grow'|'vim-inline'|'vim-full'}}
 | {op:'prompt-action';payload:{action:string}}
 | {op:'prompt-key';payload:{key:string;ctrl?:boolean;alt?:boolean;meta?:boolean;shift?:boolean}}
 | {op:'value';payload:{value:number|string}};
class WorkbenchSession {
    constructor(public readonly model:WorkbenchModel, public readonly renderer:WorkbenchRenderer) {}
    /** Inputs: caller-loaded WASM bytes and Studio schema. No file/network I/O.
     * Returns an independent session; rejects incompatible WASM/schema.
     * Example: await WorkbenchSession.create(wasmBytes,studioSchema). */
    static async create(bytes:Uint8Array, schema:unknown) {
        const engine = await StudioEngine.create(bytes, schema), world = await WorldEngine.create(bytes);
        const m = new WorkbenchModel();
        m.configure({ motion: false });
        m.simulation = false;
        return new WorkbenchSession(m, new WorkbenchRenderer(engine, world));
    }
    /** Typed convenience API. Every edit renders immediately at the held motion
     * timestamp. Only time/configured presets change decorative state explicitly. */
    apply(command:WorkbenchCommand) { return this.dispatch(command.op, command.payload ?? {}); }
    /** Runtime boundary for bounded JSON bridge requests. Invalid command/payload
     * throws; no string is evaluated or passed to a shell. Returned cells are owned.
     * Graph solving is completed synchronously here: use a worker for large graphs.
     * Example: session.dispatch('draft',{text:'visible now',caret:3}). */
    dispatch(op:string, payload:Record<string,any> = {}):SessionResult {
        if (!payload || typeof payload !== 'object' || Array.isArray(payload))
            throw new RangeError('Object payload required');
        const m = this.model;
        switch (op) {
            case 'render':
            case 'export':
            case 'prompt-snapshot': break;
            case 'prompt-config':
                m.configurePrompt(payload);
                break;
            case 'prompt-mode':
                m.promptMode(payload.mode);
                break;
            case 'prompt-action':
                m.promptAction(payload.action);
                break;
            case 'prompt-key':
                for(const k of ['ctrl','alt','meta','shift'])if(payload[k]!==undefined&&typeof payload[k]!=='boolean')throw new RangeError('Boolean modifier '+k);
                if (typeof payload.key !== 'string' || payload.key.length > 64)
                    throw new RangeError('prompt key');
                m.promptKey(payload);
                break;
            case 'prompt-restore':
                m.document.restore(payload);
                m.draft = m.document.text;
                m.draftCaret = m.document.caret;
                m.revision++;
                break;
            case 'decoration':
                m.decoration = validateDecoration({ ...m.decoration, ...payload });
                m.showDecoration=true;
                break;
            case 'change-style':
                m.changeTrack.configure(payload);
                break;
            case 'value':
                m.updateValue(payload.value);
                break;
            case 'particle-options':
                m.configureParticles(payload);
                break;
            case 'window-options':
                m.spaceWindows.configure(payload);
                break;
            case 'text-options':
                new TextActor(payload.text ?? m.textSource,validateTextOptions({...m.textOptions,...(payload.options??{})}));
                m.configureText(payload.options ?? {});
                if (payload.text !== undefined)
                    m.setText(payload.text);
                m.atelierTextEnabled = false;
                m.hardReplayText();
                break;
            case 'style-demo': {
                const style = validateDecoration({ ...m.decoration, ...(payload.style ?? {}) });
                const config = this.renderer.engine.defaults({ width: m.width, height: m.height, pattern: 3, brightness: 250 });
                const base = this.renderer.engine.render(config, m.motionMs);
                const nodes = payload.nodes ?? [{ kind: 'box', id: 700, x: 6, y: 5, width: m.width - 12, height: 18 }, { kind: 'text', id: 701, x: 9, y: 7, width: m.width - 20, height: 5, text: 'SELECTED / A LIVING INTERFACE' }, { kind: 'item', id: 702, x: 11, y: 14, width: 44, height: 3, text: '> inspect agent · available' }];
                if (!Array.isArray(nodes) || nodes.length > 256)
                    throw new RangeError('styled nodes');
                return { frame: paintStyled(this.renderer.engine, base, nodes, style, m.motionMs), metadata: { version: 1, edition: '0.9.0-rc.2', scene: 'styled-component' } };
            }
            case 'node-demo': {
                if (!Array.isArray(payload.nodes) || payload.nodes.length > 2000)
                    throw new RangeError('nodes');
                const config = this.renderer.engine.defaults({ width: m.width, height: m.height, ...(payload.material ?? {}) });
                for (const k of ['palette', 'starPalette', 'glyphs'])
                    if (payload.arrays?.[k]) {
                        if (!Array.isArray(payload.arrays[k]) || payload.arrays[k].length > 32)
                            throw new RangeError(k);
                        config[k] = [...payload.arrays[k]];
                    }
                const frame = this.renderer.engine.render(config, m.motionMs, payload.nodes, []);
                return { frame, metadata: { version: 1, edition: '0.9.0-rc.2', scene: 'component' } };
            }
            case 'scene':
                m.setScene(payload.id);
                break;
            case 'preset':
                applyContinuityPreset(m, payload.id);
                break;
            case 'resize':
                m.resize(payload.width, payload.height);
                break;
            case 'time':
                if (!Number.isSafeInteger(payload.timeMs) || payload.timeMs < 0)
                    throw new RangeError('timeMs');
                m.setTime(payload.timeMs);
                break;
            case 'input':
                if (typeof payload.text !== 'string' || payload.text.length > 8192)
                    throw new RangeError('input text');
                m.input(payload.text);
                break;
            case 'draft':
                m.replaceDraft(payload.text, payload.caret);
                break;
            case 'caret':
                m.setDraftCaret(payload.index);
                break;
            case 'backspace':
                m.backspace();
                break;
            case 'wheel':
                m.wheel(payload);
                break;
            case 'look':
                m.lookBy(payload.yaw, payload.pitch, payload.roll ?? 0);
                break;
            case 'pan':
                m.panBy(payload.right, payload.up, payload.forward ?? 0);
                break;
            case 'navigate':
                if (typeof payload.action !== 'string')
                    throw new RangeError('navigation action');
                m.navigate(payload.action);
                break;
            case 'move-window':
                m.moveWindowByScreen(payload.id, payload.dx, payload.dy, payload.forward ?? 0);
                break;
            case 'mesh':
                if (typeof payload.text !== 'string' || payload.text.length > 4194304)
                    throw new RangeError('OBJ text limit');
                m.loadMesh(payload.text, payload.name, payload.upAxis);
                break;
            case 'effect-play':
                m.playEffect(payload.id, payload.space, payload.x, payload.y);
                break;
            case 'clear-effects':
                m.effectShelf.clear();
                m.events = [];
                m.worldEvents = [];
                m.inkEvents = [];
                break;
            case 'pointer': {
                const view=this.renderer.render(m), opts={button:payload.button??0,shiftKey:payload.shiftKey??false,altKey:payload.altKey??false};
                for(const k of ['shiftKey','altKey'])if(payload[k]!==undefined&&typeof payload[k]!=='boolean')throw new RangeError('Boolean modifier '+k);
                // Validate before consuming the caller's gesture identity.
                workbenchPointerIntent(m,view,payload.x,payload.y,opts);
                if(m.pointerGate.accept(payload.id??payload.dispatchId))beginWorkbenchPointer(m,view,payload.x,payload.y,opts);
                break;
            }
            case 'water': {
                const next = { ...m.worldDetail };
                for (const [name, value] of Object.entries(payload)) {
                    const f = WORLD_DETAIL_FIELDS.find(f => f.name === name);
                    if (!f || typeof value !== 'number' || !Number.isFinite(value) || value < f.min || value > f.max || (f.scale === 1 && !Number.isInteger(value)))
                        throw new RangeError('water ' + name);
                    (next as any)[name] = value;
                }
                m.worldDetail = next;
                break;
            }
            case 'configure':
                m.configure(payload);
                break;
            case 'material':
                m.configureBH(payload);
                break;
            case 'camera':
                m.camera.configure(payload);
                m.flight.anchor(m.camera.snapshot());
                break;
            case 'graph':
                m.loadGraph(payload);
                break;
            case 'select-node':
                m.selectGraph(payload.id);
                break;
            case 'dismiss':
                m.dismissModal();
                break;
            case 'classic-effect':
                if (!['nova', 'sparks', 'embers', 'ripples'].includes(payload.kind))
                    throw new RangeError('classic kind');
                m.emitClassic(payload.kind);
                break;
            case 'effect':
                m.emit(payload.x ?? m.width / 2, payload.y ?? m.height / 2, '*', payload.kind);
                break;
            case 'atelier-text':
                if (!['show', 'hide'].includes(payload.phase ?? 'show'))
                    throw new RangeError('text phase');
                atelierTextOptions({ ...m.atelierPlayer.options, ...(payload.options ?? {}) });
                if (payload.text !== undefined)
                    m.setText(payload.text);
                m.replayAtelier(payload.phase ?? 'show', payload.options ?? {});
                m.setScene('text');
                break;
            case 'window':
                m.windowAction(payload.id, payload.action);
                break;
            case 'action': {
                const v = this.renderer.render(m);
                if (!Number.isInteger(payload.id) || !(v.actions as Record<number,unknown>)[payload.id])
                    throw new RangeError('unknown rendered action');
                activateWorkbench(m, payload.id, v);
                break;
            }
            case 'import':
                applyWorkbenchConfiguration(m, payload);
                break;
            default: throw new RangeError('Unknown scene operation ' + op);
        }
        while (m.layoutJob)
            m.stepLayout(128);
        const v = this.renderer.render(m);
        return { frame: v.frame, metadata: { version: 1, edition: '0.9.0-rc.2', scene: m.scene, motionMs: m.motionMs,
                notice: m.notice, semantics: v.semantics, actions: v.actions, caret: m.draftCaret, impulses: m.inkEvents.length,
                promptMode: m.document.mode, promptState: m.document.vimState, promptRect: m.promptLayout().rect,
                ...(op === 'prompt-snapshot' ? { document: m.document.snapshot() } : {}),
                ...(op === 'export' ? { configuration: exportWorkbenchConfiguration(m) } : {}) } };
    }
}

export {WorkbenchSession};
