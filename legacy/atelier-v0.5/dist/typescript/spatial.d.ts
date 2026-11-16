/** Deterministic, bounded graph layout and an explicit camera rig.
 * All lengths are world units; angles are degrees. No timers or rendering APIs.
 * The synchronous convenience solver and chunked job use identical iterations.
 */
import { Vec3 } from './observatory.js';
export interface GraphNode {
    id: string;
    label?: string;
    width?: number;
    height?: number;
    pin?: Vec3;
}
export interface GraphEdge {
    source: string;
    target: string;
}
export interface Graph {
    nodes: GraphNode[];
    edges: GraphEdge[];
}
export interface LayoutOptions {
    dimensions: 2 | 3;
    algorithm: 'layered' | 'force' | 'radial';
    seed: number;
    iterations: number;
    rankGap: number;
    nodeGap: number;
    depthGap: number;
    repulsion: number;
    spring: number;
    damping: number;
    cyclePolicy: 'condense' | 'reject';
}
export interface PlacedNode extends GraphNode, Vec3 {
    label: string;
    width: number;
    height: number;
    rank: number;
    component: number;
}
export interface Bounds3 {
    min: Vec3;
    max: Vec3;
}
export interface GraphLayout {
    nodes: PlacedNode[];
    edges: GraphEdge[];
    cycles: string[][];
    bounds: Bounds3;
    warnings: string[];
    iterations: number;
    options: LayoutOptions;
}
export declare const DEFAULT_LAYOUT_OPTIONS: LayoutOptions;
export declare function idHash(id: string): number;
export declare function layoutOptions(patch?: Partial<LayoutOptions>): LayoutOptions;
/** Validate and clone a graph. Limit: 256 nodes, 2048 edges. Stable IDs are
 * sorted with codepoint ordering, independent of locale and input order.
 * Duplicate IDs/edges and dangling references are errors, not implicit edits.
 */
export declare function validateGraph(graph: Graph): Graph;
/** Cooperative graph layout. Call step(4..16) from the host's work queue, NOT
 * from render(); commit result only when done. Fixed iterations, stable seed,
 * and copied inputs make the result independent of scheduler chunk size/FPS.
 * Force solving is O(iterations * nodes²), deliberately capped at 256 nodes.
 * Pins may overlap; warnings disclose conflicts instead of moving a pin.
 */
export declare class GraphLayoutJob {
    readonly options: LayoutOptions;
    readonly graph: Graph;
    readonly cycles: string[][];
    readonly nodes: PlacedNode[];
    done: boolean;
    completed: number;
    private velocities;
    private indices;
    private total;
    constructor(graph: Graph, options?: Partial<LayoutOptions>);
    step(budget?: number): boolean;
    result(): GraphLayout;
}
/** Blocking convenience for small graphs, CLI hosts and tests. Throws on invalid
 * data/limits; does not mutate the graph. Browser hosts should step a job. */
export declare function layoutGraph(graph: Graph, options?: Partial<LayoutOptions>): GraphLayout;
/** Camera looking toward target, with screen-right x and screen-up y. Orbit
 * moves around target; look rotates without moving the eye; pan moves both.
 * All interaction deltas are explicit, and work with a paused animation clock.
 */
export declare class CameraRig {
    target: Vec3;
    yaw: number;
    pitch: number;
    roll: number;
    distance: number;
    fov: number;
    private radians;
    basis(): {
        forward: Vec3;
        right: Vec3;
        up: Vec3;
    };
    position(): Vec3;
    orbit(dx: number, dy: number): void;
    look(dx: number, dy: number): void;
    pan(right: number, up: number, forward?: number): void;
    dolly(factor: number): void;
    reset(): void;
    fit(b: Bounds3, width?: number, height?: number): void;
    /** Capture a projection transform once per render. Later camera edits do
     * not mutate this snapshot. Reuse it for many points instead of recalculating
     * trigonometry per cell. Width/height are terminal-cell dimensions. */
    projector(width: number, height: number): (p: Vec3) => {
        x: number;
        y: number;
        z: number;
        scale: number;
    } | null;
    project(p: Vec3, width: number, height: number): {
        x: number;
        y: number;
        z: number;
        scale: number;
    } | null;
    snapshot(): {
        target: {
            x: number;
            y: number;
            z: number;
        };
        yaw: number;
        pitch: number;
        roll: number;
        distance: number;
        fov: number;
    };
}
