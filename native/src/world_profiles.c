#include "internal.h"
#include "window_palette_source.h"
#include "window_source_math.h"
static int reject(NrContext*c,const char*message){size_t n=strlen(message);if(n>255)n=255;memcpy(c->error,message,n);c->error[n]=0;return -1;}
int nrWorldSourceProfile(const State*s,int slot){
    if(slot<0||slot>=(int)NR_MAX_EMITTERS||!s->emitters[slot].used)return -1;
    const char*names[]={"weather/starburst","weather/forked-voltage","weather/solar-cinders","weather/leaf-ribbon","weather/storm-volume","weather/snowfall-volume","weather/ejecta-shell","weather/pressure-shell"};
    for(int i=0;i<8;i++)if(!strcmp(nrEffectName(s->emitters[slot].effect),names[i]))return i;return -1;
}
static int valid(const WorldSourceControls*b){return (b->used==1||b->used==2)&&b->count>=1&&b->count<=1200&&b->scale>=.001&&b->scale<=1000&&b->gravity>=0&&b->gravity<=100&&b->lifeMs>=200&&b->lifeMs<=10000;}
int nrValidWorldSourceControls(const State*s){
    for(int slot=0;slot<(int)NR_MAX_EMITTERS;slot++){
        const WorldSourceControls*b=&s->worldSourceControls[slot];
        if(!b->used){const unsigned char*p=(const unsigned char*)b;for(size_t i=0;i<sizeof(*b);i++)if(p[i])return 0;continue;}
        if(s->schema<NR_STATE_SCHEMA_WORLD_PROFILES||(b->used==2&&s->schema<NR_STATE_SCHEMA_WORLD_PAINT)||nrWorldSourceProfile(s,slot)<0||!valid(b)||b->generation!=s->emitters[slot].generation||b->startUs>s->timeUs)return 0;
    }return 1;
}
int nrWorldSourceCommand(NrContext*c,State*s,const Json*j){
    if(s->schema<NR_STATE_SCHEMA_WORLD_PROFILES)return reject(c,"World source requires schema62");
    int removal=nrEqual(j,nrField(j,0,"op"),"remove-world-style");double id;
    if(!nrAllowed(j,0,removal?"op id":"op id seed count scale lifeMs gravity paint"))return reject(c,"Unknown world source setting");
    if(!nrNumber(j,nrField(j,0,"id"),&id)||id<1||id>65535||id!=(uint32_t)id)return reject(c,"World source emitter id required");
    int slot=nrFindEmitter(s,(int)id);if(nrWorldSourceProfile(s,slot)<0)return reject(c,"World source requires supported world emitter");
    if(removal){memset(&s->worldSourceControls[slot],0,sizeof(WorldSourceControls));return 0;}
    WorldSourceControls b=s->worldSourceControls[slot];if(!b.used)b=(WorldSourceControls){.used=2,.generation=s->emitters[slot].generation,.seed=2030,.count=64,.scale=1,.lifeMs=5000,.gravity=2.6,.startUs=s->timeUs};
    int mode=nrField(j,0,"paint");if(mode>=0){if(nrEqual(j,mode,"source"))b.used=2;else if(nrEqual(j,mode,"material"))b.used=1;else return reject(c,"Invalid world painting mode");}
    if(b.used==2&&s->schema<NR_STATE_SCHEMA_WORLD_PAINT)return reject(c,"World painting requires schema81");
    int at=nrField(j,0,"seed");double value;
    if(at>=0){if(!nrNumber(j,at,&value)||value<0||value>4294967295.0||value!=(uint32_t)value)return reject(c,"World seed requires uint32");b.seed=(uint32_t)value;}
    at=nrField(j,0,"lifeMs");if(at>=0){if(!nrNumber(j,at,&value)||value<200||value>10000)return reject(c,"World lifeMs out of range");b.lifeMs=value;}
    at=nrField(j,0,"count");if(at>=0){if(!nrNumber(j,at,&value)||value<1||value>1200||value!=(uint32_t)value)return reject(c,"World count requires integer1..1200");b.count=(uint32_t)value;}
    at=nrField(j,0,"scale");if(at>=0){if(!nrNumber(j,at,&value)||value<.001||value>1000)return reject(c,"World scale out of range");b.scale=value;}
    at=nrField(j,0,"gravity");if(at>=0){if(!nrNumber(j,at,&value)||value<0||value>100)return reject(c,"World gravity out of range");b.gravity=value;}
    if(!valid(&b))return reject(c,"Invalid world source controls");s->worldSourceControls[slot]=b;return 0;
}
static double seededUnit(uint32_t seed,uint32_t index){return nrHash(seed^((index+1u)*2654435761u))/4294967296.0;}
static double soft(double x){x=nrClamp(x,0,1);return x*x*(3-2*x);}
static double sine(double x,int source){return source?nrWindowSourceSin(x):nrSin(x*180/NR_PI);}
static double cosine(double x,int source){return source?nrWindowSourceCos(x):nrCos(x*180/NR_PI);}
static Vec3 ballistic(double theta,double lat,double rr,double speed,double gravity,double t,int source){return nrV(cosine(theta,source)*rr*speed*t,lat*speed*t-gravity*t*t*.5,sine(theta,source)*rr*speed*t);}
static Vec3 rising(double a,double b,double r,double scale,double gravity,double t,int source){return nrV((a-.5)*scale*4*t+sine(t*2+b*20,source)*scale*.4,scale*(3+5*b)*t-gravity*t*t*.5,(r-.5)*scale*4*t);}
static Vec3 branchPoint(double angle,uint32_t branch,double scale,double age,double v,int source){return nrV(cosine(angle,source)*scale*18*v+sine(v*45+branch*3+nrFloor(age*16),source)*scale*.5,sine(angle,source)*scale*18*v+sine(v*63+branch*5,source)*scale*.6,sine(branch*7,source)*v*scale*7);}
int nrWorldSourceSample(const State*s,int slot,WorldSourceSample*out){
    int kind=nrWorldSourceProfile(s,slot);if(!out||kind<0||!s->worldSourceControls[slot].used)return 0;
    const WorldSourceControls*b=&s->worldSourceControls[slot];if(b->generation!=s->emitters[slot].generation)return 0;
    memset(out,0,sizeof(*out));if(kind==7&&b->used==2)return 1;double ageMs=(double)(s->timeUs-b->startUs)/1000;if(ageMs>=b->lifeMs)return 1;
    int source=b->used==2;double age=ageMs/1000,life=b->lifeMs/1000,fade=soft((1-age/life)*2),rise=soft(age/.12);
    for(uint32_t i=0;i<b->count;i++){
        double a=seededUnit(b->seed,i*4),v=seededUnit(b->seed,i*4+1),r=seededUnit(b->seed,i*4+2),wave=sine(age*(9+12*a)+v*60,source),flicker=.7+.3*wave*wave;
        double alpha=fade*rise,hue;uint32_t glyph;Vec3 p,previous=nrV(0,0,0);int trail=0;
        if(kind==6){
            double latitude=1-2*(i+.5)/b->count,ring=nrSqrt(1-latitude*latitude),angle=i*2.399963229728653+b->seed*.0001;
            double radius=b->scale*(1+age*4.2)*(1+.13*sine(angle*3+latitude*8+b->seed,source)),clumpWave=sine(angle*2+latitude*9+b->seed,source);
            p=nrV(cosine(angle,source)*ring*radius,latitude*radius,sine(angle,source)*ring*radius);
            alpha*=.3+.7*clumpWave*clumpWave;hue=25+260*age/life+60*a;glyph=0xb7;
        }else if(kind==0){
            double theta=a*2*NR_PI,lat=v*2-1,rr=nrSqrt(1-lat*lat),speed=b->scale*(4+r*12);
            p=ballistic(theta,lat,rr,speed,b->gravity,age,source);previous=ballistic(theta,lat,rr,speed,b->gravity,age>.045?age-.045:0,source);trail=1;hue=a*360;alpha*=flicker;glyph=0x2219;
        }else if(kind==2||kind==3){
            p=rising(a,v,r,b->scale,b->gravity,age,source);previous=rising(a,v,r,b->scale,b->gravity,age>.06?age-.06:0,source);trail=1;alpha*=flicker;
            hue=kind==3?35+v*95:15+v*60;glyph=kind==3?(sine(age*4+a*50,source)>0?0x2312:0x223c):0x2219;
        }else if(kind==1){
            uint32_t branches=b->count/14;if(branches<3)branches=3;uint32_t branch=i%branches,seg=i/branches,steps=(b->count+branches-1)/branches;
            double t=(double)seg/steps,angle=seededUnit(b->seed,branch+800)*2*NR_PI;
            p=branchPoint(angle,branch,b->scale,age,t,source);previous=branchPoint(angle,branch,b->scale,age,t>.1?t-.1:0,source);trail=1;
            hue=205+v*100;double strike=life<.85?life:.85;alpha*=nrClamp(1-age/strike,0,1)*flicker;glyph=seg%3==0?0x22c6:0xb7;
        }else{
            p=nrV((a-.5)*50*b->scale,(v-.5)*30*b->scale-age*(kind==4?17:4),(r-.5)*30*b->scale);alpha*=flicker;
            hue=kind==4?205:240;glyph=kind==4?0x2571:0xb7;if(kind==5)p.x+=sine(age*1.6+v*22,source)*3;
        }
        double*point=out->points[out->pointCount++];point[0]=p.x;point[1]=p.y;point[2]=p.z;point[3]=glyph;point[4]=alpha;point[5]=hue;
        if(trail){double*segment=out->segments[out->segmentCount++];segment[0]=previous.x;segment[1]=previous.y;segment[2]=previous.z;segment[3]=p.x;segment[4]=p.y;segment[5]=p.z;segment[6]=alpha;segment[7]=hue;}
    }return 1;
}

static uint32_t mix(uint32_t a,uint32_t b,double t){
 t=nrClamp(t,0,1);uint32_t out=0;
 for(int shift=0;shift<=16;shift+=8){double aa=(a>>shift)&255,bb=(b>>shift)&255;out|=(uint32_t)nrFloor(aa*(1-t)+bb*t+.5)<<shift;}return out;
}
static uint32_t flattened(const uint32_t*c){return c[0]==0x2580||c[0]==0x2584||c[0]==0x258c||c[0]==0x2590?mix(c[1],c[2],.5):c[2];}
typedef struct {uint32_t width,height,*cells;const uint32_t*wheel;} Painter;
static uint32_t ink(const Painter*p,double hue){int h=(int)nrFloor(hue+.5)%360;if(h<0)h+=360;return p->wheel[h];}
static void cell(Painter*p,double x,double y,uint32_t glyph,uint32_t fg,double a){
 x=nrFloor(x);y=nrFloor(y);if(x<0||y<0||x>=p->width||y>=p->height)return;
 uint32_t*c=p->cells+4*((size_t)y*p->width+(size_t)x),bg=flattened(c);c[0]=glyph;c[1]=mix(bg,fg,a);c[2]=bg;c[3]=0;
}
static void dot(Painter*p,double x,double y,uint32_t color,double a){
 static const uint32_t bits[8]={1,8,2,16,4,32,64,128};x=nrFloor(x+.5);y=nrFloor(y+.5);
 if(x<0||y<0||x>=p->width*2.0||y>=p->height*4.0)return;
 uint64_t px=(uint64_t)x,py=(uint64_t)y;uint32_t*c=p->cells+4*((size_t)(py/4)*p->width+(size_t)(px/2));
 if(c[0]<0x2800||c[0]>0x28ff){c[2]=flattened(c);c[0]=0x2800;}
 c[0]|=bits[(py%4)*2+px%2];c[1]=mix(c[2],color,a);
}
static void line(Painter*p,double x0,double y0,double x1,double y1,uint32_t color,double a){
 x0*=2;x1*=2;y0*=4;y1*=4;double dx=x1-x0,dy=y1-y0,lo=0,hi=1;
 double ps[4]={-dx,dx,-dy,dy},qs[4]={x0,p->width*2.0-1-x0,y0,p->height*4.0-1-y0};
 for(int i=0;i<4;i++){double pp=ps[i],q=qs[i];if(!pp&&q<0)return;if(!pp)continue;double v=q/pp;if(pp<0){if(v>lo)lo=v;}else if(v<hi)hi=v;if(lo>hi)return;}
 double ax=nrFloor(x0+lo*dx+.5),ay=nrFloor(y0+lo*dy+.5),bx=nrFloor(x0+hi*dx+.5),by=nrFloor(y0+hi*dy+.5);
 double n=nrAbs(bx-ax);if(n<nrAbs(by-ay))n=nrAbs(by-ay);if(n<1)n=1;
 for(uint64_t j=0;j<=(uint64_t)n;j++)dot(p,ax+(bx-ax)*j/n,ay+(by-ay)*j/n,color,a);
}

void nrWorldOriginalProjection(const State*s,const Projection*in,Projection*out){
    *out=*in;if(out->sourceEnabled)return;Camera camera=nrCameraAt(s);
    double yaw=camera.yaw*NR_PI/180,pitch=camera.pitch*NR_PI/180,roll=camera.roll*NR_PI/180;
    double cy=nrWindowSourceCos(yaw),sy=nrWindowSourceSin(yaw),cp=nrWindowSourceCos(pitch),sp=nrWindowSourceSin(pitch),cr=nrWindowSourceCos(roll),sr=nrWindowSourceSin(roll);
    Vec3 a=nrV(cy,0,sy),b=nrV(-sy*sp,cp,cy*sp);
    out->right=nrAdd(nrScale(a,cr),nrScale(b,sr));out->up=nrAdd(nrScale(b,cr),nrScale(a,-sr));out->forward=nrV(sy*cp,sp,-cy*cp);
    out->focal=out->cy*nrWindowSourceCos(camera.fov*NR_PI/360)/nrWindowSourceSin(camera.fov*NR_PI/360);
}
static int originalPoint(const Projection*p,Vec3 origin,const double*r,double out[3]){
    if(!nrProject(p,nrV(origin.x+r[0],origin.y+r[1],origin.z-r[2]),&out[0],&out[1],&out[2]))return 0;
    out[0]*=.5;out[1]*=.25;return 1;
}
static Vec3 rotatePlane(Vec3 v,Vec3 a){
    if(!a.x&&!a.y&&!a.z)return v;
    double c=nrWindowSourceCos(a.x*NR_PI/180),s=nrWindowSourceSin(a.x*NR_PI/180);v=nrV(v.x,c*v.y-s*v.z,s*v.y+c*v.z);
    c=nrWindowSourceCos(a.y*NR_PI/180);s=nrWindowSourceSin(a.y*NR_PI/180);v=nrV(c*v.x+s*v.z,v.y,-s*v.x+c*v.z);
    c=nrWindowSourceCos(a.z*NR_PI/180);s=nrWindowSourceSin(a.z*NR_PI/180);return nrV(c*v.x-s*v.y,s*v.x+c*v.y,v.z);
}
static void originalRipple(NrContext*c,const State*s,int slot,const Projection*p,double weight){
    const WorldSourceControls*w=&s->worldSourceControls[slot];double elapsed=(double)(s->timeUs-w->startUs)/1000;if(elapsed>=w->lifeMs||weight<=0)return;
    /* Actual RC2 rich world ripple: a Studio integer tile on the authored,
     * immutable plane. Event identity selects palette phase, not weather seed. */
    StudioNovaControls b={.seed=s->emitters[slot].id,.novaDurationMs=(uint32_t)w->lifeMs,.rippleSpeed=2048,.rippleWidth=384,.rippleOpacity=600,.rippleRings=4,.cellAspect=2000,.strength=1000,.waveScale=6144,.paletteCount=5,.palette={0x28304f,0x785c89,0x367876,0xae7357,0x504565}};
    Vec3 right=rotatePlane(nrV(1,0,0),s->birthOrientations[slot]),up=rotatePlane(nrV(0,1,0),s->birthOrientations[slot]),origin=s->emitters[slot].position;
    Painter painter={s->width,s->height,(uint32_t*)c->cells,0};
    for(int y=0;y<44;y++)for(int x=0;x<80;x++){
        NrCell source;nrStudioOriginalRippleTileCell(&b,(uint64_t)elapsed,x,y,&source);
        if(!source.background&&(source.glyph==32||!source.foreground))continue;
        Vec3 v=nrAdd(origin,nrScale(nrAdd(nrScale(right,x-40),nrScale(up,-(y-22)*2)),w->scale));double xx,yy,z;
        if(!nrProject(p,v,&xx,&yy,&z))continue;xx=nrFloor(xx*.5+.5);yy=nrFloor(yy*.25+.5);
        if(xx<0||yy<0||xx>=s->width||yy>=s->height)continue;
        uint32_t*d=(uint32_t*)&c->cells[(size_t)yy*s->width+(size_t)xx];
        if(source.background)d[2]=mix(flattened(d),source.background,.7*weight);
        if(source.glyph!=32&&source.foreground)cell(&painter,xx,yy,source.glyph,source.foreground,.95*weight);
    }
}
static void originalPaint(NrContext*c,const State*s,int slot,const Projection*projection,const WorldSourceSample*sample,double weight){
    if(weight<=0)return;if(nrWorldSourceProfile(s,slot)==7){originalRipple(c,s,slot,projection,weight);return;}
    uint32_t wheel[360];for(int h=0;h<360;h++)if(nrWindowPaletteSourceTextInk(.83,.1,h,&wheel[h]))return;
    Painter p={s->width,s->height,(uint32_t*)c->cells,wheel};Vec3 origin=s->emitters[slot].position;
    /* The original paints each current-to-previous trail immediately before its
     * point. Grouping every trail ahead of every point changes overlap art. */
    for(uint32_t i=0;i<sample->pointCount;i++){
        const double*r=sample->points[i];double q[3];if(!originalPoint(projection,origin,r,q))continue;uint32_t color=ink(&p,r[5]);
        if(i<sample->segmentCount){double previous[3];if(originalPoint(projection,origin,sample->segments[i],previous))line(&p,q[0],q[1],previous[0],previous[1],color,r[4]*.65*weight);}
        cell(&p,q[0],q[1],(uint32_t)r[3],color,r[4]*.9*weight);
    }
}

void nrDrawWorldSource(NrContext*c,const Projection*p){
    const State*s=nrView(c);Projection original;nrWorldOriginalProjection(s,p,&original);
    for(int slot=0;slot<(int)NR_MAX_EMITTERS;slot++){
        if(!s->worldSourceControls[slot].used)continue;WorldSourceSample sample;if(!nrWorldSourceSample(s,slot,&sample))continue;
        const Emitter*e=&s->emitters[slot];nrUseMaterial(c,e->material);c->characterOwner=0;double materialAlpha;
        uint32_t material=nrPaint(s,e->material,s->timeUs,(uint32_t)e->id,&materialAlpha);double alpha=e->alpha*materialAlpha;
        if(s->worldSourceControls[slot].used==2){originalPaint(c,s,slot,&original,&sample,alpha);continue;}
        for(uint32_t i=0;i<sample.segmentCount;i++){const double*r=sample.segments[i];double projected[6];
            if(nrThermalSourceProjectSegment(p,e->position,r,projected))nrSourceScreenSegment(c,projected,nrSourcePrimitiveColor(material,r[7]),alpha*r[6],e->material,i);}
        for(uint32_t i=0;i<sample.pointCount;i++){const double*r=sample.points[i];Vec3 v=nrAdd(e->position,nrV(r[0],r[1],r[2]));double x,y,z;
            if(!nrProject(p,v,&x,&y,&z))continue;x=nrFloor(x*.5);y=nrFloor(y*.25);
            if(x>=0&&y>=0&&x<s->width&&y<s->height){uint32_t ink=nrSourcePrimitiveColor(material,r[5]);if(e->material>=0&&e->material<NR_MATERIALS&&s->materialPatterns[e->material].used){double ignored;ink=nrPaintAt(s,e->material,s->timeUs,(int32_t)x*256,(int32_t)y*256,i,&ignored);}nrIndexedGlyph(c,(int)x,(int)y,(uint32_t)r[3],ink,alpha*r[4],0,i);}
        }
    }c->paintBlend=0;
}
