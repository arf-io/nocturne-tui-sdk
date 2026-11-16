/* CRC-valid hostile contact data must reject before any simulation/render use. */
#include "internal.h"
#include <assert.h>
#include <limits.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

static void command(NrContext*c,const char*text) {
    int result=nrCommand(c,text,(uint32_t)strlen(text));
    if(result<0)fprintf(stderr,"command rejected: %s\n",nrError(c));
    assert(result>=0);
}
static void put32(unsigned char*p,uint32_t value) {
    for(int i=0;i<4;i++)p[i]=(unsigned char)(value>>(8*i));
}
static int hostileInactive(NrContext*c) {
    command(c,"{\"op\":\"surface\",\"id\":1}");
    command(c,"{\"op\":\"floor\",\"maxIndividual\":1,\"maxTiles\":1,\"reentrainWindSpeed\":0}");
    command(c,"{\"op\":\"emitter\",\"id\":1,\"effect\":\"weather/autumn-drift\",\"count\":2,\"runningTimeMs\":0,\"shape\":\"point\",\"position\":[0,0,0],\"velocity\":[0,0,0],\"spread\":[0,0,0],\"gravity\":[0,0,0],\"wind\":[0,0,0],\"windVariation\":[0,0,0],\"drag\":0,\"lift\":0,\"flutterAmount\":0,\"deposit\":true}");
    command(c,"{\"op\":\"emitter\",\"id\":2,\"effect\":\"weather/autumn-drift\",\"count\":1,\"runningTimeMs\":0,\"shape\":\"point\",\"position\":[0,5,0],\"velocity\":[0,0,0],\"spread\":[0,0,0],\"gravity\":[0,0,0],\"wind\":[0,0,0],\"windVariation\":[0,0,0],\"drag\":0,\"lift\":0,\"flutterAmount\":0,\"deposit\":false}");
    command(c,"{\"op\":\"time\",\"timeUs\":8333}");
    assert(c->state.deposits[0].used&&c->state.tiles[0].used&&c->state.particles[2].state);
    assert(!c->state.geometry.depositContacts[0].used&&!c->state.geometry.particleContacts[2].used);
    uint32_t bytes=nrSnapshotSize();unsigned char*before=malloc(bytes),*input=malloc(bytes),*after=malloc(bytes);
    assert(before&&input&&after&&nrSave(c,before,bytes)==0);
    int accepted=0,cases=0;
    for(int family=0;family<3;family++)for(int variant=0;variant<7;variant++) {
        memcpy(input,before,bytes);State*s=(State*)(void*)(input+24);
        if(family<2) {
            SurfaceContact*q=family?&s->geometry.depositContacts[0]:&s->geometry.particleContacts[2];
            switch(variant) {
                case 0:q->surfaceId=INT_MAX;break;
                case 1:q->surfaceId=-1;break;
                case 2:q->surfaceId=NR_SURFACES+1;break;
                case 3:q->surfaceId=2;break; /* bounded but absent surface */
                case 4:q->surfaceId=1;break; /* existing surface, inactive record */
                case 5:q->triangleIndex=NR_MESH;break;
                default:q->normal.x=NAN;break;
            }
        } else {
            /* Slot zero is a live floor tile; slot one is inactive. Neither can
             * retain a concealed invalid surface payload behind a zero owner. */
            SurfaceTile*q=&s->geometry.tileSurfaces[variant==3?1:0];
            switch(variant) {
                case 0:q->surfaceId=INT_MAX;break;
                case 1:q->surfaceId=-1;break;
                case 2:q->surfaceId=NR_SURFACES+1;break;
                case 3:q->surfaceId=2;break;
                case 4:q->normal.x=NAN;break;
                case 5:q->triangleIndex=NR_MESH;break;
                default:q->a.x=INFINITY;break;
            }
        }
        put32(input+20,nrCrc(input+24,bytes-24));cases++;
        int result=nrLoad(c,input,bytes);
        if(result>=0) {
            fprintf(stderr,"FAIL: accepted inactive contact payload family=%d variant=%d\n",family,variant);accepted++;
            /* Restore a safe source immediately; never render accepted hostile data. */
            assert(nrLoad(c,before,bytes)==0);
        } else assert(nrSave(c,after,bytes)==0&&!memcmp(before,after,bytes));
    }
    assert(nrLoad(c,before,bytes)==0&&nrSave(c,after,bytes)==0&&!memcmp(before,after,bytes));
    nrRender(c);assert(nrInfo(c)&&nrSave(c,after,bytes)==0&&!memcmp(before,after,bytes));
    free(after);free(input);free(before);
    printf("%s: %d hostile inactive-contact cases, accepted=%d; valid floor snapshot remains pure\n",accepted?"FAIL":"PASS",cases,accepted);
    return accepted;
}
static void retainedExpiredGeometry(NrContext*c) {
    command(c,"{\"op\":\"reset\"}");command(c,"{\"op\":\"floor\",\"enabled\":false}");
    command(c,"{\"op\":\"surface\",\"id\":1,\"maxIndividual\":1,\"maxTiles\":1,\"retentionMs\":1,\"reentrainWindSpeed\":0}");
    command(c,"{\"op\":\"mesh\",\"triangles\":[{\"a\":[-4,0,-4],\"b\":[4,0,-4],\"c\":[0,0,4],\"surfaceId\":1}]}");
    command(c,"{\"op\":\"emitter\",\"id\":1,\"effect\":\"weather/autumn-drift\",\"count\":2,\"runningTimeMs\":0,\"shape\":\"point\",\"position\":[0,0.1,0],\"velocity\":[0,-240,0],\"spread\":[0,0,0],\"gravity\":[0,0,0],\"wind\":[0,0,0],\"windVariation\":[0,0,0],\"drag\":0,\"lift\":0,\"flutterAmount\":0,\"deposit\":true,\"colliders\":{\"surfaces\":[1]}}");
    command(c,"{\"op\":\"time\",\"timeUs\":8333}");
    assert(c->state.deposits[0].used&&c->state.tiles[0].used);
    command(c,"{\"op\":\"time\",\"timeUs\":16666}");
    assert(!c->state.deposits[0].used&&!c->state.tiles[0].used);
    assert(c->state.geometry.depositContacts[0].used&&c->state.geometry.tileSurfaces[0].surfaceId==1);
    uint32_t bytes=nrSnapshotSize();unsigned char*before=malloc(bytes),*after=malloc(bytes);assert(before&&after);
    assert(nrSave(c,before,bytes)==0&&nrLoad(c,before,bytes)==0&&nrSave(c,after,bytes)==0&&!memcmp(before,after,bytes));
    nrRender(c);assert(nrSave(c,after,bytes)==0&&!memcmp(before,after,bytes));
    free(after);free(before);puts("PASS: legitimately retained expired contact/tile geometry still round trips");
}
int main(void) {
    NrContext*c=malloc(sizeof(*c));assert(c&&nrInit(c,sizeof(*c),61006)==0);
    int rejected=hostileInactive(c);retainedExpiredGeometry(c);free(c);
    return rejected?1:0;
}
