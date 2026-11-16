#ifndef NR_WINDOW_ATELIER_H
#define NR_WINDOW_ATELIER_H
#include <stdint.h>
typedef struct {double from,to;uint64_t atUs,durationUs;} NrAtelierTween;
typedef struct {
 uint32_t enabled,mode,rolled,chrome,customSide,toolWidth,toolHeight,reserved;
 uint32_t order[4],glyphs[4],colors[4];
 double fadeFloor;
 NrAtelierTween visibility,fade,maximize,body;
} SourceAtelierWindow;
#endif
