# 1.0.0

- Commands no longer copy the whole scene. Clock ticks, typing, pointer, widget and graph-node updates are planned against the live scene and then committed directly: about 0.003 to 0.03 ms each, down from about 3.5 ms. A rejected command still leaves the scene untouched.
- The Gallery reads the full scene state once per frame instead of four times.
- All 16 v0.1 prompt surfaces work and are in the Gallery, including the nine that were missing (Iris, Dusk Plasma, Chromatic Type, Quiet Machinery, Small Pocket, Pearl Signal, Split Light, Braille Field, Plasma 360). Each matches the original v0.1 kernel frame for frame. The Gallery now has 322 original works.
- `prompt-source` can be bound to a region, to the prompt, or to a widget, with separate foreground and background alpha and an optional frame. The rest of the scene renders around it.
- `environment.occlusionTint` and `environment.occludedDots` let you choose how particles hidden behind others look: background tint from 0 to 1, and hidden or merged dots.
- The Gallery can paint with WebGL (`?paint=webgl`); Canvas2D remains the default.
- Cursor and typing-weather settings in the Gallery apply as soon as they change.
- Saved scenes from older builds that hold a scheduled prompt-source command restore again.
- MIT license. Home: https://nocturne.arf.io and https://github.com/arf-io/nocturne-tui-sdk. Credits in `CREDITS.md`.

# 1.0.0-rc.5

- The Gallery shows original artwork. Each entry resolves to a file in the original Nocturne explorations (0.1 through 0.9). The shipped list, `native/contract/GALLERY-ADMISSION.json`, has 313 entries: 305 original works and 8 recipes built on ported original effects. Entries that were test fixtures, entries wrapped in an invented application frame and placeholder specimens are gone.
- Workshop panels open 17 labelled SDK examples.
- `weather/silver-squall` and `weather/snowglobe` are hidden from the Gallery and the catalogue pages. The core still accepts them. See `docs/current/Nullification.md`.
- `test_project_export_languages` exports the three ready-made Workshop projects and checks that WASM (Node), Python, Go and Rust draw byte-identical frames. The TypeScript entry point type-checks in strict mode.
- The example project for work units is now the neutral Work Graph example.
- Generated READMEs contain no host-specific instructions.

# 1.0.0-rc.4

- Hybrid sampling. Each object gets one sampling class: plots and weather use braille; floors, aggregate floor tiles, meshes, surface tiles and float bodies use half blocks. An object never mixes the two. A full braille mask is always U+28FF. The braille, half and cell policies are unchanged.
- Gallery pacing. The live loop drops its backlog instead of accumulating it, counts hidden time separately, reports how far the simulation is behind, and advances at a fixed budget of 24 steps per frame.
- WebAssembly memory routines use bulk memory (`memory.copy`, `memory.fill`) and a word-wise `memcmp`. A no-op core command in Chromium dropped from about 30 ms to about 6 ms. Results are byte-identical.
- Nullification contract: `native/contract/NULLIFICATION.json` lists effects, recipes and rendering outputs to hide. `apply_nullification.py` applies it to the Gallery, the HTTP bundle, the reference documentation and the packaging binding. It shows a plan by default; pass `--allow-removal` to withdraw a decision.

# 1.0.0-rc.3

- Tests import the repository root themselves, and the runner and CI set `PYTHONPATH`. Hard-coded macOS paths are gone. Generated TypeScript is written outside the source fingerprint. A leak in the LeakSanitizer harness is fixed, and coverage builds use clang.
- The first prompt follows the viewport up to the kernel's integer limits. The old 512x256 limit is gone, and a stack-buffer overflow past column 512 is fixed.
- Gallery attract mode shuffles every showcase recipe without immediate repeats and shows captions.
- The reference documentation covers all 111 catalogue components with their commands, parameters, defaults, domains and examples the library accepts and refuses (`docs/current/components.json`).
- Fixes: selector, condition and value language (restore checks style guards; character selector path grammar); status area and notifications (a consumed action keeps its hit ID, clipped content counts for the reader, the status tick runs before scheduled commands); lifecycle and end transitions (destructive endings complete; a drain stop after one begins is rejected); camera coordinate space (the grab is released at every press-time capture site, path-owned camera position is protected from pointer gestures, look and drag edit orientation during a commanded flight, a suspended flight stops when path travel is removed); braille coverage at every capture tick and family default.

# Unified RC3

- A real Python, TypeScript, Go and Rust framework host, each tested through a terminal.
- Versioned text and window sampler contracts and flight tests.
- Fixed DOM modifier alias drift at the shared host input boundary. Impossible frame geometry is rejected.
- Explicit OS and framework provisioning, locked test phases, full-resolution capture at every tick, byte and bit comparison, MP4 validation.

# 0.9.0-rc.2+input.1

- Graph actions are placed outside the node inspector footprint. Inspector keyboard buttons are separate from scene actions. Closing a nested modal restores the inspector context.
- Spatial pointer navigation is separate from opt-in keyboard navigation.
- Clicking no longer starts weather in the Gallery, Field Guide, terminal or session pointer command.
- Pointer intent, gesture displacement and wheel routing are shared across hosts.
- The Field Guide has drag, pan and wheel controls, including for imported sessions. Stale raw-component hit maps are cleared.
- Prompt selection, resize, explicit effects and typing weather behave as before.
- Browser and terminal interaction tests and model regression tests.

# 0.9.0-rc.2: Workbench

- Shared prompt document and alpha composition.
- A live Field Guide of 150 entries, generated examples and explicit installer profiles.
- Native and WASM discovery, atomic private draft recovery, and topmost modal fixes.
- The broker child resets inherited ignored interrupts.

# 0.9.0-rc.1: Continuity

- The v0.9 browser implementation as readable JavaScript, the v0.8 Git history, and the detailed-water and mesh ABI.
- Signed wheel, screen-relative manipulation, a shared caret, immutable insertion weather and gesture identity. Cruise direction survives view edits.
- Interruptible world-space graph focus and a 30-effect catalogue.
- Model navigation, wave freeze and highlights, a joined river lip, descriptive dock labels, current terminal, server, Git and tmux entry points, and runnable examples.
- Separate corpora of 50 native and 206 controller frames.
- A typed session API, a Rust test gate, documentation, CI and extracted-archive verification.

# 0.8: Restoration

- One depth-tested native and WASM World kernel for five scenic compositions.
- Rust, Python, Go and TypeScript World APIs and a full-scene Node bridge.
- Classic Nova and Sparks launch separately next to world weather.
- The Atelier source and gallery, and 18 text-effect families.
- The Gallery starts with demos and collapsed controls, and keeps scroll position on focus.
- Reserved graph inspector space, interpolated family focus, SHA-256 labels, preserved metadata and configurable type colors.
- Read-only Git history examples, isolated tmux profiles, a lab and a popup, wrapper scripts, conformance corpora and artifact verification.

# 0.7.0: Black Hole

- A stable fixed-sector starfield, distance exposure, cached projection and bounded world weather.
- Nova sphere, Firework and Ripple effects. Auto off and a world/classic switch.
- Analytic continuous, curved and orbital flight.
- Metadata workgraphs and local Git export.
- Window groups with gather, visit and summon. Scoped keys and reserved override validation.
- Typed form and formula state and modal styles.
- Procedural Black Hole, infinite, environmental and scenic studies. An optional GPU probe. Stage traces.
- Additive rendering hooks leave Kinetic defaults and the native C ABI unchanged.
- Fixed unbounded cruise, orbit entry roll continuity, truthy policy flags, nonfinite metadata and form and modal schema validation.

# 0.5.0: Kinetic Observatory

- A visible camera and travel deck, and the Oblique Hyperlane first screen.
- Six automatic graph layout modes with cycle reporting and pins.
- Sixteen entrances and sixteen exits for immutable text.
- Nova ejecta, branching arcs and rising and falling embers.
- Twenty-one reversible window choreographies, ten masks, large labelled chrome profiles and a restore dock. Shaped windows have inscribed content areas.
- Visual configuration export and import. A safe loopback server.
- Fixed backward-scrub rate editing, hidden maximized-from-minimized windows, Restore keeping maximized geometry, glyph brightness-zero leakage, ignored shape controls in the nonrectangular scene, and Pan mode rotating on a normal drag.
- The PTY broker test harness stops collecting stderr after a deadline.

# 0.4: Observatory

- A fixed-point OKLCh converter with chroma-reduction gamut mapping and cross-binding fixtures.
- TypeScript reactive and spatial materials, 49 controls, 16 interactive mockups, 12 recipes, 15 background styles and 32 modulation targets.
- Waveform, system and audio producers.
- Six isolated tmux profiles and an optional controlling-PTY broker and emulator skin.
- Full-opacity local input planes and time-based 60 FPS host defaults.
- Browser, transport, invalid-data, source-quality, color-safety and lifecycle tests.

# 0.3: Pearl Fleet

- A shared TypeScript Fleet model and controller with browser and POSIX Node hosts.
- Per-agent expansion and drafts, streaming arrival and horizon opacity, history anchoring and 32-agent paging.
- Explicit input and command descriptors, and Python and Go scene ingestion.
- A scalar opacity helper in all four bindings.
- Fixed pause and resume ink retraction, raw mouse reports entering drafts, and blocking pipe input hanging terminal exit.

# 0.2.0: Studio

- Event ripples and nova lifecycle, stable single-dot stars, 12 patterns, directional and radial focus, 48 palettes, 14 primitives and picking.
- 15 interactive mock scenes, scalar keyframes and pseudo-alpha.
- 8 tmux profiles, an AFD status seam and a bounded TD Figlet adapter.
- Four bindings, a reference corpus, CI definitions, documentation and source packaging.
- ABI v1 and the 26 original Python tests and 55 original frame fixtures are unchanged. The original gallery is under `legacy/`.
