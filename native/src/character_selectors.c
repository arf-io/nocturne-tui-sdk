#include "internal.h"
/* Historical character predicates are pure reads over explicit owner/cell data.
 * Geometry sums widen before comparison; viewport size is not an authoring cap. */
static int strings(const Json*j,int at,char out[64][129],int*count){
    if(at<0)return 1;
    if(j->tokens[at].type==J_STRING){*count=1;return nrString(j,at,out[0],129)>=0;}
    if(j->tokens[at].type!=J_ARRAY||j->tokens[at].count<1||j->tokens[at].count>64)return 0;
    *count=j->tokens[at].count;int child=at+1;
    for(int i=0;i<*count;i++){if(nrString(j,child,out[i],129)<0)return 0;child=j->tokens[child].next;}return 1;
}
static int integers(const Json*j,int at,uint32_t*out,int*count){
    if(at<0)return 1;
    if(j->tokens[at].type!=J_ARRAY||j->tokens[at].count>4096)return 0;
    *count=j->tokens[at].count;int child=at+1;
    for(int i=0;i<*count;i++){double n;if(!nrNumber(j,child,&n)||n<0||n>4294967295.0||n!=(uint32_t)n)return 0;out[i]=(uint32_t)n;child=j->tokens[child].next;}return 1;
}
/* Historical valuePath: absolute, no empty segment (so no "//", trailing or bare
 * "/"), "~" only as the ~0/~1 escapes, no prototype-name segment. validateSelector
 * skips an empty string, which then imposes no filter. Native strings fit 127 bytes. */
static int historicalPath(const char*path){
    if(!path[0])return 1;
    if(path[0]!='/')return 0;
    const char*segment=path+1;
    for(const char*p=segment;;p++){
        if(*p&&*p!='/'){if(*p=='~'&&p[1]!='0'&&p[1]!='1')return 0;continue;}
        size_t n=(size_t)(p-segment);
        if(!n||(n==9&&(!memcmp(segment,"__proto__",9)||!memcmp(segment,"prototype",9)))||(n==11&&!memcmp(segment,"constructor",11)))return 0;
        if(!*p)return 1;
        segment=p+1;
    }
}
static int compileSelector(const Json*j,int at,CharacterSelector*out){
    memset(out,0,sizeof(*out));
    if(at<0||!nrAllowed(j,at,"role path pathPrefix ids state rect indices glyphs inkOnly"))return 0;
    if(!strings(j,nrField(j,at,"role"),out->roles,&out->roleCount)||!strings(j,nrField(j,at,"state"),out->states,&out->stateCount))return 0;
    int ids=nrField(j,at,"ids"),indices=nrField(j,at,"indices");out->hasIds=ids>=0;out->hasIndices=indices>=0;
    if(!integers(j,ids,out->ids,&out->idCount)||!integers(j,indices,out->indices,&out->indexCount))return 0;
    int glyphs=nrField(j,at,"glyphs");if(glyphs>=0){out->glyphCount=nrDecode(j,glyphs,out->glyphs,4096);if(out->glyphCount<0)return 0;}
    int ink=nrField(j,at,"inkOnly");if(ink>=0&&!nrBoolean(j,ink,&out->inkOnly))return 0;
    int path=nrField(j,at,"path"),prefix=nrField(j,at,"pathPrefix");
    if(path>=0&&(nrString(j,path,out->path,128)<0||!historicalPath(out->path)))return 0;
    if(prefix>=0&&(nrString(j,prefix,out->prefix,128)<0||!historicalPath(out->prefix)))return 0;
    int rect=nrField(j,at,"rect");if(rect>=0){
        if(!nrAllowed(j,rect,"x y width height"))return 0;out->hasRect=1;
        const char*names[]={"x","y","width","height"};int*targets[]={&out->x,&out->y,&out->width,&out->height};
        for(int i=0;i<4;i++){double n;if(!nrNumber(j,nrField(j,rect,names[i]),&n)||n<(i<2?NR_LAYOUT_MIN:0)||n>NR_LAYOUT_MAX||n!=(int)n)return 0;*targets[i]=(int)n;}
    }return 1;
}
int nrCompileCharacterSelector(const Json*j,int at,CharacterSelector*out){
    if(!j||!out)return 0;
    CharacterSelector candidate;
    if(!compileSelector(j,at,&candidate))return 0;
    *out=candidate;return 1;
}
int nrCharacterSelectorMatches(const CharacterSelector*s,const char*role,const char*state,const char*path,uint32_t id,uint32_t index,uint32_t glyph,int x,int y){
    if(s->inkOnly&&(glyph<=32||(glyph>=0x2580&&glyph<=0x259f)||(glyph>=0x2800&&glyph<=0x28ff)))return 0;
    if(s->roleCount){int found=0;for(int i=0;i<s->roleCount;i++){
        const char*r=s->roles[i];if(!strcmp(r,"all")||!strcmp(r,"background")||!strcmp(r,role)||(!strcmp(r,"component")&&id))found=1;
    }if(!found)return 0;}
    if(s->stateCount){int found=0;for(int i=0;i<s->stateCount;i++)if(!strcmp(s->states[i],state))found=1;if(!found)return 0;}
    if(s->path[0]&&strcmp(s->path,path))return 0;
    if(s->prefix[0]){size_t n=strlen(s->prefix),length=strlen(path);if(length<n||memcmp(s->prefix,path,n)||(length>n&&path[n]!='/'))return 0;}
    if(s->hasIds){int found=0;for(int i=0;i<s->idCount;i++)if(s->ids[i]==id)found=1;if(!found)return 0;}
    if(s->hasIndices){int found=0;for(int i=0;i<s->indexCount;i++)if(s->indices[i]==index)found=1;if(!found)return 0;}
    if(s->glyphCount){int found=0;uint32_t g=glyph?glyph:32;for(int i=0;i<s->glyphCount;i++)if(s->glyphs[i]==g)found=1;if(!found)return 0;}
    if(s->hasRect&&(x<s->x||y<s->y||(int64_t)x>=(int64_t)s->x+s->width||(int64_t)y>=(int64_t)s->y+s->height))return 0;
    return 1;
}
/* Consume a completed frame and its scratch planes. Never draw, evaluate a
 * trigger, refresh a clock, or write either authoritative or presentation data. */
uint32_t nrCharacterFragmentOwner(const State*s,uint32_t owner){
    if(owner==1||owner==3)return 8u<<16;
    if(owner==2)return 9u<<16;
    uint32_t family=owner&0xffff0000u,slot=owner&0xffffu;
    if(family==0x20000000u&&slot&&slot<=NR_MAX_PARTICLES){
        const Particle*p=&s->particles[slot-1];
        if(p->state&&p->emitterId&&p->emitterId<=65535u)return (3u<<16)|p->emitterId;
    }
    if(family==0x30000000u&&slot&&slot<=NR_DEPOSITS){
        const Deposit*d=&s->deposits[slot-1];
        if(d->used&&d->emitterId&&d->emitterId<=65535u)return (3u<<16)|d->emitterId;
    }
    return 0; /* Shared/aggregated geometry has no unambiguous registered owner. */
}
int nrCharacterCellMatches(const NrContext*c,const CharacterSelector*selector,int x,int y){
    const State*s=nrView(c);
    if(x<0||y<0||(uint32_t)x>=s->width||(uint32_t)y>=s->height)return 0;
    size_t at=(size_t)y*s->width+(uint32_t)x;
    const NrCell*cell=&c->cells[at];
    const char*role,*state,*path;nrCharacterCellOwner(c,at,&role,&state,&path);
    uint32_t index=c->characterIndices[at];
    if(index==UINT32_MAX)index=(uint32_t)at;
    return nrCharacterSelectorMatches(selector,role,state,path,cell->id,index,cell->glyph,x,y);
}
