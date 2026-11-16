/* Nocturne v0.1: deterministic terminal-cell materials.
 * No platform APIs, mutable globals, allocation, terminal I/O, or floating math.
 * Public functions are documented in include/nocturne.h.
 */
#include "nocturne.h"
#include <stddef.h>
#include "defaults.inc"
#include "sine.inc"
#define V(key) (config->values[(key)])

static int32_t clampI(int32_t value, int32_t lo, int32_t hi)
{
  return (value < lo) ? (lo) : ((value > hi) ? (hi) : (value));
}



static int32_t modI(int64_t value, int32_t divisor)
{
  int32_t r = (int32_t) (value % divisor);
  return (r < 0) ? (r + divisor) : (r);
}



static int32_t sinI(int64_t phase)
{
  return SINE[modI(phase, 1024)];
}



static uint32_t hashI(uint32_t value)
{
  value ^= value >> 16;
  value *= 0x7feb352du;
  value ^= value >> 15;
  value *= 0x846ca68bu;
  return value ^ (value >> 16);
}



/* Coordinate-keyed randomness preserves existing stars when the surface grows. */
static uint32_t xyHash(const NsConfig *config, int32_t x, int32_t y)
{
  return hashI((((uint32_t) V(NS_SEED)) ^ (((uint32_t) (x + V(NS_ORIGIN_X))) * 0x9e3779b9u)) ^ (((uint32_t) (y + V(NS_ORIGIN_Y))) * 0x85ebca6bu));
}



static uint32_t rgbI(int32_t r, int32_t g, int32_t b)
{
  return (((uint32_t) (clampI(r, 0, 255) << 16)) | ((uint32_t) (clampI(g, 0, 255) << 8))) | ((uint32_t) clampI(b, 0, 255));
}



static int32_t redI(uint32_t c)
{
  return (int32_t) ((c >> 16) & 255);
}



static int32_t greenI(uint32_t c)
{
  return (int32_t) ((c >> 8) & 255);
}



static int32_t blueI(uint32_t c)
{
  return (int32_t) (c & 255);
}



static uint32_t mixI(uint32_t a, uint32_t b, int32_t p)
{
  p = clampI(p, 0, 1000);
  return rgbI(redI(a) + (((redI(b) - redI(a)) * p) / 1000), greenI(a) + (((greenI(b) - greenI(a)) * p) / 1000), blueI(a) + (((blueI(b) - blueI(a)) * p) / 1000));
}



static uint32_t saturateI(uint32_t c, int32_t p)
{
  int32_t l = (((2126 * redI(c)) + (7152 * greenI(c))) + (722 * blueI(c))) / 10000;
  return rgbI(l + (((redI(c) - l) * p) / 1000), l + (((greenI(c) - l) * p) / 1000), l + (((blueI(c) - l) * p) / 1000));
}



static uint32_t hsvI(int64_t hue, int32_t saturation, int32_t value)
{
  int32_t h = modI(hue, 360);
  int32_t c = (value * saturation) / 1000;
  int32_t x = (c * (60 - (((h % 120) > 60) ? ((h % 120) - 60) : (60 - (h % 120))))) / 60;
  int32_t m = value - c;
  int32_t r = 0;
  int32_t g = 0;
  int32_t b = 0;
  switch (h / 60)
  {
    case 0:
      r = c;
      g = x;
      break;

    case 1:
      r = x;
      g = c;
      break;

    case 2:
      g = c;
      b = x;
      break;

    case 3:
      g = x;
      b = c;
      break;

    case 4:
      r = x;
      b = c;
      break;

    default:
      r = c;
      b = x;
      break;

  }

  return rgbI(((r + m) * 255) / 1000, ((g + m) * 255) / 1000, ((b + m) * 255) / 1000);
}



static int32_t decayI(int32_t value, int32_t factor, uint32_t distance)
{
  distance = (distance > 256) ? (256) : (distance);
  for (uint32_t d = 0; d < distance; d++)
    value = (value * factor) / 1000;

  return value;
}



static uint64_t sqrtI(uint64_t n)
{
  uint64_t result = 0;
  uint64_t bit = ((uint64_t) 1) << 62;
  while (bit > n)
    bit >>= 2;

  while (bit)
  {
    if (n >= (result + bit))
    {
      n -= result + bit;
      result = (result >> 1) + bit;
    }
    else
      result >>= 1;
    bit >>= 2;
  }

  return result;
}



/* Closed-loop, integer encoded-RGB interpolation. The final stop wraps to zero. */
static uint32_t paletteI(const NsConfig *config, int64_t phase)
{
  int32_t count = V(NS_PALETTE_COUNT);
  int32_t p = modI(phase, 1024) * count;
  int32_t index = p / 1024;
  return mixI(config->palette[index], config->palette[(index + 1) % count], ((p % 1024) * 1000) / 1024);
}



uint32_t nsAbiVersion(void)
{
  return NS_ABI_VERSION;
}



uint32_t nsConfigSize(void)
{
  return (uint32_t) (sizeof(NsConfig));
}



uint32_t nsCellSize(void)
{
  return (uint32_t) (sizeof(NsCell));
}



void nsDefaultConfig(NsConfig *config)
{
  if (!config)
    return;
  for (int i = 0; i < 64; i++)
    config->values[i] = DEFAULT_VALUES[i];

  const uint32_t p[8] = {0x654f72, 0x356a6a, 0x735569, 0x817451, 0x654f72, 0x356a6a, 0x735569, 0x817451};
  const uint32_t s[8] = {0xb6a4c4, 0x9fb9b0, 0xc7bca7, 0x9cacca, 0xc6a0aa, 0xadbdbb, 0xb6a4c4, 0x9fb9b0};
  for (int i = 0; i < 8; i++)
  {
    config->palette[i] = p[i];
    config->starPalette[i] = s[i];
  }

  for (int i = 0; i < 32; i++)
    config->glyphs[i] = 0;

}



int32_t nsValidateConfig(const NsConfig *config)
{
  if (!config)
    return 1;
  for (int i = 0; i < NS_FIELD_COUNT; i++)
    if ((V(i) < MIN_VALUES[i]) || (V(i) > MAX_VALUES[i]))
    return i + 1;

  for (int i = 0; i < V(NS_PALETTE_COUNT); i++)
    if (config->palette[i] > 0xffffff)
    return NS_PALETTE_COUNT + 1;

  for (int i = 0; i < V(NS_STAR_PALETTE_COUNT); i++)
    if (config->starPalette[i] > 0xffffff)
    return NS_STAR_PALETTE_COUNT + 1;

  return 0;
}



/* Periods double at the default 500/1000 neighbor speed; cap before overflow. */
uint64_t nsRowPeriod(const NsConfig *config, uint32_t distance)
{
  if ((!config) || (V(NS_NEIGHBOR_SPEED_PERMILLE) < 1))
    return 0;
  uint64_t p = (uint64_t) V(NS_GRADIENT_PERIOD_MS);
  distance = (distance > 256) ? (256) : (distance);
  for (uint32_t d = 0; d < distance; d++)
  {
    if (p > ((((uint64_t) 1) << 52) / 1000))
      return ((uint64_t) 1) << 52;
    p = (p * 1000) / ((uint32_t) V(NS_NEIGHBOR_SPEED_PERMILLE));
  }

  return p;
}



int32_t nsRowSaturation(const NsConfig *config, uint32_t distance)
{
  return (config) ? (decayI(V(NS_SATURATION_PERMILLE), V(NS_NEIGHBOR_SATURATION_PERMILLE), distance)) : (0);
}



static int32_t focusI(const NsConfig *config)
{
  int32_t h = V(NS_HEIGHT);
  return (V(NS_FOCUS_ROW) < 0) ? (h / 2) : (clampI(V(NS_FOCUS_ROW), 0, (h > 0) ? (h - 1) : (0)));
}



static uint32_t materialI(const NsConfig *config, uint64_t timeMs, int32_t xQ, int32_t yQ)
{
  uint32_t base = (uint32_t) V(NS_BASE_COLOR);
  if (V(NS_EFFECT) == 0)
    return base;
  int32_t row = yQ / 1024;
  int32_t focus = focusI(config);
  int32_t distance = (row > focus) ? (row - focus) : (focus - row);
  int32_t band = (V(NS_LAYOUT) == 1) || V(NS_PROMPT_BANDS);
  int32_t sat = (band) ? (nsRowSaturation(config, (uint32_t) distance)) : (V(NS_SATURATION_PERMILLE));
  int32_t brightness = (band) ? (decayI(V(NS_BRIGHTNESS_PERMILLE), V(NS_NEIGHBOR_BRIGHTNESS_PERMILLE), (uint32_t) distance)) : (V(NS_BRIGHTNESS_PERMILLE));
  uint64_t period = (band) ? (nsRowPeriod(config, (uint32_t) distance)) : ((uint64_t) V(NS_GRADIENT_PERIOD_MS));
  int32_t phase = ((int32_t) (((timeMs % period) * 1024) / period)) + ((V(NS_PHASE_DEGREES) * 1024) / 360);
  int64_t x = (((int64_t) xQ) + (((int64_t) V(NS_ORIGIN_X)) * 1024)) / V(NS_SCALE_CELLS);
  int64_t y = (((((int64_t) yQ) + (((int64_t) V(NS_ORIGIN_Y)) * 1024)) * V(NS_CELL_ASPECT_PERMILLE)) / 1000) / V(NS_SCALE_CELLS);
  int64_t field = 0;
  switch (V(NS_EFFECT))
  {
    case 1:
      field = x + phase;
      break;

    case 2:
    {
      int32_t angle = (V(NS_ANGLE_DEGREES) * 1024) / 360;
      field = (((x * sinI(angle + 256)) + (y * sinI(angle))) / 1000) + phase;
      break;
    }

    case 3:
      field = (x + ((sinI(y + phase) * V(NS_WAVE_AMPLITUDE_PERMILLE)) / 1300)) + phase;
      break;

    case 4:
      field = ((x * sinI(phase + 256)) + (y * sinI(phase))) / 1000;
      break;

    default:
    {
      int64_t xx = x % 8192;
      int64_t yy = y % 8192;
      int64_t radius = (int64_t) sqrtI((uint64_t) ((xx * xx) + (yy * yy)));
      int32_t sum = ((sinI(x + phase) + sinI(y - phase)) + sinI(((x + y) / 2) + (phase * 2))) + sinI(radius - (phase * 3));
      field = (((sum + 4000) * 1024) / 8000) + phase;
      break;
    }

  }

  uint32_t color = mixI(base, saturateI((V(NS_COLOR_MODE) == 1) ? (hsvI(((field * 360) / 1024) + V(NS_BASE_HUE_DEGREES), 1000, 800)) : ((V(NS_COLOR_MODE) == 2) ? (rgbI((((sinI(field) + 1000) * 95) / 1000) + 30, (((sinI(field + 341) + 1000) * 95) / 1000) + 30, (((sinI(field + 682) + 1000) * 95) / 1000) + 30)) : (paletteI(config, field))), sat), brightness);
  int32_t grain = ((((int32_t) (xyHash(config, xQ / 1024, yQ / 1024) % 17)) - 8) * V(NS_GRAIN_PERMILLE)) / 1000;
  return rgbI(redI(color) + grain, greenI(color) + grain, blueI(color) + grain);
}



static uint32_t safeGlyph(uint32_t glyph)
{
  if (((((((((((glyph >= 32) && (glyph <= 126)) || ((glyph >= 0x2500) && (glyph <= 0x259f))) || ((glyph >= 0x2800) && (glyph <= 0x28ff))) || (glyph == 0xb7)) || (glyph == 0x2022)) || (glyph == 0x2219)) || (glyph == 0x22c5)) || (glyph == 0x22c6)) || (glyph == 0x207a)) || (glyph == 0x2217))
    return glyph;
  return '?';
}



static int32_t smoothI(int32_t p)
{
  p = clampI(p, 0, 1000);
  return (int32_t) (((((int64_t) p) * p) * (3000 - (2 * p))) / 1000000);
}



static uint32_t starGlyphI(const NsConfig *config, uint32_t hash)
{
  static const uint32_t mixed[] = {0x2801, 0x2808, 0x2802, 0x2810, 0x2804, 0x2820, 0x2840, 0x2880, 0xb7, 0x2219, 0x22c5, '.', 0x2801, 0xb7, 0x22c6, '+', 0x2809, 0x2812, 0x2801};
  static const uint32_t braille[] = {0x2801, 0x2808, 0x2802, 0x2810, 0x2804, 0x2820, 0x2840, 0x2880, 0x2809, 0x2812, 0x2824};
  static const uint32_t punctuation[] = {'.', 0xb7, 0x2219, 0x2022, ':', '+', '*'};
  static const uint32_t math[] = {0x22c5, 0x22c6, 0x2217, '+', 0x207a, 0x2219};
  switch (V(NS_GLYPH_SET))
  {
    case 1:
      return braille[hash % ((sizeof(braille)) / (sizeof(braille[0])))];

    case 2:
      return punctuation[hash % ((sizeof(punctuation)) / (sizeof(punctuation[0])))];

    case 3:
      return math[hash % ((sizeof(math)) / (sizeof(math[0])))];

    case 4:
      if (V(NS_GLYPH_COUNT) > 0)
      return safeGlyph(config->glyphs[hash % ((uint32_t) V(NS_GLYPH_COUNT))]);

      return mixed[hash % (sizeof(mixed) / sizeof(mixed[0]))];
    default:
      return mixed[hash % ((sizeof(mixed)) / (sizeof(mixed[0])))];

  }

}



/* Text/stars replace the half-block glyph, so flatten its two color samples. */
static uint32_t flattenedBg(const NsCell *cell)
{
  return ((cell->glyph == 0x2580) || (cell->glyph == 0x258c)) ? (mixI(cell->bg, cell->fg, 500)) : (cell->bg);
}



/* Evaluate the entire twinkle envelope from position and time, never frame history. */
static void starI(const NsConfig *config, uint64_t timeMs, int32_t x, int32_t y, NsCell *cell)
{
  uint32_t h = xyHash(config, x, y);
  if (((int32_t) (h % 1000)) >= V(NS_DENSITY_PERMILLE))
    return;
  uint32_t rh = hashI(h ^ 0xa2c79b3du);
  uint32_t period = ((uint32_t) V(NS_STAR_PERIOD_MIN_MS)) + (rh % (((uint32_t) V(NS_STAR_PERIOD_RANGE_MS)) + 1));
  uint32_t p = (uint32_t) (((timeMs % period) + (hashI(h ^ 0x13579bdfu) % period)) % period);
  uint32_t duration = (period * ((uint32_t) V(NS_STAR_DUTY_PERMILLE))) / 1000;
  if (duration < 2)
    duration = 2;
  uint32_t attack = (duration * ((uint32_t) V(NS_STAR_ATTACK_PERMILLE))) / 1000;
  if (attack < 1)
    attack = 1;
  if (attack >= duration)
    attack = duration - 1;
  int32_t envelope = 0;
  if (p < duration)
    envelope = (p < attack) ? (smoothI((int32_t) ((p * 1000) / attack))) : (smoothI((int32_t) (((duration - p) * 1000) / (duration - attack))));
  int32_t amount = V(NS_STAR_FLOOR_PERMILLE) + (((1000 - V(NS_STAR_FLOOR_PERMILLE)) * envelope) / 1000);
  amount = (amount * V(NS_STAR_PEAK_PERMILLE)) / 1000;
  if (amount < 8)
    return;
  uint32_t bg = flattenedBg(cell);
  cell->glyph = starGlyphI(config, hashI(h ^ 0xdeadbeefu));
  cell->bg = bg;
  cell->fg = mixI(bg, config->starPalette[hashI(h) % ((uint32_t) V(NS_STAR_PALETTE_COUNT))], amount);
}



static uint32_t hueI(const NsConfig *config, uint64_t timeMs, int32_t index)
{
  int64_t hue = (V(NS_BASE_HUE_DEGREES) + (((int64_t) index) * V(NS_HUE_STEP_DEGREES))) + ((((int64_t) (timeMs % 360000)) * V(NS_HUE_DEGREES_PER_SECOND)) / 1000);
  return hsvI(hue, V(NS_HUE_SATURATION_PERMILLE), V(NS_HUE_BRIGHTNESS_PERMILLE));
}



static void putI(const NsConfig *config, NsCell *cells, int32_t x, int32_t y, uint32_t glyph, uint32_t color, int32_t scrim)
{
  if ((((x < 0) || (y < 0)) || (x >= V(NS_WIDTH))) || (y >= V(NS_HEIGHT)))
    return;
  NsCell *cell = &cells[(y * V(NS_WIDTH)) + x];
  cell->bg = mixI(flattenedBg(cell), (uint32_t) V(NS_BASE_COLOR), scrim);
  cell->glyph = safeGlyph(glyph);
  cell->fg = color;
  cell->flags = 0;
}



static void textI(const NsConfig *config, NsCell *cells, int32_t x, int32_t y, const char *text, uint32_t color)
{
  for (int32_t i = 0; text[i] && (i < 512); i++)
    putI(config, cells, x + i, y, (uint8_t) text[i], color, V(NS_TEXT_SCRIM_PERMILLE));

}



static void numberI(const NsConfig *config, NsCell *cells, int32_t x, int32_t y, int32_t value, uint32_t color)
{
  char s[12];
  int n = 0;
  value = clampI(value, 0, 1000000);
  do
  {
    s[n++] = (char) ('0' + (value % 10));
    value /= 10;
  }
  while (value);
  for (int i = 0; i < n; i++)
    putI(config, cells, x + i, y, (uint32_t) s[(n - i) - 1], color, V(NS_TEXT_SCRIM_PERMILLE));

}



static void boxI(const NsConfig *config, NsCell *cells, uint64_t timeMs, int32_t x, int32_t y, int32_t w, int32_t h)
{
  if ((w < 2) || (h < 2))
    return;
  static const uint32_t borders[4][6] = {{0x256d, 0x256e, 0x2570, 0x256f, 0x2500, 0x2502}, {0x250c, 0x2510, 0x2514, 0x2518, 0x2500, 0x2502}, {0x2554, 0x2557, 0x255a, 0x255d, 0x2550, 0x2551}, {0x250f, 0x2513, 0x2517, 0x251b, 0x2501, 0x2503}};
  const uint32_t *g = borders[V(NS_BORDER_STYLE)];
  for (int i = 0; i < w; i++)
  {
    putI(config, cells, x + i, y, (i == 0) ? (g[0]) : ((i == (w - 1)) ? (g[1]) : (g[4])), mixI((uint32_t) V(NS_BASE_COLOR), hueI(config, timeMs, i), 550), 0);
    putI(config, cells, x + i, (y + h) - 1, (i == 0) ? (g[2]) : ((i == (w - 1)) ? (g[3]) : (g[4])), mixI((uint32_t) V(NS_BASE_COLOR), hueI(config, timeMs, (w + h) + i), 550), 0);
  }

  for (int i = 1; i < (h - 1); i++)
  {
    putI(config, cells, x, y + i, g[5], mixI((uint32_t) V(NS_BASE_COLOR), hueI(config, timeMs, i), 550), 0);
    putI(config, cells, (x + w) - 1, y + i, g[5], mixI((uint32_t) V(NS_BASE_COLOR), hueI(config, timeMs, w + i), 550), 0);
  }

}



static void barI(const NsConfig *config, NsCell *cells, uint64_t timeMs, int32_t x, int32_t y, int32_t w, int32_t value, int32_t style)
{
  if (w < 1)
    return;
  static const uint32_t fraction[9] = {' ', 0x258f, 0x258e, 0x258d, 0x258c, 0x258b, 0x258a, 0x2589, 0x2588};
  int32_t filled = ((w * 8) * clampI(value, 0, 1000)) / 1000;
  for (int32_t i = 0; i < w; i++)
  {
    int32_t amount = clampI(filled - (i * 8), 0, 8);
    uint32_t glyph = (style == 1) ? ((amount > 0) ? (0x2584) : (0x2500)) : (fraction[amount]);
    uint32_t color = hueI(config, timeMs, i);
    putI(config, cells, x + i, y, glyph, (amount) ? (color) : (mixI((uint32_t) V(NS_BASE_COLOR), color, 180)), 0);
    if ((style == 2) && (amount == 0))
      putI(config, cells, x + i, y, 0xb7, mixI((uint32_t) V(NS_BASE_COLOR), color, 200), 0);
  }

}



/* Demonstration signal only: two sampled waves share one braille glyph/color. */
static void graphI(const NsConfig *config, NsCell *cells, uint64_t timeMs, int32_t x, int32_t y, int32_t w, int32_t h)
{
  if ((w < 1) || (h < 1))
    return;
  static const uint8_t dots[4][2] = {{1, 8}, {2, 16}, {4, 32}, {64, 128}};
  int32_t phase = (int32_t) (((timeMs % 6000) * 1024) / 6000);
  int32_t amp = clampI(V(NS_VALUE_PERMILLE), 100, 1000);
  for (int32_t cy = 0; cy < h; cy++)
    for (int32_t cx = 0; cx < w; cx++)
  {
    uint32_t mask = 0;
    for (int dx = 0; dx < 2; dx++)
    {
      int32_t px = (cx * 2) + dx;
      int32_t wave = ((sinI((px * 17) + phase) + ((sinI((px * 31) - phase) * 3) / 10)) * amp) / 1000;
      int32_t py = clampI((((h * 4) - 1) / 2) + ((wave * ((h * 4) - 3)) / 2600), 0, (h * 4) - 1);
      if ((py / 4) == cy)
        mask |= dots[py % 4][dx];
      int32_t second = clampI((((h * 4) - 1) / 2) + ((sinI((px * 11) - phase) * ((h * 4) - 3)) / 4500), 0, (h * 4) - 1);
      if ((second / 4) == cy)
        mask |= dots[second % 4][dx];
    }

    if (mask)
      putI(config, cells, x + cx, y + cy, 0x2800 + mask, hueI(config, timeMs, cx / 2), 0);
  }


}



static void cursorI(const NsConfig *config, NsCell *cells, uint64_t timeMs, int32_t x, int32_t y)
{
  static const uint32_t modes[] = {0x258c, 0x2581, 0x2502, 0x2801};
  uint32_t glyph = modes[V(NS_CURSOR_MODE)];
  if (V(NS_CURSOR_MODE) == 3)
  {
    static const uint32_t orbit[] = {0x2801, 0x2808, 0x2810, 0x2820, 0x2880, 0x2840, 0x2804, 0x2802};
    glyph = orbit[(timeMs / 100) % 8];
  }
  int32_t glow = 650 + (((sinI((((int64_t) (timeMs % 2400)) * 1024) / 2400) + 1000) * 175) / 1000);
  putI(config, cells, x, y, glyph, mixI((uint32_t) V(NS_BASE_COLOR), hueI(config, timeMs, 0), glow), 0);
}



static uint32_t inputI(const NsConfig *config, NsCell *cells, int32_t x, int32_t y, int32_t maxLength, const uint32_t *text, uint32_t length)
{
  uint32_t n = (uint32_t) ((maxLength > 0) ? (maxLength) : (0));
  if (n > length)
    n = length;
  uint32_t start = length - n;
  for (uint32_t i = 0; i < n; i++)
    putI(config, cells, x + ((int32_t) i), y, text[start + i], (uint32_t) V(NS_FOREGROUND_COLOR), V(NS_TEXT_SCRIM_PERMILLE));

  return n;
}



static void promptI(const NsConfig *config, NsCell *cells, uint64_t timeMs, const uint32_t *text, uint32_t length)
{
  int32_t w = V(NS_WIDTH);
  int32_t h = V(NS_HEIGHT);
  int32_t f = focusI(config);
  int32_t x = (w > 12) ? (5) : (0);
  uint32_t fg = (uint32_t) V(NS_FOREGROUND_COLOR);
  uint32_t muted = mixI((uint32_t) V(NS_BASE_COLOR), fg, 420);
  if (h > 8)
  {
    textI(config, cells, x, 2, "NOCTURNE / PROMPT SURFACE", muted);
    textI(config, cells, x, h - 3, "motion 30 Hz   /   data is event-driven", muted);
  }
  if (f > 3)
    textI(config, cells, x, f - 2, "  leave room for the unexpected.", muted);
  if ((f + 2) < (h - 2))
    textI(config, cells, x, f + 2, "  a little light. a little mischief.", muted);
  putI(config, cells, x, f, '>', hueI(config, timeMs, 0), 0);
  uint32_t n = inputI(config, cells, x + 2, f, (w - x) - 4, text, length);
  cursorI(config, cells, timeMs, (x + 2) + ((int32_t) n), f);
}



static void controlsI(const NsConfig *config, NsCell *cells, uint64_t timeMs, const uint32_t *text, uint32_t length)
{
  int32_t w = V(NS_WIDTH);
  int32_t h = V(NS_HEIGHT);
  if ((w < 64) || (h < 26))
  {
    promptI(config, cells, timeMs, text, length);
    return;
  }
  uint32_t fg = (uint32_t) V(NS_FOREGROUND_COLOR);
  uint32_t muted = mixI((uint32_t) V(NS_BASE_COLOR), fg, 520);
  boxI(config, cells, timeMs, 1, 1, w - 2, h - 2);
  textI(config, cells, 4, 1, " NOCTURNE / MATERIAL PLAYGROUND ", fg);
  int32_t split = w / 3;
  const char *menu[] = {"Star nursery", "Prompt surfaces", "Liquid chrome", "Field instruments", "Quiet machinery", "Demoscene"};
  textI(config, cells, 4, 4, "COLLECTION", muted);
  for (int i = 0; i < 6; i++)
  {
    int yy = 6 + (i * 2);
    if (i == V(NS_SELECTION))
    {
      for (int xx = 3; xx < (split - 1); xx++)
      {
        NsCell *cell = &cells[(yy * w) + xx];
        cell->bg = mixI(cell->bg, hueI(config, timeMs, xx), 180);
        cell->glyph = ' ';
      }

      putI(config, cells, 3, yy, '>', hueI(config, timeMs, 0), 0);
    }
    textI(config, cells, 5, yy, menu[i], (i == V(NS_SELECTION)) ? (fg) : (muted));
  }

  for (int yy = 3; yy < (h - 7); yy++)
    putI(config, cells, split, yy, 0x2502, mixI((uint32_t) V(NS_BASE_COLOR), fg, 160), 0);

  int32_t rx = split + 3;
  int32_t rw = (w - rx) - 5;
  textI(config, cells, rx, 4, "SIGNAL / LIVE VALUE", muted);
  numberI(config, cells, (rx + rw) - 4, 4, V(NS_VALUE_PERMILLE) / 10, fg);
  textI(config, cells, (rx + rw) - 1, 4, "%", muted);
  barI(config, cells, timeMs, rx, 6, rw, V(NS_VALUE_PERMILLE), 0);
  textI(config, cells, rx, 9, "HALF-CELL LIGHT RAIL", muted);
  barI(config, cells, timeMs, rx, 11, rw, 780, 1);
  if (h >= 27)
  {
    textI(config, cells, rx, 14, "BRAILLE INTERFERENCE / SYNTHETIC", muted);
    graphI(config, cells, timeMs, rx, 16, rw, h - 24);
  }
  else
    barI(config, cells, timeMs, rx, 14, rw, 450, 2);
  boxI(config, cells, timeMs, 3, h - 6, w - 6, 3);
  putI(config, cells, 5, h - 5, '>', hueI(config, timeMs, 0), 0);
  uint32_t n = inputI(config, cells, 7, h - 5, w - 12, text, length);
  cursorI(config, cells, timeMs, 7 + ((int32_t) n), h - 5);
  textI(config, cells, 4, h - 2, " immediate data / unhurried light ", muted);
  if (V(NS_MODAL_OPEN))
  {
    for (int i = 0; i < (w * h); i++)
    {
      cells[i].bg = mixI(cells[i].bg, (uint32_t) V(NS_BASE_COLOR), 650);
      cells[i].fg = mixI(cells[i].fg, (uint32_t) V(NS_BASE_COLOR), 650);
    }

    int32_t mw = (w > 64) ? (50) : (w - 10);
    int32_t mh = 11;
    int32_t mx = (w - mw) / 2;
    int32_t my = (h - mh) / 2;
    for (int yy = my; yy < (my + mh); yy++)
      for (int xx = mx; xx < (mx + mw); xx++)
    {
      NsCell *cell = &cells[(yy * w) + xx];
      cell->bg = mixI((uint32_t) V(NS_BASE_COLOR), materialI(config, timeMs, xx * 1024, yy * 1024), 450);
      cell->glyph = ' ';
    }


    boxI(config, cells, timeMs, mx, my, mw, mh);
    textI(config, cells, mx + 3, my + 2, "A SMALL POCKET OF POSSIBILITY", fg);
    textI(config, cells, mx + 3, my + 4, "Keep the stars. Change everything else.", muted);
    barI(config, cells, timeMs, mx + 3, my + 6, mw - 6, V(NS_VALUE_PERMILLE), 2);
    textI(config, cells, mx + 3, my + 8, "[ keep exploring ]        [ close ]", hueI(config, timeMs, 0));
  }
}



static void ribbonI(const NsConfig *config, NsCell *cells, uint64_t timeMs, const uint32_t *text, uint32_t length)
{
  int32_t w = V(NS_WIDTH);
  int32_t h = V(NS_HEIGHT);
  int32_t y = h / 2;
  uint32_t muted = mixI((uint32_t) V(NS_BASE_COLOR), (uint32_t) V(NS_FOREGROUND_COLOR), 480);
  textI(config, cells, 4, 2, "CHROMATIC TYPE / PHASE-LOCKED HUES", muted);
  uint32_t n = (length > ((uint32_t) ((w > 4) ? (w - 4) : (0)))) ? ((uint32_t) ((w > 4) ? (w - 4) : (0))) : (length);
  int32_t x = (w - ((int32_t) n)) / 2;
  for (uint32_t i = 0; i < n; i++)
    putI(config, cells, x + ((int32_t) i), y, text[i], hueI(config, timeMs, (int32_t) i), 0);

  cursorI(config, cells, timeMs, x + ((int32_t) n), y);
  if (h > 12)
  {
    for (int32_t i = 0; i < (w - 8); i++)
    {
      int yy = (h - 6) + (sinI((i * 30) + ((((int64_t) (timeMs % 5000)) * 1024) / 5000)) / 600);
      putI(config, cells, 4 + i, yy, 0x2584, hueI(config, timeMs, i), 0);
    }

    textI(config, cells, 4, h - 3, "hue(i,t) = base + i * step + t * speed", muted);
  }
}



static void scopeI(const NsConfig *config, NsCell *cells, uint64_t timeMs)
{
  int32_t w = V(NS_WIDTH);
  int32_t h = V(NS_HEIGHT);
  if ((w < 8) || (h < 8))
    return;
  uint32_t muted = mixI((uint32_t) V(NS_BASE_COLOR), (uint32_t) V(NS_FOREGROUND_COLOR), 550);
  boxI(config, cells, timeMs, 1, 1, w - 2, h - 2);
  textI(config, cells, 4, 1, " FIELD INSTRUMENTS ", muted);
  textI(config, cells, 4, 3, "synthetic interference / 2 x 4 subcells", muted);
  graphI(config, cells, timeMs, 4, 6, w - 8, ((h - 13) > 0) ? (h - 13) : (1));
  barI(config, cells, timeMs, 4, h - 5, w - 8, V(NS_VALUE_PERMILLE), 0);
  textI(config, cells, 4, h - 3, "data /", muted);
  numberI(config, cells, 11, h - 3, V(NS_VALUE_PERMILLE), hueI(config, timeMs, 0));
}



/* Rendering is pure with respect to config/time; only caller-owned cells change. */
int32_t nsRender(const NsConfig *config, uint64_t motionMs, const uint32_t *text, uint32_t textLength, NsCell *cells, uint32_t capacity)
{
  if (nsValidateConfig(config))
    return -1;
  uint32_t count = (uint32_t) (V(NS_WIDTH) * V(NS_HEIGHT));
  if ((capacity < count) || ((!cells) && count))
    return -2;
  if ((textLength > NS_MAX_TEXT) || ((!text) && textLength))
    return -3;
  uint64_t timeMs = (V(NS_MOTION)) ? (motionMs) : (0);
  int32_t w = V(NS_WIDTH);
  int32_t h = V(NS_HEIGHT);
  for (int32_t y = 0; y < h; y++)
    for (int32_t x = 0; x < w; x++)
  {
    NsCell *cell = &cells[(y * w) + x];
    uint32_t bg = materialI(config, timeMs, x * 1024, y * 1024);
    cell->glyph = ' ';
    cell->fg = (uint32_t) V(NS_FOREGROUND_COLOR);
    cell->bg = bg;
    cell->flags = 0;
    switch (V(NS_PIXEL_MODE))
    {
      case 1:
        cell->glyph = 0x2580;
        cell->fg = materialI(config, timeMs, x * 1024, (y * 1024) + 256);
        cell->bg = materialI(config, timeMs, x * 1024, (y * 1024) + 768);
        break;

      case 2:
        cell->glyph = 0x258c;
        cell->fg = materialI(config, timeMs, (x * 1024) + 256, y * 1024);
        cell->bg = materialI(config, timeMs, (x * 1024) + 768, y * 1024);
        break;

      case 3:
        cell->glyph = (((x + y) % 3) == 0) ? (0x2591) : (0x2592);
        cell->fg = mixI(bg, (uint32_t) V(NS_FOREGROUND_COLOR), 130);
        break;

      case 4:
      {
        static const int32_t levels[4][2] = {{5, 41}, {57, 21}, {29, 61}, {45, 13}};
        static const uint32_t dots[4][2] = {{1, 8}, {2, 16}, {4, 32}, {64, 128}};
        uint32_t mask = 0;
        int32_t baseL = ((redI((uint32_t) V(NS_BASE_COLOR)) + greenI((uint32_t) V(NS_BASE_COLOR))) + blueI((uint32_t) V(NS_BASE_COLOR))) / 3;
        for (int32_t dy = 0; dy < 4; dy++)
          for (int32_t dx = 0; dx < 2; dx++)
        {
          uint32_t sample = materialI(config, timeMs, ((x * 1024) + (dx * 512)) + 256, ((y * 1024) + (dy * 256)) + 128);
          int32_t luminance = ((redI(sample) + greenI(sample)) + blueI(sample)) / 3;
          if ((luminance - baseL) > levels[dy][dx])
            mask |= dots[dy][dx];
        }


        cell->glyph = 0x2800 + mask;
        cell->fg = mixI(bg, (uint32_t) V(NS_FOREGROUND_COLOR), 250);
        break;
      }

      default:
        break;

    }

    if (V(NS_STARS))
      starI(config, timeMs, x, y, cell);
  }


  if (!count)
  {
    return 0;
  }
  static const uint32_t defaultText[] = {'M', 'a', 'k', 'e', ' ', 's', 'o', 'm', 'e', 't', 'h', 'i', 'n', 'g', ' ', 't', 'h', 'a', 't', ' ', 'f', 'e', 'e', 'l', 's', ' ', 'a', 'l', 'i', 'v', 'e', '.'};
  if (!text)
  {
    text = defaultText;
    textLength = (sizeof(defaultText)) / (sizeof(defaultText[0]));
  }
  switch (V(NS_LAYOUT))
  {
    case 1:
      promptI(config, cells, timeMs, text, textLength);
      break;

    case 2:
      controlsI(config, cells, timeMs, text, textLength);
      break;

    case 3:
      ribbonI(config, cells, timeMs, text, textLength);
      break;

    case 4:
      scopeI(config, cells, timeMs);
      break;

    default:
      break;

  }

  return (int32_t) count;
}



/* Additive v0.2 Studio implementation. */
#include "ok_color.inc"
#include "studio.inc"

/* v0.3 Fleet: independent arrival and spatial horizon, no ABI changes. */
NS_API int32_t nsFleetInkOpacity(uint32_t ageMs,uint32_t fadeMs,int32_t rowQ8,int32_t bandQ8,int32_t topMinimum)
{
  if (bandQ8 < 0 || topMinimum < 0 || topMinimum > 1000) return -1;
  int32_t arrival = nsStageTween(0,1000,ageMs,fadeMs,1);
  int32_t horizon = 1000;
  if (bandQ8 > 0 && rowQ8 < bandQ8) {
    uint32_t row = rowQ8 > 0 ? (uint32_t)rowQ8 : 0;
    horizon = nsStageTween(topMinimum,1000,row,(uint32_t)bandQ8,1);
  }
  return arrival * horizon / 1000;
}
