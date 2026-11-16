/** Nocturne Studio. One native/WASM material and widget kernel; no host side effects. */
export interface StudioField {
    name: string;
    index: number;
    default: number;
    minimum: number;
    maximum: number;
    description: string;
}
export interface StudioSchema {
    abiVersion: number;
    fields: StudioField[];
}
export interface StudioConfig {
    values: Record<string, number>;
    palette: string[];
    starPalette: string[];
    glyphs: string[];
    novaGlyphs: string[];
}
export interface StudioFrame {
    width: number;
    height: number;
    cells: Uint32Array;
}
export interface StudioNode {
    kind: string;
    x: number;
    y: number;
    width: number;
    height: number;
    text?: string;
    data?: number[];
    changedMs?: number;
    [key: string]: string | number | number[] | undefined;
}
export interface StudioImpulse {
    x: number;
    y: number;
    atMs: number;
    strength?: number;
    kind?: number;
    id?: number;
}
export declare const STUDIO_KINDS: string[];
/** Stateful configuration is owned by the caller. Calls are synchronous, non-reentrant.
 * Returned frames own storage. Use separate engines in separate workers.
 */
export declare class StudioEngine {
    private native;
    readonly schema: StudioSchema;
    private constructor();
    /** Instantiate caller-supplied WASM. No fetch, imports, terminal, or event loop. */
    static create(bytes: Uint8Array, schema: StudioSchema): Promise<StudioEngine>;
    /** Create independent defaults. Unknown or out-of-range values are rejected at render. */
    defaults(overrides?: Record<string, number>): StudioConfig;
    /** Validate before copying config into bounded native scratch. */
    private packConfig;
    private packNodes;
    /** Pure rendering. timeMs is explicit, safe integer milliseconds. Calling again
     * at the same time with new nodes implements an immediate data-only commit.
     * Throws RangeError for bounds/invalid config; output never aliases scratch.
     */
    render(config: StudioConfig, timeMs: number, nodes?: StudioNode[], events?: StudioImpulse[]): StudioFrame;
    /** Gamut-mapped OKLCh, integer L/1000, C/10000, millidegrees. Throws RangeError.
     * Example: engine.oklch(700,1400,270000). No allocation or clock access. */
    oklch(l: number, c: number, h: number): number;
    /** Approximate Oklab lightness of packed sRGB in thousandths. */
    lightness(color: number): number;
    /** Paint nodes over an existing surface. Retains background sampling until ink
     * occupies a cell. Caller retains original storage; result is a copied frame. */
    paint(frame: StudioFrame, timeMs: number, nodes: StudioNode[], config?: StudioConfig): StudioFrame;
    /** Reverse-z hit testing; disabled regions block. Returns semantic ID and subitem. */
    hit(nodes: StudioNode[], x: number, y: number): {
        id: number;
        item: number;
    } | null;
    /** Composite an independent source frame into dest and return an owned result. */
    composite(dest: StudioFrame, src: StudioFrame, x?: number, y?: number, fgOpacity?: number, bgOpacity?: number): StudioFrame;
    /** Scalar keyframe interpolation, clamped at the target; same arithmetic as C. */
    tween(from: number, to: number, elapsedMs: number, durationMs: number, easing?: number): number;
    /** Opacity for arriving transcript ink with a spatial top-edge fade.
     * Inputs: arrival age/duration in ms, row and top band in Q8 cells, minimum
     * in thousandths. fadeMs=0 disables arrival animation. Returns 0..1000.
     * Throws RangeError for invalid values; no mutation. Example:
     * engine.inkOpacity(420,420,3*256,6*256,760) === 880.
     */
    inkOpacity(ageMs: number, fadeMs: number, rowQ8: number, bandQ8: number, topMinimum: number): number;
}
