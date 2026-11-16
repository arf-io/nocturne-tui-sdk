#ifndef NR_OBSERVATORY_SOURCE_BACKGROUND_H
#define NR_OBSERVATORY_SOURCE_BACKGROUND_H
#include "window_application.h"
#include "window_palette_source.h"
int nrObservatorySourceProject(const Camera*,Vec3,double,double,double*,double*,double*);
void nrObservatorySourceWarp(NrContext*,const WindowApplication*,const NrWindowPaletteSourcePrepared*,double,double);
void nrObservatorySourceWeather(NrContext*,const WindowApplication*,const NrWindowPaletteSourcePrepared*,double);
#endif
