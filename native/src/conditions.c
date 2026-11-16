#include "internal.h"
/* Prefix-ordered bounded trees. Parsing resolves paths once; evaluation never
 * runs source expressions, allocates, or consumes notification intentions. */
static int findValue(const State*s,const char*path) {
    for(int i=0;i<NR_VALUES;i++)if(s->values[i].used&&!s->typedValues[i].kind&&!strcmp(s->values[i].path,path))return i;
    return -1;
}
static int numberAt(const Json*j,int at,const char*name,double*out,int required) {
    int n=nrField(j,at,name);if(n<0)return !required;
    return nrNumber(j,n,out)&&*out>=-1000000&&*out<=1000000;
}
static int parseNode(const State*s,const Json*j,int at,Trigger*t,int depth) {
    if(depth>NR_CONDITION_DEPTH||t->conditionCount>=NR_CONDITIONS||at<0||j->tokens[at].type!=J_OBJECT)return 0;
    int index=t->conditionCount++;Condition*c=&t->conditions[index];
    memset(c,0,sizeof(*c));c->source=-1;
    const char*names[]={"all","any","not"};int found=-1,arg=-1;
    for(int k=0;k<3;k++)if(nrField(j,at,names[k])>=0){if(found>=0)return 0;found=k;arg=nrField(j,at,names[k]);}
    if(found>=0) {
        if(!nrAllowed(j,at,names[found]))return 0;
        c->kind=found+1;
        if(found==2) {c->children=1;if(!parseNode(s,j,arg,t,depth+1))return 0;}
        else {
            if(j->tokens[arg].type!=J_ARRAY||j->tokens[arg].count<1||j->tokens[arg].count>NR_CONDITIONS)return 0;
            c->children=j->tokens[arg].count;int child=arg+1;
            for(int k=0;k<c->children;k++){if(!parseNode(s,j,child,t,depth+1))return 0;child=j->tokens[child].next;}
        }
    } else {
        int intentValue=nrField(j,at,"intentValue");
        int object=intentValue>=0?intentValue:at;
        if(intentValue>=0) {
            if(!nrAllowed(j,at,"intentValue")||j->tokens[intentValue].type!=J_OBJECT||
               !nrAllowed(j,object,"comparison value min max hysteresis"))return 0;
            c->kind=4;c->source=-1;
        } else {
            if(!nrAllowed(j,at,"path comparison value min max hysteresis"))return 0;
            char path[128];int p=nrField(j,at,"path");
            if(p<0||nrString(j,p,path,sizeof(path))<0||(c->source=findValue(s,path))<0)return 0;
        }
        int q=nrField(j,object,"comparison");if(q<0)return 0;
        const char*cmp[]={"above","below","equal","not-equal","at-least","at-most","between"};
        c->comparison=-1;for(int k=0;k<7;k++)if(nrEqual(j,q,cmp[k]))c->comparison=k;
        if(c->comparison<0)return 0;
        if(!numberAt(j,object,"hysteresis",&c->hysteresis,0)||c->hysteresis<0||
           (intentValue>=0&&c->hysteresis!=0))return 0;
        if(c->comparison==6) {
            if(nrField(j,object,"value")>=0||!numberAt(j,object,"min",&c->low,1)||!numberAt(j,object,"max",&c->high,1)||c->low>c->high)return 0;
        } else {
            if(nrField(j,object,"min")>=0||nrField(j,object,"max")>=0||!numberAt(j,object,"value",&c->low,1))return 0;
            c->high=c->low;
        }
        if((c->comparison==2||c->comparison==3)&&c->hysteresis!=0)return 0;
    }
    c->end=t->conditionCount;return 1;
}
int nrParseConditions(const State*s,const Json*j,int at,Trigger*t) {
    t->conditionCount=0;memset(t->conditions,0,sizeof(t->conditions));
    return parseNode(s,j,at,t,1);
}
static int evaluateLeaf(Condition*c,double x) {
    double h=c->lastTruth?c->hysteresis:0;int truth=0;
    switch(c->comparison) {
        case 0:truth=x>c->low-h;break;
        case 1:truth=x<c->low+h;break;
        case 2:truth=x==c->low;break;
        case 3:truth=x!=c->low;break;
        case 4:truth=x>=c->low-h;break;
        case 5:truth=x<=c->low+h;break;
        case 6:truth=x>=c->low-h&&x<=c->high+h;break;
    }
    return truth;
}
static int evaluateNode(Trigger*t,int index,const double*before,const Intent*candidate) {
    Condition*c=&t->conditions[index];int truth=0;
    if(c->kind==0)truth=evaluateLeaf(c,before[c->source]);
    else if(c->kind==5)truth=1;
    else if(c->kind==4)truth=candidate?evaluateLeaf(c,candidate->value):0;
    else {
        truth=c->kind==1;int child=index+1;
        for(int k=0;k<c->children;k++) {
            /* No short circuit: every leaf updates its own Schmitt state. */
            int value=evaluateNode(t,child,before,candidate);
            if(c->kind==1)truth=truth&&value;
            else if(c->kind==2)truth=truth||value;
            else truth=!value;
            child=t->conditions[child].end;
        }
    }
    c->lastTruth=truth;return truth;
}
int nrConditionTruth(Trigger*t,const double*before,const Intent*candidate) {return evaluateNode(t,0,before,candidate);}
static int validateNode(const State*s,const Trigger*t,int index,int depth) {
    if(depth>NR_CONDITION_DEPTH||index<0||index>=t->conditionCount)return -1;
    const Condition*c=&t->conditions[index];
    if(c->kind<0||c->kind>5||c->end<=index||c->end>t->conditionCount||c->lastTruth<0||c->lastTruth>1||
       !(c->low>=-1000000&&c->low<=1000000)||!(c->high>=-1000000&&c->high<=1000000)||
       !(c->hysteresis>=0&&c->hysteresis<=1000000))return -1;
    if(c->kind==0) {
        if(c->children||c->source<0||c->source>=NR_VALUES||!s->values[c->source].used||s->typedValues[c->source].kind||c->comparison<0||c->comparison>6||
           c->end!=index+1||c->low>c->high||((c->comparison==2||c->comparison==3)&&c->hysteresis))return -1;
    } else if(c->kind==5) {
        if(s->schema<NR_STATE_SCHEMA_GENERAL_API||c->source!=-1||c->children||c->comparison||c->low||c->high||c->hysteresis||c->end!=index+1)return -1;
    } else if(c->kind==4) {
        if(s->schema==NR_STATE_SCHEMA_OLDEST||!t->eventPath[0]||c->source!=-1||c->children||c->comparison<0||c->comparison>6||
           c->end!=index+1||c->low>c->high||c->hysteresis!=0)return -1;
    } else {
        if(c->source!=-1||c->children<1||c->children>NR_CONDITIONS||(c->kind==3&&c->children!=1))return -1;
        int child=index+1;
        for(int k=0;k<c->children;k++){child=validateNode(s,t,child,depth+1);if(child<0)return -1;}
        if(child!=c->end)return -1;
    }
    return c->end;
}
int nrValidConditions(const State*s,const Trigger*t) {
    return t->conditionCount>0&&t->conditionCount<=NR_CONDITIONS&&validateNode(s,t,0,1)==t->conditionCount;
}
