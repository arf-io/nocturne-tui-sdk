#include "source_weather.h"
#include <string.h>
int nrSourceWeatherProbe(uint32_t kind,const double *event,const double *values,
 const uint32_t *glyphs,uint32_t glyphCount,double weight,const uint32_t *wheel,
 uint32_t width,uint32_t height,uint32_t *cells,double *sample) {
 NrSourceWeatherOptions options;nrSourceWeatherDefaults(&options);
 memcpy(&options,values,18*sizeof(double));options.glyphCount=glyphCount;
 if(glyphCount<=64)memcpy(options.glyphs,glyphs,glyphCount*sizeof(uint32_t));
 NrSourceWeatherEvent e={kind,event[0],event[1],event[2],event[3]};
 NrSourceWeatherSample s;int rc=nrSourceWeatherSample(&e,event[4],&options,&s);if(rc)return rc;
 sample[0]=s.pointCount;sample[1]=s.segmentCount;sample[2]=s.core;sample[3]=s.radius;sample[4]=s.shockwave;
 int at=5;for(uint32_t i=0;i<s.pointCount;i++){NrSourceWeatherPoint*p=&s.points[i];
 sample[at++]=p->x;sample[at++]=p->y;sample[at++]=p->opacity;sample[at++]=p->heat;sample[at++]=p->size;sample[at++]=p->glyph;}
 for(uint32_t i=0;i<s.segmentCount;i++){NrSourceWeatherSegment*p=&s.segments[i];
 sample[at++]=p->x1;sample[at++]=p->y1;sample[at++]=p->x2;sample[at++]=p->y2;sample[at++]=p->opacity;sample[at++]=p->heat;sample[at++]=p->branch;}
 return nrSourceWeatherPaint(&e,event[4],&options,weight,wheel,width,height,cells);
}

int nrSourceWeatherLayerProbe(const uint32_t *kinds,const double *events,uint32_t count,
 double timeMs,const double *values,const uint32_t *glyphs,uint32_t glyphCount,
 const double *layer,const uint32_t *wheel,uint32_t width,uint32_t height,uint32_t *cells) {
 if(count>64)return -1;NrSourceWeatherOptions options;nrSourceWeatherDefaults(&options);
 memcpy(&options,values,18*sizeof(double));options.glyphCount=glyphCount;
 if(glyphCount<=64)memcpy(options.glyphs,glyphs,glyphCount*sizeof(uint32_t));
 NrSourceWeatherEvent e[64];for(uint32_t i=0;i<count;i++)e[i]=(NrSourceWeatherEvent){kinds[i],events[i*4],events[i*4+1],events[i*4+2],events[i*4+3]};
 return nrSourceWeatherPaintLayer(e,count,timeMs,&options,layer[0],layer[1],layer[2],wheel,width,height,cells);
}
