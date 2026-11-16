#include "window_content_source.h"

#include "source_stage_components.h"
#include "window_texture_source.h"

#include <limits.h>
#include <stddef.h>
#include <stdint.h>

enum { K=0, ID=1, X=2, Y=3, W=4, H=5, STATE=6, VALUE=7, FROM=8,
       CHANGED_LO=9, CHANGED_HI=10, DURATION=11, FG=12, BG=13, FGA=14,
       BGA=15, STYLE=16, TOFF=17, TLEN=18, DOFF=19, DLEN=20,
       HSTEP=21, HSPEED=22, HBASE=23, REVEAL=24, SAT=26, BRIGHT=27,
       ANIM=28, GLYPH=29, ZOOM=30 };

typedef struct {
    uint32_t *cells;
    uint32_t width,height;
} NrWindowContentSink;

static int finiteNumber(double n) {
    return n==n && n<=1.7976931348623157e308 && n>=-1.7976931348623157e308;
}

static uint32_t mixChannel(uint32_t a,uint32_t b,uint32_t p) {
    int32_t av=(int32_t)a,bv=(int32_t)b;
    return (uint32_t)(av+(bv-av)*(int32_t)p/1000);
}

static uint32_t mixRgb(uint32_t a,uint32_t b,uint32_t p) {
    return mixChannel((a>>16)&255u,(b>>16)&255u,p)<<16 |
           mixChannel((a>>8)&255u,(b>>8)&255u,p)<<8 |
           mixChannel(a&255u,b&255u,p);
}

static uint32_t mixRgbRounded(uint32_t a,uint32_t b,double amount) {
    uint32_t out=0;
    for(int shift=16;shift>=0;shift-=8) {
        double av=(double)((a>>(uint32_t)shift)&255u);
        double bv=(double)((b>>(uint32_t)shift)&255u);
        uint32_t ch=(uint32_t)(av*(1.0-amount)+bv*amount+0.5);
        out|=ch<<(uint32_t)shift;
    }
    return out;
}

static uint32_t ceilPositive(double value) {
    uint32_t integer=(uint32_t)value;
    return integer+(value>(double)integer);
}

static int validScalars(const uint32_t *text,uint32_t count,uint32_t limit,
                        uint32_t utf16Limit) {
    uint64_t units=0;
    if(count>limit || (count && !text)) return 0;
    for(uint32_t i=0;i<count;i++) {
        uint32_t c=text[i];
        if(c>0x10ffffu || (c>=0xd800u && c<=0xdfffu)) return 0;
        units+=c>0xffffu?2u:1u;
        if(units>utf16Limit) return 0;
    }
    return 1;
}

static int dimensionsValid(uint32_t width,uint32_t height) {
    size_t cells;
    /* The generated box and footer carry positive extents even for callers
       outside the old camera's 24x12 minimum. */
    if(width<9u || height<4u || width>(uint32_t)(INT32_MAX/2) ||
       height>(uint32_t)(INT32_MAX/4)) return 0;
    if((size_t)width>SIZE_MAX/(size_t)height) return 0;
    cells=(size_t)width*(size_t)height;
    return cells<=SIZE_MAX/(4u*sizeof(uint32_t));
}

int nrWindowContentSourceValid(const NrWindowContentSource *s) {
    if(!s || !s->cells4 || !s->ramp2048 || !s->waveform ||
       !dimensionsValid(s->width,s->height) || s->shape>9u ||
       s->inkRgb>0xffffffu || s->backgroundRgb>0xffffffu || s->accentRgb>0xffffffu ||
       !validScalars(s->titleScalars,s->titleCount,160u,160u) ||
       !validScalars(s->contentScalars,s->contentCount,4096u,4096u) ||
       !validScalars(s->labelScalars,s->labelCount,76u,76u) ||
       s->waveformCount!=NR_WINDOW_CONTENT_WAVEFORM_SAMPLES ||
       !finiteNumber(s->clockMs) || !finiteNumber(s->stopTotal) || s->stopTotal<=0.0)
        return 0;
    for(uint32_t i=0;i<NR_WINDOW_CONTENT_RAMP_CELLS;i++)
        if(s->ramp2048[i]>0xffffffu) return 0;
    for(uint32_t i=0;i<s->waveformCount;i++)
        if(!finiteNumber(s->waveform[i])) return 0;
    /* x/width and y/height each stay in [0,1]; checking both extrema proves
       all source phase arithmetic finite without a dimensions-sized scan. */
    double timePhase=s->clockMs/18000.0;
    if(!finiteNumber(timePhase) || !finiteNumber(timePhase/s->stopTotal) ||
       !finiteNumber((timePhase+2.0)/s->stopTotal)) return 0;
    return 1;
}

static uint32_t colorAt(const NrWindowContentSource *s,uint32_t x,uint32_t y) {
    double phase=((double)x/(double)s->width+(double)y/(double)s->height+
                  s->clockMs/18000.0)/s->stopTotal;
    /* Above 2^63 every representable double is integral, avoiding an
       out-of-range float-to-integer conversion for extreme finite clocks. */
    double fract=(phase>9.0e18 || phase< -9.0e18)?0.0:
                 phase-(double)(int64_t)phase;
    if(fract<0.0) fract+=1.0;
    if(fract>=1.0) fract=0.0;
    return s->ramp2048[(uint32_t)(fract*(double)NR_WINDOW_CONTENT_RAMP_CELLS)];
}

static int readCell(void *context,int32_t x,int32_t y,NrSourceStageCell *out) {
    NrWindowContentSink *sink=(NrWindowContentSink *)context;
    if(!sink||!out||x<0||y<0||(uint32_t)x>=sink->width||(uint32_t)y>=sink->height) return -1;
    size_t at=((size_t)(uint32_t)y*sink->width+(uint32_t)x)*4u;
    out->glyph=sink->cells[at];out->foregroundRgb=sink->cells[at+1u];
    out->backgroundRgb=sink->cells[at+2u];out->legacyFlags=sink->cells[at+3u];
    out->semanticOwner=0;return 0;
}

static void cell(void *context,int32_t x,int32_t y,uint32_t operation,uint32_t glyph,
                 uint32_t fg,uint32_t fgOpacity,uint32_t bg,uint32_t bgOpacity,
                 uint32_t bgExplicit,uint32_t legacyFlags,uint32_t semanticOwner) {
    NrWindowContentSink *sink=(NrWindowContentSink *)context;
    size_t at=((size_t)(uint32_t)y*sink->width+(uint32_t)x)*4u;
    uint32_t oldGlyph=sink->cells[at],flat=sink->cells[at+2u];
    if(oldGlyph==0x2580u || oldGlyph==0x2584u || oldGlyph==0x258cu)
        flat=mixRgb(sink->cells[at+2u],sink->cells[at+1u],500u);
    if(operation==NR_SOURCE_CELL_BACKGROUND_TINT) {
        sink->cells[at+2u]=mixRgb(sink->cells[at+2u],bg,bgOpacity);return;
    }
    if(operation==NR_SOURCE_CELL_FLATTEN) {
        sink->cells[at]=glyph;sink->cells[at+2u]=bg;sink->cells[at+3u]=legacyFlags;return;
    }
    if(operation==NR_SOURCE_CELL_FILL) {
        uint32_t nextBg=bgExplicit&&bgOpacity?mixRgb(flat,bg,bgOpacity):sink->cells[at+2u];
        uint32_t base=(bgExplicit&&bgOpacity)?nextBg:flat;
        sink->cells[at]=glyph;
        if(fgOpacity) sink->cells[at+1u]=mixRgb(sink->cells[at+1u],base,fgOpacity);
        sink->cells[at+2u]=nextBg;
    } else {
        sink->cells[at]=glyph;sink->cells[at+1u]=mixRgb(flat,fg,fgOpacity);sink->cells[at+2u]=flat;
    }
    sink->cells[at+3u]=legacyFlags;(void)x;(void)y;(void)semanticOwner;
}

static void subcell(void *context,int32_t x,int32_t y,uint32_t sx,uint32_t sy,
                    uint32_t rgb,uint32_t opacity,uint32_t coverage,
                    uint32_t legacyFlags,uint32_t semanticOwner) {
    static const uint8_t bits[8]={1,8,2,16,4,32,64,128};
    NrWindowContentSink *sink=(NrWindowContentSink *)context;
    if(!coverage||sx>1u||sy>3u)return;
    size_t at=((size_t)(uint32_t)y*sink->width+(uint32_t)x)*4u;
    if(sink->cells[at]<0x2800u||sink->cells[at]>0x28ffu)sink->cells[at]=0x2800u;
    sink->cells[at]|=bits[sy*2u+sx];
    sink->cells[at+1u]=mixRgb(sink->cells[at+2u],rgb,opacity);
    sink->cells[at+3u]=legacyFlags;(void)semanticOwner;
}

static void nodeDefaults(int32_t node[32],uint32_t kind,int32_t x,int32_t y,
                         uint32_t width,uint32_t height,uint32_t fg,uint32_t fgOpacity) {
    for(uint32_t i=0;i<32u;i++)node[i]=0;
    node[K]=(int32_t)kind;node[X]=x;node[Y]=y;node[W]=(int32_t)width;node[H]=(int32_t)height;
    node[FG]=(int32_t)fg;node[FGA]=(int32_t)fgOpacity;node[ZOOM]=1;node[HSTEP]=17;
    node[HSPEED]=24;node[SAT]=620;node[BRIGHT]=830;
}

static void componentRecord(const NrWindowContentSource *s,NrSourceStageComponent *component,
                            uint32_t kind,int32_t x,int32_t y,uint32_t width,uint32_t height,
                            uint32_t fg,uint32_t fgOpacity,const uint32_t *text,uint32_t count,
                            const int32_t *data,uint32_t dataCount,uint32_t style) {
    *component=(NrSourceStageComponent){0};
    nodeDefaults(component->node,kind,x,y,width,height,fg,fgOpacity);
    component->node[STYLE]=(int32_t)style;component->node[TLEN]=(int32_t)count;
    component->node[DLEN]=(int32_t)dataCount;component->text=text;component->textCount=count;
    component->data=data;component->dataCount=dataCount;component->baseColor=s->backgroundRgb;
}

static int componentValid(const NrWindowContentSource *s,int32_t frameWidth,int32_t frameHeight,
                          uint32_t kind,int32_t x,int32_t y,uint32_t width,uint32_t height,
                          uint32_t fg,uint32_t fgOpacity,const uint32_t *text,uint32_t count,
                          const int32_t *data,uint32_t dataCount,uint32_t style) {
    NrSourceStageComponent component;
    componentRecord(s,&component,kind,x,y,width,height,fg,fgOpacity,text,count,data,dataCount,style);
    return nrSourceStageComponentValid(&component,frameWidth,frameHeight);
}

static int applyComponent(const NrWindowContentSource *s,NrSourceStageComponentSink *sink,
                          uint32_t kind,int32_t x,int32_t y,uint32_t width,uint32_t height,
                          uint32_t fg,uint32_t fgOpacity,const uint32_t *text,uint32_t count,
                          const int32_t *data,uint32_t dataCount,uint32_t style) {
    NrSourceStageComponent component;
    componentRecord(s,&component,kind,x,y,width,height,fg,fgOpacity,text,count,data,dataCount,style);
    if(!nrSourceStageComponentValid(&component,sink->frameWidth,sink->frameHeight))return -1;
    return nrSourceStageComponentApply(&component,sink);
}

static uint32_t nextUtf16Chunk(const uint32_t *src,uint32_t end,uint32_t *cursor,
                               int *pendingLow,uint32_t capacity,uint32_t out[4096]) {
    uint32_t used=0,count=0;
    while(used<capacity && (*pendingLow || *cursor<end)) {
        uint32_t c=src[*cursor];
        if(*pendingLow) { out[count++]=0xfffdu;*pendingLow=0;(*cursor)++;used++;continue; }
        if(c<=0xffffu) { out[count++]=c;(*cursor)++;used++;continue; }
        if(capacity-used>=2u) { out[count++]=c;(*cursor)++;used+=2u;continue; }
        out[count++]=0xfffdu;*pendingLow=1;used++;
    }
    return count;
}

static int preflightComponents(const NrWindowContentSource *s,uint32_t px,uint32_t py,
                               uint32_t innerW,int shaped,int64_t startY,int64_t scopeY,
                               uint32_t rowsMax,const int32_t *lineValues) {
    uint32_t frameWidth=(int32_t)s->width,frameHeight=(int32_t)s->height;
    if(shaped) {
        if(!componentValid(s,(int32_t)frameWidth,(int32_t)frameHeight,0u,
             (int32_t)px,(int32_t)py,innerW,1u,s->accentRgb,1000u,
             s->titleScalars,s->titleCount,NULL,0u,0u))return 0;
    } else {
        uint32_t padded[162],n=0;padded[n++]=' ';
        for(uint32_t i=0;i<s->titleCount;i++)padded[n++]=s->titleScalars[i];
        padded[n++]=' ';
        if(!componentValid(s,(int32_t)frameWidth,(int32_t)frameHeight,1u,1,1,
             s->width-2u,s->height-2u,s->accentRgb,900u,padded,n,NULL,0u,0u))return 0;
    }
    uint32_t row=0;
    for(uint32_t i=0;i<=s->contentCount&&row<rowsMax;i++) {
        if(i<s->contentCount&&s->contentScalars[i]!='\n')continue;
        uint32_t end=i,begin=0;
        for(uint32_t j=0;j<i;j++)if(s->contentScalars[j]=='\n')begin=j+1u;
        if(end>begin) {
            uint32_t at=begin;int pendingLow=0;
            while((at<end||pendingLow)&&row<rowsMax) {
                uint32_t chunk[4096];
                uint32_t count=nextUtf16Chunk(s->contentScalars,end,&at,&pendingLow,innerW,chunk);
                if(!componentValid(s,(int32_t)frameWidth,(int32_t)frameHeight,0u,
                    (int32_t)px,(int32_t)(startY+row),innerW,1u,s->inkRgb,1000u,
                    chunk,count,NULL,0u,0u))return 0;
                row++;
            }
        } else row++;
    }
    int64_t remaining=(int64_t)s->height-(int64_t)py-scopeY;
    uint32_t lineHeight=remaining<1?1u:(remaining>3?3u:(uint32_t)remaining);
    if(!componentValid(s,(int32_t)frameWidth,(int32_t)frameHeight,11u,
        (int32_t)px,(int32_t)scopeY,innerW,lineHeight,s->accentRgb,900u,
        NULL,0u,lineValues,NR_WINDOW_CONTENT_WAVEFORM_SAMPLES,0u))return 0;
    if(!shaped&&s->labelCount&&!componentValid(s,(int32_t)frameWidth,(int32_t)frameHeight,0u,
        4,(int32_t)s->height-2u,(s->width>8u?s->width-8u:1u),1u,
        s->accentRgb,1000u,s->labelScalars,s->labelCount,NULL,0u,0u))return 0;
    return 1;
}

int nrWindowContentSourceRender(const NrWindowContentSource *s) {
    NrWindowContentSink context;NrSourceStageComponentSink sink={0};
    uint32_t bodyChunk[4096];
    int32_t lineValues[NR_WINDOW_CONTENT_WAVEFORM_SAMPLES];
    uint32_t px,py,innerW,shaped,tight,rowsMax;
    int64_t scopeY,startY;
    if(!nrWindowContentSourceValid(s))return -1;
    context.cells=s->cells4;context.width=s->width;context.height=s->height;
    sink.context=&context;sink.frameWidth=(int32_t)s->width;sink.frameHeight=(int32_t)s->height;
    sink.readCell=readCell;sink.cell=cell;sink.subcell=subcell;
    shaped=!(s->shape==0u||s->shape==1u||s->shape==6u||s->shape==9u);
    tight=(s->shape==4u||s->shape==8u);
    px=shaped?ceilPositive((double)s->width*(tight?0.25:s->shape==3u?0.15:0.2)):4u;
    py=shaped?ceilPositive((double)s->height*(tight?0.25:0.18)):3u;
    innerW=s->width>px*2u?s->width-px*2u:4u;if(innerW<4u)innerW=4u;
    scopeY=(int64_t)py+3;
    if(scopeY<(int64_t)s->height-(int64_t)py-3)
        scopeY=(int64_t)s->height-(int64_t)py-3;
    startY=shaped?(int64_t)py+2:3;
    rowsMax=scopeY>startY+1?(uint32_t)(scopeY-startY-1):1u;
    for(uint32_t i=0;i<s->waveformCount;i++) {
        double value=0.5+s->waveform[i]*0.4;
        if(value<0.0)value=0.0;if(value>1.0)value=1.0;
        lineValues[i]=(int32_t)(value*1000.0+0.5);
    }
    /* Validate every emitted component against the actual shared Stage
       geometry contract before initialization can mutate caller storage. */
    if(!preflightComponents(s,px,py,innerW,(int)shaped,startY,scopeY,rowsMax,lineValues))return -1;
    for(uint32_t y=0;y<s->height;y++)for(uint32_t x=0;x<s->width;x++) {
        size_t at=((size_t)y*s->width+x)*4u;
        s->cells4[at]=32u;s->cells4[at+1u]=s->inkRgb;
        s->cells4[at+2u]=mixRgbRounded(s->backgroundRgb,colorAt(s,x,y),0.72);
        s->cells4[at+3u]=0u;
    }
    if(shaped) {
        if(applyComponent(s,&sink,0u,(int32_t)px,(int32_t)py,innerW,1u,s->accentRgb,1000u,
                          s->titleScalars,s->titleCount,NULL,0u,0u)<0)return -1;
    } else {
        uint32_t padded[162];uint32_t n=0;padded[n++]=' ';
        for(uint32_t i=0;i<s->titleCount;i++)padded[n++]=s->titleScalars[i];padded[n++]=' ';
        if(applyComponent(s,&sink,1u,1,1,s->width-2u,s->height-2u,s->accentRgb,900u,
                          padded,n,NULL,0u,0u)<0)return -1;
    }
    uint32_t row=0;
    for(uint32_t i=0;i<=s->contentCount&&row<rowsMax;i++) {
        if(i<s->contentCount&&s->contentScalars[i]!='\n')continue;
        uint32_t end=i,begin=0;
        /* Locate this LF-delimited row without relying on prior mutation. */
        for(uint32_t j=0;j<i;j++)if(s->contentScalars[j]=='\n')begin=j+1u;
        if(end>begin) {
            uint32_t at=begin;int pendingLow=0;
            while((at<end||pendingLow)&&row<rowsMax) {
                uint32_t chunkCount=nextUtf16Chunk(s->contentScalars,end,&at,&pendingLow,
                                                    innerW,bodyChunk);
                if(applyComponent(s,&sink,0u,(int32_t)px,(int32_t)(startY+row),innerW,1u,
                    s->inkRgb,1000u,bodyChunk,chunkCount,NULL,0u,0u)<0)return -1;
                row++;
            }
        } else row++;
    }
    int64_t remaining=(int64_t)s->height-(int64_t)py-scopeY;
    uint32_t lineHeight=remaining<1?1u:(remaining>3?3u:(uint32_t)remaining);
    if(applyComponent(s,&sink,11u,(int32_t)px,(int32_t)scopeY,innerW,lineHeight,
        s->accentRgb,900u,NULL,0u,lineValues,NR_WINDOW_CONTENT_WAVEFORM_SAMPLES,0u)<0)return -1;
    if(!shaped && s->labelCount) {
        if(applyComponent(s,&sink,0u,4,(int32_t)s->height-2,(s->width>8u?s->width-8u:1u),1u,
            s->accentRgb,1000u,s->labelScalars,s->labelCount,NULL,0u,0u)<0)return -1;
    }
    return 0;
}
