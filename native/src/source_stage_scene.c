/* Original Stage background and controls, composed with the current node pool.
 * The original stActive/stSample/stStar/stQuantize arithmetic is retained below;
 * field/palette sampling delegates to the already qualified current sampler. */
#include "internal.h"
#include "../../include/nocturne_studio.h"
#include "../../src/studio_defaults.inc"
#include <limits.h>
#define S(k) (config->values[NST_##k])
/* ST_MAX[0..1] (512,256) is the archived library's declared extent for its own
 * NsStageConfig callers, not a limit of the scene. The only limits are where the
 * retained int32 arithmetic below stops being representable for every admitted
 * config and event. Cells sample at Q8 x*256+-64 and y*256+-96, and stSample forms
 * x-e[0] and (int)((y-e[1])*cellAspect/1000) against impulses anywhere in the
 * +-1048576 Q8 (+-4096-cell) event domain, with cellAspect up to 4000:
 *   (8384512-1)*256+64+1048576 = 2147483456 <= INT32_MAX (width+1 exceeds it);
 *   ((2093056-1)*256+96+1048576)*4 = 2147483008 <= INT32_MAX (height+1 exceeds it).
 * Novas lie 30/14 cells before and 29/13 past the far edge; their Q8 terms
 * (width+29)*256+64 and ((height+13)*256+96)*4 also fit at these bounds. */
#define NR_SOURCE_STAGE_MAX_WIDTH 8384512
#define NR_SOURCE_STAGE_MAX_HEIGHT 2093056
_Static_assert(sizeof(*((NrContext*)0)->plotColor)==sizeof(NsImpulse),"One active impulse per viewport cell of plot scratch");
static int32_t clampI(int32_t x,int32_t lo,int32_t hi){return x<lo?lo:x>hi?hi:x;}
static int32_t modI(int64_t n,int32_t d){int32_t r=(int32_t)(n%d);return r<0?r+d:r;}
static int32_t smoothI(int32_t p){return (int32_t)((int64_t)p*p*(3000-2*p)/1000000);}
static uint32_t hashI(uint32_t v){v^=v>>16;v*=0x7feb352du;v^=v>>15;v*=0x846ca68bu;return v^(v>>16);}
static int32_t redI(uint32_t c){return c>>16&255;}static int32_t greenI(uint32_t c){return c>>8&255;}static int32_t blueI(uint32_t c){return c&255;}
static uint32_t rgbI(int r,int g,int b){return (uint32_t)clampI(r,0,255)<<16|(uint32_t)clampI(g,0,255)<<8|(uint32_t)clampI(b,0,255);}
static uint32_t mixI(uint32_t a,uint32_t b,int32_t p){p=clampI(p,0,1000);return rgbI(redI(a)+(redI(b)-redI(a))*p/1000,greenI(a)+(greenI(b)-greenI(a))*p/1000,blueI(a)+(blueI(b)-blueI(a))*p/1000);}
static uint64_t sqrtI(uint64_t n){uint64_t r=0,b=UINT64_C(1)<<62;while(b>n)b>>=2;while(b){if(n>=r+b){n-=r+b;r=(r>>1)+b;}else r>>=1;b>>=2;}return r;}
static uint32_t flattenedBg(const NsCell*c){return c->glyph==0x2580||c->glyph==0x2584||c->glyph==0x258c||c->glyph==0x2590?mixI(c->bg,c->fg,500):c->bg;}
static uint32_t safeGlyph(uint32_t g){return (g>=32&&g<=126)||(g>=0x2800&&g<=0x28ff)||g==0xb7||g==0x2022||g==0x2219||g==0x22c5||g==0x22c6||g==0x207a||g==0x2217?g:'?';}
static const uint32_t ST_ANSI16[16]={0x000000,0xaa0000,0x00aa00,0xaa5500,0x0000aa,0xaa00aa,0x00aaaa,0xaaaaaa,0x555555,0xff5555,0x55ff55,0xffff55,0x5555ff,0xff55ff,0x55ffff,0xffffff};
static int32_t stAbs(int32_t x){return x<0?-x:x;}
static uint64_t stTime(const int32_t *v){return ((uint64_t)(uint32_t)v[1]<<32)|(uint32_t)v[0];}
static uint32_t stGlyph(uint32_t g){
 if((g>=0x2190&&g<=0x22ff)||(g>=0x2500&&g<=0x25ff)||g==0x2726||g==0x2727||g==0x203a||g==0x2039||g==0xd7||g==0xb0)return g;
 return safeGlyph(g);
}
static uint32_t stHash(int32_t seed,int32_t x,int32_t y){return hashI((uint32_t)seed^(uint32_t)x*0x9e3779b9u^(uint32_t)y*0x85ebca6bu);}
static int32_t stFloor(int32_t n,int32_t d){int32_t q=n/d;return n<0&&n%d?q-1:q;}
static uint64_t stDistance(int32_t x,int32_t y){return sqrtI((uint64_t)((int64_t)x*x)+(uint64_t)((int64_t)y*y));}
void nrSourceStagePalette(const SourceStageScene*q,NrSourceMaterialSampler*p){
 nrSourceMaterialSamplerDefaults(p);
 p->pattern=q->values[2];
 p->focusMode=q->values[3];
 p->focusXQ8=q->values[4];
 p->focusYQ8=q->values[5];
 p->periodMs=q->values[6];
 p->saturationMilli=q->values[7];
 p->brightnessMilli=q->values[8];
 p->speedFalloffMilli=q->values[9];
 p->saturationFalloffMilli=q->values[10];
 p->brightnessFalloffMilli=q->values[11];
 p->cellAspectMilli=q->values[12];
 p->scaleQ8=q->values[13];
 p->angleMilliDegrees=q->values[14];
 p->pivotXQ8=q->values[15];
 p->pivotYQ8=q->values[16];
 p->rotationPeriodMs=q->values[17];
 p->rotationMode=q->values[18];
 p->swingMilliDegrees=q->values[19];
 p->phase1024=q->values[20];
 p->seed=q->values[22];
 p->baseRgb=q->values[23];
 p->inkRgb=q->values[24];
 p->paletteCount=q->values[25];
 p->gradientWrap=q->values[26];
 p->interpolation=q->values[27];
 p->colorMode=q->values[28];
 p->hueOffsetDegrees=q->values[29];
 p->motion=q->values[47];
 p->originXCells=q->values[49];
 p->originYCells=q->values[50];
 p->waveAmplitudeMilli=q->values[51];
 p->reverse=q->values[53];
 memcpy(p->palette,q->palette,sizeof(p->palette));
}
static uint32_t stPalette(const SourceStageScene*config,int64_t phase){NrSourceMaterialSampler p;nrSourceStagePalette(config,&p);uint32_t out=(uint32_t)S(BASE_COLOR);nrSourceMaterialPaletteColor(&p,phase,&out);return out;}
static uint32_t stField(const SourceStageScene*config,uint64_t t,int32_t x,int32_t y){NrSourceMaterialSampler p;nrSourceStagePalette(config,&p);uint32_t out=(uint32_t)S(BASE_COLOR);nrSourceMaterialSampleColor(&p,t*1000,x,y,&out);return out;}
static uint32_t stQuantize(uint32_t c,int mode){
 if(!mode)return c;
 int best=2147483647;uint32_t result=0;
 if(mode==1){for(int i=0;i<16;i++){int dr=redI(c)-redI(ST_ANSI16[i]),dg=greenI(c)-greenI(ST_ANSI16[i]),db=blueI(c)-blueI(ST_ANSI16[i]);int d=dr*dr+dg*dg+db*db;if(d<best){best=d;result=ST_ANSI16[i];}}return result;}
 static const int cube[6]={0,95,135,175,215,255};int parts[3]={redI(c),greenI(c),blueI(c)},v[3];
 for(int k=0;k<3;k++){int m=9999;v[k]=0;for(int i=0;i<6;i++){int d=stAbs(parts[k]-cube[i]);if(d<m){m=d;v[k]=cube[i];}}}
 result=rgbI(v[0],v[1],v[2]);int dr=parts[0]-v[0],dg=parts[1]-v[1],db=parts[2]-v[2];best=dr*dr+dg*dg+db*db;
 for(int i=0;i<24;i++){int g=8+i*10;dr=parts[0]-g;dg=parts[1]-g;db=parts[2]-g;int d=dr*dr+dg*dg+db*db;if(d<best){best=d;result=rgbI(g,g,g);}}
 for(int i=0;i<16;i++){dr=parts[0]-redI(ST_ANSI16[i]);dg=parts[1]-greenI(ST_ANSI16[i]);db=parts[2]-blueI(ST_ANSI16[i]);int d=dr*dr+dg*dg+db*db;if(d<best){best=d;result=ST_ANSI16[i];}}
 return result;
}
static uint32_t stActive(const SourceStageScene *config,uint64_t timeMs,const NsImpulse *events,uint32_t n,NsImpulse *out,uint32_t capacity){
 uint32_t count=0;
 for(uint32_t i=0;i<n;i++){uint64_t at=stTime(&events[i].values[4]);uint64_t life=events[i].values[3]?S(NOVA_DURATION_MS):S(RIPPLE_LIFE_MS);if(timeMs>=at&&timeMs-at<life)out[count++]=events[i];}
 if(!S(STARS)||!S(NOVA_CHANCE))return count;
 int32_t x0=stFloor(S(ORIGIN_X),32),x1=stFloor(S(ORIGIN_X)+S(WIDTH)-1,32);
 int32_t y0=stFloor(S(ORIGIN_Y),16),y1=stFloor(S(ORIGIN_Y)+S(HEIGHT)-1,16);
 for(int32_t ty=y0;ty<=y1;ty++)for(int32_t tx=x0;tx<=x1;tx++){
  uint32_t h=stHash(S(SEED)^14593,tx,ty),period=S(NOVA_CYCLE_MS),offset=hashI(h)%period;
  /* Split quotient/remainder avoids overflowing timeMs + offset. */
  uint64_t cycle=timeMs/period;uint32_t within=(uint32_t)(timeMs%period);within+=offset;if(within>=period){within-=period;cycle++;}
  for(int back=0;back<=S(NOVA_DURATION_MS)/S(NOVA_CYCLE_MS)+1;back++){
   if(cycle<(uint64_t)back)break;
   uint64_t age=(uint64_t)within+(uint64_t)back*period;
   if(age>timeMs||age>=(uint32_t)S(NOVA_DURATION_MS)||hashI(h^(uint32_t)(cycle-back))%1000>=(uint32_t)S(NOVA_CHANCE))continue;
   int32_t wx=tx*32+1+(int32_t)(hashI(h^7u)%30),wy=ty*16+1+(int32_t)(hashI(h^19u)%14);
   if(count>=capacity)return count;
   NsImpulse e={{(wx-S(ORIGIN_X))*256,(wy-S(ORIGIN_Y))*256,850,1,0,0,(int32_t)h,0}};
   uint64_t at=timeMs-age;e.values[4]=(int32_t)(uint32_t)at;e.values[5]=(int32_t)(uint32_t)(at>>32);out[count++]=e;break; /* latest eligible burst per tile */
  }
 }
 return count;
}
static uint32_t stSample(const SourceStageScene *config,uint64_t t,int x,int y,const NsImpulse *ev,uint32_t count){
 uint32_t color=stField(config,t,x,y);
 for(uint32_t i=0;i<count;i++){
  const int32_t *e=ev[i].values;uint64_t age=t-stTime(&e[4]);int life=e[3]?S(NOVA_DURATION_MS):S(RIPPLE_LIFE_MS);
  int dx=x-e[0],dy=(int)((int64_t)(y-e[1])*S(CELL_ASPECT)/1000);
  int64_t radius=(int64_t)age*S(RIPPLE_SPEED)/1000;
  if((int64_t)stAbs(dx)>radius+S(RIPPLE_WIDTH)||(int64_t)stAbs(dy)>radius+S(RIPPLE_WIDTH))continue;
  int distance=(int)stDistance(dx,dy);
  int fade=smoothI(1000-(int)(age*1000/(uint32_t)life));
  int peak=0;
  for(int k=0;k<S(RIPPLE_RINGS);k++){
   int64_t r=radius-(int64_t)k*S(RIPPLE_WIDTH)*4;if(r<0)continue;
   int64_t delta=(int64_t)distance-r;if(delta<0)delta=-delta;
   if(delta<S(RIPPLE_WIDTH)){int a=smoothI(1000-(int)(delta*1000/S(RIPPLE_WIDTH)));a=a*fade/1000;a=a*e[2]/1000;a=a*S(RIPPLE_OPACITY)/1000;a=a*1000/(1000+k*420);if(a>peak)peak=a;}
  }
  if(peak)color=mixI(color,stPalette(config,(int64_t)(uint32_t)e[6]%1024+(int64_t)distance*1024/S(SCALE)),peak);
 }
 return color;
}
static void stStar(const SourceStageScene *config,uint64_t t,int x,int y,NsCell *cell,const NsImpulse *events,uint32_t count){
 uint32_t h=stHash(S(SEED),x+S(ORIGIN_X),y+S(ORIGIN_Y));
 int wx=x+S(ORIGIN_X),wy=y+S(ORIGIN_Y),tx=stFloor(wx,32),ty=stFloor(wy,16);
 uint32_t nh=stHash(S(SEED)^14593,tx,ty);
 int candidate=S(NOVA_CHANCE)&&wx==tx*32+1+(int32_t)(hashI(nh^7u)%30)&&wy==ty*16+1+(int32_t)(hashI(nh^19u)%14);
 if(S(STARS)&&(candidate||h%1000<(uint32_t)S(STAR_DENSITY))){
  uint32_t period=S(STAR_MIN_MS)+hashI(h^13u)%((uint32_t)S(STAR_RANGE_MS)+1);
  uint32_t p=(uint32_t)((t%period+hashI(h^97u)%period)%period),duration=(uint32_t)((uint64_t)period*(uint32_t)S(STAR_DUTY)/1000);
  if(duration<2){duration=2;}
  uint32_t attack=(uint32_t)((uint64_t)duration*(uint32_t)S(STAR_ATTACK)/1000);if(attack<1)attack=1;if(attack>=duration)attack=duration-1;
  int a=0;if(p<duration)a=p<attack?smoothI((int)((uint64_t)p*1000/attack)):smoothI((int)((uint64_t)(duration-p)*1000/(duration-attack)));
  a=a*S(STAR_PEAK)/1000;
  if(a>6){cell->bg=flattenedBg(cell);cell->glyph=stGlyph(config->glyphs[hashI(h^31u)%(uint32_t)S(STAR_GLYPH_COUNT)]);cell->fg=mixI(cell->bg,config->starPalette[hashI(h^79u)%(uint32_t)S(STAR_COLOR_COUNT)],a);}
 }
 for(uint32_t i=0;i<count;i++){
  const int32_t *e=events[i].values;if(!e[3]||e[0]/256!=x||e[1]/256!=y)continue;
  int p=(int)((t-stTime(&e[4]))*1000/(uint32_t)S(NOVA_DURATION_MS));
  int envelope=p<240?smoothI(p*1000/240):smoothI((1000-p)*1000/760);
  int index=envelope*(S(NOVA_GLYPH_COUNT)-1)/1000;cell->bg=flattenedBg(cell);cell->glyph=stGlyph(config->novaGlyphs[index]);
  cell->fg=mixI(cell->bg,config->starPalette[(uint32_t)e[6]%(uint32_t)S(STAR_COLOR_COUNT)],envelope);
 }
}

uint64_t nrSourceStageTime(const State*s){return s->sourceStageScene.enabled?(s->sourceStageScene.values[NST_MOTION]?s->sourceStageScene.timeMs:0):s->timeUs/1000;}
static void defaults(SourceStageScene*q){
 memset(q,0,sizeof(*q));q->enabled=1;memcpy(q->values,ST_DEFAULT,sizeof(q->values));q->values[0]=q->values[1]=0;
 const uint32_t p[]={0x28304f,0x785c89,0x367876,0xae7357,0x504565},sp[]={0xb6a4c4,0x9fb9b0,0xc7bca7,0x9cacca,0xc6a0aa,0xadbdbb},g[]={'.',0xb7,0x2219,0x22c5,0x2801,0x2802,0x2804,0x2840,0x2808,0x2810,0x2820,0x2880},ng[]={0xb7,0x2219,'*',0x2726,0x2727};
 memcpy(q->palette,p,sizeof(p));memcpy(q->starPalette,sp,sizeof(sp));memcpy(q->glyphs,g,sizeof(g));memcpy(q->novaGlyphs,ng,sizeof(ng));
}
int nrValidSourceStageScene(const State*s){
 const SourceStageScene*q=&s->sourceStageScene;if(!q->enabled){SourceStageScene zero={0};return !memcmp(q,&zero,sizeof(zero));}
 if(q->enabled!=1||s->schema<NR_STATE_SCHEMA_SOURCE_STAGE_SCENE||s->width>NR_SOURCE_STAGE_MAX_WIDTH||s->height>NR_SOURCE_STAGE_MAX_HEIGHT||q->eventCount>128||q->timeMs>9007199254740991ULL||q->values[0]||q->values[1])return 0;
 for(int i=2;i<ST_FIELD_COUNT;i++)if(q->values[i]<ST_MIN[i]||q->values[i]>ST_MAX[i])return 0;
 for(int i=ST_FIELD_COUNT;i<64;i++)if(q->values[i])return 0;
 const uint32_t*arrays[]={q->palette,q->starPalette,q->glyphs,q->novaGlyphs};const int caps[]={32,32,32,16},keys[]={25,37,36,41};
 for(int a=0;a<4;a++)for(int i=0;i<caps[a];i++){uint32_t v=arrays[a][i];if(i>=q->values[keys[a]]){if(v)return 0;}else if(a<2?v>0xffffff:v>0x10ffff||(v>=0xd800&&v<=0xdfff))return 0;}
 for(uint32_t i=0;i<128;i++){const int32_t*e=q->events[i];if(i>=q->eventCount){for(int k=0;k<8;k++)if(e[k])return 0;continue;}if(e[0]<-1048576||e[0]>1048576||e[1]<-1048576||e[1]>1048576||e[2]<0||e[2]>1000||e[3]<0||e[3]>1||e[6]<0||e[7]||stTime(e+4)>9007199254740991ULL)return 0;}
 return 1;
}
static int fail(NrContext*c,const char*m){size_t n=strlen(m);if(n>=sizeof(c->error))n=sizeof(c->error)-1;memcpy(c->error,m,n);c->error[n]=0;return -1;}
static int scalar(const Json*j,int obj,const char*name,double lo,double hi,double*out,int integral){int at=nrField(j,obj,name);if(at<0)return 1;double n;if(!nrNumber(j,at,&n)||n<lo||n>hi||(integral&&n!=(int64_t)n))return 0;*out=n;return 1;}
int nrSourceStageSceneCommand(NrContext*c,State*s,const Json*j){
 if(s->schema<NR_STATE_SCHEMA_SOURCE_STAGE_SCENE||!nrAllowed(j,0,"op enabled config timeMs events"))return fail(c,"Unknown source stage scene field");
 int enabled=1,at=nrField(j,0,"enabled");if(at>=0&&!nrBoolean(j,at,&enabled))return fail(c,"Source stage enabled must be boolean");
 if(!enabled){if(nrField(j,0,"config")>=0||nrField(j,0,"timeMs")>=0||nrField(j,0,"events")>=0)return fail(c,"Disable source stage without patch");memset(&s->sourceStageScene,0,sizeof(s->sourceStageScene));return 0;}
 SourceStageScene q=s->sourceStageScene;if(!q.enabled)defaults(&q);double time=(double)q.timeMs;if(!scalar(j,0,"timeMs",0,9007199254740991.0,&time,1))return fail(c,"Invalid source stage time");q.timeMs=(uint64_t)time;
 int config=nrField(j,0,"config");if(config>=0){if(!nrAllowed(j,config,"values palette starPalette glyphs novaGlyphs"))return fail(c,"Unknown source stage config");
 int oldCounts[4]={q.values[25],q.values[37],q.values[36],q.values[41]};
 int values=nrField(j,config,"values");
 static const char*names[]={"width","height","pattern","focusMode","focusX","focusY","periodMs","saturation","brightness","speedFalloff","saturationFalloff","brightnessFalloff","cellAspect","scale","angle","pivotX","pivotY","rotationPeriodMs","rotationMode","swing","phase","pixelMode","seed","baseColor","inkColor","paletteCount","gradientWrap","interpolation","colorMode","hueOffset","stars","starDensity","starMinMs","starRangeMs","starDuty","starPeak","starGlyphCount","starColorCount","novaChance","novaCycleMs","novaDurationMs","novaGlyphCount","rippleSpeed","rippleWidth","rippleLifeMs","rippleOpacity","rippleRings","motion","quantize","originX","originY","waveAmplitude","starAttack","reverse"};
 if(values>=0){if(!nrAllowed(j,values,"width height pattern focusMode focusX focusY periodMs saturation brightness speedFalloff saturationFalloff brightnessFalloff cellAspect scale angle pivotX pivotY rotationPeriodMs rotationMode swing phase pixelMode seed baseColor inkColor paletteCount gradientWrap interpolation colorMode hueOffset stars starDensity starMinMs starRangeMs starDuty starPeak starGlyphCount starColorCount novaChance novaCycleMs novaDurationMs novaGlyphCount rippleSpeed rippleWidth rippleLifeMs rippleOpacity rippleRings motion quantize originX originY waveAmplitude starAttack reverse"))return fail(c,"Unknown source stage value");for(int i=0;i<54;i++){double n=q.values[i];if(!scalar(j,values,names[i],ST_MIN[i],i==0?NR_SOURCE_STAGE_MAX_WIDTH:i==1?NR_SOURCE_STAGE_MAX_HEIGHT:ST_MAX[i],&n,1))return fail(c,"Invalid source stage value");if(i<2){if(nrField(j,values,names[i])>=0&&n!=(i?s->height:s->width))return fail(c,"Source stage dimensions must match viewport");}else q.values[i]=(int32_t)n;}}

 const char*anames[]={"palette","starPalette","glyphs","novaGlyphs"};uint32_t*arrays[]={q.palette,q.starPalette,q.glyphs,q.novaGlyphs};const int caps[]={32,32,32,16},keys[]={25,37,36,41};
 for(int a=0;a<4;a++){int t=nrField(j,config,anames[a]);if(t<0){if(values>=0&&nrField(j,values,names[keys[a]])>=0&&q.values[keys[a]]!=oldCounts[a])return fail(c,"Palette count requires matching array");continue;}if(j->tokens[t].type!=J_ARRAY||j->tokens[t].count<1||j->tokens[t].count>caps[a])return fail(c,"Invalid source stage array");int count=j->tokens[t].count;if(values>=0&&nrField(j,values,names[keys[a]])>=0&&q.values[keys[a]]!=count)return fail(c,"Source stage count mismatch");memset(arrays[a],0,(size_t)caps[a]*4);int k=0;for(int v=t+1;v<j->tokens[t].next;v=j->tokens[v].next){double n;if(!nrNumber(j,v,&n)||n<0||n>(a<2?0xffffff:0x10ffff)||n!=(uint32_t)n||(a>=2&&n>=0xd800&&n<=0xdfff))return fail(c,"Invalid source stage array scalar");arrays[a][k++]=(uint32_t)n;}q.values[keys[a]]=count;}
 }
 at=nrField(j,0,"events");if(at>=0){if(j->tokens[at].type!=J_ARRAY||j->tokens[at].count>128)return fail(c,"Invalid source stage events");q.eventCount=0;memset(q.events,0,sizeof(q.events));for(int t=at+1;t<j->tokens[at].next;t=j->tokens[t].next){if(!nrAllowed(j,t,"x y atMs strength kind id")||nrField(j,t,"x")<0||nrField(j,t,"y")<0||nrField(j,t,"atMs")<0)return fail(c,"Invalid source stage event");double x=0,y=0,atMs=0,strength=1000,kind=0,id=0;if(!scalar(j,t,"x",-4097,4097,&x,0)||!scalar(j,t,"y",-4097,4097,&y,0)||!scalar(j,t,"atMs",0,9007199254740991.0,&atMs,1)||!scalar(j,t,"strength",0,1000,&strength,1)||!scalar(j,t,"kind",0,1,&kind,1)||!scalar(j,t,"id",0,INT32_MAX,&id,1))return fail(c,"Invalid source stage event scalar");int32_t*e=q.events[q.eventCount++];e[0]=(int32_t)nrFloor(x*256+.5);e[1]=(int32_t)nrFloor(y*256+.5);if(e[0]<-1048576||e[0]>1048576||e[1]<-1048576||e[1]>1048576)return fail(c,"Source stage event Q8 coordinate range");e[2]=(int32_t)strength;e[3]=(int32_t)kind;uint64_t stamp=(uint64_t)atMs;e[4]=(int32_t)(uint32_t)stamp;e[5]=(int32_t)(uint32_t)(stamp>>32);e[6]=(int32_t)id;}}
 s->sourceStageScene=q;if(!nrValidSourceStageScene(s))return fail(c,"Invalid source stage scene");return 0;
}
void nrSourceStageBackground(NrContext*c,const State*s){
 if(!s->sourceStageScene.enabled)return;SourceStageScene resolved=s->sourceStageScene;resolved.values[0]=s->width;resolved.values[1]=s->height;const SourceStageScene*config=&resolved;
 /* The archived 512-entry scratch holds every live impulse within its 512x256
  * extent: 128 events plus one nova per 32x16 world tile, at most 17x17 tiles.
  * A larger viewport keeps the list in the plot scratch of caller-owned render
  * memory, one impulse per viewport cell: beyond 512x256, 128 events plus
  * ((width-1)/32+2)*((height-1)/16+2) tiles never exceed width*height. Plot
  * scratch is write-before-read per widget; nothing else touches it in this pass. */
 NsImpulse archived[512];int archivedExtent=s->width<=(uint32_t)ST_MAX[NST_WIDTH]&&s->height<=(uint32_t)ST_MAX[NST_HEIGHT];
 NsImpulse*active=archivedExtent?archived:(NsImpulse*)c->plotColor;uint32_t capacity=archivedExtent?512u:s->width*s->height;
 uint64_t t=nrSourceStageTime(s);uint32_t n=stActive(config,t,(const NsImpulse*)config->events,config->eventCount,active,capacity);static const uint32_t bits[8]={1,8,2,16,4,32,64,128};
 for(int y=0;y<S(HEIGHT);y++)for(int x=0;x<S(WIDTH);x++){NsCell*cell=(NsCell*)&c->cells[(size_t)y*s->width+x];cell->flags=0;cell->glyph=32;cell->bg=stSample(config,t,x*256,y*256,active,n);cell->fg=(uint32_t)S(INK_COLOR);
 if(S(PIXEL_MODE)==1){cell->glyph=0x2580;cell->fg=stSample(config,t,x*256,y*256-64,active,n);cell->bg=stSample(config,t,x*256,y*256+64,active,n);}
 if(S(PIXEL_MODE)==2){cell->glyph=0x258c;cell->fg=stSample(config,t,x*256-64,y*256,active,n);cell->bg=stSample(config,t,x*256+64,y*256,active,n);}
 if(S(PIXEL_MODE)==3){uint32_t mask=0;for(int k=0;k<8;k++){uint32_t v=stSample(config,t,x*256+(k%2?64:-64),y*256+(k/2)*64-96,active,n);int l=(redI(v)+greenI(v)+blueI(v))/3;if(l>12+(int)(hashI((uint32_t)(x*8+k)^(uint32_t)y*307u)%105))mask|=bits[k];}cell->glyph=0x2800+mask;cell->fg=mixI(cell->bg,stPalette(config,(int64_t)x*1024/S(SCALE)*256),480);cell->bg=(uint32_t)S(BASE_COLOR);}
 stStar(config,t,x,y,cell,active,n);
 }
 memset(c->characterIndices,0xff,(size_t)s->width*s->height*4);memset(c->characterOwners,0,(size_t)s->width*s->height*4);
}
void nrSourceStageQuantize(NrContext*c,const State*s){int mode=s->sourceStageScene.enabled?s->sourceStageScene.values[48]:0;if(!mode)return;for(size_t i=0;i<(size_t)s->width*s->height;i++){c->cells[i].foreground=stQuantize(c->cells[i].foreground,mode);c->cells[i].background=stQuantize(c->cells[i].background,mode);}}
