#include "window_content_source.h"

int nrWindowContentSourceProbe(uint32_t width,uint32_t height,uint32_t shape,
    const uint32_t *title,uint32_t titleCount,const uint32_t *body,uint32_t bodyCount,
    const uint32_t *label,uint32_t labelCount,double clockMs,
    uint32_t ink,uint32_t background,uint32_t accent,const uint32_t *ramp,
    double stopTotal,const double *waveform,uint32_t waveformCount,uint32_t *cells4) {
    NrWindowContentSource source={width,height,shape,title,titleCount,body,bodyCount,
        label,labelCount,clockMs,ink,background,accent,ramp,stopTotal,waveform,
        waveformCount,cells4};
    return nrWindowContentSourceRender(&source);
}
