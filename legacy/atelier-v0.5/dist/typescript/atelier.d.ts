import { StudioEngine, StudioFrame } from './studio.js';
import { ObservatoryModel, ObservatoryRenderer, ObservatoryFrame } from './observatory.js';
import { CameraRig, Graph, GraphLayout, GraphLayoutJob, LayoutOptions } from './spatial.js';
import { TextPlayer, TextOptions } from './text_fx.js';
import { ParticleOptions } from './particles.js';
import { ManagedWindow, WindowManager, WindowOptions } from './window_fx.js';
export declare const ATELIER_VERSION = "0.5.0";
export declare const ATELIER_SCENES: {
    id: string;
    name: string;
    detail?: string;
}[];
export declare const DEFAULT_GRAPH: Graph;
export declare class AtelierModel extends ObservatoryModel {
    readonly camera: CameraRig;
    workspace: WindowManager;
    layout: GraphLayout;
    graph: Graph;
    layoutConfig: LayoutOptions;
    layoutJob: GraphLayoutJob | null;
    layoutSerial: number;
    private layoutFrom;
    private layoutAt;
    selectedNode: string;
    textValue: string;
    textConfig: TextOptions;
    textPlayer: TextPlayer;
    particleConfig: ParticleOptions;
    textPhase: 'show' | 'hide';
    textStarted: number;
    private lastTimelineEdit;
    private forkTimelines;
    routeRates(atMs: number): void;
    recipe: string;
    flightSpeed: number;
    private flightX;
    private flightY;
    private flightZ;
    layoutBusy: boolean;
    cameraMode: 'orbit' | 'look';
    windowMotion: string;
    constructor();
    configure(patch: Record<string, unknown>): void;
    private updateFlight;
    setVelocity(speed: number): void;
    flightPosition(): {
        x: number;
        y: number;
        z: number;
    };
    aimTravel(): void;
    setScene(scene: string): void;
    resize(w: number, h: number): void;
    cameraCommand(command: string, amount?: number): void;
    frameGraph(): void;
    beginLayout(patch?: Partial<LayoutOptions>, graph?: Graph): number;
    stepLayout(serial?: number, budget?: number): boolean;
    private commitLayout;
    graphPositions(): GraphLayout['nodes'];
    configureText(patch: Partial<TextOptions>): void;
    playText(phase: 'show' | 'hide', restart?: boolean): void;
    setDisplayText(text: string): void;
    configureParticles(patch: Partial<ParticleOptions>): void;
    windowConfigure(patch: Partial<WindowOptions>): void;
    /** Preserve local notes/edit buffers when applying visual settings. This is
     * not provider/session restoration and does not copy hardware subscriptions. */
    preserveLocalContent(previous: AtelierModel): void;
    exportState(): Record<string, unknown>;
}
export interface AtelierFrame extends ObservatoryFrame {
    windowHits: {
        id: number;
        action: string;
        x: number;
        y: number;
        width: number;
        height: number;
    }[];
    visibleNodes: number;
}
export type WindowBodyPainter = (body: StudioFrame, timeMs: number, window: Readonly<ManagedWindow>) => void;
export declare class AtelierRenderer {
    readonly engine: StudioEngine;
    private bodyPainters;
    /** Attach application-owned body content. The callback receives a fresh owned
     * cell surface below the chrome, with inherited colors and explicit time.
     * Do not mutate model state or read a wall clock while painting. Custom hit
     * IDs >=100000 are available to the host's action dispatcher. */
    setWindowPainter(id: number, painter: WindowBodyPainter | null): void;
    readonly base: ObservatoryRenderer;
    private heatColors;
    private heatColor;
    constructor(engine: StudioEngine);
    private stars;
    private warp;
    private particles;
    private graph;
    private spatialMenu;
    private typography;
    private paintText;
    private windows;
    render(m: AtelierModel): AtelierFrame;
}
/** Shared activation route for terminal hit IDs and browser companion controls. */
export declare function activateAtelier(m: AtelierModel, id: number): void;
