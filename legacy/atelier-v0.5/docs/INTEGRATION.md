# Embedding Nocturne Studio

## Ownership and scheduling

A host owns the terminal session, raw mode, frame presentation, input decoder, layout, focus, application data and lifecycle. The renderer owns no threads, keyboard, terminal, network, randomness source or wall clock. A call returns an owned row-major frame; never print ANSI from a nested widget into a framework-managed screen.

Use one explicit animation clock. Sample it at the decorative cadence. On input/data, apply the model change and render immediately using the existing sample. At high throughput coalesce pending model updates to the newest value only when the host cannot keep up; never drop durable application events just because not every state can be displayed. A blocking stdout writer still introduces transport latency.

```text
on motion deadline:
    motionMs = monotonic elapsed minus paused durations
    present(render(config, motionMs, ordered nodes, ordered events))
on data or input:
    update the application model immediately
    create any visual impulse at motionMs
    present(render(config, motionMs, ordered nodes, ordered events))
```

Pausing holds time and still accepts input. An impulse created during a pause is registered at the held time; it starts traveling when time resumes. Expire impulses based on the same clock, cap the replay list at 128, and choose a documented policy for bursts larger than that. The supplied hosts keep the latest bounded events. Do not use render-call count as time. Rendering at the same time has no side effects.

## Python: complete minimal snapshot

From the source root after `sh scripts/build.sh`:

```sh
PYTHONPATH=bindings/python python3 - <<'PY'
from studio import Studio, Node, Impulse
from terminal import AnsiWriter

studio = Studio(width=80, height=24, pattern=3, focusMode=1,
                focusX=40*256, focusY=12*256, stars=1)
studio.configure(palette=['#31354f','#655679','#4e7875'],
                 glyphs=['·','⠁','⠂','⠄'])
nodes = [Node('box', 3, 9, 72, 6, text='LIVE / value is authoritative',
              colorAnimation=2, bgOpacity=380),
         Node('progress', 5, 12, 66, 1, id=7, value=670, colorAnimation=2)]
events = [Impulse(20, 12, atMs=1700)]
writer = AnsiWriter()
print(writer.encode(studio.render(2500, nodes=nodes, events=events)), end='', flush=True)
print('\x1b[0m')
# In a framework adapter, consume frame.cells directly instead of printing.
PY
```

`Studio.configure()` copies and validates before replacing configuration. `Node.asDict()` is JSON-safe. `.hit(nodes,x,y)` returns `(stableId, zeroBasedItem)` or `None`. `.composite(dest,src,x=...,y=...,fgOpacity=...,bgOpacity=...)` mutates an owned destination; overlapping/malformed storage is rejected. `tween()` and `interaction.KeyframeTrack` interpolate explicit scalar values. `Dag` and `FocusModel` are optional Python host reference models, not dependencies of other languages.

`examples/studio_terminal.py --data-fd FD` accepts bounded newline-separated JSON on a caller-owned descriptor. Inspect its parser before wiring a producer; it is a demonstration transport, not authenticated network IPC. Authoritative values and prompt text can commit while motion is paused.

## TypeScript / Node

Run `node examples/studio_node.mjs` for the complete executable example. `bindings/typescript/studio.ts` compiles to `dist/typescript/studio.js` and declarations. `StudioEngine.create(wasmBytes,schema)` accepts a Uint8Array supplied by your loader. `.defaults(overrides)`, `.render(config,timeMs,nodes,events)`, `.hit(nodes,x,y)`, `.composite(...)` and `.tween(...)` use the native contract.

The binding does not fetch WASM or depend on Node/DOM APIs. After initialization, calls are synchronous and frames are copied. Each engine owns a WASM instance and scratch buffers; use separate instances in workers. JavaScript time is a safe integer through `Number.MAX_SAFE_INTEGER`; native time is unsigned 64-bit. Cross-language fixture times stay within the common range.

## Go

Run `(cd bindings/go && go test ./... && go run ./cmd/studio)`. The local module is `nocturne.local/surfaces`. Preserve the repository layout when consuming it:

```sh
go mod edit -require=nocturne.local/surfaces@v0.0.0
go mod edit -replace=nocturne.local/surfaces=/absolute/path/nocturne-surfaces/bindings/go
```

`NewStudio`, `Set`, `SetColors`, `SetGlyphs`, `NewStudioNode`, `StudioNode.Set`, `StudioNode.ChangedAt`, `Render`, `Hit`, `Composite` and `Tween` expose the shared contract. `StudioImpulse` uses Q8 coordinates. `cmd/studio/main.go` is complete. cgo compiles sibling C sources, so CGO_ENABLED=0 is not supported. Use separate instances when mutating configurations concurrently. The rendering algorithm is not duplicated in Go.

## Rust

Run `(cd bindings/rust && cargo test --all-targets && cargo run --example studio)`. A consuming application can use a path dependency:

```toml
[dependencies]
nocturne-surfaces = { path = "/absolute/path/nocturne-surfaces/bindings/rust" }
```

`studio::{Studio,StageKey,Node,NodeKind,NodeKey,Impulse}` provides typed configuration and owned frames. `examples/studio.rs` is complete. `build.rs` invokes native POSIX `cc` and `ar`, tracks included sources, and explicitly rejects cross compilation and Windows. No Cargo dependencies are needed. **Rust was not compiled locally.** See `RUST_REVIEW.md`; example source is not execution evidence.

## Framework bridge contract

Write cell frames into the host framework's own render representation. In Ratatui that means the supplied buffer rectangle; in Textual, rows/segments; in Bubble Tea, the host's view/message lifecycle; in Ink, framework-owned output. These are integration directions, **not shipped framework adapters**. Confirm each framework's version/API, input ownership and grapheme policy during integration. Never independently toggle terminal modes or write stdout inside a nested widget.

## Composition, focus and actions

Node order is back-to-front; hits traverse reverse order. Positive stable IDs are interactive, zero is decoration. Disabled nodes block hit-through. Applications should enforce unique IDs even though the renderer does not check global uniqueness. A hit returns identity/subitem, never executes an action.

Keep keyboard focus separate from selection. Trap modal input to modal nodes, then restore prior focus. The reference hosts illustrate this; the core does not own a window stack. A full-opacity background erases underneath. Partial backgrounds blend colors and can retain underlying glyphs.

Charts take normalized samples: scale your own units and expose original values in labels/details. Pie/donut weights are proportional positive values; scatter is interleaved x/y. A colorful shape is not an accessible data model. Publish semantic names/values and keyboard actions; browser semantic buttons demonstrate this but are not a complete screen-reader solution.

## Distribution / ABI

Keep the source tree layout intact while vendoring. ABI v1 retains its 448-byte config and functions; Studio v2 adds separate 704-byte config,128-byte node,32-byte impulse records. Cells are four uint32 words. Raw C callers satisfy alignment/liveness/nonalias contracts; bindings return owned snapshots. Change version markers for breaking layouts. Source/checkouts are supplied, not independent wheel/npm/crate distribution artifacts.
