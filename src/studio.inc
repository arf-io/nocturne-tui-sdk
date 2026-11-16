/* Nocturne Studio: additive, integer-only materials and event-driven wavefronts.
 * Included after the v1 renderer so pinned arithmetic is shared, not duplicated.
 * No heap allocation, clock reads, terminal I/O, or retained input pointers.
 */
#include "nocturne_studio.h"
#include "studio_defaults.inc"
#define S(k) (config->values[NST_##k])
#define N(k) (node->values[NTN_##k])
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
static int32_t stAngle(int32_t x,int32_t y){
 if(!x&&!y)return 0;
 int32_t ax=stAbs(x),ay=stAbs(y),lo=0,hi=256;
 while(lo<hi){int32_t m=(lo+hi)/2;if((int64_t)sinI(m)*ax<(int64_t)sinI(m+256)*ay)lo=m+1;else hi=m;}
 if(x>=0)return y>=0?lo:modI(1024-lo,1024);
 return y>=0?512-lo:512+lo;
}
uint32_t nsStageVersion(void){return NST_ABI_VERSION;}
uint32_t nsStageConfigSize(void){return sizeof(NsStageConfig);}
void nsStageDefaults(NsStageConfig *config){
 if(!config)return;
 for(int i=0;i<64;i++)config->values[i]=ST_DEFAULT[i];
 const uint32_t p[]={0x28304f,0x785c89,0x367876,0xae7357,0x504565};
 const uint32_t sp[]={0xb6a4c4,0x9fb9b0,0xc7bca7,0x9cacca,0xc6a0aa,0xadbdbb};
 const uint32_t g[]={'.',0xb7,0x2219,0x22c5,0x2801,0x2802,0x2804,0x2840,0x2808,0x2810,0x2820,0x2880};
 const uint32_t ng[]={0xb7,0x2219,'*',0x2726,0x2727};
 for(int i=0;i<32;i++){config->palette[i]=p[i%5];config->starPalette[i]=sp[i%6];config->glyphs[i]=g[i%12];}
 for(int i=0;i<16;i++)config->novaGlyphs[i]=ng[i%5];
}
int32_t nsStageValidate(const NsStageConfig *config){
 if(!config)return 1;
 for(int i=0;i<ST_FIELD_COUNT;i++)if(config->values[i]<ST_MIN[i]||config->values[i]>ST_MAX[i])return i+1;
 for(int i=0;i<S(PALETTE_COUNT);i++)if(config->palette[i]>0xffffff)return 65;
 for(int i=0;i<S(STAR_COLOR_COUNT);i++)if(config->starPalette[i]>0xffffff)return 66;
 for(int i=0;i<S(STAR_GLYPH_COUNT);i++)if(config->glyphs[i]>0x10ffff||(config->glyphs[i]>=0xd800&&config->glyphs[i]<=0xdfff))return 67;
 for(int i=0;i<S(NOVA_GLYPH_COUNT);i++)if(config->novaGlyphs[i]>0x10ffff||(config->novaGlyphs[i]>=0xd800&&config->novaGlyphs[i]<=0xdfff))return 68;
 return 0;
}
int32_t nsStageTween(int32_t from,int32_t to,uint64_t elapsedMs,uint32_t durationMs,int32_t easing){
 if(!durationMs||elapsedMs>=durationMs)return to;
 int32_t p=(int32_t)(elapsedMs*1000/durationMs);
 if(easing==1)p=smoothI(p);
 else if(easing==2)p=(1000-sinI(256+p*512/1000))/2;
 else if(easing==3){int64_t q=1000-p;p=1000-(int32_t)(q*q*q/1000000);}
 return (int32_t)((int64_t)from+((int64_t)to-from)*p/1000);
}
static uint32_t stPalette(const NsStageConfig *config,int64_t phase){
 int count=S(PALETTE_COUNT),i,p;
 if(S(COLOR_MODE)==1)return hsvI(phase*360/1024+S(HUE_OFFSET),1000,1000);
 if(S(COLOR_MODE)==2)return rgbI((sinI(phase)+1000)*255/2000,(sinI(phase+341)+1000)*255/2000,(sinI(phase+683)+1000)*255/2000);
 if(count==1)return config->palette[0];
 if(S(GRADIENT_WRAP)==1){p=modI(phase,2048);if(p>1024)p=2048-p;p*=count-1;i=p/1024;if(i>=count-1)return config->palette[count-1];}
 else {p=modI(phase,1024)*count;i=p/1024;}
 int f=(p%1024)*1000/1024;if(S(INTERPOLATION))f=smoothI(f);
 if(S(GRADIENT_WRAP)==2)f=0;
 return mixI(config->palette[i],config->palette[(i+1)%count],f);
}
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
static uint32_t stField(const NsStageConfig *config,uint64_t timeMs,int32_t x,int32_t y){
 int32_t fx=x-S(FOCUS_X),fy=y-S(FOCUS_Y),dist=0;
 if(S(FOCUS_MODE)==1)dist=stAbs(fy)/256;
 if(S(FOCUS_MODE)==2)dist=stAbs(fx)/256;
 if(S(FOCUS_MODE)==3)dist=(int32_t)stDistance(fx,(int32_t)((int64_t)fy*S(CELL_ASPECT)/1000))/256;
 if(S(FOCUS_MODE)==4)dist=stAbs(fx-fy)/362;
 uint64_t period=S(PERIOD_MS);
 for(int d=0;d<dist&&d<64;d++){period=period*1000/S(SPEED_FALLOFF);if(period>3600000000ULL){period=3600000000ULL;break;}}
 int32_t phase=(int32_t)((timeMs%period)*1024/period);if(S(REVERSE))phase=-phase;
 int32_t sat=decayI(S(SATURATION),S(SATURATION_FALLOFF),(uint32_t)dist);
 int32_t brightness=decayI(S(BRIGHTNESS),S(BRIGHTNESS_FALLOFF),(uint32_t)dist);
 int64_t dx=x-S(PIVOT_X),dy=(int64_t)(y-S(PIVOT_Y))*S(CELL_ASPECT)/1000;
 int32_t angle=S(ANGLE)*1024/360000;
 int32_t rot=(int32_t)((timeMs%(uint32_t)S(ROTATION_PERIOD_MS))*1024/S(ROTATION_PERIOD_MS));if(S(REVERSE))rot=-rot;
 if(S(ROTATION_MODE)==1)angle+=rot;
 if(S(ROTATION_MODE)==2)angle+=(int32_t)((int64_t)sinI(rot)*S(SWING)*1024/360000000);
 int64_t px=(int64_t)(x+S(ORIGIN_X)*256)*1024/S(SCALE),py=(int64_t)(y+S(ORIGIN_Y)*256)*S(CELL_ASPECT)*1024/(1000*S(SCALE));
 int64_t p=0;
 switch(S(PATTERN)){
  case 0:return (uint32_t)S(BASE_COLOR);
  case 1:p=px;break;
  case 2:p=(px+py)/2;break;
  case 3:p=px+(int64_t)sinI(py+phase)*S(WAVE_AMPLITUDE)/1000;break;
  case 4:p=(dx*sinI(angle+256)+dy*sinI(angle))*1024/(1000*S(SCALE));break;
  case 5:p=(sinI(px+phase)+sinI(py-phase)+sinI((px+py)/2+phase)+sinI((int64_t)stDistance((int32_t)dx,(int32_t)dy)*1024/S(SCALE)-phase))/4;break;
  case 6:p=(int64_t)stDistance(fx,(int32_t)((int64_t)fy*S(CELL_ASPECT)/1000))*1024/S(SCALE);break;
  case 7:p=sinI(px+phase)+sinI(px*103/100+py/2-phase);break;
  case 8:p=py/2+(int64_t)sinI(px/2+phase)*S(WAVE_AMPLITUDE)/1000+sinI(px*3-phase)/5;break;
  case 9:p=(sinI(px+phase)+sinI(py-phase)+sinI(px-py+phase))/3;break;
  case 10:p=stAbs(modI(px,2048)-1024)+py;break;
  case 11:p=((int64_t)stAbs(fx)+stAbs((int32_t)((int64_t)fy*S(CELL_ASPECT)/1000)))*1024/S(SCALE);break;
 }
 p+=phase+S(PHASE);
 return mixI((uint32_t)S(BASE_COLOR),saturateI(stPalette(config,p),sat),brightness);
}
/* Active wavefronts are prepared once per render. Rare auto-novae are anchored
 * to 32x16 world tiles. The chosen star never moves or changes its quiet glyph. */
static uint32_t stActive(const NsStageConfig *config,uint64_t timeMs,const NsImpulse *events,uint32_t n,NsImpulse *out){
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
   if(count>=512)return count;
   NsImpulse e={{(wx-S(ORIGIN_X))*256,(wy-S(ORIGIN_Y))*256,850,1,0,0,(int32_t)h,0}};
   uint64_t at=timeMs-age;e.values[4]=(int32_t)(uint32_t)at;e.values[5]=(int32_t)(uint32_t)(at>>32);out[count++]=e;break; /* latest eligible burst per tile */
  }
 }
 return count;
}
static uint32_t stSample(const NsStageConfig *config,uint64_t t,int x,int y,const NsImpulse *ev,uint32_t count){
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
static void stStar(const NsStageConfig *config,uint64_t t,int x,int y,NsCell *cell,const NsImpulse *events,uint32_t count){
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
static int stValidateNodes(const NsNode *nodes,uint32_t n,const uint32_t *text,uint32_t nt,const int32_t *data,uint32_t nd){
 if(n>NST_MAX_NODES||nt>NST_MAX_TEXT||nd>NST_MAX_DATA||(n&&!nodes)||(nt&&!text)||(nd&&!data))return 0;
 for(uint32_t i=0;i<nd;i++)if(data[i]<-1000000||data[i]>1000000)return 0;
 for(uint32_t i=0;i<n;i++){
  const NsNode *node=&nodes[i];
  if(N(KIND)<0||N(KIND)>13||N(ID)<0||N(X)<-4096||N(X)>4096||N(Y)<-4096||N(Y)>4096||N(WIDTH)<0||N(WIDTH)>512||N(HEIGHT)<0||N(HEIGHT)>256)return 0;
  if(N(STATE)<0||N(STATE)>3||N(FG_OPACITY)<0||N(FG_OPACITY)>1000||N(BG_OPACITY)<0||N(BG_OPACITY)>1000||N(FG)<0||N(FG)>0xffffff||N(BG)<0||N(BG)>0xffffff)return 0;
  if(N(TEXT_OFFSET)<0||N(TEXT_LENGTH)<0||(uint64_t)(uint32_t)N(TEXT_OFFSET)+(uint32_t)N(TEXT_LENGTH)>nt)return 0;
  if(N(DATA_OFFSET)<0||N(DATA_LENGTH)<0||(uint64_t)(uint32_t)N(DATA_OFFSET)+(uint32_t)N(DATA_LENGTH)>nd)return 0;
  if(N(DURATION_MS)<0||N(DURATION_MS)>3600000||N(REVEAL_MS)<0||N(REVEAL_MS)>3600000||N(STYLE)<0||N(STYLE)>15||N(COLOR_ANIMATION)<0||N(COLOR_ANIMATION)>3)return 0;
  if(N(HUE_STEP)<-3600||N(HUE_STEP)>3600||N(HUE_SPEED)<-3600||N(HUE_SPEED)>3600||N(HUE_BASE)<-360000||N(HUE_BASE)>360000||N(HUE_SATURATION)<0||N(HUE_SATURATION)>1000||N(HUE_BRIGHTNESS)<0||N(HUE_BRIGHTNESS)>1000||N(ZOOM)<1||N(ZOOM)>4)return 0;
 }
 return 1;
}
#include "studio_widgets.inc"
int32_t nsStageRender(const NsStageConfig *config,uint64_t timeMs,const NsImpulse *events,uint32_t eventCount,const NsNode *nodes,uint32_t nodeCount,const uint32_t *text,uint32_t textCount,const int32_t *data,uint32_t dataCount,NsCell *cells,uint32_t capacity){
 if(nsStageValidate(config))return -1;
 uint32_t size=(uint32_t)S(WIDTH)*(uint32_t)S(HEIGHT);if(capacity<size||(size&&!cells))return -2;
 if(eventCount>NST_MAX_EVENTS||(eventCount&&!events))return -3;
 for(uint32_t i=0;i<eventCount;i++){const int32_t *e=events[i].values;if(e[0]<-1048576||e[0]>1048576||e[1]<-1048576||e[1]>1048576||e[2]<0||e[2]>1000||e[3]<0||e[3]>1)return -3;}
 if(!stValidateNodes(nodes,nodeCount,text,textCount,data,dataCount))return -4;
 if(!size)return 0;
 uint64_t t=S(MOTION)?timeMs:0;NsImpulse active[512];uint32_t n=stActive(config,t,events,eventCount,active);
 static const uint32_t bits[8]={1,8,2,16,4,32,64,128};
 for(int y=0;y<S(HEIGHT);y++)for(int x=0;x<S(WIDTH);x++){
  NsCell *c=&cells[y*S(WIDTH)+x];c->flags=0;c->glyph=32;c->bg=stSample(config,t,x*256,y*256,active,n);c->fg=(uint32_t)S(INK_COLOR);
  if(S(PIXEL_MODE)==1){c->glyph=0x2580;c->fg=stSample(config,t,x*256,y*256-64,active,n);c->bg=stSample(config,t,x*256,y*256+64,active,n);}
  if(S(PIXEL_MODE)==2){c->glyph=0x258c;c->fg=stSample(config,t,x*256-64,y*256,active,n);c->bg=stSample(config,t,x*256+64,y*256,active,n);}
  if(S(PIXEL_MODE)==3){uint32_t mask=0;for(int k=0;k<8;k++){uint32_t v=stSample(config,t,x*256+(k%2?64:-64),y*256+(k/2)*64-96,active,n);int l=(redI(v)+greenI(v)+blueI(v))/3;if(l>12+(int)(hashI((uint32_t)(x*8+k)^(uint32_t)y*307u)%105))mask|=bits[k];}c->glyph=0x2800+mask;c->fg=mixI(c->bg,stPalette(config,(int64_t)x*1024/S(SCALE)*256),480);c->bg=(uint32_t)S(BASE_COLOR);}
  stStar(config,t,x,y,c,active,n);
 }
 for(uint32_t i=0;i<nodeCount;i++)stWidget(config,cells,t,&nodes[i],text,data);
 if(S(QUANTIZE))for(uint32_t i=0;i<size;i++){cells[i].fg=stQuantize(cells[i].fg,S(QUANTIZE));cells[i].bg=stQuantize(cells[i].bg,S(QUANTIZE));}
 return (int32_t)size;
}
int32_t nsStageComposite(NsCell *dest,int32_t dw,int32_t dh,const NsCell *src,int32_t sw,int32_t sh,int32_t x,int32_t y,int32_t fa,int32_t ba){
 if(dw<0||dw>512||dh<0||dh>256||sw<0||sw>512||sh<0||sh>256||fa<0||fa>1000||ba<0||ba>1000||x< -4096||x>4096||y< -4096||y>4096||(dw&&dh&&!dest)||(sw&&sh&&!src))return -1;
 if(!fa&&!ba)return 0;
 for(int j=0;j<sh;j++)for(int i=0;i<sw;i++){int dx=x+i,dy=y+j;if(dx<0||dy<0||dx>=dw||dy>=dh)continue;const NsCell *s=&src[j*sw+i];NsCell *d=&dest[dy*dw+dx];
  uint32_t old=flattenedBg(d),bg=mixI(old,s->bg,ba);
  if(ba){d->bg=bg;d->fg=mixI(d->fg,bg,ba);if(ba==1000)d->glyph=32;}
  if(s->glyph&&s->glyph!=32&&fa){d->glyph=stGlyph(s->glyph);d->bg=bg;d->fg=mixI(bg,s->fg,fa);d->flags=s->flags;}
 }
 return 0;
}
int32_t nsStagePaint(const NsStageConfig *config,uint64_t timeMs,const NsNode *nodes,uint32_t nodeCount,const uint32_t *text,uint32_t textCount,const int32_t *data,uint32_t dataCount,NsCell *cells,uint32_t capacity){
 if(nsStageValidate(config))return -1;
 uint32_t size=(uint32_t)S(WIDTH)*(uint32_t)S(HEIGHT);
 if(capacity<size||(size&&!cells))return -2;
 if(!stValidateNodes(nodes,nodeCount,text,textCount,data,dataCount))return -4;
 uint64_t t=S(MOTION)?timeMs:0;
 for(uint32_t i=0;i<nodeCount;i++)stWidget(config,cells,t,&nodes[i],text,data);
 return (int32_t)size;
}
#undef S
#undef N
