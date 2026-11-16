# Configuration reference

All properties below are integer-valued. `Permille` uses thousandths. Palettes and custom glyph arrays are separately configurable. The gallery JSON exporter writes schemaVersion 1.

| Name | Default | Range | Meaning |
|---|---:|---|---|
| `width` | 84 | 0..512 | Surface width in terminal cells. |
| `height` | 28 | 0..256 | Surface height in terminal cells. |
| `effect` | 0 | 0..5 | 0 solid; 1 linear; 2 diagonal; 3 wave; 4 rotation; 5 plasma. |
| `layout` | 0 | 0..4 | 0 material only; 1 prompt; 2 controls; 3 hue ribbon; 4 scope. |
| `seed` | 73419 | 0..2147483647 | Coordinate-hashed star and grain seed. |
| `stars` | 1 | 0..1 | Enable the star foreground layer. |
| `densityPermille` | 135 | 0..1000 | Probability per cell of containing a star, in thousandths. |
| `glyphSet` | 0 | 0..4 | 0 mixed; 1 braille; 2 punctuation; 3 mathematical; 4 custom. |
| `starPeriodMinMs` | 1600 | 80..120000 | Minimum individual twinkle cycle in milliseconds. |
| `starPeriodRangeMs` | 6400 | 0..120000 | Additional coordinate-hashed cycle range. |
| `starDutyPermille` | 500 | 1..1000 | Active fraction of each individual twinkle cycle. |
| `starFloorPermille` | 25 | 0..1000 | Minimum star intensity relative to its peak color. |
| `starPeakPermille` | 1000 | 0..1000 | Maximum star intensity relative to its peak color. |
| `gradientPeriodMs` | 3200 | 80..120000 | Time for one full material cycle, in milliseconds. |
| `saturationPermille` | 700 | 0..1000 | Palette saturation, in thousandths. |
| `brightnessPermille` | 500 | 0..1000 | Material contribution over the base color. |
| `focusRow` | -1 | -1..255 | Active row; -1 selects the middle row. |
| `neighborSpeedPermille` | 500 | 1..1000 | Speed multiplier per row away from focus. |
| `neighborSaturationPermille` | 620 | 0..1000 | Saturation multiplier per row away from focus. |
| `neighborBrightnessPermille` | 860 | 0..1000 | Brightness multiplier per row away from focus. |
| `angleDegrees` | 32 | 0..359 | Static diagonal angle in degrees. |
| `scaleCells` | 42 | 2..512 | Spatial wavelength in terminal columns. |
| `hueStepDegrees` | 23 | -360..360 | Hue offset per character. |
| `hueDegreesPerSecond` | 35 | -360..360 | Signed rotation speed of character hues. |
| `baseHueDegrees` | 220 | 0..359 | Starting hue for character effects. |
| `pixelMode` | 0 | 0..4 | 0 whole cell; 1 upper half; 2 left half; 3 shade; 4 braille contour. |
| `originX` | 0 | -1000000..1000000 | World-space horizontal origin for stable resize and scrolling. |
| `originY` | 0 | -1000000..1000000 | World-space vertical origin for stable resize and scrolling. |
| `valuePermille` | 630 | 0..1000 | Immediate demonstration data value; not interpolated. |
| `motion` | 1 | 0..1 | 0 renders the zero-time state; host pause instead preserves last motion time. |
| `phaseDegrees` | 0 | 0..359 | Initial material phase. |
| `grainPermille` | 12 | 0..1000 | Subtle fixed spatial grain amplitude. |
| `cursorMode` | 0 | 0..3 | 0 block; 1 underline; 2 bar; 3 orbiting dots. |
| `borderStyle` | 0 | 0..3 | 0 rounded; 1 square; 2 double; 3 heavy. |
| `selection` | 2 | 0..5 | Immediate selected demonstration menu index. |
| `foregroundColor` | 14077116 | 0..16777215 | Default text color as packed RGB. |
| `baseColor` | 1118222 | 0..16777215 | Dark Black Creme, packed RGB. |
| `waveAmplitudePermille` | 650 | 0..2000 | Wave distortion strength. |
| `starAttackPermille` | 350 | 1..999 | Fraction of active twinkle spent brightening. |
| `paletteCount` | 4 | 1..8 | Number of active gradient colors. |
| `starPaletteCount` | 6 | 1..8 | Number of active star peak colors. |
| `glyphCount` | 0 | 0..32 | Number of custom star code points. |
| `modalOpen` | 0 | 0..1 | Show the demonstration modal. |
| `hueSaturationPermille` | 430 | 0..1000 | Saturation of character hue-wheel effects. |
| `hueBrightnessPermille` | 780 | 0..1000 | Brightness of character hue-wheel effects. |
| `cellAspectPermille` | 2000 | 500..4000 | Physical cell height / width, in thousandths. |
| `textScrimPermille` | 180 | 0..1000 | Text-cell background blend toward the base color. |
| `promptBands` | 0 | 0..1 | Apply focused row falloff even without the prompt demonstration layout. |
| `colorMode` | 0 | 0..2 | 0 predefined palette; 1 full 360-degree hue wheel; 2 120-degree-offset RGB sine waves. |

## Palettes and custom glyphs

`palette` and `starPalette`: 1..8 `#RRGGBB` colors. `glyphs`: at most 32 single code points, sanitized by the material glyph profile. Select `glyphSet=4` for a custom set. In TypeScript, active palette/glyph counts are derived from these arrays at render time. Native bindings supply setters that maintain counts. Avoid manually setting active counts unless writing raw ABI configuration.
