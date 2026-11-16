# Experimental terminal-process skin

## What is implemented and what is not yet verified

The Python broker creates a controlling PTY, starts an explicit argv, forwards bytes, handles resize, returns exit status and reaps the child. Its tests ran against real local child processes, including echo-disabled input and interrupts.

The JavaScript front end uses **@xterm/headless 5.5.0**, then applies the material plane below default-background cells. The dependency could not be installed in the development container because network/toolchain access was unavailable. Its actual emulator integration tests are supplied and required by CI but **did not run locally**. Codex, Claude, shell editors and interactive applications were **not** tested through the complete skin. Do not call this universally compatible or production-hardened.

## Installation and explicit execution

From the extracted checkout, with network available:

```sh
npm --prefix integrations/pty install --ignore-scripts
REQUIRE_PTY=1 node tests/observatory/pty_headless.mjs
node integrations/pty/nocturne_skin.mjs --help
node integrations/pty/nocturne_skin.mjs --palette smart-dark -- /bin/bash
node integrations/pty/nocturne_skin.mjs --palette smart-dark -- codex
node integrations/pty/nocturne_skin.mjs --background warp --palette stellar -- claude
```

The child commands must already be installed and authenticated. Unlike the mockups, **this executes the actual argv as your user**. It is not a sandbox, authorization layer, approval mechanism, provider proxy or filesystem barrier. The wrapper itself does not authenticate to a service, but a child can use your existing credentials and perform its ordinary actions. Start with a harmless local shell before using workflows with consequences.

Run the same command inside a tmux pane. No existing tmux settings or AFD processes are modified. Tmux/native platform testing remains pending. The wrapper has a reserved `Ctrl+]` prefix: prefix then `q` exits, `p` holds motion, `t` changes palette, and doubled prefix sends a literal prefix to the child.

## Composition contract

The terminal emulator is the source of truth. Feed bytes into its parser and render in its write completion callback. Never strip a regex over arbitrary terminal output and call the result an emulator. Never parse prompts by guessed process names. Terminal cursor reports go back to the child, not into the draft composer.

Only default backgrounds receive the theme by default. Explicit child RGB/indexed colors, inverse selections and invisible text are preserved. A default blank cell can reveal half-block or braille material; text cells receive a flattened background. `--recolor-default-text` is an opt-in exception for recoloring otherwise-default text. There is no guarantee that a child using explicit backgrounds everywhere will show the material.

Input is forwarded without predictive echo. The child line discipline and application decide what appears, which preserves password input and application shortcuts. The broker never persists key logs or terminal transcripts. Bytes can still be seen by the running child and in memory, as in ordinary terminal use.

The renderer carries wide/combining-cell strings from the emulator, mirrors cursor/mouse/paste/focus modes, and attempts synchronized-output handling with a bounded watchdog. It coalesces unpresented visual frames under stdout pressure, not the child byte stream. A bounded parser backlog pauses upstream reads.

## Compatibility boundaries

This is a conservative initial skin, not a complete terminal emulator product. Test alternate screens, line wrapping, colors, escape replies, selection, Unicode, resizing, paste, mouse, shell editing and cleanup for each application before relying on it. OSC clipboard/title/hyperlink/graphics passthrough is intentionally not forwarded raw. Extended keyboard protocols, sixel/Kitty images, terminal palette queries/mutation, native scrollback UI, advanced underline variants and nested input mode corner cases need further compatibility work. Viewports are bounded to the Observatory range, which can be restrictive for tiny panes.

There is no automatic capture of audio, provider messages or shell commands from the wrapper. Sensor-driven skinning should be added through the same explicit validated source layer, not by sniffing secrets from the PTY stream.

## Tests

```sh
python3 -m unittest discover -s tests/observatory -p 'test_pty_broker.py' -v
node tests/observatory/skin_core.mjs
REQUIRE_PTY=1 node tests/observatory/pty_headless.mjs
```

The first two ran locally. The third intentionally fails without its dependency. Keeping it required in CI avoids mistaking an absent emulator test for passing compatibility.
