# Nocturne / Pearl Fleet — Volume III

**Interactive fleet deck → maximized agent workspace → streaming text with soft-horizon fading.**

Open `Nocturne-Pearl-Fleet.html`, or run:

```sh
node examples/fleet_terminal.mjs --palette smart-dark
```

The delivered browser/Node build runs without installing dependencies. Rebuild from source with `sh scripts/build.sh --wasm`, `tsc -p tsconfig.json`, and `python3 scripts/build_fleet_gallery.py`.

Read `docs/fleet/EXPERIENCE.md` for behavior, `docs/fleet/INTEGRATION.md` for embedding and real data adapters, and `docs/fleet/TEST_REPORT.md` for executed results. Run `sh scripts/check_fleet.sh`; CI requires Rust. Live browser tests: `python3 scripts/check_fleet_browser.py` (Playwright/Chromium required).

The default fleet is synthetic. No agents, shell commands, tmux settings or remote repositories are touched. The source SDK retains the previous Studio and its 48 palettes. The high-level Fleet controller is TypeScript; normalized scenes and primitive opacity are shared through C/Python/Go/Rust/TypeScript. Rust source is reviewed but not compiled locally.

## Continue the Git history

The release includes a Git bundle. Preserve its history instead of initializing over it:

```sh
git clone git/nocturne-pearl-fleet.bundle nocturne-work
cd nocturne-work
git switch feature/vol3-pearl-fleet
```

After choosing your private repository destination, these Bash commands set the remote, push the feature branch and open a PR. Nothing was pushed by this delivery:

```sh
read -r -p 'Git repository SSH/HTTPS URL: ' REPO_URL
read -r -p 'PR base branch: ' BASE_BRANCH
git remote set-url origin "$REPO_URL"
git push -u origin feature/vol3-pearl-fleet
gh pr create --base "$BASE_BRANCH" --head feature/vol3-pearl-fleet \
  --title 'Pearl Fleet: animated workspaces and transcript ink' \
  --body-file docs/fleet/PR_BODY.md
```

Future edits should use a new branch, test before implementation, and commit full source:

```sh
git switch -c feature/pearl-next
sh scripts/check_fleet.sh
git add --all
git commit -m "Extend Pearl Fleet with verified behavior"
git push -u origin feature/pearl-next
```

---

# Nocturne Studio / Volume II

**Terminal surfaces as moving art. A source SDK, an interactive studio, and a shared integer cell renderer.**

12 field patterns · 14 drawing primitives · 48 named palettes · 15 playable compositions · 8 tmux profiles.

Open **`Nocturne-Studio.html`** in a desktop browser. It contains the renderer, WASM, palettes and scenes; no server or network is needed. Download/open the file outside an attachment preview that disables scripts. The browser renders the same cell records as the native terminal host, not a shader approximation. No fonts are included.

## Play first

**Starwrite:** type into the prompt to emit ripples at the inserted characters. Click empty space for a ripple; shift-click or use **Nova** for a burst. Choose your own ordinary/nova glyphs. Ordinary stars retain their glyph while fading. **Row current / Column current / Centricity:** move the focus between rows, columns and radial centers. **Pivot room:** move the axis offscreen, reverse rotation, or choose eased pendulum motion. **Controls / Charts / Fleet:** tab or click through enabled items; inspect samples and multiple parents. Open the glass modal and adjust its opacity. Pause motion and type or change a value: data is not gated by the motion clock.

The browser's mock feed is explicitly synthetic. No buttons issue commands, change fleet infrastructure or call providers.

## Run in a terminal

Requires native POSIX Python 3.10+ and a C11 compiler. From this project root:

```sh
sh scripts/build.sh
python3 examples/studio_terminal.py --scene starwrite --palette smart-dark
python3 examples/studio_terminal.py --scene fleet --palette copper
```

`Ctrl+Q` quit; `Ctrl+N` next composition; `Ctrl+T` next palette; `Ctrl+P` pause; `Ctrl+R` nova; `Ctrl+O` modal; `Ctrl+F` mock feed; `Ctrl+L` clear. Tab/arrows navigate; Enter inspects; Escape closes; mouse clicks hit-test. The input is an **inert demo prompt, not a shell**. Bracketed paste is treated as text. The host restores its terminal modes on normal exit and handled signals.

```sh
# One frame without an interactive event loop:
python3 examples/studio_terminal.py --scene charts --snapshot-ms 2500

# Optional: a SEPARATE tmux server, without sourcing your existing configuration:
python3 tmux/preview.py --profile smart-dark --scene starwrite
```

A theme does not add an animated background to an arbitrary existing shell or application. This demo owns its pane. Actual shell prompt redraw integration is not included. See [tmux integration](docs/TMUX.md) before connecting a status writer to AFD.

## Use the library

The shared core remains C11, with **additive Studio ABI v2**. Legacy ABI v1, its tests and original gallery are retained. Native Python/Go/Rust and TypeScript/WASM use the same renderer. Applications own terminal mode, layout, events, focus, I/O and scheduling; the SDK returns owned cell frames.

```sh
PYTHONPATH=bindings/python python3 - <<'PYCODE'
from studio import Studio, Node, Impulse
from terminal import AnsiWriter
studio = Studio(width=80, height=24, pattern=3, focusMode=1, focusY=12*256)
node = Node('progress', 5, 12, 65, 2, id=7, value=670, colorAnimation=2)
frame = studio.render(2500, nodes=[node], events=[Impulse(20, 12, atMs=1700)])
print(AnsiWriter().encode(frame), end='', flush=True)
PYCODE
```

This is a **source-checkout SDK**, not four independently installable registry packages. Keep the repository's source/schema layout intact. Python loads the sibling shared library; Go and Rust build the sibling C source; TypeScript accepts supplied WASM bytes. Full runnable host examples exist for all four languages:

```sh
node examples/studio_node.mjs
(cd bindings/go && go run ./cmd/studio)
(cd bindings/rust && cargo run --example studio)
```

The Rust command is supplied for your environment. **Rust was statically reviewed but was not compiled here because rustc/cargo were unavailable.** CI is configured to require it. Do not treat configured CI as an executed remote pass.

Read [API](docs/STUDIO_API.md), [embedding and complete examples](docs/INTEGRATION.md), [typography](docs/TYPOGRAPHY.md), [36 user stories](docs/USER_STORIES.md), [Rust review](docs/RUST_REVIEW.md), and [execution report](docs/TEST_REPORT_STUDIO.md). `AGENTS.md` is the agent handoff.

## Test / build / gallery

```sh
# C, Python, Go, Node, TypeScript compiler, Clang and wasm-ld:
sh scripts/check_studio.sh

# For a release gate, Rust must exist and pass:
REQUIRE_RUST=1 sh scripts/check_studio.sh

# Optional browser test dependency; not needed to USE the gallery:
python3 -m pip install playwright
python3 -m playwright install chromium
# Set CHROMIUM_PATH to that installation's browser executable when needed.
python3 scripts/check_studio_browser.py

# Optional actual tmux profile parser test:
python3 scripts/check_tmux.py

python3 scripts/package_studio.py --output /tmp/nocturne-release
```

`make` targets: `build`, `gallery`, `test`, `browser`, `demo`, `tmux`. No normal test regenerates reference fixtures. `.github/workflows/test.yml` defines Linux + native macOS checks and an optional pinned-fork TDF smoke test. `release.yml` runs required native/WASM checks and creates an artifact on manual dispatch; it does not publish packages or mutate a release.

## Deliberate limits

- 30 FPS is the **decorative target**, not a guarantee for every terminal, surface size, SSH link or palette. A data event renders immediately using the last sampled motion time. Transport/backpressure and physical presentation still exist.
- Single-cell glyph profile, not a general Unicode editor. Unsupported glyphs become `?`; no general grapheme/CJK/emoji/bidi layout.
- One glyph and two RGB colors per cell. Braille dots share one foreground. Text over a half-block flattens its two background samples. Pseudo-alpha is an RGB composition policy, not terminal/window transparency.
- The 16/256-color modes quantize the resulting RGB values. The supplied ANSI writers still use true-color SGR; automatic capability negotiation and indexed escape encoders are not implemented.
- No native Ratatui/Textual/Bubble Tea/Ink adapters are claimed. The four bindings and embedding contracts are provided; framework-specific ownership must be integrated in the host.
- Demo layouts and the five-node DAG are bounded compositions, not a general arbitrarily large graph layout engine. Real telemetry, chat transports, knowledge indexes and agent actions are host responsibilities.
- AFD native plugin compatibility and actual TD Figlet process execution were not verified locally. The adapters are additive seams with tests for their own contracts.
- Native Linux tested here; macOS and Rust checks configured, not executed here. Windows native console host, prebuilt universal binaries, cross compilation and registry publication are not delivered.

## Repository map

```text
nocturne-surfaces/
├── Nocturne-Studio.html             Standalone playable gallery
├── legacy/                         Exact original v1 gallery
├── include/                        C ABI v1 + additive Studio v2
├── src/                            Shared integer materials/widgets
├── bindings/{python,go,rust,typescript}/
├── examples/                       Four language hosts + interactive POSIX host
├── integrations/                   AFD status seam + bounded TD Figlet bridge
├── tmux/profiles/                   Eight explicit theme profiles
├── studio.schema.json              54 material fields, units and ranges
├── scene.jsonschema.json           Export-envelope structural schema
├── component-catalog.json          Machine-readable primitive metadata
├── palettes.json                   48 palette profiles
├── studio.scenes.json              15 example scene graphs
├── tests/                          Legacy + Studio acceptance and fixtures
├── scripts/                        Build, CI, replay, gallery, packaging
├── docs/                           Embedding, stories, limits, evidence
└── dist/                           Built WASM/JS and executed test evidence
```

## Continue on Git

The delivery has a local `main` baseline and `feature/vol2-interactive-studio` history, plus a Git bundle. No remote repository was created or modified. Use the bundle to preserve that history:

```sh
git clone nocturne-studio.bundle nocturne-studio
cd nocturne-studio
git switch feature/vol2-interactive-studio
git log --oneline --decorate --all

# Choose the owner you control. These commands perform remote writes only when YOU run them.
OWNER=your-github-user-or-organization
gh repo create "$OWNER/nocturne-surfaces" --private --source=. --remote=origin
git push -u origin main
git push -u origin feature/vol2-interactive-studio
gh pr create --base main --head feature/vol2-interactive-studio \
  --title 'Nocturne Studio: interactive material and component library' \
  --body-file docs/PR_BODY.md
```

When starting from the ZIP alone, the bundle is preferred for history. Otherwise initialize without inventing prior commits:

```sh
git init -b main
git add .
git commit -m 'Import Nocturne Studio source delivery'
git switch -c feature/studio-integration
```

No third-party font assets are redistributed. The repository does not choose a new open-source license on your behalf; establish the desired license before public distribution.
