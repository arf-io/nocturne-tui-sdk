# Observatory v0.4: execution report

Source base: Pearl Fleet commit `34e8806`, preserved through the supplied Git history. Feature branch: `feature/vol4-observatory`. The first two commits recorded acceptance and transport/sensor contracts before the feature implementation. `BUILD-IDENTITY.json` and `RELEASE.json` identify the final packaged commit.

## Executed locally

| Area | Actual result |
|---|---|
| Python/native full source suite | **63 test methods passed**, including original/Studio/Fleet regression and three new OKLCh wrapper tests. |
| Python hardware/host abstractions | **18 methods passed**: five system-sensor fixtures, three audio-feature fixtures, five controlling-PTY broker tests, five loopback-server boundary tests. |
| Shared new color corpus | **320 accepted colors** matched through Python/native, Go/native and TypeScript/WASM, including resulting lightness. This is one corpus checked through three paths, not 960 different input cases. |
| New native color safety | **7,128 L/C/hue combinations** passed range and lightness checks under address/undefined-behavior sanitizers. Tolerance: resulting Oklab L within 5/1000 in that sweep. |
| Observatory contracts | **12 groups passed**, covering independent clocks, FPS phase, rate integration, spacing, projection, configuration, stale sensors, validation and immediate drafts. |
| Observatory rendering | **13 groups passed**, including 64 scene/viewport combinations, every numeric control endpoint and 720 palette/pattern combinations (48 × 15), plus ownership, purity, native paint, hit state, waveform/rate and local-text checks. |
| Lifecycle | **12 assertions passed** for paused reveal watermark, invalid-message atomicity, surrogate-safe scratch editing and source quality. |
| Browser Observatory | **17 checks passed**, including actual DOM input while motion is frozen, 30/60 control changes, stop spacing, commands, camera keys, all scenes/palettes/recipes, disabled state, selected cells, window movement, scratch editing, routing, bounds and no network requests/exceptions. |
| Browser media software | **5 checks passed** with a synthetic Web Audio oscillator: no capture on initialization, explicit capture, waveform plumbing, stopped tracks and failure on a source without audio. **No physical audio device was tested.** |
| Actual Observatory terminal host | **13 checks passed** in a POSIX PTY, including first local character while held at a 1 FPS ceiling, explicit sensor records, invalid-record recovery, mouse decoding, resize and terminal restoration. |
| Pure optional skin composition | **13 assertions passed**, including explicit colors, inverse/hidden cells, widths, control filtering, palette colors and underlined blank preservation. |
| Prior Fleet browser | **20 checks passed again** against the updated 60 FPS browser build. |
| Prior renderer references | Original **55**, Studio **72**, Fleet **10** complete canonical frames and **96** Fleet opacity cases passed unchanged. |
| Prior native safety | **16,665** geometry/material combinations; Studio **4,810** assertions over **2,400** randomized scenes; Fleet **3,150** opacity range/monotonic cases plus boundaries passed. |
| Go | Full package suite passed with the new shared color tests; CLI examples without tests were reported as such, not counted as tests. |
| Preview | **720 rendered cell frames**, 60 FPS, 12 seconds, six studies. Screenshots and movie are renderer output, not concept art. |

The method/group/assertion/subcase units above are different; they must not be added into a misleading single total. Tests do not automatically overwrite accepted color/frame references. Browser tests load the exact self-contained HTML bytes with Playwright `set_content` because this environment's managed file-URL policy is separate from application script behavior.

## Rendering and bandwidth measurements

Node 22/Linux, 136×44 cells, 10 warmup frames followed by 80 measured frames per scene. Across 16 default scenes, per-scene median model/render costs were approximately **1.26–1.62 ms**; p95 **1.50–2.19 ms**. Dirty ANSI encoding medians were about **0.06–0.08 ms**. These exclude writing to an actual terminal, its renderer and the physical display.

Estimated output at 60 FPS using those observed median dirty-frame sizes was approximately **0.63–1.14 MB/s**. Different effects, chroma modulation, larger viewports, frequent changes, glyphs, transport and terminal behavior can cost more. A sparse star surface and a constantly changing full-screen half-block gradient have very different budgets.

The browser's combined render/actual-cell raster test at the same size measured **5.7 ms median, 6.9 ms p95, and 34.3 ms maximum** over 80 warmed samples. The maximum shows occasional stalls; this is not a locked 60 FPS or zero-latency display claim. The movie records explicit timestamps offline and cannot establish real-time terminal throughput.

Raw measurements are `dist/observatory/performance-node.json`, `performance-node.txt`, and `performance-browser.json`. Changing FPS does not alter motion duration. Local edits call rendering immediately; the final display remains subject to the host's compositor, terminal, transport and backpressure.

## Bugs and validation issues addressed

Fleet previously lacked a usable persistent draft plane during the earliest part of workspace expansion. The new plane stays visible before a body layout becomes available. Local drafts have no reveal fade. Pause/resume retains already disclosed remote text.

Native color gamut handling keeps L/h fixed while reducing C; shared lookup tables and fixed-point operations avoid four divergent conversions. The new gradient phase is consistently measured in screens. Output/rate changes are integrated without resetting positions.

Browser data imports, samples and waveform records have explicit bounds. Invalid new messages do not advance reveal metadata. Native scratch editing avoids splitting surrogate pairs. Window dragging is confined to title regions. Measured scopes do not silently add a synthetic reference trace. Underlined blank emulator cells preserve their style instead of being replaced by a decorative glyph.

The initial browser test held the clock but did not synchronize the model before capturing its baseline; that test setup was corrected. A revision test also incorrectly assumed an empty constructor despite authored initial messages; it now checks a one-step increase from the observed pre-input revision. Neither correction weakens the immediate-input/time contract.

## NOT RUN or NOT CLAIMED

**Rust compile/test/doc execution:** Cargo/rustc unavailable. New scalar wrapper, shared 320-case corpus, examples and review are supplied. CI requires Rust and must fail on its absence.

**Complete optional terminal-emulator skin:** @xterm/headless could not be installed locally. Its nine emulator assertions are supplied; `REQUIRE_PTY=1` correctly exits nonzero when the dependency is missing. The broker and pure composition were tested, but this does not prove complete front-end or Codex/Claude compatibility.

**Physical audio, system-loopback audio, physical accelerometers, exposed host temperature/power channels:** unavailable or not exercised against hardware. System collectors were verified using filesystem fixtures and audio math using known values. No synthetic result is represented as a hardware reading.

**Live tmux, macOS, native Windows, other browsers, SSH links and real agent providers:** not exercised locally. Six new isolated profiles and the previous eight are included; actual tmux parsing is configured in CI. No AFD source integration was verified or existing AFD server modified.

**Remote CI/CD and publishing:** workflows were written/updated and YAML syntax checked, not dispatched. No repository push, provider connection, deployment, registry publication or external system configuration change occurred.

## Reproduce

```sh
sh scripts/check_observatory.sh
python3 scripts/check_observatory_browser.py
python3 scripts/check_observatory_media.py
python3 scripts/check_fleet_browser.py
node scripts/benchmark_observatory.mjs
```

On an environment with required toolchains and the explicitly installed optional emulator:

```sh
REQUIRE_RUST=1 REQUIRE_PTY=1 sh scripts/check_observatory.sh
```

The source release includes an integrity manifest, full source contents and Git history. Its final extracted-artifact verification is recorded separately in the release directory, not inferred from this working-checkout report.
