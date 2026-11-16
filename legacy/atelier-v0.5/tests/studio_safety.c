/* Native ABI stress suite: randomized validated bounds and every primitive.
 * Includes the renderer to enumerate its private schema range tables safely.
 */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <limits.h>
#include "../src/nocturne.c"
static uint32_t rng=71933;
static uint32_t next(void){rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;return rng;}
int main(void){
 NsStageConfig c;NsCell cells[64*24];NsNode n;NsImpulse e;uint32_t text[]={'6','7'};int32_t data[8]={-1000000,1000000,0,1000,200,600,900,100};int checks=0;
 _Static_assert(sizeof(NsCell)==16,"cell ABI");_Static_assert(sizeof(NsStageConfig)==704,"config ABI");_Static_assert(sizeof(NsNode)==128,"node ABI");_Static_assert(sizeof(NsImpulse)==32,"event ABI");
 for(int iteration=0;iteration<2400;iteration++){
  nsStageDefaults(&c);c.values[NST_WIDTH]=1+next()%64;c.values[NST_HEIGHT]=1+next()%24;
  c.values[NST_PATTERN]=iteration%12;c.values[NST_PIXEL_MODE]=iteration%4;c.values[NST_FOCUS_MODE]=iteration%5;
  int key=iteration%54;if(key>1){int64_t span=(int64_t)ST_MAX[key]-ST_MIN[key]+1;c.values[key]=(int32_t)((int64_t)ST_MIN[key]+next()%span);}
  memset(&n,0,sizeof n);n.values[NTN_KIND]=iteration%14;n.values[NTN_ID]=7;n.values[NTN_X]=(int)(next()%80)-10;n.values[NTN_Y]=(int)(next()%30)-5;n.values[NTN_WIDTH]=next()%64;n.values[NTN_HEIGHT]=next()%24;n.values[NTN_FG]=0x997755;n.values[NTN_BG]=0x12121a;n.values[NTN_FG_OPACITY]=next()%1001;n.values[NTN_BG_OPACITY]=next()%1001;n.values[NTN_STYLE]=next()%16;n.values[NTN_TEXT_LENGTH]=2;n.values[NTN_DATA_LENGTH]=8;n.values[NTN_ZOOM]=1+next()%4;n.values[NTN_VALUE]=(int32_t)next();n.values[NTN_FROM_VALUE]=(int32_t)next();n.values[NTN_DURATION_MS]=next()%3600001;n.values[NTN_COLOR_ANIMATION]=iteration%3;n.values[NTN_HUE_SATURATION]=700;n.values[NTN_HUE_BRIGHTNESS]=800;n.values[NTN_HUE_SPEED]=3600;n.values[NTN_HUE_STEP]=-3600;
  memset(&e,0,sizeof e);e.values[0]=next()%16000;e.values[1]=next()%6000;e.values[2]=next()%1001;e.values[3]=iteration%2;
  uint64_t t=iteration%3==0?UINT64_MAX:iteration%3==1?((uint64_t)next()<<32)|next():next()%15000;
  int count=nsStageRender(&c,t,&e,1,&n,1,text,2,data,8,cells,64*24);assert(count==c.values[0]*c.values[1]);checks++;
  assert(nsStageHit(&n,1,data,8,10,10)>=0);checks++;
 }
 nsStageDefaults(&c);c.values[0]=1;c.values[1]=1;cells[0]=(NsCell){65,1,2,3};NsCell before=cells[0];
 assert(nsStageRender(&c,0,NULL,129,NULL,0,NULL,0,NULL,0,cells,1)==-3);assert(memcmp(cells,&before,16)==0);checks++;
 c.values[NST_PERIOD_MS]=0;assert(nsStageRender(&c,0,NULL,0,NULL,0,NULL,0,NULL,0,cells,1)==-1);assert(memcmp(cells,&before,16)==0);checks++;
 for(int k=0;k<4;k++){assert(nsStageTween(INT_MIN,INT_MAX,0,1,k)==INT_MIN);assert(nsStageTween(INT_MIN,INT_MAX,1,1,k)==INT_MAX);checks+=2;}
 printf("PASS: %d Studio sanitizer assertions; 2400 randomized scenes\n",checks);return 0;
}
