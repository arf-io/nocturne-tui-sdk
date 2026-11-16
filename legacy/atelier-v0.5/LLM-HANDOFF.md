# Spatial Atelier: application-builder handoff / v0.5

Use this with the complete source SDK, not with screenshots alone. Build the requested application, preserve the existing history and tests, and deliver runnable code plus an interactive host. This is a source-checkout SDK. Do not claim a library is published or a service connected merely because an example exists.

## Application brief

Purpose and users: [fill in]. Host language/framework: [fill in]. Data sources/outbound actions and permission boundaries: [fill in]. Terminal/OS/tmux/SSH constraints: [fill in]. Motion/density/accessibility preferences: [fill in]. Acceptance workflow: [fill in]. Make minimal labelled assumptions; do not invent credentials or endpoints.

## Inspect before changing

Read `README.md`, `AGENTS.md`, `CHANGELOG.md`, `BUILD-IDENTITY.json`, `docs/atelier/API.md`, `CONTROLS.md`, `EXPERIENCE.md`, `TEST_REPORT.md`, and `atelier.schema.json`. Inspect `git status`, branch/log/remotes, most recent relevant remote work when connected, and uncommitted changes. Continue the included history rather than rebuilding from scratch. The runnable examples are `examples/atelier_embed.mjs`, `atelier_terminal.mjs`, `atelier_layout.mjs`; the browser host is `web/atelier.template.html`.

## API map

- `spatial.ts`: `layoutGraph`, `GraphLayoutJob`, `CameraRig`. Fixed-seed/fixed-iteration work; never solve graphs in a render callback. Up to 256 nodes/2048 edges. SCC handling must preserve original edges and shared child identity. Host controls job slicing/worker execution. Pins can defeat spacing; warn instead of silently discarding them.
- `text_fx.ts`: `sampleText`, `TextPlayer`, `textDuration`. Original text is separate from display substitution. Explicit time, separate show/hide, exact endpoints. `.configure(patch,time)` captures the current pose before changing effect. Local input remains full-opacity and immediate.
- `particles.ts`: seeded points/segments/glows; ember Y-down gravity; nova short core and ejecta; arcs rather than ripple-only sparks. Respect active-event budgets and reduced motion.
- `window_fx.ts`: `WindowManager`, masks and reversible geometry. Use stable window IDs and a permanent dock. `restore` reopens, unfolds and restores opacity. Projected planes are painter-ordered, not a solid depth-buffer engine.
- `atelier.ts`: host-neutral model/composer. `setWindowPainter(id,callback)` paints an owned body frame with application data and custom hit IDs >=100000. Parent framework owns the terminal. Numeric hit IDs are current-frame routes, not durable graph identities.
- `atelier_settings.ts`: visual import/export, strict validation before replacing the model. Use `.preserveLocalContent(previous)` when changing settings in a live local editor. Settings are not a conversation archive or complete timed replay.

These new high-level modules are **TypeScript**. C11/native/WASM cells, widgets, OKLCh and earlier effects have Rust/Python/Go/TypeScript façades. Do not claim native high-level ports exist. For another language, consume explicit preprocessed graph/scene data, port a bounded feature with conformance tests, or implement native application state. Do not hide a Node child process inside something advertised as a native library.

## Non-negotiable behavior

1. Input/data receipt mutates state and immediately presents at the current decorative timestamp, even when motion is held or FPS is 1. Local keystrokes never fade or wait for a growing panel. Display backpressure may replace an unpresented frame, not domain events.
2. FPS controls sampling, not speed. At the same time, 30/60 FPS produce the same animation pose. Rate edits integrate from current position; edits after seeking backward explicitly fork future rate changes.
3. The host alone owns raw mode, terminal output, clocks and transports. Embed cells into Ratatui/Textual/Bubble Tea/Ink or other parent buffers; no second ANSI writer inside a component.
4. Preserve OKLCh lightness/chroma/hue distinction and gamut mapping; do not revert to HSV for new hue sweeps. Subcell glyphs have one fg/bg pair, not arbitrary per-dot RGB. Unsupported wide/combining/control glyphs display safely; never mutate original text into its sanitized representation.
5. Visible camera actions, focus, dock and plain-text fallback are required. Motion and depth cannot make controls or errors unreachable. Do not equate color/animation alone with status.
6. Source data and output escape sequences are untrusted. Do not execute gallery notes. Hardware capture remains explicit/stoppable. Optional PTY runs the actual child as the operator; it is not a sandbox or a regex escape filter.
7. New effects need concrete bounds, units, defaults and schema/UI exposure. Update the control schema, documentation and examples alongside behavior. Distinguish genuinely required parameters from irrelevant controls.

## Test and deliver

Write new acceptance tests before implementation. Preserve old fixture hashes and bug regressions. Test actual canvas/cell controls and PTYs, not just private methods. Cover input while held, 30/60 timing equivalence, interrupted/reversed motion, masking/hit regions, zero/small viewports, invalid graph/settings, cycles/pins, UTF-8/control data, bounded events and cleanup on failure.

```sh
sh scripts/check_atelier.sh
python3 scripts/check_atelier_browser.py
node scripts/benchmark_atelier.mjs
```

On a machine with full toolchains/dependencies, CI must run:

```sh
REQUIRE_RUST=1 REQUIRE_PTY=1 sh scripts/check_atelier.sh
```

Do not remove the requirements to conceal missing tests. Record Rust/optional emulator/platform/hardware status accurately. Measure render, encode, bytes per second and host behavior separately; a fast renderer is not a physical 60 FPS guarantee.

Deliver all full files, archive, source tree/readable source, test evidence, instructions, changelog, integrity manifest and Git history. No font assets. Provide exact remote commands only for an explicit destination; no force push or invented publication claims. Explain limitations that affect use, without replacing implementation with a plan.

## Previous architecture and integrations

The retained `docs/observatory/LLM-HANDOFF-v0.4.md` covers sensors, audio routing, Fleet messages and the optional PTY bridge in additional detail. Its boundaries remain in force. Earlier galleries stay available; `START-HERE.html` is the Spatial Atelier entry point.
