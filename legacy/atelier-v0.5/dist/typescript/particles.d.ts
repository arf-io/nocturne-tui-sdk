export interface ParticleOptions {
    lifeMs: number;
    count: number;
    speed: number;
    gravity: number;
    rise: number;
    drag: number;
    turbulence: number;
    glitterHz: number;
    trailMs: number;
    branches: number;
    jaggedness: number;
    coreMs: number;
    coreRadius: number;
    ejecta: number;
    shockwave: number;
    intensity: number;
    seed: number;
    reducedMotion: boolean;
}
export declare const DEFAULT_PARTICLE_OPTIONS: ParticleOptions;
export declare const PARTICLE_RANGES: Record<string, [number, number, number]>;
export declare function particleOptions(patch?: Partial<ParticleOptions>): ParticleOptions;
export interface BurstEvent {
    id: number;
    x: number;
    y: number;
    atMs: number;
    kind: string;
}
export interface ParticlePoint {
    x: number;
    y: number;
    glyph: string;
    alpha: number;
    heat: number;
}
export interface ParticleSegment {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
    alpha: number;
    heat: number;
}
export interface ParticleGlow {
    x: number;
    y: number;
    radius: number;
    alpha: number;
    heat: number;
    ring?: boolean;
}
export interface BurstFrame {
    points: ParticlePoint[];
    segments: ParticleSegment[];
    glows: ParticleGlow[];
}
/** sampleBurst(event, nowMs, options) returns owned primitives. Heat is a 0..1
 * palette selector, not a temperature reading. Timeline and position units:
 * milliseconds, terminal cells (vertical geometry uses 2:1 cell aspect). */
export declare function sampleBurst(e: BurstEvent, nowMs: number, patch?: Partial<ParticleOptions>): BurstFrame;
