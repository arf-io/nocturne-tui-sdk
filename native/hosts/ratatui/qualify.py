#!/usr/bin/env python3
"""Offline, process-owned Ratatui qualification. No packages are downloaded.

Example (from the SDK root, with an already verified dependency cache):
  python3 native/hosts/ratatui/qualify.py --create-lock \
    --evidence-dir /tmp/nocturne-ratatui-run-1 --target-dir /tmp/nocturne-ratatui-target

An existing Cargo.lock is never regenerated. Only explicit --create-lock authorizes
first-time offline resolution when this source-only host has no lock. Exit codes:
0 PASS, 2 FAIL, 3 BLOCKED, 4 TIMEOUT, 130 INTERRUPTED. PTY checks are POSIX-only.
"""
from __future__ import annotations

import argparse
import codecs
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[3]
HOST = Path(__file__).resolve().parent
MAX_TRANSCRIPT = 16 * 1024 * 1024
ENV_KEYS = ("PATH", "RUSTC", "RUSTDOC", "CARGO_HOME", "CARGO_TARGET_DIR", "CARGO_NET_OFFLINE",
            "RUSTFLAGS", "RUSTC_WRAPPER", "RUSTC_WORKSPACE_WRAPPER", "CC", "AR", "TERM")


def writeJson(path: Path, value: Any) -> None:
    """Atomically replace a receipt owned by this run; propagate filesystem errors."""
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def sha256(path: Path) -> str:
    """Hash a file incrementally; missing/unreadable files raise OSError."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def classifyCommand(exitCode: int, output: str) -> str:
    """Distinguish Cargo's missing offline packages from compilation/test failures."""
    if exitCode == 0:
        return "PASS"
    if any(term in output.lower() for term in ("checksum", "signature verification", "corrupt archive")):
        return "FAIL"
    missing = ("error: no matching package named", "attempting to make an HTTP request, but --offline was specified",
               "failed to download")
    if exitCode == 101 and any(message in output for message in missing):
        return "BLOCKED"
    return "FAIL"


def runCommand(name: str, argv: list[str], cwd: Path, env: dict[str, str],
               directory: Path, timeout: float) -> dict[str, Any]:
    """Execute and wait for one child; retain raw exit code, output and terminal status.

    A timeout kills and reaps the owned POSIX process group. New receipt/log paths
    are mandatory. Invalid deadlines and reused receipt names reject before spawn.
    No missing dependency or interrupted process is counted as an executed test.
    """
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be finite and positive")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
        raise ValueError("invalid command identifier")
    receipt = directory / (name + ".json")
    log = directory / (name + ".log")
    if receipt.exists() or log.exists():
        raise FileExistsError(receipt)
    result: dict[str, Any] = {"id": name, "argv": argv, "cwd": str(cwd), "timeoutSeconds": timeout,
        "environment": {key: env[key] for key in ENV_KEYS if key in env},
        "startedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(), "status": "RUNNING"}
    with receipt.open("x", encoding="utf-8") as owner:
        json.dump(result, owner, indent=2)
        owner.write("\n")
    started = time.monotonic()
    child = None
    with log.open("xb") as stream:
        try:
            child = subprocess.Popen(argv, cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT,
                                     start_new_session=(os.name == "posix"))
            result["pid"] = child.pid
            writeJson(receipt, result)
            try:
                result["exitCode"] = child.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                result["status"] = "TIMEOUT"
                if os.name == "posix":
                    try:
                        os.killpg(child.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                else:
                    child.kill()
                result["exitCode"] = child.wait()
        except OSError as error:
            result.update(status="BLOCKED", exitCode=None, reason=str(error))
            stream.write(str(error).encode())
        except BaseException as error:
            result.update(status="INTERRUPTED", reason=repr(error))
            if child is not None and child.poll() is None:
                if os.name == "posix":
                    try:
                        os.killpg(child.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                else:
                    child.kill()
                child.wait()
            result["exitCode"] = child.returncode if child else None
    if result["status"] == "RUNNING":
        result["status"] = classifyCommand(result["exitCode"], log.read_text(errors="replace"))
    result.update(seconds=round(time.monotonic() - started, 6),
                  finishedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  log=log.name, logSha256=sha256(log))
    writeJson(receipt, result)
    print(f"{name}: {result['status']} (exit {result['exitCode']})", flush=True)
    return result


class Screen:
    """Bounded decoder for this fixture's CSI cursor/erase/SGR output, not a full VT.

    This only observes printable single-cell glyphs. Unknown control sequences fail
    the test instead of being interpreted as proof of a rendered screen.
    """
    def __init__(self, width: int, height: int):
        self.decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self.pending = ""
        self.resize(width, height)

    def resize(self, width: int, height: int) -> None:
        if not 1 <= width <= 1000 or not 1 <= height <= 1000:
            raise ValueError("screen dimensions outside test bounds")
        self.width, self.height = width, height
        self.cells = [[" "] * width for _ in range(height)]
        self.x = self.y = 0

    def lines(self) -> list[str]:
        return ["".join(row) for row in self.cells]

    def feed(self, chunk: bytes) -> None:
        self.pending += self.decoder.decode(chunk)
        while self.pending:
            if self.pending.startswith("\x1b["):
                match = re.match(r"\x1b\[([0-?]*)([ -/]*)([@-~])", self.pending)
                if not match:
                    if len(self.pending) > 256:
                        raise ValueError("unterminated or unsupported CSI")
                    return
                arguments, intermediate, final = match.groups()
                self.pending = self.pending[match.end():]
                if intermediate:
                    raise ValueError("unsupported intermediate CSI")
                if arguments.startswith("?") and final in "hl":
                    if arguments == "?1049" and final == "h":
                        self.resize(self.width, self.height)
                    continue
                values = [int(value) if value else 0 for value in arguments.split(";")]
                first = values[0] if values else 0
                count = first or 1
                if final in "Hf":
                    self.y = max(0, min(self.height - 1, count - 1))
                    self.x = max(0, min(self.width - 1, ((values[1] if len(values) > 1 else 1) or 1) - 1))
                elif final == "A": self.y = max(0, self.y - count)
                elif final == "B": self.y = min(self.height - 1, self.y + count)
                elif final == "C": self.x = min(self.width - 1, self.x + count)
                elif final == "D": self.x = max(0, self.x - count)
                elif final == "G": self.x = min(self.width - 1, count - 1)
                elif final == "d": self.y = min(self.height - 1, count - 1)
                elif final == "J" and first in (0, 2):
                    for y in range(0 if first == 2 else self.y, self.height):
                        begin = self.x if first == 0 and y == self.y else 0
                        self.cells[y][begin:] = [" "] * (self.width - begin)
                elif final == "K" and first in (0, 1, 2):
                    begin, end = (self.x, self.width) if first == 0 else ((0, self.x + 1) if first == 1 else (0, self.width))
                    self.cells[self.y][begin:end] = [" "] * (end - begin)
                elif final == "m": pass
                else: raise ValueError(f"unsupported CSI: {arguments}{final}")
                continue
            if self.pending == "\x1b":
                return
            ch, self.pending = self.pending[0], self.pending[1:]
            if ch == "\x1b": raise ValueError("unsupported non-CSI escape")
            if ch == "\r": self.x = 0
            elif ch == "\n": self.y = min(self.height - 1, self.y + 1)
            elif ch == "\b": self.x = max(0, self.x - 1)
            elif ch >= " ":
                if self.x >= self.width:
                    self.x = 0
                    self.y = min(self.height - 1, self.y + 1)
                self.cells[self.y][self.x] = ch
                self.x += 1


def restoreParentTerminal(slave, before):
    """Retain cleanup failure after a revoked PTY without losing its run receipt."""
    import termios
    try:termios.tcsetattr(slave,termios.TCSANOW,before)
    except (OSError,termios.error) as error:return repr(error)
    return None

def drainPending(master: int, consume: Callable[[bytes], None], deadline: float) -> None:
    """Drain actual ready terminal bytes, stopping on EOF and bounded by deadline."""
    import errno
    import select
    while select.select([master], [], [], 0)[0]:
        if time.monotonic() >= deadline:
            raise TimeoutError("post-exit PTY drain deadline")
        try:
            chunk=os.read(master,65536)
        except OSError as error:
            if error.errno==errno.EIO:return
            raise
        if not chunk:return
        consume(chunk)

def runPty(name: str, binary: Path, directory: Path, env: dict[str, str], timeout: float,
           exercise: Callable[[Any], None] | None, *, failure: str = "none", quitByte: bytes = b"\x11") -> dict[str, Any]:
    """Run a freshly built qualification example on a real controlling POSIX PTY.

    Assertions inspect native trace records AND terminal output. Complete termios is
    measured before any parent cleanup. Each fixture has a bounded lifetime; forced
    parent cleanup is recorded, never mistaken for the child's restoration.
    """
    import fcntl
    import pty
    import select
    import struct
    import termios

    receipt, transcriptPath, trace = (directory / (name + suffix) for suffix in (".json", ".terminal.bin", ".trace.jsonl"))
    if any(path.exists() for path in (receipt, transcriptPath, trace)):
        raise FileExistsError(receipt)
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
    before = termios.tcgetattr(slave)
    acknowledgement=directory/(name+".exit-ack")
    env=dict(env,NOCTURNE_QUALIFICATION_EXIT_ACK=str(acknowledgement))
    argv = [str(binary), "--trace", str(trace), "--hold", "--failure", failure]
    result: dict[str, Any] = {"id": name, "argv": argv, "cwd": str(ROOT), "status": "RUNNING",
        "startedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(), "timeoutSeconds": timeout,
        "environment": {key: env[key] for key in ENV_KEYS if key in env}, "checks": []}
    writeJson(receipt, result)
    output = bytearray()
    screen = Screen(80, 24)
    started = time.monotonic()
    deadline = started + timeout
    child = None
    forced = False

    def controllingTerminal():
        os.setsid()
        fcntl.ioctl(slave, termios.TIOCSCTTY, 0)

    class Probe:
        def records(self):
            if not trace.exists(): return []
            raw = trace.read_bytes()
            if len(raw) > MAX_TRANSCRIPT: raise AssertionError("trace bound exceeded")
            # The last unterminated record may still be in the writer's syscall.
            return [json.loads(line) for line in raw.split(b"\n")[:-1] if line]

        def info(self):
            rows = self.records()
            return rows[-1].get("info", {}) if rows else {}

        def wait(self, predicate, message):
            while not predicate():
                if time.monotonic() >= deadline:
                    raise TimeoutError(message)
                self.drain(min(0.05, max(0, deadline - time.monotonic())))
                if child.poll() is not None and not predicate():
                    raise AssertionError(f"{message}; child exited {child.returncode}")
            result["checks"].append(message)

        def drain(self, wait=0):
            if select.select([master], [], [], wait)[0]:
                try: chunk = os.read(master, 65536)
                except OSError as error:
                    if error.errno == 5: return
                    raise
                if chunk:
                    output.extend(chunk)
                    if len(output) > MAX_TRANSCRIPT: raise AssertionError("terminal transcript bound exceeded")
                    screen.feed(chunk)

        def send(self, data):
            pending = memoryview(data)
            while pending:
                if time.monotonic() >= deadline: raise TimeoutError("PTY write deadline")
                if select.select([], [master], [], min(0.05, max(0, deadline - time.monotonic())))[1]:
                    pending = pending[os.write(master, pending):]

        def resize(self, width, height):
            screen.resize(width, height)
            fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", height, width, 0, 0))
            os.kill(child.pid, signal.SIGWINCH)

        def visible(self, text):
            return text in "\n".join(screen.lines())

    probe = Probe()
    try:
        child = subprocess.Popen(argv, stdin=slave, stdout=slave, stderr=slave, cwd=ROOT,
                                 env=env, close_fds=True, preexec_fn=controllingTerminal)
        result["pid"] = child.pid
        writeJson(receipt, result)
        def rawMode():
            flags = termios.tcgetattr(slave)
            return not flags[3] & (termios.ICANON | termios.ECHO | termios.ISIG) and not flags[0] & termios.IXON
        if failure == "setup":
            probe.wait(lambda: rawMode() and any(r["event"] == "setup-raw" for r in probe.records()),
                       "raw partial setup was observed before authorizing its failure")
            if b"\x1b[?1049h" in output: raise AssertionError("partial-setup case entered the alternate screen")
            probe.send(b"\x11")
        else:
            def ready():
                flags = termios.tcgetattr(slave)
                raw = not flags[3] & (termios.ICANON | termios.ECHO | termios.ISIG) and not flags[0] & termios.IXON
                return raw and b"\x1b[?1049h" in output and probe.visible("RATATUI NATIVE PTY") and any(r["event"] == "ready" for r in probe.records())
            probe.wait(ready, "raw PTY and actual first native frame precede input")
            if not all(code in output for code in (b"\x1b[?1003h", b"\x1b[?1006h", b"\x1b[?2004h", b"\x1b[?1004h")):
                raise AssertionError("mouse/paste/focus protocols not enabled")
            if exercise is not None: exercise(probe)
            probe.send(quitByte)
        probe.wait(lambda: any(r.get("event")=="exit" for r in probe.records()),
                   "child restoration precedes exit acknowledgement")
        after=termios.tcgetattr(slave)
        result["terminalAttributesRestoredByChild"]=after==before
        result["restorationObservedBeforeExit"]=child.poll() is None
        if after!=before:raise AssertionError("child did not restore exact termios")
        if not result["restorationObservedBeforeExit"]:raise AssertionError("child exited before restoration observation")
        with acknowledgement.open("x") as ack:ack.write("observed\n")
        probe.wait(lambda: child.poll() is not None, "child reached terminal exit")
        child.wait()
        # Keep the slave open for the termios oracle; drain until no bytes remain.
        def retainTerminal(chunk):
            output.extend(chunk)
            if len(output)>MAX_TRANSCRIPT:raise AssertionError("terminal transcript bound exceeded")
            screen.feed(chunk)
        drainPending(master,retainTerminal,deadline)

        expected = {"none": 0, "error": 1, "panic": 101, "setup": 1}[failure]
        if child.returncode != expected: raise AssertionError(f"expected exit {expected}, got {child.returncode}")
        if failure != "setup":
            codes = (b"\x1b[?1049l", b"\x1b[?25h", b"\x1b[?1003l", b"\x1b[?1006l", b"\x1b[?2004l", b"\x1b[?1004l")
            if not all(code in output for code in codes): raise AssertionError("terminal mode cleanup missing")
        records = probe.records()
        if not records or records[-1].get("event") != "exit": raise AssertionError("missing completed exit trace")
        hint = {"none": "normal", "setup": "intentional partial-startup failure",
                "error": "intentional post-input failure", "panic": "intentional unwinding qualification panic"}[failure]
        if hint not in records[-1].get("note", ""):
            raise AssertionError("exit did not reach the requested failure/quit path")
        result.update(status="PASS", expectedExitCode=expected, finalInfo=probe.info())
        result["checks"].append("exact termios and enabled terminal protocols restored by child")
    except TimeoutError as error:
        result.update(status="TIMEOUT", reason=str(error))
    except FileNotFoundError as error:
        result.update(status="BLOCKED", reason=str(error))
    except Exception as error:
        result.update(status="FAIL", reason=repr(error))
    except BaseException as error:
        result.update(status="INTERRUPTED", reason=repr(error))
    finally:
        if child is not None and child.poll() is None:
            forced = True
            try: os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError: pass
            child.wait()
        result["exitCode"] = child.returncode if child else None
        result["parentForcedCleanup"] = forced
        if "terminalAttributesRestoredByChild" not in result:
            try:result["terminalAttributesRestoredByChild"]=termios.tcgetattr(slave)==before
            except (OSError,termios.error) as error:
                result["terminalAttributesRestoredByChild"]=None
                result["terminalObservationError"]=repr(error)
        # Isolated test-owned PTY recovery; this is not evidence of child restoration.
        result["parentCleanupError"] = restoreParentTerminal(slave,before)
        os.close(master)
        os.close(slave)
        transcriptPath.write_bytes(output)
        result.update(seconds=round(time.monotonic() - started, 6),
            finishedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            transcript=transcriptPath.name, transcriptSha256=sha256(transcriptPath),
            trace=trace.name if trace.exists() else None, traceSha256=sha256(trace) if trace.exists() else None,
            binarySha256=sha256(binary) if binary.exists() else None)
        writeJson(receipt, result)
    print(f"{name}: {result['status']} (exit {result['exitCode']})", flush=True)
    return result


def exerciseInput(probe) -> None:
    """Observe immediate C-owned input/edit/paste and a real terminal repaint while held."""
    for data, text, caret in [
        (b"abc", "abc", 3),
        (b"\x1b[H", "abc", 0),
        ("é".encode(), "éabc", 1),
        (b"\x1b[F", "éabc", 4),
        (b'\x1b[200~ \\"Z\x1b[201~', 'éabc \\"Z', 8),
        (b"\x7f", 'éabc \\"', 7),
    ]:
        probe.send(data)
        probe.wait(lambda: probe.info().get("prompt", {}).get("text") == text and probe.info()["prompt"]["caret"] == caret,
                   f"native edit committed: {text!r}, caret {caret}")
        if probe.info().get("clock", {}).get("timeUs") != 0:
            raise AssertionError("held input advanced simulation")
    probe.wait(lambda: probe.visible("éabc"), "typed Unicode appears in actual terminal output")
    probe.resize(100, 30)
    probe.wait(lambda: any(r.get("width") == 100 and r.get("height") == 30 for r in probe.records()),
               "PTY resize reached current native frame")
    probe.wait(lambda: probe.visible("RATATUI NATIVE PTY"), "native title repainted after resize")
    if probe.info()["clock"]["timeUs"] != 0: raise AssertionError("resize advanced held simulation")


def exercisePointer(probe) -> None:
    """Feed actual SGR mouse and focus-loss events into the current native state owner."""
    def states():
        rows = probe.info().get("registeredStates", [])
        return rows[0].get("states", {}) if rows else {}
    for data, field, expected in [(b"\x1b[<35;9;10M", "hover", True),
                                  (b"\x1b[<0;9;10M", "pressed", True),
                                  (b"\x1b[<0;9;10m", "pressed", False),
                                  (b"\x1b[O", "hover", False)]:
        count = len(probe.records())
        probe.send(data)
        probe.wait(lambda: len(probe.records()) > count and states().get(field) is expected, f"native {field}={expected}")
    if not states().get("selected"): raise AssertionError("native button was not selected")
    info = probe.info()
    if info["clock"]["timeUs"] != 0 or info["fieldCount"] != 0:
        raise AssertionError("mouse input changed time or spawned text weather")


def sourceHashes() -> dict[str, str]:
    """Fingerprint compiled source and dependency policy, excluding generated outputs."""
    paths = []
    for directory in [ROOT / "native/src", ROOT / "native/include", ROOT / "native/bindings/rust", HOST]:
        paths.extend(path for path in directory.rglob("*") if path.is_file() and
                     path.suffix in (".rs", ".c", ".h", ".toml", ".lock", ".py") and
                     not any(part in ("target", "__pycache__") for part in path.relative_to(directory).parts))
    return {str(path.relative_to(ROOT)): sha256(path) for path in sorted(set(paths))}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", type=Path, required=True, help="new run directory outside the SDK")
    parser.add_argument("--target-dir", type=Path, help="Cargo output directory outside the SDK")
    parser.add_argument("--rust-bin", type=Path, help="already verified compiler bin directory")
    parser.add_argument("--create-lock", action="store_true", help="explicit first-time offline lock resolution; never regenerates an existing lock")
    parser.add_argument("--timeout", type=float, default=180, help="per-command deadline in seconds")
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0: parser.error("timeout must be finite and positive")
    directory = args.evidence_dir.resolve()
    target = (args.target_dir or Path(os.environ.get("CARGO_TARGET_DIR", str(directory / "target")))).resolve()
    if directory.is_relative_to(ROOT) or target.is_relative_to(ROOT): parser.error("evidence and target must be outside the SDK")
    if directory.exists(): parser.error("evidence directory must be new")
    directory.mkdir(parents=True)
    target.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    if args.rust_bin:
        binPath = args.rust_bin.resolve()
        env.update(PATH=str(binPath) + os.pathsep + env.get("PATH", ""), RUSTC=str(binPath / "rustc"), RUSTDOC=str(binPath / "rustdoc"))
    env.update(CARGO_NET_OFFLINE="true", CARGO_TARGET_DIR=str(target), CARGO_TERM_COLOR="never")
    report: dict[str, Any] = {"schema": "nocturne.ratatui.qualification.v1", "status": "RUNNING",
        "ratatuiQualified": False, "fullRC4Qualified": False, "scope": "Current dependency-backed Ratatui adapter and synthetic POSIX fixture only",
        "commands": [], "pty": [], "sourceBefore": sourceHashes(), "unexecuted": []}
    reportPath = directory / "QUALIFICATION.json"
    writeJson(reportPath, report)
    lock = HOST / "Cargo.lock"
    sys.path.insert(0,str(ROOT/'native/scripts'))
    from cargo_example import cargoEnvironment
    env=cargoEnvironment(ROOT,env)
    originalLock = lock.read_bytes() if lock.exists() else None
    report["lockInitiallyPresent"] = originalLock is not None

    def finish(status, reason=None):
        report.update(status=status, sourceAfter=sourceHashes())
        report["sourceChanges"] = [path for path in sorted(set(report["sourceBefore"]) | set(report["sourceAfter"]))
                                  if report["sourceBefore"].get(path) != report["sourceAfter"].get(path)]
        allowed = ["native/hosts/ratatui/Cargo.lock"] if args.create_lock and originalLock is None else []
        unexpected = [path for path in report["sourceChanges"] if path not in allowed]
        if unexpected or (originalLock is not None and (not lock.exists() or lock.read_bytes() != originalLock)):
            report.update(status="FAIL", reason="source or existing lock changed during qualification", unexpectedSourceChanges=unexpected)
        elif reason:
            report["reason"] = reason
        report["ratatuiQualified"] = report["status"] == "PASS" and bool(report["pty"])
        report["finishedAt"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        writeJson(reportPath, report)
        print(f"Ratatui qualification: {report['status']}", flush=True)
        return {"PASS": 0, "FAIL": 2, "BLOCKED": 3, "TIMEOUT": 4, "INTERRUPTED": 130}[report["status"]]

    def command(name, argv):
        row = runCommand(name, argv, ROOT, env, directory, args.timeout)
        report["commands"].append(row)
        writeJson(reportPath, report)
        return row

    try:
        for name, argv in [("rust-identity", [env.get("RUSTC", "rustc"), "-vV"]),
                           ("cargo-identity", ["cargo", "--version"]),
                           ("rustdoc-identity", [env.get("RUSTDOC", "rustdoc"), "--version"]),
                           ("sysroot", [env.get("RUSTC", "rustc"), "--print", "sysroot"])]:
            result = command(name, argv)
            if result["status"] != "PASS": return finish(result["status"], "compiler identity command failed; recover/qualify compiler separately")
        manifest = str(HOST / "Cargo.toml")
        if originalLock is None:
            if not args.create_lock:
                return finish("BLOCKED", "no host Cargo.lock; explicit --create-lock is required for first offline resolution")
            result = command("initial-lock", ["cargo", "generate-lockfile", "--offline", "--manifest-path", manifest])
            if result["status"] != "PASS":
                report["unexecuted"] = ["dependency-metadata", "host-tests", "host-doctests", "host-docs", "fixture-build", "PTY lifecycle/input/render/exit"]
                return finish(result["status"], "offline host dependency resolution did not complete; see initial-lock.log")
        flags = ["--offline", "--locked", "--manifest-path", manifest]
        result = command("dependency-metadata", ["cargo", "metadata", *flags, "--format-version", "1"])
        if result["status"] != "PASS": return finish(result["status"], "locked dependency closure unavailable")
        for name, argv in [("host-tests", ["cargo", "test", *flags, "--all-targets"]),
                           ("host-doctests", ["cargo", "test", *flags, "--doc"]),
                           ("host-docs", ["cargo", "doc", *flags, "--no-deps"]),
                           ("fixture-build", ["cargo", "build", *flags, "--example", "qualification", "--message-format=json-render-diagnostics"])]:
            result = command(name, argv)
            if result["status"] != "PASS": return finish(result["status"], f"{name} did not pass; PTY checks not executed")
        artifacts = []
        for line in (directory / "fixture-build.log").read_text().splitlines():
            if not line.startswith("{"): continue
            entry = json.loads(line)
            if entry.get("reason") == "compiler-artifact" and entry.get("target", {}).get("name") == "qualification" and entry.get("executable"):
                artifacts.append(Path(entry["executable"]).resolve())
        if len(set(artifacts)) != 1 or not artifacts[0].is_file(): return finish("FAIL", "Cargo did not identify exactly one built qualification executable")
        if os.name != "posix": return finish("BLOCKED", "this PTY harness requires POSIX; other platforms remain unqualified")
        env.update(TERM="xterm-256color", LANG="C.UTF-8")
        for name, exercise, failure, quitByte in [("pty-input-resize-ctrlq", exerciseInput, "none", b"\x11"),
                ("pty-pointer-focus", exercisePointer, "none", b"\x11"), ("pty-ctrlc", None, "none", b"\x03"),
                ("pty-error", None, "error", b"\x11"), ("pty-panic", None, "panic", b"\x11"),
                ("pty-partial-setup", None, "setup", b"\x11")]:
            result = runPty(name, artifacts[0], directory, env, min(args.timeout, 30), exercise, failure=failure, quitByte=quitByte)
            report["pty"].append(result)
            writeJson(reportPath, report)
        status = next((s for s in ["INTERRUPTED", "TIMEOUT", "FAIL", "BLOCKED"] if any(row["status"] == s for row in report["pty"])), "PASS")
        return finish(status)
    except KeyboardInterrupt:
        return finish("INTERRUPTED", "qualification interrupted")
    except Exception as error:
        return finish("FAIL", repr(error))


if __name__ == "__main__":
    raise SystemExit(main())
