# Observatory: embedding and ownership

## Choose the correct entry point

**Whole application in Node/TypeScript:** reuse `ObservatoryModel`, `ObservatoryRenderer`, `MotionClock`, `CellWriter`, and the event-loop pattern in `examples/observatory_terminal.mjs`. Run the included compiled host without npm or C compilation. Node 22/Linux was tested. A browser host using the same classes is `web/observatory.template.html`.

**A real AI fleet:** the existing `FleetModel` and `FleetController` remain the agent/domain layer. Use `examples/fleet_terminal.mjs --fps 60`, `docs/fleet/INTEGRATION.md`, and its explicit inbound/outbound descriptors. Observatory's chat scene is a local art/mockup model, not a replacement transport. Bridge validated sensor samples to visual options; do not translate decorative events into agent commands.

**Embedding in an existing TUI framework:** the host owns terminal modes, input, layout, focus, event loop, output and transport. Consume returned cells in the framework buffer. Do not print a second stream of independent ANSI into its screen. Native Python/Go/Rust integrations can use the existing Studio nodes, frames, compositor and the new OKLCh converter. The new 3D/sensor/controller implementation is TypeScript; a native application needs a model port or a bounded bridge to the TypeScript renderer. There is no claim of complete native Ratatui/Textual/Bubble Tea/Ink/OpenTUI adapters.

**Skinning an existing terminal process:** read `PTY.md`. This uses an emulator and a controlling PTY, not normal widget integration. It is optional and less verified than the main gallery.

## Run complete examples

From the extracted project root:

```sh
node examples/observatory_terminal.mjs --scene chat --fps 60
node examples/observatory_terminal.mjs --scene scope --palette pearl
node examples/observatory_terminal.mjs --scene windows --palette copper
node examples/observatory_terminal.mjs --scene dag --palette smart-dark
node examples/observatory_terminal.mjs --scene nano --no-demo
node examples/observatory_terminal.mjs --snapshot 4000 > /tmp/nocturne.ansi
node examples/observatory_embed.mjs > /tmp/observatory-frame.json
```

The supplied hosts do not execute typed drafts, access providers, or write files automatically. The last two commands redirect explicit outputs. Native rebuilds require a C11 compiler:

```sh
sh scripts/build.sh --wasm
tsc -p tsconfig.json
python3 scripts/build_observatory_gallery.py
python3 scripts/build_fleet_gallery.py
```

## The three clocks and the immediate path

Use one monotonic host clock and distinguish **presentation deadlines**, **motion time**, and **source/data time**. Source timestamps may be mapped into the host's monotonic domain when entering from another process. Keep their original source time separately when needed for analysis. Never subtract wall-clock timestamps from monotonic timestamps.

On local input, validate and update draft state synchronously, sample/hold the motion clock, render, and present. Do not put this path behind `requestAnimationFrame`, a 16.67 ms timeout, a debounce, or a transition promise. The browser still physically displays on its own compositor cycle; software cannot promise photons between display refreshes. The renderer promises no intentional decorative scheduling delay.

On a decorative deadline, evaluate motion at elapsed time. `fps` changes only `shouldPaint` cadence. 30 and 60 FPS must have equal animation phase at a common timestamp. The default is 60; controls permit 1..120. The writer coalesces only frames that have not yet been written when stdout applies backpressure. It never drops input or domain events.

Data heartbeats evaluate source envelopes and integrate changing velocities independently of presentation. `model.routeRates(dataMs)` samples those envelopes at explicit heartbeat times and updates velocity checkpoints at the current motion time. The demo uses 20 Hz data updates. Record these heartbeat timestamps along with measurements/configuration/input for reproducible reactive playback. Do not call `routeRates` as an accidental side effect of rendering.

## High-level API

`MotionClock(fps)`: `sample(wallMs)`, `shouldPaint(wallMs)`, `setFps(fps)`, `setPaused(paused,wallMs)`, `seek(timeMs,wallMs)`. Time is milliseconds. Backward monotonic samples reject. When pausing externally, synchronize the model to `clock.timeMs` before establishing a frozen baseline.

`ObservatoryModel`: `configure(patch)`, `resize(columns,rows)`, `setScene(id)`, `setTime(motionMs)`, `input(text)`, `replaceDraft(text)`, `backspace()`, `send()`, `receive(text)`, `emit(x,y,glyph,weatherKind)`, `ingest(sample)`, `ingestWaveform(row)`, `routeRates(dataMs)`, `toggleWindow(index,mode)`, `windowProgress(window)`, `windowAlpha(window)`, `exportState()`.

`ObservatoryRenderer(engine)`: `render(model)` returns `{frame,nodes,semantics,drawnStars,activeWeather}`; `renderSurface(model)` returns only the material plane for compositing below another renderer. Rendering does not mutate model state. Returned cell arrays are owned snapshots. Internal palette caches are implementation details.

`editScratch(model,action,value)` edits the mock editor buffer without command execution. Actions include insert, backspace, delete, left/right/up/down, home/end. Cursor offsets are UTF-16 offsets compatible with browser textarea selection; scalar-aware operations avoid splitting surrogate pairs. Full grapheme editing, CJK/emoji display, bidi and native IME editing remain outside the narrow cell renderer.

`activateObservatory(model,id)` dispatches only the supplied local demonstration actions. Stable positive IDs provide hit regions and companion semantic buttons. Treat returned actions as intentions in a production host; validate authorization in the application layer.

`projectPoint(point,camera,width,height)` projects XYZ through yaw/pitch/roll, near/far clipping and cell aspect. `flatNavigation` provides a 2D alternative. The sample graph has fixed coordinates and multiple parents; it is not an automatic graph-layout package or a full depth-buffered scene graph.

## Shared native colour APIs

```python
# Run after sh scripts/build.sh, with PYTHONPATH=bindings/python
from studio import oklchColor, oklchLightness
color = oklchColor(620, 1400, 285000)
print(f"#{color:06x}", oklchLightness(color))
```

Python `oklchColor`, Go `OklchColor`, Rust `studio::oklchColor`, and TypeScript `StudioEngine.oklch` share native code. L is integer 0..1000 (divide by 1000); C is 0..4000 (divide by 10000); hue is signed millidegrees. Invalid native arguments return -1; wrappers translate failures into their language's errors. The gamut mapper reduces C while holding requested L/h, then rounds encoded sRGB. It is not the CSS local-MINDE algorithm, nor a calibrated display/vision guarantee.

Studio text's additive `colorAnimation:3` selects OKLCh. For that mode only, `hueBrightness` maps to L/1000 and `hueSaturation` maps to C/2500; `hueBase` and `hueStep` are degrees and `hueSpeed` is degrees/second. Legacy modes 0..2 retain their original semantics and golden frames. Existing application colors are not silently migrated.

## Configuration and composition

`observatory.schema.json` is generated from executable constraints; `observatory.recipes.json` supplies 12 authored starting points. Numeric fields reject nonfinite and out-of-range values. `configure` validates a full candidate before committing. Palette editing accepts explicit hex colors; do not insert ANSI into text fields.

There are 49 numeric controls, four enum groups, four policy booleans, custom glyphs, palette stops and relative stop weights. The gradient distance is measured **between adjacent stops**, not across the entire palette. For `gradientScreens:2, stopWidths:[1,2,.5]`, successive distances are 2, 4 and 1 normalized screens. Missing weights are one. The palette closes from its last stop back to the first. Screen extent uses viewport-normalized X/Y; it is not a device-independent physical meter at arbitrary angles.

Primary and second-axis rates are degrees/second. Double-axis mode projects a rotating field, not a 3D texture shader. Offscreen pivots accept -3..4 screens. Pendulum mode follows its own specified cycle/swing with smooth turning points. No frame-number dependency changes its period.

Opacity is precomposition into RGB. A cell ultimately has one glyph and one foreground/background pair. Text over a half-block field flattens that cell's background samples. Braille offers eight coverage bits, not eight independently colored subpixels. Colored/higher-resolution output has a byte cost; see performance evidence before selecting transport limits.

## Error handling, budgets and persistence

Model draft: 4096 Unicode scalars; 256 retained messages; 128 events, with the last 24 active events drawn; 128 scalar sources, 128 waveform identities, 16 routes; 256 rate checkpoints; 32768 UTF-16 scratch units. Waveform input is 2..1024 finite samples; the scope retains 128 resampled values. Old samples are not converted to zero measurements. A stale route restores the configured baseline.

`exportState` is for inspection. It does not include sufficient mutable history/checkpoints for an arbitrary full-session restore. Full deterministic replay requires the same engine/version/viewport/palette, configuration and input events, source events, data heartbeats and initial checkpoint. The native color corpus is cross-language byte-equal; spatial floating-point composition is implemented in TypeScript and has not been proven bit-identical on every JS engine or CPU.

Native/WASM frame and widget APIs remain bounded and owned. UI compositors are single-thread owned: serialize mutations or use independent instances. No autonomous disk persistence, network, device access or telemetry occurs in the model.
