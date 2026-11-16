/* Ordered raster-coverage differential against instrumented original world.inc. */
#include "scenic_art.h"
#include "scenic_source_raster.h"
#include "nocturne_world.h"
#include <errno.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    int32_t x,y,depth,alpha,threshold;
    uint32_t rgb;
} Coverage;
typedef struct { Coverage *v; size_t n,cap; } Trace;
static Trace original,ported;

static void append(Trace *t,Coverage q) {
    if(t->n==t->cap) {
        size_t cap=t->cap?t->cap*2:16384;
        if(cap<t->cap||cap>SIZE_MAX/sizeof(*t->v)){fputs("coverage trace overflow\n",stderr);exit(70);}
        Coverage *v=realloc(t->v,cap*sizeof(*v));
        if(!v){fputs("coverage trace allocation failed\n",stderr);exit(70);}
        t->v=v;t->cap=cap;
    }
    t->v[t->n++]=q;
}

/* Inserted into actual original wRaster/wDot/wLine immediately before its
 * framebuffer depth test, so this oracle records source coverage candidates. */
void nsOriginalRasterCoverage(int32_t x,int32_t y,int32_t depth,uint32_t rgb,
                              int32_t alpha,int32_t threshold) {
    append(&original,(Coverage){x,y,depth,alpha,threshold,rgb});
}
static void portedCoverage(void *user,int32_t x,int32_t y,int32_t depth,
                           uint32_t rgb,int32_t alpha,int32_t threshold) {
    append((Trace *)user,(Coverage){x,y,depth,alpha,threshold,rgb});
}
static int equalCoverage(Coverage a,Coverage b) {
    return a.x==b.x&&a.y==b.y&&a.depth==b.depth&&a.rgb==b.rgb&&
           a.alpha==b.alpha&&a.threshold==b.threshold;
}
extern int nsOriginalProjectWitness(const int32_t *,int32_t,int32_t,
    int32_t,int32_t,int32_t,int32_t *,int32_t *,int32_t *,int32_t *,int32_t *,int32_t *);
static int projectionWitness(const NrScenicSourceRaster *r,const NrScenicArtConfig *config) {
    const int32_t *v=config->world;
    const int32_t points[3][3]={
        {v[NR_WORLD_CAMERA_X],v[NR_WORLD_CAMERA_Y],v[NR_WORLD_CAMERA_Z]+100*256},
        {v[NR_WORLD_CAMERA_X]-12*256,v[NR_WORLD_CAMERA_Y]+3*256,v[NR_WORLD_CAMERA_Z]+30*256},
        {0,0,0}
    };
    for(int i=0;i<3;i++) {
        int32_t ocx=0,ocy=0,ocz=0,ox=0,oy=0,od=0;
        int32_t pcx=0,pcy=0,pcz=0,px=0,py=0,pd=0;
        int originalVisible=nsOriginalProjectWitness(v,r->outputWidth,r->outputHeight,
            points[i][0],points[i][1],points[i][2],&ocx,&ocy,&ocz,&ox,&oy,&od);
        int portedVisible=nrScenicSourceRasterProjectPoint(r,points[i][0],points[i][1],
            points[i][2],&pcx,&pcy,&pcz,&px,&py,&pd);
        if(originalVisible!=portedVisible||
           (originalVisible&&(ocx!=pcx||ocy!=pcy||ocz!=pcz||ox!=px||oy!=py||od!=pd))) {
            fprintf(stderr,"projection witness mismatch point%d original=%d (%d,%d,%d;%d,%d;%d) ported=%d (%d,%d,%d;%d,%d;%d)\n",
                i,originalVisible,ocx,ocy,ocz,ox,oy,od,portedVisible,pcx,pcy,pcz,px,py,pd);return 0;
        }
    }
    return 1;
}
static int compare(const char *id,int mutate) {
    if(mutate&&original.n)original.v[0].x++;
    size_t common=original.n<ported.n?original.n:ported.n,mismatch=common;
    for(size_t i=0;i<common;i++)if(!equalCoverage(original.v[i],ported.v[i])){mismatch=i;break;}
    if(mismatch!=common||original.n!=ported.n) {
        fprintf(stderr,"%s coverage trace mismatch at %zu (original=%zu ported=%zu)",id,mismatch,original.n,ported.n);
        if(mismatch<common){Coverage a=original.v[mismatch],b=ported.v[mismatch];
            fprintf(stderr," xy=%d,%d/%d,%d z=%d/%d rgb=%06x/%06x alpha=%d/%d threshold=%d/%d",
                    a.x,a.y,b.x,b.y,a.depth,b.depth,a.rgb,b.rgb,a.alpha,b.alpha,a.threshold,b.threshold);}
        fputc('\n',stderr);return 0;
    }
    return 1;
}

int main(int argc,char **argv) {
    if(argc!=2&&argc!=3){fprintf(stderr,"usage: scenic_source_raster_diff EVIDENCE_DIR [--mutate]\n");return 2;}
    int mutate=argc==3&&strcmp(argv[2],"--mutate")==0;if(argc==3&&!mutate)return 2;
    char path[1024];
    if(snprintf(path,sizeof(path),"%s/ORIGINAL-WORLD-FRAMES.tsv",argv[1])>=(int)sizeof(path))return 2;
    FILE *f=fopen(path,"r");if(!f){perror(path);return 2;}
    NsCell cells[120*40];uint32_t colors[120*40*8];int32_t depth[120*40*8];
    char line[4096];unsigned scenarios=0;
    while(fgets(line,sizeof(line),f)) {
        char *save=NULL,*token=strtok_r(line," \t\r\n",&save);if(!token)continue;
        char id[160];if(strlen(token)>=sizeof(id))return 3;strcpy(id,token);
        token=strtok_r(NULL," \t\r\n",&save);if(!token)return 3;
        errno=0;uint64_t timeMs=strtoull(token,NULL,10);if(errno)return 3;
        NrScenicArtConfig config;memset(&config,0,sizeof(config));
        for(int i=0;i<NR_WORLD_FIELD_COUNT+NR_WORLD_DETAIL_FIELD_COUNT;i++) {
            token=strtok_r(NULL," \t\r\n",&save);if(!token)return 3;
            errno=0;long value=strtol(token,NULL,10);
            if(errno||value<INT32_MIN||value>INT32_MAX)return 3;
            if(i<NR_WORLD_FIELD_COUNT)config.world[i]=(int32_t)value;
            else config.detail[i-NR_WORLD_FIELD_COUNT]=(int32_t)value;
        }
        if(strtok_r(NULL," \t\r\n",&save))return 3;
        config.hasWorldDetail=1;
        NsWorldConfig originalConfig;memcpy(originalConfig.v,config.world,sizeof(originalConfig.v));
        NsWorldDetail detail;memcpy(detail.v,config.detail,sizeof(detail.v));
        uint32_t count=(uint32_t)config.world[NR_WORLD_WIDTH]*(uint32_t)config.world[NR_WORLD_HEIGHT];
        if(!count||count>120*40)return 3;
        original.n=ported.n=0;
        int32_t rendered=nsWorldRenderDetailed(&originalConfig,timeMs,&detail,cells,count,colors,depth,count*8);
        if(rendered!=(int32_t)count){fprintf(stderr,"%s original render rejected: %d\n",id,rendered);return 4;}
        NrScenicSourceRaster raster;
        if(!nrScenicSourceRasterInit(&raster,&config,config.world[NR_WORLD_WIDTH],config.world[NR_WORLD_HEIGHT],portedCoverage,&ported)) {
            fprintf(stderr,"%s raster adapter rejected source config\n",id);return 4;
        }
        if(!projectionWitness(&raster,&config)){fprintf(stderr,"%s source camera/projection mismatch\n",id);return 5;}
        NrScenicSourceRaster invalid;
        if(nrScenicSourceRasterInit(NULL,&config,1,1,portedCoverage,&ported)||
           nrScenicSourceRasterInit(&invalid,NULL,1,1,portedCoverage,&ported)||
           nrScenicSourceRasterInit(&invalid,&config,0,1,portedCoverage,&ported)||
           nrScenicSourceRasterInit(&invalid,&config,INT32_MAX,1,portedCoverage,&ported)||
           nrScenicSourceRasterInit(&invalid,&config,1,1,NULL,&ported)) {
            fprintf(stderr,"%s invalid raster initialization was accepted\n",id);return 5;
        }
        NrScenicArtConfig invalidConfig=config;invalidConfig.world[NR_WORLD_SCENE]=5;
        if(nrScenicSourceRasterInit(&invalid,&invalidConfig,1,1,portedCoverage,&ported)||
           nrScenicSourceRasterSink(NULL)!=NULL) {
            fprintf(stderr,"%s invalid source configuration was accepted\n",id);return 5;
        }
        const NrScenicArtSink *sink=nrScenicSourceRasterSink(&raster);
        if(!nrScenicArtDraw(&config,timeMs,sink)){fprintf(stderr,"%s scenic sampler rejected source config\n",id);return 4;}
        if(!compare(id,mutate))return 5;
        scenarios++;
        if(mutate)mutate=0;
    }
    fclose(f);free(original.v);free(ported.v);
    if(scenarios!=16){fprintf(stderr,"expected 16 source scenarios, compared %u\n",scenarios);return 6;}
    puts("scenic raster: ordered original-C coverage traces matched across all 16 WASM-bound scenarios");
    return 0;
}
