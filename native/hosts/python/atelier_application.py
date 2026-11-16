"""Adapters for historical Atelier artwork on the unified native scene API.

These functions translate authoring controls into native SDK commands. They do
not evaluate an HTML/JavaScript renderer or maintain a second scene runtime.
"""
from __future__ import annotations

import math
import re
from typing import Any, Mapping, Sequence


# Source identities and their native names are the original 0.5/RC.2 catalogue
# names. Keep each historical family addressable even where the visible label
# overlaps with its parallel implementation.
TEXT_TRANSITIONS = {
    **{f"kinetic/{old}": f"text/{new}" for old, new in {
        "immediate": "direct-ink", "fade": "ink-dissolve", "rain": "glyph-rain",
        "scramble": "cipher-resolve", "flipboard": "station-board",
        "sweep-left": "ribbon-left", "sweep-right": "ribbon-right",
        "marquee": "travelling-line", "orbit": "satellite-type",
        "constellation": "star-map-type", "prism-stitch": "prism-stitch",
        "gravity-loom": "gravity-loom", "scanline": "scanline-type",
        "elastic": "elastic-type", "typewriter": "keystep",
        "curtain": "curtain-type", "fall": "glyph-fall", "ash": "ash-type",
    }.items()},
    **{f"atelier/{old}": f"text/{new}" for old, new in {
        "instant": "instant-ink", "fade": "velvet-dissolve", "rain": "skyfall-type",
        "scramble": "static-resolve", "flipboard": "departure-board",
        "sweep-left": "weft-left", "sweep-right": "weft-right",
        "lift": "rising-ink", "fall": "falling-ink", "marquee": "ticker-type",
        "iris": "iris-type", "constellation": "constellation-type",
        "prism-weave": "prism-weave", "ink-tide": "ink-tide",
        "comet-stitch": "comet-stitch", "orbit": "orbital-type",
        "fold": "folded-type", "zipper": "zipper-type",
    }.items()},
}
ATELIER_TEXT_EFFECTS = {k.removeprefix("atelier/"): v for k, v in TEXT_TRANSITIONS.items()
                        if k.startswith("atelier/")}

_KINETIC_WINDOW_NAMES = {
    "fade": "glass-dissolve", "bounce": "elastic-pop", "genie": "lamp-genie",
    "roll-up": "scroll-up", "roll-down": "scroll-down", "drawer-left": "rail-left",
    "drawer-right": "rail-right", "drawer-top": "rail-top", "drawer-bottom": "rail-bottom",
    "center": "center-aperture", "top-left": "northwest-aperture",
    "top-right": "northeast-aperture", "bottom-left": "southwest-aperture",
    "bottom-right": "southeast-aperture", "iris": "circular-iris",
    "explosion": "shard-burst", "accordion": "concertina", "portal": "portal-fold",
    "orbital-bloom": "orbital-bloom", "venetian": "venetian",
    "ribbon-unfurl": "ribbon-unfurl",
}
_ATELIER_WINDOW_NAMES = {
    "fade": "silk-dissolve", "expand-center": "center-bloom",
    "expand-nw": "northwest-bloom", "expand-ne": "northeast-bloom",
    "expand-sw": "southwest-bloom", "expand-se": "southeast-bloom",
    "circle": "circle-bloom", "roll-up": "reel-up", "roll-down": "reel-down",
    "drawer-left": "pocket-left", "drawer-right": "pocket-right",
    "drawer-top": "pocket-top", "drawer-bottom": "pocket-bottom",
    "bounce": "spring-pop", "genie": "ribbon-genie", "explode": "fragment-scatter",
    "accordion": "accordion-fold", "origami": "origami", "vortex": "vortex-fold",
    "ribbon-unspool": "ribbon-unspool", "petal-bloom": "petal-bloom",
    "gravity-well": "gravity-well",
}
SPATIAL_WINDOW_EFFECTS = {
    **{f"kinetic/{old}": f"window-transition/{new}" for old, new in _KINETIC_WINDOW_NAMES.items()},
    **{f"atelier/{old}": f"window-transition/{new}" for old, new in _ATELIER_WINDOW_NAMES.items()},
}
RC2_WINDOW_EFFECTS = {old: f"window-transition/{new}" for old, new in _KINETIC_WINDOW_NAMES.items()}

_ATELIER_TEXT_CONTROLS = {
    "durationMs": "durationMs", "delayMs": "delayMs", "staggerMs": "staggerMs",
    "batchSize": "batchSize", "seed": "seed", "travelRows": "distance",
    "spreadColumns": "scatter", "drift": "wind", "speedJitter": "variation",
    "alphabet": "alphabet", "cycleHz": "scrambleHz", "easing": "easing",
    "reverseOrder": "reverseOrder", "randomOrder": "randomOrder",
    "trailLength": "trailLength", "overshoot": "overshoot", "turns": "cycles",
    "hueSpread": "hueSpread", "local": "local",
}
_TEXT_DEFAULTS = {
    "durationMs": 1200, "delayMs": 0, "staggerMs": 28, "batchSize": 1,
    "seed": 6137, "travelRows": 13, "spreadColumns": 8, "drift": 2,
    "speedJitter": .55,
    "alphabet": " 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!?+-*/",
    "cycleHz": 18, "easing": "smooth", "reverseOrder": False,
    "randomOrder": False, "trailLength": 2, "overshoot": 1.2, "turns": 1.5,
    "hueSpread": 110, "local": False,
}
_KINETIC_TEXT_DEFAULTS = {
    "durationMs": 1200, "delayMs": 0, "staggerMs": 24, "jitterMs": 360,
    "batchSize": 1, "seed": 2030, "distance": 18, "scatter": 5,
    "variation": .4, "wind": 1.3, "cycles": 3, "overshoot": .2,
    "scrambleHz": 24, "hueSpread": 10, "alphabet": " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+-*/!?",
    "easing": "smooth", "reverseOrder": False, "randomOrder": False,
    "trailLength": 0, "local": False,
}
_KINETIC_TEXT_CONTROLS = {name: name for name in _KINETIC_TEXT_DEFAULTS}
_TEXT_EFFECT_ALIASES = {name: f"atelier/{name}" for name in ATELIER_TEXT_EFFECTS}
_TEXT_EFFECT_ALIASES.update({f"text/{name}": f"kinetic/{name}" for name in (
    "immediate", "fade", "rain", "scramble", "flipboard", "sweep-left",
    "sweep-right", "marquee", "orbit", "constellation", "prism-stitch",
    "gravity-loom", "scanline", "elastic", "typewriter", "curtain", "fall", "ash")})

_PROMPT_MODES = {"marquee", "grow", "vim-inline", "vim-full"}
_PROMPT_DEFAULTS = {
    "alpha": .32, "background": "#10161e", "foreground": "#dedbd2",
    "accent": "#8ccfc4", "border": "rounded", "paddingX": 1,
    "paddingY": 0, "margin": 1, "minRows": 1, "maxRows": 7,
    "inlineRows": 12, "inlineWidth": 88, "lineNumbers": True,
    "active": True, "selected": False, "hueStep": 0, "hueSpeed": 0,
    "huePeriodMs": 1000, "maxChars": 0, "selectionColor": "#385763",
}
_PROMPT_LIMITS = {
    "alpha": (0, 1), "paddingX": (0, 8), "paddingY": (0, 4),
    "margin": (0, 6), "minRows": (1, 24), "maxRows": (1, 60),
    "inlineRows": (5, 80), "inlineWidth": (24, 240),
    "hueStep": (-360, 360), "hueSpeed": (-360, 360),
    "huePeriodMs": (1, 120000), "maxChars": (0, 0x7fffffff),
}
_PROMPT_COLORS = {"background", "foreground", "accent", "selectionColor"}
_PROMPT_BORDERS = {"none", "rounded", "square", "double", "heavy"}


def atelier_prompt_command(mode: str = "marquee",
                           options: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Map the original Atelier prompt controls onto an RC4 prompt command.

    The explicit framed presentation restores RC2's authored border, heading,
    prefix and mode-specific geometry. Direct RC4 callers that omit this field
    retain their existing compact presentation and defaults.
    """
    if mode not in _PROMPT_MODES:
        raise ValueError(f"Unknown historical prompt mode: {mode}")
    values = dict(_PROMPT_DEFAULTS)
    if options is not None and not isinstance(options, Mapping):
        raise ValueError("prompt options must be a mapping")
    supplied = dict(options or {})
    allowed = set(_PROMPT_DEFAULTS) | {"padding"}
    unknown = supplied.keys() - allowed
    if unknown:
        raise ValueError(f"Unknown historical prompt controls: {', '.join(sorted(unknown))}")
    if "padding" in supplied:
        padding = supplied["padding"]
        _integer(padding, "padding", 0, 8)
        values["paddingX"] = padding
        values["paddingY"] = padding
    values.update({key: value for key, value in supplied.items() if key != "padding"})
    for key, (low, high) in _PROMPT_LIMITS.items():
        value = values[key]
        if key in {"alpha", "hueStep", "hueSpeed"}:
            _finite(value, key, low, high)
        else:
            _integer(value, key, low, high)
    if values["minRows"] > values["maxRows"]:
        raise ValueError("minRows must not exceed maxRows")
    for key in _PROMPT_COLORS:
        if not isinstance(values[key], str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", values[key]):
            raise ValueError(f"{key} must be a six-digit RGB hex color")
    if values["border"] not in _PROMPT_BORDERS:
        raise ValueError("border must be one of none, rounded, square, double, heavy")
    for key in ("lineNumbers", "active", "selected"):
        if not isinstance(values[key], bool):
            raise ValueError(f"{key} must be boolean")
    return {"op": "prompt", "mode": mode, "presentation": "framed", **values}
def _finite(value: Any, name: str, low: float, high: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f"{name} must be finite and in {low}..{high}")
    return value


def _integer(value: Any, name: str, low: int, high: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}")
    return value


def _text_style(effect: str) -> tuple[str, str]:
    key = _TEXT_EFFECT_ALIASES.get(effect, effect)
    if key in TEXT_TRANSITIONS:
        return key.split("/", 1)[0], TEXT_TRANSITIONS[key]
    raise ValueError(f"Unknown historical text effect: {effect}")


def atelier_text_command(text: str, effect: str, options: Mapping[str, Any] | None = None,
                         *, identity: int = 1, x: int = 3, y: int = 8,
                         width: int = 100, phase: str = "show") -> dict[str, Any]:
    """Translate an old Atelier/Kinetic text actor into one native SDK command."""
    family, native_effect = _text_style(effect)
    if not isinstance(text, str) or len(text) > 32768:
        raise ValueError("text must be a string of at most 32768 code points")
    if phase not in ("show", "hide"):
        raise ValueError("phase must be show or hide")
    for name, value, lo, hi in (("identity", identity, 1, 65535), ("x", x, -4096, 4096),
                                ("y", y, -4096, 4096), ("width", width, 1, 4096)):
        if isinstance(value, bool) or not isinstance(value, int) or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in {lo}..{hi}")
    supplied = dict(options or {})
    controls = _ATELIER_TEXT_CONTROLS if family == "atelier" else _KINETIC_TEXT_CONTROLS
    defaults = _TEXT_DEFAULTS if family == "atelier" else _KINETIC_TEXT_DEFAULTS
    unknown = supplied.keys() - controls.keys()
    if unknown:
        raise ValueError(f"Unknown historical text controls: {', '.join(sorted(unknown))}")
    values = {**defaults, **supplied}
    for name in ("durationMs", "delayMs", "staggerMs"):
        _finite(values[name], name, 0, 60000 if name != "staggerMs" else 10000)
    if family == "kinetic":
        _finite(values["jitterMs"], "jitterMs", 0, 10000)
    for name, lo, hi in (("batchSize", 1, 128), ("seed", 0, 0xffffffff),
                         ("trailLength", 0, 8)):
        value = values[name]
        if isinstance(value, bool) or not isinstance(value, int) or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in {lo}..{hi}")
    numeric_ranges = (("travelRows", 0, 100), ("spreadColumns", 0, 120),
                      ("drift", -100, 100), ("speedJitter", 0, 2),
                      ("cycleHz", 0, 120), ("overshoot", 0, 3),
                      ("turns", 0, 50), ("hueSpread", -360, 360)) if family == "atelier" else (
                      ("distance", 0, 100), ("scatter", 0, 120), ("variation", 0, 2),
                      ("wind", -100, 100), ("cycles", 0, 50), ("overshoot", 0, 3),
                      ("scrambleHz", 0, 120), ("hueSpread", -360, 360))
    for name, lo, hi in numeric_ranges:
        _finite(values[name], name, lo, hi)
    if values["easing"] not in ("linear", "ease-in", "ease-out", "smooth", "smoother", "sine", "step", "cubic", "back", "bounce"):
        raise ValueError("Unknown historical text easing")
    for name in ("local", "reverseOrder", "randomOrder"):
        if not isinstance(values[name], bool):
            raise ValueError(f"{name} must be boolean")
    if not isinstance(values["alphabet"], str) or not 1 <= len(values["alphabet"]) <= 256:
        raise ValueError("alphabet must contain 1..256 Unicode scalars")
    command = {"op": "text", "id": identity, "text": text, "effect": native_effect,
               "phase": phase, "x": x, "y": y, "width": width}
    if family in ("kinetic", "atelier"):
        # Historical text routes select original pose/palette/cell
        # painting. Unused material 15 carries the source defaults; applications
        # may configure it with the ordinary retained material command.
        command["phaseModel"] = "source-paint"
        command["material"] = 15
    if family == "atelier":
        for old_name, native_name in _ATELIER_TEXT_CONTROLS.items():
            command[native_name] = values[old_name]
    else:
        command.update(values)
    return command


def _window_style(effect: str) -> tuple[str, str]:
    if effect in SPATIAL_WINDOW_EFFECTS:
        return effect.split("/", 1)[0], SPATIAL_WINDOW_EFFECTS[effect]
    if effect.startswith("window/"):
        parts = effect.split("/")
        key = "/".join(parts[1:]) if len(parts) == 3 else ""
        if key in SPATIAL_WINDOW_EFFECTS:
            return key.split("/", 1)[0], SPATIAL_WINDOW_EFFECTS[key]
    if effect in RC2_WINDOW_EFFECTS:
        return "kinetic", RC2_WINDOW_EFFECTS[effect]
    raise ValueError(f"Unknown historical spatial window effect: {effect}")


_WINDOW_SHAPES = {"rectangle", "rounded", "ellipse", "hexagon", "diamond", "capsule",
                  "ticket", "squircle", "petal", "wave", "cloud", "polygon"}
_RC2_WINDOW_SHAPES = _WINDOW_SHAPES - {"cloud", "polygon"}


def atelier_window_command(identity: str, effect: str, *, title: str = "ATELIER / WORKSPACE",
                           text: str = "A spatial surface for the original application.",
                           position: Sequence[float] = (0, 0, 0), width: float = 30,
                           height: float = 16, duration_ms: int | None = None,
                           shape: str | None = None, seed: int | None = None,
                           **controls: Any) -> dict[str, Any]:
    """Build one retained native window using the matching historical geometry."""
    family, native_effect = _window_style(effect)
    if not isinstance(identity, str) or not re.fullmatch(r"[\w.-]{1,64}", identity):
        raise ValueError("identity must be a 1..64 character native window key")
    if not isinstance(title, str) or not isinstance(text, str):
        raise ValueError("title and text must be strings")
    if shape is not None and shape not in _WINDOW_SHAPES:
        raise ValueError(f"Unknown native window shape: {shape}")
    if family == "kinetic" and shape is not None and shape not in _RC2_WINDOW_SHAPES:
        raise ValueError(f"Shape is not supported by the original RC2 window contract: {shape}")
    if len(position) != 3:
        raise ValueError("position must contain three coordinates")
    p = [_finite(v, "position", -4096, 4096) for v in position]
    w = _finite(width, "width", 2, 256); h = _finite(height, "height", 2, 256)
    defaults = ({"duration": 850, "seed": 2030, "alpha": .85, "overshoot": .18,
                 "folds": 6, "scatter": 32, "anchorX": .5, "anchorY": 1.15,
                 "bend": 9} if family == "kinetic" else
                {"duration": 950, "seed": 6001, "alpha": .88, "overshoot": .18,
                 "folds": 6, "scatter": 24, "anchorX": .5, "anchorY": 1.15,
                 "bend": 9})
    duration_ms = defaults["duration"] if duration_ms is None else duration_ms
    shape = shape or "rounded"
    seed = defaults["seed"] if seed is None else seed
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed <= 0xffffffff:
        raise ValueError("seed must be a uint32")
    if isinstance(duration_ms, bool) or not isinstance(duration_ms, (int, float)) or not math.isfinite(duration_ms) or not 0 <= duration_ms <= 5000:
        raise ValueError("duration_ms must be finite and in 0..5000")
    values = dict(defaults)
    values.pop("duration")
    values.update({"durationMs": duration_ms})
    values["seed"] = seed
    aliases = {"opacity": "alpha"}
    if family == "kinetic":
        aliases.update({"explosionDistance": "scatter"})
        source_ranges = {"opacity": (0, 1), "depthFade": (0, .08), "overshoot": (0, .7),
                         "folds": (1, 20), "explosionDistance": (0, 100),
                         "anchorX": (-2, 3), "anchorY": (-2, 3),
                         "controlWidth": (5, 15), "controlHeight": (3, 6)}
    else:
        aliases.update({"bounce": "overshoot", "genieBend": "bend"})
        source_ranges = {"opacity": (0, 1), "depth": (-12, 70), "yaw": (-70, 70),
                         "pitch": (-65, 65), "roll": (-60, 60), "fadeFloor": (0, 1),
                         "bounce": (0, .6), "scatter": (0, 80), "genieBend": (-30, 30)}
    direct = {"anchorX", "anchorY", "overshoot", "scatter", "bend", "folds", "alpha",
              "material", "border", "padding", "chromeSize", "minColumns", "maxColumns",
              "fadeStartRatio", "fadeEndRatio", "polygon", "yaw", "pitch", "roll"}
    source_fields = {"depthFade", "chrome", "controlWidth", "controlHeight", "customSide",
                     "customOrder", "customGlyphs", "sourcePresentation"}
    accepted = direct | set(source_ranges) | {"sourcePresentation"} | (
        source_fields - {"sourcePresentation"} if family == "kinetic" else set())
    unknown = controls.keys() - accepted
    if unknown:
        raise ValueError(f"Unknown historical window controls: {', '.join(sorted(unknown))}")
    for source_name, (low, high) in source_ranges.items():
        if source_name in controls:
            if source_name in {"folds", "controlWidth", "controlHeight"}:
                _integer(controls[source_name], source_name, int(low), int(high))
            else:
                _finite(controls[source_name], source_name, low, high)
    source_only = {"depthFade", "chrome", "controlWidth", "controlHeight", "customSide",
                   "customOrder", "customGlyphs"}
    source_presentation = family == "kinetic"
    if "sourcePresentation" in controls:
        source_presentation = controls["sourcePresentation"]
        if not isinstance(source_presentation, bool):
            raise ValueError("sourcePresentation must be a boolean")
        if family == "atelier" and source_presentation:
            raise ValueError("sourcePresentation is only available for RC2 windows")
    if family == "kinetic":
        if not source_presentation and source_only.intersection(controls):
            raise ValueError("source-only controls cannot accompany sourcePresentation=False")
        if "chrome" in controls and controls["chrome"] not in {"mac", "windows", "gnome", "custom"}:
            raise ValueError("chrome must be mac, windows, gnome, or custom")
        if "customSide" in controls and controls["customSide"] not in {"left", "right"}:
            raise ValueError("customSide must be left or right")
        action_names = {"minimize", "maximize", "background", "close"}
        if "customOrder" in controls:
            order = controls["customOrder"]
            if not isinstance(order, str):
                raise ValueError("customOrder must be a comma-separated string")
            entries = order.split(",")
            if len(entries) != 4 or set(entries) != action_names:
                raise ValueError("customOrder must contain each window action exactly once")
        if "customGlyphs" in controls:
            glyphs = controls["customGlyphs"]
            if not isinstance(glyphs, str):
                raise ValueError("customGlyphs must be a comma-separated string")
            entries = glyphs.split(",")
            if len(entries) != 4 or any(
                len(glyph) != 1 or 0xD800 <= ord(glyph) <= 0xDFFF or
                ord(glyph) < 0x20 or 0x7F <= ord(glyph) <= 0x9F
                for glyph in entries
            ):
                raise ValueError("customGlyphs must contain four single printable scalars")
    for native_name in direct:
        if native_name in controls and native_name not in source_ranges and native_name not in {"opacity", "depthFade", "explosionDistance", "bounce", "genieBend", "depth", "fadeFloor"}:
            # Native control bounds are still checked by the command parser; type
            # check here so a malformed adapter call fails before emission.
            value = controls[native_name]
            if native_name in {"material", "padding", "chromeSize", "minColumns", "maxColumns", "folds"}:
                if isinstance(value, bool) or not isinstance(value, int):
                    raise ValueError(f"{native_name} must be an integer")
            elif native_name != "polygon" and native_name != "border":
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                    raise ValueError(f"{native_name} must be finite")
    for old_name, new_name in aliases.items():
        if old_name in controls:
            if new_name in controls:
                raise ValueError(f"Specify only one of {old_name} or {new_name}")
            values[new_name] = controls[old_name]
    if family == "kinetic" and "explosionDistance" in controls:
        values["scatter"] = controls["explosionDistance"]
    if family == "atelier" and "depth" in controls:
        p[2] += _finite(controls["depth"], "depth", -12, 70)
    unsupported_semantics = set(controls) & {"fadeFloor", "chromeSize"}
    if unsupported_semantics:
        raise ValueError(f"Window controls need retained application semantics: {', '.join(sorted(unsupported_semantics))}")
    command = {"op": "window", "id": sum((i + 1) * b for i, b in enumerate(identity.encode("utf-8"))) % 65535 or 1,
               "title": title, "text": text, "effect": native_effect, "shape": shape,
               "position": p, "width": w, "height": h, "durationMs": duration_ms,
               "sourceGeometry": True, "seed": seed}
    command["sourcePresentation"] = source_presentation
    if family == "kinetic":
        if source_presentation:
            command.update({
                "depthFade": .008, "chrome": "mac", "controlWidth": 10,
                "controlHeight": 3, "customSide": "right",
                "customOrder": "minimize,maximize,background,close",
                "customGlyphs": "−,□,◇,×",
            })
    if family == "atelier" and shape == "polygon" and "polygon" not in controls:
        command["polygon"] = [[.05,.2],[.35,0],[.9,.12],[1,.8],[.65,1],[0,.85]]
    command.update(values)
    for key in direct:
        if key in controls:
            command[key] = controls[key]
    if family == "kinetic":
        for key in source_only.intersection(controls):
            command[key] = controls[key]
    for alias in aliases:
        if alias in controls:
            target = aliases[alias]
            if target not in {"durationMs"}:
                command[target] = controls[alias]
    command.setdefault("alpha", defaults["alpha"])
    return command


_RC2_WINDOW_ITEM_DEFAULTS = {
    "x": 0, "y": 0, "z": 0, "width": 30, "height": 16,
    "yaw": 0, "pitch": 0, "roll": 0,
    "content": "A surface for your application.",
}
_RC2_WINDOW_ITEM_FIELDS = {"id", "title", "content", "x", "y", "z", "width",
                           "height", "yaw", "pitch", "roll", "shape"}
_RC2_WINDOW_APPEARANCE_FIELDS = {
    "effect", "durationMs", "chrome", "shape", "opacity", "depthFade", "overshoot",
    "folds", "explosionDistance", "anchorX", "anchorY", "controlWidth",
    "controlHeight", "customSide", "customOrder", "customGlyphs", "seed",
}
_RC2_RASTER_DEFAULTS = {
    "lightness": .62, "chroma": .14, "brightness": .28, "hueOffset": 0,
    "feather": 1, "textLightness": .83, "textChroma": .10,
    "lockLightness": True, "stopWidths": [],
}
_RC2_RASTER_LIMITS = {
    "lightness": (.05, .95), "chroma": (0, .4), "brightness": (0, 1),
    "hueOffset": (-360, 360), "feather": (0, 1),
    "textLightness": (.35, .95), "textChroma": (0, .3),
}
_RC2_PALETTE_DEFAULTS = {
    "id": "smart-dark", "name": "Smart Dark / Velvet Circuitry",
    "colors": ["#647795", "#af88bb", "#69a9a5", "#b89477", "#73709f"],
    "background": "#101319", "ink": "#dfd8cc",
}


def _rc2_utf16_units(value: str, name: str, limit: int) -> None:
    try:
        units = len(value.encode("utf-16-le", "strict")) // 2
    except UnicodeEncodeError as error:
        raise ValueError(f"{name} must contain Unicode scalar values") from error
    if units > limit:
        raise ValueError(f"{name} exceeds {limit} UTF-16 units")


def _rc2_palette_rgb(value: Any, name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be an RGB integer or #RRGGBB")
    if isinstance(value, int) and 0 <= value <= 0xffffff:
        return value
    if isinstance(value, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        return int(value[1:], 16)
    raise ValueError(f"{name} must be an RGB integer or #RRGGBB")


def rc2_window_commands(item: Mapping[str, Any], *, source_index: int = 0,
                        options: Mapping[str, Any] | None = None,
                        palette: Mapping[str, Any] | None = None,
                        appearance: Mapping[str, Any] | None = None,
                        waveform: Sequence[float] | None = None,
                        native_id: int | None = None) -> list[dict[str, Any]]:
    """Translate one original RC2 authored window into retained native commands.

    The initial item is visible immediately, as it is after `WindowManager.add`.
    Its configured duration is restored in a third command so later actions keep
    the RC2 timing without inventing an opening transition. The source Z axis is
    reflected once for the native source-camera convention.
    """
    if not isinstance(item, Mapping):
        raise ValueError("window item must be a mapping")
    values = dict(item)
    if any(not isinstance(key, str) for key in values):
        raise ValueError("window item keys must be strings")
    unknown = values.keys() - _RC2_WINDOW_ITEM_FIELDS
    if unknown:
        raise ValueError(f"Unknown RC2 window item fields: {', '.join(sorted(unknown))}")
    identity = values.get("id")
    title = values.get("title")
    if not isinstance(identity, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", identity):
        raise ValueError("window item id must be 1..64 ASCII word, dot, or dash characters")
    if not isinstance(title, str):
        raise ValueError("window item title must be a string")
    _rc2_utf16_units(title, "window title", 160)
    text = values.get("content", _RC2_WINDOW_ITEM_DEFAULTS["content"])
    if text is None:
        text = _RC2_WINDOW_ITEM_DEFAULTS["content"]
    if not isinstance(text, str):
        raise ValueError("window content must be a string")
    _rc2_utf16_units(text, "window content", 4096)
    pose: dict[str, float] = {}
    for key, default in _RC2_WINDOW_ITEM_DEFAULTS.items():
        if key == "content":
            continue
        value = values.get(key, default)
        low, high = ((2, 100) if key in {"width", "height"} else (-1000, 1000))
        pose[key] = _finite(value, key, low, high)
    if "shape" in values and (not isinstance(values["shape"], str) or
                               values["shape"] not in _RC2_WINDOW_SHAPES):
        raise ValueError("window shape is not supported by the original RC2 contract")

    source_index = _integer(source_index, "source_index", 0, 31)
    if native_id is not None:
        native_id = _integer(native_id, "native_id", 1, 65535)

    if options is not None and not isinstance(options, Mapping):
        raise ValueError("observatory raster options must be a mapping")
    raster = dict(_RC2_RASTER_DEFAULTS)
    supplied_options = dict(options or {})
    if any(not isinstance(key, str) for key in supplied_options):
        raise ValueError("observatory option names must be strings")
    unknown = supplied_options.keys() - _RC2_RASTER_DEFAULTS.keys()
    if unknown:
        raise ValueError(f"Unsupported generated-window observatory options: {', '.join(sorted(unknown))}")
    raster.update(supplied_options)
    for key, (low, high) in _RC2_RASTER_LIMITS.items():
        raster[key] = _finite(raster[key], key, low, high)
    if not isinstance(raster["lockLightness"], bool):
        raise ValueError("lockLightness must be boolean")
    stop_widths = raster["stopWidths"]
    if not isinstance(stop_widths, (list, tuple)) or len(stop_widths) > 32:
        raise ValueError("stopWidths must contain zero to 32 intervals")
    raster["stopWidths"] = [_finite(width, "stop width", .05, 16) for width in stop_widths]

    if palette is not None and not isinstance(palette, Mapping):
        raise ValueError("palette must be a mapping")
    palette_values = dict(_RC2_PALETTE_DEFAULTS)
    supplied_palette = dict(palette or {})
    if any(not isinstance(key, str) for key in supplied_palette):
        raise ValueError("palette keys must be strings")
    unknown = supplied_palette.keys() - set(_RC2_PALETTE_DEFAULTS)
    if unknown:
        raise ValueError(f"Unknown RC2 palette fields: {', '.join(sorted(unknown))}")
    palette_values.update(supplied_palette)
    for key in ("id", "name"):
        if not isinstance(palette_values[key], str) or not palette_values[key]:
            raise ValueError(f"palette {key} must be a non-empty string")
    colors = palette_values["colors"]
    if not isinstance(colors, (list, tuple)) or not 1 <= len(colors) <= 32:
        raise ValueError("palette colors must contain one to 32 stops")
    colors = [_rc2_palette_rgb(color, "palette stop") for color in colors]
    background = _rc2_palette_rgb(palette_values["background"], "palette background")
    ink = _rc2_palette_rgb(palette_values["ink"], "palette ink")

    if appearance is not None and not isinstance(appearance, Mapping):
        raise ValueError("window appearance must be a mapping")
    appearance_values = dict(appearance or {})
    if any(not isinstance(key, str) for key in appearance_values):
        raise ValueError("window appearance names must be strings")
    unknown = appearance_values.keys() - _RC2_WINDOW_APPEARANCE_FIELDS
    if unknown:
        raise ValueError(f"Unknown RC2 window appearance fields: {', '.join(sorted(unknown))}")
    effect = appearance_values.get("effect", "genie")
    if not isinstance(effect, str):
        raise ValueError("window effect must be an original RC2 effect name")
    duration = appearance_values.get("durationMs", 850)
    appearance_shape = appearance_values.get("shape", "rounded")
    if not isinstance(appearance_shape, str) or appearance_shape not in _RC2_WINDOW_SHAPES:
        raise ValueError("window appearance shape is not supported by the original RC2 contract")
    shape = values.get("shape", appearance_shape)
    seed = appearance_values.get("seed", 2030)
    controls = {key: value for key, value in appearance_values.items()
                if key not in {"effect", "durationMs", "shape", "seed"}}
    # The ordinary window document is capped at 2048 Unicode scalars. Keep it
    # as a remove-content fallback only when the complete generated body fits;
    # otherwise an empty base document lets window-content own all 4096 units.
    base_text = text if len(text) <= 2048 else ""
    _, configured_native_effect = _window_style(effect)
    window = atelier_window_command(
        identity, "fade", title=title, text=base_text,
        position=(pose["x"], pose["y"], -pose["z"]),
        width=pose["width"], height=pose["height"], duration_ms=0,
        shape=shape, seed=seed, yaw=pose["yaw"], pitch=pose["pitch"],
        roll=pose["roll"], **controls,
    )
    window_id = window["id"] if native_id is None else native_id
    window["id"] = window_id

    if waveform is None:
        samples = [0.0] * 128
    elif not isinstance(waveform, Sequence) or isinstance(waveform, (str, bytes)) or len(waveform) != 128:
        raise ValueError("waveform must contain exactly 128 samples")
    else:
        samples = [_finite(value, "waveform sample", -32, 32) for value in waveform]
    content = {
        "op": "window-content", "id": window_id, "label": identity,
        "sourceIndex": source_index, "text": text, "colors": colors,
        "stopWidths": raster["stopWidths"], "background": background, "ink": ink,
        **{key: raster[key] for key in _RC2_RASTER_LIMITS},
        "lockLightness": raster["lockLightness"], "waveform": samples,
    }
    duration_patch = {
        "op": "window", "id": window_id, "effect": configured_native_effect,
        "durationMs": _finite(duration, "durationMs", 0, 5000),
    }
    return [window, content, duration_patch]


def atelier_application_commands(*, text: str, text_effect: str, window_effect: str,
                                 draft: str, window_identity: str = "atelier-window",
                                 position: Sequence[float] = (0, 0, 0),
                                 prompt_mode: str = "marquee",
                                 prompt_options: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    """Compose historical choreography with the always-local prompt document.

    Native UI draws the prompt after spatial window contents, so draft editing
    stays immediate and recoverable while the decorative text actor animates.
    """
    return [
        {"op": "resize", "width": 100, "height": 40},
        {"op": "environment", "stars": 0},
        atelier_prompt_command(prompt_mode, prompt_options),
        {"op": "draft", "text": draft, "emitWeather": False},
        atelier_window_command(window_identity, window_effect, title="ATELIER / SIGNAL DESK",
                               text="Original motion, native ownership.\nLocal input stays viewer-facing.",
                               position=position, width=36, height=18),
        atelier_text_command(text, text_effect, identity=91, x=5, y=8, width=90),
    ]
