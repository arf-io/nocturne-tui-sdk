# Nocturne Studio / executed verification report

Build date: 2026-09-17. This records executed tests in the current Linux runtime, not remote CI status. Native C/Python/Go and TypeScript/WASM were run. Rust, tmux, macOS and an actual TD Figlet executable were unavailable and **not** counted as passes.

## Executed results

| Area | Evidence | Result |
|---|---|---|
| Python old + new | `dist/python-tests.txt` | **56 test methods pass**, including26original,17Studio,12integration,1reference corpus loop. |
| Legacy canonical frames | `dist/wasm-tests.json`, original Go/Python tests | **55 fixed reference frames retained**; original rendering behavior passes. |
| Studio parity | `tests/studio.fixtures.json`, `dist/studio/wasm-tests.json`, `dist/go-tests.txt` | **72 reference frames match** in Python/native,Go/native,TypeScript/WASM;8additional WASM assertions pass. |
| Legacy native safety | `dist/sanitizer-tests.txt` | **16,665 geometry/material combinations and boundary contracts pass** with ASan/UBSan. |
| Studio native safety | `dist/studio/sanitizers.txt` | **4,810 assertions across2,400randomized scenes pass** with ASan/UBSan, warnings-as-errors and nonrecovering sanitizer mode. |
| New browser gallery | `dist/studio/browser-tests.json` | **15scenes,48palettes**; input/value/feed redraw during pause; disabled buttons,DAGparents,modalEscape,keyboardchartinspection;0networkrequests,0pageerrors. |
| New POSIX host | `dist/studio/tty-tests.json` | Immediate data/prompt changes while paused;mouse sequence accepted;exit and termios restoration pass. |
| Legacy browser + POSIX host | `dist/browser-test-results.json`, `dist/tty-test-results.json` | Original interaction/resize/mobile-width and pause/cleanup regressions pass. |
| Node and Go snapshot examples | Executed `node examples/studio_node.mjs` and `go run ./cmd/studio` | Both complete successfully and emit ANSI frames. |
| tmux command construction | `tmux/preview.py --print-command` and adapter unit tests | Quoted separate-server command produced; status escaping/replay tested without starting tmux. |
| Structural export schema | Draft 2020-12 validator against all15 normalized gallery documents | All15validate; native validation remains authoritative for aggregate counts. |
| Original gallery bytes | SHA-256 comparison with original mounted gallery | Exact preserved copy under `legacy/Nocturne-Gallery-v0.1.html`. |
| Preview | `dist/studio/preview-record.json` |360explicit-time frames,12seconds,encoded30FPS,6actual-WASMcell scenes. This is not a throughput benchmark. |

## What the tests prove and do not prove

Reference images test byte-level canonical cell parity under the accepted cases, not all possible input combinations. All12patterns×4samplingmodes appear in the new corpus, plus14primitive cases,impulses,attention modes,long clocks and color quantization. Fixtures are fixed during ordinary tests; they are not silently regenerated to match new output.

Native sanitizer tests cover malformed geometry,limits,longtime arithmetic and random scenes. They are bounded automated tests, not a formal proof of memory safety. Bindings independently check sizes and owned output; Python's compositor additionally rejects malformed or aliased ctypes storage.

Browser checks used the full embedded HTML through Playwright `set_content`. The runtime's browser policy blocked local-file URL navigation; **direct file opening was not tested here**. The page made zero network requests and uses no fetched assets. File-open behavior in another browser can still depend on local security settings. The gallery is designed as one self-contained document.

Input/data commits are not intentionally gated by the decorative deadline. Tests hold motion time and observe changed frame/data state. They do not claim zero transport/display latency. A terminal, SSH link or blocking stdout can limit effective frame rate. No universal30FPS performance guarantee is made.

## Not run locally

- **Rust:** no cargo/rustc. SixStudio unit tests and72reference-frame integration cases supplied; source/FFI/build reviewed in `docs/RUST_REVIEW.md`. Native C success is not Rust compilation evidence.
- **Actual tmux:** no executable. Eight profiles and optional status scheduler supplied; `scripts/check_tmux.py` is configured in CI but not run locally.
- **Actual TD Figlet process:** no installed fork binary/fonts. ANSI parser,argv bounds/control removal tested; pinned-fork smoke job is optionalCI,not executed.
- **Native macOS/Windows:** current runtime isLinux. macOS CI configured; nativeWindows/Crosscompilation unsupported by bootstrap. Browser/Node WASM are separate targets,not a claim of universal runtime coverage.
- **Remote GitHub Actions/CD:** no remote repository created,PRopened,workflow dispatched or registry published. Workflows are source definitions.
- **AFD native plugin:** source inaccessible; status provider is an additive seam,not verified with AFD's actual scheduler API.

## Required verification commands

```sh
sh scripts/check_studio.sh
REQUIRE_RUST=1 sh scripts/check_studio.sh
python3 scripts/check_studio_browser.py
python3 scripts/check_browser.py
python3 scripts/check_studio_tty.py
python3 scripts/check_tty.py
python3 scripts/check_tmux.py
(cd bindings/rust && cargo test --all-targets && cargo doc --no-deps)
```

A release gate setsREQUIRE_RUST=1,so absence fails instead of silently skipping. The manual packaging workflow requires the core/binding suite before artifact upload; it does not publish a registry package or automatically deploy an application.

## Tool versions

- C compiler: `cc (Debian 14.2.0-19) 14.2.0`
- Clang: `clang version 17.0.0 (https://github.com/swiftlang/llvm-project.git 10999b6d034fe318f3d56c83bddb6572593a8bb0)`
- Go: `go version go1.23.2 linux/amd64`
- Node: `v22.16.0`
- TypeScript: `Version 5.8.3`
- Python: `3.13.5`
- OS: `Linux x86_64`

## Known integration gaps

Per-framework adapters,independently packaged registrypackages,actualAFD/fishhooks,fullUnicodegraphemeediting,hugeDAGlayout,realtelemetry/chatbackends,multi-tracktypographyeditor,nativeWindows/crossbuilds and automaticcapability/indexedSGRencoders remain explicit follow-on work. The delivered sourceSDK and interactive examples should not be represented as those integrations already completed.
