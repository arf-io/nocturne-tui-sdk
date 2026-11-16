#include "nocturne_native.h"
#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
static void command(NrContext*c,const char*s){assert(nrCommand(c,s,(uint32_t)strlen(s))==0);}
int main(void){uint32_t n=nrContextSize();NrContext*c=malloc(n);assert(c&&nrInit(c,n,2030)==0);
 assert(nrSourceStageTween(INT32_MIN,INT32_MAX,UINT64_MAX,UINT32_MAX,3)==INT32_MAX);assert(nrSourceStageTween(INT32_MIN,INT32_MAX,UINT32_MAX-1,UINT32_MAX,2)<=INT32_MAX);
 assert(nrSourceStageInkOpacity(UINT32_MAX,UINT32_MAX,INT32_MIN,INT32_MAX,0)==0);
 command(c,"{\"op\":\"source-stage-component\",\"id\":1,\"legacyFlags\":2147483647,\"kind\":\"scatter\",\"x\":-4096,\"y\":-4096,\"width\":1073741823,\"height\":536870911,\"data\":[1000,0,0,1000]}");
 int32_t row[2]={91,92};int result=nrSourceStageHit(c,0,0,row,2);assert(result==0);assert(row[0]==91&&row[1]==92);
 assert(nrSourceStageHit(c,0,0,(int32_t*)c,2)==-1);assert(nrSourceStageHit(c,0,0,(int32_t*)((char*)row+1),2)==-1);assert(nrSourceStageHit(c,0,0,(int32_t*)(UINTPTR_MAX-3),2)==-1);
 command(c,"{\"op\":\"source-stage-component\",\"id\":1,\"legacyFlags\":2147483647,\"kind\":\"donut\",\"x\":-4096,\"y\":-4096,\"width\":1073741823,\"height\":536870911,\"data\":[1000000,1000000]}");assert(nrSourceStageHit(c,4096,4096,row,2)==0);
 command(c,"{\"op\":\"source-stage\",\"timeMs\":9007199254740991,\"events\":[{\"x\":1.5,\"y\":-2.5,\"atMs\":9007199254740991}]}");
 free(c);return 0;}
