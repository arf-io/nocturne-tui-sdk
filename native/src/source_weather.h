#ifndef NR_SOURCE_WEATHER_H
#define NR_SOURCE_WEATHER_H
#include <stdint.h>
enum { NR_SOURCE_WEATHER_EMBERS, NR_SOURCE_WEATHER_SPARKS, NR_SOURCE_WEATHER_NOVA,
 NR_SOURCE_WEATHER_RAIN, NR_SOURCE_WEATHER_SNOW, NR_SOURCE_WEATHER_RIPPLES };
enum { NR_SOURCE_WEATHER_MAX_POINTS=160, NR_SOURCE_WEATHER_MAX_SEGMENTS=384 };
typedef struct {
 double count,lifeMs,launchSpeed,gravity,drag,wind,flickerHz,trailMs,branches,arcSegments,
 arcJitter,coreMs,shockwave,explosionForce,seed,brightness,emberSpread,arcReach;
 uint32_t glyphCount,glyphs[64];
} NrSourceWeatherOptions;
typedef struct { uint32_t kind; double id,x,y,atMs; } NrSourceWeatherEvent;
typedef struct { double x,y,opacity,heat,size; uint32_t glyph; } NrSourceWeatherPoint;
typedef struct { double x1,y1,x2,y2,opacity,heat; uint32_t branch; } NrSourceWeatherSegment;
typedef struct {
 uint32_t pointCount,segmentCount; double core,radius,shockwave;
 NrSourceWeatherPoint points[NR_SOURCE_WEATHER_MAX_POINTS];
 NrSourceWeatherSegment segments[NR_SOURCE_WEATHER_MAX_SEGMENTS];
} NrSourceWeatherSample;
void nrSourceWeatherDefaults(NrSourceWeatherOptions *options);
int nrSourceWeatherValidate(const NrSourceWeatherOptions *options);
/* Return 0 on success, -1 on invalid input. Invalid calls leave output intact. */
int nrSourceWeatherSample(const NrSourceWeatherEvent *event,double timeMs,
 const NrSourceWeatherOptions *options,NrSourceWeatherSample *output);
int nrSourceWeatherPaint(const NrSourceWeatherEvent *event,double timeMs,
 const NrSourceWeatherOptions *options,double weight,const uint32_t wheel360[360],
 uint32_t width,uint32_t height,uint32_t *cells4);
/* Whole original Kinetic weather layer: final 24 eligible explicit events in
 * caller order, then at most two automatic nova events. Returns event count,
 * or -1 without mutation on invalid input. Rendering never inserts events. */
int nrSourceWeatherPaintLayer(const NrSourceWeatherEvent *events,uint32_t eventCount,
 double timeMs,const NrSourceWeatherOptions *options,double weatherIntensity,
 double novaStrength,double novaRegularity,const uint32_t wheel360[360],
 uint32_t width,uint32_t height,uint32_t *cells4);
/* The same layer with writes limited to the clip rectangle; geometry uses the full width and height,
 * so the cells inside the clip equal an unclipped paint. A clip outside the grid is invalid (-1). */
int nrSourceWeatherPaintLayerClipped(const NrSourceWeatherEvent *events,uint32_t eventCount,
 double timeMs,const NrSourceWeatherOptions *options,double weatherIntensity,
 double novaStrength,double novaRegularity,const uint32_t wheel360[360],
 uint32_t width,uint32_t height,uint32_t *cells4,uint32_t clipX,uint32_t clipY,uint32_t clipWidth,uint32_t clipHeight);
/* Shared original subcell line painter, also used by the spatial star trails. */
int nrSourcePaintCell(double,double,uint32_t,uint32_t,double,uint32_t,uint32_t,uint32_t*);
int nrSourceWeatherDrawSegment(double x0,double y0,double x1,double y1,uint32_t color,
 double alpha,uint32_t width,uint32_t height,uint32_t*cells4);
#endif
