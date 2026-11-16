#ifndef NR_DOCUMENT_BIDI_H
#define NR_DOCUMENT_BIDI_H
#include <stdint.h>
/* Forty uint32 words per (scalar+1). Output, source and scratch are disjoint.
 * Scratch is mutable workspace; output remains unchanged on rejection. */
int nrDocumentBidiClusterLayout(const uint32_t*,uint32_t,uint32_t,uint32_t,uint32_t,
    uint32_t*,uint32_t,uint32_t*,uint64_t);
#endif
