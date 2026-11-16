#include "internal.h"
#include "source_weather.h"
#include "window_palette_source.h"
static int reject(NrContext*c,const char*message){size_t n=strlen(message);if(n>255)n=255;memcpy(c->error,message,n);c->error[n]=0;return -1;}
static int number(const Json*j,const char*key,double*out,double lo,double hi){int t=nrField(j,0,key);if(t<0)return 1;double v;if(!nrNumber(j,t,&v)||!(v>=lo&&v<=hi))return 0;*out=v;return 1;}
static int integer(const Json*j,const char*key,uint32_t*out,uint32_t lo,uint32_t hi){double v=*out;if(!number(j,key,&v,lo,hi)||v!=(uint32_t)v)return 0;*out=(uint32_t)v;return 1;}
int nrKineticProfile(const State*s,int slot){
    if(slot<0||slot>=(int)NR_MAX_EMITTERS||!s->emitters[slot].used)return -1;
    const char*names[]={"weather/hearth-spray","weather/branchlight","weather/chrysanthemum","weather/wire-rain","weather/pearl-flurry"};
    for(int i=0;i<5;i++)if(!strcmp(nrEffectName(s->emitters[slot].effect),names[i]))return i;return -1;
}
static KineticControls defaults(const State*s,int slot){
    KineticControls b={.used=1,.generation=s->emitters[slot].generation,.seed=2030,.eventId=(uint32_t)s->emitters[slot].id,.count=52,.branches=5,.arcSegments=10,.glyphCount=8,
        .lifeMs=5000,.launchSpeed=12,.gravity=8,.drag=.65,.wind=1.2,.flickerHz=18,.trailMs=90,.arcJitter=1.2,.coreMs=260,.shockwave=0,.explosionForce=48,.brightness=.85,.emberSpread=5,.arcReach=17,.startUs=s->timeUs,
        .glyphs={0xb7,0x2219,0x22c5,'*','+',0x2801,0x2802,0x2804}};return b;
}
static int valid(const KineticControls*b){
    if(b->used!=1||b->count<1||b->count>160||b->branches<1||b->branches>12||b->arcSegments<3||b->arcSegments>24||b->glyphCount<1||b->glyphCount>64)return 0;
#define RANGE(field,lo,hi) if(!(b->field>=lo&&b->field<=hi))return 0
    RANGE(lifeMs,100,12000);RANGE(launchSpeed,0,40);RANGE(gravity,0,40);RANGE(drag,0,5);RANGE(wind,-20,20);
    RANGE(flickerHz,0,60);RANGE(trailMs,0,400);RANGE(arcJitter,0,6);RANGE(coreMs,0,1500);RANGE(shockwave,0,1);
    RANGE(explosionForce,1,70);RANGE(brightness,0,1);RANGE(emberSpread,0,20);RANGE(arcReach,1,45);
#undef RANGE
    for(uint32_t i=0;i<64;i++){uint32_t g=b->glyphs[i];if(i>=b->glyphCount){if(g)return 0;}else if(g<32||(g>=127&&g<=159)||(g>=0xd800&&g<=0xdfff)||g>0x10ffff)return 0;}
    return 1;
}
int nrValidKineticControls(const State*s){
    for(int slot=0;slot<(int)NR_MAX_EMITTERS;slot++){
        const KineticControls*b=&s->kineticControls[slot];
        if(s->kineticPaint[slot]>1||(!b->used&&s->kineticPaint[slot])||(s->schema<NR_STATE_SCHEMA_KINETIC_PAINT&&s->kineticPaint[slot]))return 0;
        if(!b->used){const unsigned char*p=(const unsigned char*)b;for(size_t i=0;i<sizeof(*b);i++)if(p[i])return 0;continue;}
        if(s->schema<NR_STATE_SCHEMA_KINETIC||nrKineticProfile(s,slot)<0||!valid(b)||b->generation!=s->emitters[slot].generation||b->startUs>s->timeUs)return 0;
    }return 1;
}
int nrKineticStyleCommand(NrContext*c,State*s,const Json*j){
    if(s->schema<NR_STATE_SCHEMA_KINETIC)return reject(c,"Kinetic style requires schema59");
    int removal=nrEqual(j,nrField(j,0,"op"),"remove-kinetic-style");
    if(!nrAllowed(j,0,removal?"op id":"op id count lifeMs launchSpeed gravity drag wind flickerHz trailMs branches arcSegments arcJitter coreMs shockwave explosionForce seed eventId brightness glyphs emberSpread arcReach paint"))return reject(c,"Unknown Kinetic setting");
    uint32_t id=0;if(nrField(j,0,"id")<0||!integer(j,"id",&id,1,65535))return reject(c,"Kinetic emitter id required");
    int slot=nrFindEmitter(s,(int)id);if(nrKineticProfile(s,slot)<0)return reject(c,"Kinetic style requires source weather emitter");
    if(removal){memset(&s->kineticControls[slot],0,sizeof(KineticControls));s->kineticPaint[slot]=0;return 0;}
    if(s->coronaControls[slot].used||s->observatoryControls[slot].used)return reject(c,"Source appearance already owned");
    KineticControls b=s->kineticControls[slot].used?s->kineticControls[slot]:defaults(s,slot);
    uint32_t paint=s->kineticControls[slot].used?s->kineticPaint[slot]:1;
    int paintToken=nrField(j,0,"paint");if(paintToken>=0){if(nrEqual(j,paintToken,"source"))paint=1;else if(nrEqual(j,paintToken,"material"))paint=0;else return reject(c,"Invalid Kinetic painting mode");}
    if(!integer(j,"count",&b.count,1,160)||!integer(j,"branches",&b.branches,1,12)||!integer(j,"arcSegments",&b.arcSegments,3,24)||!integer(j,"seed",&b.seed,0,0xffffffffu)||!integer(j,"eventId",&b.eventId,0,0xffffffffu))return reject(c,"Invalid Kinetic integer");
#define FIELD(name,lo,hi) if(!number(j,#name,&b.name,lo,hi))return reject(c,"Invalid Kinetic setting")
    FIELD(lifeMs,100,12000);FIELD(launchSpeed,0,40);FIELD(gravity,0,40);FIELD(drag,0,5);FIELD(wind,-20,20);
    FIELD(flickerHz,0,60);FIELD(trailMs,0,400);FIELD(arcJitter,0,6);FIELD(coreMs,0,1500);FIELD(shockwave,0,1);
    FIELD(explosionForce,1,70);FIELD(brightness,0,1);FIELD(emberSpread,0,20);FIELD(arcReach,1,45);
#undef FIELD
    int glyphs=nrField(j,0,"glyphs");if(glyphs>=0){memset(b.glyphs,0,sizeof(b.glyphs));int count=nrDecode(j,glyphs,b.glyphs,64);if(count<1)return reject(c,"Kinetic printable glyphs required");b.glyphCount=(uint32_t)count;}
    if(!valid(&b))return reject(c,"Invalid Kinetic controls");s->kineticControls[slot]=b;s->kineticPaint[slot]=paint;return 0;
}
static double decay(double x){
    if(x>745)return 0;int squares=0;while(x>.125){x*=.5;squares++;}
    double result=1,term=1;for(int i=1;i<=20;i++){term*= -x/i;result+=term;}
    for(int i=0;i<squares;i++)result*=result;return result;
}
static double power065(double x){
    if(x<=0)return 0;if(x>=1)return 1;
    /* Reduce ln(x) using powers of two, then the atanh series; no host libm. */
    int exponent=0;while(x<.75){x*=2;exponent--;}
    double z=(x-1)/(x+1),square=z*z,term=z,sum=z;
    for(int i=3;i<=39;i+=2){term*=square;sum+=term/i;}
    return decay(-.65*(2*sum+exponent*.6931471805599453094));
}
static double randomAt(uint32_t seed,uint32_t index,uint32_t salt){
    return nrHash((seed^(salt*2246822519u))^((index+1u)*2654435769u))/4294967296.0;
}
static void point(KineticSample*out,double x,double y,double alpha,double heat,uint32_t glyph,double size){
    if(out->pointCount>=160)return;double*r=out->points[out->pointCount++];
    r[0]=x;r[1]=y;r[2]=nrClamp(alpha,0,1);r[3]=heat;r[4]=glyph;r[5]=size;
}
static void segment(KineticSample*out,double x,double y,double xx,double yy,double alpha,double heat,uint32_t branch){
    if(out->segmentCount>=512)return;double*r=out->segments[out->segmentCount++];
    r[0]=x;r[1]=y;r[2]=xx;r[3]=yy;r[4]=nrClamp(alpha,0,1);r[5]=heat;r[6]=branch;
}
static double integral(double drag,double seconds){return drag?(1-decay(drag*seconds))/drag:seconds;}
static void ember(const KineticControls*b,uint32_t seed,uint32_t index,double age,double out[5]){
    double t=nrClamp(age,0,1e12)/1000,vy=b->launchSpeed*(.72+.55*randomAt(seed,index,11));
    double vx=(randomAt(seed,index,12)-.5)*b->emberSpread;
    out[0]=vx*integral(b->drag,t)+b->wind*t+.4*nrSin((t*3+randomAt(seed,index,13)*6)*180/NR_PI)*t;
    out[1]=-vy*t+.5*b->gravity*t*t;
    double life=b->lifeMs*(.9+.1*randomAt(seed,index,14)),fade=nrClamp(1-age/life,0,1);
    double flicker=.35+.65*randomAt(seed,index,(uint32_t)nrFloor(age*b->flickerHz/1000)+201);
    out[2]=power065(fade)*flicker*b->brightness;out[3]=.1+.4*fade;
    out[4]=b->glyphs[(uint32_t)nrFloor(randomAt(seed,index,16)*b->glyphCount)];
}
int nrKineticSample(const State*s,int slot,KineticSample*out){
    int kind=nrKineticProfile(s,slot);if(!out||kind<0||!s->kineticControls[slot].used)return 0;
    const KineticControls*b=&s->kineticControls[slot];if(b->generation!=s->emitters[slot].generation)return 0;
    memset(out,0,sizeof(*out));double age=(double)(s->timeUs-b->startUs)/1000;
    if(age>=b->lifeMs)return 1;
    double t=age/1000,remaining=1-age/b->lifeMs,fade=remaining*nrSqrt(remaining);
    uint32_t seed=b->seed^(b->eventId*2654435761u);
    if(kind==0){
        for(uint32_t i=0;i<b->count;i++){
            double a=age-randomAt(seed,i,9)*180;if(a<0)continue;double p[5];ember(b,seed,i,a,p);
            point(out,p[0],p[1],p[2],p[3],(uint32_t)p[4],1);
            if(b->trailMs&&p[2]>.02){double previous[5];ember(b,seed,i,nrClamp(a-b->trailMs,0,1e12),previous);segment(out,previous[0],previous[1],p[0],p[1],p[2]*.25,p[3],0);}
        }
    }else if(kind==1){
        double envelope=decay(age/(b->lifeMs*.22>100?b->lifeMs*.22:100));
        uint32_t phase=(uint32_t)nrFloor(age*(b->flickerHz>1?b->flickerHz:1)/1000);
        double flicker=.45+.55*randomAt(seed,phase,43);out->core=decay(age/(b->coreMs>1?b->coreMs:1))*.65*b->brightness;
        for(uint32_t branch=0;branch<b->branches;branch++){
            double angle=randomAt(seed,branch,44)*360,reach=b->arcReach*(.5+.5*randomAt(seed,branch,45))*(.4+.6*nrClamp(age/90,0,1)),x=0,y=0;
            for(uint32_t j=1;j<=b->arcSegments;j++){
                double u=(double)j/b->arcSegments,jitter=(randomAt(seed,branch*37+j,phase+51)-.5)*b->arcJitter;
                double xx=nrCos(angle)*reach*u-nrSin(angle)*jitter,yy=(nrSin(angle)*reach*u+nrCos(angle)*jitter)*.5;
                segment(out,x,y,xx,yy,envelope*flicker*b->brightness,.85,branch);
                if(j%3==0){double a2=angle+(randomAt(seed,j,branch+71)-.5)*2.3*180/NR_PI,length=reach*.23;
                    segment(out,xx,yy,xx+nrCos(a2)*length,yy+nrSin(a2)*length*.5,envelope*.65*b->brightness,1,branch+1);
                    point(out,xx,yy,envelope*flicker*b->brightness,1,'*',1);}
                x=xx;y=yy;
            }
        }
        for(uint32_t i=0;i<b->count&&i<40;i++){
            double a=randomAt(seed,i,84)*360,v=b->explosionForce*(.3+.7*randomAt(seed,i,85));
            point(out,nrCos(a)*v*t,nrSin(a)*v*t*.5+.6*t*t,fade*decay(t*2)*b->brightness,.75,b->glyphs[i%b->glyphCount],1);
        }
    }else if(kind==2){
        out->core=b->coreMs?nrSqrt(nrClamp(1-age/b->coreMs,0,1))*b->brightness:0;
        out->radius=b->explosionForce*t;out->shockwave=b->shockwave*fade;
        for(uint32_t i=0;i<b->count;i++){
            double a=randomAt(seed,i,91)*360,v=b->explosionForce*(.3+.9*randomAt(seed,i,92)),d=integral(b->drag,t),x=nrCos(a)*v*d,y=nrSin(a)*v*d*.5;
            double previous=integral(b->drag,nrClamp(t-b->trailMs/1000,0,1e12));
            double flicker=.4+.6*randomAt(seed,i,(uint32_t)nrFloor(age*b->flickerHz/1000)+100),alpha=fade*flicker*b->brightness;
            point(out,x,y,alpha,.3+.7*fade,age<150?'*':b->glyphs[i%b->glyphCount],1);
            segment(out,nrCos(a)*v*previous,nrSin(a)*v*previous*.5,x,y,alpha*.9,.7,0);
            if(age<b->coreMs*2&&i<20)segment(out,x*.15,y*.15,x*1.4,y*1.4,decay(age/180)*b->brightness,.95,0);
        }
    }else{
        for(uint32_t i=0;i<b->count;i++){
            double seconds=(age-randomAt(seed,i,120)*b->lifeMs*.6)/1000;if(seconds<0)continue;
            double v=b->launchSpeed*(.4+randomAt(seed,i,121)),x=(randomAt(seed,i,122)-.5)*24+b->wind*seconds;
            if(kind==4)x+=nrSin((seconds*2+i)*180/NR_PI)*1.7;
            point(out,x,-8+v*seconds,fade*b->brightness,.6,kind==4?0xb7:0x2502,1);
        }
    }return 1;
}
int nrKineticCenter(const State*s,int slot,double out[3]){
    if(!out||nrKineticProfile(s,slot)<0||!s->kineticControls[slot].used)return 0;
    int width,height;nrSceneViewport(s,&width,&height);
    Projection p;nrProjection(s,width,height,&p);int visible=nrProject(&p,s->emitters[slot].position,&out[0],&out[1],&out[2]);
    if(visible){out[0]*=.5;out[1]*=.25;}return visible;
}
static void screenSegment(NrContext*c,double x,double y,double xx,double yy,uint32_t color,double alpha,int material,uint32_t index){
    const State*s=nrView(c);int steps=(int)nrFloor(nrAbs(xx-x)+nrAbs(yy-y))+1;
    int previousX=NR_LAYOUT_MIN,previousY=NR_LAYOUT_MIN;
    for(int i=0;i<=steps;i++){
        double u=(double)i/steps;int px=(int)nrFloor(x+(xx-x)*u),py=(int)nrFloor(y+(yy-y)*u);
        if(px==previousX&&py==previousY)continue;previousX=px;previousY=py;
        if(px>=0&&py>=0&&px<(int)s->width&&py<(int)s->height){uint32_t ink=color;if(material>=0&&material<NR_MATERIALS&&s->materialPatterns[material].used){double ignored;ink=nrPaintAt(s,material,s->timeUs,px*256,py*256,index,&ignored);}nrCellBackground(c,px,py,ink,alpha);}
    }
}
static void sourcePaint(NrContext*c,const State*s,int slot,const double center[3],double weight){
    const KineticControls*b=&s->kineticControls[slot];NrSourceWeatherOptions o;nrSourceWeatherDefaults(&o);
#define COPY(field) o.field=b->field
    COPY(count);COPY(lifeMs);COPY(launchSpeed);COPY(gravity);COPY(drag);COPY(wind);COPY(flickerHz);COPY(trailMs);COPY(branches);COPY(arcSegments);COPY(arcJitter);COPY(coreMs);COPY(shockwave);COPY(explosionForce);COPY(seed);COPY(brightness);COPY(emberSpread);COPY(arcReach);COPY(glyphCount);
#undef COPY
    memcpy(o.glyphs,b->glyphs,sizeof(o.glyphs));uint32_t wheel[360];
    for(int h=0;h<360;h++)if(nrWindowPaletteSourceTextInk(.83,.1,h,&wheel[h]))return;
    NrSourceWeatherEvent event={(uint32_t)nrKineticProfile(s,slot),b->eventId,center[0],center[1],(double)b->startUs/1000};
    nrSourceWeatherPaint(&event,(double)s->timeUs/1000,&o,nrClamp(weight,0,1),wheel,s->width,s->height,(uint32_t*)c->cells);
}
void nrDrawKinetic(NrContext*c,const Projection*projection){
    const State*s=nrView(c);
    for(int slot=0;slot<(int)NR_MAX_EMITTERS;slot++){
        if(!s->kineticControls[slot].used)continue;
        KineticSample sample;double center[3];if(!nrKineticSample(s,slot,&sample)||!nrProject(projection,s->emitters[slot].position,&center[0],&center[1],&center[2]))continue;
        center[0]*=.5;center[1]*=.25;const Emitter*e=&s->emitters[slot];double materialAlpha;
        nrUseMaterial(c,e->material);c->characterOwner=0;
        uint32_t color=nrPaint(s,e->material,s->timeUs,(uint32_t)e->id,&materialAlpha);double alpha=e->alpha*materialAlpha;
        if(s->kineticPaint[slot]){sourcePaint(c,s,slot,center,alpha);continue;}
        for(uint32_t i=0;i<sample.segmentCount;i++){
            const double*r=sample.segments[i];screenSegment(c,center[0]+r[0],center[1]+r[1],center[0]+r[2],center[1]+r[3],color,r[4]*alpha,e->material,i);
        }
        for(uint32_t i=0;i<sample.pointCount;i++){
            const double*r=sample.points[i];double x=nrFloor(center[0]+r[0]),y=nrFloor(center[1]+r[1]);
            if(x>=0&&y>=0&&x<s->width&&y<s->height){uint32_t ink=color;if(e->material>=0&&e->material<NR_MATERIALS&&s->materialPatterns[e->material].used){double ignored;ink=nrPaintAt(s,e->material,s->timeUs,(int32_t)x*256,(int32_t)y*256,i,&ignored);}nrIndexedGlyph(c,(int)x,(int)y,(uint32_t)r[4],ink,r[2]*alpha,0,i);}
        }
        if(sample.core>0||sample.shockwave>0){
            double extent=sample.shockwave>0?sample.radius+3:3;
            int left=(int)nrFloor(nrClamp(center[0]-extent,0,s->width)),right=(int)nrClamp(center[0]+extent+1,0,s->width);
            int top=(int)nrFloor(nrClamp(center[1]-extent*.5,0,s->height)),bottom=(int)nrClamp(center[1]+extent*.5+1,0,s->height);
            for(int y=top;y<bottom;y++)for(int x=left;x<right;x++){
                double dx=x-center[0],dy=2*(y+.5-center[1]),distance=nrSqrt(dx*dx+dy*dy);
                double core=sample.core*decay(distance*distance/2),ring=sample.shockwave*decay((distance-sample.radius)*(distance-sample.radius));
                uint32_t ink=color;if(e->material>=0&&e->material<NR_MATERIALS&&s->materialPatterns[e->material].used){double ignored;ink=nrPaintAt(s,e->material,s->timeUs,x*256,y*256,0,&ignored);}nrCellBackground(c,x,y,ink,nrClamp(core+ring,0,1)*alpha);
            }
        }
    }c->paintBlend=0;
}
