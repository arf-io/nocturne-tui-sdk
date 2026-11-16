#ifndef NR_WINDOW_PRESENTATION_H
#define NR_WINDOW_PRESENTATION_H

#include "window_source_presentation.h"

typedef struct {
    int x, y, width, height;
    int action, index;
} NrWindowPresentationControlRect;

/* The RC2 theatre row shares exact descriptor geometry between paint and hit. */
int nrWindowPresentationControlRects(
    int frameWidth, const NrWindowSourcePresentationOptions *options,
    NrWindowPresentationControlRect out[4]);
int nrWindowPresentationControlHit(
    int frameWidth, const NrWindowSourcePresentationOptions *options,
    int x, int y);

#endif
