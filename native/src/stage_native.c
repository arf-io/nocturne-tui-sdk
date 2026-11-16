#include "internal.h"
#include "source_stage_components.h"

#include <limits.h>
#include <string.h>

enum { K=0, LEGACY=1, X=2, Y=3, W=4, H=5, STATE=6, VALUE=7,
       FROM=8, CHANGED_LO=9, CHANGED_HI=10, DURATION=11, FG=12, BG=13,
       FGA=14, BGA=15, STYLE=16, TOFF=17, TLEN=18, DOFF=19, DLEN=20,
       HSTEP=21, HSPEED=22, HBASE=23, REVEAL=24, SAT=26, BRIGHT=27,
       ANIM=28, GLYPH=29, ZOOM=30 };

static const char *const kinds[14] = {
    "text", "box", "rule", "button", "item", "cursor", "progress",
    "bars", "pie", "donut", "scatter", "line", "digits", "edge"
};
static int fail(NrContext *c, const char *message) {
    size_t n=strlen(message); if(n>=sizeof(c->error))n=sizeof(c->error)-1;
    memcpy(c->error,message,n);c->error[n]=0;return -1;
}
static int parseInt(const Json *j,int obj,const char *name,int32_t *out,
                    int32_t minimum,int32_t maximum) {
    int token=nrField(j,obj,name); if(token<0)return 1;
    double d;if(!nrNumber(j,token,&d)||d<minimum||d>maximum||d!=(int64_t)d)return 0;
    *out=(int32_t)d;return 1;
}
static int parseKind(const Json*j,int obj,int32_t *kind) {
    int token=nrField(j,obj,"kind");if(token<0)return 0;
    for(int i=0;i<14;i++)if(nrEqual(j,token,kinds[i])){*kind=i;return 1;}
    return 0;
}
static int parseData(const Json*j,int token,int32_t*out,uint32_t*count) {
    if(token<0)return 1;
    if(j->tokens[token].type!=J_ARRAY||j->tokens[token].count>NR_SOURCE_STAGE_DATA_CAPACITY)return 0;
    uint32_t n=0;
    for(int at=token+1;at<j->tokens[token].next;at=j->tokens[at].next){
        double d;if(!nrNumber(j,at,&d)||d<-1000000||d>1000000||d!=(int64_t)d)return 0;
        out[n++]=(int32_t)d;
    }
    *count=n;return 1;
}
static int parseNode(NrContext*c,const Json*j,SourceStageComponentRecord *r,
                     uint32_t *text,uint32_t *textCount,int32_t *data,uint32_t *dataCount) {
    if(!nrAllowed(j,0,"op id kind legacyFlags x y width height state value fromValue changedMs durationMs fg bg fgOpacity bgOpacity style text data hueStep hueSpeed hueBase revealMs hueSaturation hueBrightness colorAnimation glyph zoom materialId"))return fail(c,"Unknown source stage field");
    memset(r,0,sizeof(*r));
    int32_t*n=r->node;
    n[FG]=0xe2d9c9;n[BG]=0x11100e;n[FGA]=1000;n[HSTEP]=17;n[HSPEED]=24;n[SAT]=620;n[BRIGHT]=830;n[ZOOM]=1;
    if(!parseKind(j,0,&n[K]))return fail(c,"Unknown source stage kind");
    struct Field {const char*name;int word;int32_t lo,hi;} fields[]={
        {"legacyFlags",LEGACY,0,INT32_MAX},{"x",X,-4096,4096},{"y",Y,-4096,4096},
        {"width",W,1,INT32_MAX/2},{"height",H,1,INT32_MAX/4},{"state",STATE,0,3},
        {"value",VALUE,-1000000,1000000},{"fromValue",FROM,-1000000,1000000},
        {"durationMs",DURATION,0,3600000},{"fg",FG,0,0xffffff},{"bg",BG,0,0xffffff},
        {"fgOpacity",FGA,0,1000},{"bgOpacity",BGA,0,1000},{"style",STYLE,0,15},
        {"hueStep",HSTEP,-3600,3600},{"hueSpeed",HSPEED,-3600,3600},
        {"hueBase",HBASE,-360000,360000},{"revealMs",REVEAL,0,3600000},
        {"hueSaturation",SAT,0,1000},{"hueBrightness",BRIGHT,0,1000},
        {"colorAnimation",ANIM,0,3},{"glyph",GLYPH,0,0x10ffff},{"zoom",ZOOM,1,4}
    };
    for(size_t i=0;i<sizeof(fields)/sizeof(fields[0]);i++)
        if(!parseInt(j,0,fields[i].name,&n[fields[i].word],fields[i].lo,fields[i].hi))return fail(c,"Invalid source stage scalar");
    int changed=nrField(j,0,"changedMs");
    if(changed>=0){double d;if(!nrNumber(j,changed,&d)||d<0||d>9007199254740991.0||d!=(uint64_t)d)return fail(c,"Invalid source stage changedMs");uint64_t ms=(uint64_t)d;n[CHANGED_LO]=(int32_t)(uint32_t)ms;n[CHANGED_HI]=(int32_t)(uint32_t)(ms>>32);}
    int t=nrField(j,0,"text");
    if(t>=0){if(j->tokens[t].type!=J_STRING)return fail(c,"Source stage text must be a string");int decoded=nrDecode(j,t,text,NR_SOURCE_STAGE_TEXT_CAPACITY);if(decoded<0)return fail(c,"Invalid source stage text");*textCount=(uint32_t)decoded;}
    int d=nrField(j,0,"data");if(!parseData(j,d,data,dataCount))return fail(c,"Invalid source stage data");
    int32_t materialId=0;
    if(!parseInt(j,0,"materialId",&materialId,0,NR_MATERIALS))return fail(c,"Invalid source stage material");
    r->materialId=(uint32_t)materialId;
    n[TLEN]=(int32_t)*textCount;n[DLEN]=(int32_t)*dataCount;
    return 0;
}
static void packPools(SourceStageState *state,int removeSlot,const SourceStageComponentRecord *replacement,
                      const uint32_t *newText,uint32_t newTextCount,
                      const int32_t *newData,uint32_t newDataCount) {
    uint32_t ti=state->textCount,di=state->dataCount;
    uint32_t out=state->count;
    if(removeSlot>=0){
        SourceStageComponentRecord *old=&state->components[removeSlot];
        uint32_t oldText=(uint32_t)old->node[TLEN],oldData=(uint32_t)old->node[DLEN];
        uint32_t textAt=(uint32_t)old->node[TOFF],dataAt=(uint32_t)old->node[DOFF];
        uint32_t textSource=textAt+oldText,dataSource=dataAt+oldData;
        uint32_t textSuffix=ti-textSource,dataSuffix=di-dataSource;
        uint32_t textInsert=replacement?newTextCount:0,dataInsert=replacement?newDataCount:0;
        if(textSuffix)memmove(state->text+textAt+textInsert,state->text+textSource,(size_t)textSuffix*sizeof(state->text[0]));
        if(dataSuffix)memmove(state->data+dataAt+dataInsert,state->data+dataSource,(size_t)dataSuffix*sizeof(state->data[0]));
        if(replacement){
            SourceStageComponentRecord copy=*replacement;
            copy.node[TOFF]=(int32_t)textAt;copy.node[DOFF]=(int32_t)dataAt;
            if(textInsert)memcpy(state->text+textAt,newText,(size_t)textInsert*sizeof(state->text[0]));
            if(dataInsert)memcpy(state->data+dataAt,newData,(size_t)dataInsert*sizeof(state->data[0]));
            state->components[removeSlot]=copy;
        }else{
            memmove(state->components+removeSlot,state->components+removeSlot+1,
                    (size_t)(state->count-(uint32_t)removeSlot-1)*sizeof(state->components[0]));
            out--;
        }
        int64_t textDelta=(int64_t)textInsert-(int64_t)oldText;
        int64_t dataDelta=(int64_t)dataInsert-(int64_t)oldData;
        for(uint32_t i=(uint32_t)removeSlot+(replacement?1u:0u);i<out;i++){
            state->components[i].node[TOFF]=(int32_t)((int64_t)state->components[i].node[TOFF]+textDelta);
            state->components[i].node[DOFF]=(int32_t)((int64_t)state->components[i].node[DOFF]+dataDelta);
        }
        ti=(uint32_t)((int64_t)ti+textDelta);di=(uint32_t)((int64_t)di+dataDelta);
    }else if(replacement){
        SourceStageComponentRecord copy=*replacement;copy.node[TOFF]=(int32_t)ti;copy.node[DOFF]=(int32_t)di;
        if(newTextCount)memcpy(state->text+ti,newText,(size_t)newTextCount*sizeof(state->text[0]));
        if(newDataCount)memcpy(state->data+di,newData,(size_t)newDataCount*sizeof(state->data[0]));
        ti+=newTextCount;di+=newDataCount;state->components[out++]=copy;
    }
    if(out<NR_SOURCE_STAGE_COMPONENT_CAPACITY)memset(state->components+out,0,(NR_SOURCE_STAGE_COMPONENT_CAPACITY-out)*sizeof(state->components[0]));
    if(ti<NR_SOURCE_STAGE_TEXT_CAPACITY)memset(state->text+ti,0,(NR_SOURCE_STAGE_TEXT_CAPACITY-ti)*sizeof(state->text[0]));
    if(di<NR_SOURCE_STAGE_DATA_CAPACITY)memset(state->data+di,0,(NR_SOURCE_STAGE_DATA_CAPACITY-di)*sizeof(state->data[0]));
    state->count=out;state->textCount=ti;state->dataCount=di;
}
int nrSourceStageCommand(NrContext*c,State*s,const Json*j) {
    int64_t publicId=0;double idValue;int idToken=nrField(j,0,"id");
    if(idToken<0||!nrNumber(j,idToken,&idValue)||idValue<1||idValue>65535||idValue!=(uint32_t)idValue)return fail(c,"Source stage id must be 1..65535");
    publicId=(int64_t)idValue;int slot=-1;
    for(uint32_t i=0;i<s->sourceStage.count;i++)if(s->sourceStage.components[i].id==(uint32_t)publicId){slot=(int)i;break;}
    int op=nrField(j,0,"op");
    if(op>=0&&nrEqual(j,op,"remove-source-stage-component")){
        if(!nrAllowed(j,0,"op id"))return fail(c,"Unknown source stage remove field");
        if(slot<0)return fail(c,"Source stage component not found");
        packPools(&s->sourceStage,slot,NULL,NULL,0,NULL,0);nrModalForgetComponent(s,(uint32_t)publicId);return 0;
    }
    if(s->schema<NR_STATE_SCHEMA_MATERIAL_PATTERN)return fail(c,"Source stage command requires current schema");
    if(slot<0&&s->sourceStage.count>=NR_SOURCE_STAGE_COMPONENT_CAPACITY)return fail(c,"Source stage capacity");
    SourceStageComponentRecord record;uint32_t text[NR_SOURCE_STAGE_TEXT_CAPACITY],textCount=0;
    int32_t data[NR_SOURCE_STAGE_DATA_CAPACITY];uint32_t dataCount=0;
    if(parseNode(c,j,&record,text,&textCount,data,&dataCount)<0)return -1;
    record.id=(uint32_t)publicId;record.used=1;
    if((uint64_t)s->sourceStage.textCount-(slot>=0?(uint32_t)s->sourceStage.components[slot].node[TLEN]:0)+textCount>NR_SOURCE_STAGE_TEXT_CAPACITY||
       (uint64_t)s->sourceStage.dataCount-(slot>=0?(uint32_t)s->sourceStage.components[slot].node[DLEN]:0)+dataCount>NR_SOURCE_STAGE_DATA_CAPACITY)return fail(c,"Source stage pool capacity");
    if(record.materialId&&!s->materials[record.materialId-1].used)return fail(c,"Source stage material must exist");
    if(slot<0)slot=(int)s->sourceStage.count;
    packPools(&s->sourceStage,slot<=(int)s->sourceStage.count-1?slot:-1,&record,text,textCount,data,dataCount);return 0;
}
int nrValidSourceStage(const State*s) {
    if(!s||s->width>INT32_MAX||s->height>INT32_MAX||s->sourceStage.reserved||s->sourceStage.count>NR_SOURCE_STAGE_COMPONENT_CAPACITY||s->sourceStage.textCount>NR_SOURCE_STAGE_TEXT_CAPACITY||s->sourceStage.dataCount>NR_SOURCE_STAGE_DATA_CAPACITY)return 0;
    if(s->schema<NR_STATE_SCHEMA_SOURCE_STAGE&&s->sourceStage.count)return 0;
    uint32_t tc=0,dc=0;
    for(uint32_t i=0;i<s->sourceStage.count;i++){
        const SourceStageComponentRecord*r=&s->sourceStage.components[i];if(!r->used||!r->id||r->id>65535||r->reserved)return 0;
        for(uint32_t j=0;j<i;j++)if(s->sourceStage.components[j].id==r->id)return 0;
        const int32_t*n=r->node;if(n[TOFF]!=(int32_t)tc||n[DOFF]!=(int32_t)dc||n[TLEN]<0||n[DLEN]<0||n[25]||n[31]||(uint64_t)tc+n[TLEN]>s->sourceStage.textCount||(uint64_t)dc+n[DLEN]>s->sourceStage.dataCount)return 0;
        tc+=(uint32_t)n[TLEN];dc+=(uint32_t)n[DLEN];
        if(r->materialId>NR_MATERIALS||(r->materialId&&!s->materials[r->materialId-1].used))return 0;
        NrSourceMaterialSampler sourcePalette;nrSourceMaterialSamplerDefaults(&sourcePalette);
        if(s->sourceStageScene.enabled)nrSourceStagePalette(&s->sourceStageScene,&sourcePalette);
        if(r->materialId&&s->materialPatterns[r->materialId-1].used)sourcePalette=s->materialPatterns[r->materialId-1].sampler;
        NrSourceStageComponent c;memset(&c,0,sizeof(c));memcpy(c.node,n,sizeof(c.node));c.text=s->sourceStage.text;c.textCount=s->sourceStage.textCount;c.data=s->sourceStage.data;c.dataCount=s->sourceStage.dataCount;c.material=&sourcePalette;c.baseColor=s->background;
        if(n[LEGACY]<0||!nrSourceStageComponentValid(&c,(int32_t)s->width,(int32_t)s->height))return 0;
        for(uint32_t k=tc-(uint32_t)n[TLEN];k<tc;k++)if(s->sourceStage.text[k]>0x10ffff||(s->sourceStage.text[k]>=0xd800&&s->sourceStage.text[k]<=0xdfff))return 0;
        for(uint32_t k=dc-(uint32_t)n[DLEN];k<dc;k++)if(s->sourceStage.data[k]<-1000000||s->sourceStage.data[k]>1000000)return 0;
    }
    if(tc!=s->sourceStage.textCount||dc!=s->sourceStage.dataCount)return 0;
    for(uint32_t i=s->sourceStage.count;i<NR_SOURCE_STAGE_COMPONENT_CAPACITY;i++){const uint8_t*p=(const uint8_t*)&s->sourceStage.components[i];for(size_t k=0;k<sizeof(s->sourceStage.components[i]);k++)if(p[k])return 0;}
    for(uint32_t i=s->sourceStage.textCount;i<NR_SOURCE_STAGE_TEXT_CAPACITY;i++)if(s->sourceStage.text[i])return 0;
    for(uint32_t i=s->sourceStage.dataCount;i<NR_SOURCE_STAGE_DATA_CAPACITY;i++)if(s->sourceStage.data[i])return 0;
    return 1;
}
static uint32_t mix(uint32_t a,uint32_t b,uint32_t p){
    if(p>1000)p=1000;uint32_t out=0;
    for(int shift=0;shift<=16;shift+=8){int32_t av=(int32_t)(a>>shift&255),bv=(int32_t)(b>>shift&255);out|=(uint32_t)(av+(bv-av)*(int32_t)p/1000)<<shift;}return out;
}
typedef struct {NrContext*c;const State*s;const SourceStageComponentRecord*r;uint32_t materialId,hitId,modal;} DrawContext;
static int readCell(void*ctx,int32_t x,int32_t y,NrSourceStageCell*out){
    DrawContext*d=ctx;const State*s=d->s;NrContext*c=d->c;if(x<0||y<0||(uint32_t)x>=s->width||(uint32_t)y>=s->height)return -1;
    size_t at=(size_t)y*s->width+x;const NrCell*n=&c->cells[at];out->glyph=n->glyph;out->foregroundRgb=n->foreground;out->backgroundRgb=n->background;out->legacyFlags=n->id;out->semanticOwner=c->characterOwners[at];return 0;
}
static uint32_t sampled(DrawContext*d,int32_t x,int32_t y,uint32_t color,uint32_t*alpha){
    if(!d->materialId)return color;int m=(int)d->materialId-1;double materialAlpha=1.0;uint32_t sampledColor=color;
    (void)nrPaint(d->s,m,d->s->timeUs,d->r->id,&materialAlpha);
    const MaterialPattern*p=&d->s->materialPatterns[m];
    if(p->used){int64_t xq=(int64_t)x*256,yq=(int64_t)y*256;if(xq>=INT32_MIN&&xq<=INT32_MAX&&yq>=INT32_MIN&&yq<=INT32_MAX)nrSourceMaterialSampleColor(&p->sampler,d->s->timeUs,(int32_t)xq,(int32_t)yq,&sampledColor);}
    uint32_t mul=(uint32_t)(materialAlpha*1000.0);if(mul>1000)mul=1000;*alpha=*alpha*mul/1000;return sampledColor;
}
static void cell(void*ctx,int32_t x,int32_t y,uint32_t operation,uint32_t glyph,uint32_t fg,uint32_t fgOpacity,uint32_t bg,uint32_t bgOpacity,uint32_t bgExplicit,uint32_t legacyFlags,uint32_t semanticOwner){
    DrawContext*d=ctx;State const*s=d->s;NrContext*c=d->c;if(x<0||y<0||(uint32_t)x>=s->width||(uint32_t)y>=s->height)return;size_t at=(size_t)y*s->width+x;NrCell*p=&c->cells[at];
    if(operation==NR_SOURCE_CELL_BACKGROUND_TINT){uint32_t opacity=bgOpacity;bg=sampled(d,x,y,bg,&opacity);p->background=mix(p->background,bg,opacity);return;}
    if(operation==NR_SOURCE_CELL_FLATTEN){uint32_t oldGlyph=p->glyph;p->glyph=glyph;p->background=bg;if(!d->modal)p->id=d->hitId;c->characterIndices[at]=UINT32_MAX;if(oldGlyph!=glyph)c->characterOwners[at]=semanticOwner;return;}
    uint32_t oldGlyph=p->glyph;
    uint32_t flat=(p->glyph==0x2580||p->glyph==0x2584||p->glyph==0x258c)?mix(p->background,p->foreground,500):p->background;
    if(operation==NR_SOURCE_CELL_FILL){
        uint32_t bo=bgExplicit?bgOpacity:0,fo=fgOpacity;bg=sampled(d,x,y,bg,&bo);fg=sampled(d,x,y,fg,&fo);
        uint32_t nextBg=bo?mix(flat,bg,bo):p->background;uint32_t fgBase=bo?nextBg:flat;
        p->glyph=glyph;p->foreground=fo?mix(p->foreground,fgBase,fo):p->foreground;p->background=nextBg;
    }else{
        fg=sampled(d,x,y,fg,&fgOpacity);p->glyph=glyph;p->foreground=mix(flat,fg,fgOpacity);p->background=flat;
    }
    if(!d->modal||(operation!=NR_SOURCE_CELL_FILL&&legacyFlags))p->id=d->hitId;c->characterIndices[at]=UINT32_MAX;if(glyph!=oldGlyph)c->characterOwners[at]=semanticOwner;
    (void)legacyFlags;
}
static void subcell(void*ctx,int32_t x,int32_t y,uint32_t sx,uint32_t sy,uint32_t rgb,uint32_t opacity,uint32_t coverage,uint32_t legacyFlags,uint32_t semanticOwner){
    DrawContext*d=ctx;State const*s=d->s;NrContext*c=d->c;if(!coverage||x<0||y<0||(uint32_t)x>=s->width||(uint32_t)y>=s->height)return;size_t at=(size_t)y*s->width+x;NrCell*p=&c->cells[at];
    rgb=sampled(d,x,y,rgb,&opacity);static const uint8_t bits[8]={1,8,2,16,4,32,64,128};if(sx>1||sy>3)return;
    uint32_t oldGlyph=p->glyph;if(p->glyph<0x2800||p->glyph>0x28ff)p->glyph=0x2800;p->glyph|=bits[sy*2+sx];p->foreground=mix(p->background,rgb,opacity);if(!d->modal||legacyFlags)p->id=d->hitId;c->characterIndices[at]=UINT32_MAX;if(oldGlyph!=p->glyph)c->characterOwners[at]=semanticOwner;(void)legacyFlags;
}
static void drawStage(NrContext*c,const State*s,int modal){
    if(!c||!s)return;
    if(!modal)nrSourceStageBackground(c,s);
    for(uint32_t i=0;i<s->sourceStage.count;i++){
        const SourceStageComponentRecord*r=&s->sourceStage.components[i];if(!r->used)continue;
        if(modal?!nrModalActiveComponent(s,r->id):nrModalOwnsComponent(s,r->id))continue;
        NrSourceStageComponent source;memset(&source,0,sizeof(source));memcpy(source.node,r->node,sizeof(source.node));source.timeMs=nrSourceStageTime(s);source.baseColor=s->sourceStageScene.enabled?(uint32_t)s->sourceStageScene.values[23]:s->background;
        NrSourceMaterialSampler sourcePalette;nrSourceMaterialSamplerDefaults(&sourcePalette);
        if(s->sourceStageScene.enabled)nrSourceStagePalette(&s->sourceStageScene,&sourcePalette);
        if(r->materialId&&s->materialPatterns[r->materialId-1].used)sourcePalette=s->materialPatterns[r->materialId-1].sampler;
        DrawContext d={c,s,r,r->materialId,NR_ID_SOURCE_STAGE|r->id,(uint32_t)modal};source.material=&sourcePalette;source.semanticOwner=0;
        source.text=s->sourceStage.text;source.textCount=s->sourceStage.textCount;source.data=s->sourceStage.data;source.dataCount=s->sourceStage.dataCount;
        NrSourceStageComponentSink sink={&d,(int32_t)s->width,(int32_t)s->height,readCell,cell,subcell};
        (void)nrSourceStageComponentApply(&source,&sink);
    }
    nrSourceStageQuantize(c,s);
}
void nrSourceStageDraw(NrContext*c,const State*s){drawStage(c,s,0);}
void nrSourceStageDrawModal(NrContext*c,const State*s){if(nrModalAssociationReady(s))drawStage(c,s,1);}
int nrSourceStageDrawTransient(NrContext*c,const int32_t node[32],const uint32_t*text,
                               uint32_t textCount,uint32_t semanticOwner,uint32_t hitId){
    if(!c||!node||(!text&&textCount))return -1;
    const State*s=nrView(c);if(!s||s->width>INT32_MAX||s->height>INT32_MAX)return -1;
    SourceStageComponentRecord record;memset(&record,0,sizeof(record));memcpy(record.node,node,sizeof(record.node));
    DrawContext d={c,s,&record,0,hitId,0};
    NrSourceMaterialSampler sourcePalette;nrSourceMaterialSamplerDefaults(&sourcePalette);
    NrSourceStageComponent source;memset(&source,0,sizeof(source));memcpy(source.node,node,sizeof(source.node));
    source.text=text;source.textCount=textCount;source.timeMs=s->timeUs/1000;source.baseColor=s->background;
    source.material=&sourcePalette;source.semanticOwner=semanticOwner;
    NrSourceStageComponentSink sink={&d,(int32_t)s->width,(int32_t)s->height,readCell,cell,subcell};
    return nrSourceStageComponentApply(&source,&sink);
}
