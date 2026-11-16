# Observatory controls

Generated from executable constraints. Numeric options use the exact units below; clamp only where explicitly documented, otherwise invalid values reject.

| Field | Meaning | Range | Default | Unit |
|---|---|---:|---:|---|
| `fps` | Presentation ceiling | 1..120 | 60 | fps |
| `gradientScreens` | Distance between adjacent stops | 0.05..8 | 0.75 | screens |
| `gradientAngle` | Primary angle | -360..360 | -18 | degrees |
| `gradientSpeed` | Gradient travel | -2..2 | 0.06 | screens/s |
| `gradientPhase` | Phase | -8..8 | 0 | screens |
| `feather` | Transition feather | 0..1 | 1 | dimensionless |
| `pivotX` | Pivot X / outside is allowed | -3..4 | 0.5 | screens |
| `pivotY` | Pivot Y | -3..4 | 0.5 | screens |
| `axisPitch` | Second-axis starting tilt | -180..180 | 20 | degrees |
| `rotationSpeed` | Primary-axis rotation | -90..90 | 4 | degrees/s |
| `secondAxisSpeed` | Second-axis rotation | -90..90 | 2 | degrees/s |
| `swingAngle` | Pendulum half-swing | 0..180 | 60 | degrees |
| `swingSeconds` | Pendulum full cycle | 0.5..90 | 16 | seconds |
| `lightness` | Oklab lightness L | 0.05..0.95 | 0.62 | dimensionless |
| `chroma` | OKLCh chroma ceiling | 0..0.4 | 0.14 | dimensionless |
| `brightness` | Background mix | 0..1 | 0.28 | dimensionless |
| `hueOffset` | Hue offset | -360..360 | 0 | degrees |
| `textLightness` | Text lightness | 0.35..0.95 | 0.83 | dimensionless |
| `textChroma` | Text chroma | 0..0.3 | 0.1 | dimensionless |
| `hueStep` | Adjacent character hue distance | -90..90 | 13 | degrees |
| `textHueSpeed` | Text hue sweep | -90..90 | 12 | degrees/s |
| `arrivalMs` | Remote text arrival | 0..2500 | 520 | ms |
| `topFade` | Top-edge attenuation | 0..0.65 | 0.18 | dimensionless |
| `fallMs` | Falling glyph travel | 0..4000 | 1100 | ms |
| `tickerSpeed` | Ticker velocity | 0..30 | 7 | cells/s |
| `starDensity` | Twinkle occupation | 0..0.3 | 0.035 | dimensionless |
| `starCount` | Warp points | 0..1200 | 420 | dimensionless |
| `starSpeed` | Travel velocity | 0..40 | 5 | units/s |
| `trailMs` | Trail exposure | 0..250 | 65 | ms |
| `novaRegularity` | Automatic nova cadence | 0..60 | 3 | per minute |
| `novaStrength` | Nova glow | 0..1 | 0.28 | dimensionless |
| `cameraYaw` | Camera yaw | -180..180 | 0 | degrees |
| `cameraPitch` | Camera pitch | -89..89 | 0 | degrees |
| `cameraRoll` | Camera roll | -180..180 | 0 | degrees |
| `cameraX` | Camera X | -30..30 | 0 | dimensionless |
| `cameraY` | Camera Y | -30..30 | 0 | dimensionless |
| `cameraZ` | Camera Z | -30..30 | 0 | dimensionless |
| `travelYaw` | Travel heading | -180..180 | 0 | degrees |
| `travelPitch` | Travel elevation | -89..89 | 0 | degrees |
| `fov` | Horizontal field of view | 25..120 | 70 | degrees |
| `weatherIntensity` | Keystroke / pointer weather | 0..1 | 0.38 | dimensionless |
| `weatherLifeMs` | Weather lifetime | 200..8000 | 2400 | ms |
| `weatherSpeed` | Weather propagation | 1..50 | 12 | cells/s |
| `windowOpacity` | Window background opacity | 0..1 | 0.78 | dimensionless |
| `transitionMs` | Window transition | 0..2000 | 560 | ms |
| `ruleSpeed` | Rule motion | 0..30 | 6 | cells/s |
| `scopeGain` | Scope gain | 0.1..10 | 1 | dimensionless |
| `sensorAttack` | Routing attack | 0..2000 | 60 | ms |
| `sensorRelease` | Routing release | 0..5000 | 420 | ms |

## Enumerations

**backgroundStyle:** `linear`, `double-axis`, `wave`, `plasma`, `caustics`, `vortex`, `contours`, `aurora`, `woven`, `moire`, `tunnel`, `diamond`, `bilinear`, `checker`, `warp`.

**weatherStyle:** `ripples`, `rain`, `snow`, `embers`, `sparks`, `nova`.

**orbitMode:** `spin`, `pendulum`.

**sampling:** `cell`, `half`, `vertical`, `braille`.

## Policies and arrays

`lockLightness` holds intended gradient L while hue moves. `flatNavigation` selects 2D graph/menu layout. `typedColor` assigns neighboring typed characters separate hues without fading their ink. `motion` controls host decorative pause, not data mutation.

`stopWidths` holds positive per-stop distance weights, at most 32. `starGlyphs` supplies the ordinary stable single-cell glyph family; quotes/colons/multidot patterns are not defaults. Palettes support explicit colors, background and ink.

## Modulation targets

`brightness`, `lightness`, `chroma`, `hueOffset`, `gradientSpeed`, `rotationSpeed`, `secondAxisSpeed`, `starCount`, `starSpeed`, `starDensity`, `novaRegularity`, `weatherIntensity`, `scopeGain`, `windowOpacity`, `gradientScreens`, `gradientAngle`, `axisPitch`, `pivotX`, `pivotY`, `cameraYaw`, `cameraPitch`, `cameraRoll`, `cameraX`, `cameraY`, `cameraZ`, `travelYaw`, `travelPitch`, `trailMs`, `weatherSpeed`, `tickerSpeed`, `hueStep`, `textHueSpeed`

A route may target numeric properties only. UI control values are baseline configuration; active source routes can temporarily override them. TTL expiry restores those baselines. Stop widths, glyph families and discrete scene choices are intentionally not interpolated by a scalar sensor.

## Recipes

- **Velvet circuitry** (`velvet`): chat / smart-dark.
- **Oblique hyperlane** (`hyperlane`): warp / stellar.
- **Copper orbital** (`copper-orbit`): dag / copper.
- **Pearl signal** (`pearl-wave`): scope / pearl.
- **Neon exchange** (`neon-bbs`): bbs / neon-dreams.
- **Millennial maintenance** (`millennial`): bbs-config / millennial-gray.
- **Gold glass** (`gold-glass`): windows / gold.
- **Software after hours** (`blueprint`): tmux / saas-blue.
- **Winterfall** (`winterfall`): text / winter.
- **Hotline signal** (`hotline`): sensors / hotline.
- **Opal pendulum** (`opal-pendulum`): spatial-menu / opal.
- **Phosphor correspondence** (`phosphor`): pico / phosphor.
