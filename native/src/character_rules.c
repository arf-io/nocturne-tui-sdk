#include "internal.h"
#define STYLE_FIELDS "enabled foreground background foregroundBlend backgroundBlend operator compositeSpace foregroundEffects backgroundEffects foregroundOpacity backgroundOpacity protectLocalInk"
static const char*blends[]={"normal","multiply","screen","overlay","darken","lighten","color-dodge","color-burn","hard-light","soft-light","difference","exclusion","hue","saturation","color","luminosity","additive","subtractive","divide","linear-burn","linear-light","vivid-light","pin-light","hard-mix","darker-color","lighter-color","dissolve","none"};
static const char*operators[]={"source-over","clear","source","destination","destination-over","source-in","destination-in","source-out","destination-out","source-atop","destination-atop","xor","lighter"};
static const char*spaces[]={"srgb","linear-srgb","oklab","oklch"};
static int choice(const Json*j,int at,const char*field,const char*const*names,int count,uint32_t*out){
    int token=nrField(j,at,field);if(token<0)return 1;
    for(int i=0;i<count;i++)if(nrEqual(j,token,names[i])){*out=(uint32_t)i;return 1;}return 0;
}
static int material(const State*s,const Json*j,int at,const char*field,int*out){
    int token=nrField(j,at,field);if(token<0)return 1;
    (void)s;
    double n;if(!nrNumber(j,token,&n)||n<0||n>=NR_MATERIALS||n!=(int)n)return 0;*out=(int)n;return 1;
}
static int opacity(const Json*j,int at,const char*field,double*out){
    int token=nrField(j,at,field);if(token<0)return 1;double n;if(!nrNumber(j,token,&n)||!(n>=0&&n<=1))return 0;*out=n;return 1;
}
static int style(const State*s,const Json*j,int at,CharacterStyle*out){
    int enabled=nrField(j,at,"enabled"),protect=nrField(j,at,"protectLocalInk");
    if((enabled>=0&&!nrBoolean(j,enabled,&out->enabled))||(protect>=0&&!nrBoolean(j,protect,&out->paint.protectLocalInk)))return 0;
    if(!material(s,j,at,"foreground",&out->foregroundMaterial)||!material(s,j,at,"background",&out->backgroundMaterial)||
       !opacity(j,at,"foregroundOpacity",&out->foregroundOpacity)||!opacity(j,at,"backgroundOpacity",&out->backgroundOpacity)||
       !choice(j,at,"foregroundBlend",blends,28,&out->paint.foregroundBlend)||!choice(j,at,"backgroundBlend",blends,28,&out->paint.backgroundBlend)||
       !choice(j,at,"operator",operators,13,&out->paint.operation)||!choice(j,at,"compositeSpace",spaces,4,&out->paint.space))return 0;
    int fg=nrField(j,at,"foregroundEffects"),bg=nrField(j,at,"backgroundEffects");
    if(fg>=0&&!nrCompileCharacterEffects(j,fg,&out->foregroundEffects))return 0;
    if(bg>=0&&!nrCompileCharacterEffects(j,bg,&out->backgroundEffects))return 0;
    return 1;
}
int nrCompileCharacterRule(const State*s,const Json*j,int at,CharacterRule*out){
    if(!s||!j||!out)return 0;
    CharacterRule candidate;memset(&candidate,0,sizeof(candidate));
    if(!nrAllowed(j,at,"id priority selector states " STYLE_FIELDS))return 0;
    if(nrString(j,nrField(j,at,"id"),candidate.id,sizeof(candidate.id))<1)return 0;
    int priority=nrField(j,at,"priority");
    if(priority>=0&&(!nrNumber(j,priority,&candidate.priority)||!(candidate.priority>=-10000&&candidate.priority<=10000)))return 0;
    int selector=nrField(j,at,"selector");
    if(selector>=0&&!nrCompileCharacterSelector(j,selector,&candidate.selector))return 0;
    candidate.style.enabled=1;candidate.style.foregroundMaterial=candidate.style.backgroundMaterial=-1;
    candidate.style.foregroundOpacity=candidate.style.backgroundOpacity=1;
    candidate.style.paint.protectLocalInk=1;candidate.style.paint.space=3;
    if(!style(s,j,at,&candidate.style))return 0;
    int states=nrField(j,at,"states");
    if(states>=0){
        if(j->tokens[states].type!=J_OBJECT||j->tokens[states].count>32)return 0;
        candidate.stateCount=j->tokens[states].count;int key=states+1;
        for(int i=0;i<candidate.stateCount;i++){
            if(nrString(j,key,candidate.states[i].name,sizeof(candidate.states[i].name))<0||!nrAllowed(j,key+1,STYLE_FIELDS))return 0;
            for(int k=0;k<i;k++)if(!strcmp(candidate.states[k].name,candidate.states[i].name))return 0;
            candidate.states[i].style=candidate.style;
            if(!style(s,j,key+1,&candidate.states[i].style))return 0;
            key=j->tokens[key+1].next;
        }
    }
    *out=candidate;return 1;
}
/* IDs are validated UTF-8. Compare decoded UTF-16 code units to preserve the
 * historical JavaScript ordering, including supplementary characters. */
static uint32_t nextIdUnit(const unsigned char**cursor,uint32_t*pending){
    if(*pending){uint32_t unit=*pending;*pending=0;return unit;}
    const unsigned char*p=*cursor;uint32_t scalar=*p;
    if(!scalar)return 0;
    p++;
    if(scalar>=0xf0){scalar&=7;for(int i=0;i<3;i++)scalar=(scalar<<6)|(*p++&63);}
    else if(scalar>=0xe0){scalar&=15;for(int i=0;i<2;i++)scalar=(scalar<<6)|(*p++&63);}
    else if(scalar>=0xc0){scalar=((scalar&31)<<6)|(*p++&63);}
    *cursor=p;
    if(scalar>0xffff){scalar-=0x10000;*pending=0xdc00+(scalar&1023);return 0xd800+(scalar>>10);}
    return scalar;
}
int nrCharacterRuleCompare(const CharacterRule*a,const CharacterRule*b){
    if(a->priority<b->priority)return -1;if(a->priority>b->priority)return 1;
    const unsigned char*left=(const unsigned char*)a->id,*right=(const unsigned char*)b->id;
    uint32_t leftPending=0,rightPending=0;
    for(;;){
        uint32_t l=nextIdUnit(&left,&leftPending),r=nextIdUnit(&right,&rightPending);
        if(l!=r)return l<r?-1:1;
        if(!l)return 0;
    }
}
int nrApplyCharacterRuleCell(const NrContext*c,const CharacterRule*rule,int x,int y,NrCell*out){
    if(!c||!rule||!out||!nrCharacterCellMatches(c,&rule->selector,x,y))return 0;
    const State*s=nrView(c);size_t at=(size_t)y*s->width+(uint32_t)x;
    const char*role,*state,*path;nrCharacterCellOwner(c,at,&role,&state,&path);
    const CharacterStyle*chosen=&rule->style;
    for(int i=0;i<rule->stateCount;i++)if(!strcmp(rule->states[i].name,state)){chosen=&rule->states[i].style;break;}
    if(!chosen->enabled)return 0;
    CharacterPaint paint=chosen->paint;double alpha;
    uint32_t index=c->characterIndices[at];if(index==UINT32_MAX)index=(uint32_t)at;
    if(chosen->foregroundMaterial>=0){
        if(chosen->foregroundMaterial>=NR_MATERIALS||!s->materials[chosen->foregroundMaterial].used)return 0;
        paint.hasForeground=1;paint.foreground=nrPaintAt(s,chosen->foregroundMaterial,s->timeUs,(int32_t)x*256,(int32_t)y*256,index,&alpha);
        paint.foregroundAlpha=(uint32_t)(alpha*chosen->foregroundOpacity*65535+.5);
    }
    if(chosen->backgroundMaterial>=0){
        if(chosen->backgroundMaterial>=NR_MATERIALS||!s->materials[chosen->backgroundMaterial].used)return 0;
        paint.hasBackground=1;paint.background=nrPaintAt(s,chosen->backgroundMaterial,s->timeUs,(int32_t)x*256,(int32_t)y*256,index,&alpha);
        paint.backgroundAlpha=(uint32_t)(alpha*chosen->backgroundOpacity*65535+.5);
    }else paint.backgroundAlpha=(uint32_t)(chosen->backgroundOpacity*65535+.5);
    int userText=!strcmp(role,"user-text");
    return nrCharacterPaintEffectsCell(&c->cells[at],&paint,&chosen->foregroundEffects,&chosen->backgroundEffects,!strcmp(state,"selected"),userText,out)?-1:1;
}
