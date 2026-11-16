# Spatial Atelier additions

Start with `README.md`, `LLM-HANDOFF.md`, `docs/atelier/API.md`, `docs/atelier/CONTROLS.md` and the actual source/tests. New high-level APIs are TypeScript. Run `scripts/check_atelier.sh`; do not remove required Rust/PTY CI gates. Preserve previous galleries/references. The source starts from v0.4 commit `9b6e40c` and test-first commit `0454849`.

# Nocturne Observatory: agent entry point

Read `LLM-HANDOFF.md` and `docs/observatory/INTEGRATION.md` before modifying this source. Start from `feature/vol4-observatory` or the newest relevant actual remote branch, not a recreated template.

Current invariants: local text bypasses fades; input presents independently of motion deadlines; 60 FPS does not change animation durations; source/data heartbeats are independent of presentation; OKLCh is the new color path; native legacy fixtures remain stable; capture/command execution is explicit; a PTY is not a sandbox; unavailable tests are NOT RUN, never PASS. Do not package fonts or dependency caches.

Required verified CI command: `REQUIRE_RUST=1 REQUIRE_PTY=1 sh scripts/check_observatory.sh`. Browser tests are separate. Full source, tests, docs, manifest and an honest execution report must accompany changes.

## Historical project instructions (apply unless superseded above)

# Nocturne Studio / agent handoff

Use this checkout as source of truth. Preserve legacy ABI v1 and accepted frames. Do not create independent render algorithms in each language or migrate the kernel just to match an earlier proposal.

Read README, docs/STUDIO_API.md, docs/TEST_REPORT_STUDIO.md and docs/RUST_REVIEW.md. Inspect `git status --short` and branch; delivered work is on feature/vol3-pearl-fleet. Read `docs/fleet/INTEGRATION.md`, `docs/fleet/TEST_REPORT.md` and `docs/fleet/EXPERIENCE.md`. Run `sh scripts/check_fleet.sh`; releases require `REQUIRE_RUST=1`. Open Nocturne-Studio.html or run examples/studio_terminal.py.

## Invariants

- Core has no hidden clock, I/O, threads, random source or actions. Decoration targets30FPS; data commits at the last sampled motion time immediately.
- Same inputs/version -> same canonical cells, not a universal pixel screenshot across different terminal fonts.
- Node order is z-order; positive IDs are semantic/hit-test identity, zero decorative. Disabled interactive regions block hits underneath. Never execute prompt text.
- Q8 values are cells×256. Percent/opacity/falloff fields use thousandths. Angle units vary by key: read the schema.
- One glyph/two colors per cell. Unsupported Unicode is not a general editor. Text-over-half-block backgrounds flatten; alpha is resolved before output.
- Chart target data must stay authoritative while decorative transitions run. Do not delay data to complete an animation.
- Test before new behavior. No ordinary test overwrites fixtures. `freeze_studio_fixtures.py --accept-new-reference` is an explicit review action that updates generated Go/Rust fixtures too.
- AFD is an unverified integration seam until source/API inspection. Never co-run competing status writers. Fonts remain external.

## Machine-readable contracts

studio.schema.json:54 material field specs; scene.jsonschema.json:structural export envelope; component-catalog.json:14 primitives; palettes.json:48 themes; studio.scenes.json:15 mock scenes; tests/studio.fixtures.json:72 accepted frames. Structural JSON validation does not replace native aggregate-count/geometry/range checks.

## Delivery

Run old and new checks, distinguish local executions from configured CI, rebuild the gallery after WASM/TypeScript changes. Include source/archive/manifest and honest report. No font files, remote mutations, shell hook installation, registry publishing or AFD overwrite without user authorization.

## Pending, not silently completed

Real AFD plugin hookup; safe fish redraw lifecycle; actual TD Figlet process compatibility; indexed-color encoders/capability negotiation; publishable independent packages; framework adapters; full Unicode/grapheme input; arbitrary-large-DAG layout; real fleet/chat/knowledge backends; multi-track typography editor; Windows native/cross-platform matrix.

## Fleet invariants

The high-level model/controller is TypeScript, shared by browser and Node terminal hosts. Native Python/Go load normalized Fleet scenes; all four bindings expose the same opacity helper. Do not claim four independent Fleet applications. Source sequence numbers are per agent. New data never waits for motion. Pause/read reveals must not fade backward on resume. Keep agent-local drafts and history anchors. Never interpret mouse reports as typed text; use TerminalInputRouter. Inherited pipes must use nonblocking stream I/O so exit does not wait for an open producer. Commands are intents, not ACKs. Preserve old ABI and all accepted scene corpora.
