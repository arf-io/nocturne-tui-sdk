# Ratatui host

A Ratatui 0.29.0 adapter for Nocturne. It paints native frames into a Ratatui buffer and never advances the scene. Dependencies are pinned in `Cargo.toml`:

```toml
nocturne-native = { path = "../../bindings/rust" }
ratatui = "=0.29.0"
unicode-width = "=0.2.0"
```

## Contents

- `src/lib.rs` is the `SceneCells` widget. It draws an owned native `Frame` into the target buffer, clipping to the buffer and checking cell offsets.
- `UnicodeDocument` produces an owned `DocumentFrame` from the retained document and its bidi cluster layout. It paints whole clusters at native coordinates, clips wide clusters whole, and maps clicks back to source offsets. Scroll state belongs to the host. Selection ranges come from the application. Building and drawing a frame never changes the scene.
- `src/shortcuts.rs` maps Crossterm keys to native shortcut chords. F1 to F12 become 0x110001 to 0x11000c. Control and alt letters become the lowercase scalar plus modifier bits 2 and 4.
- `tests/` has the dependency-backed contract tests, which run against real Ratatui buffers and `TestBackend`.
- `examples/unicode_document.rs` is a terminal program for editing a document. `examples/qualification.rs` is a small full-screen fixture for the terminal tests; it is not an application.

## Run

```sh
cargo test --manifest-path native/hosts/ratatui/Cargo.toml
cargo run --manifest-path native/hosts/ratatui/Cargo.toml --example unicode_document -- --document-text=TEXT
```

Ctrl-Q exits. The example supports pointer placement and dragging, scrolling, bracketed paste and these options:

- `--info-on-exit=PATH` writes the scene info on exit.
- `--reserve-shortcut=Ctrl+q` reserves a key. The host picks another: Alt+q for Ctrl+q, with Help on F1 or F7 and Reader on F6 or F8. The option repeats, and the hint row shows the assigned keys. Ctrl+c stays the emergency exit.

Keys: arrows, Home, End, PageUp and PageDown move the caret, and Shift extends the selection. Vertical movement keeps its preferred column across shorter lines. The caret scrolls into view, and repainting an unchanged frame keeps a manual scroll. Alt-W copies the selection, Ctrl-W cuts and Ctrl-Y pastes through a buffer kept by the host, which is separate from the system clipboard. When a modal or the reader owns input, the example switches to the scene renderer and sends keys and the pointer to that owner. Ordinary text goes through native key commands, so an overlay cannot leak input into the draft.

## Terminal fixture

`examples/qualification.rs` turns on a controlling terminal, all-motion mouse input, bracketed paste and focus events. It translates key, paste, pointer and resize input into native commands and paints native frames through Ratatui. It has no provider and no network.

- `--hold` freezes the scene while input and painting continue. Time catch-up runs at most eight steps per loop turn.
- The viewport command is sent only when the dimensions change.
- `--trace NEW_FILE` writes a trace. Traces are limited to eight MiB, and the fixture exits after 20 seconds.
- Ctrl-Q and Ctrl-C exit. Ctrl-P toggles hold.
- `--failure error|panic|setup` injects a failure to test cleanup.

The fixture assumes a normal terminal at start: visible cursor, and no alternate screen, mouse, paste or focus modes active. On exit it restores the saved termios settings and turns off the modes it enabled. A SIGKILL, `panic=abort` or a broken output device does not restore the terminal.

## Terminal tests

`qualify.py` builds and tests the host offline and then runs six pseudo-terminal cases: held input, edit, paste, resize and Ctrl-Q; mouse and focus ownership; Ctrl-C; error cleanup; panic cleanup; and a failure part-way through startup. Each case waits for raw mode and a painted title before sending input. A case passes when the child exits with the expected status (0 for normal exits, 1 for error and startup failure, 101 for a panic), has drained its output, and has restored its termios settings and terminal modes itself.

```sh
python3 native/hosts/ratatui/qualify.py \
  --rust-bin /absolute/path/to/rust/bin \
  --target-dir /absolute/path/outside/sdk/ratatui-target \
  --evidence-dir /absolute/path/outside/sdk/ratatui-run-001 \
  --timeout 180
```

The target and evidence directories must be outside the SDK, and the evidence directory must be new for every run. The run needs a local Cargo registry cache or vendor directory with the exact pinned versions. It uses `--offline --locked` and never downloads. `--create-lock` lets it create `Cargo.lock` from the cache when there is none; an existing lock is never rewritten. Without a lock and without that option the run reports BLOCKED.

Exit codes: 0 pass, 2 fail, 3 blocked, 4 timeout, 130 interrupted. `QUALIFICATION.json` and the per-command logs show what ran. The pseudo-terminal checks run on Linux.

The harness has its own tests, which do not need Ratatui:

```sh
python3 native/hosts/ratatui/test_qualification.py
rustc --edition=2021 --test native/hosts/ratatui/examples/support/mod.rs -o /absolute/path/outside/sdk/support-tests
/absolute/path/outside/sdk/support-tests
```

Scene frames draw one scalar per cell. `UnicodeDocument` adds cluster layout and bidi for documents. Font shaping and input method editors are not supported.
