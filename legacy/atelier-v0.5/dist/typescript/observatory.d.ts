/** Nocturne Observatory: host-neutral controls, kinetics, reactive material fields,
 * and interactive mockups. No terminal, wall clock, filesystem, media permissions,
 * network, provider, or subprocess ownership lives in this module.
 */
import { StudioEngine, StudioFrame, StudioNode } from './studio.js';
export declare const TAU: number;
export declare const clamp: (v: number, a: number, b: number) => number;
export declare const fract: (v: number) => number;
export declare const smooth: (v: number) => number;
export declare function finite(v: unknown, lo: number, hi: number, label: string): number;
export declare function hash32(v: number): number;
export declare const randomAt: (seed: number, index: number) => number;
export declare const hex: (c: number) => string;
export declare const rgb: (s: string) => number;
export declare function mixColor(a: number, b: number, t: number): number;
/** An explicit monotonic clock. sample() advances elapsed time, not frame count.
 * Call shouldPaint() only for decorative work. Input must call present directly.
 * Changing fps never changes timeMs. setPaused needs the current host timestamp.
 */
export declare class MotionClock {
    timeMs: number;
    fps: number;
    paused: boolean;
    private exact;
    private last;
    private paintAt;
    constructor(fps?: number);
    setFps(fps: number): void;
    sample(wallMs: number): number;
    shouldPaint(wallMs: number): boolean;
    setPaused(paused: boolean, wallMs: number): void;
    seek(timeMs: number, wallMs: number): void;
}
/** Piecewise constant rate integration. Changing speed preserves position.
 * Units: rate units/second, times milliseconds. Retains 256 rate boundaries.
 * Old checkpoints must be retained externally for unlimited backwards replay.
 */
export declare class RateTimeline {
    private segments;
    constructor(rate: number);
    at(timeMs: number): number;
    /** Fork future rate edits at a retained timestamp while preserving position. */
    fork(atMs: number): void;
    set(atMs: number, rate: number): void;
}
export interface SensorSample {
    source: string;
    value: number;
    atMs: number;
    seq: number;
    unit?: string;
    quality?: string;
}
export interface ModulationBinding {
    source: string;
    target: string;
    inputMin: number;
    inputMax: number;
    outputMin: number;
    outputMax: number;
    attackMs: number;
    releaseMs: number;
    ttlMs: number;
    curve?: number;
    deadband?: number;
}
export declare const MODULATION_TARGETS: string[];
/** Bounded sensor-to-style routing with analytical attack/release envelopes.
 * The caller supplies all timestamps in ONE monotonic domain. No device access.
 * Stale samples restore the caller's baseline, never a fabricated zero sample.
 */
export declare class ModulationBus {
    readonly samples: Map<string, SensorSample>;
    readonly bindings: ModulationBinding[];
    private envelopes;
    bind(binding: ModulationBinding): void;
    unbind(target: string): void;
    private valueAt;
    ingest(sample: SensorSample): boolean;
    resolve<T extends Record<string, unknown>>(base: T, atMs: number): T;
}
export interface NumericControl {
    label: string;
    group: string;
    min: number;
    max: number;
    step: number;
    default: number;
    unit: string;
}
export declare const OBSERVATORY_CONTROLS: Record<string, NumericControl>;
export declare const BACKGROUND_STYLES: string[];
export declare const WEATHER_STYLES: string[];
export interface ObservatoryOptions extends Record<string, number | string | boolean | number[]> {
    fps: number;
    gradientScreens: number;
    gradientAngle: number;
    gradientSpeed: number;
    gradientPhase: number;
    feather: number;
    pivotX: number;
    pivotY: number;
    axisPitch: number;
    rotationSpeed: number;
    secondAxisSpeed: number;
    swingAngle: number;
    swingSeconds: number;
    lightness: number;
    chroma: number;
    brightness: number;
    hueOffset: number;
    textLightness: number;
    textChroma: number;
    hueStep: number;
    textHueSpeed: number;
    arrivalMs: number;
    topFade: number;
    fallMs: number;
    tickerSpeed: number;
    starDensity: number;
    starCount: number;
    starSpeed: number;
    trailMs: number;
    novaRegularity: number;
    novaStrength: number;
    cameraYaw: number;
    cameraPitch: number;
    cameraRoll: number;
    cameraX: number;
    cameraY: number;
    cameraZ: number;
    travelYaw: number;
    travelPitch: number;
    fov: number;
    weatherIntensity: number;
    weatherLifeMs: number;
    weatherSpeed: number;
    windowOpacity: number;
    transitionMs: number;
    ruleSpeed: number;
    scopeGain: number;
    sensorAttack: number;
    sensorRelease: number;
    backgroundStyle: string;
    weatherStyle: string;
    orbitMode: string;
    sampling: string;
    lockLightness: boolean;
    flatNavigation: boolean;
    typedColor: boolean;
    motion: boolean;
    stopWidths: number[];
    starGlyphs: string;
}
export declare const DEFAULT_OBSERVATORY_OPTIONS: ObservatoryOptions;
/** Atomic options normalization. Unknown fields, NaN, infinities, wrong types,
 * unsupported glyphs, and unbounded arrays throw before callers commit state. */
export declare function validateOptions(patch: Record<string, unknown>, base?: ObservatoryOptions): ObservatoryOptions;
export interface Vec3 {
    x: number;
    y: number;
    z: number;
}
export interface Camera extends Vec3 {
    yaw: number;
    pitch: number;
    roll: number;
    fov: number;
}
/** Camera-space perspective. Glyph cell aspect is 1:2. Near plane 0.2, far 150.
 * Returns a floating cell coordinate/depth, or null behind/outside depth range. */
export declare function projectPoint(point: Vec3, camera: Camera, width: number, height: number): {
    x: number;
    y: number;
    z: number;
} | null;
/** Signed distance in adjacent-stop units. One horizontal/vertical screen is
 * respectively width/height cells. Double-axis input is handled by fieldPhase. */
export declare function gradientPosition(x: number, y: number, width: number, height: number, o: ObservatoryOptions): number;
export interface WeatherEvent {
    id: number;
    x: number;
    y: number;
    atMs: number;
    kind: string;
    glyph: string;
}
export interface PaletteSpec {
    id: string;
    name: string;
    colors: string[];
    background: string;
    ink: string;
}
export interface SurfaceMessage {
    text: string;
    atMs: number;
    local: boolean;
    id: number;
}
export interface WindowState {
    id: number;
    title: string;
    x: number;
    y: number;
    width: number;
    height: number;
    mode: 'normal' | 'collapsed' | 'maximized';
    from: number;
    target: number;
    changedMs: number;
    fadeFrom: number;
    fadeTarget: number;
    fadeAt: number;
}
export declare const OBSERVATORY_SCENES: {
    id: string;
    name: string;
}[];
/** Bounded interaction state. All domain writes are synchronous; input never
 * advances motion time or waits for animation. save/export is explicit. */
export declare class ObservatoryModel {
    options: ObservatoryOptions;
    motionMs: number;
    dataMs: number;
    revealThroughMs: number;
    revision: number;
    scene: string;
    draft: string;
    selected: number;
    focusId: number;
    hover: number;
    events: WeatherEvent[];
    messages: SurfaceMessage[];
    bus: ModulationBus;
    palette: PaletteSpec;
    readonly travel: RateTimeline;
    readonly warpTravel: RateTimeline;
    readonly orbit: RateTimeline;
    readonly orbit2: RateTimeline;
    width: number;
    height: number;
    notice: string;
    showPalette: boolean;
    paletteQuery: string;
    page: number;
    scroll: number;
    windowSelected: number;
    drag: {
        index: number;
        x: number;
        y: number;
        startX: number;
        startY: number;
    } | null;
    simulation: boolean;
    editor: string;
    editorCursor: number;
    waveform: number[];
    sourceLabel: string;
    sensorSeq: number;
    private waveStates;
    protected serial: number;
    private routedRates;
    windows: WindowState[];
    constructor();
    configure(patch: Record<string, unknown>): void;
    resize(width: number, height: number): void;
    setScene(scene: string): void;
    setTime(timeMs: number): void;
    input(text: string): void;
    replaceDraft(text: string): void;
    backspace(): void;
    send(): void;
    receive(text: string): void;
    emit(x: number, y: number, glyph?: string, kind?: string): void;
    ingest(sample: SensorSample): boolean;
    demoData(timeMs: number): void;
    /** Validate and commit one bounded waveform block. Never fabricates samples.
     * Hardware access remains in the host; this accepts normalized telemetry only. */
    ingestWaveform(row: {
        source: string;
        samples: number[];
        seq: number;
        atMs: number;
        quality?: string;
    }): boolean;
    /** Commit sensor-rate targets on explicit DATA heartbeats, never in render().
     * This makes phase changes replayable and independent of presentation FPS.
     * Record these heartbeat timestamps alongside source samples for exact replay. */
    routeRates(atMs: number): void;
    effective(atMs?: number): ObservatoryOptions;
    windowProgress(w: WindowState): number;
    windowAlpha(w: WindowState): number;
    toggleWindow(index: number, mode: 'collapsed' | 'maximized' | 'fade'): void;
    exportState(): Record<string, unknown>;
}
/** Convert authored sRGB palette stops to Oklch for interpolation. The final
 * gamut map is performed by the shared integer C/WASM converter, not CSS/HSV. */
export declare function rgbToOklch(color: number): [number, number, number];
export declare function flattened(frame: StudioFrame, i: number): number;
export declare function putCell(frame: StudioFrame, x: number, y: number, glyph: number, fg: number, alpha?: number, id?: number): void;
/** Eight addressable braille bits share one foreground colour, as on a terminal. */
export declare function putDot(frame: StudioFrame, px: number, py: number, color: number, alpha?: number, id?: number): void;
/** Clipped braille segment; avoids unbounded loops for near-plane projections. */
export declare function drawSegment(frame: StudioFrame, x0: number, y0: number, x1: number, y1: number, color: number, alpha?: number, id?: number): void;
export interface ObservatoryFrame {
    frame: StudioFrame;
    nodes: StudioNode[];
    semantics: {
        id: number;
        label: string;
        disabled?: boolean;
    }[];
    drawnStars: number;
    activeWeather: number;
}
/** CPU material renderer, exporting ordinary terminal cells. Colors use the
 * shared OKLCh kernel; projection/scene composition is the TS high-level layer.
 * render() never owns a clock and never mutates the application's event log. */
export declare class ObservatoryRenderer {
    readonly engine: StudioEngine;
    private rampKey;
    private ramp;
    private stopTotal;
    private wheel;
    private wheelKey;
    constructor(engine: StudioEngine);
    private prepare;
    colorAt(phase: number): number;
    ink(hue: number): number;
    private field;
    background(m: ObservatoryModel, o?: ObservatoryOptions): StudioFrame;
    private twinkle;
    private warp;
    private weather;
    /** Paint local/remote text effects without touching stored content. Local input
     * is laid out last and never receives arrival or fall opacity. */
    private skyText;
    /** Render one immutable frame. No mutation to m.options/events/domain data. */
    /** Material plane without UI nodes, suitable below a terminal emulator buffer.
     * Caller still owns the child terminal's text, styles, cursor and presentation. */
    renderSurface(m: ObservatoryModel): StudioFrame;
    render(m: ObservatoryModel, atMs?: number): ObservatoryFrame;
}
export declare const ORBITAL_NODES: {
    id: string;
    label: string;
    x: number;
    y: number;
    z: number;
    parents: string[];
}[];
/** Shared composition of gallery/terminal scenes. Synthetic product mockups are
 * explicitly labeled. All drawing is cell output; no pixel shaders or CSS glow. */
export declare function composeObservatory(m: ObservatoryModel, o: ObservatoryOptions, r: ObservatoryRenderer, under: StudioFrame): {
    nodes: StudioNode[];
    semantics: {
        id: number;
        label: string;
        disabled?: boolean;
    }[];
};
/** Activate semantic IDs from pointer or keyboard through one path. Local study
 * actions never dispatch shell commands, agents, or network requests. */
export declare function activateObservatory(m: ObservatoryModel, id: number): void;
/** Minimal code-point-safe scratch editor, not a full Unicode/grapheme editor.
 * Cursor is a UTF-16 offset so browser textarea selections map directly.
 * No reads/writes/commands; one edit is committed before the host paints. */
export declare function editScratch(m: ObservatoryModel, action: string, value?: string): void;
