#include "source_stage_components.h"

#include <limits.h>
#include <stddef.h>
#include <string.h>
#include "tables.inc"
#include "source_ok_color_tables.inc"

enum { K=0, ID=1, X=2, Y=3, W=4, H=5, STATE=6, VALUE=7, FROM=8,
       CHANGED_LO=9, CHANGED_HI=10, DURATION=11, FG=12, BG=13, FGA=14,
       BGA=15, STYLE=16, TOFF=17, TLEN=18, DOFF=19, DLEN=20,
       HSTEP=21, HSPEED=22, HBASE=23, REVEAL=24, SAT=26, BRIGHT=27,
       ANIM=28, ZOOM=30 };

static int32_t clampi(int32_t n,int32_t lo,int32_t hi){return n<lo?lo:n>hi?hi:n;}
static int32_t modp(int64_t n,int32_t d){int64_t r=n%d;return (int32_t)(r<0?r+d:r);}
int32_t nrSourceStageSin1024(int32_t phase){
    int32_t index=modp(phase,1024)*4;int64_t v=(int64_t)SIN_Q30[index]*1000;
    return (int32_t)(v>=0?(v+(1LL<<29))/(1LL<<30):(v-(1LL<<29))/(1LL<<30));
}
static uint32_t mixRgb(uint32_t a,uint32_t b,int32_t p){
    p=clampi(p,0,1000);
    uint32_t r=(uint32_t)((int32_t)(a>>16&255)+((int32_t)(b>>16&255)-(int32_t)(a>>16&255))*p/1000);
    uint32_t g=(uint32_t)((int32_t)(a>>8&255)+((int32_t)(b>>8&255)-(int32_t)(a>>8&255))*p/1000);
    uint32_t bl=(uint32_t)((int32_t)(a&255)+((int32_t)(b&255)-(int32_t)(a&255))*p/1000);
    return (r<<16)|(g<<8)|bl;
}
static uint32_t hsvI(int64_t hue,int32_t saturation,int32_t value){
    int32_t h=modp(hue,360),c=value*saturation/1000,within=h%120;
    int32_t x=c*(60-(within>60?within-60:60-within))/60,m=value-c;
    int32_t r=0,g=0,b=0;
    switch(h/60){case 0:r=c;g=x;break;case 1:r=x;g=c;break;case 2:g=c;b=x;break;
      case 3:g=x;b=c;break;case 4:r=x;b=c;break;default:r=c;b=x;break;}
    return (uint32_t)((r+m)*255/1000)<<16|(uint32_t)((g+m)*255/1000)<<8|(uint32_t)((b+m)*255/1000);
}
static int64_t okCube(int64_t x){return (x*x/1048576LL)*x/1048576LL;}
static void okLinear(int32_t l,int32_t c,int32_t h,int64_t out[3]){
    int64_t L=(int64_t)l*1048576/1000,C=(int64_t)c*1048576/10000;
    int32_t phase=(int32_t)((int64_t)modp(h,360000)*1024/360000);
    int64_t a=C*nrSourceStageSin1024(phase+256)/1000,b=C*nrSourceStageSin1024(phase)/1000;
    int64_t ll=okCube(L+(396338*a+215804*b)/1000000),m=okCube(L-(105561*a+63854*b)/1000000),s=okCube(L-(89484*a+1291486*b)/1000000);
    out[0]=(4076742*ll-3307712*m+230970*s)/1000000;
    out[1]=(-1268438*ll+2609757*m-341319*s)/1000000;
    out[2]=(-4196*ll-703419*m+1707615*s)/1000000;
}
static int okGamut(const int64_t rgb[3]){return rgb[0]>=0&&rgb[0]<=1048576&&rgb[1]>=0&&rgb[1]<=1048576&&rgb[2]>=0&&rgb[2]<=1048576;}
static uint32_t okColor(int32_t l,int32_t c,int32_t h){
    if(!l)return 0;if(l==1000)return 0xffffff;
    int64_t rgb[3];okLinear(l,c,h,rgb);
    if(!okGamut(rgb)){int lo=0,hi=c;for(int i=0;i<14&&lo<hi;i++){int mid=(lo+hi+1)/2;okLinear(l,mid,h,rgb);if(okGamut(rgb))lo=mid;else hi=mid-1;}okLinear(l,lo,h,rgb);}
    uint32_t channels[3];for(int k=0;k<3;k++){int lo=0,hi=255;while(lo<hi){int mid=(lo+hi)/2;if(rgb[k]>OK_BOUNDARY[mid])lo=mid+1;else hi=mid;}channels[k]=(uint32_t)lo;}
    return channels[0]<<16|channels[1]<<8|channels[2];
}
static uint32_t nodeColor(const NrSourceStageComponent *c,int64_t index){
    const int32_t *n=c->node; int64_t t=(int64_t)(c->timeMs%360000);
    uint32_t color=(uint32_t)n[FG];
    if(n[ANIM]==1) color=hsvI((int64_t)n[HBASE]+(int64_t)index*n[HSTEP]+t*n[HSPEED]/1000,n[SAT],n[BRIGHT]);
    else if(n[ANIM]==2 && c->material){
        uint32_t out=color;
        if(nrSourceMaterialPaletteColor(c->material,(int64_t)index*37+t*n[HSPEED]/350,&out)==0)color=out;
    }
    else if(n[ANIM]==3)color=okColor(n[BRIGHT],n[SAT]*4,modp((int64_t)n[HBASE]*1000+(int64_t)index*n[HSTEP]*1000+t*n[HSPEED],360000));
    if(n[STATE]==3)color=mixRgb(c->baseColor,color,330);
    return color;
}
static int valid(const NrSourceStageComponent *c,const NrSourceStageComponentSink *s){
    if(!c||!s||!s->cell||!s->subcell||!s->readCell||s->frameWidth<0||s->frameHeight<0)return 0;
    const int32_t *n=c->node;
    /* Width and height are source-authored component geometry, not the old
       Stage viewport dimensions. Bound only where source 2x/4x fixed-point
       subcell extents remain representable in signed 32-bit coordinates. */
    if(n[K]<0||n[K]>13||n[ID]<0||n[X]<-4096||n[X]>4096||n[Y]<-4096||n[Y]>4096||n[W]<1||n[W]>INT32_MAX/2||n[H]<1||n[H]>INT32_MAX/4||
       n[STATE]<0||n[STATE]>3||n[FGA]<0||n[FGA]>1000||n[BGA]<0||n[BGA]>1000||n[FG]<0||n[FG]>0xffffff||n[BG]<0||n[BG]>0xffffff||
       c->textCount>32768||c->dataCount>16384||n[TOFF]<0||n[TLEN]<0||(uint64_t)(uint32_t)n[TOFF]+(uint32_t)n[TLEN]>c->textCount||
       n[DOFF]<0||n[DLEN]<0||(uint64_t)(uint32_t)n[DOFF]+(uint32_t)n[DLEN]>c->dataCount||
       n[DURATION]<0||n[DURATION]>3600000||n[REVEAL]<0||n[REVEAL]>3600000||n[STYLE]<0||n[STYLE]>15||n[ANIM]<0||n[ANIM]>3||
       n[HSTEP]<-3600||n[HSTEP]>3600||n[HSPEED]<-3600||n[HSPEED]>3600||n[HBASE]<-360000||n[HBASE]>360000||n[SAT]<0||n[SAT]>1000||
       n[BRIGHT]<0||n[BRIGHT]>1000||n[ZOOM]<1||n[ZOOM]>4||(c->textCount&&!c->text)||(c->dataCount&&!c->data)||c->baseColor>0xffffff)return 0;
    for(uint32_t i=0;i<c->dataCount;i++)if(c->data[i]<-1000000||c->data[i]>1000000)return 0;
    if((n[ANIM]==2||n[K]==NR_SOURCE_STAGE_PIE||n[K]==NR_SOURCE_STAGE_DONUT)&&
       (!c->material||!nrSourceMaterialSamplerValidate(c->material)))return 0;
    return 1;
}
static int validateRead(void*context,int32_t x,int32_t y,NrSourceStageCell*out){(void)context;(void)x;(void)y;memset(out,0,sizeof(*out));return 0;}
static void validateCell(void*context,int32_t x,int32_t y,uint32_t operation,uint32_t glyph,uint32_t fg,uint32_t fga,uint32_t bg,uint32_t bga,uint32_t explicitBg,uint32_t flags,uint32_t owner){(void)context;(void)x;(void)y;(void)operation;(void)glyph;(void)fg;(void)fga;(void)bg;(void)bga;(void)explicitBg;(void)flags;(void)owner;}
static void validateSubcell(void*context,int32_t x,int32_t y,uint32_t sx,uint32_t sy,uint32_t rgb,uint32_t opacity,uint32_t coverage,uint32_t flags,uint32_t owner){(void)context;(void)x;(void)y;(void)sx;(void)sy;(void)rgb;(void)opacity;(void)coverage;(void)flags;(void)owner;}
int nrSourceStageComponentValid(const NrSourceStageComponent*c,int32_t width,int32_t height){
    NrSourceStageComponentSink sink={0};sink.frameWidth=width;sink.frameHeight=height;
    sink.readCell=validateRead;sink.cell=validateCell;sink.subcell=validateSubcell;
    return valid(c,&sink);
}
static int inBounds(const NrSourceStageComponentSink *s,int64_t x,int64_t y){return x>=0&&y>=0&&x<s->frameWidth&&y<s->frameHeight;}
static void visibleRange(int64_t origin,int64_t extent,int32_t frameSize,int scale,int64_t*lo,int64_t*hi){
    int64_t a=0,b=extent*scale,view=(int64_t)frameSize*scale,start=origin*scale;
    if(-start>a)a=-start;if(view-start<b)b=view-start;if(a<0)a=0;if(b>extent*scale)b=extent*scale;if(b<a)b=a;*lo=a;*hi=b;
}
static void put(const NrSourceStageComponent *c,const NrSourceStageComponentSink *s,int64_t x,int64_t y,uint32_t glyph,uint32_t color,int index){
    const int32_t *n=c->node;
    if(!inBounds(s,x,y)||x<n[X]||y<n[Y]||x>=(int64_t)n[X]+n[W]||y>=(int64_t)n[Y]+n[H]||!n[FGA])return;
    int permitted=(glyph>=0x2190&&glyph<=0x22ff)||(glyph>=0x2500&&glyph<=0x25ff)||
        glyph==0x2726||glyph==0x2727||glyph==0x203a||glyph==0x2039||glyph==0xd7||glyph==0xb0||
        (glyph>=32&&glyph<=126)||(glyph>=0x2800&&glyph<=0x28ff)||glyph==0xb7||glyph==0x2022||
        glyph==0x2219||glyph==0x22c5||glyph==0x22c6||glyph==0x207a||glyph==0x2217;
    if(!permitted)glyph='?';
    s->cell(s->context,(int32_t)x,(int32_t)y,NR_SOURCE_CELL_GLYPH,glyph,color,(uint32_t)n[FGA],0,0,0,(uint32_t)n[ID],c->semanticOwner);
    (void)index;
}
static void dot(const NrSourceStageComponent *c,const NrSourceStageComponentSink *s,int64_t px,int64_t py,uint32_t color){
    const int32_t *n=c->node;
    if(!n[FGA]||px<0||py<0||px>=(int64_t)n[W]*2||py>=(int64_t)n[H]*4)return;
    int64_t x=(int64_t)n[X]+px/2,y=(int64_t)n[Y]+py/4;
    if(!inBounds(s,x,y))return;
    NrSourceStageCell old={0}; if(s->readCell(s->context,(int32_t)x,(int32_t)y,&old)!=0)return;
    if(old.glyph<0x2800||old.glyph>0x28ff){
        uint32_t flat=(old.glyph==0x2580||old.glyph==0x258c)?mixRgb(old.backgroundRgb,old.foregroundRgb,500):old.backgroundRgb;
        s->cell(s->context,(int32_t)x,(int32_t)y,NR_SOURCE_CELL_FLATTEN,0x2800,old.foregroundRgb,0,flat,1000,1,(uint32_t)n[ID],c->semanticOwner);
    }
    s->subcell(s->context,(int32_t)x,(int32_t)y,(uint32_t)(px%2),(uint32_t)(py%4),color,(uint32_t)n[FGA],1,(uint32_t)n[ID],c->semanticOwner);
}
static uint64_t changed(const int32_t *n){return ((uint64_t)(uint32_t)n[CHANGED_HI]<<32)|(uint32_t)n[CHANGED_LO];}
static int32_t tween(int32_t from,int32_t to,uint64_t age,uint32_t duration){
    if(!duration||age>=duration)return to;
    int32_t p=(int32_t)(age*1000/duration);p=(int32_t)((int64_t)p*p*(3000-2*p)/1000000);
    return (int32_t)((int64_t)from+((int64_t)to-from)*p/1000);
}
static void drawText(const NrSourceStageComponent *c,const NrSourceStageComponentSink *s,int64_t startX,int64_t startY){
    const int32_t *n=c->node;int64_t x=startX,y=startY;uint64_t ch=changed(n),age=c->timeMs>=ch?c->timeMs-ch:0;
    uint32_t count=(uint32_t)n[TLEN];if(n[REVEAL]>0&&age/(uint32_t)n[REVEAL]<count)count=(uint32_t)(age/(uint32_t)n[REVEAL]);
    for(uint32_t k=0;k<count;k++){uint32_t glyph=c->text[(uint32_t)n[TOFF]+k];if(glyph=='\n'){x=startX;y++;continue;}if(x>=(int64_t)n[X]+n[W]){x=startX;y++;}if(y>=(int64_t)n[Y]+n[H])break;put(c,s,x++,y,glyph,nodeColor(c,(int)k),(int)k);}
}
static void drawBox(const NrSourceStageComponent *c,const NrSourceStageComponentSink *s){
    static const uint32_t styles[4][6]={{0x256d,0x256e,0x2570,0x256f,0x2500,0x2502},{0x250c,0x2510,0x2514,0x2518,0x2500,0x2502},{0x2554,0x2557,0x255a,0x255d,0x2550,0x2551},{0x250f,0x2513,0x2517,0x251b,0x2501,0x2503}};
    const int32_t *n=c->node;int x=n[X],y=n[Y],w=n[W],h=n[H];if(w<2||h<2)return;
    const uint32_t *g=styles[n[STYLE]%4];
    int64_t x0,x1,y0,y1;visibleRange(x,w,s->frameWidth,1,&x0,&x1);visibleRange(y,h,s->frameHeight,1,&y0,&y1);
    int64_t hx0=x0<1?1:x0,hx1=x1>w-1?w-1:x1,vy0=y0<1?1:y0,vy1=y1>h-1?h-1:y1;
    for(int64_t i=hx0;i<hx1;i++){put(c,s,(int64_t)x+i,y,g[4],nodeColor(c,i),0);put(c,s,(int64_t)x+i,(int64_t)y+h-1,g[4],nodeColor(c,(int64_t)w+h+i),0);}
    for(int64_t j=vy0;j<vy1;j++){put(c,s,x,(int64_t)y+j,g[5],nodeColor(c,j),0);put(c,s,(int64_t)x+w-1,(int64_t)y+j,g[5],nodeColor(c,(int64_t)w+j),0);}
    put(c,s,x,y,g[0],nodeColor(c,0),0);put(c,s,(int64_t)x+w-1,y,g[1],nodeColor(c,w),w);
    put(c,s,x,(int64_t)y+h-1,g[2],nodeColor(c,h),h);put(c,s,(int64_t)x+w-1,(int64_t)y+h-1,g[3],nodeColor(c,w+h),w+h);
}
static void drawDotSegment(const NrSourceStageComponent *c,const NrSourceStageComponentSink *s,int x0,int y0,int x1,int y1,uint32_t color){
    const int32_t*n=c->node;int64_t xlo,xhi,ylo,yhi;
    visibleRange(n[X],n[W],s->frameWidth,2,&xlo,&xhi);visibleRange(n[Y],n[H],s->frameHeight,4,&ylo,&yhi);
    int64_t xmax=xhi-1,ymax=yhi-1;if(xmax<xlo||ymax<ylo)return;
    for(int pass=0;pass<8;pass++){
        int a=(x0<xlo?1:x0>xmax?2:0)|(y0<ylo?4:y0>ymax?8:0);
        int b=(x1<xlo?1:x1>xmax?2:0)|(y1<ylo?4:y1>ymax?8:0);
        if(!(a|b))break;if(a&b)return;
        int out=a?a:b;int64_t nx,ny;
        if(out&8){ny=ymax;nx=x0+((int64_t)x1-x0)*(ymax-y0)/((int64_t)y1-y0);}
        else if(out&4){ny=ylo;nx=x0+((int64_t)x1-x0)*(ylo-y0)/((int64_t)y1-y0);}
        else if(out&2){nx=xmax;ny=y0+((int64_t)y1-y0)*(xmax-x0)/((int64_t)x1-x0);}
        else {nx=xlo;ny=y0+((int64_t)y1-y0)*(xlo-x0)/((int64_t)x1-x0);}
        if(out==a){x0=(int)nx;y0=(int)ny;}else{x1=(int)nx;y1=(int)ny;}
    }
    int64_t dx=x1>x0?(int64_t)x1-x0:(int64_t)x0-x1,sx=x0<x1?1:-1;
    int64_t dy=-(y1>y0?(int64_t)y1-y0:(int64_t)y0-y1),sy=y0<y1?1:-1,err=dx+dy;
    for(;;){dot(c,s,x0,y0,color);if(x0==x1&&y0==y1)break;int64_t e=err*2;if(e>=dy){err+=dy;x0+=(int)sx;}if(e<=dx){err+=dx;y0+=(int)sy;}}
}

int nrSourceStageComponentApply(const NrSourceStageComponent *c,const NrSourceStageComponentSink *s){
    if(!c||!s)return -1;
    int kind=c->node[K];
    if(!valid(c,s))return -1;
    if(kind!=0&&kind!=1&&kind!=3&&kind!=4&&kind!=5&&kind!=7&&kind!=10&&kind!=11&&kind!=13&&
       kind!=NR_SOURCE_STAGE_RULE&&kind!=NR_SOURCE_STAGE_PROGRESS&&kind!=NR_SOURCE_STAGE_PIE&&kind!=NR_SOURCE_STAGE_DONUT&&kind!=NR_SOURCE_STAGE_DIGITS)return 1;
    const int32_t *n=c->node;int32_t x=n[X],y=n[Y],w=n[W],h=n[H];
    uint64_t age=c->timeMs>=changed(n)?c->timeMs-changed(n):0;
    int value=clampi(tween(n[FROM],n[VALUE],age,(uint32_t)n[DURATION]),0,1000);
    if(!w||!h)return 0;
    int64_t bgX0,bgX1,bgY0,bgY1;visibleRange(x,w,s->frameWidth,1,&bgX0,&bgX1);visibleRange(y,h,s->frameHeight,1,&bgY0,&bgY1);
    if(n[BGA])for(int64_t dy=bgY0;dy<bgY1;dy++)for(int64_t dx=bgX0;dx<bgX1;dx++){
        int64_t yy=(int64_t)y+dy,xx=(int64_t)x+dx;
        NrSourceStageCell old={0};if(s->readCell(s->context,(int32_t)xx,(int32_t)yy,&old))return -1;
        uint32_t flat=(old.glyph==0x2580||old.glyph==0x258c)?mixRgb(old.backgroundRgb,old.foregroundRgb,500):old.backgroundRgb;
        s->cell(s->context,(int32_t)xx,(int32_t)yy,NR_SOURCE_CELL_FILL,n[BGA]==1000?32:old.glyph,old.foregroundRgb,(uint32_t)n[BGA],(uint32_t)n[BG],(uint32_t)n[BGA],1,0,old.semanticOwner);
        (void)flat;
    }
    if(kind==0){drawText(c,s,x,y);return 0;}
    if(kind==1||kind==3){
        drawBox(c,s);
        if(kind==3){int64_t tx=(int64_t)x+2,ty=(int64_t)y+h/2;if(n[TLEN]<w-2)tx=(int64_t)x+(w-n[TLEN])/2;drawText(c,s,tx,ty);}
        else drawText(c,s,(int64_t)x+2,y);
        return 0;
    }
    if(kind==4){
        uint32_t glyph=n[STATE]==2?0x25b6:n[STATE]==3?0xd7:n[STATE]==1?0x203a:0x25cb;
        put(c,s,x,y,glyph,nodeColor(c,0),0);drawText(c,s,(int64_t)x+2,y);return 0;
    }
    if(kind==5){
        uint32_t color=nodeColor(c,0);int pulse=(nrSourceStageSin1024((int64_t)(c->timeMs%1600)*1024/1600)+1000)/2;
        uint32_t glyph=n[29]?(uint32_t)n[29]:n[STYLE]%5==0?0x2588:n[STYLE]%5==1?0x2581:n[STYLE]%5==2?0x258f:n[STYLE]%5==3?0x25b8:0x2800+(1u<<(c->timeMs/120%8));
        if(n[STYLE]%5==0&&inBounds(s,x,y)){
            NrSourceStageCell old={0};if(s->readCell(s->context,x,y,&old))return -1;
            if(old.glyph!=32&&old.glyph!=0x2580&&old.glyph!=0x258c){
                uint32_t flat=(old.glyph==0x2580||old.glyph==0x258c)?mixRgb(old.backgroundRgb,old.foregroundRgb,500):old.backgroundRgb;
                uint32_t tint=mixRgb(flat,color,400+pulse/3);
                s->cell(s->context,x,y,NR_SOURCE_CELL_BACKGROUND_TINT,old.glyph,old.foregroundRgb,0,tint,1000,1,0,old.semanticOwner);
                return 0;
            }
        }
        put(c,s,x,y,glyph,mixRgb(c->baseColor,color,400+pulse*600/1000),0);return 0;
    }
    if(kind==NR_SOURCE_STAGE_RULE){
        static const uint32_t sets[12][4]={{0x2500,0x2500,0x2500,0x2500},{0x2501,0x2501,0x2501,0x2501},{0x2550,0x2550,0x2550,0x2550},{0xb7,0x22c5,0x2219,0xb7},{0x2801,0x2808,0x2810,0x2802},{0x2581,0x2582,0x2583,0x2582},{0x203a,0x203a,0x203a,32},{0x2580,0x2584,0x2580,0x2584},{0x2574,32,0x2576,32},{0x2571,0x2572,0x2571,0x2572},{32,0x2219,0x2022,0x2219},{0x25cb,0xb7,0x25cb,0xb7}};
        int vertical=h>w,style=n[STYLE]%12;int64_t lo,hi;visibleRange(vertical?y:x,vertical?h:w,vertical?s->frameHeight:s->frameWidth,1,&lo,&hi);
        for(int64_t i=lo;i<hi;i++){uint32_t g=sets[style][modp(i-(int64_t)(c->timeMs/150),4)];if(vertical&&style<3)g=style==0?0x2502:style==1?0x2503:0x2551;put(c,s,(int64_t)x+(vertical?0:i),(int64_t)y+(vertical?i:0),g,nodeColor(c,i),0);}return 0;
    }
    if(kind==NR_SOURCE_STAGE_PROGRESS){
        static const uint32_t blocks[9]={32,0x258f,0x258e,0x258d,0x258c,0x258b,0x258a,0x2589,0x2588};
        int64_t lo,hi;visibleRange(x,w,s->frameWidth,1,&lo,&hi);int64_t qbase=(int64_t)value*w*8/1000;
        for(int64_t i=lo;i<hi;i++){int64_t qv=qbase-i*8;int q=qv<0?0:qv>8?8:(int)qv;uint32_t g=n[STYLE]%3==1?(q?0x2584:0x2500):n[STYLE]%3==2?(q?0x25a0:0x25a1):blocks[q];put(c,s,(int64_t)x+i,(int64_t)y+h/2,g,nodeColor(c,i),0);}return 0;
    }
    if(kind==NR_SOURCE_STAGE_DIGITS){
        static const unsigned masks[10]={119,36,93,109,46,107,123,37,127,111};int zoom=n[ZOOM];
        for(int k=0;k<n[TLEN];k++){uint32_t ch=c->text[n[TOFF]+k];int64_t bx=(int64_t)x+(int64_t)k*5*zoom;unsigned mask=ch>='0'&&ch<='9'?masks[ch-'0']:ch=='-'?8:0;
            for(int j=0;j<7;j++){if(!(mask&(1u<<j)))continue;int ax=j==1||j==4?0:j==2||j==5?3:1;int ay=j==0?0:j==1||j==2?1:j==3?2:j==4||j==5?3:4;int len=j==0||j==3||j==6?2:1;uint32_t g=j==0||j==3?0x2584:j==6?0x2580:0x2588;
                for(int l=0;l<len;l++)for(int zy=0;zy<zoom;zy++)for(int zx=0;zx<zoom;zx++)put(c,s,bx+(ax+l)*zoom+zx,(int64_t)y+ay*zoom+zy,g,nodeColor(c,k*6+j),k*6+j);
            }
        }return 0;
    }
    if(kind==7){
        int count=n[DLEN];if(count<1)return 0;int64_t barW=w/count;if(barW<1)barW=1;
        int64_t visibleX0,visibleX1,visibleY0,visibleY1;visibleRange(x,w,s->frameWidth,1,&visibleX0,&visibleX1);visibleRange(y,h,s->frameHeight,1,&visibleY0,&visibleY1);
        for(int k=0;k<count&&(int64_t)k*barW<w;k++){
            int target=clampi(c->data[n[DOFF]+k],0,1000),v=tween(0,target,age,(uint32_t)n[DURATION]);
            int64_t col0=(int64_t)k*barW,col1=col0+barW-(barW>2?1:0);if(col0<visibleX0)col0=visibleX0;if(col1>visibleX1)col1=visibleX1;
            for(int64_t j=visibleY0;j<visibleY1;j++){int64_t fillValue=(int64_t)v*h*8/1000-((int64_t)h-1-j)*8;int fill=fillValue<0?0:fillValue>8?8:(int)fillValue;for(int64_t i=col0;i<col1;i++)
                put(c,s,(int64_t)x+i,(int64_t)y+j,fill?0x2580+fill:32,nodeColor(c,(int64_t)k*5+j),0);}
        }return 0;
    }
    if(kind==10){
        int count=n[DLEN];for(int k=0;k+1<count;k+=2){
            int px=(int)((int64_t)clampi(c->data[n[DOFF]+k],0,1000)*((int64_t)w*2-1)/1000);
            int py=(int)((int64_t)(1000-clampi(c->data[n[DOFF]+k+1],0,1000))*((int64_t)h*4-1)/1000);
            uint32_t color=nodeColor(c,k*7);dot(c,s,px,py,color);
            if(n[STYLE]%2){dot(c,s,px-1,py,color);dot(c,s,px+1,py,color);dot(c,s,px,py-1,color);dot(c,s,px,py+1,color);}
        }return 0;
    }
    if(kind==11||kind==13){
        int count=n[DLEN],points=kind==13?count/2:count;if(points<1)return 0;int ox=0,oy=0;
        for(int k=0;k<points;k++){
            int px=kind==13?(int)((int64_t)clampi(c->data[n[DOFF]+k*2],0,1000)*((int64_t)w*2-1)/1000):(points==1?0:(int)((int64_t)k*((int64_t)w*2-1)/(points-1)));
            int py=kind==13?(int)((int64_t)clampi(c->data[n[DOFF]+k*2+1],0,1000)*((int64_t)h*4-1)/1000):(int)((int64_t)(1000-clampi(c->data[n[DOFF]+k],0,1000))*((int64_t)h*4-1)/1000);
            uint32_t color=nodeColor(c,k*2);if(k)drawDotSegment(c,s,ox,oy,px,py,color);else dot(c,s,px,py,color);ox=px;oy=py;
        }
        if(kind==13&&points>=2){
            int phase=(int)(c->timeMs%2400)*1000/2400,part=phase*(points-1)/1000,local=phase*(points-1)%1000;
            if(part>=points-1)part=points-2;
            int a=c->data[n[DOFF]+part*2],b=c->data[n[DOFF]+(part+1)*2];
            int d=c->data[n[DOFF]+part*2+1],e=c->data[n[DOFF]+(part+1)*2+1];
            int px=(int)((int64_t)(a+(b-a)*local/1000)*((int64_t)w*2-1)/1000),py=(int)((int64_t)(d+(e-d)*local/1000)*((int64_t)h*4-1)/1000);
            dot(c,s,px,py,0xf2e6d4);dot(c,s,px+1,py,0xf2e6d4);
        }return 0;
    }
    int count=n[DLEN];int64_t total=0;for(int k=0;k<count;k++)if(c->data[n[DOFF]+k]>0)total+=c->data[n[DOFF]+k];if(!total)return 0;
    int64_t cx=(int64_t)w,cy=(int64_t)h*2,r=(w<(int64_t)h*2?w:(int64_t)h*2)-1;if(r<1)return 0;
    int reveal=tween(0,1024,age,(uint32_t)n[DURATION]);
    int64_t px0,px1,py0,py1;visibleRange(x,w,s->frameWidth,2,&px0,&px1);visibleRange(y,h,s->frameHeight,4,&py0,&py1);int64_t r2=r*r,inner=r2/100*38+(r2%100)*38/100;
    for(int64_t py=py0;py<py1;py++)for(int64_t px=px0;px<px1;px++){
        int64_t dx=px-cx,dy=py-cy,adx=dx<0?-dx:dx,ady=dy<0?-dy:dy;if(adx>r||ady>r)continue;int64_t dx2=dx*dx,dy2=dy*dy;if(dx2>r2||dy2>r2-dx2||(kind==NR_SOURCE_STAGE_DONUT&&dx2+dy2<inner))continue;
        /* stAngle's binary search form is exact and avoids floating point. */
        int32_t ax=(int32_t)(dx<0?-dx:dx),ay=(int32_t)(dy<0?-dy:dy),lo=0,hi=256;
        while(lo<hi){int32_t m=(lo+hi)/2;if((int64_t)nrSourceStageSin1024(m)*ax<(int64_t)nrSourceStageSin1024(m+256)*ay)lo=m+1;else hi=m;}
        int32_t angle=!dx&&!dy?0:dx>=0?(dy>=0?lo:modp(1024-lo,1024)):(dy>=0?512-lo:512+lo);
        int a=modp(angle+256,1024);if(a>reveal)continue;
        int64_t target=(int64_t)a*total,acc=0;int k=0;
        for(;k<count;k++){if(c->data[n[DOFF]+k]>0)acc+=(int64_t)c->data[n[DOFF]+k]*1024;if(target<acc)break;}if(k>=count)k=count-1;
        uint32_t color=(uint32_t)n[FG];if(c->material)nrSourceMaterialPaletteColor(c->material,(int64_t)k*1024/count,&color);
        dot(c,s,px,py,color);
    }
    return 0;
}
