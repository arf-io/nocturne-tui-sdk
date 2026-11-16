export declare const WINDOW_EFFECTS: readonly ["fade", "expand-center", "expand-nw", "expand-ne", "expand-sw", "expand-se", "circle", "roll-up", "roll-down", "drawer-left", "drawer-right", "drawer-top", "drawer-bottom", "bounce", "genie", "explode", "accordion", "origami", "vortex", "ribbon-unspool", "petal-bloom", "gravity-well"];
export type WindowEffect = typeof WINDOW_EFFECTS[number];
export declare const WINDOW_SHAPES: readonly ["rectangle", "rounded", "ellipse", "hexagon", "diamond", "capsule", "ticket", "cloud", "polygon"];
export type WindowShape = typeof WINDOW_SHAPES[number];
export type WindowAction = 'minimize' | 'maximize' | 'fade' | 'close';
export interface WindowOptions {
    effect: WindowEffect;
    durationMs: number;
    chrome: 'mac' | 'windows' | 'gnome' | 'custom';
    customSide: 'left' | 'right';
    customGlyphs: string[];
    customOrder: WindowAction[];
    toolColors: Record<WindowAction, number>;
    toolWidth: number;
    toolHeight: number;
    shape: WindowShape;
    opacity: number;
    depth: number;
    yaw: number;
    pitch: number;
    roll: number;
    fadeFloor: number;
    bounce: number;
    scatter: number;
    genieBend: number;
    seed: number;
    polygon: number[][];
}
export declare const DEFAULT_WINDOW_OPTIONS: WindowOptions;
export declare const WINDOW_RANGES: Record<string, [number, number, number]>;
/** Simple normalized polygon validation (3..32 vertices). Crossing edges and
 * zero area reject. Convex and concave simple masks are both supported. */
export declare function validatePolygon(points: number[][]): number[][];
export declare function windowOptions(patch?: Partial<WindowOptions>, base?: WindowOptions): WindowOptions;
export declare function windowMask(shape: WindowShape, u: number, v: number, polygon?: number[][]): boolean;
interface Tween {
    from: number;
    to: number;
    at: number;
    duration: number;
}
export interface WindowSpec {
    title: string;
    x: number;
    y: number;
    width: number;
    height: number;
    shape?: WindowShape;
    depth?: number;
}
export interface ManagedWindow extends WindowSpec {
    id: number;
    shape: WindowShape;
    depth: number;
    yaw: number;
    pitch: number;
    roll: number;
    mode: 'normal' | 'minimized' | 'closed';
    maximized: boolean;
    rolled: boolean;
    visibility: Tween;
    fade: Tween;
    maximize: Tween;
    body: Tween;
    stack: number;
}
export interface WindowSample {
    x: number;
    y: number;
    width: number;
    height: number;
    visibility: number;
    alpha: number;
    depth: number;
    yaw: number;
    pitch: number;
    roll: number;
    rolled: boolean;
    bodyScale: number;
}
export interface WindowTool {
    action: WindowAction;
    glyph: string;
    color: number;
    x: number;
    y: number;
    width: number;
    height: number;
}
/** Bounded state owner; mutation is explicit, rendering and sampling are pure.
 * All commands carry motion milliseconds. show/hide are reversible; windows
 * are never deleted by the close button, so a user can recover them in the dock.
 */
export declare class WindowManager {
    options: WindowOptions;
    readonly windows: ManagedWindow[];
    selected: number;
    private serial;
    private stack;
    viewport: {
        width: number;
        height: number;
    };
    configure(patch: Partial<WindowOptions>): void;
    add(spec: WindowSpec): number;
    get(id: number): ManagedWindow;
    private set;
    hide(id: number, time: number, closed?: boolean): void;
    show(id: number, time: number): void;
    /** Restore visibility, ink and rolled body without discarding placement. */
    restore(id: number, time: number): void;
    /** Roll the body into its tool strip, with reversible explicit-time motion. */
    toggleRoll(id: number, time: number): void;
    focus(id: number): void;
    action(id: number, action: WindowAction, time: number): void;
    sample(id: number, time: number): WindowSample;
    tasks(): {
        id: number;
        title: string;
        mode: string;
        selected: boolean;
    }[];
    controls(id: number): WindowTool[];
}
/** Map local window coordinates through a reversible visibility field. Return
 * null for unrevealed cells (circle/roll/drawer), otherwise displaced cells.
 * Position is in cell coordinates. The caller applies 3D tilt/perspective next.
 * Named experimental effects are original compositions, not a novelty claim.
 */
export declare function warpWindowCell(u: number, v: number, width: number, height: number, visibility: number, effect: WindowEffect, o: WindowOptions): {
    x: number;
    y: number;
    alpha: number;
} | null;
export {};
