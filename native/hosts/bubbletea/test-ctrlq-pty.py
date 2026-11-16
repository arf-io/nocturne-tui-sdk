#!/usr/bin/env python3
"""Exercise both Bubble Tea quit keys through a real PTY."""
import os
import pty
import select
import subprocess
import termios
import time


def drain(master, transcript, duration):
    deadline = time.monotonic() + duration
    while time.monotonic() < deadline:
        ready, _, _ = select.select([master], [], [], min(0.05, deadline - time.monotonic()))
        if not ready:
            continue
        try:
            chunk = os.read(master, 65536)
        except OSError:
            break
        if not chunk:
            break
        transcript.extend(chunk)


def run_key(name, byte):
    master, slave = pty.openpty()
    env = os.environ.copy()
    env.setdefault("TERM", "xterm-256color")
    proc = subprocess.Popen(
        ["./bubbletea-host"], stdin=slave, stdout=slave, stderr=slave, env=env,
        close_fds=True,
    )
    os.close(slave)
    transcript = bytearray()
    deadline = time.monotonic() + 8
    raw_seen = False
    while time.monotonic() < deadline and proc.poll() is None:
        ready, _, _ = select.select([master], [], [], 0.05)
        if ready:
            try:
                transcript.extend(os.read(master, 65536))
            except OSError:
                break
        if b"\x1b[?1049h" in transcript:
            lflag = termios.tcgetattr(master)[3]
            raw_seen = not (lflag & (termios.ICANON | termios.ECHO | termios.IXON))
            if raw_seen:
                break
    if not raw_seen:
        proc.kill()
        proc.wait()
        raise AssertionError(f"{name}: host did not enter raw PTY mode")

    # Let Bubble Tea finish initialization before sending input.
    time.sleep(0.25)
    drain(master, transcript, 0.05)
    if proc.poll() is not None:
        raise AssertionError(f"{name}: host exited before key input, status {proc.returncode}")
    os.write(master, byte)
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired as exc:
        proc.kill()
        proc.wait()
        raise AssertionError(f"{name}: quit key did not exit host") from exc
    drain(master, transcript, 0.5)
    if proc.returncode != 0:
        raise AssertionError(f"{name}: host exited with status {proc.returncode}")
    if b"\x1b[?1049l" not in transcript:
        raise AssertionError(f"{name}: host exited without restoring alternate screen")
    os.close(master)


def main():
    run_key("Ctrl-Q", b"\x11")
    run_key("Ctrl-C", b"\x03")
    print("PASS: Ctrl-Q and Ctrl-C exit via PTY key events and restore terminal")


if __name__ == "__main__":
    main()
