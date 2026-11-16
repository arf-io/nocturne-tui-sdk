# Nocturne Spatial Atelier / Volume V

**Direct camera controls. Automatic graphs. Explosive weather. Reversible typography. Recoverable spatial windows.**

Open **`START-HERE.html`** or **`Nocturne-Spatial-Atelier.html`**. The first scene is explicitly named **Oblique Hyperlane**. The page displays **v0.5** plus its source-build ID. Earlier HTML files are earlier experiences; opening an old filename does not update it.

The standalone gallery embeds its modules and WASM. No server, network, fonts, account or installation is required. Typed notes are local and are never executed. Example agents/readings are synthetic. The original Observatory sensor and optional PTY tools remain separate, with their prior permission/verification boundaries.

## Pilot the scene

The always-visible pilot console separates **look/orbit**, **move**, and **starfield travel**. Drag the canvas to turn; Shift-drag to strafe. Wheel translates forward/back; Shift-wheel zooms. The full-sized arrow buttons provide the same actions. Home resets the view; Frame all fits the graph. Look turns in place; orbit turns around the target. Camera motion does not automatically steer flight.

The signed velocity slider, heading and elevation fields are immediately visible. Brake sets speed to zero; Reverse reverses velocity; Aim along view copies the camera direction once; Reset flight restores Oblique Hyperlane. Exact XYZ, angles and field of view are also available in the camera panel. These controls operate while decorative motion is paused.

In Windows, drag a window body to move that window. Alt-drag rotates the workspace instead. Shift-drag empty space pans. Independent window depth/yaw/pitch/roll controls are in the Windows panel. The dock restores minimized, closed, faded or rolled-up windows without erasing their content.

## Run in a terminal

The compiled host requires Node.js 22 and a POSIX terminal. No npm packages are required to run the supplied JS/WASM.

```sh
node examples/atelier_terminal.mjs --scene warp --fps 60
node examples/atelier_terminal.mjs --scene dag --layout layered --dimensions 3
node examples/atelier_terminal.mjs --scene windows --palette copper
node examples/atelier_terminal.mjs --scene text --palette pearl
```

**Ctrl+G opens a named, clickable action console.** Alt-arrows look; Alt-W/S move forward/back; Alt-A/D strafe; Alt-Q/E roll; Alt-H resets; Alt-Space brakes. Ctrl+P pauses only motion. Ctrl+N changes scenes. Ctrl+R reveals text, Ctrl+U conceals it, Ctrl+E changes the text effect, Ctrl+O changes the window effect, Ctrl+B triggers a nova, Ctrl+L changes graph dimensionality and arranges it, Ctrl+Q exits. The Node host restores terminal modes and does not execute notes.

```sh
# Standalone graph preprocessing. No terminal required.
node examples/atelier_layout.mjs graph.json 3 layered > arranged.json

# Complete application-window embedding example; emits a real ANSI snapshot.
node examples/atelier_embed.mjs

# A specific time sample, without entering an interactive terminal.
node examples/atelier_terminal.mjs --scene warp --snapshot 2200
```

## What's added

- **3 bounded layout algorithms in 2D or 3D:** layered, force, radial. Shared node identities, multiple parents, node pins, size-aware layered spacing, stable seeds, fixed solver steps, SCC cycle disclosure/rejection and JSON interchange. Up to 256 nodes / 2,048 edges. Force/radial do not guarantee nonoverlap or minimum crossings.
- **18 text families, each with show/hide:** instant, fade, rain, scramble, flipboard, directional sweeps, lift, fall, marquee, iris, constellation, prism weave, ink tide, comet stitch, orbit, fold and zipper. Every accepted parameter is exposed. Local drafts never pass through these effects.
- **Weather:** hot-core nova ejecta, branching electrical arcs, upward-then-downward glittering embers, plus rain/snow/ripples. Independent lifespan, count, velocity, gravity, drag, branches, cadence, core and shockwave controls.
- **22 window transformations and 9 masks:** corner/center/circle, rolls, drawers, bounce, genie-to-dock, explode, accordion, origami, vortex, ribbon-unspool, petal-bloom and gravity-well. Full source-space 6×2 control pads by default; mac/windows/gnome/custom placement, glyphs and colors. Permanent dock; independent visibility, opacity, maximize and body-roll tweens.
- **18 playable scenes, 48 palettes**, existing OKLCh material controls, visual settings import/export and a six-study Motion Cabinet. The updated spatial menu uses the same camera. Native C/widget/color APIs and previous SDK versions remain present.

## Timing and integration

Input mutates the model and presents immediately at the current motion timestamp, even at a held 1 FPS ceiling. Decorative animation targets 60 FPS using elapsed time. A shared timestamp gives the same animation pose at 30 or 60 FPS. Output backpressure may coalesce pending visual frames, not application events.

The **new high-level modules are TypeScript**, not four independently ported implementations. C11/native/WASM still provides common cells, widgets, OKLCh and composition with Rust/Python/Go/TypeScript façades. Use `docs/atelier/API.md` and `examples/atelier_embed.mjs` to embed. Parent TUI frameworks own their terminal; copy cells into their buffers, never start a second writer in a widget.

```text
bindings/typescript/
  spatial.ts            Layout jobs, graph identity, camera and projection
  text_fx.ts            Pure text sampling and reversible text players
  particles.ts          Seeded points, segments and glow envelopes
  window_fx.ts          Window state, geometry, masks and chrome
  atelier.ts            Working composition and host interaction
  atelier_settings.ts   Validated visual settings interchange
  cell_profile.ts       Explicit one-cell display profile
examples/               Interactive terminal, layout CLI, embedding example
web/                    Actual self-contained gallery template
scripts/                Build, checks, previews, benchmark, packaging
atelier.schema.json     Generated defaults, ranges, enums and bounds
docs/atelier/           API, controls, experience, execution report
```

## Build and test

```sh
sh scripts/build.sh --wasm
tsc -p tsconfig.json
node scripts/build_atelier_schema.mjs
python3 scripts/build_atelier_gallery.py
sh scripts/check_atelier.sh
python3 scripts/check_atelier_browser.py
node scripts/benchmark_atelier.mjs
```

Build prerequisites: C11 compiler, Clang/wasm-ld, Python, Node22/TypeScript, Go. Native Rust needs cargo/rustc. The browser check needs Playwright/Chromium; `CHROMIUM_PATH` can select its executable. Preview video additionally needs ffmpeg. Source builds do not require downloading fonts.

For a verified CI release, missing dependencies must fail, not be treated as passes:

```sh
npm install --ignore-scripts
npm --prefix integrations/pty install --ignore-scripts
REQUIRE_RUST=1 REQUIRE_PTY=1 sh scripts/check_atelier.sh
```

The local execution report explicitly records Rust and the optional headless PTY dependency as unavailable. No remote CI run, live tmux, hardware/provider connection, registry publish or platform-wide 60 FPS guarantee is claimed.

## Continue the Git history

The included bundle continues v0.4 at `9b6e40c`, with a test-first branch at `0454849`. Do not initialize another repository over the history.

```sh
git clone git/nocturne-spatial-atelier.bundle ../nocturne-checkout
git -C ../nocturne-checkout switch feature/vol5-spatial-atelier
```

`sh scripts/continue_git.sh YOUR_GITHUB_OWNER YOUR_REPOSITORY` prints/checks the intended destination, attaches that existing repository to a separate `publish` remote, pushes the feature branch, and opens a PR using `gh`. Run only after choosing/creating that destination and authenticating. It does not create or guess an account.

After packaging, `python3 scripts/verify_atelier_release.py release.zip /tmp/new-atelier-check` verifies every checksum, safely extracts, rebuilds, reruns tests and recovers the Git bundle. The destination must be unused.

See `LLM-HANDOFF.md` for a complete implementation handoff, `docs/atelier/CONTROLS.md` for every control, and `docs/atelier/TEST_REPORT.md` for executed and unexecuted checks.
