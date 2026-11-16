# Studio API / v2

The material renderer, scalar tween, cell compositor and primitive painter are the common cross-language core. The existing v1 API is separate and unchanged. This document describes implemented behavior, not a future framework API.

## Types and bounds

`NsStageConfig`:704bytes; `NsNode`:128bytes; `NsImpulse`:32bytes; `NsCell`:16bytes (`glyph,fg,bg,flags`). Frames are row-major. Positive node IDs provide semantic/hit identity; flags are not a terminal escape or alpha channel. Configuration uses explicit integers and packed24-bit RGB. Bindings accept convenient #RRGGBB colors where documented.

Surface:0..512columns,0..256rows. Node/event coordinates can be offscreen within±4096cells. Scene caps:512nodes,128explicit impulses,32768text scalars,16384data integers. Aggregate numeric data range±1,000,000. Empty surfaces are valid. Time is nonnegative milliseconds; JavaScript safe-integer range is narrower than nativeu64. Angles/positions have explicit units below.

## Material properties

| Key | Default | Range | Meaning |
|---|---:|---|---|
| `width` | 100 | 0..512 | Width in terminal cells. |
| `height` | 32 | 0..256 | Height in terminal cells. |
| `pattern` | 5 | 0..11 | 0 solid; 1 linear; 2 diagonal; 3 wave; 4 rotating linear; 5 plasma; 6 concentric; 7 moire; 8 aurora; 9 interference; 10 chevrons; 11 diamond. |
| `focusMode` | 0 | 0..4 | 0 none; 1 row; 2 column; 3 radial; 4 diagonal band. |
| `focusX` | 12800 | -1048576..1048576 | Focus x in Q8 cells (256 = one column). |
| `focusY` | 4096 | -1048576..1048576 | Focus y in Q8 cells. |
| `periodMs` | 5000 | 50..3600000 | Color field cycle in milliseconds. |
| `saturation` | 700 | 0..2000 | Color saturation in thousandths. |
| `brightness` | 260 | 0..1000 | Field brightness blended from base, in thousandths. |
| `speedFalloff` | 500 | 10..1000 | Speed multiplier for each cell away from focus. |
| `saturationFalloff` | 760 | 0..1000 | Saturation multiplier per cell away from focus. |
| `brightnessFalloff` | 940 | 0..1000 | Brightness multiplier per cell away from focus. |
| `cellAspect` | 2000 | 500..4000 | Cell height / width in thousandths; circles compensate for this. |
| `scale` | 6144 | 64..262144 | Gradient wavelength in Q8 cells. |
| `angle` | 0 | -360000..360000 | Gradient angle in millidegrees. |
| `pivotX` | 12800 | -1048576..1048576 | Rotation axis x in Q8 cells; may lie offscreen. |
| `pivotY` | 4096 | -1048576..1048576 | Rotation axis y in Q8 cells; may lie offscreen. |
| `rotationPeriodMs` | 18000 | 100..3600000 | Independent axis rotation / pendulum period. |
| `rotationMode` | 1 | 0..2 | 0 fixed axis; 1 continuous rotation; 2 eased pendulum. |
| `swing` | 65000 | 0..360000 | Pendulum half-amplitude in millidegrees. |
| `phase` | 0 | -65536..65536 | Color phase in 1/1024 turns. |
| `pixelMode` | 1 | 0..3 | 0 whole cell; 1 upper/lower half; 2 left/right half; 3 braille dither. |
| `seed` | 7319 | 0..2147483647 | Deterministic seed. Stable under resize. |
| `baseColor` | 1118222 | 0..16777215 | Opaque bottom color, packed RGB. |
| `inkColor` | 14866889 | 0..16777215 | Default foreground, packed RGB. |
| `paletteCount` | 5 | 1..32 | Number of configured gradient colors (binding-managed). |
| `gradientWrap` | 0 | 0..2 | 0 seamless loop; 1 mirrored forward/back; 2 hard cyclic stops. |
| `interpolation` | 1 | 0..1 | 0 encoded RGB linear; 1 eased RGB interpolation. |
| `colorMode` | 0 | 0..2 | 0 palette; 1 full HSV wheel; 2 three phase-separated RGB sine channels. |
| `hueOffset` | 0 | -3600..3600 | Hue-wheel offset in degrees. |
| `stars` | 1 | 0..1 | Enable stable-glyph twinkling stars. |
| `starDensity` | 38 | 0..1000 | Chance per cell, in thousandths. |
| `starMinMs` | 4400 | 100..3600000 | Minimum independent star period. |
| `starRangeMs` | 8200 | 0..3600000 | Additional deterministic period range. |
| `starDuty` | 540 | 1..1000 | Visible portion of a star cycle, in thousandths. |
| `starPeak` | 730 | 0..1000 | Peak star opacity relative to its configured peak color. |
| `starGlyphCount` | 12 | 1..32 | Number of chosen ordinary star glyphs. |
| `starColorCount` | 6 | 1..32 | Number of star peak colors. |
| `novaChance` | 30 | 0..1000 | Per world-tile chance per nova cycle, in thousandths. Zero disables automatic novae. |
| `novaCycleMs` | 45000 | 1000..3600000 | Stable world-tile nova opportunity cycle. |
| `novaDurationMs` | 3600 | 100..30000 | Nova glyph evolution and shockwave duration. |
| `novaGlyphCount` | 5 | 1..16 | Ordered expansion glyph sequence; contracts on fade. |
| `rippleSpeed` | 2560 | 1..262144 | Shockwave propagation in Q8 cells per second. |
| `rippleWidth` | 384 | 16..8192 | Soft ring thickness in Q8 cells. |
| `rippleLifeMs` | 3200 | 100..30000 | Lifetime of a user/data ripple. |
| `rippleOpacity` | 280 | 0..1000 | Peak background ring opacity. |
| `rippleRings` | 2 | 1..6 | Number of trailing concentric wavefronts. |
| `motion` | 1 | 0..1 | 0 evaluates decorative fields at time zero; host pause holds explicit time instead. |
| `quantize` | 0 | 0..2 | 0 RGB; 1 canonical ANSI16 approximation; 2 xterm256 approximation. |
| `originX` | 0 | -4096..4096 | World origin x in whole cells; stable sky coordinates. |
| `originY` | 0 | -4096..4096 | World origin y in whole cells. |
| `waveAmplitude` | 640 | 0..4000 | Wave deformation in thousandths. |
| `starAttack` | 340 | 10..990 | Fraction of visible star lifetime used for brightening. |
| `reverse` | 0 | 0..1 | Reverse decorative phase and continuous rotation. |

Arrays: `palette`1..32 RGB stops; `starPalette`1..32 peak colors; `glyphs`1..32single scalars; `novaGlyphs`1..16scalars. Language array setters update count fields; do not manually desynchronize counts. Unknown properties/range errors are rejected. Changing counts directly can expose initialized/default spare entries; prefer array setters.

## Primitive catalogue

| Kind | Purpose | Data | Picking | Variants |
|---|---|---|---|---|
| `text` | Glyph text with wrapping/reveal and per-character color motion. | text; newlines wrap within rectangle | rectangle | revealMs, colorAnimation, hueStep, hueSpeed |
| `box` | Clipped information enclosure with title and optional blended fill. | text title | rectangle | style 0 rounded,1 square,2 double,3 heavy |
| `rule` | Animated horizontal/vertical information rule; longer axis chooses direction. | none | rectangle | style 0..11, hue/palette motion |
| `button` | Framed centered label; disabled/focus/selection are explicit states. | text label | rectangle | style, state, alpha, colorAnimation |
| `item` | Menu/tree item with state marker; semantic hierarchy belongs to host. | text label | rectangle | state 0 normal,1 focus,2 selected,3 disabled |
| `cursor` | Five cursor treatments, including a text-preserving block highlight. | optional glyph scalar | rectangle | style 0 block,1 underline,2 thin bar,3 pointer,4 braille |
| `progress` | Fractional progress with an eased decorative target transition. | value/fromValue 0..1000 displayed range | rectangle | style 0 eighth-block,1 lower-half rail,2 squares; durationMs |
| `bars` | Vertical normalized bar series with eased entrance. | data array; each value clamped to0..1000 | rendered bar index | durationMs, colorAnimation |
| `pie` | Braille disk partitioned by positive weights with angular entrance. | data weights; nonpositive omitted | geometric sector index | durationMs; current material palette supplies sectors |
| `donut` | Braille ring with empty center and sector hit testing. | same as pie | geometric ring sector; no center hit | durationMs; fixed inner-radius policy |
| `scatter` | Braille sample marks with optional plus-shaped points. | interleaved x,y normalized0..1000; odd tail ignored | nearest sample pair index | style 0 dot,1 plus; colorAnimation |
| `line` | Braille line trace connecting normalized samples. | data normalized0..1000 | sample index along the plot | colorAnimation; sample x evenly spaced |
| `digits` | Original seven-segment display geometry, not a bundled font. | text digits0..9 or minus | rectangle | zoom1..4; hue/palette rotation |
| `edge` | Braille routed connector with traveling highlight. | interleaved normalized x,y path points | rectangle | colorAnimation; fixed2400ms traveling highlight cycle |

All primitives share `x,y,width,height`, stable `id`, `state`, `fg,bg`, `fgOpacity,bgOpacity` and optional color motion. Node dimensions clip all drawing. Styles0..15 are accepted; kinds with fewer styles select modulo their style count. The renderer is intentionally not a layout engine.

### Common node properties

`state`:0normal,1focused,2selected,3disabled. Disabled changes appearance and blocks picking through its interactive rectangle. `id=0` is noninteractive decoration. Host keyboard navigation must omit disabled IDs.

`fgOpacity,bgOpacity`:0..1000. Default foreground1000,background0. Fill then glyph drawing occurs in node order. Partial background fill mixes both underlying background and existing foreground toward the fill; opaque fill blanks underlying glyphs. Incoming glyph foreground is mixed with the composed background, not a second simultaneously drawn glyph mask.

`colorAnimation`:0literalforeground,1HSVhue wheel,2palette traversal. `hueStep` degrees per index; `hueSpeed` signed degrees/second in HSV mode and a rate factor in palette mode. `hueBase` degrees; `hueSaturation,hueBrightness`0..1000. Defaults17,24,0,620,830. A negative hue speed reverses travel. Per-primitive index choices differ (text character, bar/row, rule position). Native hue/palette clocks wrap at360000ms, a documented periodic boundary.

`changedMs` starts transition/reveal; `durationMs`0..3600000, zero immediate. Progress interpolates `fromValue` to`value`, clamping displayed fill0..1000. Bar entrance interpolates from zero, not automatically from the previous dataset; hosts wanting animated retargeting should keep state/tracks explicitly. Pie/donut entrance reveals angle. `revealMs` is milliseconds per scalar for text. Text wraps within its rectangle; unknown glyphs become`?`.

`glyph` optionally supplies a cursor scalar. `zoom`1..4applies to seven-segment digits only. Edge travel currently has a fixed2400ms cycle; rule glyph phase150ms and cursor pulse periods are built-in style constants. They are deterministic but not every internal constant has an independent knob yet. A host can time-scale a separately rendered layer for additional control.

### Chart data and clicks

Bars/line/scatter values normalize0..1000 at drawing. Scatter uses pairs, with odd tail ignored. Pie/donut ignore nonpositive weights; all-zero charts show no sectors and produce no geometric hit. Braille shares one foreground per cell: at a boundary, the final painted dot's foreground applies to all dots in that cell. Charts use fixed canonical2:1cell geometry for subcell plotting; the background's cellAspect setting does not independently reshape charts. Native hit tests use cell coordinates, not fractional mouse pixel locations. Host click areas are coupled to rendered bar subdivisions/sector geometry/nearest plotted samples; semantic labels provide another route to inspect data.

## Impulses / stars

Event `x,y` in convenience bindings becomes Q8cell coordinates. Native records use xQ8/yQ8directly. `atMs` shares the render clock; `kind=0`ripple or`1`nova; strength0..1000. Event order is replay order. The renderer does not maintain an event list. Future/expired impulses have no effect. Empty cells may represent multiple samples with half-blocks; occupied glyphs retain text with a flattened background wave.

Ordinary stars derive positions, glyphs, phases and periods from world coordinates/seed, and preserve glyph identity across their fading cycle. Default glyphs exclude quotes, colons and multi-dot braille. Automatic novae use seeded candidates per32×16world tile, with the latest eligible active burst per tile; overlapping automatic bursts in one tile coalesce. Automatic candidates are gathered for the viewport, so offscreen-auto-nova influence is not guaranteed invariant during resize. Ordinary sky growth invariance is tested with novae disabled. Explicit offscreen impulses remain host-controlled.

Peak colors are art direction, not physical luminance or astronomical calibration. Stellar palette is a qualitative blue/white/warm progression. The48profiles combine with all patterns; the API supports custom stops within array bounds.

## Tween / keyframes

`nsStageTween(from,to,elapsedMs,durationMs,easing)` returns a scalar. Easing0linear,1smoothstep,2sine,3cubic-out. Endpoint/duration clamps are explicit; zero duration returns target. PythonKeyframeTrack is a piecewise/optionally looping host helper; other languages use the same tween to implement their own tracks. No wallclock or frame-count dependence.

## Composition

`nsStageComposite` blends source into destination with separate foreground/background opacity and clipping/negative offsets. Source glyph0meansnoink; space contributes background but not new ink. One terminal cell cannot contain two independent glyph masks: an incoming nonspace glyph replaces the previous glyph after color blending. Text over a half-block flattens its underlying pair. Blends are performed on encoded RGB integers, not linear-light photometric alpha. No terminal/window opacity control is issued.

## C call contracts / errors

Header`include/nocturne_studio.h` contains complete function signatures. Render returns cell count; negative errors are-1config,-2outputbuffer,-3events,-4scene. Validation happens before writes. `nsStageHit` returns0nohit,-1invalid or`((nodeIndex+1)<<16)|(itemIndex+1)`. Safe bindings decode to stableID/subitem. Composition returns0success/-1invalid.

Raw C caller pointers must be aligned, live, sized and nonoverlapping for the call. Nonzero counts require storage. Bindings own and bound their scratch/output. Malformed inputs are not a way to partially render. Keep configuration/model mutation outside concurrent rendering or use independent instances.

## Determinism and portability

Pinned implementation/configuration/eventorder/time/geometry yield canonical cells. Do not promise identical glyph pixels across terminal fonts. Native/WASM parity is tested, but Rust execution is not yet verified. Quantize selects16/256RGB values; writers still emitRGBSGR. GeneralUnicodewidth, automaticcapabilities, nativeWindows and independently publishedpackages remain out of scope.
