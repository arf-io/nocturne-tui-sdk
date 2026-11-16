#include "../src/scenic_art.h"

#include <stdio.h>
#include <string.h>

typedef struct {
    uint64_t triangles, lines, points, hash;
    int32_t min[3], max[3];
    uint8_t minRgb[3],maxRgb[3];
    uint16_t colorMask;
} Observation;
static const uint32_t WATCHED_COLORS[]={0x35434d,0x86cfc5,0xdde9d7,0x142c40,0x79bcb8,
    0x343f51,0xdfbc9c,0x255361,0x9ac7b8,0x07090f,0xebbb7a,0xf5e7d0};

static uint64_t fold(uint64_t h, uint32_t x) {
    h ^= x;
    return h * UINT64_C(1099511628211);
}

static void vertex(Observation *o, int32_t x, int32_t y, int32_t z,
                   uint32_t color, int32_t alpha, uint32_t kind) {
    int32_t p[3] = {x,y,z};
    for (int k=0;k<3;k++) {
        if (p[k] < o->min[k]) o->min[k]=p[k];
        if (p[k] > o->max[k]) o->max[k]=p[k];
        o->hash=fold(o->hash,(uint32_t)p[k]);
    }
    uint8_t rgb[3]={(uint8_t)(color>>16),(uint8_t)(color>>8),(uint8_t)color};
    for(int k=0;k<3;k++){if(rgb[k]<o->minRgb[k])o->minRgb[k]=rgb[k];if(rgb[k]>o->maxRgb[k])o->maxRgb[k]=rgb[k];}
    o->hash=fold(o->hash,color);o->hash=fold(o->hash,(uint32_t)alpha);o->hash=fold(o->hash,kind);
    for(uint16_t i=0;i<(uint16_t)(sizeof(WATCHED_COLORS)/sizeof(WATCHED_COLORS[0]));i++)
        if(WATCHED_COLORS[i]==color)o->colorMask|=(uint16_t)(1u<<i);
}

static void triangle(void *u,int32_t ax,int32_t ay,int32_t az,
                     int32_t bx,int32_t by,int32_t bz,
                     int32_t cx,int32_t cy,int32_t cz,
                     uint32_t color,int32_t alpha) {
    Observation *o=u;o->triangles++;
    vertex(o,ax,ay,az,color,alpha,1);vertex(o,bx,by,bz,color,alpha,1);vertex(o,cx,cy,cz,color,alpha,1);
}
static void line(void *u,int32_t ax,int32_t ay,int32_t az,int32_t bx,int32_t by,int32_t bz,
                 uint32_t color,int32_t alpha) {
    Observation *o=u;o->lines++;vertex(o,ax,ay,az,color,alpha,2);vertex(o,bx,by,bz,color,alpha,2);
}
static void point(void *u,int32_t x,int32_t y,int32_t z,uint32_t color,int32_t alpha,int32_t radius) {
    Observation *o=u;o->points++;vertex(o,x,y,z,color,alpha,3);o->hash=fold(o->hash,(uint32_t)radius);
}
static NrScenicArtSink sink(Observation *o) { return (NrScenicArtSink){o,triangle,line,point}; }
static void init(Observation *o) {
    memset(o,0,sizeof(*o));o->hash=UINT64_C(1469598103934665603);
    for(int k=0;k<3;k++){o->min[k]=INT32_MAX;o->max[k]=INT32_MIN;}
    for(int k=0;k<3;k++)o->minRgb[k]=255;
}

/* Exact rc2 defaults: WORLD_FIELDS values are stored at their declared scale. */
static NrScenicArtConfig defaults(int scene) {
    NrScenicArtConfig c={0};
    const int32_t world[NR_WORLD_FIELD_COUNT]={
        120,40,scene,-68*256,48*256,-96*256,35*256,-22*256,0,62*256,
        1,145*256,1000,0,2030,700,12*256,1,940,1053726,0,0,0,1
    };
    const int32_t detail[NR_WORLD_DETAIL_FIELD_COUNT]={358,8704,5632,480,430,620,1000,1};
    memcpy(c.world,world,sizeof(world));memcpy(c.detail,detail,sizeof(detail));c.hasWorldDetail=1;return c;
}
static int draw(const NrScenicArtConfig *c,uint64_t ms,Observation *o) {
    NrScenicArtSink s=sink(o);return nrScenicArtDraw(c,ms,&s);
}
static int hasColor(const Observation *o,uint32_t color) {
    for(uint16_t i=0;i<(uint16_t)(sizeof(WATCHED_COLORS)/sizeof(WATCHED_COLORS[0]));i++)
        if(WATCHED_COLORS[i]==color)return (o->colorMask&(uint16_t)(1u<<i))!=0;
    return 0;
}
static uint64_t count(const Observation *o) { return o->triangles+o->lines+o->points; }

int main(void) {
    const int scenes[]={0,3,1,4,2};
    Observation baseline[5];uint64_t signatures[5];
    for(int i=0;i<5;i++) {
        NrScenicArtConfig c=defaults(scenes[i]);init(&baseline[i]);
        Observation repeat;init(&repeat);
        if(!nrScenicArtValidate(&c)||!draw(&c,2000,&baseline[i])||!draw(&c,2000,&repeat)) {
            fprintf(stderr,"rc2 scene index %d rejected its field defaults\n",scenes[i]);return 1;
        }
        Observation *o=&baseline[i];
        if(!count(o)||o->hash!=repeat.hash||o->triangles!=repeat.triangles||
           o->lines!=repeat.lines||o->points!=repeat.points) {
            fprintf(stderr,"scene %d empty or non-repeatable at absolute 2000ms\n",scenes[i]);return 2;
        }
        if(o->triangles>200000||o->lines>200000||o->points>200000) return 3;
        signatures[i]=o->hash;
        for(int k=0;k<3;k++)if(o->min[k]>=o->max[k])return 4;
        if(scenes[i]==0&&(!hasColor(o,0xdde9d7)||o->minRgb[0]>80||o->maxRgb[1]<120))return 5;
        if(scenes[i]==3&&(o->minRgb[0]>45||o->minRgb[1]>70||o->minRgb[2]>95||!o->lines))return 6;
        if(scenes[i]==1&&(!hasColor(o,0x343f51)||!hasColor(o,0xdfbc9c)))return 7;
        if(scenes[i]==4&&(o->maxRgb[2]<90||o->minRgb[0]>60))return 8;
        if(scenes[i]==2&&(!hasColor(o,0x07090f)||o->maxRgb[0]<180||
            o->maxRgb[1]<160||o->maxRgb[2]<150||!o->points))return 9;
    }
    for(int i=0;i<5;i++)for(int j=i+1;j<5;j++)if(signatures[i]==signatures[j])return 10;
    NrScenicArtConfig noViewportCap=defaults(NR_SCENIC_TIDAL_GLASS);
    noViewportCap.world[NR_WORLD_WIDTH]=4096;noViewportCap.world[NR_WORLD_HEIGHT]=2048;
    Observation viewportA;init(&viewportA);
    if(!draw(&noViewportCap,2000,&viewportA)||viewportA.hash!=signatures[1])return 101;

    /* Absolute seeking and original per-scene time semantics. */
    const int moving[]={0,3,4,2};
    for(unsigned i=0;i<sizeof(moving)/sizeof(moving[0]);i++) {
        NrScenicArtConfig c=defaults(moving[i]);Observation a,b,seek;
        init(&a);init(&b);init(&seek);
        if(!draw(&c,2000,&a)||!draw(&c,3000,&b)||a.hash==b.hash)return 11;
        if(!draw(&c,77,&seek))return 12;
        init(&seek);if(!draw(&c,2000,&seek)||seek.hash!=a.hash)return 12;
        Observation direct;init(&direct);if(!draw(&c,2000,&direct)||direct.hash!=a.hash)return 13;
    }
    NrScenicArtConfig c=defaults(NR_SCENIC_COPPER_CAUSEWAY);Observation a,b;
    init(&a);init(&b);if(!draw(&c,2000,&a)||!draw(&c,3000,&b)||a.hash!=b.hash)return 14;
    c.world[NR_WORLD_TRAVEL]=4*256;init(&b);if(!draw(&c,2000,&b)||a.hash==b.hash)return 15;
    c=defaults(NR_SCENIC_PEARL_CASCADE);c.world[NR_WORLD_FLOW]=0;init(&a);init(&b);
    if(!draw(&c,2000,&a)||!draw(&c,3000,&b)||a.hash!=b.hash)return 16;
    c=defaults(NR_SCENIC_TIDAL_GLASS);c.detail[NR_WORLD_DETAIL_WAVE_SPEED]=0;init(&a);init(&b);
    if(!draw(&c,2000,&a)||!draw(&c,3000,&b)||a.hash!=b.hash)return 17;
    c=defaults(NR_SCENIC_TIDAL_GLASS);c.detail[NR_WORLD_DETAIL_WAVE_HEIGHT]=0;init(&b);
    if(!draw(&c,2000,&b)||b.hash==signatures[1])return 18;
    c=defaults(NR_SCENIC_TIDAL_GLASS);c.hasWorldDetail=0;c.detail[NR_WORLD_DETAIL_WAVE_SPEED]=0;
    init(&a);init(&b);if(!draw(&c,2000,&a)||!draw(&c,3000,&b)||a.hash==b.hash)return 181;
    c=defaults(NR_SCENIC_TIDAL_GLASS);c.detail[NR_WORLD_DETAIL_WAVE_SPEED]=0;
    init(&a);init(&b);if(!draw(&c,2000,&a)||!draw(&c,3000,&b)||a.hash!=b.hash)return 182;
    c=defaults(NR_SCENIC_RED_SHIFT);c.world[NR_WORLD_DISC_TILT]=35*256;init(&b);
    if(!draw(&c,2000,&b)||b.hash==signatures[4])return 19;
    c=defaults(NR_SCENIC_RED_SHIFT);c.world[NR_WORLD_YAW]=-15*256;init(&b);
    if(!draw(&c,2000,&b)||b.hash==signatures[4])return 191;
    c=defaults(NR_SCENIC_PEARL_CASCADE);c.world[NR_WORLD_WATER_ALPHA]=400;init(&b);
    if(!draw(&c,2000,&b)||b.hash==signatures[0])return 192;
    struct Variation { int scene,field,value; } variations[]={
        {NR_SCENIC_PEARL_CASCADE,NR_WORLD_SEED,97},
        {NR_SCENIC_PEARL_CASCADE,NR_WORLD_INK,0xc5d7e8},
        {NR_SCENIC_PEARL_CASCADE,NR_WORLD_ACCENT,0x68b9d5},
        {NR_SCENIC_PEARL_CASCADE,NR_WORLD_SECONDARY,0x24384a},
        {NR_SCENIC_TIDAL_GLASS,NR_WORLD_FLOW,1800},
        {NR_SCENIC_TIDAL_GLASS,NR_WORLD_ACCENT,0x6aa6d0},
        {NR_SCENIC_COPPER_CAUSEWAY,NR_WORLD_TRAVEL,3*256},
        {NR_SCENIC_COPPER_CAUSEWAY,NR_WORLD_ACCENT,0xc59a67},
        {NR_SCENIC_SILT,NR_WORLD_ACCENT,0x7f937b},
        {NR_SCENIC_RED_SHIFT,NR_WORLD_REDSHIFT,250},
        {NR_SCENIC_RED_SHIFT,NR_WORLD_DETAIL,2},
        {NR_SCENIC_RED_SHIFT,NR_WORLD_SEED,97},
        {NR_SCENIC_RED_SHIFT,NR_WORLD_ACCENT,0x73c5d1}
    };
    const int sceneOrder[]={0,3,1,4,2};
    for(unsigned i=0;i<sizeof(variations)/sizeof(variations[0]);i++) {
        c=defaults(variations[i].scene);c.world[variations[i].field]=variations[i].value;
        int bi=0;while(sceneOrder[bi]!=variations[i].scene)bi++;
        init(&b);if(!draw(&c,2000,&b)||b.hash==signatures[bi])return 193;
    }
    const int detailVariation[NR_WORLD_DETAIL_FIELD_COUNT]={0,12000,0,900,900,0,0,0};
    for(int i=0;i<NR_WORLD_DETAIL_JOIN_RIVER;i++) {
        c=defaults(NR_SCENIC_TIDAL_GLASS);c.detail[i]=detailVariation[i];
        init(&b);if(!draw(&c,2000,&b)||b.hash==signatures[1])return 194+i;
    }
    c=defaults(NR_SCENIC_PEARL_CASCADE);c.detail[NR_WORLD_DETAIL_JOIN_RIVER]=0;init(&b);
    if(!draw(&c,2000,&b)||b.hash==signatures[0])return 202;

    /* Validate all exact rc2 domains before any callback; rejection is atomic. */
    const int32_t wmin[24]={0,0,0,-25600000,-25600000,-25600000,-92160,-22784,-92160,3840,0,4096,0,-2048000000,0,0,-21760,0,0,0,0,0,0,0};
    const int32_t wmax[24]={512,256,4,25600000,25600000,25600000,92160,22784,92160,35840,1,256000,8000,2048000000,2147483647,1000,21760,2,1000,16777215,16777215,16777215,16777215,1};
    /* Draw receives the current canonical camera domain, while authored
       source configuration keeps the exact RC2 domains above (f4b5c25). */
    const int32_t vmin[24]={0,0,0,-25600000,-25600000,-25600000,-9216000,-23014,-9216000,2560,0,26,0,-2048000000,0,0,-21760,0,0,0,0,0,0,0};
    const int32_t vmax[24]={INT32_MAX,INT32_MAX,4,25600000,25600000,25600000,9216000,23014,9216000,38400,1,512000,8000,2048000000,2147483647,1000,21760,2,1000,16777215,16777215,16777215,16777215,1};
    const int32_t dmin[8]={0,2048,-92160,0,0,0,0,0};
    const int32_t dmax[8]={2048,30720,92160,1000,1000,1000,4000,1};
    for(int i=0;i<24;i++)for(int side=0;side<(i<2?1:(wmax[i]<INT32_MAX?2:1));side++) {
        c=defaults(NR_SCENIC_TIDAL_GLASS);c.world[i]=side?wmax[i]+1:wmin[i]-1;
        NrScenicArtConfig before=c;
        Observation rejected;init(&rejected);NrScenicArtSink s=sink(&rejected);
        if(nrScenicArtValidate(&c)||memcmp(&c,&before,sizeof(c)))return 20;
        int validView=c.world[i]>=vmin[i]&&c.world[i]<=vmax[i];
        if(nrScenicArtValidateView(&c)!=validView)return 203;
        if(nrScenicArtDraw(&c,0,&s)!=validView||
           (validView?!count(&rejected):count(&rejected))||memcmp(&c,&before,sizeof(c)))return 204;
    }
    for(int i=0;i<24;i++)for(int side=0;side<(vmax[i]<INT32_MAX?2:1);side++) {
        c=defaults(NR_SCENIC_TIDAL_GLASS);c.world[i]=side?vmax[i]+1:vmin[i]-1;
        NrScenicArtConfig before=c;Observation rejected;init(&rejected);NrScenicArtSink s=sink(&rejected);
        if(nrScenicArtValidateView(&c)||nrScenicArtDraw(&c,0,&s)||count(&rejected)||memcmp(&c,&before,sizeof(c)))return 205;
    }
    for(int i=0;i<8;i++)for(int side=0;side<2;side++) {
        c=defaults(NR_SCENIC_TIDAL_GLASS);c.detail[i]=side?dmax[i]+1:dmin[i]-1;
        NrScenicArtConfig before=c;
        Observation rejected;init(&rejected);NrScenicArtSink s=sink(&rejected);
        if(nrScenicArtValidate(&c)||nrScenicArtDraw(&c,0,&s)||count(&rejected)||memcmp(&c,&before,sizeof(c)))return 21;
    }
    c=defaults(NR_SCENIC_TIDAL_GLASS);c.hasWorldDetail=2;Observation invalidDetail;init(&invalidDetail);
    NrScenicArtSink invalidSink=sink(&invalidDetail);
    if(nrScenicArtValidate(&c)||nrScenicArtDraw(&c,0,&invalidSink)||count(&invalidDetail))return 211;
    c=defaults(NR_SCENIC_TIDAL_GLASS);NrScenicArtSink missing=sink(&a);Observation rejected;init(&rejected);
    missing.user=&rejected;missing.triangle=NULL;
    if(nrScenicArtDraw(&c,0,&missing)||count(&rejected))return 22;
    missing=sink(&rejected);missing.line=NULL;if(nrScenicArtDraw(&c,0,&missing)||count(&rejected))return 23;
    missing=sink(&rejected);missing.point=NULL;if(nrScenicArtDraw(&c,0,&missing)||count(&rejected))return 24;
    NrScenicArtSink absent={0};if(nrScenicArtDraw(&c,0,&absent))return 25;
    init(&rejected);NrScenicArtSink s=sink(&rejected);
    if(nrScenicArtDraw(&c,UINT64_C(9007199254740992),&s)||count(&rejected))return 26;
    Observation largeA,largeB;init(&largeA);init(&largeB);
    if(!draw(&c,UINT64_C(9007199254740991),&largeA)||
       !draw(&c,UINT64_C(9007199254740991),&largeB)||largeA.hash!=largeB.hash)return 27;

    puts("scenic-art: rc2 fixed-point configs, five source scene families, seek/motion and atomic rejection contracts recorded");
    return 0;
}
