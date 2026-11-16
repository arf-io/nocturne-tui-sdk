#include "internal.h"
#include "window_texture_source.h"
#include "window_source_math.h"
#include "original_math.h"

static int fail(NrContext*c,const char*message){
    size_t length=strlen(message);if(length>=sizeof(c->error))length=sizeof(c->error)-1;
    memcpy(c->error,message,length);c->error[length]=0;return -1;
}
static int integer(const Json*j,const char*name,uint32_t*out,uint32_t maximum){
    int token=nrField(j,0,name);double value;
    if(token<0)return 1;
    if(!nrNumber(j,token,&value)||value<0||value>maximum||value!=(uint32_t)value)return 0;
    *out=(uint32_t)value;return 1;
}
static void resizeTexture(WindowTextures*t,int slot,uint32_t width,uint32_t height){
    WindowTextureRecord*r=&t->windows[slot];
    uint32_t old=r->width*r->height,count=width*height;
    uint32_t at=old?r->offset:t->count,suffix=t->count-at-old;
    if(suffix)memmove(t->cells+at+count,t->cells+at+old,(size_t)suffix*sizeof(t->cells[0]));
    for(int i=0;i<(int)NR_MAX_WINDOWS;i++)if(i!=slot&&t->windows[i].width&&t->windows[i].offset>at)
        t->windows[i].offset=t->windows[i].offset-old+count;
    t->count=t->count-old+count;
    if(count){
        *r=(WindowTextureRecord){width,height,at,0};
        memset(t->cells+at,0,(size_t)count*sizeof(t->cells[0]));
        for(uint32_t i=0;i<count;i++)t->cells[at+i][0]=32;
    }else memset(r,0,sizeof(*r));
    if(count<old)memset(t->cells+t->count,0,(size_t)(old-count)*sizeof(t->cells[0]));
}
int nrWindowTextureCommand(NrContext*c,State*s,const Json*j){
    if(s->schema<NR_STATE_SCHEMA_WINDOW_TEXTURE)return fail(c,"Window textures require schema68");
    uint32_t id=0;if(!integer(j,"id",&id,65535)||!id)return fail(c,"Window texture id required");
    int slot=nrFindWindow(s,(int)id);if(slot<0)return fail(c,"Window texture requires an existing window");
    if(nrEqual(j,nrField(j,0,"op"),"remove-window-texture")){
        if(!nrAllowed(j,0,"op id"))return fail(c,"Unknown remove-window-texture field");
        if(s->windowTextures.windows[slot].width)resizeTexture(&s->windowTextures,slot,0,0);
        return 0;
    }
    if(s->windowContent[slot].enabled)return fail(c,"Remove generated window content before attaching raw texture");
    if(!nrAllowed(j,0,"op id width height offset cells"))return fail(c,"Unknown window texture field");
    if(s->windows[slot].shape>9)return fail(c,"Window texture requires an source shape");
    WindowTextureRecord*r=&s->windowTextures.windows[slot];
    uint32_t width=r->width,height=r->height,offset=0;
    if((nrField(j,0,"width")>=0)!=(nrField(j,0,"height")>=0))return fail(c,"Texture width and height must be supplied together");
    if(!integer(j,"width",&width,NR_WINDOW_TEXTURE_CELLS)||!integer(j,"height",&height,NR_WINDOW_TEXTURE_CELLS)||
       !width||!height||(uint64_t)width*height>NR_WINDOW_TEXTURE_CELLS||
       !integer(j,"offset",&offset,NR_WINDOW_TEXTURE_CELLS))return fail(c,"Invalid window texture dimensions or offset");
    uint32_t count=width*height,old=r->width*r->height;
    if(s->windowTextures.count-old+count>NR_WINDOW_TEXTURE_CELLS)return fail(c,"Window texture resource capacity");
    if(offset>count)return fail(c,"Window texture offset outside cells");
    int cells=nrField(j,0,"cells");
    if(cells>=0){
        if(j->tokens[cells].type!=J_ARRAY||(uint32_t)j->tokens[cells].count>count-offset)
            return fail(c,"Window texture patch outside cells");
        /* Validate the complete patch before resizing or touching the pool. The
         * command transaction additionally protects other commands in a batch. */
        for(int row=cells+1;row<j->tokens[cells].next;row=j->tokens[row].next){
            if(j->tokens[row].type!=J_ARRAY||j->tokens[row].count!=3)return fail(c,"Texture cells require three words");
            int token=row+1;
            for(int word=0;word<3;word++){
                double value;if(!nrNumber(j,token,&value)||value<0||value>(word?0xffffff:0x10ffff)||value!=(uint32_t)value)
                    return fail(c,"Invalid window texture cell word");
                if(!word&&(value<32||(value>=0xd800&&value<=0xdfff)))return fail(c,"Texture glyph must be a printable Unicode scalar");
                token=j->tokens[token].next;
            }
        }
    }
    if(width!=r->width||height!=r->height)resizeTexture(&s->windowTextures,slot,width,height);
    if(cells>=0){
        uint32_t index=r->offset+offset;
        for(int row=cells+1;row<j->tokens[cells].next;row=j->tokens[row].next,index++){
            int token=row+1;
            for(int word=0;word<3;word++){double value;nrNumber(j,token,&value);s->windowTextures.cells[index][word]=(uint32_t)value;token=j->tokens[token].next;}
        }
    }
    return 0;
}
int nrValidWindowTextures(const State*s){
    const WindowTextures*t=&s->windowTextures;
    if(t->reserved||t->count>NR_WINDOW_TEXTURE_CELLS)return 0;
    uint32_t total=0;
    for(int i=0;i<(int)NR_MAX_WINDOWS;i++){
        const WindowTextureRecord*r=&t->windows[i];
        if(r->reserved)return 0;
        if(!r->width){if(r->height||r->offset)return 0;continue;}
        uint64_t count=(uint64_t)r->width*r->height;
        if(s->schema<NR_STATE_SCHEMA_WINDOW_TEXTURE||!s->windows[i].used||s->windows[i].shape>9||!r->height||
           count>NR_WINDOW_TEXTURE_CELLS||(uint64_t)r->offset+count>t->count)return 0;
        for(int k=0;k<i;k++){
            const WindowTextureRecord*q=&t->windows[k];
            if(q->width&&r->offset<q->offset+q->width*q->height&&q->offset<r->offset+count)return 0;
        }
        total+=(uint32_t)count;
    }
    if(total!=t->count)return 0;
    for(uint32_t i=0;i<t->count;i++){
        const uint32_t*q=t->cells[i];
        if(q[0]<32||q[0]>0x10ffff||(q[0]>=0xd800&&q[0]<=0xdfff)||q[1]>0xffffff||q[2]>0xffffff||q[3])return 0;
    }
    return 1;
}

/* FOV is in (0,180), so the half-angle stays in (0,pi/2). The
 * ordinary scene's interpolated sine table changes source blend rounding. */
static double sourceTan(double radians){
    double square=radians*radians,sine=radians,cosine=1,st=radians,ct=1;
    for(int i=1;i<=10;i++){
        st*=-square/((2*i)*(2*i+1));sine+=st;
        ct*=-square/((2*i-1)*(2*i));cosine+=ct;
    }
    return sine/cosine;
}
/* RC2 uses horizontal field of view and terminal cell aspect two. The
 * canonical camera basis is the source basis reflected only across world Z. */
static void sourceBasis(const Camera*c,Vec3*r,Vec3*u,Vec3*f,int exact){
    double (*sinFn)(double)=exact?nrOriginalSin:nrWindowSourceSin;double (*cosFn)(double)=exact?nrOriginalCos:nrWindowSourceCos;
    double rad=NR_PI/180,yaw=exact?c->yaw*NR_PI/180:c->yaw*rad,pitch=exact?c->pitch*NR_PI/180:c->pitch*rad,roll=exact?c->roll*NR_PI/180:c->roll*rad;
    double cy=cosFn(yaw),sy=sinFn(yaw),cp=cosFn(pitch),sp=sinFn(pitch),cr=cosFn(roll),sr=sinFn(roll);
    *f=nrV(sy*cp,sp,-cy*cp);
    Vec3 a=nrV(cy,0,sy),b=nrV(-sy*sp,cp,cy*sp);
    *r=nrAdd(nrScale(a,cr),nrScale(b,sr));
    *u=nrAdd(nrScale(b,cr),nrScale(a,-sr));
}
int nrWindowSourceProject(const State*s,const Camera*camera,Vec3 point,
                         double*x,double*y,double*z){
    Vec3 r,u,f;sourceBasis(camera,&r,&u,&f,s->originalCamera.enabled);Vec3 d=nrSub(point,camera->position);
    *z=nrDot(d,f);if(*z<camera->nearPlane||*z>camera->farPlane)return 0;
    double radians=camera->fov*NR_PI/180/2;double focal=s->width/(2*(s->originalCamera.enabled?nrOriginalTan(radians):sourceTan(radians)));
    *x=s->width/2.0+nrDot(d,r)*focal/ *z;
    *y=s->height/2.0-nrDot(d,u)*focal/(*z*2);return 1;
}
static int vertex(const State*s,int slot,const Window*w,const Projection*p,const Camera*camera,
                  double u,double v,double visibility,NrWindowTextureVertex*out){
    double alpha,x,y,z;int generated=s->windowContent[slot].enabled;
    Vec3 local=(generated||s->windowSourceGeometry[slot])?nrWindowSourcePoint(w,u,v,visibility,&alpha):nrWindowPoint(w,u,v,visibility,&alpha);
    Vec3 world;
    if(generated){
        double (*sinFn)(double)=s->originalCamera.enabled?nrOriginalSin:nrWindowSourceSin;double (*cosFn)(double)=s->originalCamera.enabled?nrOriginalCos:nrWindowSourceCos;
        double rad=NR_PI/180,yaw=s->originalCamera.enabled?w->yaw*NR_PI/180:w->yaw*rad,pitch=s->originalCamera.enabled?w->pitch*NR_PI/180:w->pitch*rad,roll=s->originalCamera.enabled?w->roll*NR_PI/180:w->roll*rad;
        double cy=cosFn(yaw),sy=sinFn(yaw),cp=cosFn(pitch),sp=sinFn(pitch),cr=cosFn(roll),sr=sinFn(roll);
        double a=local.x*cy+local.z*sy,b=-local.x*sy+local.z*cy,c=local.y*cp-b*sp;
        world=nrAdd(w->position,nrV(a*cr-c*sr,a*sr+c*cr,-(local.y*sp+b*cp)));
        if(!nrWindowSourceProject(s,camera,world,&x,&y,&z))return 0;
    }else{
        Camera orientation={.yaw=w->yaw,.pitch=w->pitch,.roll=w->roll};
        Vec3 right,up,forward;nrBasis(&orientation,&right,&up,&forward);
        world=nrAdd(w->position,nrAdd(nrScale(right,local.x),nrAdd(nrScale(up,local.y),nrScale(forward,-local.z))));
        if(!nrProject(p,world,&x,&y,&z))return 0;x/=2;y/=4;
    }
    *out=(NrWindowTextureVertex){x,y,z,u,v,alpha*nrWindowOpacity(s,slot)};return 1;
}
int nrDrawWindowTexture(NrContext*c,const Projection*p,int slot){
    if(nrView(c)->atelierWindows[slot].enabled)return nrDrawAtelierWindow(c,slot);
    const State*s=nrView(c);const Window*w=&s->windows[slot];
    const WindowTextureRecord*r=&s->windowTextures.windows[slot];
    int generated=s->windowContent[slot].enabled;
    if(!r->width&&!generated)return 0;
    Window posed;Camera camera=nrCameraAt(s);
    uint32_t textureWidth=r->width,textureHeight=r->height;
    const uint32_t*texture=&s->windowTextures.cells[r->offset][0];
    double visibility=generated?nrWindowContentVisibility(s,slot):s->reducedMotion?w->target:nrWindowVisibility(w,s->timeUs);
    if(visibility<.001)return 1;
    if(generated){
        posed=*w;posed.effect=s->windowContent[slot].transitionEffect;
        double t=nrWindowContentMaximized(s,slot);
        if(t>0){
            Vec3 right,up,forward;sourceBasis(&camera,&right,&up,&forward,s->originalCamera.enabled);
            double radians=camera.fov*NR_PI/360;double width=2*34*(s->originalCamera.enabled?nrOriginalTan(radians):sourceTan(radians))*.9;
            double height=width*((double)s->height-17)*2/s->width;
            Vec3 target=nrAdd(camera.position,nrScale(forward,34));
            posed.position=nrAdd(nrScale(w->position,1-t),nrScale(target,t));
            posed.width=w->width*(1-t)+width*t;posed.height=w->height*(1-t)+height*t;
            posed.yaw=w->yaw*(1-t);posed.pitch=w->pitch*(1-t);posed.roll=w->roll*(1-t);
        }
        w=&posed;
        double x0=0,y0=0,x1=60,y1=23,z;
        Vec3 low=nrAdd(w->position,nrV(-w->width/2,-w->height/2,0));
        Vec3 high=nrAdd(w->position,nrV(w->width/2,w->height/2,0));
        double x,y;
        if(nrWindowSourceProject(s,&camera,low,&x,&y,&z)){x0=x;y0=y;}
        if(nrWindowSourceProject(s,&camera,high,&x,&y,&z)){x1=x;y1=y;}
        textureWidth=(uint32_t)nrClamp(nrFloor(nrAbs(x1-x0)+.5),24,100);
        textureHeight=(uint32_t)nrClamp(nrFloor(nrAbs(y1-y0)+.5),12,40);
        if(!nrWindowContentTexture(c,slot,textureWidth,textureHeight,&texture))return 1;
    }else if(w->maximized){
        posed=*w;double depth=34,scale=p->orthographic?p->scale:p->focal/depth;
        posed.position=nrAdd(p->position,nrScale(p->forward,depth));
        posed.yaw=camera.yaw;posed.pitch=camera.pitch;posed.roll=camera.roll;
        posed.width=(s->width>4?s->width-4:1)*2/scale;
        posed.height=(c->promptTop>4?c->promptTop-4:1)*4/scale;w=&posed;
    }
    int columns=w->meshColumns,rows=w->meshRows;
    int source=generated||s->windowSourceGeometry[slot];
    int explosion=source&&nrEffectProfile(w->effect)==0&&nrEffectAlgorithm(w->effect)==15;
    if(source){columns=explosion?6:8;rows=explosion?4:(w->folds*2>12?w->folds*2:12);}
    uint32_t id=NR_ID_WINDOW|(uint32_t)w->id;
    int x0=c->clip.x<0?0:c->clip.x,y0=c->clip.y<0?0:c->clip.y;
    int64_t right=(int64_t)c->clip.x+c->clip.width,bottom=(int64_t)c->clip.y+c->clip.height;
    uint32_t x1=right<s->width?(uint32_t)(right<0?0:right):s->width;
    uint32_t y1=bottom<s->height?(uint32_t)(bottom<0?0:bottom):s->height;
    if(generated){if(y0<9)y0=9;uint32_t limit=s->height>11?s->height-11:0;if(y1>limit)y1=limit;}
    if(x0>=(int)x1||y0>=(int)y1)return 1;
    for(int row=0;row<rows;row++)for(int col=0;col<columns;col++){
        double epsilon=explosion?1e-6:0,u=col/(double)columns,v=row/(double)rows;
        double u2=(col+1)/(double)columns-epsilon,v2=(row+1)/(double)rows-epsilon;
        NrWindowTextureVertex a,b,d,e;
        if(!vertex(s,slot,w,p,&camera,u,v,visibility,&a)||!vertex(s,slot,w,p,&camera,u2,v,visibility,&b)||
           !vertex(s,slot,w,p,&camera,u2,v2,visibility,&d)||!vertex(s,slot,w,p,&camera,u,v2,visibility,&e))continue;
        NrWindowTextureVertex triangles[2][3]={{a,b,d},{a,d,e}};
        uint32_t iris=nrEffectProfile(w->effect)==0&&nrEffectAlgorithm(w->effect)==14;
        for(int t=0;t<2;t++)nrWindowTextureTriangle(triangles[t],(uint32_t)w->shape,iris,visibility,id,
            textureWidth,textureHeight,texture,s->width,s->height,
            (uint32_t)x0,(uint32_t)y0,x1,y1,(uint32_t*)c->cells,c->windowDepth);
    }
    for(size_t cell=0;cell<(size_t)s->width*s->height;cell++)if(c->cells[cell].id==id){
        c->characterIndices[cell]=UINT32_MAX;c->characterOwners[cell]=0;
    }
    return 1;
}
