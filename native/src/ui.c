#include "internal.h"
static void ascii(NrContext*c,int x,int y,const char*s,int width,uint32_t color,double alpha,uint32_t id) {
    uint32_t text[512];
    int n=0;
    while(*s&&n<512) {
        uint32_t cp=(uint8_t)*s++;int more=0;
        if(cp>=0xc2&&cp<=0xdf){cp&=31;more=1;}
        else if(cp>=0xe0&&cp<=0xef){cp&=15;more=2;}
        else if(cp>=0xf0&&cp<=0xf4){cp&=7;more=3;}
        else if(cp>=128){text[n++]=0xfffd;continue;}
        int valid=1;for(int k=0;k<more;k++){unsigned byte=(uint8_t)*s;if(byte<128||byte>191){valid=0;break;}cp=(cp<<6)|(byte&63);s++;}
        text[n++]=valid&&cp<=0x10ffff&&!(cp>=0xd800&&cp<=0xdfff)?cp:0xfffd;
    }
    nrText(c,x,y,text,n,width,color,alpha,id);
}
static void fill(NrContext*c,int x,int y,int w,int h,uint32_t color,double alpha,uint32_t id) {
    if(w<=0||h<=0)return;
    int64_t right=(int64_t)x+w,bottom=(int64_t)y+h;
    int x0=x<0?0:x,y0=y<0?0:y;
    int x1=right>(int64_t)nrView(c)->width?(int)nrView(c)->width:(int)right;
    int y1=bottom>(int64_t)nrView(c)->height?(int)nrView(c)->height:(int)bottom;
    if(x0<c->clip.x)x0=c->clip.x;if(y0<c->clip.y)y0=c->clip.y;
    if(x1>c->clip.x+c->clip.width)x1=c->clip.x+c->clip.width;
    if(y1>c->clip.y+c->clip.height)y1=c->clip.y+c->clip.height;
    for(int yy=y0; yy<y1; yy++)for(int xx=x0; xx<x1; xx++) {
        nrCellBackground(c,xx,yy,color,alpha);
        if(xx>=0&&yy>=0&&xx<(int)nrView(c)->width&&yy<(int)nrView(c)->height&&id&&nrInClip(c,xx,yy))c->cells[yy*nrView(c)->width+xx].id=id;
    }
}
static int sourcePatternEnabled(const State*s,int material) {
    return material>=0&&material<NR_MATERIALS&&s->materialPatterns[material].used;
}
static uint32_t sampleCell(const State*s,int material,uint64_t timeUs,int x,int y,
                           double index,double*alpha) {
    int64_t xQ8=(int64_t)x*256,yQ8=(int64_t)y*256;
    if(xQ8<INT32_MIN)xQ8=INT32_MIN;if(xQ8>INT32_MAX)xQ8=INT32_MAX;
    if(yQ8<INT32_MIN)yQ8=INT32_MIN;if(yQ8>INT32_MAX)yQ8=INT32_MAX;
    return nrPaintAt(s,material,timeUs,(int32_t)xQ8,(int32_t)yQ8,index,alpha);
}
static void fillMaterial(NrContext*c,int x,int y,int w,int h,int material,
                         double index,double alpha,uint32_t id) {
    const State*s=nrView(c);
    if(!sourcePatternEnabled(s,material)) {
        double materialAlpha=1;uint32_t color=nrPaint(s,material,s->timeUs,index,&materialAlpha);
        fill(c,x,y,w,h,color,alpha*materialAlpha,id);
        return;
    }
    if(w<=0||h<=0)return;
    int64_t right=(int64_t)x+w,bottom=(int64_t)y+h;
    int x0=x<0?0:x,y0=y<0?0:y;
    int x1=right>(int64_t)s->width?(int)s->width:(int)right;
    int y1=bottom>(int64_t)s->height?(int)s->height:(int)bottom;
    if(x0<c->clip.x)x0=c->clip.x;if(y0<c->clip.y)y0=c->clip.y;
    if(x1>c->clip.x+c->clip.width)x1=c->clip.x+c->clip.width;
    if(y1>c->clip.y+c->clip.height)y1=c->clip.y+c->clip.height;
    for(int yy=y0;yy<y1;yy++)for(int xx=x0;xx<x1;xx++) {
        double materialAlpha=1;
        uint32_t color=sampleCell(s,material,s->timeUs,xx,yy,index,&materialAlpha);
        nrCellBackground(c,xx,yy,color,alpha*materialAlpha);
        if(id&&nrInClip(c,xx,yy))c->cells[yy*s->width+xx].id=id;
    }
}
static void patternText(NrContext*c,int x,int y,const uint32_t*text,int n,int width,
                        int material,double alpha,uint32_t id,double index) {
    const State*s=nrView(c);
    if(!sourcePatternEnabled(s,material)) {
        double ignored;uint32_t color=nrPaint(s,material,s->timeUs,index,&ignored);
        nrText(c,x,y,text,n,width,color,alpha,id);
        return;
    }
    if(width<1)return;
    int64_t origin=x,cursorX=x,cursorY=y;
    for(int i=0;i<n;i++) {
        uint32_t glyph=text[i];
        if(glyph=='\n'){cursorX=origin;cursorY++;continue;}
        if(cursorX-origin>=width){cursorX=origin;cursorY++;}
        if(cursorY>=s->height)return;
        if(cursorX>=0&&cursorX<s->width&&cursorY>=0) {
            double materialAlpha=1;
            uint32_t color=sampleCell(s,material,s->timeUs,(int)cursorX,(int)cursorY,index,&materialAlpha);
            nrIndexedGlyph(c,(int)cursorX,(int)cursorY,glyph=='\t'?' ':glyph,color,
                           alpha*materialAlpha,id,(uint32_t)i);
        }
        cursorX++;
    }
}
static void patternBox(NrContext*c,int x,int y,int w,int h,int style,int material,
                      double alpha,uint32_t id,double index) {
    const State*s=nrView(c);
    if(!sourcePatternEnabled(s,material)) {
        double ignored;uint32_t color=nrPaint(s,material,s->timeUs,index,&ignored);
        nrBox(c,x,y,w,h,style,color,alpha,id);
        return;
    }
    if(w<1||h<1||!style)return;
    uint32_t left=style==2?0x250c:style==3?0x2554:style==4?0x250f:0x256d;
    uint32_t right=style==2?0x2510:style==3?0x2557:style==4?0x2513:0x256e;
    uint32_t bl=style==2?0x2514:style==3?0x255a:style==4?0x2517:0x2570;
    uint32_t br=style==2?0x2518:style==3?0x255d:style==4?0x251b:0x256f;
    uint32_t horiz=style==3?0x2550:style==4?0x2501:0x2500;
    uint32_t vert=style==3?0x2551:style==4?0x2503:0x2502;
    int64_t rightEdge=(int64_t)x+w-1,bottomEdge=(int64_t)y+h-1;
    int64_t xmin=c->clip.x,ymin=c->clip.y,xmax=xmin+c->clip.width,ymax=ymin+c->clip.height;
    if(xmin<0)xmin=0;if(ymin<0)ymin=0;
    if(xmax>s->width)xmax=s->width;if(ymax>s->height)ymax=s->height;
#define PATTERN_GLYPH(gx,gy,gg) do { \
    double materialAlpha=1;uint32_t color=sampleCell(s,material,s->timeUs,(int)(gx),(int)(gy),index,&materialAlpha); \
    nrGlyph(c,(int)(gx),(int)(gy),(gg),color,alpha*materialAlpha,id); \
} while(0)
    int64_t first=(int64_t)x+1;if(first<xmin)first=xmin;
    int64_t last=rightEdge;if(last>xmax)last=xmax;
    for(int64_t xx=first;xx<last;xx++){
        if(y>=ymin&&y<ymax)PATTERN_GLYPH(xx,y,horiz);
        if(h>1&&bottomEdge>=ymin&&bottomEdge<ymax)PATTERN_GLYPH(xx,bottomEdge,horiz);
    }
    first=(int64_t)y+1;if(first<ymin)first=ymin;
    last=bottomEdge;if(last>ymax)last=ymax;
    for(int64_t yy=first;yy<last;yy++){
        if(x>=xmin&&x<xmax)PATTERN_GLYPH(x,yy,vert);
        if(w>1&&rightEdge>=xmin&&rightEdge<xmax)PATTERN_GLYPH(rightEdge,yy,vert);
    }
    if(x>=xmin&&x<xmax&&y>=ymin&&y<ymax)PATTERN_GLYPH(x,y,left);
    if(w>1&&rightEdge>=xmin&&rightEdge<xmax&&y>=ymin&&y<ymax)PATTERN_GLYPH(rightEdge,y,right);
    if(h>1&&bottomEdge>=ymin&&bottomEdge<ymax){
        if(x>=xmin&&x<xmax)PATTERN_GLYPH(x,bottomEdge,bl);
        if(w>1&&rightEdge>=xmin&&rightEdge<xmax)PATTERN_GLYPH(rightEdge,bottomEdge,br);
    }
#undef PATTERN_GLYPH
}
/* Readable panels own their ink plane. Background composition remains intact;
 * old text/borders behind a new panel must not leak into its empty cells.
 * Cursor/background-only overlays intentionally keep using fill(), not panel(). */
static void panel(NrContext*c,int x,int y,int w,int h,uint32_t color,double alpha,uint32_t id) {
    fill(c,x,y,w,h,color,alpha,id);
    if(alpha<=0)return;
    int64_t right=(int64_t)x+w,bottom=(int64_t)y+h;
    int x0=x<0?0:x,y0=y<0?0:y;
    int x1=right>(int64_t)nrView(c)->width?(int)nrView(c)->width:(int)right;
    int y1=bottom>(int64_t)nrView(c)->height?(int)nrView(c)->height:(int)bottom;
    for(int yy=y0;yy<y1;yy++)for(int xx=x0;xx<x1;xx++)if(nrInClip(c,xx,yy)) {
        uint32_t background=c->cells[yy*nrView(c)->width+xx].background;
        nrGlyph(c,xx,yy,' ',background,1,id);
    }
}
static int lines(const uint32_t*t,int n,int width) {
    if(width<1)return 1;
    int line=1,col=0;
    for(int i=0; i<n; i++) {
        if(t[i]==10) {
            line++;
            col=0;
        }
        else {
            if(col>=width) {
                line++;
                col=0;
            }
            col++;
        }
    }
    return line;
}
/* Display-card policy is current native state; metadata is never destructively
 * shortened. SHA prefix zero means full supplied value, not a generated hash. */
static int longestLine(const uint32_t*t,int count) {
    int width=0,col=0;
    for(int i=0;i<count;i++){if(t[i]==10)col=0;else {col++;if(col>width)width=col;}}
    return width;
}
static int byteRows(const char*text,int inner) {
    return text[0]?1+((int)strlen(text)-1)/inner:0;
}
int nrNodeWidth(const Node*n) {
    int pad=2*(n->padding+1),width=longestLine(n->label,n->labelCount)+pad,measure;
    if(n->showKind&&(measure=(int)strlen(n->kind)+pad)>width)width=measure;
    if(n->showStatus&&(measure=(int)strlen(n->status)+pad)>width)width=measure;
    if(n->showDetail&&(measure=longestLine(n->detail,n->detailCount)+pad)>width)width=measure;
    if(n->showSha&&n->sha[0]){
        int length=(int)strlen(n->sha);if(n->shaPrefix&&length>n->shaPrefix)length=n->shaPrefix;
        measure=length+4+pad;if(measure>width)width=measure;
    }
    return (int)nrClamp(width,n->minColumns,n->maxColumns);
}
int nrNodeHeight(const Node*n,int width) {
    int pad=n->padding+1,inner=width-2*pad;
    if(inner<1)inner=1;
    int height=2*pad+lines(n->label,n->labelCount,inner);
    if(n->showKind)height+=byteRows(n->kind,inner);
    if(n->showStatus)height+=byteRows(n->status,inner);
    if(n->showSha&&n->sha[0]){
        int length=(int)strlen(n->sha);if(n->shaPrefix&&length>n->shaPrefix)length=n->shaPrefix;
        height+=1+(length+3)/inner;
    }
    if(n->showDetail&&n->detailCount)height+=lines(n->detail,n->detailCount,inner);
    return height;
}
int nrPromptColumns(const State*s) {
    int columns=(int)s->width-4;
    return columns>0?columns:1;
}
int nrPromptRows(const State*s) {
    /* A full-viewport source shows one input row; a bounded layer leaves the ordinary prompt layout. */
    if(s->firstPromptSource.enabled&&!s->promptSourceLayer.placement)return 1;
    const Prompt*p=&s->promptDocument;
    if(s->promptFramed.enabled){NrPromptSourceInput input;NrPromptSourceLayout layout;if(nrPromptFramedLayout(s,&input,&layout)==0)return layout.rectHeight;}
    if(!p->active)return 0;
    if(p->mode==0)return 1;
    if(p->mode==3)return s->height>6?(int)s->height-6:1;
    int content=lines(p->glyphs,p->count,nrPromptColumns(s));
    if(s->promptPresentation.layout){uint32_t*logical=s->dynamicPrompt.scratch+51*((size_t)s->dynamicPrompt.capacity+1);int n=nrPromptLogical(s,logical);content=1;for(int i=0;i<n;i++)if((int)logical[i*5+3]+1>content)content=(int)logical[i*5+3]+1;if(p->count&&nrPromptHardBreak(p->glyphs[p->count-1]))content++;}
    if(p->mode==2)content+=2;
    int rows=(int)nrClamp(content,p->minRows,p->maxRows);
    int visible=s->height>5?(int)s->height-5:1;
    return rows<visible?rows:visible;
}
/* The rectangle the active prompt paints in without a prompt source: the framed layout's rectangle, or the
 * compact strip (the boxed band for modes 2 and 3), as nrDrawUI paints them. 0 when no prompt is painted. */
int nrPromptFrameRect(const State*s,int*x,int*y,int*w,int*h) {
    *x=*y=*w=*h=0;if(s->windowApplication.enabled)return 0;
    NrPromptSourceInput input;NrPromptSourceLayout layout;const Prompt*q=&s->promptDocument;
    if(s->promptFramed.enabled&&nrPromptFramedLayout(s,&input,&layout)==0){*x=layout.rectX;*y=layout.rectY;*w=layout.rectWidth;*h=layout.rectHeight;return *w>0&&*h>0;}
    if(!q->active)return 0;
    int rows=nrPromptRows(s),top=(int)s->height-rows-2;if(top<3)top=3;
    if(q->mode>=2){top=q->mode==3?3:top-2;*h=(int)s->height-top-1;}else *h=rows;
    *y=top;*w=(int)s->width;return *w>0&&*h>0;
}
/* One immutable geometry map drives presentation and pointer selection. */
void nrPromptCoordinates(const State*s,int (*out)[2]) {
    if(s->firstPromptSource.enabled){nrFirstPromptCoordinates(s,out);return;}
    const Prompt*p=&s->promptDocument;
    if(s->windowApplication.enabled&&(s->promptAppearance.cursorConfigured||s->promptAppearance.weatherConfigured)){
        int columns=s->width>10?(int)s->width-10:1,start=p->caret>columns?p->caret-columns:0;
        start=nrGraphemeFloor(p->glyphs,p->count,start);
        for(int i=0;i<=p->count;i++){out[i][0]=5+i-start;out[i][1]=i>=start&&i<=start+columns?(int)s->height-4:-1;}
        return;
    }
    if(s->promptFramed.enabled){NrPromptSourceInput input;NrPromptSourceLayout layout;if(nrPromptFramedLayout(s,&input,&layout)<0)return;int64_t row=0,col=0;
        for(int i=0;i<=p->count;i++){if(col==layout.innerWidth){row++;col=0;}out[i][0]=p->mode==0?layout.innerX+i-layout.offset:layout.innerX+(int)col;out[i][1]=p->mode==0?layout.innerY:layout.innerY+(int)row-layout.top;if(i<p->count){if(p->glyphs[i]==10){row++;col=0;}else col++;}}return;}
    if(s->promptPresentation.layout){nrPromptGraphemeCoordinates(s,out);return;}
    int columns=nrPromptColumns(s),rows=nrPromptRows(s),top=(int)s->height-rows-2;
    if(p->mode==0) {
        int start=p->caret>columns?p->caret-columns:0;
        for(int i=0;i<=p->count;i++){out[i][0]=2+i-start;out[i][1]=top;}
        return;
    }
    if(p->mode>=2)top=p->mode==3?3:top-2;
    int row=0,column=0;
    for(int i=0;i<=p->count;i++) {
        out[i][0]=column>=columns?0:column;
        out[i][1]=row+(column>=columns);
        if(i==p->count)break;
        if(p->glyphs[i]==10){row++;column=0;}
        else {if(column>=columns){row++;column=0;}column++;}
    }
    int caretRow=out[p->caret][1],first=caretRow>=rows?caretRow-rows+1:0;
    for(int i=0;i<=p->count;i++) {
        out[i][0]+=2;out[i][1]+=top-first+(p->mode>=2?2:0);
    }
}
void nrPromptCoordinate(const State*s,int index,int*x,int*y) {
    if(s->promptFramed.enabled&&!s->firstPromptSource.enabled){nrPromptFramedCoordinate(s,index,x,y);return;}
    int (*coordinates)[2]=(int(*)[2])s->dynamicPrompt.scratch;nrPromptCoordinates(s,coordinates);
    index=(int)nrClamp(index,0,s->promptDocument.count);
    *x=coordinates[index][0];*y=coordinates[index][1];
}
int nrPromptHit(const State*s,int x,int y) {
    if(s->firstPromptSource.enabled)return nrFirstPromptHit(s,x,y);
    if(s->promptFramed.enabled){int index=nrPromptFramedHit(s,x,y);return index>=0?index:s->promptDocument.caret;}
    if(s->promptPresentation.layout)return nrPromptGraphemeHit(s,x,y);
    int (*coordinates)[2]=(int(*)[2])s->dynamicPrompt.scratch;nrPromptCoordinates(s,coordinates);
    int top=(int)s->height-nrPromptRows(s)-2;if(top<3)top=3;
    int minimum=s->promptDocument.mode==3?5:top;
    int best=s->promptDocument.caret,bestRow=INT32_MAX,bestColumn=INT32_MAX;
    for(int i=0;i<=s->promptDocument.count;i++) {
        int cx=coordinates[i][0],cy=coordinates[i][1];
        if(cx<2||cx>=(int)s->width-1||cy<minimum||cy>=(int)s->height-2)continue;
        int dy=cy-y,dx=cx-x;if(dy<0)dy=-dy;if(dx<0)dx=-dx;
        /* Prefer the later boundary at a shared position (e.g. a newline after
         * an exact-width row). Clipped/offscreen source cannot capture a hit. */
        if(dy<bestRow||(dy==bestRow&&dx<=bestColumn)){best=i;bestRow=dy;bestColumn=dx;}
    }
    return best;
}
int nrPromptVertical(const State*s,int direction,int grapheme) {
    const Prompt*p=&s->promptDocument;
    if(p->mode==0) {
        int index=(int)nrClamp(p->caret+direction*nrPromptColumns(s),0,p->count);
        return grapheme?nrGraphemeFloor(p->glyphs,p->count,index):index;
    }
    int (*coordinates)[2]=(int(*)[2])s->dynamicPrompt.scratch;nrPromptCoordinates(s,coordinates);
    uint32_t*boundaries=s->dynamicPrompt.scratch+56*((size_t)s->dynamicPrompt.capacity+1);
    int n=grapheme?nrGraphemeBreaks(p->glyphs,(uint32_t)p->count,boundaries,s->dynamicPrompt.capacity+1):p->count+1;
    int origin=grapheme?nrGraphemeFloor(p->glyphs,p->count,p->caret):p->caret;
    int x=coordinates[origin][0],y=coordinates[origin][1],target=y+direction;
    int best=origin,bestRow=INT32_MAX,bestColumn=INT32_MAX,bestX=x;
    for(int k=0;k<n;k++) {
        int i=grapheme?(int)boundaries[k]:k,cx=coordinates[i][0],cy=coordinates[i][1];
        if(direction<0?cy>=y:cy<=y)continue;
        int dy=cy-target,dx=cx-x;if(dy<0)dy=-dy;if(dx<0)dx=-dx;
        /* All document rows are available, including clipped source. Equal
         * distance across a cluster chooses its left boundary; duplicate
         * screen positions choose the later source offset, as pointer hits do. */
        if(dy<bestRow||(dy==bestRow&&(dx<bestColumn||(dx==bestColumn&&cx<=bestX)))) {
            best=i;bestRow=dy;bestColumn=dx;bestX=cx;
        }
    }
    return best;
}
void nrDrawSceneGeometry(NrContext*c,const Projection*p) {
    const State*s=nrView(c);
    c->paintDetail=1;c->paintSampling=2;
    for(int e=0; e<s->edgeCount; e++) {
        c->paintOwner=0x40000000u|(uint32_t)(e+1);
        int ai=nrFindNode(s,s->edges[e].from),bi=nrFindNode(s,s->edges[e].to);
        if(ai<0||bi<0)continue;
        Vec3 a=nrNodeAt(&s->nodes[ai],s->timeUs),b=nrNodeAt(&s->nodes[bi],s->timeUs);
        uint32_t color=s->edges[e].kind==0?0x5c8f91:s->edges[e].kind==2?0x9d829c:0x92784e;
        double alpha=.5;
        if(s->selection&&(s->edges[e].from==s->selection||s->edges[e].to==s->selection))alpha=.85;
        nrLine(c,p,a,b,color,alpha);
        Vec3 tip=nrAdd(a,nrScale(nrSub(b,a),.6));
        nrPoint(c,p,tip,color,alpha,.1);
    }
    c->paintDetail=0;c->paintSampling=1;c->paintOwner=4;
    nrDrawWindowsGeometry(c,p);
}
static void drawGraph(NrContext*c,const Projection*p) {
    const State*s=nrView(c);
    const int compactSpatial=s->sourceGraphLayout.enabled&&s->dimensions==3&&!p->orthographic;
    int graphWidth=s->selection?(int)s->width-38:(int)s->width;if(graphWidth<20)graphWidth=20;
    int graphTop=1;
    if(s->canvasPresentation){int sceneHeight;nrSceneViewport(s,&graphWidth,&sceneHeight);graphTop=0;}
    ClipRect graphClip=nrClip(c,0,graphTop,graphWidth,c->promptTop-graphTop);
    int order[NR_MAX_NODES],count=0;double depths[NR_MAX_NODES];
    for(int i=0;i<(int)NR_MAX_NODES;i++)if(s->nodes[i].used){order[count]=i;depths[count++]=nrDot(nrSub(nrNodeAt(&s->nodes[i],s->timeUs),p->position),p->forward);}
    if(s->dimensions==3)for(int i=1;i<count;i++){int slot=order[i],k=i;double depth=depths[i];while(k&&(depths[k-1]<depth||(depths[k-1]==depth&&s->nodes[order[k-1]].id>s->nodes[slot].id))){order[k]=order[k-1];depths[k]=depths[k-1];k--;}order[k]=slot;depths[k]=depth;}
    for(int oi=0;oi<count;oi++) {
        const Node*n=&s->nodes[order[oi]];
        if(!n->used)continue;
        double x,y,z;
        if(!nrProject(p,nrNodeAt(n,s->timeUs),&x,&y,&z))continue;
        int width=nrNodeWidth(n),height=nrNodeHeight(n,width);
        if(compactSpatial){int utf16=n->labelCount;for(int i=0;i<n->labelCount;i++)if(n->label[i]>0xffff)utf16++;
            double scale=p->orthographic?1:nrClamp(65/(z<12?12:z),.5,1.4);width=(int)nrFloor(nrClamp((utf16+5)*scale,9,s->selection==n->id?30:23)+.5);height=s->selection==n->id?5:3;}
        int xx=s->dimensions==3?(int)nrFloor(x/2-width/2.0+.5):(int)(x/2)-width/2,yy=s->dimensions==3?(int)nrFloor(y/4-height/2.0+.5):(int)(y/4)-height/2;
        if((int64_t)xx+width<0||xx>=(int)s->width||(int64_t)yy+height<1||yy>=c->promptTop)continue;
        double fade=nrClamp(150/(z+30),.25,1);
        uint32_t color=n->color?n->color:nrOklch(730000,80000,(int32_t)(nrHash((uint32_t)(uint8_t)n->kind[0]*17+ (uint8_t)n->kind[1])%360000));
        uint32_t id=NR_ID_NODE|(uint32_t)n->id;
        panel(c,xx,yy,width,height,0x14202a,.91*fade,id);
        nrBox(c,xx,yy,width,height,s->selection==n->id?3:1,color,fade,id);
        if(compactSpatial){
            uint32_t label[32];int length=0,limit=width-5;label[length++]=s->selection==n->id?0x25c6:0x25c7;label[length++]=32;
            int shown=n->labelCount;if(shown>limit)shown=limit-1;for(int i=0;i<shown&&length<30;i++)label[length++]=n->label[i];if(shown<n->labelCount)label[length++]=0x2026;
            nrText(c,xx+1,yy+1,label,length,width-2,0xe4dfd2,fade,id);continue;
        }
        int pad=n->padding+1,inner=width-2*pad,row=yy+pad;
        if(n->showKind&&n->kind[0]){ascii(c,xx+pad,row,n->kind,inner,color,fade,id);row+=byteRows(n->kind,inner);}
        nrText(c,xx+pad,row,n->label,n->labelCount,inner,0xe4dfd2,fade,id);
        row+=lines(n->label,n->labelCount,inner);
        if(n->showStatus&&n->status[0]){ascii(c,xx+pad,row,n->status,inner,0xa2c7b5,fade,id);row+=byteRows(n->status,inner);}
        if(n->showSha&&n->sha[0]) {
            char value[134]="SHA ";int length=(int)strlen(n->sha);
            if(n->shaPrefix&&length>n->shaPrefix)length=n->shaPrefix;
            memcpy(value+4,n->sha,(size_t)length);value[length+4]=0;
            ascii(c,xx+pad,row,value,inner,0xa8a0b4,fade,id);row+=1+(length+3)/inner;
        }
        if(n->showDetail&&n->detailCount)nrText(c,xx+pad,row,n->detail,n->detailCount,inner,0xa8b8bf,fade,id);
    }
    c->clip=graphClip;
    if(s->selection) {
        int ni=nrFindNode(s,s->selection);
        if(ni<0)return;
        const Node*n=&s->nodes[ni];
        int x=(int)s->width-37,y=2,h=c->promptTop-3;
        panel(c,x,y,36,h,0x15212c,.96,0x7fffffffu);
        nrBox(c,x,y,36,h,1,0x8faeb1,1,0x7fffffffu);
        ascii(c,x+2,y+1,"NODE / PgUp PgDn / scroll",32,0xc6aecf,1,0x7fffffffu);
        ClipRect clip=nrClip(c,x+1,y+2,34,h-3);
        int row=y+3-s->selectionScroll;
        nrText(c,x+2,row,n->label,n->labelCount,32,0xe4dfd2,1,0x7fffffffu);
        row+=lines(n->label,n->labelCount,32)+1;
        ascii(c,x+2,row,n->status,32,0xa3caba,1,0x7fffffffu);row+=((int)strlen(n->status)+31)/32;
        if(n->sha[0]) {
            ascii(c,x+2,row++,"SHA / supplied record",32,0xabb5c6,1,0x7fffffffu);
            ascii(c,x+2,row,n->sha,32,0xa7a7bc,1,0x7fffffffu);
            row+=(int)strlen(n->sha)/32+1;
        }
        if(n->detailCount){nrText(c,x+2,row,n->detail,n->detailCount,32,0xabb5c6,1,0x7fffffffu);row+=lines(n->detail,n->detailCount,32)+1;}
        static const char*kind[]={"contains","depends","parent","reference","produces","related"};
        for(int relation=0; relation<2; relation++) {
            ascii(c,x+2,row++,relation?"CHILDREN":"PARENTS",32,0xc5b18c,1,0x7fffffffu);
            for(int e=0; e<s->edgeCount; e++) {
                int target=-1;
                if(!relation&&s->edges[e].to==s->selection)target=nrFindNode(s,s->edges[e].from);
                if(relation&&s->edges[e].from==s->selection)target=nrFindNode(s,s->edges[e].to);
                if(target<0)continue;
                const Node*q=&s->nodes[target];
                int rows=lines(q->label,q->labelCount,30);
                ascii(c,x+2,row++,kind[s->edges[e].kind],32,0xc5b18c,1,0x7fffffffu);
                nrText(c,x+3,row,q->label,q->labelCount,30,0x9bc5c5,1,NR_ID_NODE|(uint32_t)q->id);
                row+=rows+1;
            }
        }
        if(row+s->selectionScroll>=y+h-1)c->contentNeedsReader++;
        c->clip=clip;
    }
}
static void pageText(NrContext*c,int x,int y,const uint32_t*text,int n,int width,int first,int height,uint32_t color,double alpha,uint32_t id) {
    ClipRect clip=nrClip(c,x,y,width,height);int row=0,col=0;
    for(int i=0;i<n;i++) {
        uint32_t g=text[i];
        if(g==10){row++;col=0;continue;}
        if(col>=width){row++;col=0;}
        if(row>=first&&row<first+height)nrIndexedGlyph(c,x+col,y+row-first,g==9?' ':g,color,alpha,id,(uint32_t)i);
        col++;
    }
    c->clip=clip;
}
/* The recovery reader has a fixed two-cell shell and one-cell content inset.
 * Its title and body form one scroll sequence; source padding/opacity and the
 * camera cannot reduce its readable footprint. These calculations are shared
 * with input routing so paging never accumulates an invisible overscroll. */
int nrWindowReaderPageRows(const State*s) {
    int rows=(int)s->height-4;
    return rows>0?rows:1;
}
int nrWindowReaderMaxScroll(const State*s,const Window*w) {
    int columns=(int)s->width-4;
    int count;const uint32_t*document=nrWindowDocument(s,w,&count);
    int rows=lines(w->title,w->titleCount,columns)+1+lines(document,count,columns);
    int maximum=rows-nrWindowReaderPageRows(s);
    return maximum>0?maximum:0;
}
static void drawWindowReader(NrContext*c) {
    const State*s=nrView(c);
    int selected=nrFindWindow(s,s->selectedWindow);
    if(selected<0)return;
    const Window*w=&s->windows[selected];
    if(!w->reader||!w->target)return;
    int width=(int)s->width-2,height=(int)s->height-2,inner=width-2;
    int rows=nrWindowReaderPageRows(s);
    int first=(int)nrClamp(w->scrollRow,0,nrWindowReaderMaxScroll(s,w));
    uint32_t id=NR_ID_WINDOW|(uint32_t)w->id;
    ClipRect clip=nrClip(c,1,1,width,height);
    panel(c,1,1,width,height,0x101923,1,id);
    nrBox(c,1,1,width,height,1,0xa3cabe,1,id);
    ascii(c,3,1,"Reader",inner-2,0xc6dace,1,id);
    pageText(c,2,2,w->title,w->titleCount,inner,first,rows,0xd7dcca,1,id);
    int count;const uint32_t*document=nrWindowDocument(s,w,&count);
    pageText(c,2,2,document,count,inner,
             first-lines(w->title,w->titleCount,inner)-1,rows,0xe0dcd0,1,id);
    if(nrWindowReaderMaxScroll(s,w)>0)c->contentNeedsReader++;
    ascii(c,2,height,s->width<40?"PgUp/Dn Esc F6":"PgUp/PgDn: scroll | Esc: exit | F6: next window",inner,0xa3cabe,1,id);
    c->clip=clip;
}
static void drawWindows(NrContext*c,const Projection*p) {
    const State*s=nrView(c);int order[NR_MAX_WINDOWS],count=0;
    int textured=s->windowTextures.count!=0;
    for(int i=0;i<(int)NR_MAX_WINDOWS;i++)if(s->windowContent[i].enabled)textured=1;
    if(textured)for(size_t cell=0;cell<(size_t)s->width*s->height;cell++)c->windowDepth[cell]=1.7976931348623157e308;
    for(int i=0;i<(int)NR_MAX_WINDOWS;i++)if(s->windows[i].used)order[count++]=i;
    /* Source presentations retain the original far-to-near painter order,
     * using selection order only at equal camera depth. Legacy slots retain
     * their established focus policy and positions relative to that subset. */
    int sourceSlots[NR_MAX_WINDOWS],sourceCount=0;
    for(int i=0;i<count;i++)if((s->windowPresentation[order[i]].enabled||s->windowTextures.windows[order[i]].width||s->windowContent[order[i]].enabled)){
        int slot=order[i],at=sourceCount;double depth=s->atelierWindows[slot].enabled?-s->windows[slot].position.z:nrDot(nrSub(s->windows[slot].position,p->position),p->forward);
        while(at>0){int prior=sourceSlots[at-1];double previous=s->atelierWindows[prior].enabled?-s->windows[prior].position.z:nrDot(nrSub(s->windows[prior].position,p->position),p->forward);
            if(previous>depth||(previous==depth&&s->windowSourceOrder[prior]<=s->windowSourceOrder[slot]))break;
            sourceSlots[at]=prior;at--;
        }sourceSlots[at]=slot;sourceCount++;
    }
    for(int i=0,k=0;i<count;i++)if((s->windowPresentation[order[i]].enabled||s->windowTextures.windows[order[i]].width||s->windowContent[order[i]].enabled))order[i]=sourceSlots[k++];
    for(int i=0;i<count;i++)if(s->windows[order[i]].id==s->selectedWindow&&!(s->windowPresentation[order[i]].enabled||s->windowTextures.windows[order[i]].width||s->windowContent[order[i]].enabled)){int k=order[i];memmove(order+i,order+i+1,(size_t)(count-i-1)*sizeof(int));order[count-1]=k;break;}
    for(int k=0;k<count;k++) {
        const Window*w=&s->windows[order[k]];
        if(w->reader&&w->target&&w->id==s->selectedWindow)continue;
        if(nrDrawWindowTexture(c,p,order[k]))continue;
        double vis=s->reducedMotion?w->target:nrWindowVisibility(w,s->timeUs);
        if(vis<.002)continue;
        double x=0,y=0,z=1;int visible=nrProject(p,w->position,&x,&y,&z);
        if(!visible&&!w->reader)continue;
        int pad=w->padding+1,width=w->minColumns;
        int bodyWidth=longestLine(w->text,w->textCount)+2*pad;
        int titleWidth=longestLine(w->title,w->titleCount)+2*pad;
        if(bodyWidth>width)width=bodyWidth;if(titleWidth>width)width=titleWidth;
        int chromeWidth=w->chromeSize*3+6;if(chromeWidth>width)width=chromeWidth;
        if(width>w->maxColumns)width=w->maxColumns;
        if(width>(int)s->width-4)width=s->width-4;
        int available=c->promptTop-4;
        if(width<8||available<4){c->contentNeedsReader++;continue;}
        int inner=width-2*pad;if(inner<1){c->contentNeedsReader++;continue;}
        int titleRows=lines(w->title,w->titleCount,inner);
        int bodyRows=lines(w->text,w->textCount,inner),height=bodyRows+titleRows+2*pad+1;
        double alpha=vis;
        if(w->reader||w->maximized) {
            width=(int)s->width-4;height=available;
            inner=width-2*pad;if(inner<1){c->contentNeedsReader++;continue;}
            titleRows=lines(w->title,w->titleCount,inner);
            bodyRows=lines(w->text,w->textCount,inner);
        } else {
            if(height>available){c->contentNeedsReader++;continue;}
            double pw=w->width*(p->orthographic?p->scale:p->focal/z)/2;
            double ph=w->height*(p->orthographic?p->scale:p->focal/z)/4;
            double ratio=pw/width;if(ph/height<ratio)ratio=ph/height;
            alpha*=nrEase((ratio-w->fadeEndRatio)/(w->fadeStartRatio-w->fadeEndRatio),3);
            if(alpha<.01){c->contentNeedsReader++;continue;}
        }
        int xx=(int)(x/2)-width/2,yy=(int)(y/4)-height/2;
        if(w->reader||w->maximized){xx=2;yy=1;}
        if(xx<1)xx=1;if(xx+width>=(int)s->width)xx=(int)s->width-width-1;
        if(yy<1)yy=1;if(yy+height>c->promptTop-3)yy=c->promptTop-3-height;
        if(yy<1)yy=1;
        ClipRect clip=nrClip(c,xx,yy,width,height);
        double ma;uint32_t color=nrPaint(s,w->material,s->timeUs,w->id,&ma),id=NR_ID_WINDOW|(uint32_t)w->id;
        if(sourcePatternEnabled(s,w->material)){
            int64_t right=(int64_t)xx+width,bottom=(int64_t)yy+height;
            int x0=xx<0?0:xx,y0=yy<0?0:yy,x1=right>s->width?(int)s->width:(int)right,y1=bottom>s->height?(int)s->height:(int)bottom;
            for(int py=y0;py<y1;py++)for(int px=x0;px<x1;px++){double pa=1;uint32_t ink=sampleCell(s,w->material,s->timeUs,px,py,w->id,&pa);nrCellBackground(c,px,py,nrMix(ink,0x10131d,.78),nrWindowOpacity(s,order[k])*alpha*pa);c->cells[(size_t)py*s->width+px].id=id;}
        }else panel(c,xx,yy,width,height,nrMix(color,0x10131d,.78),nrWindowOpacity(s,order[k])*alpha,id);
        patternBox(c,xx,yy,width,height,w->border,w->material,alpha,id,w->id);
        pageText(c,xx+pad,yy+pad,w->title,w->titleCount,inner,0,titleRows,0xd7dcca,alpha,id);
        int right=xx+width-2;
        const uint32_t tools[3]={NR_ID_CLOSE,NR_ID_MAX,NR_ID_MIN};
        const uint32_t toolColors[3]={0xeb989a,0xa0d2b2,0xddbf88};
        const uint32_t glyphs[3]={'x','+','-'};
        for(int tool=0;tool<3;tool++){
            int bx=right-w->chromeSize+1;
            uint32_t hit=tools[tool]|(uint32_t)w->id;
            fill(c,bx,yy,w->chromeSize,1,toolColors[tool],.17*alpha,hit);
            nrGlyph(c,bx+w->chromeSize/2,yy,glyphs[tool],toolColors[tool],alpha,hit);
            right=bx-2;
        }
        int h=height-titleRows-2*pad-1,first=w->scrollRow;
        if(h<1)h=1;if(first>bodyRows-h)first=bodyRows-h;if(first<0)first=0;
        pageText(c,xx+pad,yy+pad+titleRows+1,w->text,w->textCount,inner,first,h,0xe0dcd0,alpha,id);
        if(bodyRows>h){c->contentNeedsReader++;ascii(c,xx+pad,yy+height-1,"PgUp/PgDn: document",inner,color,alpha,id);}
        c->clip=clip;
    }
    if(count&&!s->windowApplication.enabled) {
        /* Ordinary dock titles are measured instead of chopped to 16 cells.
         * Oversized titles wrap in the two-row slot; F6 exposes the complete
         * document when a title itself exceeds this bounded navigation surface. */
        int slotWidth=18;
        for(int i=0;i<(int)NR_MAX_WINDOWS;i++)if(s->windows[i].used){
            int n=longestLine(s->windows[i].title,s->windows[i].titleCount)+2;
            if(n>slotWidth)slotWidth=n;
        }
        if(slotWidth>44)slotWidth=44;
        int dockColumns=(int)s->width-4;
        /* Below the dock's readable footprint retain its documents for F6 and
         * metadata recovery. Never manufacture negative slot widths/divisors. */
        if(dockColumns<3){c->contentNeedsReader+=count;return;}
        if(slotWidth>dockColumns)slotWidth=dockColumns;
        int pageSize=dockColumns/(slotWidth+1);if(pageSize<1)pageSize=1;
        int pages=(count+pageSize-1)/pageSize,page=s->dockPage%pages;
        int first=page*pageSize,xx=2,yy=c->promptTop-2,seen=0;
        for(int i=0;i<(int)NR_MAX_WINDOWS;i++) {
            const Window*w=&s->windows[i];if(!w->used)continue;
            int ordinal=seen++;if(ordinal<first||ordinal>=first+pageSize)continue;
            int width=slotWidth;
            uint32_t id=NR_ID_DOCK|(uint32_t)w->id;
            panel(c,xx,yy,width,2,0x1b2830,.95,id);
            int titleRows=lines(w->title,w->titleCount,width-2);
            pageText(c,xx+1,yy,w->title,w->titleCount,width-2,0,titleRows>1?2:1,0xbad9cd,1,id);
            if(titleRows<=1)ascii(c,xx+1,yy+1,"F6: full reader",width-2,0x8ba5b0,1,id);
            xx+=slotWidth+1;
        }
    }
}
static void drawWidgets(NrContext*c) {
    const State*s=nrView(c);
    uint32_t previousOwner=c->characterOwner;
    for(int i=0; i<NR_WIDGETS; i++) {
        c->characterOwner=previousOwner;
        const Widget*w=&s->widgets[i];
        if(!w->used)continue;
        double ma;
        int x=w->x,y=w->y,width=w->width,h=w->height;
        uint32_t color=sourcePatternEnabled(s,w->material)?sampleCell(s,w->material,s->timeUs,x,y,i,&ma):nrPaint(s,w->material,s->timeUs,i,&ma);
        uint32_t id=w->enabled?(NR_ID_WIDGET|(uint32_t)w->id):0;
        double a=(w->enabled?1:.38)*ma;
        double patternInkAlpha=sourcePatternEnabled(s,w->material)?(w->enabled?1:.38):a;
        double value=nrClamp((w->value-w->min)/(w->max-w->min),0,1);
        if((int64_t)x+width<=0||(int64_t)y+h<=0||x>=(int)s->width||y>=(int)s->height)continue;
        c->characterOwner=(1u<<16)|(uint32_t)w->id;
        int geometric=w->kind>=6&&w->kind<=13;
        nrUseMaterial(c,w->backgroundMaterial);
        if(w->backgroundMaterial>=0)fillMaterial(c,x,y,width,h,w->backgroundMaterial,i,w->alpha,geometric?0:id);
        else fill(c,x,y,width,h,w->selected?0x304844:0x142029,w->alpha,geometric?0:id);
        nrUseMaterial(c,w->material);
        if(w->active){double pulse=s->reducedMotion?.25:w->pulseUs?.2+.15*nrSin((s->timeUs%w->pulseUs)*360.0/w->pulseUs):.25;fillMaterial(c,x,y,width,h,w->material,i,pulse*(w->enabled?1:.38),geometric?0:id);}
        patternBox(c,x,y,width,h,w->border,w->material,patternInkAlpha,id,i);
        int pad=w->padding+(w->border?1:0),ix=x+pad,iy=y+pad,iw=width-pad*2,ih=h-pad*2;
        if(iw<1||ih<1)continue;
        if(geometric){
            ClipRect previousClip=nrClip(c,ix,iy,iw,ih);
            nrDrawPlot(c,w,ix,iy,iw,ih,color,a,id,i);
            c->clip=previousClip;continue;
        }
        switch(w->kind) {
            case 0:case 3:case 4:case 16:patternText(c,ix,iy,w->text,w->count,iw,w->material,patternInkAlpha,id,i);
            break;
            case 1:break;
            case 2: {
                uint32_t glyphs[6]= {
                    0x2500,0x00b7,'_',0x203e,'-',0x2501
                };
                int64_t first=ix<0?-(int64_t)ix:0,last=(int64_t)s->width-ix;if(last>iw)last=iw;
                for(int64_t k=first;k<last;k++){int gx=(int)((int64_t)ix+k);uint32_t ink=nrOklch(700000,65000,(int32_t)((k*7+(int)(s->timeUs/20000))%360*1000));double inkAlpha=a;if(sourcePatternEnabled(s,w->material)){double materialAlpha=1;ink=sampleCell(s,w->material,s->timeUs,gx,iy,i,&materialAlpha);inkAlpha=(w->enabled?1:.38)*materialAlpha;}nrGlyph(c,gx,iy,glyphs[(k+(int)(s->timeUs/150000)+w->mode)%6],ink,inkAlpha,id);}
                break;
            }
            case 5: {
                NrCell*p=&c->cells[(iy>=0&&iy<(int)s->height?iy:0)*s->width+(ix>=0&&ix<(int)s->width?ix:0)];
                uint32_t old=p->foreground;
                double waveAlpha=.5+.25*nrSin(s->timeUs/10000.0);uint32_t waveColor=color;
                if(sourcePatternEnabled(s,w->material)){double materialAlpha=1;waveColor=sampleCell(s,w->material,s->timeUs,ix,iy,i,&materialAlpha);waveAlpha=(.5+.25*nrSin(s->timeUs/10000.0))*materialAlpha;}
                nrCellBackground(c,ix,iy,waveColor,waveAlpha);
                if(p->glyph!=32)p->foreground=old;
                break;
            }
            case 14:case 15:{
            const char*mark=w->kind==14?(w->selected?"[x]":"[ ]"):(w->selected?"(*)":"( )");
            if(sourcePatternEnabled(s,w->material)){uint32_t glyphs[3]={(uint8_t)mark[0],(uint8_t)mark[1],(uint8_t)mark[2]};patternText(c,ix,iy,glyphs,3,3,w->material,patternInkAlpha,id,i);}
            else ascii(c,ix,iy,mark,3,color,a,id);
            patternText(c,ix+4,iy,w->text,w->count,iw-4,w->material,patternInkAlpha,id,i);
            break;
            }
            case 17: {
                int64_t first=iy<0?-(int64_t)iy:0,last=(int64_t)s->height-iy;if(last>ih)last=ih;
                for(int64_t yy=first;yy<last;yy++){int gy=(int)((int64_t)iy+yy);double inkAlpha=yy==(int)(value*(ih-1))?a:.25;uint32_t ink=color;if(sourcePatternEnabled(s,w->material)){double materialAlpha=1;ink=sampleCell(s,w->material,s->timeUs,ix,gy,i,&materialAlpha);inkAlpha=(yy==(int)(value*(ih-1))?(w->enabled?1:.38):.25)*materialAlpha;}nrGlyph(c,ix,gy,yy==(int)(value*(ih-1))?0x2588:0x2502,ink,inkAlpha,id);}
                break;
            }
            default:break;
        }
    }
    c->characterOwner=previousOwner;
}
static int areaRect(const State*s,int id,int*x,int*y,int*w,int*h,int*clipX,int*clipY,int*clipW,int*clipH,int depth) {
    (void)depth;int64_t row[12];
    if(!nrResolveArea(s,(uint32_t)id,row)||!row[6]||!row[7]||row[0]<NR_LAYOUT_MIN||row[0]>NR_LAYOUT_MAX||row[1]<NR_LAYOUT_MIN||row[1]>NR_LAYOUT_MAX)return 0;
    *x=(int)row[0];*y=(int)row[1];*w=(int)row[2];*h=(int)row[3];
    *clipX=(int)row[4];*clipY=(int)row[5];*clipW=(int)row[6];*clipH=(int)row[7];return 1;
}
static void drawStatus(NrContext*c) {
    const State*s=nrView(c);
    uint32_t previousOwner=c->characterOwner;
    for(int a=-1; a<NR_AREAS; a++) {
        c->characterOwner=previousOwner;
        Area fallback= {
            .used=1,.id=0,.x=1,.y=(int)s->height-1,.width=(int)s->width-2,.height=1,.material=2,.speedX=8,.speedY=1,.fadeUs=500000
        };
        const Area*area=a<0?&fallback:&s->areas[a];
        if(!area->used)continue;
        int x=area->x,y=area->y,w=area->width,h=area->height,cx=0,cy=0,cw=s->width,ch=s->height;
        if(a>=0&&!areaRect(s,area->id,&x,&y,&w,&h,&cx,&cy,&cw,&ch,0))continue;
        int active=0;
        for(int m=0; m<NR_MESSAGES; m++)if(s->messages[m].used&&s->messages[m].area==area->id&&s->messages[m].state==1)active++;
        if(!active&&area->hideEmpty)continue;
        c->characterOwner=a>=0?(5u<<16)|(uint32_t)area->id:0;
        double ma;
        uint32_t color=nrPaint(s,area->material,s->timeUs,0,&ma);
        int oldBlend=c->paintBlend;c->paintBlend=s->materials[area->material].blend;
        int x0=x>cx?x:cx,y0=y>cy?y:cy;
        int x1=(int)((int64_t)x+w<(int64_t)cx+cw?(int64_t)x+w:(int64_t)cx+cw);
        int y1=(int)((int64_t)y+h<(int64_t)cy+ch?(int64_t)y+h:(int64_t)cy+ch);
        ClipRect oldClip=nrClip(c,cx,cy,cw,ch);
        fill(c,x0,y0,x1-x0,y1-y0,0x122028,area->alpha,0);
        if(sourcePatternEnabled(s,area->material))patternBox(c,x,y,w,h,area->border,area->material,.7,0,area->id);
        else nrBox(c,x,y,w,h,area->border,color,.7*ma,0);
        int pad=area->padding+(area->border?1:0),iw=w-2*pad,ih=h-2*pad;
        if(iw<1||ih<1){
            for(int m=0;m<NR_MESSAGES;m++){const Message*q=&s->messages[m];if(q->used&&q->area==area->id&&q->state==1&&(q->count||q->actionCount))c->contentNeedsReader++;}
            c->clip=oldClip;c->paintBlend=oldBlend;continue;
        }
        int order=0;
        for(int m=0; m<NR_MESSAGES; m++) {
            const Message*q=&s->messages[m];
            if(!q->used||q->area!=area->id||q->state!=1)continue;
            double age=(s->timeUs-q->startUs)/1e6,alpha=ma;
            if(q->mode==3||q->mode==5||q->mode==6) {
                double fade=area->fadeUs/1e6+.000001;
                alpha*=nrEase(age/fade,3);
                if(q->durationUs)alpha*=nrEase((q->durationUs/1e6-age)/fade,3);
            }
            if(s->reducedMotion)alpha=ma;
            double scrollX=0,scrollY=0;
            int contentLines=lines(q->text,q->count,iw);
            if(q->mode==1||q->mode==5) {
                int64_t period=(int64_t)q->count+iw+4;
                scrollX=age*area->speedX;
                scrollX-=period*nrFloor(scrollX/period);
                if(q->count<=iw)scrollX=0;
            }
            if(q->mode==2||q->mode==6) {
                int64_t period=(int64_t)contentLines+ih+1;
                scrollY=age*area->speedY;
                scrollY-=period*nrFloor(scrollY/period);
            }
            if(s->reducedMotion)scrollX=scrollY=0;
            int64_t col=area->layout==2?q->x:0,row=area->layout==2?q->y:order;
            int overflow=0; /* Unscrolled text outside the content box; marquee motion does not enlarge it. */
            for(int k=0; k<q->count; k++) {
                uint32_t g=q->text[k];
                if(g==10) {
                    row++;
                    col=0;
                    continue;
                }
                if(q->mode!=1&&q->mode!=5&&col>=iw) {
                    row++;
                    col=0;
                }
                if(row>=ih||col>=iw)overflow=1;
                int64_t xx=(int64_t)x+pad+col-(int64_t)scrollX,yy=(int64_t)y+pad+row-(int64_t)scrollY;
                if(xx>=x+pad&&xx<(int64_t)x+w-pad&&yy>=(int64_t)y+pad&&yy<(int64_t)y+h-pad&&xx>=cx&&xx<(int64_t)cx+cw&&yy>=cy&&yy<(int64_t)cy+ch){double glyphAlpha=alpha;uint32_t glyphColor=color;if(sourcePatternEnabled(s,area->material)){double pa=1;glyphColor=sampleCell(s,area->material,s->timeUs,(int)xx,(int)yy,k,&pa);glyphAlpha=(ma>0?alpha/ma:0)*pa;}nrIndexedGlyph(c,(int)xx,(int)yy,g,glyphColor,glyphAlpha,0,(uint32_t)k);}
                col++;
            }
            if(overflow)c->contentNeedsReader++;
            int64_t actionRow=(int64_t)(area->layout==2?q->y:order)+contentLines;int actionCol=0,actionHeight=0;
            for(int a=0;a<q->actionCount;a++) {
                const NotificationAction*n=&q->actions[a];int width=n->labelCount+4;
                if(width>iw)width=iw;
                if(width<3){c->contentNeedsReader++;continue;}
                int height=2+(n->labelCount+width-3)/(width-2);
                if(actionCol&&actionCol+width>iw){actionRow+=actionHeight;actionCol=0;actionHeight=0;}
                if(actionRow+height>ih){c->contentNeedsReader++;continue;}
                int64_t rawY=(int64_t)y+pad+actionRow;
                if(rawY>=s->height||rawY+height<=0)continue;
                int xx=x+pad+actionCol,yy=(int)rawY;
                int enabled=!(q->actionMask&(1u<<a));
                /* A consumed button keeps its hit: the press reaches the idempotent
                 * activation instead of falling through to camera/weather input. */
                uint32_t id=alpha>.01?(NR_ID_NOTIFICATION_ACTION|((uint32_t)q->id<<2)|(uint32_t)a):0;
                if(alpha>.01) {
                    fill(c,xx,yy,width,height,enabled?0x27433d:0x17262b,.78*alpha,id);
                    patternBox(c,xx,yy,width,height,1,area->material,alpha*(enabled?.9:.4),id,a);
                    patternText(c,xx+1,yy+1,n->label,n->labelCount,width-2,area->material,alpha*(enabled?1:.45),id,a);
                }
                actionCol+=width+1;if(height>actionHeight)actionHeight=height;
            }
            order+=(q->actionCount?actionRow+actionHeight-(area->layout==2?q->y:order):contentLines)+area->margin;
        }
        c->clip=oldClip;c->paintBlend=oldBlend;
    }
    for(int i=0; i<NR_INDICATORS; i++) {
        c->characterOwner=previousOwner;
        const Indicator*q=&s->indicators[i];
        if(!q->used||!q->count)continue;
        int x=q->x,y=q->y;
        if(q->area) {
            int64_t row[12];if(!nrResolveArea(s,(uint32_t)q->area,row))continue;
            int64_t absoluteX=(int64_t)x+row[0],absoluteY=(int64_t)y+row[1];
            if(absoluteX<row[4]||absoluteX>=row[4]+row[6]||absoluteY<row[5]||absoluteY>=row[5]+row[7])continue;
            x=(int)absoluteX;y=(int)absoluteY;
        }
        double a;
        uint32_t color=nrPaint(s,q->material,s->timeUs,i,&a);
        c->characterOwner=(6u<<16)|(uint32_t)q->id;
        if(sourcePatternEnabled(s,q->material))color=sampleCell(s,q->material,s->timeUs,x,y,i,&a);
        if(q->cursor)nrCellBackground(c,x,y,color,s->reducedMotion?.5:.4+.3*nrSin(s->timeUs/10000.0));
        else {uint32_t index=s->reducedMotion?0:(s->timeUs/q->stepUs)%q->count;nrIndexedGlyph(c,x,y,q->glyphs[index],color,a,0,index);}
    }
    c->characterOwner=previousOwner;
}
void nrDrawUI(NrContext*c,const Projection*p) {
    const State*s=nrView(c);
    int rows=nrPromptRows(s);
    NrPromptSourceInput framedInput;
    NrPromptSourceLayout framedLayout;
    int framed=s->promptFramed.enabled&&nrPromptFramedLayout(s,&framedInput,&framedLayout)==0;
    c->promptTop=framed?framedLayout.rectY:(int)s->height-rows-2;
    if(c->promptTop<3)c->promptTop=3;
    if(s->canvasPresentation&&!s->promptDocument.active&&!framed)c->promptTop=(int)s->height;
    c->paintBlend=0;if(!s->firstPromptSource.enabled||s->promptSourceLayer.placement)nrPromptAppearanceWeather(c);c->paintBlend=0;
    c->paintBlend=0;nrDrawTextTransitions(c);c->paintBlend=0;
    c->paintBlend=0;drawWidgets(c);c->paintBlend=0;
    c->paintBlend=0;drawGraph(c,p);c->paintBlend=0;
    c->paintBlend=0;drawWindows(c,p);c->paintBlend=0;
    c->paintBlend=0;drawStatus(c);c->paintBlend=0;
    int selected=nrFindWindow(s,s->selectedWindow);
    if(!s->windowApplication.enabled&&selected>=0&&s->windowPresentation[selected].enabled&&!s->windows[selected].reader)
        nrWindowPresentationDrawTheatreToolbar(c,(int)s->width,&s->windowPresentation[selected].options,1,(uint32_t)s->selectedWindow);
    const Prompt*q=&s->promptDocument;
    if(!s->firstPromptSource.enabled&&!s->windowApplication.enabled&&(q->active||framed)) {
        if(framed){nrPromptFramedPaint(c,s);}
        else {
        int (*coordinates)[2]=(int(*)[2])s->dynamicPrompt.scratch;nrPromptCoordinates(s,coordinates);
        int top=c->promptTop;
        if(q->mode>=2) {
            top=q->mode==3?3:top-2;
            int boxh=(int)s->height-top-1;
            fill(c,0,top,s->width,boxh,0x14202a,q->alpha,NR_ID_PROMPT);
            nrBox(c,0,top,s->width,boxh,q->border,0x789b9d,.9,NR_ID_PROMPT);
            ascii(c,2,top+1,q->vimMode?"VIM STYLE / INSERT":"VIM STYLE / NORMAL: i insert, u undo, arrows move",s->width-4,0xc6afc7,1,NR_ID_PROMPT);
        }
        else fill(c,0,top,s->width,rows,0x0b121b,q->alpha,NR_ID_PROMPT);
        double*clusters=(double*)(s->dynamicPrompt.scratch+2*((size_t)s->dynamicPrompt.capacity+1));int clusterCount=s->promptPresentation.layout?nrPromptVisualMap(s,clusters):0;
        if(s->promptPresentation.layout)for(int k=0;k<clusterCount;k++){double*r=clusters+k*10;int a=r[0],b=r[1],w=r[4],x=r[5],y=r[6];if(!r[7])continue;
            for(int j=0;j<w;j++){if(q->anchor>=0&&a<(q->anchor>q->caret?q->anchor:q->caret)&&b>(q->anchor<q->caret?q->anchor:q->caret))nrCellBackground(c,x+j,y,0x43637f,.8);nrIndexedGlyph(c,x+j,y,j||q->glyphs[a]==9?32:(uint32_t)r[9],0xe4dacc,1,NR_ID_PROMPT,(uint32_t)a);}}
        else for(int i=0; i<q->count; i++) {
            if(q->glyphs[i]==10)continue;
            int x=coordinates[i][0],y=coordinates[i][1];
            if(y>=top+(q->mode>=2?2:0)&&y<(int)s->height-2&&x>=2&&x<(int)s->width-1) {
                if(q->anchor>=0&&i>=(q->anchor<q->caret?q->anchor:q->caret)&&i<(q->anchor>q->caret?q->anchor:q->caret))nrCellBackground(c,x,y,0x43637f,.8);
                nrIndexedGlyph(c,x,y,q->glyphs[i]==9?' ':q->glyphs[i],0xe4dacc,1,NR_ID_PROMPT,(uint32_t)i);
            }
        }
        int x=coordinates[q->caret][0],y=coordinates[q->caret][1];
        if(x>=(int)s->width-1)x=s->width-2;
        if(y<(int)s->height-2) {
            if(s->promptAppearance.cursorConfigured)nrPromptAppearanceCursor(c,s,x,y);
            else nrCellBackground(c,x,y,0xaaa0a2,s->reducedMotion?.4:.25+.15*nrSin(s->timeUs/12000.0));
        }
        ascii(c,0,top,">",1,0xbbd7c5,1,NR_ID_PROMPT);
        }
    }
    nrWindowApplicationChrome(c);
    nrPromptAppearanceApplication(c,s);
    if(s->firstPromptSource.enabled)nrFirstPromptPaint(c,s);
    /* Explicit recovery owns the foreground after every decorative/document
     * surface, including a full prompt. Modal help is painted after it. */
    c->paintBlend=0;drawWindowReader(c);c->paintBlend=0;
    if(!s->canvasPresentation&&!s->firstPromptSource.enabled){
    fill(c,0,0,s->width,1,0x0b1118,.9,0);
    ascii(c,1,0,s->width<60?"NOCTURNE | F1 help":"NOCTURNE | F1 Help | F6 Reader",s->width-2,0xbcc3bb,1,0);
    }
    else if(!s->canvasPresentation&&s->promptSourceLayer.placement){
    /* The header bar of the ordinary scene, drawn around the layer: left and right of it on row 0. */
    int lx,ly,lw,lh,placed=nrFirstPromptViewport(s,&lx,&ly,&lw,&lh)&&ly==0;
    int spans[2][2]={{0,placed?lx:(int)s->width},{placed?lx+lw:(int)s->width,(int)s->width}};
    for(int k=0;k<2;k++){if(spans[k][1]<=spans[k][0])continue;ClipRect previous=nrClip(c,spans[k][0],0,spans[k][1]-spans[k][0],1);
    fill(c,0,0,s->width,1,0x0b1118,.9,0);
    ascii(c,1,0,s->width<60?"NOCTURNE | F1 help":"NOCTURNE | F1 Help | F6 Reader",s->width-2,0xbcc3bb,1,0);
    c->clip=previous;}
    }
    nrSourceStageDrawModal(c,s);
    if(s->promptDocument.modal) {
        int w=(int)s->width-2;
        if(w>100)w=100;
        int h=(int)s->height-2;if(h>14)h=14;
        int x=((int)s->width-w)/2,y=((int)s->height-h)/2;
        panel(c,x,y,w,h,0x17242e,1,0x7fffffffu);
        nrBox(c,x,y,w,h,3,0xaebad0,1,0x7fffffffu);
        if(w<62||h<14) {
            static const char*help[]={"HELP","F1 / Esc: close","F6: next reader","PgUp/Dn: scroll","Ctrl-A/E: ends","Drag: camera"};
            for(int row=0;row<6&&row<h-2;row++)ascii(c,x+1,y+1+row,help[row],w-2,0xd5dcd7,1,0x7fffffffu);
        } else {
            ascii(c,x+3,y+2,"CURRENT NATIVE CONTRACTS",w-6,0xd5c4d7,1,0x7fffffffu);
            ascii(c,x+3,y+4,"Drag: look / Shift or right drag: pan / Wheel: dolly",w-6,0xb9d6c8,1,0x7fffffffu);
            ascii(c,x+3,y+6,"F6: reader. PgUp/PgDn: scroll. Escape: close reader/help.",w-6,0xb9d6c8,1,0x7fffffffu);
            ascii(c,x+3,y+8,"Ctrl-A / Ctrl-E: text endpoints. Input remains local.",w-6,0xb9d6c8,1,0x7fffffffu);
            ascii(c,x+3,y+10,"The runtime performs no network, file or subprocess I/O.",w-6,0xcbb89a,1,0x7fffffffu);
        }
    }
}

int nrInputOwner(const State*s) {
    if(s->promptDocument.modal||nrModalBlocking(s))return 1;
    int i=nrFindWindow(s,s->selectedWindow);
    return i>=0&&s->windows[i].reader&&s->windows[i].target?2:0;
}
