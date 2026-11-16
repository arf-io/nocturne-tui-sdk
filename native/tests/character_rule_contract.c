#include "character_test_context.h"
static int characterRuleChecks(CharacterTestContext*fixture){
    NrContext*context=fixture->context;static Json json;static CharacterRule rule,before,other;

    Widget*w=&context->state.widgets[0];w->used=1;w->id=7;w->enabled=0;w->active=1;
    RegisteredState*r=&context->state.registeredStates[0];r->used=1;r->id=1;r->family=1;r->targetId=7;r->active=1;
    memcpy(r->role,"control",8);memcpy(r->path,"/app/control",13);
    context->cells[0]=(NrCell){.glyph='A',.foreground=0xffffff,.background=0,.id=0};
    context->characterOwners[0]=(1u<<16)|7;context->characterIndices[0]=0;
    const char*source="{\"id\":\"disabled-treatment\",\"priority\":1.5,\"selector\":{\"path\":\"/app/control\"},\"enabled\":false,\"states\":{\"disabled\":{\"enabled\":true,\"foregroundEffects\":[{\"type\":\"invert\"}]}}}";
    if(!nrParse(&json,source,(int)strlen(source))||!nrCompileCharacterRule(&context->state,&json,0,&rule))return 2;
    if(rule.style.enabled||rule.style.paint.space!=3||rule.stateCount!=1||!rule.states[0].style.enabled)return 3;
    characterTestRemember(fixture);NrCell out;
    if(nrApplyCharacterRuleCell(context,&rule,0,0,&out)!=1||out.foreground!=0||out.glyph!='A'||out.id)return 4;
    if(!characterTestUnchanged(fixture)||context->cells[0].foreground!=0xffffff)return 5;
    before=rule;
    if(nrCompileCharacterRule(NULL,&json,0,&rule)||memcmp(&rule,&before,sizeof(rule)))return 14;
    if(nrCompileCharacterRule(&context->state,NULL,0,&rule)||memcmp(&rule,&before,sizeof(rule)))return 15;
    if(nrCompileCharacterRule(&context->state,&json,0,NULL))return 16;
    const char*invalid[]={"{\"id\":\"\"}","{\"id\":\"x\",\"priority\":10001}","{\"id\":\"x\",\"foreground\":9999}","{\"id\":\"x\",\"states\":{\"active\":{\"selector\":{}}}}","{\"id\":\"x\",\"foregroundOpacity\":2}","{\"id\":\"x\",\"compositeSpace\":\"cmyk\"}","{\"id\":\"x\",\"states\":{\"active\":{},\"active\":{}}}"};
    for(unsigned i=0;i<sizeof(invalid)/sizeof(invalid[0]);i++){
        if(nrParse(&json,invalid[i],(int)strlen(invalid[i]))&&nrCompileCharacterRule(&context->state,&json,0,&rule))return 6;
        if(memcmp(&rule,&before,sizeof(rule)))return 7;
    }
    other=rule;other.priority=rule.priority+1;
    if(nrCharacterRuleCompare(&rule,&other)>=0||nrCharacterRuleCompare(&other,&rule)<=0)return 8;
    other.priority=rule.priority;memcpy(other.id,"z",2);
    if(nrCharacterRuleCompare(&rule,&other)>=0||nrCharacterRuleCompare(&rule,&rule))return 9;
    w->enabled=1;w->active=1;out=(NrCell){.glyph=123};
    if(nrApplyCharacterRuleCell(context,&rule,0,0,&out)||out.glyph!=123)return 10;
    before=rule;other=rule;
    memcpy(before.id,"\xf0\x90\x80\x80",5);memcpy(other.id,"\xee\x80\x80",4);
    if(nrCharacterRuleCompare(&before,&other)>=0||nrCharacterRuleCompare(&other,&before)<=0)return 11;
    memcpy(other.id,"\xf0\x90\x80\x81",5);
    if(nrCharacterRuleCompare(&before,&other)>=0)return 12;
    memcpy(other.id,"\xf0\x90\x80\x80" "a",6);
    if(nrCharacterRuleCompare(&before,&other)>=0||nrCharacterRuleCompare(&other,&other))return 13;
    return 0;
}

int nrTestCharacterRule(void){return characterTestRun(characterRuleChecks);}
