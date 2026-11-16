#!/usr/bin/env python3
"""Observe the actual prompt_toolkit application in an owned qualification PTY.

The fixture loads native authoring commands and observes frames after the real
framework render. It never substitutes an input, output, framework or C adapter.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from prompt_toolkit_host import FrameworkHost

MAX_TRACE_BYTES = 16 * 1024 * 1024


def main() -> None:
    """Run one fixture with explicit file paths; failures preserve host cleanup."""
    scenario = os.environ['NOCTURNE_TEST_SCENARIO']
    tracePath = Path(os.environ['NOCTURNE_TEST_TRACE'])
    fixturePath = Path(os.environ['NOCTURNE_TEST_FIXTURE'])
    host = FrameworkHost(fps=1 if scenario == 'latency' else 60)
    host.scene.command({'op': 'reset', 'seed': 2030})
    for line in fixturePath.read_text().splitlines():
        if line.strip():
            host.scene.command(json.loads(line))
    host.held = scenario != 'backpressure'
    host.scene.command({'op': 'pause', 'paused': host.held})
    host.control.viewport = None
    byteCount = 0
    with tracePath.open('x', encoding='utf-8') as trace:
        def record(event: str) -> None:
            nonlocal byteCount
            frame = host.scene.render()
            hits = {}
            for index, (_, _, _, owner) in enumerate(frame.words()):
                if owner & 0xff000000 == 0x10000000:
                    hits.setdefault(str(owner & 0xffff), [index % frame.width, index // frame.width])
            line = json.dumps({'event': event, 'info': host.scene.info(),
                               'width': frame.width, 'height': frame.height,
                               'nodeHits': hits}, ensure_ascii=False) + '\n'
            byteCount += len(line.encode('utf-8'))
            if byteCount > MAX_TRACE_BYTES:
                raise RuntimeError('qualification trace capacity')
            trace.write(line)
            trace.flush()

        host.application.after_render += lambda _: record('paint')
        try:
            host.run(max_seconds=30)
        finally:
            record('exit')
            host.scene.close()


if __name__ == '__main__':
    main()
