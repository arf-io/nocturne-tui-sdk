#include "window_palette_source.h"

#include <stddef.h>
#include <stdint.h>

/* Test-only ABI introspection shared by the native ctypes test and freestanding
 * Wasm runner. This keeps JSON-to-memory encoding tied to the compiled structs. */
void nrWindowPaletteSourceProbeLayout(uint32_t out[19]) {
    if (!out) return;
    const uint32_t values[19] = {
        (uint32_t)sizeof(NrWindowPaletteSourceConfig),
        (uint32_t)offsetof(NrWindowPaletteSourceConfig, colorCount),
        (uint32_t)offsetof(NrWindowPaletteSourceConfig, weightCount),
        (uint32_t)offsetof(NrWindowPaletteSourceConfig, colors),
        (uint32_t)offsetof(NrWindowPaletteSourceConfig, backgroundRgb),
        (uint32_t)offsetof(NrWindowPaletteSourceConfig, inkRgb),
        (uint32_t)offsetof(NrWindowPaletteSourceConfig, lockLightness),
        (uint32_t)offsetof(NrWindowPaletteSourceConfig, reserved),
        (uint32_t)offsetof(NrWindowPaletteSourceConfig, weights),
        (uint32_t)offsetof(NrWindowPaletteSourceConfig, lightness),
        (uint32_t)offsetof(NrWindowPaletteSourceConfig, chroma),
        (uint32_t)offsetof(NrWindowPaletteSourceConfig, brightness),
        (uint32_t)offsetof(NrWindowPaletteSourceConfig, hueOffsetDegrees),
        (uint32_t)offsetof(NrWindowPaletteSourceConfig, feather),
        (uint32_t)offsetof(NrWindowPaletteSourceConfig, textLightness),
        (uint32_t)offsetof(NrWindowPaletteSourceConfig, textChroma),
        (uint32_t)sizeof(NrWindowPaletteSourcePrepared),
        (uint32_t)offsetof(NrWindowPaletteSourcePrepared, wheel),
        (uint32_t)offsetof(NrWindowPaletteSourcePrepared, stopTotal),
    };
    for (int i = 0; i < 19; ++i) out[i] = values[i];
}
