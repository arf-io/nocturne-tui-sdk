# Pearl Fleet / execution report

This report separates actual local execution from configured CI. The source baseline is the supplied Studio bundle at `3ff7d49`. A new feature branch preserves that history; commit `5148d5b` records the first Fleet acceptance contracts before implementation.

## Executed locally

| Suite | Result |
|---|---|
| Python/native, legacy + Studio + Fleet | **60 test methods passed**. Fleet includes 10 native scene hashes and 96 shared opacity cases. |
| TypeScript Fleet contracts | **15 passed**: data immediacy, validation, streaming timestamps, opacity, expansion/reversal, resize, history, drafts/outbox and error emphasis. |
| TypeScript Fleet robustness | **12 passed**: pause/resume ink, normalized event ownership, outbox capacity, external-source isolation, lifecycle, bounded retention, 32-agent paging, maximum viewport/fragmentation and control glyph handling. |
| Node input demultiplexer | **7 checks passed**, including split SGR mouse reports, keyboard escape sequences and split UTF-8. |
| TypeScript/WASM Fleet parity | **10 complete scene hashes and 96 opacity values passed**. |
| Go/native | Existing suite plus the same **10 Fleet scene hashes and 96 opacity values passed**; validation tests passed. |
| C opacity sanitizer test | **3,150 range/monotonic cases plus boundary assertions passed** under ASan/UBSan. |
| Prior material renderer parity | **55 original reference frames passed**. |
| Prior Studio parity | **72 reference frames plus 8 assertions passed**. |
| Prior native safety | **16,665 geometry/material combinations passed**; Studio added **4,810 assertions across 2,400 randomized scenes**, all passing. |
| Browser | **20 checks passed**, including all 48 palettes, actual cell clicks, accessible companion buttons, draft preservation, paused input/data, historical anchoring, reading mode, five viewport sizes and no external requests/browser exceptions. |
| New POSIX terminal host | **9 PTY checks passed** with an external NDJSON pipe and command sink: paused data, explicit outbound messages, SGR mouse selection, error recovery, exit and terminal restoration. |
| Prior Studio terminal host | Existing PTY regression passed, including data during paused motion and restored termios. |
| Preview | **360 actual cell frames, 30 FPS, 12 seconds** encoded successfully; no browser exceptions. |

Raw logs are in `dist/fleet/`, `dist/studio/`, `dist/python-tests.txt`, and `dist/go-tests.txt`. The 60 Python methods include the new native tests, so do not add them again when counting a total. Scalar boundary assertions, subcases and complete methods are different units; no inflated single grand-total claim is made.

The managed local Chromium policy blocks file:// navigation. Browser tests execute the exact self-contained HTML bytes with Playwright `set_content`; no server, external assets or network request is used. That is a script/interaction test of the artifact, not a claim that this sandbox's file URL policy was bypassed.

## Bugs found and fixed during this extension

Pause/read disclosure initially allowed new text to fade backwards on resume. A reveal watermark now keeps already-shown runs visible. Raw SGR mouse input initially escaped the generic keyboard parser and became draft text; a bounded demultiplexer now separates the channels. A worker-thread file read on a live pipe could prevent terminal shutdown; inherited pipe input now uses a nonblocking stream watcher. These cases have executed regression checks.

Oversized and highly fragmented transcripts retain text while falling back to bounded visual composition. Small workspaces omit metadata that would overflow their bounds. Event logs normalize validated scalar fields before commit, avoiding cyclic extra properties poisoning the replay record after a successful state mutation.

## Not executed here

**Rust compilation/tests/doc generation:** unavailable Cargo/rustc. Supplied: safe scalar wrapper, two wrapper unit tests, a 96-case scalar corpus, two complete frame fixtures and a runnable example. Reviewed in `RUST_REVIEW.md`; not falsely counted as executed.

**Remote GitHub Actions / release workflow:** configured but not dispatched. **macOS, Windows-native and live tmux:** not executed. **Real AI provider / AFD / shell-editor integration:** not implemented or claimed. The default fleet and preview telemetry are synthetic.

## Reproduce

```sh
sh scripts/check_fleet.sh
python3 scripts/check_fleet_browser.py
```

The first command builds and tests all previous and new components, including the terminal PTY. It reports missing Rust explicitly. In CI and before a verified release:

```sh
REQUIRE_RUST=1 sh scripts/check_fleet.sh
```

That command must fail if Rust is missing. Do not remove the requirement to turn an unverified build green. Browsers require Playwright/Chromium; preview generation additionally requires ffmpeg. Normal tests never run `scripts/accept_fleet_fixtures.mjs --accept` or overwrite accepted references.
