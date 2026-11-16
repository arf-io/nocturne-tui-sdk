#ifndef NR_WINDOW_APPLICATION_H
#define NR_WINDOW_APPLICATION_H
#include <stdint.h>
#include "source_weather.h"
typedef struct {
 uint32_t enabled,paletteWindowId,scene,backgroundStyle,sampling,orbitMode,motion,starGlyphCount;
 uint64_t atUs;
 double motionMs,travel,orbit,orbit2;
 double fps,gradientScreens,gradientAngle,gradientSpeed,gradientPhase,pivotX,pivotY,axisPitch;
 double rotationSpeed,secondAxisSpeed,swingAngle,swingSeconds,starDensity;
 uint32_t starGlyphs[64];
 double weatherIntensity,novaStrength,novaRegularity,eventSerial;
 NrSourceWeatherOptions particles;
 double starCount,starSpeed,trailMs,travelYaw,travelPitch;
 uint32_t flightCount,flightReserved;
 double flight[256][7]; /* atMs, position xyz, velocity xyz */
 uint32_t eventCount,reserved;
 NrSourceWeatherEvent events[128];
} WindowApplication;
#endif
