#ifndef NR_GRAPHEME_CURSOR_H
#define NR_GRAPHEME_CURSOR_H
#include <stdint.h>
/* Constant-size extended-grapheme state. Source is validated before emission. */
typedef struct {
    const uint32_t *text;
    uint32_t count,index,riRun;
    int started,finished,previous,epChain,previousZwjHasEp,indic;
} NrGraphemeCursor;
int nrGraphemeCursorNext(NrGraphemeCursor*,uint32_t*);
static inline int nrGraphemeOutputOverlaps(const uint32_t*text,uint32_t count,const uint32_t*out,uint64_t words){
    if(!count||!words)return 0;
    uint64_t sourceBytes=(uint64_t)count*4,outputBytes=words*4;
    if(sourceBytes>UINTPTR_MAX||outputBytes>UINTPTR_MAX)return 1;
    uintptr_t a=(uintptr_t)text,b=(uintptr_t)out;
    return a<=b?(uint64_t)(b-a)<sourceBytes:(uint64_t)(a-b)<outputBytes;
}
#endif
