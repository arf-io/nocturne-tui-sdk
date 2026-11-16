/* Browser scratch ABI. One synchronous render at a time per WASM instance.
 * Native clients call nsRender with their own buffers and do not use this file. */
#include "nocturne.h"
static NsConfig CONFIG;
static NsCell FRAME[NS_MAX_CELLS];
static uint32_t TEXT[NS_MAX_TEXT];
NS_API NsConfig *nsConfigPtr(void){return &CONFIG;}
NS_API NsCell *nsFramePtr(void){return FRAME;}
NS_API uint32_t *nsTextPtr(void){return TEXT;}
NS_API void nsInit(void){nsDefaultConfig(&CONFIG);}
NS_API int32_t nsRenderFrame(uint32_t timeLo,uint32_t timeHi,uint32_t textLength){return nsRender(&CONFIG,((uint64_t)timeHi<<32)|timeLo,TEXT,textLength,FRAME,NS_MAX_CELLS);}
#include "nocturne_studio.h"
static NsStageConfig STUDIO_CONFIG;
static NsImpulse STUDIO_EVENTS[NST_MAX_EVENTS];
static NsNode STUDIO_NODES[NST_MAX_NODES];
static uint32_t STUDIO_TEXT[NST_MAX_TEXT];
static int32_t STUDIO_DATA[NST_MAX_DATA];
NS_API NsStageConfig *nsStageConfigPtr(void){return &STUDIO_CONFIG;}
NS_API NsImpulse *nsStageEventsPtr(void){return STUDIO_EVENTS;}
NS_API NsNode *nsStageNodesPtr(void){return STUDIO_NODES;}
NS_API uint32_t *nsStageTextPtr(void){return STUDIO_TEXT;}
NS_API int32_t *nsStageDataPtr(void){return STUDIO_DATA;}
NS_API void nsStageInit(void){nsStageDefaults(&STUDIO_CONFIG);}
NS_API int32_t nsStageRenderFrame(uint32_t lo,uint32_t hi,uint32_t ev,uint32_t nodes,uint32_t text,uint32_t data){return nsStageRender(&STUDIO_CONFIG,((uint64_t)hi<<32)|lo,STUDIO_EVENTS,ev,STUDIO_NODES,nodes,STUDIO_TEXT,text,STUDIO_DATA,data,FRAME,NS_MAX_CELLS);}
NS_API int32_t nsStageHitFrame(uint32_t nodes,uint32_t data,int32_t x,int32_t y){return nsStageHit(STUDIO_NODES,nodes,STUDIO_DATA,data,x,y);}
static NsCell STUDIO_LAYER[NS_MAX_CELLS];
NS_API NsCell *nsStageLayerPtr(void){return STUDIO_LAYER;}
NS_API int32_t nsStageTweenWords(int32_t from,int32_t to,uint32_t lo,uint32_t hi,uint32_t duration,int32_t ease){return nsStageTween(from,to,((uint64_t)hi<<32)|lo,duration,ease);}

NS_API int32_t nsStagePaintFrame(uint32_t lo,uint32_t hi,uint32_t nodes,uint32_t text,uint32_t data){return nsStagePaint(&STUDIO_CONFIG,((uint64_t)hi<<32)|lo,STUDIO_NODES,nodes,STUDIO_TEXT,text,STUDIO_DATA,data,FRAME,NS_MAX_CELLS);}

#include "nocturne_world.h"
static NsWorldConfig WORLD_CONFIG;
static uint32_t WORLD_COLORS[NS_MAX_CELLS*8];
static int32_t WORLD_DEPTH[NS_MAX_CELLS*8];
NS_API NsWorldConfig *nsWorldConfigPtr(void){return &WORLD_CONFIG;}
NS_API int32_t nsWorldRenderFrame(uint32_t lo,uint32_t hi){return nsWorldRender(&WORLD_CONFIG,((uint64_t)hi<<32)|lo,FRAME,NS_MAX_CELLS,WORLD_COLORS,WORLD_DEPTH,NS_MAX_CELLS*8);}

static NsWorldDetail WORLD_DETAIL;
static NsWorldTriangle WORLD_MESH[NSW_MAX_TRIANGLES];
NS_API NsWorldDetail *nsWorldDetailPtr(void){return &WORLD_DETAIL;}
NS_API NsWorldTriangle *nsWorldMeshPtr(void){return WORLD_MESH;}
NS_API int32_t nsWorldRenderDetailedFrame(uint32_t lo,uint32_t hi){return nsWorldRenderDetailed(&WORLD_CONFIG,((uint64_t)hi<<32)|lo,&WORLD_DETAIL,FRAME,NS_MAX_CELLS,WORLD_COLORS,WORLD_DEPTH,NS_MAX_CELLS*8);}
NS_API int32_t nsWorldRenderMeshFrame(uint32_t lo,uint32_t hi,uint32_t count){return nsWorldRenderMesh(&WORLD_CONFIG,((uint64_t)hi<<32)|lo,WORLD_MESH,count,FRAME,NS_MAX_CELLS,WORLD_COLORS,WORLD_DEPTH,NS_MAX_CELLS*8);}
