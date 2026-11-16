# TD Figlet / TheDraw typography

The connector inspected `arf-io/tdfiglet`, feature branch `feature/classic-tdf-full-support`, at **94e212569244229f78b23aade9053940e6dcb6fa**. This is a pinned compatibility target, not a claim that the feature commit is the default branch. No upstream source or fonts are redistributed.

Source: https://github.com/arf-io/tdfiglet/blob/94e212569244229f78b23aade9053940e6dcb6fa/README.md .

```sh
python3 integrations/tdfiglet_bridge.py \
  --binary /absolute/path/to/tdfiglet \
  --font /absolute/path/to/a-font.tdf \
  --subfont 0 \
  --output /tmp/nocturne-title.json \
  NOCTURNE
```

Import the output using the gallery's **TD Figlet / cell art import** control. Use a local font/subfont with coverage for the requested text. There is no assumed valid font filename or random-font selection.

The adapter uses argv, not a shell; requests ANSI/Unicode; adds end-of-options before text; bounds output to8MiB and times out after5s. The line-oriented ANSI parser handles16/256/RGB SGR, strips unsafe control families and converts output to owned cell data with provenance. It is **not a terminal emulator**: cursor-addressed full-screen artwork is not supported. Import bounds are100 columns×24rows.

## Animation

Keep the rendered glyph/color layer and provenance. Recolor/composite it without invoking the font process every frame. The gallery demonstrates a stepped palette cycle over imported art, not a complete TDF animation editor. Native text separately supports per-character hue offset, temporal hue speed, palette cycling, reveal delay and alpha.

`KeyframeTrack` in Python samples explicit scalar tracks using the shared integer tween. Other bindings expose tweening for their own host track management. It can drive position, opacity, value and material parameters within their schema ranges. There is no multi-track editor/serialization standard or font morphing implementation.

`digits` uses **original seven-segment geometry**, not TheDraw art. It supports integer zoom1..4 and color motion. Imported words do not yet have separate per-letter semantic/kerning identities or continuously smooth zoom.

## Verification boundary

Unit tests cover ANSI parsing, control removal, bounds and argv separation. **No actual TD Figlet executable was available locally.** Its process execution/full compatibility cannot be inferred from parser tests. An optional CI job checks out the pinned fork, builds it and renders a nonempty sample, but that workflow has not run remotely in this session. No font files are included.
