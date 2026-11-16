#ifndef NR_WINDOW_CONTENT_H
#define NR_WINDOW_CONTENT_H
#include "window_palette_source.h"
typedef struct {
    uint32_t enabled,sourceIndex,labelCount,textCount;
    uint32_t label[64],text[4096];
    NrWindowPaletteSourceConfig palette;
    double waveform[128];
    uint64_t atUs,maxAtUs;
    double visibilityFrom,visibilityTo,visibilityDurationUs,maxFrom,maxTo;
    int32_t transitionEffect;
    uint32_t reserved;
} WindowContent;
#endif
