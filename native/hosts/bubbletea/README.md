# Bubble Tea host

A Bubble Tea 1.3.4 application that runs the C core through the Go binding (cgo). Bubble Tea owns the terminal, time and input. `View` returns a cached frame, and `Update` turns input and the clock into native commands. `go.mod` replaces `nocturne/native` with `../../bindings/go`.

## Build and run

```sh
sh build-native.sh
cd native/hosts/bubbletea
go run .
```

The module needs Bubble Tea's dependencies in a Go module cache. To build offline with a cache you provisioned yourself, use a separate build copy and keep the cache outside the SDK:

```sh
export GOFLAGS=-mod=readonly GOPROXY=off GOSUMDB=off GOTOOLCHAIN=local
export GOMODCACHE=/absolute/verified/go-cache
export GOCACHE=/absolute/external/go-build-cache
(cd native/hosts/bubbletea && go test -count=1 -v .)
(cd native/hosts/bubbletea && go build -o /absolute/external/bubbletea-host .)
/absolute/external/bubbletea-host
```

Do not run `go mod tidy` or `go mod download` in the SDK to prepare a test. They change `go.sum`.

`go mod verify` exits 1 for the local replacement `nocturne/native v0.0.0` because that module has no downloaded archive and so no ziphash. The remote modules verify.

## Options and keys

Ctrl-Q and Ctrl-C quit and restore the terminal. Pasted text is always data, so a pasted Ctrl-Q does not quit.

- `--paused` holds the scene.
- `--document-text=TEXT` sets the starting document.
- `--info-on-exit=PATH` writes the scene info when the program exits.
- `--unicode-document` shows a document viewport built from the native `BidiLayout` and `BidiHit`. It keeps whole combining and emoji clusters, uses native mirrored scalars and source offsets, highlights selected ranges, and maps left clicks into the prompt. The mouse wheel scrolls the viewport without changing the scene. Arrows, Home, End, PageUp, PageDown, Shift selection and dragging work through native source mapping. Vertical movement keeps its preferred column, and an unchanged repaint keeps a manual scroll. When another owner has input, the host uses the scene renderer.
- `--reserve-shortcut=ctrl+q` reserves a key, and the host picks another (alt+q here). Repeat the option to reserve more keys. The hint row shows the keys in use or `unassigned`. Ctrl+c stays the emergency exit.

Shift with the arrows, Home and End extends the selection. Alt-W copies, Ctrl-W cuts and Ctrl-Y pastes through a buffer kept by the host, which is separate from the system clipboard. Clipboard shortcuts respect modal and reader ownership.

On blur the host sends the native pointer cancel, so hover and pressed state do not survive a focus change. The pinned framework restores the terminal after a panic in the event loop or the first `View`, but returns `(nil, nil)`. `runModel` rejects the missing final model and the program exits 1.

## Tests

There are five Go model tests (held edits and paste, `View` leaves the scene unchanged, focus loss, resize and native errors, and atomic rejection of a paste with C0 control characters) and focused tests for cluster order, click-to-edit in right-to-left text, viewport scrolling and input-owner fallback.

Ten pseudo-terminal cases run the real program: Ctrl-Q and Ctrl-C quit, advancing time, held input with Unicode, paste and resize, click, hover, focus and camera drags, a rejected paste, a native error, a recovered panic and a failure during startup. Each case waits for raw mode, and passes when the child exits with the expected status (1 for errors) and restores its own termios settings, alternate screen and cursor.

`test-ctrlq-pty.py` checks the two quit keys. It runs `./bubbletea-host` from the current directory:

```sh
(cd native/hosts/bubbletea && go build -o bubbletea-host . && python3 test-ctrlq-pty.py)
```

`native/scripts/check_bubbletea_unicode.py --binary PATH --output NEW_DIRECTORY` checks the `--unicode-document` view in a pseudo-terminal. The full set runs from `qualify_dependency_hosts.py`:

```sh
python3 native/scripts/qualify_dependency_hosts.py \
  --target-dir /new/external/hosts-target --evidence-dir /new/external/hosts-run
```

The pseudo-terminal checks run on Linux. Terminal font shaping is outside what they check.
