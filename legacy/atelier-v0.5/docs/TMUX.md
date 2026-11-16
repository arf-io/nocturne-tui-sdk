# tmux, shell prompts, and AFD

Eight explicit profiles: smart-dark,black-creme,neon-dreams,molten-lava,copper,gold,millennial-gray,winter. They style status, windows, panes, messages and selection. None starts a daemon.

```sh
sh scripts/build.sh
python3 tmux/preview.py --profile smart-dark --scene starwrite
python3 tmux/preview.py --profile copper --scene fleet --print-command
```

`preview.py` starts a separate socket/server with that profile and the Nocturne app as its pane command. It bypasses ~/.tmux.conf and does not change the active AFD server. Ctrl+Q exits. **tmux was not installed locally**, so actual server execution is not verified here. `scripts/check_tmux.py` is a real isolated-server parser test, configured in Linux CI.

To deliberately apply a profile to your normal server, review/save existing settings first:

```sh
tmux source-file /absolute/path/nocturne-surfaces/tmux/profiles/smart-dark.conf
```

This changes options. It is not run automatically. Coordinate any settings also owned by AFD.

## RGB and status cadence

Profiles expose `tmux-256color` to pane applications. Correct outer-terminal RGB support still matters. Do not force all terminal types to RGB; match the actual outer terminal's advertised capabilities. The tmux FAQ explains `terminal-features` and color support. Profiles include only a commented example for a known outer terminal.

Primary references: https://github.com/tmux/tmux/wiki/FAQ and https://man.openbsd.org/tmux .

`status-interval` is specified in **seconds**, not fractional frame intervals. `refresh-client -S` refreshes status only. The pane app is the main rich animated surface. Do not assume status formatting can repaint pane backgrounds.

## AFD additive seam

`integrations/afd_bridge.py` exposes `renderStatus(timeMs,paletteId,width,title)`. It returns tmux `#[fg=...,bg=...]` styled text without I/O, clocks, subprocesses or threads, escaping formatting metacharacters in untrusted title text. Prefer invoking it from AFD's existing scheduler once the actual API is available. **AFD source was inaccessible, so this is an adapter seam, not a verified drop-in AFD plugin.** No AFD component is replaced.

```sh
# Pure, explicit-time status text:
python3 tmux/status.py --palette smart-dark --time-ms 2500 --width 40

# Opt-in writer, only after stopping other status-left writers:
python3 tmux/status.py --animate --session my-session --palette copper --fps 10
```

The optional writer changes one session's `status-left`. On clean exit it restores the previous local/inherited setting only when its last value has not been replaced. This is not a lock; concurrent AFD writers can fight it. SIGKILL, server loss and transport failures can prevent cleanup. It spawns a tmux command for each update, allows requested 1..30 updates/s, defaults to10, and is not a low-overhead 30-FPS daemon. One scheduler is preferable to competing processes.

## Real shell prompts

A theme cannot paint behind an arbitrary program's cells. Independent Nocturne and fish/readline writers can damage cursor position, wrapping, completion menus, scrollback and redraws. Starwrite is an inert input inside an app-owned surface; it never executes text. Safe ongoing shell animation requires cooperating repaint hooks or a terminal-level compositor. Fish hooks, right prompts, multiline editing, completion/IME handling and command-boundary integration are **not implemented here**. A one-shot decorative prompt is not equivalent to that integration.
