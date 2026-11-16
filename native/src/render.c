#include "internal.h"
#include "scenic_native.h"
#include "source_compositor.h"
#include "scenic_native.h"
static void projectionSample(void*user,int32_t x,int32_t y,int32_t depth,uint32_t rgb,int32_t alpha,int32_t threshold){
    (void)user;(void)x;(void)y;(void)depth;(void)rgb;(void)alpha;(void)threshold;
}
void nrProjection(const State*s,int width,int height,Projection*p) {
    Camera cam=nrCameraAt(s);
    p->position=cam.position;
    nrBasis(&cam,&p->right,&p->up,&p->forward);
    p->cx=width;
    p->cy=height*2;
    p->focal=height*2*nrCos(cam.fov*.5)/nrSin(cam.fov*.5);
    if(s->originalCamera.enabled){for(int i=0;i<NR_MAX_NODES;i++)if(s->nodes[i].used){p->focal=width*nrCos(cam.fov*.5)/nrSin(cam.fov*.5);break;}}
    p->nearPlane=cam.nearPlane;
    p->farPlane=cam.farPlane;
    p->orthographic=cam.orthographic;
    p->scale=width*2/cam.span;
    p->sourceEnabled=0;
    if(s->sceneArt.used){
        NrScenicArtConfig config;
        if(nrSceneArtEffective(s,width,height,&config)&&
           nrScenicSourceRasterInit(&p->source,&config,width,height,projectionSample,0)){
            p->sourceEnabled=1;
            /* Source field-of-view is horizontal. Half samples expand 2x2 in
             * the common sample grid; the scene's projection covers that grid. */
            p->focal=p->source.focal/(config.world[NR_WORLD_SAMPLING]?16.0:8.0);
            p->nearPlane=1.5;
        }
    }
}
int nrProject(const Projection*p,Vec3 v,double*x,double*y,double*z) {
    if(p->sourceEnabled){
        double qx=nrFloor(v.x*256+.5),qy=nrFloor(v.y*256+.5),qz=nrFloor(-v.z*256+.5);
        if(!(qx>=INT32_MIN&&qx<=INT32_MAX&&qy>=INT32_MIN&&qy<=INT32_MAX&&qz>=INT32_MIN&&qz<=INT32_MAX))return 0;
        int32_t cx,cy,cz,sx,sy,depth;
        if(!nrScenicSourceRasterProjectPoint(&p->source,(int32_t)qx,(int32_t)qy,(int32_t)qz,&cx,&cy,&cz,&sx,&sy,&depth))return 0;
        *z=cz/256.0;if(*z>p->farPlane)return 0;
        double divisor=p->source.config.world[NR_WORLD_SAMPLING]?16.0:8.0;
        *x=sx/divisor;*y=sy/divisor;return 1;
    }
    Vec3 d=nrSub(v,p->position);
    *z=nrDot(d,p->forward);
    if(*z<p->nearPlane||*z>p->farPlane)return 0;
    double f=p->orthographic?p->scale:p->focal/ *z;
    *x=p->cx+nrDot(d,p->right)*f;
    *y=p->cy-nrDot(d,p->up)*f;
    return 1;
}
void nrPixel(NrContext*c,int x,int y,double depth,uint32_t rgb,double alpha) {
    if(x<0||y<0||x>=c->screenWidth||y>=c->screenHeight||alpha<=0)return;
    if(!nrSourceFragmentVisible(c,x,y,depth))return;
    if(c->paintMaterialId>0&&c->paintMaterialId<=NR_MATERIALS&&nrView(c)->materialPatterns[c->paintMaterialId-1].used){
        double ignoredAlpha;
        int64_t xq=(int64_t)x*128+64,yq=(int64_t)y*64+32;
        rgb=nrPaintAt(nrView(c),c->paintMaterialId-1,nrView(c)->timeUs,
            (int32_t)(xq>INT32_MAX?INT32_MAX:xq),(int32_t)(yq>INT32_MAX?INT32_MAX:yq),0,&ignoredAlpha);
    }
    size_t index=(size_t)y*c->screenWidth+x;
    int count=c->fragmentCounts[index];
    Fragment f= {
        (int32_t)(nrClamp(depth,0,100000)*1024),rgb,(uint16_t)(nrClamp(alpha,0,1)*65535+.5),(uint16_t)c->paintBlend,c->paintOwner,(uint16_t)c->paintDetail,(uint16_t)c->paintSampling
    };
    /* A polyline vertex/shared triangle edge is one sample, not repeated alpha.
       Stable owner+role preserves separate objects and separate surface/detail passes. */
    for(int k=0;k<count;k++) {
        Fragment*old=&c->fragments[index][k];
        if(f.owner&&old->owner==f.owner&&old->detail==f.detail&&old->sampling==f.sampling&&old->rgb==f.rgb&&
           nrAbs((double)old->depth-f.depth)<=2) {
            if(f.alpha>old->alpha)old->alpha=f.alpha;
            /* A duplicate outside the old three slots was formerly dropped
             * on every attempt, even though the six-slot candidate is retained. */
            if(k>=3&&f.alpha)c->legacyFragmentOverflow[index]++;
            return;
        }
    }
    if(!f.alpha)return;
    if(count>=3&&count<NR_LAYERS)c->legacyFragmentOverflow[index]++;
    int pos=0;
    while(pos<count&&c->fragments[index][pos].depth<=f.depth)pos++;
    if(pos>=NR_LAYERS) {
        c->fragmentOverflow++;
        return;
    }
    if(count<NR_LAYERS)c->fragmentCounts[index]++;
    else c->fragmentOverflow++;
    for(int k=(count<NR_LAYERS?count:NR_LAYERS-1); k>pos; k--)c->fragments[index][k]=c->fragments[index][k-1];
    c->fragments[index][pos]=f;
}
static int clipLine(double*x0,double*y0,double*x1,double*y1,int w,int h,double*clipStart,double*clipEnd) {
    double dx=*x1-*x0,dy=*y1-*y0,t0=0,t1=1;
    double p[4]= {
        -dx,dx,-dy,dy
    },q[4]= {
        *x0,w-1-*x0,*y0,h-1-*y0
    };
    for(int i=0; i<4; i++) {
        if(nrAbs(p[i])<1e-12) {
            if(q[i]<0)return 0;
        }
        else {
            double r=q[i]/p[i];
            if(p[i]<0) {
                if(r>t1)return 0;
                if(r>t0)t0=r;
            }
            else {
                if(r<t0)return 0;
                if(r<t1)t1=r;
            }
        }
    }
    double x=*x0,y=*y0;
    *x0=x+dx*t0;
    *y0=y+dy*t0;
    *x1=x+dx*t1;
    *y1=y+dy*t1;
    *clipStart=t0;*clipEnd=t1;
    return 1;
}
void nrLine(NrContext*c,const Projection*p,Vec3 a,Vec3 b,uint32_t color,double alpha) {
    double da=nrDot(nrSub(a,p->position),p->forward),db=nrDot(nrSub(b,p->position),p->forward);
    if((da<p->nearPlane&&db<p->nearPlane)||(da>p->farPlane&&db>p->farPlane))return;
    Vec3 d=nrSub(b,a);
    if(da<p->nearPlane) {
        a=nrAdd(a,nrScale(d,(p->nearPlane-da)/(db-da)));
        da=p->nearPlane;
    }
    else if(db<p->nearPlane) {
        b=nrAdd(a,nrScale(d,(p->nearPlane-da)/(db-da)));
        db=p->nearPlane;
    }
    if(da>p->farPlane) {
        a=nrAdd(a,nrScale(nrSub(b,a),(p->farPlane-da)/(db-da)));
        da=p->farPlane;
    }
    else if(db>p->farPlane) {
        b=nrAdd(a,nrScale(nrSub(b,a),(p->farPlane-da)/(db-da)));
        db=p->farPlane;
    }
    double x0,y0,z0,x1,y1,z1;
    if(!nrProject(p,a,&x0,&y0,&z0)||!nrProject(p,b,&x1,&y1,&z1))return;
    double clipStart,clipEnd;
    if(!clipLine(&x0,&y0,&x1,&y1,c->screenWidth,c->screenHeight,&clipStart,&clipEnd))return;
    double dx=x1-x0,dy=y1-y0;
    int steps=(int)(nrAbs(dx)>nrAbs(dy)?nrAbs(dx):nrAbs(dy))+1;
    for(int i=0; i<=steps; i++) {
        double t=i/(double)steps;
        double u=clipStart+(clipEnd-clipStart)*t;
        double depth=p->orthographic?z0+(z1-z0)*u:1/((1-u)/z0+u/z1);
        nrPixel(c,(int)(x0+dx*t+.5),(int)(y0+dy*t+.5),depth,color,alpha);
    }
}
void nrPoint(NrContext*c,const Projection*p,Vec3 v,uint32_t rgb,double alpha,double size) {
    double x,y,z;
    if(!nrProject(p,v,&x,&y,&z))return;
    double radius=nrClamp(size*(p->orthographic?p->scale:p->focal/z),.45,12);
    int r=(int)radius+1;
    for(int dy=-r; dy<=r; dy++)for(int dx=-r; dx<=r; dx++) {
        double d=nrSqrt(dx*dx+dy*dy);
        if(d<=radius+.5)nrPixel(c,(int)x+dx,(int)y+dy,z,rgb,alpha*nrClamp(radius+.5-d,0,1));
    }
}
static void triangleProjected(NrContext*c,const Projection*p,Vec3 a,Vec3 b,Vec3 d,uint32_t rgb,double alpha) {
    double x[3],y[3],z[3];
    if(!nrProject(p,a,&x[0],&y[0],&z[0])||!nrProject(p,b,&x[1],&y[1],&z[1])||!nrProject(p,d,&x[2],&y[2],&z[2]))return;
    double area=(x[1]-x[0])*(y[2]-y[0])-(y[1]-y[0])*(x[2]-x[0]);
    if(nrAbs(area)<1e-9)return;
    double minx=x[0],maxx=x[0],miny=y[0],maxy=y[0];
    for(int k=1; k<3; k++) {
        if(x[k]<minx)minx=x[k];
        if(x[k]>maxx)maxx=x[k];
        if(y[k]<miny)miny=y[k];
        if(y[k]>maxy)maxy=y[k];
    }
    int ix0=(int)nrClamp(nrFloor(minx),0,c->screenWidth-1),ix1=(int)nrClamp(maxx+1,0,c->screenWidth-1),iy0=(int)nrClamp(nrFloor(miny),0,c->screenHeight-1),iy1=(int)nrClamp(maxy+1,0,c->screenHeight-1);
    for(int yy=iy0; yy<=iy1; yy++)for(int xx=ix0; xx<=ix1; xx++) {
        double px=xx+.5,py=yy+.5;
        double u=((x[1]-px)*(y[2]-py)-(y[1]-py)*(x[2]-px))/area,v=((x[2]-px)*(y[0]-py)-(y[2]-py)*(x[0]-px))/area,w=1-u-v;
        if(u>=0&&v>=0&&w>=0) {
            double depth=p->orthographic?u*z[0]+v*z[1]+w*z[2]:1/(u/z[0]+v/z[1]+w/z[2]);
            nrPixel(c,xx,yy,depth,rgb,alpha);
        }
    }
}
void nrTriangle(NrContext*c,const Projection*p,Triangle t) {
    Vec3 in[8]= {
        t.a,t.b,t.c
    },out[8];
    int n=3;
    for(int plane=0; plane<2; plane++) {
        int count=0;
        double bound=plane?p->farPlane:p->nearPlane+1e-7;
        for(int i=0; i<n; i++) {
            Vec3 a=in[i],b=in[(i+1)%n];
            double da=nrDot(nrSub(a,p->position),p->forward)-bound,db=nrDot(nrSub(b,p->position),p->forward)-bound;
            int ai=plane?da<=0:da>=0,bi=plane?db<=0:db>=0;
            if(ai)out[count++]=a;
            if(ai!=bi)out[count++]=nrAdd(a,nrScale(nrSub(b,a),da/(da-db)));
        }
        n=count;
        if(n<3)return;
        memcpy(in,out,(size_t)n*sizeof(Vec3));
    }
    for(int i=1; i<n-1; i++)triangleProjected(c,p,in[0],in[i],in[i+1],t.color,t.alpha);
}
static uint32_t flattened(const NrCell*cell) {
    if(cell->glyph==0x2588)return cell->foreground;
    if(cell->glyph==0x2580||cell->glyph==0x2584)return nrMix(cell->background,cell->foreground,.5);
    if(cell->glyph>=0x2800&&cell->glyph<=0x28ff) {
        unsigned bits=cell->glyph-0x2800;
        int n=0;
        for(; bits; bits>>=1)n+=bits&1;
        return nrMix(cell->background,cell->foreground,n/8.0);
    }
    return cell->background;
}
int nrInClip(const NrContext*c,int x,int y) {
    return x>=c->clip.x&&y>=c->clip.y&&x<c->clip.x+c->clip.width&&y<c->clip.y+c->clip.height;
}
ClipRect nrClip(NrContext*c,int x,int y,int w,int h) {
    ClipRect old=c->clip;int64_t r=(int64_t)x+w,b=(int64_t)y+h;
    if(x<old.x)x=old.x;if(y<old.y)y=old.y;
    if(r>(int64_t)old.x+old.width)r=(int64_t)old.x+old.width;
    if(b>(int64_t)old.y+old.height)b=(int64_t)old.y+old.height;
    c->clip=(ClipRect){x,y,r>x?(int)(r-x):0,b>y?(int)(b-y):0};return old;
}
void nrUseMaterial(NrContext*c,int material) {
    c->paintBlend=material>=0&&material<NR_MATERIALS&&nrView(c)->materials[material].used?nrView(c)->materials[material].blend:0;
}
static uint32_t composited(uint32_t base,uint32_t source,double alpha,int blend,uint32_t seed) {
    if(!blend)return nrMix(base,source,alpha);
    uint32_t out[2];
    if(nrComposite(base,source,65535,(uint32_t)(nrClamp(alpha,0,1)*65535+.5),(uint32_t)blend,0,seed,out))return base;
    return out[0];
}
static void drawCellArt(NrContext*c,int layer){
    const State*s=nrView(c);
    for(int i=0;i<4;i++)if(s->cellArt[i].used&&s->cellArt[i].layer==layer){
        for(int k=0;k<s->cellArt[i].width*s->cellArt[i].height;k++){
            int64_t wideX=(int64_t)s->cellArt[i].x+k%s->cellArt[i].width,wideY=(int64_t)s->cellArt[i].y+k/s->cellArt[i].width;
            if(wideX<0||wideY<0||wideX>=s->width||wideY>=s->height)continue;
            int x=(int)wideX,y=(int)wideY;
            if(!s->cellArt[i].cells[k][0]||s->cellArt[i].alpha<=0||!nrInClip(c,x,y)||x<0||y<0||x>=(int)s->width||y>=(int)s->height)continue;
            NrCell*cell=&c->cells[y*s->width+x];uint32_t base=flattened(cell),index=(uint32_t)(y*s->width+x);
            cell->background=composited(base,s->cellArt[i].cells[k][2],s->cellArt[i].alpha,0,index);
            cell->foreground=composited(base,s->cellArt[i].cells[k][1],s->cellArt[i].alpha,0,index);
            cell->glyph=s->cellArt[i].cells[k][0]; /* Decorative art keeps underlying hit ownership. */
            c->characterIndices[index]=(uint32_t)k;
            c->characterOwners[index]=0; /* Art is decorative, not the underlying hit target. */
        }
    }
}
void nrCellBackground(NrContext*c,int x,int y,uint32_t color,double alpha) {
    if(!nrInClip(c,x,y))return;
    if(x<0||y<0||x>=(int)nrView(c)->width||y>=(int)nrView(c)->height)return;
    NrCell*p=&c->cells[y*nrView(c)->width+x];
    p->background=composited(p->background,color,alpha,c->paintBlend,(uint32_t)(y*nrView(c)->width+x));
    if(p->glyph==0x2580||p->glyph==0x2584||(p->glyph>=0x2800&&p->glyph<=0x28ff))p->foreground=composited(p->foreground,color,alpha,c->paintBlend,(uint32_t)(y*nrView(c)->width+x));
}
void nrIndexedGlyph(NrContext*c,int x,int y,uint32_t glyph,uint32_t color,double alpha,uint32_t id,uint32_t sourceIndex) {
    if(!nrInClip(c,x,y))return;
    if(x<0||y<0||x>=(int)nrView(c)->width||y>=(int)nrView(c)->height||alpha<=0)return;
    NrCell*p=&c->cells[y*nrView(c)->width+x];
    p->background=flattened(p);
    p->glyph=glyph;
    p->foreground=composited(p->background,color,alpha,c->paintBlend,(uint32_t)(y*nrView(c)->width+x));
    p->id=id;
    c->characterIndices[(size_t)y*nrView(c)->width+x]=sourceIndex;
    uint32_t owner=c->characterOwner;
    if(!owner){
        uint32_t family=id&0xff000000u,target=id&0xffffu;
        if(family==NR_ID_WIDGET)owner=(1u<<16)|target;
        else if(family==NR_ID_WINDOW||family==NR_ID_DOCK||family==NR_ID_CLOSE||family==NR_ID_MIN||family==NR_ID_MAX)owner=(2u<<16)|target;
        else if(family==NR_ID_NODE)owner=(7u<<16)|target;
        else if(family==NR_ID_PROMPT)owner=10u<<16;
    }
    c->characterOwners[(size_t)y*nrView(c)->width+x]=owner;
}
void nrGlyph(NrContext*c,int x,int y,uint32_t glyph,uint32_t color,double alpha,uint32_t id) {
    nrIndexedGlyph(c,x,y,glyph,color,alpha,id,UINT32_MAX);
}
void nrText(NrContext*c,int x,int y,const uint32_t*text,int n,int width,uint32_t color,double alpha,uint32_t id) {
    if(width<1)return;
    int64_t origin=x,cursorX=x,cursorY=y;
    for(int i=0; i<n; i++) {
        uint32_t g=text[i];
        if(g=='\n') {
            cursorX=origin;
            cursorY++;
            continue;
        }
        if(cursorX-origin>=width) {
            cursorX=origin;
            cursorY++;
        }
        if(cursorY>=nrView(c)->height)return;
        if(cursorX>=0&&cursorX<nrView(c)->width&&cursorY>=0)
            nrIndexedGlyph(c,(int)cursorX,(int)cursorY,g=='\t'?' ':g,color,alpha,id,(uint32_t)i);
        cursorX++;
    }
}
void nrBox(NrContext*c,int x,int y,int w,int h,int style,uint32_t color,double alpha,uint32_t id) {
    if(w<1||h<1)return;
    uint32_t left=style==2?0x250c:style==3?0x2554:style==4?0x250f:0x256d,right=style==2?0x2510:style==3?0x2557:style==4?0x2513:0x256e,bl=style==2?0x2514:style==3?0x255a:style==4?0x2517:0x2570,br=style==2?0x2518:style==3?0x255d:style==4?0x251b:0x256f,horiz=style==3?0x2550:style==4?0x2501:0x2500,vert=style==3?0x2551:style==4?0x2503:0x2502;
    if(!style)return;
    int64_t rightEdge=(int64_t)x+w-1,bottomEdge=(int64_t)y+h-1;
    int64_t xmin=c->clip.x,ymin=c->clip.y;
    int64_t xmax=xmin+c->clip.width,ymax=ymin+c->clip.height;
    if(xmin<0)xmin=0;if(ymin<0)ymin=0;
    if(xmax>nrView(c)->width)xmax=nrView(c)->width;
    if(ymax>nrView(c)->height)ymax=nrView(c)->height;
    int64_t first=(int64_t)x+1;if(first<xmin)first=xmin;
    int64_t last=rightEdge;if(last>xmax)last=xmax;
    for(int64_t xx=first;xx<last;xx++){
        if(y>=ymin&&y<ymax)nrGlyph(c,(int)xx,y,horiz,color,alpha,id);
        if(h>1&&bottomEdge>=ymin&&bottomEdge<ymax)nrGlyph(c,(int)xx,(int)bottomEdge,horiz,color,alpha,id);
    }
    first=(int64_t)y+1;if(first<ymin)first=ymin;
    last=bottomEdge;if(last>ymax)last=ymax;
    for(int64_t yy=first;yy<last;yy++){
        if(x>=xmin&&x<xmax)nrGlyph(c,x,(int)yy,vert,color,alpha,id);
        if(w>1&&rightEdge>=xmin&&rightEdge<xmax)nrGlyph(c,(int)rightEdge,(int)yy,vert,color,alpha,id);
    }
    if(x>=xmin&&x<xmax&&y>=ymin&&y<ymax)nrGlyph(c,x,y,left,color,alpha,id);
    if(w>1&&rightEdge>=xmin&&rightEdge<xmax&&y>=ymin&&y<ymax)nrGlyph(c,(int)rightEdge,y,right,color,alpha,id);
    if(h>1&&bottomEdge>=ymin&&bottomEdge<ymax){
        if(x>=xmin&&x<xmax)nrGlyph(c,x,(int)bottomEdge,bl,color,alpha,id);
        if(w>1&&rightEdge>=xmin&&rightEdge<xmax)nrGlyph(c,(int)rightEdge,(int)bottomEdge,br,color,alpha,id);
    }
}
static void background(NrContext*c) {
    const State*s=nrView(c);
    uint32_t palette[256];
    double t=s->timeUs/1e6;
    for(int i=0; i<256; i++) {
        uint32_t col=nrOklch((int32_t)((.32+.13*nrSin(i*360.0/256))*1e6),50000,(int32_t)((220+i*1.1+t*4)*1000));
        palette[i]=nrMix(s->background,col,.42);
    }
    for(int y=0; y<c->screenHeight; y++)for(int x=0; x<c->screenWidth; x++) {
        double p=0;
        switch(s->style) {
            case 1:p=x*.004+t*.055;
            break;
            case 2:p=.25*(nrSin(x*.9+t*24)+nrSin(y*1.7-t*18)+nrSin((x+y)*.55+t*11)+nrSin(nrSqrt((x-180.0)*(x-180)+(y-80.0)*(y-80))*1.4-t*14));
            break;
            case 3:p=nrSin(x*.8+t*19)+nrSin(y*1.5+x*.5-t*11);
            break;
            case 4:p=nrSin(x*2+t*12)*nrSin(y*2.6-t*14)+nrSin((x+y)*1.7);
            break;
            case 5:p=nrSqrt((double)x*x+(double)y*y)*.02+t*.06;
            break;
            default:break;
        }
        int ix=(int)(p*63+128);
        ix=((ix%256)+256)%256;
        c->backgroundPixels[(size_t)y*c->screenWidth+x]=s->style?palette[ix]:s->background;
    }
    if(s->sceneArt.used){int width,height;nrSceneViewport(s,&width,&height);nrSceneArtDrawSource(c,NULL,s,width,height,0);}
    if(s->sourceModel.view.used){int width,height;nrSceneViewport(s,&width,&height);nrSourceModelDraw(c,s,width,height);}
    for(int k=0; k<NR_FIELDS; k++) {
        const Field*f=&s->fields[k];
        if(!nrFieldLive(s,k))continue;
        const FieldControls*q=&s->fieldControls[k];
        if(NR_FIELD_SOURCE_PAINT(q))continue;
        double age=(s->timeUs-f->atUs)/1e6;
        double radius=q->continuous?0:age*f->speed*2,band=f->width*2,extent=radius+band*6;
        double cx,cy;nrFieldCenter(s,k,&cx,&cy);cx*=2;cy*=4;
        int x0=(int)nrClamp(cx-extent,0,c->screenWidth),x1=(int)nrClamp(cx+extent+1,0,c->screenWidth),y0=(int)nrClamp(cy-extent,0,c->screenHeight),y1=(int)nrClamp(cy+extent+1,0,c->screenHeight);
#ifndef NR_REFERENCE_FIELDS
        /* The field is radial. Sample its transfer curve once, instead of doing
         * chroma gamut mapping independently for every covered pixel. A separate
         * exact-equation test build measures the resulting quantization error. */
        enum { FIELD_SAMPLES=256 };
        uint32_t ramp[FIELD_SAMPLES+1];
        double strength[FIELD_SAMPLES+1];
        double start=radius-band*5;
        if(start<0)start=0;
        double range=radius+band*5-start;
        for(int j=0;j<=FIELD_SAMPLES;j++) {
            double dist=start+range*j/FIELD_SAMPLES;
            nrFieldCurve(s,k,dist,&ramp[j],&strength[j]);
        }
#endif
        for(int y=y0; y<y1; y++)for(int x=x0; x<x1; x++) {
            double dist=nrSqrt((x-cx)*(x-cx)+(y-cy)*(y-cy)),d=dist-radius;
            if((!NR_FIELD_OPTICS(q)&&!NR_FIELD_RINGS(q)&&nrAbs(d)>band*5)||!nrFieldContains(s,k,x/2.0,y/4.0))continue;
#ifdef NR_REFERENCE_FIELDS
            double intensity;uint32_t color;nrFieldCurve(s,k,dist,&color,&intensity);
#else
            double intensity;uint32_t color;
            if(NR_FIELD_RINGS(q)||NR_FIELD_OPTICS(q))nrFieldCurve(s,k,dist,&color,&intensity);else {
            double position=nrClamp((dist-start)*FIELD_SAMPLES/range,0,FIELD_SAMPLES-0.000001);
            int j=(int)position;double fraction=position-j;
            color=nrMix(ramp[j],ramp[j+1],fraction);
            intensity=strength[j]+(strength[j+1]-strength[j])*fraction;}
#endif
            if(q->materialAuthored&&f->material>=0&&f->material<NR_MATERIALS&&s->materialPatterns[f->material].used){
                int64_t xq=(int64_t)x*128,yq=(int64_t)y*64;
                nrFieldCurveAt(s,k,dist,(int32_t)(xq>INT32_MAX?INT32_MAX:xq),
                    (int32_t)(yq>INT32_MAX?INT32_MAX:yq),&color,&intensity);
            }
            if(NR_FIELD_OPTICS(q)==3&&!nrSourceFieldHit(s,k,x/2.0,y/4.0))continue;
            size_t i=(size_t)y*c->screenWidth+x;
            c->backgroundPixels[i]=nrMix(c->backgroundPixels[i],color,intensity);
        }
    }
}
static void stars(NrContext*c,const Projection*p) {
    const State*s=nrView(c);
    if(!s->stars||s->sourceSky.enabled)return;
    double side=50,far=s->starFar;
    int radius=(int)(far/side)+1;
    if(radius>8)radius=8;
    int cx=(int)nrFloor(p->position.x/side),cy=(int)nrFloor(p->position.y/side),cz=(int)nrFloor(p->position.z/side);
    int per=1+s->stars/125;
    int considered=0;
    for(int z=cz-radius; z<=cz+radius; z++)for(int y=cy-radius; y<=cy+radius; y++)for(int x=cx-radius; x<=cx+radius; x++) {
        uint32_t seed=nrHash(s->seed^(uint32_t)x*0x9e3779b9u^(uint32_t)y*0x85ebca6bu^(uint32_t)z*0xc2b2ae35u);
        for(int k=0; k<per; k++) {
            if(++considered>100000)return;
            Vec3 v=nrV((x+nrRandom(seed,k,1))*side,(y+nrRandom(seed,k,2))*side,(z+nrRandom(seed,k,3))*side);
            Vec3 d=nrSub(v,p->position);
            double distance=nrSqrt(nrDot(d,d));
            if(distance>far||distance<.4)continue;
            double exposure=nrClamp(1/(.65+distance*distance/1800),.12,1);
            exposure*=nrEase((far-distance)/(far*.2),3)*nrEase((distance-.4)/1.5,3);
            double twinkle=.83+.17*nrSin(s->timeUs/1e6*40+nrRandom(seed,k,4)*360);
            uint32_t color=nrOklch((int32_t)((.73+nrRandom(seed,k,5)*.16)*1e6),20000,(int32_t)((40+nrRandom(seed,k,6)*270)*1000));
            double px,py,depth;
            if(nrProject(p,v,&px,&py,&depth)) {
                nrPixel(c,(int)px,(int)py,depth,color,exposure*twinkle);
                if(exposure>.7)nrPixel(c,(int)px+1,(int)py,depth,color,exposure*.2);
            }
        }
    }
}
/* Select the nearest visible detail owner before encoding the cell. Lower
 * surfaces retain their color and occlusion but cannot fill a leaf's dot mask.
 * A terminal cell has one glyph: other owners are retained in its flattened matte.
 */
void nrResolveLayerCell(NrContext*c,unsigned x,unsigned y,NrCell*out) {
    /* Retain candidates until all geometry has arrived: an eventual braille
     * blade needs its floor/vein context. Other samples keep the historical
     * first three fragments and exact overflow/duplicate accounting. */
    for(int k=0;k<8;k++) {
        size_t index=(size_t)(y*4+k/2)*c->screenWidth+x*2+k%2;
        int count=c->fragmentCounts[index],blade=0;
        for(int j=0;j<count;j++)if(c->fragments[index][j].detail==2&&c->fragments[index][j].sampling==2){blade=1;break;}
        if(!blade){
            c->fragmentOverflow+=c->legacyFragmentOverflow[index];
            if(count>3)c->fragmentCounts[index]=3;
        }
        c->legacyFragmentOverflow[index]=0;
    }
    static const unsigned dots[8]={1,8,2,16,4,32,64,128};
    uint32_t owner=0,pixels[8],base[8];int32_t nearest=2147483647;
    if((nrView(c)->windowApplication.enabled&&!c->sourceActive)||nrView(c)->sourceSky.enabled){
        int fragments=0;for(int k=0;k<8;k++)fragments+=c->fragmentCounts[(size_t)(y*4+k/2)*c->screenWidth+x*2+k%2];
        if(!fragments){*out=c->cells[(size_t)y*nrView(c)->width+x];return;}
    }
    int sourceCell=c->sourceActive&&x<(unsigned)c->sourceWidth&&y<(unsigned)c->sourceHeight;
    if(sourceCell){
        int fragments=0;int32_t depths[8];
        for(int k=0;k<8;k++){
            size_t index=(size_t)(y*4+k/2)*c->screenWidth+x*2+k%2;
            pixels[k]=c->backgroundPixels[index];depths[k]=c->sourceDepth[index];
            fragments+=c->fragmentCounts[index];
        }
        if(!fragments){
            nrResolveSourceSamples(out,pixels,depths,c->sourceBackground,c->sourceSampling);
            size_t at=(size_t)y*nrView(c)->width+x;
            c->characterIndices[at]=UINT32_MAX;c->characterOwners[at]=0;
            return;
        }
    }
    int chosenDetail=-1,sampling=nrView(c)->sampling;
    /* The floor grid is background detail. It must not take a foreground
     * object's mask merely because another dot of the sloping floor is nearer
     * within the same cell. Per-sample transmission still enforces occlusion. */
    for(int d=2;d>=0&&chosenDetail<0;d--)for(int k=0;k<8;k++) {
        size_t index=(size_t)(y*4+k/2)*c->screenWidth+x*2+k%2;
        double transmission=1;
        for(int j=0;j<c->fragmentCounts[index];j++) {
            const Fragment*f=&c->fragments[index][j];
            int priority=f->detail?((f->owner==1&&f->sampling==2)?1:2):0;
            if(f->alpha&&transmission>1e-9&&priority==d&&f->owner&&
               (f->depth<nearest||(f->depth==nearest&&f->owner<owner))) {
                owner=f->owner;nearest=f->depth;sampling=f->sampling;chosenDetail=f->detail;
            }
            transmission*=1-f->alpha/65535.0;
        }
    }
    /* Role 2 is a braille blade. Its depth competes with other detail owners,
     * but its own outline/veins still supply the fine mask when present. Both
     * roles belong to one foreground object: neither may paint its dot gaps. */
    int brailleBlade=0,hasOutline=0;
    if(sampling==2&&owner)for(int k=0;k<8;k++) {
        size_t index=(size_t)(y*4+k/2)*c->screenWidth+x*2+k%2;
        double transmission=1;
        for(int j=0;j<c->fragmentCounts[index];j++) {
            const Fragment*f=&c->fragments[index][j];
            if(f->owner==owner&&f->detail==2)brailleBlade=1;
            if(f->owner==owner&&f->detail==1&&f->alpha&&transmission>1e-9)hasOutline=1;
            transmission*=1-f->alpha/65535.0;
        }
    }
    if(brailleBlade&&hasOutline)chosenDetail=1;
    /* Environment occlusion controls. An occluder is another braille-family particle (owner > 1) behind the
     * braille owner of this cell. occludedDots "merge" lets an occluder's fragments of the chosen detail add
     * their dots to the mask instead of tinting the background. occlusionTint < 1 also composites the scene
     * without occluders (sceneP, sceneB) and blends each sub-sample background from that scene (0) towards
     * the full tint (1). At the defaults (hidden, 1) this is exactly the earlier resolve. */
    const State*view=nrView(c);
    const int mergeDots=view->occlusionControls.occludedDots==1u;
    const double tint=NR_OCCLUSION_TINT(view);
    const int behind=tint<1;
#define OCCLUDER(f) (sampling==2&&(f)->sampling==2&&(f)->owner>1&&(f)->owner!=owner)
#define MERGED(f) (mergeDots&&OCCLUDER(f))
    uint32_t sceneP[8],sceneB[8];
    unsigned coverage=0;
    for(int k=0;k<8;k++) {
        size_t index=(size_t)(y*4+k/2)*c->screenWidth+x*2+k%2;
        pixels[k]=base[k]=sceneP[k]=sceneB[k]=c->backgroundPixels[index];
        for(int j=c->fragmentCounts[index]-1;j>=0;j--) {
            const Fragment*f=&c->fragments[index][j];
            pixels[k]=composited(pixels[k],f->rgb,f->alpha/65535.0,f->blend,index);
            if(behind&&!OCCLUDER(f))sceneP[k]=composited(sceneP[k],f->rgb,f->alpha/65535.0,f->blend,index);
            if((f->owner!=owner&&!(MERGED(f)&&f->detail==chosenDetail))||(f->owner==owner&&!brailleBlade&&f->detail!=chosenDetail)) {
                base[k]=composited(base[k],f->rgb,f->alpha/65535.0,f->blend,index);
                if(behind&&!OCCLUDER(f))sceneB[k]=composited(sceneB[k],f->rgb,f->alpha/65535.0,f->blend,index);
            }
        }
        double transmission=1;
        for(int j=0;j<c->fragmentCounts[index];j++) {
            const Fragment*f=&c->fragments[index][j];
            if((f->owner==owner||MERGED(f))&&f->detail==chosenDetail&&f->alpha&&transmission>1e-9)
                coverage|=dots[k];
            transmission*=1-f->alpha/65535.0;
        }
        /* A braille blade's unmarked dot gaps retain the underlying scene too. */
        if(!(coverage&dots[k])&&!brailleBlade){base[k]=pixels[k];sceneB[k]=sceneP[k];}
        if(behind){
            uint32_t a=sceneB[k],b=base[k],m=0;
            for(int s=0;s<24;s+=8){double v=((a>>s)&255)*(1-tint)+((b>>s)&255)*tint;m|=(uint32_t)(v+.5)<<s;}
            base[k]=m;
        }
    }
#undef MERGED
#undef OCCLUDER
    nrResolveSamples(out,pixels,base,coverage,sampling);
    size_t at=(size_t)y*nrView(c)->width+x;
    c->characterIndices[at]=UINT32_MAX;
    c->characterOwners[at]=nrCharacterFragmentOwner(nrView(c),owner);
}
void nrRenderAll(NrContext*c) {
    const State*s=nrView(c);
    c->paintBlend=0;
    c->paintMaterialId=0;c->sourceActive=0;
    c->clip=(ClipRect){0,0,(int)s->width,(int)s->height};
    c->screenWidth=s->width*2;
    c->screenHeight=s->height*4;
    memset(c->characterIndices,0xff,(size_t)s->width*s->height*sizeof(uint32_t));
    memset(c->characterOwners,0,(size_t)s->width*s->height*sizeof(uint32_t));
    c->characterOwner=0;
    memset(c->fragmentCounts,0,(size_t)c->screenWidth*c->screenHeight);
    memset(c->legacyFragmentOverflow,0,(size_t)c->screenWidth*c->screenHeight*sizeof(uint32_t));
    background(c);
    nrWindowApplicationBackground(c);
    nrDrawSourceSky(c);
    Projection p;
    int sceneW,availableH;nrSceneViewport(s,&sceneW,&availableH);
    nrProjection(s,sceneW,availableH,&p);
    c->paintOwner=0x10000000u;c->paintDetail=1;c->paintSampling=2;
    stars(c,&p);
    /* A hybrid floor and mesh are block objects: exactly their half encoding. */
    const int floorSampling=nrDictatedSampling(s->floor.sampling,1);
    c->paintOwner=1;c->paintDetail=0;c->paintSampling=floorSampling;
    if(s->floor.visible) {
        double h=s->floor.height;
        uint32_t color=0x547b77;
        /* In braille mode grid lines own their subcell detail; the filled
         * floor remains a matte and must not saturate the grid's dot mask. */
        c->paintDetail=floorSampling==2;
        for(int i=-10; i<=10; i++) {
            nrLine(c,&p,nrV(i*5,h,-50),nrV(i*5,h,50),color,s->floor.alpha);
            nrLine(c,&p,nrV(-50,h,i*5),nrV(50,h,i*5),color,s->floor.alpha);
        }
        c->paintDetail=0;
        nrTriangle(c,&p,(Triangle) {
            nrV(-50,h, -50),nrV(50,h,-50),nrV(50,h,50),0x374238,s->floor.alpha*.18
        });
        nrTriangle(c,&p,(Triangle) {
            nrV(-50,h,-50),nrV(50,h,50),nrV(-50,h,50),0x374238,s->floor.alpha*.18
        });
    }
    c->paintOwner=2;c->paintDetail=0;c->paintSampling=nrDictatedSampling(s->meshSampling,1);
    double flowAlpha[NR_SURFACES],wetness[NR_SURFACES]={0};nrFlowSurfaceAlpha(s,flowAlpha);
    for(int i=0;i<NR_SURFACES;i++)if(s->flowSinks[i].flowId){double sink[4];nrFlowSinkVolumes(s,i,sink);wetness[i]=sink[3];}
    for(int i=0;i<s->meshCount;i++) {
        Triangle triangle;int id=s->geometry.triangleSurfaces[i];
        c->paintOwner=id?0x40000000u|(uint32_t)id:2;
        if(nrSurfaceTriangle(s,i,&triangle)){if(id){triangle.alpha*=flowAlpha[id-1];double cell[3];nrSurfaceWaterCell(s,i,cell);double localWetness=wetness[id-1]>cell[2]?wetness[id-1]:cell[2];double shade=1-.35*localWetness;uint32_t rgb=triangle.color;triangle.color=((uint32_t)(((rgb>>16)&255)*shade)<<16)|((uint32_t)(((rgb>>8)&255)*shade)<<8)|(uint32_t)((rgb&255)*shade);}triangle.color=nrThermalPaint(s,i,triangle.color);nrTriangle(c,&p,triangle);}
    }
    nrDrawFloatBodies(c,&p);
    nrDrawWeather(c,&p);c->paintBlend=0;
    nrDrawElectricalArcs(c,&p);c->paintBlend=0;
    nrDrawSceneGeometry(c,&p);c->paintBlend=0;
    for(unsigned y=0;y<s->height;y++)for(unsigned x=0;x<s->width;x++)
        nrResolveLayerCell(c,x,y,&c->cells[y*s->width+x]);
    nrDrawOriginalFields(c);
    nrDrawCorona(c,&p);
    nrDrawObservatory(c,&p);
    nrDrawKinetic(c,&p);
    nrDrawAtelier(c,&p);
    nrDrawThermalSource(c,&p);
    nrDrawWorldSource(c,&p);
    nrDrawStudioNova(c,&p);
    drawCellArt(c,0);
    nrSourceStageDraw(c,s);
    nrDrawUI(c,&p);
    drawCellArt(c,1);
}
