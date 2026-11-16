/** Nocturne WASM binding. No DOM, Node APIs, framework, or terminal side effects. */
export interface Field {
    name: string;
    index: number;
    default: number;
    minimum: number;
    maximum: number;
    description: string;
}
export interface Schema {
    schemaVersion: number;
    abiVersion: number;
    fields: Field[];
    gradientPalette: string[];
    starPalette: string[];
}
export interface SurfaceSettings {
    values: Record<string, number>;
    palette: string[];
    starPalette: string[];
    glyphs: string[];
}
export interface CellFrame {
    width: number;
    height: number;
    cells: Uint32Array;
}
/** Parse a strict #RRGGBB string; throws RangeError for invalid colors. */
export declare function parseColor(value: string): number;
/** A shared, stateless renderer. Sequential calls may use unrelated configurations.
 * Each returned frame is an owned copy. An instance must not be reentered while
 * rendering. Independent instances can run in independent workers.
 */
export declare class NocturneEngine {
    private native;
    readonly schema: Schema;
    private constructor();
    /** Instantiate supplied bytes; no fetch, external assets, or host imports.
     * Throws WebAssembly errors for invalid bytes, Error for ABI mismatch.
     * Example: const engine=await NocturneEngine.create(bytes,schema);
     */
    static create(bytes: Uint8Array, schema: Schema): Promise<NocturneEngine>;
    /** Produce independent defaults and validate any named integer overrides. */
    defaults(changes?: Record<string, number>): SurfaceSettings;
    /** Validate named keys, finite integer ranges, palettes, and custom glyphs.
     * Throws RangeError or TypeError; does not mutate config.
     */
    validate(config: SurfaceSettings): void;
    /** Render at an explicit time. Data may change at the same motion timestamp.
     * Returns row-major [glyph, foreground, background, flags] uint32 words.
     * Inputs: validated config, safe nonnegative integer milliseconds, <=512 code
     * points of demo text. Throws RangeError for input/renderer errors.
     */
    render(config: SurfaceSettings, motionMs: number, text?: string): CellFrame;
}
/** Encode a complete owned frame as ANSI without taking over a terminal.
 * Synchronized output is opt-in and must be negotiated by the host.
 * Suitable for a standalone view; framework adapters should consume cells.
 */
export declare function toAnsi(frame: CellFrame, synchronized?: boolean): string;
