# Embedding Pearl Fleet

## Run the delivered build

The browser file is self-contained, with no installation or server. The terminal host uses Node.js 22 and the bundled compiled JavaScript/WASM:

```sh
node examples/fleet_terminal.mjs
node examples/fleet_terminal.mjs --agent atlas --palette smart-dark
node examples/fleet_terminal.mjs --dense --columns 120 --rows 40
```

Run the host inside an existing tmux pane like any other full-screen TUI. It does not alter tmux configuration or start an AFD status writer. Live tmux was not tested in this environment. The earlier eight profiles remain in `tmux/`.

On a source change, run `sh scripts/build.sh --wasm`, `tsc -p tsconfig.json`, then `python3 scripts/build_fleet_gallery.py`. A native C compiler is only required for rebuilding and native Python/Go/Rust usage; the delivered Node host runs its bundled WASM.

## Model and host responsibilities

`FleetModel` owns bounded data. `FleetController` owns focus, transitions, per-agent drafts/history, an explicit outbox and composition policy. `composeFleet()` emits normalized Studio nodes. `StudioEngine` renders the nodes through C/WASM. The host owns clocks, input decoding, transport, output and lifecycle.

A complete initialization example is `examples/fleet_terminal.mjs`. The browser counterpart is `web/fleet.template.html`; its builder embeds compiled modules and the same WASM. Neither host is a replacement for a production provider adapter.

```typescript
import { StudioEngine } from './dist/typescript/studio.js';
import { FleetModel, FleetController } from './dist/typescript/fleet.js';

// wasmBytes and studioSchema are loaded by your application, not by the engine.
const engine = await StudioEngine.create(wasmBytes, studioSchema);
const model = new FleetModel([
  { id: 'coordinator', name: 'COORDINATOR', role: 'Task orchestration' },
  { id: 'research', name: 'RESEARCH', role: 'Evidence gathering' },
]);
const fleet = new FleetController(engine, model, {
  expandMs: 560,
  arrivalMs: 520,
  horizonRows: 6,
  horizonMinimum: 760,
});
fleet.resize(144, 48);

function frameNow() {
  const scene = fleet.compose();
  return engine.render(scene.config, scene.timeMs, scene.nodes, scene.events);
}

function onIncomingEvent(event: unknown) {
  fleet.ingest(event);       // authoritative state changes now
  present(frameNow());      // your host's presentation function; no frame wait
}

function onMotionDeadline(explicitMotionMs: number) {
  fleet.setTime(explicitMotionMs);
  present(frameNow());
}
```

`present`, `wasmBytes`, and `studioSchema` above are intentionally host-supplied integration points. The complete runnable host defines them. Never write independent ANSI into a parent TUI framework's screen; copy returned cells into its buffer instead.

## Event contract

Every event has `version:1`, a stable configured `agentId`, positive integer `seq` increasing **per agent**, nonnegative integer source `atMs`, a type and payload. Unknown/stale agents are not created. Duplicate/older sequence numbers return false without mutation. Invalid new data throws without consuming the sequence. Known fields are normalized into the replay log; arbitrary extra properties are not retained.

```json
{"version":1,"seq":1,"agentId":"coordinator","type":"telemetry","atMs":1200,"payload":{"tokenRate":67,"latencyMs":184,"contextPermille":530,"queue":3,"tools":12,"progressPermille":670}}
{"version":1,"seq":2,"agentId":"coordinator","type":"message.start","atMs":1220,"payload":{"messageId":"reply-42","role":"agent","severity":"normal"}}
{"version":1,"seq":3,"agentId":"coordinator","type":"message.delta","atMs":1230,"payload":{"messageId":"reply-42","text":"First arriving text. "}}
{"version":1,"seq":4,"agentId":"coordinator","type":"message.delta","atMs":1270,"payload":{"messageId":"reply-42","text":"The previous run does not restart."}}
{"version":1,"seq":5,"agentId":"coordinator","type":"message.end","atMs":1290,"payload":{"messageId":"reply-42"}}
```

Telemetry fields are authoritative scalar samples, not decorative targets. Token rate/latency/queue/tools accept 0..1,000,000; context and progress are thousandths 0..1000. Graph display scales currently use throughput 0..140, latency 0..600 ms and context 0..100%; plotted values above the display scale clip, while labels and exports retain their actual values. Change the composer scale explicitly for different workloads; automatic scaling is not implemented.

Statuses: running, waiting, idle, offline, error. Message roles: agent, operator, tool, system. Severities: normal, warning, error. A completed message refuses additional chunks. Text is retained literally; the renderer sanitizes unsupported/control glyphs for display and never executes them.

## Input and output descriptors

The Node host supports an inherited **pipe or socket** for newline-separated input and an explicit output descriptor for command records. The input uses nonblocking libuv stream I/O, avoiding a blocked file-read worker that could hang exit while the producer remains open. Do not pass a regular file directly to `--data-fd`; stream it through a pipe. Each inbound line is bounded to 64 KiB; invalid lines report an error and the host continues.

This runnable Bash example uses a labeled synthetic external producer and appends outbound records to a file:

```sh
node examples/fleet_terminal.mjs \
  --agents examples/fleet_agents.json \
  --data-fd 3 --commands-fd 4 \
  3< <(python3 examples/fleet_event_source.py) \
  4>> fleet-outbox.ndjson
```

The default internal simulation is disabled when `--data-fd` or `--agents` is used. Replace the producer with your authenticated source and replace the sink with your command transport. The preview does not manage authentication, reconnects, authorization, ACKs or provider limits.

`fleet.send(text)` appends a local/outbound message and queues `{version,commandId,type:'agent.message',agentId,text}`. `drainCommands()` transfers pending records to the host. A returned command is **not a delivery acknowledgement**. The host must persist/retry/ACK outside this renderer. The bounded outbox throws when full instead of silently losing messages. Rendered frames may coalesce under output backpressure, but queued domain events are not discarded to catch up.

## Native Python and Go

Export a scene from the browser, or generate one without a terminal:

```sh
node examples/fleet_terminal.mjs --agent atlas --scene-out /tmp/fleet.scene.json
sh scripts/build.sh
python3 examples/fleet_scene.py /tmp/fleet.scene.json --hash
(cd bindings/go && go run ./cmd/fleet-scene /tmp/fleet.scene.json)
```

Python `renderFleetScene(sceneDict)` returns the native owned Frame. Go `RenderFleetScene(jsonBytes)` does the same. The two hash commands should print the identical SHA-256 of canonical cells. Scene readers do not implement agent networking or high-level Fleet interaction. A host can create its own model and use the same nodes directly.

The additive opacity helper is available as Python `fleetInkOpacity`, Go `FleetInkOpacity`, Rust `studio::fleetInkOpacity`, and TypeScript `StudioEngine.inkOpacity`. Its arguments are `(ageMs,fadeMs,rowQ8,bandQ8,topMinimum)`: time in unsigned milliseconds, positions in cells ×256, opacity in thousandths. Zero duration is immediate; zero band disables top fading.

## Rust

```sh
(cd bindings/rust && cargo test --all-targets)
(cd bindings/rust && cargo run --example fleet_ink)
```

`examples/fleet_ink.rs` is a complete host-neutral composition example. `tests/fleet_fixtures.rs` checks 96 scalar values and two accepted complete Fleet frames through the safe façade. These were supplied and reviewed but **not compiled locally** because Cargo/rustc were unavailable. CI requires Rust and must fail if it is absent. See `RUST_REVIEW.md` in this directory.

## Replay, storage and safety

`compose()` is pure; rendering a scene twice yields the same canonical cells. Inbound records store their supplied motion timestamps. The UI's action/scroll/pause/configuration history is not automatically included in the event log; capture those actions as well for a full session replay. Retained-event export alone cannot reconstruct evicted history without a snapshot/checkpoint. Snapshot restore/import is not provided.

Models/frames are owned on one controller thread. Host callers must serialize mutations or create independent controller/engine instances. No session data is automatically persisted by the browser; exports are explicit. Notes and transcripts may contain sensitive information supplied by your future adapter, so choose export/storage permissions accordingly.

Terminal input is a basic scalar draft composer, not a shell editor. Tab, arrows, Escape, Enter, page movement, backspace and SGR mouse are supported. General grapheme editing, sophisticated selections, IME integration in native terminals and rich clipboard protocols are not implemented. Browser textarea provides its platform's ordinary editing behavior.
