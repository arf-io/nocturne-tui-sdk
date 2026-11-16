#include "internal.h"

static int reject(NrContext*c,const char*message){size_t n=strlen(message);if(n>255)n=255;memcpy(c->error,message,n);c->error[n]=0;return -1;}
static int number(const Json*j,int object,const char*key,double*out,double lo,double hi){int t=nrField(j,object,key);if(t<0)return 1;double v;if(!nrNumber(j,t,&v)||!(v>=lo&&v<=hi))return 0;*out=v;return 1;}
static int duration(const Json*j,const char*key,uint64_t*out){double v=*out/1000.0;if(!number(j,0,key,&v,0,86400000))return 0;double us=v*1000;if(us!=(uint64_t)us)return 0;*out=(uint64_t)us;return 1;}
static int lengths(const ElectricalArc*a,double distance[32],double*maximum){
    if(a->count<2||a->count>32)return 0;
    *maximum=0;distance[0]=0;
    for(uint32_t i=0;i<a->count;i++){
        const ElectricalPoint*p=&a->points[i];
        if(p->reserved||!(p->position.x>=-16000&&p->position.x<=16000)||!(p->position.y>=-16000&&p->position.y<=16000)||!(p->position.z>=-16000&&p->position.z<=16000))return 0;
        if(!i){if(p->parent!=-1)return 0;continue;}
        if(p->parent<0||p->parent>=(int)i)return 0;
        Vec3 delta=nrSub(p->position,a->points[p->parent].position);double length=nrSqrt(nrDot(delta,delta));
        if(length<1e-8)return 0;
        distance[i]=distance[p->parent]+length;if(distance[i]>*maximum)*maximum=distance[i];
    }return 1;
}
static int validArc(const State*s,const ElectricalArc*a){
    if(!a->id)return 1;
    double d[32],maximum;
    if(s->schema<NR_STATE_SCHEMA_ELECTRICAL_ARCS||a->id>65535||a->material>=NR_MATERIALS||!s->materials[a->material].used||a->startUs>s->timeUs||
       a->delayUs>86400000000ull||a->holdUs>86400000000ull||a->fadeUs>86400000000ull||a->periodUs>86400000000ull||
       !(a->speed>=.001&&a->speed<=10000)||!(a->jitter>=0&&a->jitter<=16)||!(a->alpha>=0&&a->alpha<=1)||!(a->flicker>=0&&a->flicker<=1)||!lengths(a,d,&maximum))return 0;
    double total=a->delayUs+maximum/a->speed*1000000.0+a->holdUs+a->fadeUs;
    return total<=86400000000.0&&(!a->periodUs||a->periodUs>=total);
}
int nrValidElectricalArcs(const State*s){
    for(int i=0;i<16;i++){const ElectricalArc*a=&s->electricalArcs[i];if(!validArc(s,a))return 0;
        if(a->id)for(int k=0;k<i;k++)if(s->electricalArcs[k].id==a->id)return 0;
    }return 1;
}
/* Validate a local candidate before committing; the retained start epoch,
 * graph joints and source seed remain unchanged by numeric animation. */
int nrBindElectricalValue(State*s,const Value*v,double x){
    int slot=-1;for(int i=0;i<16;i++)if(s->electricalArcs[i].id==(uint32_t)v->bindingId){slot=i;break;}
    if(slot<0)return 0;ElectricalArc a=s->electricalArcs[slot];int matched=0;
#define SCALAR(name,member,lo,hi) if(!strcmp(v->field,name)){if(!(x>=lo&&x<=hi))return 0;a.member=x;matched=1;}
    SCALAR("speed",speed,.001,10000) SCALAR("jitter",jitter,0,16)
    SCALAR("alpha",alpha,0,1) SCALAR("flicker",flicker,0,1)
#undef SCALAR
#define DURATION(name,member) if(!strcmp(v->field,name)){double us=x*1000;if(!(x>=0&&x<=86400000)||us!=(uint64_t)us)return 0;a.member=(uint64_t)us;matched=1;}
    DURATION("delayMs",delayUs) DURATION("holdMs",holdUs)
    DURATION("fadeMs",fadeUs) DURATION("repeatMs",periodUs)
#undef DURATION
    if(!matched||!validArc(s,&a))return 0;s->electricalArcs[slot]=a;return 1;
}
int nrElectricalArcCommand(NrContext*c,State*s,const Json*j){
    if(s->schema<NR_STATE_SCHEMA_ELECTRICAL_ARCS)return reject(c,"Electrical graphs require schema52");
    double id=0;if(nrField(j,0,"id")<0||!number(j,0,"id",&id,1,65535)||id!=(uint32_t)id)return reject(c,"Electrical arc id required");
    int slot=-1,freeSlot=-1;for(int i=0;i<16;i++){if(s->electricalArcs[i].id==(uint32_t)id)slot=i;if(!s->electricalArcs[i].id&&freeSlot<0)freeSlot=i;}
    if(nrEqual(j,nrField(j,0,"op"),"remove-electrical-arc")){
        if(!nrAllowed(j,0,"op id"))return reject(c,"Unknown electrical removal field");
        if(slot>=0)memset(&s->electricalArcs[slot],0,sizeof(ElectricalArc));return 0;
    }
    if(!nrAllowed(j,0,"op id points seed material speed jitter alpha flicker delayMs holdMs fadeMs repeatMs"))return reject(c,"Unknown electrical arc field");
    if(slot>=0)return reject(c,"Electrical arc already exists");if(freeSlot<0)return reject(c,"Electrical arc capacity");
    ElectricalArc a;memset(&a,0,sizeof(a));a.id=(uint32_t)id;a.seed=nrHash(s->seed^a.id);a.material=2;a.startUs=s->timeUs;a.speed=30;a.jitter=.15;a.alpha=.8;a.flicker=.15;a.holdUs=100000;a.fadeUs=150000;
    double seed=a.seed,material=a.material;
    if(!number(j,0,"seed",&seed,0,4294967295.0)||seed!=(uint32_t)seed||!number(j,0,"material",&material,0,NR_MATERIALS-1)||material!=(uint32_t)material||
       !number(j,0,"speed",&a.speed,.001,10000)||!number(j,0,"jitter",&a.jitter,0,16)||!number(j,0,"alpha",&a.alpha,0,1)||!number(j,0,"flicker",&a.flicker,0,1)||
       !duration(j,"delayMs",&a.delayUs)||!duration(j,"holdMs",&a.holdUs)||!duration(j,"fadeMs",&a.fadeUs)||!duration(j,"repeatMs",&a.periodUs))return reject(c,"Invalid electrical arc setting");
    a.seed=(uint32_t)seed;a.material=(uint32_t)material;
    int points=nrField(j,0,"points");if(points<0||j->tokens[points].type!=J_ARRAY||j->tokens[points].count<2||j->tokens[points].count>32)return reject(c,"Electrical points required");
    a.count=j->tokens[points].count;int t=points+1;
    for(uint32_t i=0;i<a.count;i++){
        if(j->tokens[t].type!=J_OBJECT||!nrAllowed(j,t,"position parent"))return reject(c,"Electrical point shape");
        int pos=nrField(j,t,"position");double parent=-2;
        if(pos<0||j->tokens[pos].type!=J_ARRAY||j->tokens[pos].count!=3||nrField(j,t,"parent")<0||!number(j,t,"parent",&parent,-1,31)||parent!=(int)parent)return reject(c,"Electrical XYZ and parent required");
        int v=pos+1;double xyz[3];for(int k=0;k<3;k++){if(!nrNumber(j,v,&xyz[k])||!(xyz[k]>=-16000&&xyz[k]<=16000))return reject(c,"Electrical coordinate bounds");v=j->tokens[v].next;}
        a.points[i].position=nrV(xyz[0],xyz[1],xyz[2]);a.points[i].parent=(int)parent;t=j->tokens[t].next;
    }
    if(!validArc(s,&a))return reject(c,"Invalid electrical topology or period");s->electricalArcs[freeSlot]=a;return 0;
}
/* Rows describe exact straight centerlines before the appearance-only jitter.
 * Branches start together when their shared parent leader arrives. */
int nrElectricalSegments(const State*s,const ElectricalArc*a,double out[31][7],double*opacity,int*phase,uint64_t*cycle){
    double distance[32],maximum;*opacity=0;*phase=0;*cycle=0;if(!a->id||!lengths(a,distance,&maximum))return 0;
    uint64_t age=s->timeUs>=a->startUs?s->timeUs-a->startUs:0;if(a->periodUs){*cycle=age/a->periodUs;age%=a->periodUs;}
    if(age<a->delayUs)return 0;
    double time=(age-a->delayUs)/1000000.0,leaderTime=maximum/a->speed,hold=a->holdUs/1000000.0,fade=a->fadeUs/1000000.0;
    if(time<leaderTime)*phase=1;else if(time<leaderTime+hold)*phase=2;
    else if(fade&&time<leaderTime+hold+fade)*phase=3;else{*phase=4;return 0;}
    *opacity=a->alpha*(*phase==3?nrClamp((leaderTime+hold+fade-time)/fade,0,1):1);
    double leader=time*a->speed;int count=0;
    for(uint32_t i=1;i<a->count;i++){
        int parent=a->points[i].parent;double length=distance[i]-distance[parent],fraction=nrClamp((leader-distance[parent])/length,0,1);if(fraction<=0)continue;
        Vec3 from=a->points[parent].position,to=nrAdd(from,nrScale(nrSub(a->points[i].position,from),fraction));
        out[count][0]=from.x;out[count][1]=from.y;out[count][2]=from.z;out[count][3]=to.x;out[count][4]=to.y;out[count][5]=to.z;out[count][6]=i;count++;
    }return count;
}
void nrDrawElectricalArcs(NrContext*c,const Projection*projection){
    const State*s=nrView(c);
    for(int i=0;i<16;i++){
        const ElectricalArc*a=&s->electricalArcs[i];if(!a->id)continue;
        double rows[31][7],opacity;int phase;uint64_t cycle;int count=nrElectricalSegments(s,a,rows,&opacity,&phase,&cycle);if(!count||opacity<=0)continue;
        double materialAlpha;uint32_t color=nrPaint(s,a->material,s->timeUs,a->id,&materialAlpha);
        nrUseMaterial(c,a->material);c->paintOwner=0x70000000u|a->id;c->paintDetail=1;c->paintSampling=2;
        uint32_t previousPattern=c->paintMaterialId;c->paintMaterialId=s->materialPatterns[a->material].used?(uint32_t)a->material+1:0;
        uint32_t epoch=(uint32_t)(s->timeUs/33333);
        double flicker=s->reducedMotion?1:1-a->flicker*nrRandom(a->seed,epoch,0);opacity*=materialAlpha*flicker;
        for(int k=0;k<count;k++){
            Vec3 from=nrV(rows[k][0],rows[k][1],rows[k][2]),to=nrV(rows[k][3],rows[k][4],rows[k][5]);
            if(!a->jitter||s->reducedMotion){nrLine(c,projection,from,to,color,opacity);continue;}
            Vec3 direction=nrNormal(nrSub(to,from)),u,v;nrSurfaceBasis(direction,&u,&v);Vec3 last=from;
            for(int point=1;point<=12;point++){
                double fraction=point/12.0;Vec3 next=nrAdd(from,nrScale(nrSub(to,from),fraction));
                if(point<12){uint32_t key=(uint32_t)rows[k][6]*32+point;double envelope=nrSin(fraction*180)*a->jitter;
                    next=nrAdd(next,nrAdd(nrScale(u,(nrRandom(a->seed,key,epoch)*2-1)*envelope),nrScale(v,(nrRandom(a->seed,key,epoch+1)*2-1)*envelope)));}
                nrLine(c,projection,last,next,color,opacity);last=next;
            }
        }
        c->paintMaterialId=previousPattern;
    }
}
