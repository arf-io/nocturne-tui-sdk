# Spatial Atelier control reference

Generated from executable defaults and bounds. Ranges describe accepted numbers; units are listed in the API guide. Settings are JSON, not code.

## Text

| Field | Default | Range | UI step |
|---|---|---|---|
| `durationMs` | 1200 | 0..10000 | 25 |
| `delayMs` | 0 | 0..5000 | 25 |
| `staggerMs` | 28 | 0..500 | 5 |
| `batchSize` | 1 | 1..64 | 1 |
| `seed` | 6137 | 0..4294967295 | 1 |
| `travelRows` | 13 | 0..80 | 0.5 |
| `spreadColumns` | 8 | 0..80 | 0.5 |
| `drift` | 2 | -30..30 | 0.25 |
| `speedJitter` | 0.55 | 0..0.95 | 0.05 |
| `cycleHz` | 18 | 1..60 | 1 |
| `trailLength` | 2 | 0..8 | 1 |
| `overshoot` | 1.2 | 0..3 | 0.1 |
| `turns` | 1.5 | 0..8 | 0.1 |
| `hueSpread` | 110 | 0..360 | 5 |

Other defaults:
```json
{
  "effect": "rain",
  "alphabet": " 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!?+-*/",
  "easing": "smooth",
  "reverseOrder": false,
  "randomOrder": false,
  "local": false
}
```

## Particles

| Field | Default | Range | UI step |
|---|---|---|---|
| `lifeMs` | 4200 | 200..10000 | 50 |
| `count` | 64 | 0..256 | 1 |
| `speed` | 20 | 0..70 | 0.5 |
| `gravity` | 9 | 0..35 | 0.5 |
| `rise` | 10 | 0..40 | 0.5 |
| `drag` | 0.22 | 0..3 | 0.05 |
| `turbulence` | 1.3 | 0..8 | 0.1 |
| `glitterHz` | 14 | 1..30 | 1 |
| `trailMs` | 100 | 0..400 | 10 |
| `branches` | 7 | 1..20 | 1 |
| `jaggedness` | 2.2 | 0..8 | 0.1 |
| `coreMs` | 280 | 0..600 | 10 |
| `coreRadius` | 3 | 0..6 | 0.1 |
| `ejecta` | 1 | 0..2 | 0.05 |
| `shockwave` | 0 | 0..1 | 0.02 |
| `intensity` | 0.8 | 0..1 | 0.02 |
| `seed` | 4711 | 0..4294967295 | 1 |

Other defaults:
```json
{
  "reducedMotion": false
}
```

## Windows

| Field | Default | Range | UI step |
|---|---|---|---|
| `durationMs` | 950 | 0..5000 | 25 |
| `toolWidth` | 6 | 5..10 | 1 |
| `toolHeight` | 2 | 2..4 | 1 |
| `opacity` | 0.88 | 0..1 | 0.02 |
| `depth` | 0 | -12..70 | 1 |
| `yaw` | 0 | -70..70 | 1 |
| `pitch` | 0 | -65..65 | 1 |
| `roll` | 0 | -60..60 | 1 |
| `fadeFloor` | 0.16 | 0..1 | 0.02 |
| `bounce` | 0.18 | 0..0.6 | 0.02 |
| `scatter` | 24 | 0..80 | 1 |
| `genieBend` | 9 | -30..30 | 1 |
| `seed` | 6001 | 0..4294967295 | 1 |

Other defaults:
```json
{
  "effect": "genie",
  "chrome": "mac",
  "customSide": "right",
  "customGlyphs": [
    "–",
    "□",
    "◌",
    "×"
  ],
  "customOrder": [
    "minimize",
    "maximize",
    "fade",
    "close"
  ],
  "toolColors": {
    "minimize": 15318885,
    "maximize": 8377259,
    "fade": 12294885,
    "close": 15698841
  },
  "shape": "rounded",
  "polygon": [
    [
      0.05,
      0.2
    ],
    [
      0.35,
      0
    ],
    [
      0.9,
      0.12
    ],
    [
      1,
      0.8
    ],
    [
      0.65,
      1
    ],
    [
      0,
      0.85
    ]
  ]
}
```

## Layout

```json
{
  "dimensions": 3,
  "algorithm": "layered",
  "seed": 7341,
  "iterations": 180,
  "rankGap": 7,
  "nodeGap": 3,
  "depthGap": 5,
  "repulsion": 42,
  "spring": 0.055,
  "damping": 0.76,
  "cyclePolicy": "condense"
}
```

Limits: 256 nodes, 2048 edges, 1..600 force iterations. Rank spacing includes node dimensions. Pins are exact; pinned overlaps are not corrected. Force/radial layouts are heuristics, not crossing/overlap-free guarantees.

## Camera

The visible console separates look/orbit, translation and starfield travel. Camera position/target uses world units. View and travel angles are degrees. The signed travel range is -40..40 units/s. Numeric camera fields expose target XYZ, yaw/pitch/roll, distance and FOV. Home and Frame all are always reachable.

All original material controls remain defined in `observatory.schema.json`. New scenes use their own particle/text/window settings; duplicated legacy controls that have no effect in those scenes are hidden in the new gallery.
