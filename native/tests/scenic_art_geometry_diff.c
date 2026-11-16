/* Compare sampler callbacks to traced calls in source src/world.inc itself. */
#include "scenic_art.h"
#include "nocturne_world.h"
#include <errno.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum { MAX_CELLS = 120 * 40, MAX_LINE = 4096 };
typedef struct {
    int32_t kind;
    int32_t v[9];
    uint32_t color;
    int32_t alpha;
    int32_t radius;
} Primitive;
typedef struct { Primitive *items; size_t count, capacity; } Stream;
static Stream originalStream, samplerStream;

static void append(Stream *s, const Primitive *p) {
    if (s->count == s->capacity) {
        size_t cap = s->capacity ? s->capacity * 2 : 4096;
        Primitive *items = realloc(s->items, cap * sizeof(*items));
        if (!items) { fprintf(stderr, "primitive trace allocation failed\n"); exit(70); }
        s->items = items; s->capacity = cap;
    }
    s->items[s->count++] = *p;
}

void nsOriginalPrimitiveTrace(int kind,int32_t ax,int32_t ay,int32_t az,
                              int32_t bx,int32_t by,int32_t bz,
                              int32_t cx,int32_t cy,int32_t cz,
                              uint32_t color,int32_t alpha,int32_t radius) {
    Primitive p; memset(&p, 0, sizeof(p));
    p.kind=kind; p.v[0]=ax; p.v[1]=ay; p.v[2]=az;
    p.v[3]=bx; p.v[4]=by; p.v[5]=bz;
    p.v[6]=cx; p.v[7]=cy; p.v[8]=cz;
    p.color=color; p.alpha=alpha; p.radius=radius; append(&originalStream,&p);
}

static void triangle(void *u,int32_t ax,int32_t ay,int32_t az,
                     int32_t bx,int32_t by,int32_t bz,
                     int32_t cx,int32_t cy,int32_t cz,
                     uint32_t color,int32_t alpha) {
    (void)u; Primitive p; memset(&p,0,sizeof(p)); p.kind=0;
    p.v[0]=ax;p.v[1]=ay;p.v[2]=az;p.v[3]=bx;p.v[4]=by;p.v[5]=bz;
    p.v[6]=cx;p.v[7]=cy;p.v[8]=cz;p.color=color;p.alpha=alpha;append(&samplerStream,&p);
}
static void line(void *u,int32_t ax,int32_t ay,int32_t az,
                 int32_t bx,int32_t by,int32_t bz,uint32_t color,int32_t alpha) {
    (void)u; Primitive p; memset(&p,0,sizeof(p)); p.kind=1;
    p.v[0]=ax;p.v[1]=ay;p.v[2]=az;p.v[3]=bx;p.v[4]=by;p.v[5]=bz;
    p.color=color;p.alpha=alpha;append(&samplerStream,&p);
}
static void point(void *u,int32_t x,int32_t y,int32_t z,uint32_t color,int32_t alpha,int32_t radius) {
    (void)u; Primitive p; memset(&p,0,sizeof(p)); p.kind=2;
    p.v[0]=x;p.v[1]=y;p.v[2]=z;p.color=color;p.alpha=alpha;p.radius=radius;append(&samplerStream,&p);
}

int main(int argc,char **argv) {
    if(argc!=2){fprintf(stderr,"usage: scenic_art_geometry_diff EVIDENCE_DIR\n");return 2;}
    char inputPath[1024];
    if(snprintf(inputPath,sizeof(inputPath),"%s/ORIGINAL-WORLD-FRAMES.tsv",argv[1])>=(int)sizeof(inputPath))return 2;
    FILE *input=fopen(inputPath,"r");if(!input){perror(inputPath);return 2;}
    NsCell cells[MAX_CELLS];uint32_t colors[MAX_CELLS*8];int32_t depth[MAX_CELLS*8];
    char lineBuf[MAX_LINE];unsigned scenarios=0;
    while(fgets(lineBuf,sizeof(lineBuf),input)){
        char *save=NULL,*token=strtok_r(lineBuf," \t\r\n",&save);if(!token)continue;
        char id[160];if(strlen(token)>=sizeof(id))return 3;strcpy(id,token);
        token=strtok_r(NULL," \t\r\n",&save);if(!token)return 3;
        errno=0;uint64_t timeMs=strtoull(token,NULL,10);if(errno)return 3;
        NrScenicArtConfig config;memset(&config,0,sizeof(config));
        for(int i=0;i<NR_WORLD_FIELD_COUNT+NR_WORLD_DETAIL_FIELD_COUNT;i++){
            token=strtok_r(NULL," \t\r\n",&save);if(!token){fprintf(stderr,"%s short record\n",id);return 3;}
            errno=0;long value=strtol(token,NULL,10);if(errno||value<INT32_MIN||value>INT32_MAX)return 3;
            if(i<NR_WORLD_FIELD_COUNT)config.world[i]=(int32_t)value;
            else config.detail[i-NR_WORLD_FIELD_COUNT]=(int32_t)value;
        }
        if(strtok_r(NULL," \t\r\n",&save))return 3;
        config.hasWorldDetail=1;
        NsWorldConfig originalConfig;memcpy(originalConfig.v,config.world,sizeof(originalConfig.v));
        NsWorldDetail detail;memcpy(detail.v,config.detail,sizeof(detail.v));
        uint32_t count=(uint32_t)config.world[NR_WORLD_WIDTH]*(uint32_t)config.world[NR_WORLD_HEIGHT];
        if(!count||count>MAX_CELLS)return 3;
        originalStream.count=0;samplerStream.count=0;
        int32_t rendered=nsWorldRenderDetailed(&originalConfig,timeMs,&detail,cells,count,colors,depth,count*8);
        if(rendered!=(int32_t)count){fprintf(stderr,"%s original render rejected: %d\n",id,rendered);return 4;}
        NrScenicArtSink sink={0,triangle,line,point};
        if(!nrScenicArtDraw(&config,timeMs,&sink)){fprintf(stderr,"%s sampler rejected input\n",id);return 4;}
        size_t common=originalStream.count<samplerStream.count?originalStream.count:samplerStream.count;
        size_t mismatch=common;
        for(size_t i=0;i<common;i++)if(memcmp(&originalStream.items[i],&samplerStream.items[i],sizeof(Primitive))){mismatch=i;break;}
        if(mismatch!=common||originalStream.count!=samplerStream.count){
            fprintf(stderr,"%s primitive mismatch at %zu (original=%zu sampler=%zu)",id,mismatch,originalStream.count,samplerStream.count);
            if(mismatch<common){const Primitive *a=&originalStream.items[mismatch],*b=&samplerStream.items[mismatch];
                fprintf(stderr," kind=%d/%d color=%06x/%06x alpha=%d/%d radius=%d/%d",a->kind,b->kind,a->color,b->color,a->alpha,b->alpha,a->radius,b->radius);
                for(int k=0;k<9;k++)fprintf(stderr," v%d=%d/%d",k,a->v[k],b->v[k]);}
            fputc('\n',stderr);return 5;
        }
        scenarios++;
    }
    fclose(input);free(originalStream.items);free(samplerStream.items);
    if(scenarios!=16){fprintf(stderr,"expected 16 scenarios, compared %u\n",scenarios);return 6;}
    puts("scenic sampler: every source primitive matched instrumented original C across 16 scenarios");
    return 0;
}
