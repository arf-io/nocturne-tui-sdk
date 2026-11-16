/** Fleet domain state. No DOM, terminal, network, hidden clocks, or renderer access. */
export interface AgentSpec {
    id: string;
    name: string;
    role: string;
    description?: string;
}
export interface FleetMetrics {
    tokenRate: number;
    latencyMs: number;
    contextPermille: number;
    queue: number;
    tools: number;
    progressPermille: number;
}
export interface TextChunk {
    text: string;
    bornMs: number;
}
export interface FleetMessage {
    id: string;
    key: number;
    role: string;
    severity: string;
    text: string;
    chunks: TextChunk[];
    atMs: number;
    complete: boolean;
    local: boolean;
}
export interface AgentState extends AgentSpec {
    status: string;
    lastSeq: number;
    lastAtMs: number;
    metrics: FleetMetrics | null;
    history: FleetMetrics[];
    messages: FleetMessage[];
    droppedMessages: number;
    unread: number;
}
export interface FleetEvent {
    version: 1;
    seq: number;
    agentId: string;
    type: string;
    atMs: number;
    payload: Record<string, unknown>;
}
export interface RecordedEvent {
    event: FleetEvent;
    motionMs: number;
}
export interface FleetCommand {
    version: 1;
    commandId: string;
    type: 'agent.message';
    agentId: string;
    text: string;
}
export declare const FLEET_LIMITS: Readonly<{
    agents: 32;
    messages: 256;
    messageScalars: 16384;
    eventLog: 8192;
    history: 96;
    chunkRuns: 256;
    outbox: 64;
}>;
/** Reject invalid scalar values before mutation. */
export declare function checkedInt(value: unknown, min: number, max: number, name: string): number;
/** Bounded authoritative state. `ingest` validates an entire event before committing.
 * Sequence numbers are increasing PER AGENT; duplicates/older events return false.
 * Arrival motionMs is supplied by the host and is recorded for deterministic replay.
 * Text is retained unchanged; unsupported terminal glyphs are a presentation concern.
 */
export declare class FleetModel {
    readonly agents: AgentState[];
    readonly eventLog: RecordedEvent[];
    revision: number;
    droppedEvents: number;
    demo: boolean;
    private nextMessageKey;
    constructor(specs: AgentSpec[]);
    /** Find an existing agent; throws for unknown IDs. Never auto-creates identities. */
    agent(agentId: string): AgentState;
    private appendMessage;
    /** Validate/commit one version-1 Fleet event. Returns false for stale sequence numbers.
     * Throws TypeError/RangeError for malformed, unknown-agent/message or oversized data.
     * Example: model.ingest({version:1,seq:1,agentId:'atlas',type:'status',atMs:0,payload:{status:'running'}},0).
     */
    ingest(input: unknown, motionMs: number): boolean;
    /** Append a LOCAL operator message. This does not consume an upstream sequence or
     * claim network delivery; only the host's explicit command adapter can send it.
     */
    localMessage(agentId: string, messageId: string, text: string, motionMs: number): void;
    /** JSON-safe diagnostic snapshot. No credentials or runtime functions are included. */
    snapshot(): object;
    /** Lossless retained text. Display fading never changes exported transcript data. */
    transcript(agentId: string): string;
}
export interface TranscriptRun {
    text: string;
    bornMs: number;
}
export interface TranscriptLine {
    messageKey: number;
    messageId: string;
    role: string;
    severity: string;
    label: boolean;
    runs: TranscriptRun[];
    lineIndex: number;
}
/** Stateless wrapping/viewport helper. All lengths are Unicode scalars, matching
 * the renderer's documented narrow glyph profile, not full grapheme layout.
 */
export declare class TranscriptViewport {
    /** Wrap text without losing content or resetting arrival timestamps. Blank
     * separators and role labels are explicit rows. Width <=0 returns an empty list.
     */
    static wrap(messages: FleetMessage[], width: number): TranscriptLine[];
    /** Return the bottom-anchored window, or a history window offset in whole rows. */
    static visible(lines: TranscriptLine[], height: number, offset: number): TranscriptLine[];
}
export declare const DEMO_AGENTS: AgentSpec[];
export declare const DEMO_NOTES: string[];
/** Deterministic example telemetry, not a measurement of a real system. */
export declare function demoMetrics(agentIndex: number, tick: number): FleetMetrics;
/** Create a clearly labeled offline fixture fleet, with a seeded sample history.
 * This factory never contacts endpoints or claims to represent the user's agents.
 */
export declare function createDemoFleet(): FleetModel;
