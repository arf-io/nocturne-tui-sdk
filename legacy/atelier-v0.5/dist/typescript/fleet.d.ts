/** Pearl Fleet application controller. Rendering is shared WASM; I/O stays in hosts. */
import { StudioEngine, StudioConfig, StudioNode, StudioImpulse } from './studio.js';
import { FleetModel, FleetCommand, FleetMetrics, TranscriptLine } from './fleet-model.js';
export * from './fleet-model.js';
export interface Rect {
    x: number;
    y: number;
    width: number;
    height: number;
}
export interface FleetOptions {
    expandMs: number;
    arrivalMs: number;
    horizonRows: number;
    horizonMinimum: number;
    reducedMotion: boolean;
    readMode: boolean;
    dense: boolean;
    backgroundBrightness: number;
    scopeColorSpeed: number;
}
export declare const DEFAULT_FLEET_OPTIONS: FleetOptions;
export interface FleetScene {
    version: 1;
    kind: 'nocturne.fleet.scene';
    timeMs: number;
    config: StudioConfig;
    nodes: StudioNode[];
    events: StudioImpulse[];
    semantics: {
        title: string;
        agentId: string;
        transcript: string;
        metrics: FleetMetrics | null;
        demo: boolean;
        revision: number;
    };
}
/** Deterministic, explicit-time controller for the shared browser/terminal experience.
 * It emits command records, never shell commands or provider requests. Hosts call
 * ingest immediately on data, setTime on the host-selected decorative deadline, and paint.
 */
export declare class FleetController {
    readonly engine: StudioEngine;
    readonly model: FleetModel;
    options: FleetOptions;
    presentationFps: number;
    width: number;
    height: number;
    motionMs: number;
    paused: boolean;
    selectedId: string;
    opened: boolean;
    /** Arrival runs already revealed by pause/read policy must never fade backward. */
    revealThroughMs: number;
    config: StudioConfig;
    impulses: StudioImpulse[];
    inspection: string;
    private views;
    private transitionAt;
    private fromRect;
    private toRect;
    private commands;
    private commandSerial;
    private demoTick;
    private nextDemoMessage;
    private replies;
    constructor(engine: StudioEngine, model: FleetModel, options?: Partial<FleetOptions>);
    /** Atomically validate configurable visual policy. Unknown keys are rejected. */
    configure(options: Partial<FleetOptions>): void;
    private view;
    /** Presentation metadata only; changing this never changes motion time. */
    setPresentationFps(fps: number): void;
    /** Current draft is agent-local and preserved when switching workspaces. */
    get draft(): string;
    get scrollOffset(): number;
    get historyUnread(): number;
    get readKey(): number;
    get immediateVisuals(): boolean;
    /** Input changes never advance decorative time or wait for a frame callback. */
    setDraft(text: string): void;
    /** Set a sampled decorative time in milliseconds; pause retains its current value. */
    setTime(timeMs: number): void;
    /** Pause settles an unfinished workspace transition and reveals arriving text;
     * authoritative data is still accepted. Resume does not change message identity.
     */
    setPaused(paused: boolean): void;
    /** Resize is a layout event: apply now and retarget from the currently visible
     * rectangle, not from its obsolete origin. Empty viewports are valid.
     */
    resize(width: number, height: number): void;
    /** Final maximized application region. Does not invoke browser/terminal fullscreen. */
    workspaceRect(): Rect;
    /** Overview source geometry. Dense/narrow views expand from the selected row. */
    cardRect(agentId: string): Rect;
    /** Current eased rectangle; interrupted transitions begin at this exact value. */
    activeRect(): Rect;
    /** Fraction of the current transition, in thousandths. */
    transitionProgress(): number;
    /** Active overlay includes the closing transition until it reaches the deck. */
    get hasWorkspace(): boolean;
    /** Select only (keyboard focus), without triggering an action. */
    selectAgent(agentId: string): void;
    /** Expand a tab/card into its agent workspace. No data stream is paused. */
    openAgent(agentId: string): void;
    /** Return the active workspace to its tile/row; reverse safely mid-animation. */
    closeAgent(): void;
    /** Cycle tabs. With an open workspace this switches agents; otherwise only focus. */
    nextAgent(step?: number): void;
    /** Logical transcript dimensions, excluding metadata and composer. */
    transcriptRect(): Rect;
    private transcriptLines;
    /** Pure logical rows in the current history/live-tail window. */
    visibleTranscript(): TranscriptLine[];
    /** Scroll upward by positive rows. A history window is never dragged by data. */
    scroll(rows: number): void;
    /** Explicitly resume following the newest messages. */
    liveTail(): void;
    /** Ingest independently of the render cadence; maintain the visible history anchor.
     * Event payload is validated by FleetModel. Returns whether state changed.
     */
    ingest(event: unknown): boolean;
    /** Queue a message for an explicit adapter. Returns its record, not an ACK.
     * A full outbox throws; it never silently drops commands. Blank input is rejected.
     */
    send(text?: string): FleetCommand;
    /** Drain outbound records. The embedding host is solely responsible for delivery. */
    drainCommands(): FleetCommand[];
    /** Click native cell hit areas. Returns a semantic action for the host composer. */
    click(x: number, y: number): string;
    /** Export a pure native-renderable scene. Render calls do not advance state. */
    compose(): FleetScene;
    /** Demo driver only. An embedding with model.demo=false never synthesizes events,
     * drains commands, or runs a reply. Input dataMs is explicit source time.
     */
    advanceDemo(dataMs: number): void;
}
