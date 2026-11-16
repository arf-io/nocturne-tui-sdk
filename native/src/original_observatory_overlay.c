/* Exact original Observatory skyText and fixed orbital connector underlays. */
#include "internal.h"
#include "observatory_source_background.h"
static int bounded(double n,double lo,double hi){return n==n&&n>=lo&&n<=hi;}
static int fail(NrContext*c,const char*m){size_t n=strlen(m);if(n>=sizeof(c->error))n=sizeof(c->error)-1;memcpy(c->error,m,n);c->error[n]=0;return -1;}
int nrValidOriginalObservatoryOverlay(const State*s){
 const OriginalObservatoryOverlay*q=&s->observatoryOverlay;if(!q->enabled){OriginalObservatoryOverlay zero={0};return !memcmp(q,&zero,sizeof(zero));}
 if(s->schema<NR_STATE_SCHEMA_OBSERVATORY_OVERLAY||q->enabled!=1||q->kind<1||q->kind>4||q->flatNavigation>1||q->reserved||!bounded(q->fallMs,0,4000)||!bounded(q->hueStep,-90,90)||!bounded(q->textHueSpeed,-90,90))return 0;
 if(!s->windowApplication.enabled||s->windowApplication.scene!=3)return 0;int slot=nrFindWindow(s,s->windowApplication.paletteWindowId);return slot>=0&&s->windowContent[slot].enabled;
}
int nrOriginalObservatoryOverlayCommand(NrContext*c,State*s,const Json*j){
 if(s->schema<NR_STATE_SCHEMA_OBSERVATORY_OVERLAY||!nrAllowed(j,0,"op enabled kind fallMs hueStep textHueSpeed flatNavigation"))return fail(c,"Unknown Observatory overlay field");
 int on=1,t=nrField(j,0,"enabled");if(t>=0&&!nrBoolean(j,t,&on))return fail(c,"Overlay enabled must be boolean");
 if(!on){if(!nrAllowed(j,0,"op enabled"))return fail(c,"Disable overlay without patch");memset(&s->observatoryOverlay,0,sizeof(s->observatoryOverlay));return 0;}
 OriginalObservatoryOverlay q=s->observatoryOverlay;if(!q.enabled){memset(&q,0,sizeof(q));q.enabled=1;q.kind=1;q.fallMs=1100;q.hueStep=13;q.textHueSpeed=12;}
 t=nrField(j,0,"kind");if(t>=0){const char*names[]={"text","dag","spatial-menu","warp"};uint32_t k=0;for(;k<4;k++)if(nrEqual(j,t,names[k]))break;if(k==4)return fail(c,"Unknown Observatory overlay kind");q.kind=k+1;}
 t=nrField(j,0,"flatNavigation");if(t>=0){int v;if(!nrBoolean(j,t,&v))return fail(c,"Flat navigation must be boolean");q.flatNavigation=(uint32_t)v;}
 const char*names[]={"fallMs","hueStep","textHueSpeed"};double*values[]={&q.fallMs,&q.hueStep,&q.textHueSpeed};const double lo[]={0,-90,-90},hi[]={4000,90,90};
 for(int i=0;i<3;i++){t=nrField(j,0,names[i]);if(t>=0&&(!nrNumber(j,t,values[i])||!bounded(*values[i],lo[i],hi[i])))return fail(c,"Invalid Observatory overlay number");}
 s->observatoryOverlay=q;return nrValidOriginalObservatoryOverlay(s)?0:fail(c,"Overlay requires Observatory application");
}
void nrDrawOriginalObservatoryOverlay(NrContext*c,const WindowApplication*a,const NrWindowPaletteSourcePrepared*p,double ms){
 const State*s=nrView(c);const OriginalObservatoryOverlay*q=&s->observatoryOverlay;if(!q->enabled||q->kind==4)return;
 if(q->kind==1){
  static const char phrase[]="THE TERMINAL IS A PLACE, NOT A PRINT OUT";const int count=(int)sizeof(phrase)-1;double age=ms-nrFloor(ms/9000)*9000;int x0=(int)nrFloor(((double)s->width-count)/2);if(x0<2)x0=2;
  int slot=nrFindWindow(s,a->paletteWindowId);if(slot<0)return;double hue=s->windowContent[slot].palette.hueOffsetDegrees;
  for(int i=0;i<count;i++){double v=(age-i*35)/(q->fallMs>1?q->fallMs:1);if(v<0)v=0;if(v>1)v=1;double progress=v*v*(3-2*v),y=2+((double)s->height*.4-2)*progress,alpha=age<i*35?0:progress*1.8;if(alpha>1)alpha=1;uint32_t rgb;if(nrWindowPaletteSourceInk(p,hue+i*q->hueStep+ms*q->textHueSpeed/1000,&rgb))continue;nrSourcePaintCell(x0+i,y,(unsigned char)phrase[i],rgb,alpha,s->width,s->height,(uint32_t*)c->cells);}
  return;
 }
 const double coordinates[8][3]={{0,5,17},{-7,1.8,22},{7,1.8,22},{-11,-2,32},{0,-1,27},{11,-2,32},{0,-6,34},{0,-9,42}};
 const int parents[8][3]={{-1,-1,-1},{0,-1,-1},{0,-1,-1},{1,-1,-1},{1,2,-1},{2,-1,-1},{3,4,5},{6,3,-1}};
 const double flatX[]={.5,.25,.75,.13,.5,.87,.5,.5},flatY[]={1,6,6,12,12,12,18,22};
 double gw=(double)s->width-6,gh=(double)s->height-19,x[8],y[8],z[8];int visible[8];Camera camera=nrCameraAt(s);
 for(int i=0;i<8;i++){if(q->flatNavigation){x[i]=flatX[i]*gw;y[i]=flatY[i]/24*gh;z[i]=20;visible[i]=1;}else visible[i]=nrObservatorySourceProject(&camera,nrV(coordinates[i][0],coordinates[i][1],coordinates[i][2]),gw,gh,&x[i],&y[i],&z[i]);if(visible[i]){x[i]+=3;y[i]+=10;}}
 for(int i=0;i<8;i++){uint32_t rgb;if(nrWindowPaletteSourceInk(p,170+i*18,&rgb))continue;for(int k=0;k<3;k++){int parent=parents[i][k];if(parent<0)break;if(visible[i]&&visible[parent])nrSourceWeatherDrawSegment(x[parent],y[parent],x[i],y[i],rgb,.52,s->width,s->height,(uint32_t*)c->cells);}}
}
