#include "internal.h"
#include <limits.h>
#include "window_palette_source.h"
uint32_t nrSourceStageOklch(int32_t l,int32_t c,int32_t h){if(l<0||l>1000||c<0||c>4000)return 0xffffffffu;return nrWindowPaletteSourceFixedOklch(l,c,h);}
extern int32_t nrSourceStageSin1024(int32_t);
int32_t nrSourceStageTween(int32_t from,int32_t to,uint64_t elapsedMs,uint32_t durationMs,int32_t easing){
 if(!durationMs||elapsedMs>=durationMs)return to;
 int32_t p=(int32_t)(elapsedMs*1000/durationMs);
 if(easing==1)p=(int32_t)((int64_t)p*p*(3000-2*p)/1000000);
 else if(easing==2)p=(1000-nrSourceStageSin1024(256+p*512/1000))/2;
 else if(easing==3){int64_t q=1000-p;p=1000-(int32_t)(q*q*q/1000000);}
 return (int32_t)((int64_t)from+((int64_t)to-from)*p/1000);
}
int32_t nrSourceStageInkOpacity(uint32_t age,uint32_t fade,int32_t row,int32_t band,int32_t minimum){
 if(band<0||minimum<0||minimum>1000)return -1;
 int32_t arrival=nrSourceStageTween(0,1000,age,fade,1),horizon=1000;
 if(band>0&&row<band)horizon=nrSourceStageTween(minimum,1000,row>0?(uint32_t)row:0,(uint32_t)band,1);
 return arrival*horizon/1000;
}
static int32_t angle(int64_t x,int64_t y){
 if(!x&&!y)return 0;int64_t ax=x<0?-x:x,ay=y<0?-y:y;int lo=0,hi=256;
 while(lo<hi){int m=(lo+hi)/2;if((int64_t)nrSourceStageSin1024(m)*ax<(int64_t)nrSourceStageSin1024(m+256)*ay)lo=m+1;else hi=m;}
 return x>=0?(y>=0?lo:(1024-lo)%1024):(y>=0?512-lo:512+lo);
}
int32_t nrSourceStageHit(const NrContext*c,int32_t x,int32_t y,int32_t*out,uint32_t capacity){
 if(!c||c->state.magic!=NR_MAGIC||x< -4096||x>4096||y< -4096||y>4096||!out||capacity<2||(uintptr_t)out%4||!nrExternalOutput(c,out,8))return -1;
 const State*state=&c->state;const SourceStageState*s=&state->sourceStage;
 if(state->promptDocument.modal)return 0;int modal=nrModalPointerOwns(state,x,y);if(modal&&(!nrModalAssociationReady(state)||x<0||y<0||(uint32_t)x>=state->width||(uint32_t)y>=state->height))return 0;
 for(int i=(int)s->count-1;i>=0;i--){uint32_t id=s->components[i].id;if(modal?!nrModalActiveComponent(state,id):nrModalOwnsComponent(state,id))continue;const int32_t*n=s->components[i].node;int64_t w=n[4],h=n[5],xx=(int64_t)x-n[2],yy=(int64_t)y-n[3];if(!n[1]||xx<0||yy<0||xx>=w||yy>=h)continue;
  if(n[6]==3)return 0;int item=0,count=n[20],kind=n[0];const int32_t*data=s->data+n[19];
  if(kind==8||kind==9){int64_t total=0;for(int k=0;k<count;k++)if(data[k]>0)total+=data[k];if(!total)continue;
   int64_t dx=xx*2+1-w,dy=yy*4+2-h*2,r=(w<h*2?w:h*2)-1,rr=dx*dx+dy*dy,r2=r*r;
   if(r<1||rr>r2||(kind==9&&rr<r2/100*38+(r2%100)*38/100))continue;
   int a=(angle(dx,dy)+256)%1024;int64_t target=(int64_t)a*total,acc=0;for(item=0;item<count;item++){if(data[item]>0)acc+=(int64_t)data[item]*1024;if(target<acc)break;}if(item>=count)item=count-1;
  }else if(kind==7&&count){int64_t bw=w/count;if(bw<1)bw=1;item=(int)(xx/bw);if(item>=count)continue;
  }else if(kind==11&&count){item=(int)(xx*count/w);if(item>=count)item=count-1;
  }else if(kind==10&&count>=2){int64_t best=INT64_MAX;item=-1;for(int k=0;k+1<count;k+=2){int32_t a=data[k]<0?0:data[k]>1000?1000:data[k],b=data[k+1]<0?0:data[k+1]>1000?1000:data[k+1];int64_t px=(int64_t)a*(w*2-1)/1000,py=(int64_t)(1000-b)*(h*4-1)/1000,dx=xx*2+1-px,dy=yy*4+2-py,d=dx*dx+dy*dy;if(d<best){best=d;item=k/2;}}if(best>36)continue;}
  int32_t row[2]={n[1],item};memcpy(out,row,8);return 1;
 }return 0;
}
