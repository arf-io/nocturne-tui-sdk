#include "internal.h"
/* Foam is a bounded intensity inventory, not water mass. Shared authored edges
 * route it horizontally. Closed edges retain inventory; no query moves it. */
static int samePoint(Vec3 a,Vec3 b){return a.x==b.x&&a.y==b.y&&a.z==b.z;}
static Vec3 vertex(const Triangle*t,int k){return k==0?t->a:k==1?t->b:t->c;}
static int neighbor(const State*s,int from,int edge){
    Vec3 a=vertex(&s->mesh[from],edge),b=vertex(&s->mesh[from],(edge+1)%3);
    int result=-1,id=s->geometry.triangleSurfaces[from];
    for(int i=0;i<s->meshCount;i++)if(i!=from&&s->geometry.triangleSurfaces[i]==id){
        for(int k=0;k<3;k++){
            Vec3 c=vertex(&s->mesh[i],k),d=vertex(&s->mesh[i],(k+1)%3);
            if((samePoint(a,c)&&samePoint(b,d))||(samePoint(a,d)&&samePoint(b,c))){
                if(result>=0)return -2;result=i;
            }
        }
    }
    return result;
}
static double projectedArea(const Triangle*t){return nrAbs(nrCross(nrSub(t->b,t->a),nrSub(t->c,t->a)).y)/2;}
static int moving(const State*s,int id){return id>0&&id<=NR_SURFACES&&(s->foamVelocity[id-1].x||s->foamVelocity[id-1].z);}
int nrValidFoamTransport(const State*s){
    if(s->meshCount<0||s->meshCount>NR_MESH)return 0;
    for(int i=0;i<s->meshCount;i++)if(s->geometry.triangleSurfaces[i]<0||s->geometry.triangleSurfaces[i]>NR_SURFACES)return 0;
    double incoming=0,outgoing=0;
    for(int i=0;i<NR_SURFACES;i++){
        double x=s->foamVelocity[i].x,z=s->foamVelocity[i].z;
        if(!(x>=-1000&&x<=1000&&z>=-1000&&z<=1000))return 0;
        if((x||z)&&(s->schema<NR_STATE_SCHEMA_FOAM_TRANSPORT||!s->geometry.surfaces[i].used||!s->foam.settings[i].used))return 0;
    }
    for(int i=0;i<NR_MESH;i++){
        double in=s->foamTransfers[i].incoming,out=s->foamTransfers[i].outgoing;
        if(!(in>=0&&in<=1e14&&out>=0&&out<=1e14))return 0;
        if((in||out)&&(s->schema<NR_STATE_SCHEMA_FOAM_TRANSPORT||i>=s->meshCount||s->geometry.triangleSurfaces[i]<=0||!s->foam.settings[s->geometry.triangleSurfaces[i]-1].used))return 0;
        incoming+=in;outgoing+=out;
        if(i<s->meshCount&&moving(s,s->geometry.triangleSurfaces[i])){
            if(projectedArea(&s->mesh[i])<1e-12)return 0;
            for(int k=0;k<3;k++)if(neighbor(s,i,k)==-2)return 0;
        }
    }
    return nrAbs(incoming-outgoing)<=1e-8*(1+incoming+outgoing);
}
int nrFoamTransportCommand(NrContext*c,State*s,const Json*j){
    double id,x,z;int at=nrField(j,0,"velocity");
    if(!nrAllowed(j,0,"op surfaceId velocity")||!nrNumber(j,nrField(j,0,"surfaceId"),&id)||id<1||id>NR_SURFACES||id!=(int)id||
       !s->geometry.surfaces[(int)id-1].used||!s->foam.settings[(int)id-1].used||at<0||j->tokens[at].type!=J_ARRAY||j->tokens[at].count!=2||
       !nrNumber(j,at+1,&x)||!nrNumber(j,j->tokens[at+1].next,&z)||!(x>=-1000&&x<=1000&&z>=-1000&&z<=1000)){
        memcpy(c->error,"Invalid foam transport configuration",sizeof("Invalid foam transport configuration"));return -1;
    }
    s->foamVelocity[(int)id-1].x=x;s->foamVelocity[(int)id-1].z=z;
    if(!nrValidFoamTransport(s)){memcpy(c->error,"Foam transport requires manifold horizontal geometry",sizeof("Foam transport requires manifold horizontal geometry"));return -1;}
    return 0;
}
void nrFoamTransportTick(State*s){
    int active=0;for(int i=0;i<s->meshCount;i++)if(moving(s,s->geometry.triangleSurfaces[i])&&s->foam.cells[i].density){active=1;break;}
    if(!active)return;
    double amounts[NR_MESH][3]={{0}},delta[NR_MESH]={0};int targets[NR_MESH][3];
    for(int i=0;i<s->meshCount;i++){
        int id=s->geometry.triangleSurfaces[i];if(!moving(s,id)||!s->foam.cells[i].density)continue;
        const Triangle*t=&s->mesh[i];double total=0,area=projectedArea(t);
        Vec3 midpoint=nrScale(nrAdd(nrAdd(t->a,t->b),t->c),1.0/3);
        for(int k=0;k<3;k++){
            int to=neighbor(s,i,k);targets[i][k]=to;if(to<0)continue;
            Vec3 a=vertex(t,k),b=vertex(t,(k+1)%3);double nx=-(b.z-a.z),nz=b.x-a.x;
            const Triangle*other=&s->mesh[to];Vec3 next=nrScale(nrAdd(nrAdd(other->a,other->b),other->c),1.0/3);
            if(nx*(next.x-midpoint.x)+nz*(next.z-midpoint.z)<0){nx=-nx;nz=-nz;}
            double rate=(s->foamVelocity[id-1].x*nx+s->foamVelocity[id-1].z*nz)/area;
            if(rate>0){amounts[i][k]=rate/120;total+=amounts[i][k];}
        }
        double scale=s->foam.cells[i].density/(total>1?total:1);
        for(int k=0;k<3;k++)if(amounts[i][k]>0){
            double amount=amounts[i][k]*scale;int to=targets[i][k];
            delta[i]-=amount;delta[to]+=amount;
            s->foamTransfers[i].outgoing+=amount;s->foamTransfers[to].incoming+=amount;
        }
    }
    for(int i=0;i<s->meshCount;i++){
        FoamCell*f=&s->foam.cells[i];f->density+=delta[i];
        /* Roundoff from summing fan-out is bounded by the inventory itself. */
        if(f->density<0)f->density=0;
        if(f->density>1){f->saturated+=f->density-1;f->density=1;}
    }
}
int nrSurfaceFoamTransport(const NrContext*c,uint32_t id,double*out,uint32_t capacity){
    int count=nrSurfaceFoam(c,id,0,0);if(count<0||(!out&&capacity)||((uintptr_t)out%8))return -1;
    if(!out)return count;if(capacity<(uint32_t)count||!nrExternalOutput(c,out,(size_t)count*7*sizeof(double)))return -1;
    int row=0;for(int i=0;i<c->state.meshCount;i++)if(c->state.geometry.triangleSurfaces[i]==(int)id){
        const FoamCell*f=&c->state.foam.cells[i];double values[7]={i,f->density,f->generated,f->decayed,f->saturated,c->state.foamTransfers[i].incoming,c->state.foamTransfers[i].outgoing};
        memcpy(out+row*7,values,sizeof(values));row++;
    }return count;
}
