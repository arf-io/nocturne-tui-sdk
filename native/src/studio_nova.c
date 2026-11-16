#include "internal.h"
static int reject(NrContext*c,const char*message){size_t n=strlen(message);if(n>255)n=255;memcpy(c->error,message,n);c->error[n]=0;return -1;}
int nrStudioNovaProfile(const State*s,int slot){return slot>=0&&slot<(int)NR_MAX_EMITTERS&&s->emitters[slot].used&&!strcmp(nrEffectName(s->emitters[slot].effect),"weather/pearl-bloom");}
static int valid(const StudioNovaControls*b){
    if((b->used!=1&&b->used!=2)||b->novaDurationMs<100||b->novaDurationMs>30000||b->rippleSpeed<1||b->rippleSpeed>262144||b->rippleWidth<16||b->rippleWidth>8192||b->rippleOpacity>1000||b->rippleRings<1||b->rippleRings>6||b->cellAspect<500||b->cellAspect>4000||b->strength>1000||b->waveScale<64||b->waveScale>262144||b->glyphCount<1||b->glyphCount>16||b->paletteCount<1||b->paletteCount>32||b->starPaletteCount<1||b->starPaletteCount>32)return 0;
    for(uint32_t i=0;i<16;i++){uint32_t g=b->glyphs[i];if(i>=b->glyphCount){if(g)return 0;}else if(g<32||(g>=127&&g<=159)||(g>=0xd800&&g<=0xdfff)||g>0x10ffff)return 0;}
    for(uint32_t i=0;i<32;i++){if(i<b->paletteCount?b->palette[i]>0xffffff:b->palette[i]!=0)return 0;if(i<b->starPaletteCount?b->starPalette[i]>0xffffff:b->starPalette[i]!=0)return 0;}return 1;
}
int nrValidStudioNovaControls(const State*s){
    for(int i=0;i<(int)NR_MAX_EMITTERS;i++){const StudioNovaControls*b=&s->studioNovaControls[i];if(!b->used){const unsigned char*p=(const unsigned char*)b;for(size_t k=0;k<sizeof(*b);k++)if(p[k])return 0;continue;}
        if(s->schema<NR_STATE_SCHEMA_STUDIO_NOVA||(b->used==2&&s->schema<NR_STATE_SCHEMA_STUDIO_PAINT)||!nrStudioNovaProfile(s,i)||!valid(b)||b->generation!=s->emitters[i].generation||b->startUs>s->timeUs)return 0;}return 1;
}
static int integer(const Json*j,const char*key,uint32_t*out,uint32_t lo,uint32_t hi){int at=nrField(j,0,key);if(at<0)return 1;double v;if(!nrNumber(j,at,&v)||v<lo||v>hi||v!=(uint32_t)v)return 0;*out=(uint32_t)v;return 1;}
static int colors(const Json*j,const char*key,uint32_t*out,uint32_t*count){
    int at=nrField(j,0,key);if(at<0)return 1;if(j->tokens[at].type!=J_ARRAY)return 0;memset(out,0,32*sizeof(uint32_t));uint32_t n=0;
    for(int child=at+1;child<j->tokens[at].next;child=j->tokens[child].next){double v;if(n>=32||!nrNumber(j,child,&v)||v<0||v>0xffffff||v!=(uint32_t)v)return 0;out[n++]=(uint32_t)v;}
    if(!n)return 0;*count=n;return 1;
}
int nrStudioNovaCommand(NrContext*c,State*s,const Json*j){
    if(s->schema<NR_STATE_SCHEMA_STUDIO_NOVA)return reject(c,"Studio nova requires schema63");int remove=nrEqual(j,nrField(j,0,"op"),"remove-studio-style");
    if(!nrAllowed(j,0,remove?"op id":"op id seed novaDurationMs rippleSpeed rippleWidth rippleOpacity rippleRings cellAspect strength waveScale glyphs palette starPalette paint"))return reject(c,"Unknown Studio nova setting");
    uint32_t id=0;if(nrField(j,0,"id")<0||!integer(j,"id",&id,1,65535))return reject(c,"Studio nova emitter id required");int slot=nrFindEmitter(s,(int)id);if(!nrStudioNovaProfile(s,slot))return reject(c,"Studio nova requires pearl-bloom emitter");
    if(remove){memset(&s->studioNovaControls[slot],0,sizeof(StudioNovaControls));return 0;}
    StudioNovaControls b=s->studioNovaControls[slot];if(!b.used)b=(StudioNovaControls){.used=2,.generation=s->emitters[slot].generation,.seed=2030,.novaDurationMs=3600,.rippleSpeed=2560,.rippleWidth=384,.rippleOpacity=280,.rippleRings=2,.cellAspect=2000,.strength=850,.waveScale=6144,.glyphCount=5,.paletteCount=5,.starPaletteCount=6,.glyphs={0xb7,0x2219,'*',0x2726,0x2727},.palette={0x28304f,0x785c89,0x367876,0xae7357,0x504565},.starPalette={0xb6a4c4,0x9fb9b0,0xc7bca7,0x9cacca,0xc6a0aa,0xadbdbb},.startUs=s->timeUs};
    int paint=nrField(j,0,"paint");if(paint>=0){if(nrEqual(j,paint,"source"))b.used=2;else if(nrEqual(j,paint,"material"))b.used=1;else return reject(c,"Invalid Studio painting mode");}
    if(b.used==2&&s->schema<NR_STATE_SCHEMA_STUDIO_PAINT)return reject(c,"Studio painting requires schema78");
#define FIELD(name,lo,hi) if(!integer(j,#name,&b.name,lo,hi))return reject(c,"Invalid Studio nova integer")
    FIELD(seed,0,0xffffffffu);FIELD(novaDurationMs,100,30000);FIELD(rippleSpeed,1,262144);FIELD(rippleWidth,16,8192);FIELD(rippleOpacity,0,1000);FIELD(rippleRings,1,6);FIELD(cellAspect,500,4000);FIELD(strength,0,1000);FIELD(waveScale,64,262144);
#undef FIELD
    int at=nrField(j,0,"glyphs");if(at>=0){memset(b.glyphs,0,sizeof(b.glyphs));int n=nrDecode(j,at,b.glyphs,16);if(n<1)return reject(c,"Studio printable glyphs required");b.glyphCount=(uint32_t)n;}
    if(!colors(j,"palette",b.palette,&b.paletteCount)||!colors(j,"starPalette",b.starPalette,&b.starPaletteCount)||!valid(&b))return reject(c,"Invalid Studio nova palette or glyphs");s->studioNovaControls[slot]=b;return 0;
}
static uint32_t smooth(uint32_t p){if(p>1000)p=1000;return (uint32_t)((uint64_t)p*p*(3000-2*p)/1000000);}
static uint64_t distanceQ8(int64_t x,int64_t y){uint64_t v=(uint64_t)(x*x+y*y),root=0,bit=(uint64_t)1<<62;while(bit>v)bit>>=2;while(bit){if(v>=root+bit){v-=root+bit;root=(root>>1)+bit;}else root>>=1;bit>>=2;}return root;}
static uint32_t mix(uint32_t a,uint32_t b,uint32_t p){uint32_t out=0;for(int shift=0;shift<=16;shift+=8){int aa=(a>>shift)&255,bb=(b>>shift)&255;out|=(uint32_t)(aa+(bb-aa)*(int)p/1000)<<shift;}return out;}
int nrStudioNovaSample(const State*s,int slot,StudioNovaSample*out){
    if(!out||!nrStudioNovaProfile(s,slot)||!s->studioNovaControls[slot].used)return 0;const StudioNovaControls*b=&s->studioNovaControls[slot];memset(out,0,sizeof(*out));out->coreColor=b->starPalette[b->seed%b->starPaletteCount];
    uint64_t age=(s->timeUs-b->startUs)/1000;if(age>=b->novaDurationMs)return 1;uint32_t phase=(uint32_t)(age*1000/b->novaDurationMs);
    out->envelope=smooth(phase<240?phase*1000/240:(1000-phase)*1000/760);out->glyphIndex=out->envelope*(b->glyphCount-1)/1000;out->glyph=b->glyphs[out->glyphIndex];return 1;
}
uint32_t nrStudioNovaRing(const StudioNovaControls*b,uint64_t age,int64_t x,int64_t y){
    if(age>=b->novaDurationMs)return 0;y=y*b->cellAspect/1000;uint64_t distance=distanceQ8(x,y),radius=age*b->rippleSpeed/1000;uint32_t fade=smooth(1000-(uint32_t)(age*1000/b->novaDurationMs)),peak=0;
    for(uint32_t k=0;k<b->rippleRings;k++){uint64_t offset=(uint64_t)k*b->rippleWidth*4;if(radius<offset)continue;uint64_t r=radius-offset,delta=distance>r?distance-r:r-distance;
        if(delta<b->rippleWidth){uint32_t a=smooth(1000-(uint32_t)(delta*1000/b->rippleWidth));a=a*fade/1000;a=a*b->strength/1000;a=a*b->rippleOpacity/1000;a=a*1000/(1000+k*420);if(a>peak)peak=a;}}
    return peak;
}
uint32_t nrStudioNovaRingColor(const StudioNovaControls*b,int64_t x,int64_t y){
    uint64_t distance=distanceQ8(x,y*b->cellAspect/1000);uint32_t phase=(uint32_t)((b->seed%1024+distance*1024/b->waveScale)%1024),p=phase*b->paletteCount,index=p/1024,f=smooth((p%1024)*1000/1024);
    return mix(b->palette[index],b->palette[(index+1)%b->paletteCount],f);
}

int nrStudioNovaCenter(const State*s,int slot,double out[3]){
    if(!out||!nrStudioNovaProfile(s,slot)||!s->studioNovaControls[slot].used)return 0;
    int width,height;nrSceneViewport(s,&width,&height);
    Projection p;nrProjection(s,width,height,&p);int visible=nrProject(&p,s->emitters[slot].position,&out[0],&out[1],&out[2]);
    if(visible){out[0]*=.5;out[1]*=.25;}return visible;
}
/* Original nsStageRender's two half-cell samples and EffectPainter.local's
 * screen-tile compositor. Each tile cell is independent, so it can be streamed
 * in the original row order without a second frame allocation. */
static uint32_t mixJs(uint32_t a,uint32_t b,double p){
    p=nrClamp(p,0,1);uint32_t out=0;for(int shift=0;shift<=16;shift+=8){double aa=(a>>shift)&255,bb=(b>>shift)&255;out|=(uint32_t)nrFloor(aa*(1-p)+bb*p+.5)<<shift;}return out;
}
static uint32_t flatJs(const NrCell*c){return c->glyph==0x2580||c->glyph==0x2584||c->glyph==0x258c||c->glyph==0x2590?mixJs(c->foreground,c->background,.5):c->background;}
static uint32_t sourceGlyph(uint32_t g){
    if((g>=32&&g<=126)||(g>=0x2190&&g<=0x22ff)||(g>=0x2500&&g<=0x25ff)||(g>=0x2800&&g<=0x28ff)||g==0x2726||g==0x2727||g==0x203a||g==0x2039||g==0xd7||g==0xb0||g==0xb7||g==0x2022||g==0x207a)return g;return '?';
}
static uint32_t sourceSample(const StudioNovaControls*b,uint64_t age,int64_t x,int64_t y){
    uint32_t opacity=nrStudioNovaRing(b,age,x,y);return opacity?mix(0,nrStudioNovaRingColor(b,x,y),opacity):0;
}
void nrStudioOriginalRippleTileCell(const StudioNovaControls*b,uint64_t age,int x,int y,NrCell*out){
    int64_t dx=(x-40)*256,dy=(y-22)*256;
    *out=(NrCell){.glyph=0x2580,.foreground=sourceSample(b,age,dx,dy-64),.background=sourceSample(b,age,dx,dy+64),.id=0};
}
static void sourcePaint(NrContext*c,const State*s,int slot,const double center[3],double weight){
    if(weight<=0)return;const StudioNovaControls*b=&s->studioNovaControls[slot];uint64_t age=(s->timeUs-b->startUs)/1000;
    StudioNovaSample core;nrStudioNovaSample(s,slot,&core);
    for(int y=0;y<44;y++)for(int x=0;x<80;x++){
        NrCell tile;nrStudioOriginalRippleTileCell(b,age,x,y,&tile);uint32_t glyph=tile.glyph,fg=tile.foreground,bg=tile.background;
        if(x==40&&y==22){bg=mix(bg,fg,500);glyph=sourceGlyph(core.glyph);fg=mix(bg,core.coreColor,core.envelope);}
        if(!bg&&(glyph==32||!fg))continue;
        double xx=nrFloor(center[0]+x-40+.5),yy=nrFloor(center[1]+y-22+.5);if(xx<0||yy<0||xx>=s->width||yy>=s->height)continue;
        NrCell*d=&c->cells[(size_t)yy*s->width+(size_t)xx];if(bg)d->background=mixJs(flatJs(d),bg,.7*weight);
        if(glyph!=32&&fg){uint32_t under=flatJs(d);d->glyph=glyph;d->foreground=mixJs(under,fg,.95*weight);d->background=under;d->id=0;}
    }
}

void nrDrawStudioNova(NrContext*c,const Projection*projection){
    const State*s=nrView(c);
    for(int slot=0;slot<(int)NR_MAX_EMITTERS;slot++){
        if(!s->studioNovaControls[slot].used)continue;const StudioNovaControls*b=&s->studioNovaControls[slot];uint64_t age=(s->timeUs-b->startUs)/1000;if(age>=b->novaDurationMs)continue;
        double center[3];if(!nrProject(projection,s->emitters[slot].position,&center[0],&center[1],&center[2]))continue;center[0]*=.5;center[1]*=.25;
        const Emitter*e=&s->emitters[slot];double materialAlpha;nrUseMaterial(c,e->material);c->characterOwner=0;nrPaint(s,e->material,s->timeUs,e->id,&materialAlpha);double alpha=e->alpha*materialAlpha;
        if(b->used==2){sourcePaint(c,s,slot,center,alpha);continue;}
        /* Radius/extent is bounded by authored source controls. Clip before casts. */
        double extent=((double)age*b->rippleSpeed/1000+b->rippleWidth)/256;
        int left=(int)nrFloor(nrClamp(center[0]-extent,0,s->width)),right=(int)nrClamp(center[0]+extent+1,0,s->width);
        double vertical=extent*1000/b->cellAspect;
        int top=(int)nrFloor(nrClamp(center[1]-vertical,0,s->height)),bottom=(int)nrClamp(center[1]+vertical+1,0,s->height);
        for(int y=top;y<bottom;y++)for(int x=left;x<right;x++){
            int64_t dx=(int64_t)((x+.5-center[0])*256),dy=(int64_t)((y+.5-center[1])*256);
            uint32_t opacity=nrStudioNovaRing(b,age,dx,dy);if(opacity)nrCellBackground(c,x,y,nrStudioNovaRingColor(b,dx,dy),alpha*opacity/1000);
        }
        StudioNovaSample sample;nrStudioNovaSample(s,slot,&sample);double x=nrFloor(center[0]),y=nrFloor(center[1]);
        if(sample.envelope&&x>=0&&y>=0&&x<s->width&&y<s->height)nrIndexedGlyph(c,(int)x,(int)y,sample.glyph,sample.coreColor,alpha*sample.envelope/1000,0,0);
    }c->paintBlend=0;
}
