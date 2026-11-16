#include "internal.h"
#include "window_content_source.h"
#include <float.h>

static int fail(NrContext*c,const char*m){size_t n=strlen(m);if(n>=sizeof(c->error))n=sizeof(c->error)-1;memcpy(c->error,m,n);c->error[n]=0;return -1;}
static int finiteValue(double d){return d==d&&d>=-DBL_MAX&&d<=DBL_MAX;}
static int scalarCount(const uint32_t*text,uint32_t n,uint32_t maximum){
    uint32_t units=0;for(uint32_t i=0;i<n;i++){
        uint32_t g=text[i];if(g>0x10ffff||(g>=0xd800&&g<=0xdfff))return 0;
        units+=g>0xffff?2:1;if(units>maximum)return 0;
    }return 1;
}
static int sourceLabel(const WindowContent*q){
    if(q->labelCount<1||q->labelCount>64)return 0;
    for(uint32_t i=0;i<q->labelCount;i++){
        uint32_t g=q->label[i];
        if(!((g>='a'&&g<='z')||(g>='A'&&g<='Z')||(g>='0'&&g<='9')||g=='_'||g=='.'||g=='-'))return 0;
    }return 1;
}
static int integer(const Json*j,const char*name,uint32_t*out,uint32_t maximum){
    int at=nrField(j,0,name);if(at<0)return 1;double d;
    if(!nrNumber(j,at,&d)||d<0||d>maximum||d!=(uint32_t)d)return 0;*out=(uint32_t)d;return 1;
}
double nrWindowContentVisibility(const State*s,int slot){
    if(s->atelierWindows[slot].enabled)return nrAtelierWindowTween(s,slot,0);
    const WindowContent*q=&s->windowContent[slot];
    if(!q->enabled)return nrWindowVisibility(&s->windows[slot],s->timeUs);
    if(s->reducedMotion)return q->visibilityTo;
    double t=q->visibilityDurationUs?nrClamp((double)(nrWindowApplicationTimeUs(s)>=q->atUs?nrWindowApplicationTimeUs(s)-q->atUs:0)/q->visibilityDurationUs,0,1):1;
    return q->visibilityFrom+(q->visibilityTo-q->visibilityFrom)*t*t*(3-2*t);
}
double nrWindowContentMaximized(const State*s,int slot){
    if(s->atelierWindows[slot].enabled)return nrAtelierWindowTween(s,slot,1);
    const WindowContent*q=&s->windowContent[slot];const Window*w=&s->windows[slot];
    if(!q->enabled)return w->maximized?1:0;
    if(s->reducedMotion)return q->maxTo;
    double t=w->durationUs?nrClamp((double)(nrWindowApplicationTimeUs(s)>=q->maxAtUs?nrWindowApplicationTimeUs(s)-q->maxAtUs:0)/w->durationUs,0,1):1;
    return q->maxFrom+(q->maxTo-q->maxFrom)*t*t*(3-2*t);
}
const uint32_t*nrWindowDocument(const State*s,const Window*w,int*count){
    int slot=nrFindWindow(s,w->id);
    if(slot>=0&&s->windowContent[slot].enabled){*count=(int)s->windowContent[slot].textCount;return s->windowContent[slot].text;}
    *count=w->textCount;return w->text;
}
int nrWindowContentCommand(NrContext*c,State*s,const Json*j){
    if(s->schema<NR_STATE_SCHEMA_WINDOW_TEXTURE)return fail(c,"Generated windows require schema68");
    uint32_t id=0;if(!integer(j,"id",&id,65535)||!id)return fail(c,"Window content id required");
    int slot=nrFindWindow(s,(int)id);if(slot<0)return fail(c,"Window content requires an existing window");
    WindowContent*q=&s->windowContent[slot];Window*w=&s->windows[slot];
    if(nrEqual(j,nrField(j,0,"op"),"remove-window-content")){
        if(!nrAllowed(j,0,"op id"))return fail(c,"Unknown remove-window-content field");
        if(!s->windowPresentation[slot].enabled)s->windowSourceOrder[slot]=0;memset(q,0,sizeof(*q));memset(&s->atelierWindows[slot],0,sizeof(s->atelierWindows[slot]));return 0;
    }
    if(!nrAllowed(j,0,"op id label sourceIndex text colors stopWidths background ink lightness chroma brightness hueOffset lockLightness feather textLightness textChroma waveform profile chrome toolWidth toolHeight customSide customOrder customGlyphs toolColors fadeFloor"))return fail(c,"Unknown window content field");
    if(s->windowTextures.windows[slot].width)return fail(c,"Remove raw window texture before attaching generated content");
    if(w->shape>9&&!s->atelierWindows[slot].enabled&&!nrEqual(j,nrField(j,0,"profile"),"atelier"))return fail(c,"Generated windows require an source shape");
    if(!q->enabled){
        memset(q,0,sizeof(*q));q->enabled=1;q->sourceIndex=(uint32_t)slot;
        q->label[0]='w';q->labelCount=1;uint32_t n=id,digits[5];int length=0;
        do{digits[length++]='0'+n%10;n/=10;}while(n);while(length)q->label[q->labelCount++]=digits[--length];
        q->textCount=(uint32_t)w->textCount;memcpy(q->text,w->text,(size_t)w->textCount*sizeof(uint32_t));
        nrWindowPaletteSourceDefaults(&q->palette);
        q->visibilityFrom=w->fromVisibility;q->visibilityTo=w->target;q->visibilityDurationUs=(double)w->durationUs;
        q->atUs=w->atUs;q->maxAtUs=nrWindowApplicationTimeUs(s);
        q->maxFrom=q->maxTo=w->maximized?1:0;q->transitionEffect=w->effect;
    }
    if(!integer(j,"sourceIndex",&q->sourceIndex,31))return fail(c,"Invalid source window index");
    int token=nrField(j,0,"label");if(token>=0){int n=nrDecode(j,token,q->label,64);if(n<0)return fail(c,"Invalid source window label");q->labelCount=(uint32_t)n;}
    token=nrField(j,0,"text");if(token>=0){int n=nrDecode(j,token,q->text,4096);if(n<0)return fail(c,"Invalid generated window text");q->textCount=(uint32_t)n;}
    if(!sourceLabel(q)||!scalarCount(q->text,q->textCount,4096)||!scalarCount(w->title,(uint32_t)w->titleCount,160))return fail(c,"Invalid source window document or label");
    NrWindowPaletteSourceConfig*p=&q->palette;
    if(!integer(j,"background",&p->backgroundRgb,0xffffff)||!integer(j,"ink",&p->inkRgb,0xffffff))return fail(c,"Invalid source palette RGB");
    token=nrField(j,0,"colors");if(token>=0){
        if(j->tokens[token].type!=J_ARRAY||j->tokens[token].count<1||j->tokens[token].count>32)return fail(c,"Source palette requires one to 32 colors");
        p->colorCount=(uint32_t)j->tokens[token].count;uint32_t i=0;
        memset(p->colors,0,sizeof(p->colors));
        for(int at=token+1;at<j->tokens[token].next;at=j->tokens[at].next){double d;if(!nrNumber(j,at,&d)||d<0||d>0xffffff||d!=(uint32_t)d)return fail(c,"Invalid source palette RGB");p->colors[i++]=(uint32_t)d;}
    }
    token=nrField(j,0,"stopWidths");if(token>=0){
        if(j->tokens[token].type!=J_ARRAY||j->tokens[token].count>32)return fail(c,"Invalid source stop widths");
        p->weightCount=(uint32_t)j->tokens[token].count;uint32_t i=0;memset(p->weights,0,sizeof(p->weights));
        for(int at=token+1;at<j->tokens[token].next;at=j->tokens[at].next)if(!nrNumber(j,at,&p->weights[i++]))return fail(c,"Invalid source stop width");
    }
    struct Field{const char*name;double*value;}fields[]={
        {"lightness",&p->lightness},{"chroma",&p->chroma},{"brightness",&p->brightness},
        {"hueOffset",&p->hueOffsetDegrees},{"feather",&p->feather},{"textLightness",&p->textLightness},{"textChroma",&p->textChroma}};
    for(size_t i=0;i<sizeof(fields)/sizeof(fields[0]);i++){token=nrField(j,0,fields[i].name);if(token>=0&&!nrNumber(j,token,fields[i].value))return fail(c,"Invalid source palette option");}
    token=nrField(j,0,"lockLightness");if(token>=0){int b;if(!nrBoolean(j,token,&b))return fail(c,"Invalid source palette boolean");p->lockLightness=(uint32_t)b;}
    if(!nrWindowPaletteSourceValidate(p))return fail(c,"Source palette option outside domain");
    token=nrField(j,0,"waveform");if(token>=0){
        if(j->tokens[token].type!=J_ARRAY||j->tokens[token].count!=128)return fail(c,"Source waveform requires 128 samples");
        uint32_t i=0;for(int at=token+1;at<j->tokens[token].next;at=j->tokens[at].next)
            if(!nrNumber(j,at,&q->waveform[i++]))return fail(c,"Invalid source waveform sample");
    }
    if(nrAtelierWindowPatch(c,s,j,slot)<0)return -1;
    return 0;
}
int nrValidWindowContent(const State*s){
    for(int slot=0;slot<(int)NR_MAX_WINDOWS;slot++){
        const WindowContent*q=&s->windowContent[slot];const Window*w=&s->windows[slot];
        if(!q->enabled){WindowContent zero={0};if(memcmp(q,&zero,sizeof(zero)))return 0;continue;}
        if(q->enabled!=1||q->reserved||s->schema<NR_STATE_SCHEMA_WINDOW_TEXTURE||!w->used||(w->shape>9&&!s->atelierWindows[slot].enabled)||s->windowTextures.windows[slot].width||
           q->sourceIndex>31||!sourceLabel(q)||q->textCount>4096||!scalarCount(q->text,q->textCount,4096)||!scalarCount(w->title,(uint32_t)w->titleCount,160)||!nrWindowPaletteSourceValidate(&q->palette))return 0;
        double values[]={q->visibilityFrom,q->visibilityTo,q->maxFrom,q->maxTo};
        for(int i=0;i<4;i++)if(!finiteValue(values[i])||values[i]<0||values[i]>1)return 0;
        if(!finiteValue(q->visibilityDurationUs)||q->visibilityDurationUs<0||q->visibilityDurationUs>60000000||q->atUs>s->timeUs||q->maxAtUs>s->timeUs||nrEffectFamily(q->transitionEffect)!=3)return 0;
        for(int i=0;i<128;i++)if(!finiteValue(q->waveform[i]))return 0;
    }return 1;
}
int nrWindowContentAction(State*s,int slot,int action){
    if(s->atelierWindows[slot].enabled)return nrAtelierWindowAction(s,slot,action);
    WindowContent*q=&s->windowContent[slot];Window*w=&s->windows[slot];if(!q->enabled)return 0;
    if(action!=0&&action!=1&&action!=2&&action!=3&&action!=8&&action!=9)return 0;
    double visibility=nrWindowContentVisibility(s,slot),maximized=nrWindowContentMaximized(s,slot);
    if(action==3){
        if(visibility<1){q->visibilityFrom=visibility;q->visibilityTo=1;q->visibilityDurationUs=w->durationUs*(1-visibility);q->atUs=nrWindowApplicationTimeUs(s);q->transitionEffect=w->effect;}
        q->maxFrom=maximized;q->maxTo=w->maximized?0:1;q->maxAtUs=nrWindowApplicationTimeUs(s);w->maximized=q->maxTo!=0;w->target=1;
    }else{
        if(action==0){q->maxFrom=maximized;q->maxTo=0;q->maxAtUs=nrWindowApplicationTimeUs(s);w->maximized=0;}
        q->visibilityFrom=visibility;q->visibilityTo=action==0||action==9?1:action==8?.16:0;
        q->visibilityDurationUs=w->durationUs*(nrAbs(q->visibilityTo-visibility)>.1?nrAbs(q->visibilityTo-visibility):.1);
        q->atUs=nrWindowApplicationTimeUs(s);q->transitionEffect=action==8||action==9?nrEffectId("window-transition/scroll-up"):w->effect;
        w->target=q->visibilityTo>0;
    }
    w->fromVisibility=visibility;w->atUs=s->timeUs;return 1;
}

int nrWindowContentTexture(NrContext*c,int slot,uint32_t width,uint32_t height,const uint32_t**cells){
    const State*s=nrView(c);const Window*w=&s->windows[slot];const WindowContent*q=&s->windowContent[slot];
    if(!q->enabled||width*height>4000)return 0;
    if(!c->windowPaletteValid[slot]||memcmp(&q->palette,&c->windowPaletteConfig[slot],sizeof(q->palette))){
        if(nrWindowPaletteSourcePrepare(&q->palette,&c->windowPalette[slot]))return 0;
        c->windowPaletteConfig[slot]=q->palette;c->windowPaletteValid[slot]=1;
    }
    uint32_t accent;if(nrWindowPaletteSourceInk(&c->windowPalette[slot],q->sourceIndex*80.0+180,&accent))return 0;
    uint32_t label[80],n=0;for(uint32_t i=0;i<q->labelCount;i++){uint32_t g=q->label[i];label[n++]=g>='a'&&g<='z'?g-32:g;}
    label[n++]=' ';label[n++]='/';label[n++]=' ';
    static const char*shapes[]={"rectangle","rounded","ellipse","hexagon","diamond","capsule","ticket","squircle","petal","wave"};
    for(const char*p=shapes[w->shape];*p;p++)label[n++]=(uint32_t)*p;
    NrWindowContentSource source={.width=width,.height=height,.shape=(uint32_t)w->shape,
        .titleScalars=w->title,.titleCount=(uint32_t)w->titleCount,.contentScalars=q->text,.contentCount=q->textCount,
        .labelScalars=label,.labelCount=n,.clockMs=nrWindowApplicationTimeUs(s)/1000.0,.inkRgb=q->palette.inkRgb,
        .backgroundRgb=q->palette.backgroundRgb,.accentRgb=accent,.ramp2048=c->windowPalette[slot].ramp,
        .stopTotal=c->windowPalette[slot].stopTotal,.waveform=q->waveform,.waveformCount=128,.cells4=&c->windowContentCells[0][0]};
    if(nrWindowContentSourceRender(&source))return 0;*cells=&c->windowContentCells[0][0];return 1;
}
