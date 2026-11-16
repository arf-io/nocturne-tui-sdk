export declare const TEXT_EFFECTS: readonly ["instant", "fade", "rain", "scramble", "flipboard", "sweep-left", "sweep-right", "lift", "fall", "marquee", "iris", "constellation", "prism-weave", "ink-tide", "comet-stitch", "orbit", "fold", "zipper"];
export type TextEffect = typeof TEXT_EFFECTS[number];
export type TextPhase = 'show' | 'hide';
export interface TextOptions {
    effect: TextEffect;
    durationMs: number;
    delayMs: number;
    staggerMs: number;
    batchSize: number;
    seed: number;
    travelRows: number;
    spreadColumns: number;
    drift: number;
    speedJitter: number;
    alphabet: string;
    cycleHz: number;
    easing: 'linear' | 'smooth' | 'cubic' | 'back' | 'bounce';
    reverseOrder: boolean;
    randomOrder: boolean;
    trailLength: number;
    overshoot: number;
    turns: number;
    hueSpread: number;
    local: boolean;
}
export declare const DEFAULT_TEXT_OPTIONS: TextOptions;
export interface GlyphPose {
    index: number;
    glyph: string;
    x: number;
    y: number;
    opacity: number;
    hueDelta: number;
    settled: boolean;
    trail: {
        x: number;
        y: number;
        opacity: number;
    }[];
}
export declare const TEXT_RANGES: Record<string, [number, number, number]>;
/** Normalize all options atomically. Durations are per character; total length
 * adds start delay, duration jitter and ceil(characters / batchSize) staggering.
 * Throws RangeError on unsupported fields, invalid scalars or control glyphs.
 */
export declare function textOptions(patch?: Partial<TextOptions>): TextOptions;
export declare function ease(p: number, kind?: TextOptions['easing'], overshoot?: number): number;
/** Exact completion bound, including all delays. Does not round by frame rate. */
export declare function textDuration(text: string, patch?: Partial<TextOptions>): number;
/** Evaluate per-glyph poses at explicit ageMs. Endpoints are exact: show ->
 * original scalars at original columns, hide -> zero opacity. Calling twice
 * never advances a clock or RNG. Text remains available to semantic readers.
 * Example: sampleText('HELLO','show',400,{effect:'flipboard',batchSize:2}). */
export declare function sampleText(text: string, phase: TextPhase, ageMs: number, patch?: Partial<TextOptions>): GlyphPose[];
/** Retargetable choreography with continuity of glyph position and opacity.
 * show()/hide() capture the current visual state. Reversal starts there instead
 * of snapping to a canned endpoint. Text modifications belong to a new player;
 * local draft editing must never be fed into a delayed reveal player. */
export declare class TextPlayer {
    readonly text: string;
    options: TextOptions;
    private phase;
    private started;
    private initial;
    private active;
    constructor(text: string, options?: Partial<TextOptions>);
    private start;
    show(timeMs: number): void;
    hide(timeMs: number): void;
    configure(patch: Partial<TextOptions>, timeMs?: number): void;
    sample(timeMs: number): GlyphPose[];
}
