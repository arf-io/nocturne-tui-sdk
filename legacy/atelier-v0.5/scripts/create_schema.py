"""Generate the shared, versioned integer configuration contract and C header."""
import json
import math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FIELDS=[
('width',84,0,512,'Surface width in terminal cells.'),
('height',28,0,256,'Surface height in terminal cells.'),
('effect',0,0,5,'0 solid; 1 linear; 2 diagonal; 3 wave; 4 rotation; 5 plasma.'),
('layout',0,0,4,'0 material only; 1 prompt; 2 controls; 3 hue ribbon; 4 scope.'),
('seed',73419,0,2147483647,'Coordinate-hashed star and grain seed.'),
('stars',1,0,1,'Enable the star foreground layer.'),
('densityPermille',135,0,1000,'Probability per cell of containing a star, in thousandths.'),
('glyphSet',0,0,4,'0 mixed; 1 braille; 2 punctuation; 3 mathematical; 4 custom.'),
('starPeriodMinMs',1600,80,120000,'Minimum individual twinkle cycle in milliseconds.'),
('starPeriodRangeMs',6400,0,120000,'Additional coordinate-hashed cycle range.'),
('starDutyPermille',500,1,1000,'Active fraction of each individual twinkle cycle.'),
('starFloorPermille',25,0,1000,'Minimum star intensity relative to its peak color.'),
('starPeakPermille',1000,0,1000,'Maximum star intensity relative to its peak color.'),
('gradientPeriodMs',3200,80,120000,'Time for one full material cycle, in milliseconds.'),
('saturationPermille',700,0,1000,'Palette saturation, in thousandths.'),
('brightnessPermille',500,0,1000,'Material contribution over the base color.'),
('focusRow',-1,-1,255,'Active row; -1 selects the middle row.'),
('neighborSpeedPermille',500,1,1000,'Speed multiplier per row away from focus.'),
('neighborSaturationPermille',620,0,1000,'Saturation multiplier per row away from focus.'),
('neighborBrightnessPermille',860,0,1000,'Brightness multiplier per row away from focus.'),
('angleDegrees',32,0,359,'Static diagonal angle in degrees.'),
('scaleCells',42,2,512,'Spatial wavelength in terminal columns.'),
('hueStepDegrees',23,-360,360,'Hue offset per character.'),
('hueDegreesPerSecond',35,-360,360,'Signed rotation speed of character hues.'),
('baseHueDegrees',220,0,359,'Starting hue for character effects.'),
('pixelMode',0,0,4,'0 whole cell; 1 upper half; 2 left half; 3 shade; 4 braille contour.'),
('originX',0,-1000000,1000000,'World-space horizontal origin for stable resize and scrolling.'),
('originY',0,-1000000,1000000,'World-space vertical origin for stable resize and scrolling.'),
('valuePermille',630,0,1000,'Immediate demonstration data value; not interpolated.'),
('motion',1,0,1,'0 renders the zero-time state; host pause instead preserves last motion time.'),
('phaseDegrees',0,0,359,'Initial material phase.'),
('grainPermille',12,0,1000,'Subtle fixed spatial grain amplitude.'),
('cursorMode',0,0,3,'0 block; 1 underline; 2 bar; 3 orbiting dots.'),
('borderStyle',0,0,3,'0 rounded; 1 square; 2 double; 3 heavy.'),
('selection',2,0,5,'Immediate selected demonstration menu index.'),
('foregroundColor',0xD6CCBC,0,0xFFFFFF,'Default text color as packed RGB.'),
('baseColor',0x11100E,0,0xFFFFFF,'Dark Black Creme, packed RGB.'),
('waveAmplitudePermille',650,0,2000,'Wave distortion strength.'),
('starAttackPermille',350,1,999,'Fraction of active twinkle spent brightening.'),
('paletteCount',4,1,8,'Number of active gradient colors.'),
('starPaletteCount',6,1,8,'Number of active star peak colors.'),
('glyphCount',0,0,32,'Number of custom star code points.'),
('modalOpen',0,0,1,'Show the demonstration modal.'),
('hueSaturationPermille',430,0,1000,'Saturation of character hue-wheel effects.'),
('hueBrightnessPermille',780,0,1000,'Brightness of character hue-wheel effects.'),
('cellAspectPermille',2000,500,4000,'Physical cell height / width, in thousandths.'),
('textScrimPermille',180,0,1000,'Text-cell background blend toward the base color.'),
('promptBands',0,0,1,'Apply focused row falloff even without the prompt demonstration layout.'),
('colorMode',0,0,2,'0 predefined palette; 1 full 360-degree hue wheel; 2 120-degree-offset RGB sine waves.'),
]
schema={'schemaVersion':1,'abiVersion':1,'description':'All integers. Permille means parts per thousand. Palette colors are #RRGGBB.','fields':[{'name':n,'index':i,'default':d,'minimum':a,'maximum':b,'description':s} for i,(n,d,a,b,s) in enumerate(FIELDS)],'gradientPalette':['#654F72','#356A6A','#735569','#817451'],'starPalette':['#B6A4C4','#9FB9B0','#C7BCA7','#9CACCA','#C6A0AA','#ADBDBB']}
(ROOT/'schema.json').write_text(json.dumps(schema,indent=2)+'\n')
def key(n):
    import re
    return 'NS_'+re.sub(r'(?<!^)(?=[A-Z])','_',n).upper()
header='''/* Generated configuration indices. Regenerate with scripts/create_schema.py. */
#ifndef NOCTURNE_H
#define NOCTURNE_H
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define NS_ABI_VERSION 1
#define NS_MAX_WIDTH 512
#define NS_MAX_HEIGHT 256
#define NS_MAX_CELLS (NS_MAX_WIDTH * NS_MAX_HEIGHT)
#define NS_MAX_TEXT 512
#if defined(_WIN32)
#define NS_API __declspec(dllexport)
#else
#define NS_API __attribute__((visibility("default")))
#endif
typedef struct { uint32_t glyph, fg, bg, flags; } NsCell;
typedef struct {
    int32_t values[64];
    uint32_t palette[8];
    uint32_t starPalette[8];
    uint32_t glyphs[32];
} NsConfig;
enum NsKey {
'''
header+=',\n'.join('    '+key(n)+' = '+str(i) for i,(n,*_) in enumerate(FIELDS))
header+='\n};\n'
header+='''/** Initialize every configuration byte. No allocation and no terminal I/O. */
NS_API void nsDefaultConfig(NsConfig *config);
/** Return zero for valid config, otherwise the one-based invalid key index. */
NS_API int32_t nsValidateConfig(const NsConfig *config);
/** Render caller-owned cells. Returns count, or -1 invalid config, -2 buffer,
 * -3 invalid text length/pointer. Text is a bounded code-point array; unsupported
 * or unsafe glyphs become '?'. No state, wall clock, allocation, or terminal I/O.
 * Example: nsRender(&config, 1000, NULL, 0, cells, width*height).
 * Pointers must reference suitably aligned, live, non-overlapping buffers. */
NS_API int32_t nsRender(const NsConfig *config, uint64_t motionMs,
    const uint32_t *text, uint32_t textLength, NsCell *cells, uint32_t capacity);
/** Exact effective row period in ms after distance falloff; config must be valid. */
NS_API uint64_t nsRowPeriod(const NsConfig *config, uint32_t distance);
/** Exact effective row saturation after distance falloff; config must be valid. */
NS_API int32_t nsRowSaturation(const NsConfig *config, uint32_t distance);
NS_API uint32_t nsAbiVersion(void);
NS_API uint32_t nsConfigSize(void);
NS_API uint32_t nsCellSize(void);
#ifdef __cplusplus
}
#endif
#endif
'''
(ROOT/'include/nocturne.h').write_text(header)
(ROOT/'src/defaults.inc').write_text('static const int32_t DEFAULT_VALUES[64] = {'+','.join(str(f[1]) for f in FIELDS)+'};\nstatic const int32_t MIN_VALUES[] = {'+','.join(str(f[2]) for f in FIELDS)+'};\nstatic const int32_t MAX_VALUES[] = {'+','.join(str(f[3]) for f in FIELDS)+'};\n#define NS_FIELD_COUNT '+str(len(FIELDS))+'\n')
values=[round(math.sin(i*math.tau/1024)*1000) for i in range(1024)]
(ROOT/'src/sine.inc').write_text('/* Pinned Q1000 sine table. Integer runtime math, 1024 phases per turn. */\nstatic const int16_t SINE[1024] = {\n'+',\n'.join(','.join(map(str,values[i:i+32])) for i in range(0,1024,32))+'\n};\n')
