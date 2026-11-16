# Terminal Kit host

A Terminal Kit 3.1.4 application (with wcwidth 1.0.1) that runs the C core as import-free WebAssembly in Node. Terminal Kit owns the terminal and a `ScreenBufferHD` holds the cells. Node is this host's runtime. No Python, Go or Rust binding starts a Node process. `host.mjs` runs directly. The functions it exports are test helpers, not part of the SDK interface.

## Run and test

```sh
sh build-native.sh
(cd native/hosts/terminal-kit && npm ci)
node native/hosts/terminal-kit/host.mjs
node --test native/hosts/terminal-kit/host.test.mjs
python3 native/scripts/check_dependency_hosts.py --host terminal-kit \
  --evidence-dir /new/external/terminal-kit-pty --timeout 20
```

`npm ci` installs the exact versions in `package-lock.json`. To keep dependencies out of the SDK, put `node_modules` in an ancestor directory; Node finds it by its normal lookup. The terminal checker starts the host in a real Linux pseudo-terminal. `native/scripts/qualify_dependency_hosts.py` runs the build, the Node tests and the pseudo-terminal cases together (see `../README.md`).

## Keys and input

Ctrl-Q quits and Ctrl-C is the emergency exit. Quit, Hold, Help and Reader are managed shortcuts. Reserve a key and the host picks the fallback:

```sh
node native/hosts/terminal-kit/host.mjs --reserve-shortcut CTRL_Q --reserve-shortcut F1
```

This selects ALT_Q and F7. If both keys of an action are reserved, the action has no key. A bottom row shows the keys in use, and the scene uses the remaining rows (a one-row terminal keeps one row of content). The key map in `shortcut-profile.mjs` normalizes F1 to F12 to 0x110001 to 0x11000c, and control and alt letters to the lowercase Unicode letter plus modifier bits 2 and 4.

- Bracketed paste is parsed apart from Terminal Kit's key parser. Delimiters and UTF-8 can arrive in fragments, and the parser holds at most 64 KiB of pending paste. Line feed and tab stay data. A control character the native text contract rejects (a pasted U+0011, for example) produces a native error, exit status 1 and the earlier text intact. It does not act as Ctrl-Q.
- Terminal Kit's `grabInput(false)` leaves SGR mouse mode 1006 on. The host restores SGR mouse, paste, focus, cursor, screen and raw mode itself, and keeps cleaning up when one write fails.
- Mouse drag events become native move events and keep the left or right button. Losing focus cancels native hover and capture without a click.
- Errors, an uncaught exception in a callback, an unhandled rejection and a failure during startup all restore the terminal before the program exits with a failure status.
- Shift with the arrows, Home and End selects text. Alt-W copies, Ctrl-W cuts and Ctrl-Y pastes through a buffer kept by the host.

## Tests

Six Node tests check `ScreenBufferHD` cell ownership, that the WASM snapshot is not changed by painting, the paste parser, pointer handling and validation errors. Eleven pseudo-terminal cases run the real program: Ctrl-Q and Ctrl-C quit, advancing time, held editing with Unicode, paste and resize, click, hover, focus and both camera drags, a rejected control paste, a native error, a callback exception, an unhandled rejection and a failure during startup. Each case waits for raw mode and output, then for the exit, and passes when the child exits with the expected status and has restored its own termios settings and terminal modes.

The host draws one scalar per cell. It does not do grapheme shaping, bidi or input method editors. The pseudo-terminal checks run on Linux.
