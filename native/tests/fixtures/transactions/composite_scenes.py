"""Three composite benchmark screens. Each: SETUP commands and per_frame(frame, time_us) -> commands for a live
session at 60 Hz (clock tick, streamed agent text, typing with weather, scene-specific live updates)."""
import textwrap

AGENT = ("Reading the repository layout. Three packages share one build graph; the renderer owns the frame and the "
         "prompt owns input. Proposing a change: move the glyph atlas upload out of the frame loop and batch the cell "
         "writes. Running the tests now. All forty-two pass. Measuring the frame budget at two hundred and forty hertz. "
         "The slowest frame spends most of its time copying state, not drawing. Drafting the fix. ")


def wrapped(chars, width, rows):
    text = (AGENT * 4)[:chars]
    lines = textwrap.wrap(text, width) or ['']
    return '\n'.join(lines[-rows:])


def materials():
    return [
        {"op": "material", "id": 11, "space": "rgb", "channels": {"r": 0.89, "g": 0.87, "b": 0.81}},
        {"op": "material", "id": 12, "space": "rgb", "channels": {"r": 0.91, "g": 0.68, "b": 0.45}},
        {"op": "material", "id": 13, "space": "rgb", "channels": {"r": 0.53, "g": 0.84, "b": 0.75}},
        {"op": "material", "id": 14, "space": "rgb", "channels": {"r": 0.05, "g": 0.08, "b": 0.12}},
        {"op": "material", "id": 15, "space": "rgb", "channels": {"r": 0.60, "g": 0.66, "b": 0.71}},
    ]


def agent_window(x, y, w, h, title):
    return [
        {"op": "widget", "id": 1, "kind": "box", "x": x, "y": y, "width": w, "height": h, "text": "",
         "border": "rounded", "material": 15, "backgroundMaterial": 14, "alpha": 0.86},
        {"op": "widget", "id": 2, "kind": "text", "x": x + 3, "y": y + 1, "width": w - 6, "height": 1, "text": title,
         "material": 13, "backgroundMaterial": 14, "alpha": 1},
        {"op": "widget", "id": 3, "kind": "text", "x": x + 3, "y": y + 3, "width": w - 6, "height": h - 5, "text": "",
         "material": 11, "backgroundMaterial": 14, "alpha": 1},
    ]


def prompt(weather):
    return [
        {"op": "prompt", "active": True, "mode": "grow", "minRows": 1, "maxRows": 4, "border": "rounded",
         "padding": 1, "alpha": 0.9},
        {"op": "prompt-appearance", "cursor": {"shape": "bar", "color": "#86d5c0", "blinkMs": 700, "duty": 0.65},
         "weather": {"style": weather, "intensity": 1.0, "lifeMs": 2200, "speed": 16, "paste": "burst"}},
    ]


TYPED = ("show me the slowest frame and explain why it is slow, then propose the smallest change that makes it fit "
         "the budget")


def common_frame(frame, time_us, win_w, win_h):
    out = [{"op": "time", "timeUs": time_us}]
    if frame % 3 == 0:
        out.append({"op": "widget", "id": 3, "text": wrapped(frame * 2 + 40, win_w - 6, win_h - 5)})
    if frame % 7 == 0:
        k = (frame // 7) % (len(TYPED) + 1)
        out.append({"op": "draft", "text": TYPED[:k], "emitWeather": True})
    return out


def warp():
    setup = [
        {"op": "resize", "width": 160, "height": 48},
        {"op": "camera", "profile": "original", "navigation": "fly", "position": [0, 0, 0],
         "yaw": -18, "pitch": 8, "roll": 12, "fov": 70, "near": 0.1, "far": 1000},
        {"op": "environment", "presentation": "canvas", "style": "wave", "starProfile": "source", "worldSeed": 2030,
         "skyDensity": 18, "skyRadius": 280, "skyExposure": 9000, "trailMs": 140},
        {"op": "field", "effect": "surface-field/silk-tide", "x": 40, "y": 30, "lifeMs": 60000, "strength": 0.55,
         "width": 2.2, "speed": 6},
        {"op": "field", "effect": "surface-field/opal-fronts", "x": 70, "y": 12, "lifeMs": 60000, "strength": 0.4,
         "width": 1.6, "speed": 5},
        {"op": "flight", "profile": "original",
         "steps": [{"kind": "turn", "durationMs": 18000, "yaw": -90, "speed": 12, "coordinated": True, "bank": 32}]},
        *materials(), *agent_window(98, 2, 60, 36, "AGENT  /  build graph review"),
        {"op": "text", "id": 1, "text": "NOCTURNE", "effect": "text/prism-weave", "x": 8, "y": 5, "width": 60,
         "durationMs": 2200, "staggerMs": 28, "jitterMs": 300, "scatter": 13, "distance": 12},
        *prompt("embers"),
    ]

    def frame(f, t):
        out = common_frame(f, t, 60, 36)
        if f % 180 == 90:
            out.append({"op": "text", "id": 1, "text": "NOCTURNE", "effect": "text/comet-stitch" if f % 360 == 90 else
                        "text/prism-weave", "x": 8, "y": 5, "width": 60, "durationMs": 2000, "staggerMs": 18,
                        "scatter": 10, "distance": 8})
        return out
    return 'warp', 'Warp: banked starfield turn, flowing field, agent stream, kinetic title, embers', setup, frame


def night_shift():
    labels = ["Plan release", "Profile frame", "Copy state once", "Batch commands", "Upload atlas", "Run tests",
              "Measure 240 Hz", "Ship"]
    setup = [
        {"op": "resize", "width": 160, "height": 48},
        {"op": "camera", "position": [0, 8, 162], "yaw": 0, "pitch": 0, "fov": 64, "profile": "original"},
        {"op": "environment", "presentation": "canvas", "style": "plasma", "stars": 260},
        {"op": "layout", "profile": "source", "dimensions": 3, "mode": "layered"},
        *[{"op": "node", "id": i + 1, "kind": "Task", "label": l, "status": "waiting", "maxColumns": 22,
           "padding": 0, "showKind": False, "showDetail": False} for i, l in enumerate(labels)],
        *[{"op": "edge", "from": a, "to": b, "kind": "depends"} for a, b in
          [(1, 2), (2, 3), (2, 4), (3, 5), (4, 5), (5, 6), (6, 7), (7, 8)]],
        {"op": "camera-action", "action": "view", "name": "iso"},
        {"op": "camera-action", "action": "fit"},
        *materials(), *agent_window(104, 2, 54, 34, "AGENT  /  night shift"),
        *prompt("rain"),
    ]

    def frame(f, t):
        out = common_frame(f, t, 54, 34)
        if f % 45 == 0:
            n = (f // 45) % 9
            for i in range(8):
                status = "ready" if i < n else ("running" if i == n else "waiting")
                if i in (n - 1, n):
                    out.append({"op": "node", "id": i + 1, "status": status})
        return out
    return 'night-shift', 'Night shift: 3D task graph progressing, agent stream, rain', setup, frame


def instruments():
    import math
    setup = [
        {"op": "resize", "width": 160, "height": 48},
        {"op": "camera", "profile": "original", "navigation": "fly", "position": [0, 0, 0],
         "yaw": 10, "pitch": 4, "roll": 0, "fov": 72, "near": 0.1, "far": 1000},
        {"op": "environment", "presentation": "canvas", "style": "caustic", "starProfile": "source",
         "worldSeed": 7, "skyDensity": 14, "skyRadius": 260, "skyExposure": 8000, "trailMs": 120},
        {"op": "flight", "profile": "original",
         "steps": [{"kind": "climb", "durationMs": 18000, "pitch": 18, "speed": 10}]},
        *materials(),
        {"op": "widget", "id": 10, "kind": "box", "x": 2, "y": 2, "width": 56, "height": 16, "text": "",
         "border": "rounded", "material": 15, "backgroundMaterial": 14, "alpha": 0.85},
        {"op": "widget", "id": 11, "kind": "line", "x": 5, "y": 4, "width": 50, "height": 12,
         "data": [0.5] * 24, "sampling": "braille", "material": 13, "backgroundMaterial": 14},
        {"op": "widget", "id": 12, "kind": "bars", "x": 5, "y": 20, "width": 50, "height": 8,
         "data": [0.4] * 12, "sampling": "braille", "material": 12, "backgroundMaterial": 14},
        {"op": "widget", "id": 13, "kind": "donut", "x": 62, "y": 3, "width": 28, "height": 12,
         "data": [61, 24, 15], "sampling": "braille", "material": 13, "backgroundMaterial": 14,
         "cellAspect": 2, "innerRadius": 0.6},
        *agent_window(98, 2, 60, 36, "AGENT  /  frame budget"),
        *prompt("snow"),
    ]

    def frame(f, t):
        out = common_frame(f, t, 60, 36)
        if f % 2 == 0:
            ph = f / 20
            out.append({"op": "widget", "id": 11,
                        "data": [round(0.5 + 0.4 * math.sin(ph + i / 3), 3) for i in range(24)]})
        if f % 6 == 0:
            out.append({"op": "widget", "id": 12,
                        "data": [round(0.3 + 0.6 * abs(math.sin(f / 30 + i)), 3) for i in range(12)]})
        return out
    return 'instruments', 'Instruments: climbing starfield, live plots and bars, agent stream, snow', setup, frame


SCENES = [warp(), night_shift(), instruments()]
