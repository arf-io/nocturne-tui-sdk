import json
from pathlib import Path
from nocturne_native import NativeScene

with NativeScene(seed=2030) as scene:
    scene.command(json.loads(Path(__file__).with_name("panel.json").read_text()))
    scene.advance_to(500_000)
    frame = scene.render()
    checkpoint = scene.snapshot()
    scene.command({"op": "widget", "id": 1, "value": 0.8})
    scene.restore(checkpoint)
    assert scene.snapshot() == checkpoint
    print(frame.width, frame.height, len(frame.bytes))
