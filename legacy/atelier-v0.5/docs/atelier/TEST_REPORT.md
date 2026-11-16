# Spatial Atelier / executed verification

The implementation continues the verified v0.4 bundle at `9b6e40c`. Commit `0454849` records new acceptance contracts before implementation. Generated release identity records the final source commit and the gallery's source-build commit separately. No source fixture was accepted/replaced by normal tests. The aggregate passed before the final optional-shockwave default adjustment; all final new contracts, render tests, browser and PTY tests were then rerun. That adjustment does not touch the earlier native/reference paths.

## Executed in this Linux container

| Suite | Result |
|---|---|
| New graph/camera/text/particle/window/settings contracts | **73 tests passed**. Stable permutations, multiple parents, SCCs/rejection, node sizes/pins, bounded inputs, projection snapshots, scalar timing, exact text endpoints, interrupted/reversed effects, settings ownership/validation and local-content preservation. |
| New real-WASM render suite | **25 tests passed**, including all 18 scenes, every **198 window effect/mask pair**, 30/60 shared-time poses, actual control hit coverage, window recovery and caller body ownership. The 198 pairs are subcases, not 198 additional test methods. |
| Browser | **25 checks passed**, including visible default Hyperlane, actual look/strafe/drag/wheel/velocity buttons, input while held, cooperative 2D/3D layouts, pin/cycle handling, canvas chrome clicks, dock recovery, roll interpolation, depth, settings, viewport changes and all scenes. No browser exceptions or external requests. |
| New terminal host | **15 real POSIX PTY checks passed**: local input before a held 1 FPS tick, Alt camera movement, Ctrl+G action console, actual SGR brake click, layout responsiveness, resize, escape demultiplexing and exact termios/output-mode restoration. |
| Existing native Python suite | **63 test methods passed**. |
| Existing sensor/audio/broker/server Python suite | **18 tests passed**, using fixtures rather than physical devices. |
| Previous renderer/Studio/Fleet/native suites | All original reference and safety suites passed unchanged through `check_observatory.sh`. This includes original 55 frame references, 72 Studio references, 10 Fleet scenes and 96 opacity cases, 320 OKLCh references, Go tests and sanitizer-backed C cases. See retained raw logs for individual assertion units. |
| Previous browser/media/Fleet checks | Observatory **17 checks**, synthetic browser-audio **5 checks**, and Fleet **20 checks** passed again. No hardware audio was captured. |
| New aggregate command | `sh scripts/check_atelier.sh` exited **0**. The aggregate retains explicit unavailable-tool disclosures; it is not a substitute for required CI dependencies. |
| Embedding / CLI | Window-body embedding example and graph preprocessing CLI executed. Native widget cells were painted into a caller-owned projected window, with custom hit ID preservation. |

Raw results are under `dist/atelier/`: `contracts.txt`, `rendering-tests.txt`, `browser-tests.json`, `tty-tests.json`, `check-all.txt`, `legacy-check.txt`, and previous-browser/media logs. Earlier suite logs remain under `dist/studio`, `dist/fleet`, and `dist/observatory`.

Nova is ejecta-first: its shockwave is off by default and is explicitly optional. The new default has its own failing-before/fixed-after regression.

The Nova draw-order regression was first observed as a failing test (`nova-layer-before.txt`), then fixed: the core glyph is emitted after ejecta, so particles near the origin do not overwrite it.

## Bugs fixed during acceptance

- Projected window-body raster footprints overwrote the second row of chrome hit pads. Half-open footprint bounds now keep the two-row controls intact.
- Text-effect changes and show/hide reversals could snap; new transitions capture the currently sampled glyph positions/alpha.
- Roll body is now a real independent reversible tween, not an instant boolean geometry change.
- A faded or rolled surface could remain difficult to recover after dock activation. `restore` resets visibility, fade and body-roll intent while preserving content and placement.
- Rate changes after a backward seek now explicitly fork retained rate timelines, rather than discarding the user's speed edit.
- Visual settings import validates a fresh model and preserves local drafts, notes and editor buffers without serial-ID collisions.
- The named Hyperlane entry and direct camera/travel controls are exercised in the actual downloadable HTML, not only in private model tests.

## Performance and preview

`dist/atelier/performance.json` records warmed Node22/WASM model/render time and separate dirty-cell encoding for six scenes at 136×44 cells. Render medians are a few milliseconds in this environment; the exact measured numbers, percentile tails and derived bytes/second are retained. They exclude stdout, the destination terminal and physical display.

`performance-browser.json` measures actual cell rendering plus canvas rasterization in the Windows scene. Occasional samples exceed a 16.67 ms budget. The gallery targets 60 FPS; no promise of uninterrupted physical 60 FPS on a terminal or loaded browser is made. Geometry/timing correctness does not depend on displayed frame count.

The preview is encoded from **1,200 actual cell frames at 60 FPS (20 seconds)**. It contains explicit-time flight, graph movement, bursts, typography and window transformations. No image generator, shader blur or non-cell scene geometry embellishes the screenshots/video. Caption text is editorial. Font files are not included.

## Not executed / not claimed

**Rust:** cargo/rustc are unavailable. The new high-level code is TypeScript and changes no C ABI. The existing Rust façade/tests are retained, but local compilation is still NOT RUN. CI/release require `REQUIRE_RUST=1`; do not remove that gate.

**Optional headless PTY skin:** `@xterm/headless` was not installed; its full optional integration remains NOT RUN. The underlying Python PTY broker fixtures pass. CI requires `REQUIRE_PTY=1`. No Codex/Claude application compatibility test was performed.

**Live tmux, macOS, Windows native, physical sensors/audio, provider/AFD integration:** not exercised. Existing explicit, read-only/opt-in adapters remain separate from this offline gallery. No remote GitHub workflow was dispatched; no repository was pushed; no package was published.

**Portability:** new graph/layout/camera/text/particle/window models are TypeScript. Native C cells/widgets/OKLCh have the earlier four façades. This is not a claim of four native high-level implementations or a complete framework adapter suite.

## Reproduce

```sh
sh scripts/check_atelier.sh
python3 scripts/check_atelier_browser.py
node scripts/benchmark_atelier.mjs
python3 scripts/build_atelier_previews.py --video
```

With full dependencies installed, before a verified remote release:

```sh
REQUIRE_RUST=1 REQUIRE_PTY=1 sh scripts/check_atelier.sh
```

The packaging script verifies every ZIP entry against SHA-256 and rejects font assets. A separate extracted-archive verification is written beside the release after unpack/rebuild/tests and Git-bundle recovery. See `EXTRACTED-VERIFICATION.json` in the delivered release directory for those results; do not infer them from a manifest alone.
