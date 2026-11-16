# Nocturne / prompting surfaces

**A working terminal-material sketchbook: sixteen studies, one cell renderer.**

Dark Black Creme, pastel stars, fast focus bands, slow surrounding currents, full-turn plasma, chromatic letters, braille signals, and small luminous controls.

## Start with the art

Open **`Nocturne-Gallery.html`** in a desktop browser. It is self-contained: the renderer, WebAssembly, configuration, and studies are embedded. It makes no network requests. No server or installation is needed. If an attachment viewer shows source or refuses scripts, save the file and open it directly in a browser.

The gallery includes an animated hero, sixteen live studies, material controls, an explicit timeline, editable palettes, and JSON import/export. `dist/Nocturne-Studies.mp4` is a 12-second 30 FPS recording of the actual renderer. The two PNG contact sheets are static samples, not animation substitutes.

**Prove the scheduling rule:** choose **Controls / quiet machinery**, pause motion, and type in the input, move the live-value slider, or enable the independent data feed. Text, values, and selection update while the motion timestamp remains held. Decorative movement targets 30 FPS; input/data events do not wait for that clock. Actual physical presentation still depends on the browser/terminal and output transport.

This is a material kernel and working showcase, not a finished Ratatui/Textual/Bubble Tea/Ink adapter suite or a full text editor. The component compositions demonstrate what the materials can do. Their complete generic widget APIs and framework-specific integration are next-stage work.

## Studies

| ID | Study | Treatment |
|---|---|---|
| `black-creme` | Black Creme / stardust | Sparse mixed braille, punctuation, and mathematical stars. |
| `lavender-hush` | Lavender hush | Denser braille dust, lavender/blue peaks, long twinkles. |
| `sage-embers` | Sage embers | Sage/oat/shell peaks, quick attacks, lingering fades. |
| `liquid-linen` | Focus / liquid linen | Fast two-color active row, exponential neighboring falloff. |
| `diagonal-silk` | Diagonal silk | Configurable oblique gradient with independent row clocks. |
| `tidepool` | Wave / tidepool | Distorted liquid field; text remains stationary. |
| `iris` | Rotation / iris | Rotating field with two vertical color samples per cell. |
| `dusk-plasma` | Plasma / dusk | Four interacting sine fields and a closed palette. |
| `nebula` | Nebula / layered sky | Low-brightness plasma under coordinate-anchored stars. |
| `chromatic-type` | Demoscene / chromatic type | Per-character hue increments and a moving half-block ribbon. |
| `quiet-machinery` | Controls / quiet machinery | Borders, menu, selection, bars, braille scope, prompt, cursor. |
| `small-pocket` | Modal / small pocket | Chromatic modal over a dimmed background. |
| `pearl-signal` | Scope / pearl signal | Synthetic dual signals sampled into braille cells. |
| `split-light` | Split light / vertical | Left-half blocks combine two horizontal color samples. |
| `braille-field` | Braille / interference | Eight-sample ordered-dither material in each braille cell. |
| `plasma-360` | Plasma 360 / pearlescence | Three RGB sine channels, phase-separated by 120 degrees. |

The graphs are deliberately synthetic demonstration signals. They are not a general time-series ingestion API.

## Palette and motion

“Dark Black Creme” is interpreted here as warm near-black **`#11100E`**. Text is **`#D6CCBC`**. Initial star peaks are:

`#B6A4C4` dusty lilac · `#9FB9B0` sage · `#C7BCA7` oat · `#9CACCA` slate blue · `#C6A0AA` shell rose · `#ADBDBB` pearl teal.

These are peak colors, not constant star brightness. Individual cells get independent deterministic phases, cycle lengths, attack/fade envelopes, glyphs, and palette choices. No global synchronized blink. World-coordinate hashing means growing a raw surface reveals more sky without reseeding existing stars. Re-centering an automatically positioned prompt can move its overlay during resize; that is separate from the underlying star field.

For row distance `d` from focus, defaults are:

- Speed: `speed0 × 0.5^d`; equivalently period `period0 × 2^d`.
- Saturation: `saturation0 × 0.62^d`.
- Brightness: `brightness0 × 0.86^d`.

Each falloff is independently configurable. Focus is symmetric above/below. Full-background studies disable row focus unless `promptBands=1`. Integer falloff and capped periods are documented in `docs/DESIGN.md`.

Hue text follows a configurable degree step per character and an independent degrees-per-second temporal rotation. Negative values reverse either progression.

## Run in a terminal

The interactive host requires a **POSIX terminal, Python 3.10+, a C11 compiler, and true-color output**. No Python packages are needed. Run from the extracted project root:

```sh
sh scripts/build.sh
python3 examples/terminal_demo.py --preset black-creme
```

More studies:

```sh
python3 examples/terminal_demo.py --preset tidepool
python3 examples/terminal_demo.py --preset quiet-machinery --feed
python3 examples/terminal_demo.py --preset plasma-360
python3 examples/terminal_demo.py --config my-exported-material.json
```

The supplied Linux shared library is a convenience, not a universal native binary. Run the build step on your own architecture. `build.sh` produces a `.dylib` on macOS. The macOS build path is provided but was not executed in this Linux environment. The interactive Python demo does not support Windows console APIs; use the browser gallery there.

**Keys:** Ctrl+N next study; Ctrl+P pause/resume; Ctrl+O modal; Ctrl+F independent synthetic data feed; Ctrl+L clear input; Ctrl+Q quit. Up/down changes the menu selection. Normal typing edits the demonstration prompt; it does not execute commands. Input is bounded to 512 code points. The host restores tty settings, cursor, and alternate screen on normal exit and handled signals.

`--sync` opts into CSI 2026 synchronized output; it is off by default and should only be used with supporting terminals. `--fps 30` controls motion scheduling, not data commits. `--snapshot 6000` emits one explicit-time ANSI frame without taking over the terminal.

## Use the material kernel

The portable prototype has one **integer C11 core**, not four independent renderers. Python uses ctypes; Go uses cgo; Rust includes a safe façade over the same C ABI; TypeScript uses the same C compiled to WebAssembly. The earlier proposed Rust-core architecture is not what this prototype implements.

No binding owns a terminal, wall clock, event loop, or keyboard. Outputs are row-major cells: a glyph, foreground RGB, background RGB, reserved flags. The host schedules motion and commits data. Frames returned by the language bindings are owned snapshots, not aliases of later output.

### Python

```sh
PYTHONPATH=bindings/python python3 - <<'PY'
from nocturne import Surface
from terminal import AnsiWriter

surface = Surface(width=84, height=28, layout=1, effect=5, stars=1)
surface.setStarPalette(['#B6A4C4', '#9FB9B0', '#C7BCA7'])
writer = AnsiWriter()
motionMs = 6000
print(writer.encode(surface.render(motionMs, text='data arrives now')), end='', flush=True)
# A data-only update uses the same motion sample and is not held for a tick.
print(writer.encode(surface.render(motionMs, text='updated immediately')), end='', flush=True)
PY
```

### TypeScript / Node

The TypeScript source, declarations, compiled JS, and WASM are included. The binding does not require a browser or Node-specific APIs. The supplied host example uses Node file loading:

```sh
node examples/node_snapshot.mjs
```

Use `NocturneEngine.create(wasmBytes, schema)`, `engine.defaults(overrides)`, and `engine.render(config, motionMs, text)`. Rendering returns cells. `toAnsi(frame)` is a simple complete-frame encoder for standalone hosts; framework integrations should consume cells directly. The Python host also demonstrates dirty-run encoding.

### Go

```sh
cd bindings/go
go test ./...
go run ./cmd/snapshot
```

The cgo package compiles the shared C sources into the Go build. No preinstalled shared library is required. Exported methods follow Go visibility conventions: `NewSurface`, `Set`, `SetPalette`, `SetStarPalette`, `SetGlyphs`, `Render`.

### Rust

```sh
cd bindings/rust
cargo test
cargo run --example snapshot
```

**The Rust façade is provided as source but was not compiled or tested here: rustc/cargo were unavailable.** Its build script targets native POSIX hosts and requires `cc` and `ar`. Do not treat it as verified or as a cross-compilation solution. The supplied CI workflow includes Rust compilation/tests but has not been run remotely.

## Configuration

`schema.json` is the authoritative description of **49 integer parameters**, defaults, and ranges. Palettes and custom glyph arrays are additional configuration. Percentage-like parameters use thousandths: `500` is 50%. Timings use integer milliseconds; angles use degrees. Array palettes accept one to eight RGB colors. Custom stars accept up to 32 single-code-point glyphs within the demo glyph profile.

Important groups:

- Dimensions/origin: `width`, `height`, `originX`, `originY`, `cellAspectPermille`; current bounds are 512 columns by 256 rows, including empty surfaces for composition tests.
- Stars: `seed`, `densityPermille`, `glyphSet`, periods, duty cycle, attack, floor, peak, star palette.
- Fields: `effect`, `colorMode`, period, scale, angle, phase, wave amplitude, saturation, brightness, grain, gradient palette.
- Focus: `focusRow`, three independent neighboring falloffs, `promptBands`.
- Chromatic controls: per-character hue step, temporal hue speed, base hue, hue saturation/brightness, border style, cursor mode, selection, value, modal state, text scrim.

Effects: `0 solid / 1 linear / 2 diagonal / 3 wave / 4 rotation / 5 plasma`.

Compositions: `0 raw material / 1 prompt / 2 controls / 3 chromatic ribbon / 4 synthetic scope`.

Cell sampling: `0 whole cell / 1 upper half / 2 left half / 3 shade / 4 braille`.

`motion=0` evaluates the material at time zero. **Host pause is different:** retain the current timestamp and keep rendering new data against it. The supplied gallery and terminal host implement that distinction.

See `docs/CONFIGURATION.md` for every parameter. The gallery exposes common controls directly and all parameters through editable JSON. Configuration can be exported into the Python host.

## Rendering limitations

This release deliberately uses a narrow single-cell glyph profile: ASCII, selected punctuation/math marks, box drawing, block elements, and braille. Unsupported/wide/control characters become `?`. It does not implement general grapheme segmentation, CJK layout, emoji, bidirectional editing, full accessibility semantics, or a terminal capability/fallback negotiator.

One terminal cell has one glyph with one foreground/background pair. Two half-block color samples are possible, but arbitrary text cannot retain both independent half-block samples in the same cell. This renderer averages that background when applying a text/star overlay. Braille dots share one foreground color per cell; they are not eight independent RGB pixels. Internal blends are emitted as RGB, not terminal transparency.

The browser is a cell-accurate material preview, not a terminal font emulator. Font metrics and glyph shapes can differ on the destination terminal. No browser shader, glow, or blur is used to embellish the material output.

## Tests and measurements

Run with C11, Clang/wasm-ld, Python, TypeScript `tsc`, Node, and Go installed:

```sh
sh scripts/check.sh
```

`check.sh` explicitly reports Rust as NOT RUN if cargo is absent. CI installs Rust and exercises it. No fixture updates occur during normal tests.

Optional host tests and preview regeneration require Playwright and Chromium; recording also requires ffmpeg:

```sh
python3 scripts/check_browser.py
python3 scripts/check_tty.py
python3 scripts/benchmark.py
python3 scripts/build_previews.py
```

Set `CHROMIUM_PATH` when Chromium is not `/usr/bin/chromium`. Exact execution status is in `docs/TEST_REPORT.md`; raw logs and measurements are in `dist/`. Native and WASM output matches across **55 SHA-256 reference frames**, also checked through Go. Python includes 26 test methods. Sanitizers exercise 16,665 geometry/material combinations and boundary cases. Browser and pseudo-tty tests verify live data during paused motion.

At 84×28 in this runtime, per-study median render cost including Python allocation ranged from about 0.04 to 2.03 ms; ANSI diff encoding cost is separately recorded. These measurements exclude terminal writes and physical display latency. Color-dense half-block backgrounds can generate substantially more output than sparse stars.

## Project map

```text
nocturne-surfaces/
  Nocturne-Gallery.html         Self-contained playable gallery
  README.md
  schema.json / presets.json   Validated controls and sixteen studies
  include/nocturne.h           Versioned C ABI
  src/                        One deterministic renderer, WASM shim, lookup tables
  bindings/
    python/                   ctypes surface and event/motion output helpers
    go/                       cgo package, reference tests, snapshot command
    rust/                     Safe façade and snapshot example; not verified here
    typescript/               Typed WASM engine and standalone ANSI helper
  examples/                   Actual terminal gallery and Node snapshot host
  web/                        Editable gallery source
  tests/                      Unit, parity, scheduler, sanitizer fixtures
  scripts/                    Builds, tests, generation, benchmark, recording
  docs/                       Design contract, config reference, test report
  dist/                       WASM, compiled JS/types, previews, test evidence
  .github/workflows/test.yml   CI definition, not executed remotely
  SOURCE-CONTENTS.md           Complete readable source bundle
  SHA256SUMS.txt               Per-file integrity manifest
```

## Initialize a private repository and open a PR

No remote repository was created or modified. Run these from the extracted root after configuring git identity and authenticating `gh`:

```sh
git init -b main
git commit --allow-empty -m "Initialize Nocturne"
git switch -c feat/prompting-surfaces
git add .
git commit -m "Add deterministic prompting surface studies"
gh repo create nocturne-surfaces --private --source=. --remote=origin
git push -u origin main
git push -u origin feat/prompting-surfaces
gh pr create --base main --head feat/prompting-surfaces \
  --title "Add prompting surface studies" \
  --body "Sixteen animated cell-material studies; shared native/WASM renderer; tests and gallery. Review Rust CI before considering that binding verified."
```

No public distribution license was selected for this private prototype.
