# Nocturne Observatory: application-builder handoff

Copy this document into a fresh model/agent session with the source SDK attached or checked out. Fill in the short application brief below. The model must inspect the actual checkout before coding; this document is guidance, not evidence that a dependency or service is connected.

---

## Your assignment

Build a usable application with the supplied Nocturne SDK, preserving its immediate-input, explicit-time, terminal-ownership and source-truth contracts. Treat the terminal as a medium for expressive interaction, not as a log dump with a neon border. Deliver working code, reproducible tests, an interactive example and a maintainable handoff. Do not substitute screenshots, an outline or a disconnected mockup for a requested working application.

**Application brief**

- Application/purpose: [describe the user's work and what success looks like]
- Primary users and workflows: [expert/occasional users, frequent actions, inspection/drill-down]
- Host language/framework: [TypeScript/Node, Rust, Python, Go; existing framework or new app]
- Data sources and outbound actions: [schemas, transports, identities, explicit permissions]
- Environment/constraints: [OS, terminal, tmux/SSH, viewport, offline/privacy, input accessibility]
- Visual direction: [palette/recipe, density, motion budget, components to emphasize]

Where the brief is incomplete, proceed with the smallest labelled assumptions that do not invent credentials, endpoints, data semantics, authorization or inaccessible hardware. Ask only when an ambiguity changes the implementation or creates a consequential external action.

## Start from evidence, not from a reconstruction

Read, in order:

1. `README.md`, `AGENTS.md`, `CHANGELOG.md`, `BUILD-IDENTITY.json` when supplied.
2. `docs/observatory/INTEGRATION.md`, `CONTROLS.md`, `SENSORS.md`, `PTY.md`, `TEST_REPORT.md`, `RUST_REVIEW.md`.
3. `observatory.schema.json`, `observatory.recipes.json`, `palettes.json`, `studio.schema.json`.
4. The relevant runnable host: `examples/observatory_terminal.mjs`, `examples/observatory_embed.mjs`, or `examples/fleet_terminal.mjs` and `docs/fleet/INTEGRATION.md`.
5. The actual public API source and its tests, not only generated declaration files.

Inspect `git status`, branch, log and remotes. The bundled history continues the original Nocturne baseline; do not initialize a replacement history over it. When a remote exists, inspect its most recent relevant branch/PR and reconcile local changes before work. Never overwrite an operator's uncommitted work. Create a feature branch. Preserve reference fixtures and retain tests for every fixed bug.

## Know what is shared and what is not

The rendering foundation is **C11**, not a Rust rewrite. Its native/WASM widget/color/composition APIs have Rust, Python, Go and TypeScript facades. `bindings/typescript/observatory.ts` implements the new high-level materials, spatial scene model, sensor routing and interaction. The full Fleet model is also TypeScript. Do not claim the TypeScript model exists natively in the other languages.

For a TypeScript application, import and compose these classes. For Rust/Python/Go, reuse native primitives and either implement the application's own state/layout, port only the required high-level model with conformance tests, or choose a clearly bounded documented scene bridge. Do not add a hidden Node process just to make a supposedly native package appear complete. Discuss that tradeoff explicitly.

Existing framework adapters are not complete products. The outer framework owns the terminal and event loop. Integrate returned cells, never run a second writer or raw-mode manager inside a widget.

## Interaction and timing are non-negotiable

1. Local drafts, cursor changes, focus changes and authoritative data commit synchronously on input/event receipt. Immediately render/present with the current decorative time; never wait for the next animation tick. Newly typed text has full foreground opacity and zero arrival/reveal delay. A growing panel must retain a visible input plane even before its body is large enough for the final layout.
2. Decorative motion is sampled by elapsed time. The default presentation ceiling is 60 FPS, configurable downwards or upwards. At a shared logical timestamp, 30 and 60 FPS have the same animation phase and duration. Do not multiply animation speeds by FPS or advance them by frame count.
3. Pausing motion must not pause editing, incoming data, accessibility text, error display or inspection. Text revealed while paused must not vanish and re-fade on resume. Remote arrival fades and top-edge attenuation are separate policies from local input.
4. Speed changes integrate from the current position. Reversing an expanding/collapsing/fading surface starts at its current appearance, not from an arbitrary endpoint. Use explicit bounded checkpoints for historical rate changes.
5. Backpressure may replace a not-yet-written decorative frame, not drop source events, commands, transcript text or state transitions. Bound all queues and expose overflow meaningfully.
6. Record the timestamps required for replay: motion/input/configuration changes, source measurements, data heartbeats and an initial checkpoint. Current exported snapshots are inspection artifacts, not a complete arbitrary-session restore facility. Do not claim replay from insufficient data.

## Design in the medium

Use OKLCh for new hue sweeps and palette interpolation. Keep intended lightness separate from chroma and hue. Use the shared converter for sRGB output; reduce out-of-gamut chroma at fixed lightness/hue. Do not describe it as a perfect perceptual/display guarantee. Legacy color modes remain available for old fixtures and applications, not as the default direction for new work.

Interpret gradient distance as **screens between adjacent stops**. Expose stop weights and feathering. Offer whole-cell, half-block and braille sampling deliberately. A terminal cell has one foreground/background pair; braille is eight coverage bits, not eight independent RGB pixels. Composite pseudo-alpha before output, and flatten subcell backgrounds where readable text needs the cell.

A saturated material should not erase semantic status. Preserve warning/error emphasis, focus, disabled state, selected state, units, source identity, stale markers and readable text. Include a reduced-motion/read mode and a 2D alternative to pseudo-3D navigation. Depth must not make a node unreachable by keyboard. Shared-parent DAGs retain one node identity, not duplicated tree branches posing as separate entities.

Compose information purposefully: a stable header, compact identity/status strip, clearly focused work area, contextual inspector, restrained activity cues and a persistent input plane. Use animations to show selection, transitions and arrivals. Avoid unbounded ambient animation that obscures failures or wastes output bandwidth. Measure cell generation, encoding, bytes/second and input latency separately; a fast kernel is not proof of physical 60 FPS.

Use the built-in studies as executable examples, not as proof that a BBS, web browser, editor, agent backend or hardware monitor is already integrated. Pico/Nano/Lynx/Windows/tmux scenes are original local interaction sketches. Label synthetic data as synthetic at all times.

## Integrate real data without inventing authority

Define a typed adapter contract before connecting a service. Validate payload sizes, finite numbers, units, stable IDs, sequence ordering and timestamp domains before mutating the model. Duplicate/stale data must not corrupt new state. Missing sensors are absent, not zero. Expired routes revert to configured baselines; keep stale status distinct from fresh measurements.

Sensor capture must be explicit and stoppable. Do not turn on a microphone, capture output, request motion data, read additional private files, persist transcripts or upload telemetry without the user's requested purpose and appropriate permission. Do not replace an inaccessible sensor with an unlabeled synthetic value. Avoid overlapping RAPL-domain sums or misleading channel labels.

Outbound agent commands require explicit transport ownership and acknowledgement semantics. Queueing a local message does not mean the provider received it. The application must own authentication, authorization, reconnects, retries, idempotency, approvals and acknowledgements. Treat agent/tool output and imported documents as untrusted data, not executable instructions.

The optional PTY skin is **not a sandbox**. It executes argv as the user. Preserve emulator cells, explicit colors, inverse selections, hidden text, cursor/mouse/paste protocols, wide characters and echo-disabled input. Do not predictively echo passwords, strip terminal control sequences with a regex, or allow raw clipboard/graphics escapes to bypass the chosen policy. The complete optional emulator integration was untested locally; run its required tests and application smoke tests before extending or relying on it.

## Test before implementing the change

Write new acceptance tests first. Include positive, negative and edge cases. At minimum cover immediate local ink at a held timestamp, 30/60 phase parity, independent data updates while paused, transition interruption, resize/empty/minimum bounds, selected/disabled hit regions, Unicode/input demultiplexing, invalid configuration, stale measurements, queue limits and terminal restoration after failure.

Run existing references unchanged. New expected snapshots require an explicit reviewed acceptance step; normal test execution must never bless its own output. For native code, include address/undefined-behavior sanitizers and cross-binding cases. For browser code, drive actual input/click/keyboard events against the self-contained gallery, not just private methods. For terminal code, exercise a real pseudo-terminal.

```sh
sh scripts/check_observatory.sh
python3 scripts/check_observatory_browser.py
python3 scripts/check_observatory_media.py
node scripts/benchmark_observatory.mjs
```

Before a verified release on a machine with required toolchains/dependencies:

```sh
npm install --ignore-scripts
npm --prefix integrations/pty install --ignore-scripts
REQUIRE_RUST=1 REQUIRE_PTY=1 sh scripts/check_observatory.sh
(cd bindings/rust && cargo test --all-targets)
```

Never delete or bypass `REQUIRE_RUST`/`REQUIRE_PTY` to make an unavailable test look green. Report missing tools and unexecuted hardware/provider/platform checks accurately. Review FFI size/alignment, signedness, pointer lifetime and owned-frame behavior even when Rust compilation is available.

## Deliver an application another person can continue

Provide full usable files, not unexplained diffs. Preserve naming conventions: PascalCase types, camelCase functions/variables, UPPER_SNAKE constants, with language-required exported-name conventions where appropriate. Public APIs need purpose, input/output units, failure behavior and examples. Comment non-obvious math, timing, clipping, protocol and ownership rules.

Deliver the archive, source tree, exact setup/run/test commands, configuration examples, real interactive demo, changelog, execution report, and integrity manifest. Include Git commit/branch identity and a continuation brief distinguishing shipped behavior, configured-but-unrun checks and future work. Do not claim a remote push, deployed app, published package, hardware capture or provider connection that did not happen.

Keep scope moving toward the requested user's workflows. A good extension should make a specific daily action easier, clearer and more delightful, not merely add another effect selector.

---

End of reusable handoff prompt.
