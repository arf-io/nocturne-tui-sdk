# Nocturne Observatory / Volume IV

**Immediate ink, OKLCh materials, 60 FPS time sampling, reactive scopes and navigable space.**

Open `Nocturne-Observatory.html` in a desktop browser, or run:

```sh
node examples/observatory_terminal.mjs --scene chat --fps 60
node examples/observatory_terminal.mjs --scene warp --palette stellar
node examples/fleet_terminal.mjs --agent atlas --fps 60
```

The self-contained browser file needs no installation/server/network. Actual browser media capture requires explicit permission and a supported environment. The bundled Node/WASM host needs Node 22; native Python/Go/Rust usage needs a C compiler. The main terminal hosts were tested on Linux/POSIX. They are **local studies**, not shells. Typed text is never executed by the gallery/Observatory host.

## What is here

16 new interactive spaces, 15 background patterns, 49 numeric controls, 48 palettes, 12 authored recipes, six weather families and 32 scalar modulation targets. Warp flight uses independent XYZ camera orientation and travel direction. Graph nodes retain shared-parent identity and have a flat-navigation fallback. Windows expand/collapse/fade and can be title-dragged in the browser. Menus, controls, source labels, disabled selections, semantic companion buttons and command palettes support keyboard/pointer inspection.

The prior Studio component library and Pearl Fleet remain. Fleet's updated browser and terminal hosts default to 60 FPS, and its draft plane stays visible before/during workspace expansion. Old native reference frames pass unchanged; legacy hue modes remain compatible. New Observatory color sweeps use the shared OKLCh converter.

Try the **Oblique hyperlane**, **Pearl signal**, **Gold glass**, and **Winterfall** recipes. Hold motion and type: input commits immediately, including between decorative frames. The movie in `dist/observatory/` is a 60 FPS recording of actual cells at explicit timestamps, not proof that every terminal transport sustains 60 FPS.

## Read and embed

- [Integration, API and ownership](docs/observatory/INTEGRATION.md)
- [All controls and units](docs/observatory/CONTROLS.md)
- [Audio/system sensors and routes](docs/observatory/SENSORS.md)
- [Optional PTY skin and its verification limits](docs/observatory/PTY.md)
- [LLM application-builder handoff](LLM-HANDOFF.md)
- [Actual test results](docs/observatory/TEST_REPORT.md)
- [Rust source review](docs/observatory/RUST_REVIEW.md)

The source SDK is not a published package set or a finished adapter suite for all TUI frameworks. C/native/WASM color/widget/composition APIs are shared by Rust/Python/Go/TypeScript. The new high-level Observatory controller, XYZ materials and sensor mapping are TypeScript. Its original BBS/Lynx/Pico/Nano/tmux/Windows scenes are interactive local mockups, not the named programs.

## Hardware and PTY opt-in

```sh
python3 scripts/serve_observatory.py --port 8765
# Open http://127.0.0.1:8765 and explicitly connect the sensor feed.

python3 tmux/observatory_preview.py --profile smart-dark --scene scope

# Optional real-command wrapper; read PTY.md first. This is NOT a sandbox.
npm --prefix integrations/pty install --ignore-scripts
REQUIRE_PTY=1 node tests/observatory/pty_headless.mjs
node integrations/pty/nocturne_skin.mjs --palette smart-dark -- /bin/bash
```

The broker and pure skin policy were tested. The complete @xterm/headless front end, actual Codex/Claude compatibility, physical audio/accelerometers, live tmux and macOS were **not tested locally**. Rust source/tests are supplied and required in CI, but the Rust toolchain was unavailable here. Missing sensor channels are absent, not synthetic replacements.

## Rebuild and test

```sh
sh scripts/check_observatory.sh
python3 scripts/check_observatory_browser.py
python3 scripts/check_observatory_media.py
node scripts/benchmark_observatory.mjs
python3 scripts/build_observatory_previews.py --video
```

`REQUIRE_RUST=1 REQUIRE_PTY=1 sh scripts/check_observatory.sh` is the verified-release gate on a machine with those dependencies. Never weaken it to conceal a missing test. Browser checks need Playwright/Chromium; previews additionally need Pillow/ffmpeg. Source reference acceptance is separate from normal test execution.

## Git continuation

The bundle in a source release preserves the original baseline and test-first feature commits. Clone it rather than rebuilding repository history:

```sh
git clone git/nocturne-observatory.bundle ../nocturne-work
cd ../nocturne-work
git switch feature/vol4-observatory
git switch -c feature/my-application
# Implement with tests, then:
git add .
git commit -m "feat: implement application using Nocturne"
```

A remote was not created or modified by this delivery. To create a new private repository, replace `OWNER/REPOSITORY` once, then publish the verified baseline and feature separately:

```sh
gh repo create OWNER/REPOSITORY --private --source . --remote github
git push github feature/vol4-observatory:main
git push -u github feature/my-application
gh pr create --repo OWNER/REPOSITORY --base main --head feature/my-application \
  --title "Application built with Nocturne" \
  --body "See the included execution report, integration documentation and acceptance tests."
```

No font files are distributed. TheDraw interoperability from Studio remains an optional local-executable/cell-art import, not an included font corpus. Read all test reports before presenting an unexecuted integration as verified.
