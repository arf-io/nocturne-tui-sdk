# Terminal hosts

A host connects Nocturne to a terminal framework. It owns input, time and the terminal. The C core owns the scene. Each host reads native cells and paints them, and it turns key, mouse, paste, focus and resize events into native commands.

| Host | Framework | Language | Directory |
|---|---|---|---|
| prompt_toolkit | prompt_toolkit 3.0.52 | Python | `python/` |
| Terminal Kit | Terminal Kit 3.1.4, wcwidth 1.0.1 | JavaScript (Node, WASM core) | `terminal-kit/` |
| Bubble Tea | Bubble Tea 1.3.4 | Go (cgo) | `bubbletea/` |
| Ratatui | Ratatui 0.29.0, unicode-width 0.2.0 | Rust | `ratatui/` |

Build the native library first with `sh build-native.sh`. Run every command below from the SDK root.

## Run a host

```sh
python3 native/hosts/python/prompt_toolkit_host.py --scene autumn
node native/hosts/terminal-kit/host.mjs
(cd native/hosts/bubbletea && go run .)
cargo run --manifest-path native/hosts/ratatui/Cargo.toml --example unicode_document -- --document-text=TEXT
```

Terminal Kit and Bubble Tea need their dependencies installed first: `npm ci` in `native/hosts/terminal-kit`, and a Go module cache for Bubble Tea. Ratatui builds with `cargo`. The Terminal Kit host runs the C core as import-free WebAssembly in Node.

Ctrl-Q quits and Ctrl-C is the emergency exit. The Ratatui host in `ratatui/` is a presentation adapter (`SceneCells`, `UnicodeDocument`) plus two example programs.

## Keys

Shift with the arrow, Home and End keys extends the selection. Alt-W copies, Ctrl-W cuts and Ctrl-Y pastes through a buffer kept by the host. It is separate from the operating-system clipboard. Quit, Hold, Scene, Copy, Cut, Paste, Help and Reader are managed shortcuts. Each has a preferred key and a fallback, and the visible hint row shows the keys in use.

Reserve a key you want to keep for your own use, and the host picks the fallback:

```sh
python3 native/hosts/python/prompt_toolkit_host.py --reserve-shortcut Ctrl+q --reserve-shortcut F2
```

This selects Alt+q and F3. If every key for an action is reserved, the action has no key and the hint row says `unassigned`. Other hosts take the same option: `--reserve-shortcut=ctrl+q` (Bubble Tea, Ratatui example) and `--reserve-shortcut CTRL_Q` (Terminal Kit).

## Display

The hosts show one scalar per cell. A scalar the terminal cannot show at one cell width is drawn as a visible replacement, and the document in the scene keeps the original text. The `--unicode-document` view of the Python and Bubble Tea hosts and the Ratatui `UnicodeDocument` widget lay out whole grapheme clusters and bidirectional text from the native document.

## Tests

Each host has unit tests and a pseudo-terminal test that starts the real program, waits for raw mode, sends keys, and checks the exit status and the restored terminal settings. The pseudo-terminal tests run on Linux.

```sh
python3 native/scripts/qualify_dependency_hosts.py \
  --target-dir /new/external/hosts-target --evidence-dir /new/external/hosts-run
```

The runner builds and tests each host that has its dependencies installed, and it runs them independently. Both directories must be new. It installs nothing and writes no source files. Exit codes: 0 pass, 2 fail, 3 blocked by a missing dependency, 4 timeout, 130 interrupted.

For Go, set `GOPROXY=off GOFLAGS=-mod=readonly GOSUMDB=off GOTOOLCHAIN=local` with `GOMODCACHE` and `GOCACHE` pointing at directories outside the SDK. Node finds `node_modules` in an ancestor directory.

See the README in each host directory for its own commands.
