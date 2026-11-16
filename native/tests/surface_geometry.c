/* Real C core, analytic collision oracles, and hostile snapshot validation.
 * No fake host or replacement physics implementation is injected into runtime. */
#include "internal.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

static void command(NrContext*c,const char*text) {
    int result=nrCommand(c,text,(uint32_t)strlen(text));
    if(result<0)fprintf(stderr,"command rejected: %s: %s\n",text,nrError(c));
    assert(result>=0);
}
static void put32(unsigned char*p,uint32_t n) {
    for(int i=0;i<4;i++)p[i]=(unsigned char)(n>>(i*8));
}
static int closeValue(double x,double y) {return nrAbs(x-y)<1e-9;}

static void analyticAndBvh(NrContext*c) {
    command(c,"{\"op\":\"surface\",\"id\":1}");
    State*s=&c->state;
    s->meshCount=NR_MESH;s->geometry.meshGeneration=1;
    for(int i=0;i<NR_MESH;i++) {
        double x=(i%16)*3,y=(i/16)*8;
        s->mesh[i]=(Triangle){nrV(x,y-2,-2),nrV(x,y+2,-2),nrV(x,y,2),0xffffff,1};
        s->geometry.triangleSurfaces[i]=1;
    }
    assert(nrBuildGeometry(s,&s->geometry.index));
    assert(s->geometry.index.nodeCount>1&&s->geometry.index.nodeCount<=NR_BVH_NODES);
    unsigned long long testedTotal=0;
    for(int k=0;k<10000;k++) {
        /* Independently known triangle inequalities on planes x=constant.
         * This oracle does not use the runtime's Moller-Trumbore calculation. */
        double fromX=(k%2)?-8:52,toX=(k%2)?52:-8;
        double y=((k*193)%14000)/100.0-10,z=((k*71)%800)/100.0-4;
        int expected=-1;double expectedT=2;
        for(int i=0;i<NR_MESH;i++) {
            double cx=(i%16)*3,cy=(i/16)*8;
            if(z< -2||z>2||nrAbs(y-cy)>(2-z)*.5+1e-12)continue;
            double t=(cx-fromX)/(toX-fromX);
            if(t>=0&&t<=1&&t<expectedT-1e-12){expected=i;expectedT=t;}
        }
        uint32_t tested=0;GeometryHit hit;
        int found=nrGeometryHit(s,2u,nrV(fromX,y,z),nrV(toX,y,z),&hit,&tested);
        assert(found==(expected>=0));
        if(found) {
            assert(hit.triangleIndex==expected&&hit.surfaceId==1);
            assert(closeValue(hit.fraction,expectedT));
            assert(closeValue(hit.position.x,(expected%16)*3));
            assert(closeValue(hit.normal.x,fromX>toX?1:-1));
        }
        testedTotal+=tested;
    }
    assert(testedTotal<10000ull*64ull); /* Actual BVH pruning, not a renamed full scan. */
    GeometryHit hit;uint32_t tested=0;
    assert(!nrGeometryHit(s,2,nrV(0,0,0),nrV(0,0,0),&hit,&tested));
    assert(!nrGeometryHit(s,2,nrV(0,0,0),nrV(0,0,1),&hit,&tested));
    printf("PASS: 10000 independent plane/triangle queries, %llu narrow-phase tests\n",testedTotal);
}

static void contactBudget(NrContext*c) {
    command(c,"{\"op\":\"reset\",\"seed\":91}");
    command(c,"{\"op\":\"floor\",\"enabled\":false}");
    command(c,"{\"op\":\"surface\",\"id\":1,\"restitution\":1,\"friction\":0}");
    command(c,"{\"op\":\"mesh\",\"triangles\":[{\"a\":[0,-2,-2],\"b\":[0,2,-2],\"c\":[0,0,2],\"surfaceId\":1},{\"a\":[0.005,-2,-2],\"b\":[0.005,2,-2],\"c\":[0.005,0,2],\"surfaceId\":1}]}");
    command(c,"{\"op\":\"emitter\",\"id\":1,\"effect\":\"weather/autumn-drift\",\"shape\":\"point\",\"count\":1,\"runningTimeMs\":0,\"position\":[0.0025,0,0],\"velocity\":[240,0,0],\"spread\":[0,0,0],\"gravity\":[0,0,0],\"wind\":[0,0,0],\"windVariation\":[0,0,0],\"drag\":0,\"lift\":0,\"flutterAmount\":0,\"deposit\":false,\"colliders\":{\"surfaces\":[1]}}");
    command(c,"{\"op\":\"time\",\"timeUs\":8333}");
    assert(c->state.geometry.contactBudgetExhausted==1);
    assert(c->state.geometry.surfaces[0].impacts==NR_COLLISION_CONTACTS);
    double x=c->state.particles[0].position.x/NR_Q;
    assert(x>=0&&x<=.005);
    assert(c->state.step==1);
    puts("PASS: four-contact bound retains last resolved position and records saturation");
}

static void hostileSnapshots(NrContext*c) {
    uint32_t bytes=nrSnapshotSize();
    unsigned char*before=malloc(bytes),*input=malloc(bytes),*after=malloc(bytes);
    assert(before&&input&&after);assert(nrSave(c,before,bytes)==0);
    for(int i=0;i<10;i++) {
        memcpy(input,before,bytes);State*s=(State*)(void*)(input+24);
        switch(i) {
            case 0:s->geometry.index.nodeCount=NR_BVH_NODES+1;break;
            case 1:s->geometry.index.nodes[0].left=NR_BVH_NODES+1;break;
            case 2:s->geometry.index.order[0]=NR_MESH;break;
            case 3:s->geometry.triangleSurfaces[0]=17;break;
            case 4:s->geometry.emitterColliders[0]=0x40000000u;break;
            case 5:s->geometry.particleContacts[0].normal=nrV(0,0,0);break;
            case 6:s->geometry.surfaces[0].wetness=NAN;break;
            case 7:s->geometry.surfaces[0].heat=1.01;break;
            case 8:s->geometry.surfaces[0].renderVisible=2;break;
            default:s->geometry.index.nodes[0].minimum.x=99;break;
        }
        put32(input+20,nrCrc(input+24,bytes-24));
        assert(nrLoad(c,input,bytes)<0);
        assert(nrSave(c,after,bytes)==0&&!memcmp(before,after,bytes));
    }
    /* Known old expanded schema/length: reject local intentValue semantics after
     * decoding the exact old payload, not merely because the extension is absent. */
    command(c,"{\"op\":\"reset\"}");
    command(c,"{\"op\":\"define\",\"path\":\"/out\",\"value\":0}");
    command(c,"{\"op\":\"trigger\",\"id\":1,\"event\":\"/review/inspect\",\"when\":{\"intentValue\":{\"comparison\":\"at-least\",\"value\":7}},\"target\":\"/out\",\"value\":1}");
    assert(nrSave(c,before,bytes)==0);memcpy(input,before,bytes);
    uint32_t oldBytes=(uint32_t)offsetof(State,geometry);
    State*old=(State*)(void*)(input+24);old->schema=NR_STATE_SCHEMA_CONTRACTS7;
    put32(input+12,NR_STATE_SCHEMA_CONTRACTS7);put32(input+16,oldBytes);
    put32(input+20,nrCrc(input+24,oldBytes));
    assert(nrLoad(c,input,oldBytes+24)<0);
    assert(nrSave(c,after,bytes)==0&&!memcmp(before,after,bytes));
    free(after);free(input);free(before);
    puts("PASS: hostile extension and exact old-schema semantic rejection preserve state");
}

int main(void) {
    NrContext*c=malloc(sizeof(*c));assert(c&&nrInit(c,sizeof(*c),7)==0);
    analyticAndBvh(c);contactBudget(c);hostileSnapshots(c);
    free(c);return 0;
}
