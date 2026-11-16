#include "internal.h"
/* Retained, bounded trees use compiled value slots, never stored callbacks or JSON. */
static int boundedNumber(double x){return x>=-1e12&&x<=1e12;}
typedef struct {const char*name;int dimension;double scale,offset;} FormulaUnit;
static const FormulaUnit units[]={
 {"seconds",0,1,0},{"milliseconds",0,.001,0},{"microseconds",0,.000001,0},
 {"nanoseconds",0,.000000001,0},{"minutes",0,60,0},{"hours",0,3600,0},
 {"meters",1,1,0},{"centimeters",1,.01,0},{"millimeters",1,.001,0},{"kilometers",1,1000,0},
 {"degrees",2,.017453292519943295,0},{"radians",2,1,0},
 {"celsius",3,1,273.15},{"fahrenheit",3,5.0/9.0,255.37222222222222222},{"kelvin",3,1,0}
};
static int unitIndex(const Json*j,int at){for(int i=0;i<15;i++)if(nrEqual(j,at,units[i].name))return i;return -1;}
static int unitPair(int ref){int from=ref/16,to=ref%16;return ref>=0&&from<15&&to<15&&units[from].dimension==units[to].dimension;}
int nrFormulaUnitRef(const Json*j,int fromAt,int toAt){
    int from=unitIndex(j,fromAt),to=unitIndex(j,toAt);
    return from>=0&&to>=0&&units[from].dimension==units[to].dimension?from*16+to:-1;
}
static int compileNode(const State*s,const Json*j,int at,int depth,NumericFormula*f){
    if(at<0||at>=j->count||depth>8||f->count>=31)return -1;
    int index=f->count++;NumericFormulaNode*n=&f->nodes[index];n->ref=-1;
    if(j->tokens[at].type==J_NUMBER){if(!nrNumber(j,at,&n->value)||!boundedNumber(n->value))return -1;return index;}
    if(j->tokens[at].type!=J_OBJECT)return -1;
    int arg=nrField(j,at,"path");
    if(arg>=0){char path[128];if(!nrAllowed(j,at,"path")||nrString(j,arg,path,sizeof(path))<0)return -1;
        n->kind=1;for(int i=0;i<NR_VALUES;i++)if(s->values[i].used&&!strcmp(path,s->values[i].path))n->ref=i;
        return n->ref>=0&&!s->typedValues[n->ref].kind?index:-1;}
    arg=nrField(j,at,"intentField");
    if(arg>=0){const char*fields[]={"value","id","messageId","actionId","messageSequence","atUs"};
        if(!nrAllowed(j,at,"intentField"))return -1;n->kind=2;
        for(int i=0;i<6;i++)if(nrEqual(j,arg,fields[i]))n->ref=i;
        if(n->ref<0)return -1;f->usesIntent=1;return index;}
    arg=nrField(j,at,"intentPath");
    if(arg>=0){if(!nrAllowed(j,at,"intentPath")||nrString(j,arg,f->intentPaths[index],128)<0||!nrPayloadPathValid(f->intentPaths[index]))return -1;
        n->kind=18;f->usesIntent=1;return index;}
    const char*operators[]={"add","subtract","multiply","divide","min","max","negate","abs","clamp","floor","ceil","round","lerp","remap","convert"};
    int op=-1;for(int k=0;k<15;k++)if(nrField(j,at,operators[k])>=0){op=k;break;}
    if(op<0||!nrAllowed(j,at,operators[op]))return -1;n->kind=op+3;arg=nrField(j,at,operators[op]);
    int children[16],count=0;
    if(op==6||op==7||(op>=9&&op<=11)){children[count++]=arg;}
    else if(op==8){if(j->tokens[arg].type!=J_OBJECT||!nrAllowed(j,arg,"value min max"))return -1;
        children[count++]=nrField(j,arg,"value");children[count++]=nrField(j,arg,"min");children[count++]=nrField(j,arg,"max");}
    else if(op==12||op==13){
        const char*keys3[]={"from","to","amount"};
        const char*keys5[]={"value","inMin","inMax","outMin","outMax"};
        if(j->tokens[arg].type!=J_OBJECT||!nrAllowed(j,arg,op==12?"from to amount":"value inMin inMax outMin outMax"))return -1;
        count=op==12?3:5;for(int k=0;k<count;k++)children[k]=nrField(j,arg,op==12?keys3[k]:keys5[k]);
    }
    else if(op==14){
        if(j->tokens[arg].type!=J_OBJECT||!nrAllowed(j,arg,"value from to"))return -1;
        int from=unitIndex(j,nrField(j,arg,"from")),to=unitIndex(j,nrField(j,arg,"to"));
        if(from<0||to<0||units[from].dimension!=units[to].dimension)return -1;
        n->ref=from*16+to;children[count++]=nrField(j,arg,"value");
    }
    else{if(j->tokens[arg].type!=J_ARRAY)return -1;count=j->tokens[arg].count;
        if(count<2||count>16||((op==1||op==3)&&count!=2))return -1;
        int child=arg+1;for(int k=0;k<count;k++){children[k]=child;child=j->tokens[child].next;}}
    n->childCount=count;
    for(int k=0;k<count;k++){int child=compileNode(s,j,children[k],depth+1,f);if(child<0)return -1;n->children[k]=(uint8_t)child;}
    return index;
}
int nrCompileTriggerFormula(const State*s,const Json*j,int at,NumericFormula*f){
    memset(f,0,sizeof(*f));return compileNode(s,j,at,1,f)==0;
}
int nrNumericOperation(int kind,int ref,const double*args,int count,double*out){
    if(kind<3||kind>17||count<1||count>16)return 0;
    if((kind==9||kind==10||(kind>=12&&kind<=14)||kind==17)?count!=1:
       (kind==11||kind==15)?count!=3:kind==16?count!=5:
       (kind==4||kind==6)?count!=2:count<2)return 0;
    for(int k=0;k<count;k++)if(!boundedNumber(args[k]))return 0;
    double x=0;
        if(kind==9)x=-args[0];else if(kind==10)x=args[0]==0?0:nrAbs(args[0]);
        else if(kind==11){if(args[1]>args[2])return 0;x=nrClamp(args[0],args[1],args[2]);}
        else if(kind==12)x=nrFloor(args[0]);
        else if(kind==13)x=-nrFloor(-args[0]);
        else if(kind==14){x=nrFloor(args[0]);if(args[0]-x>=.5)x+=1;}
        else if(kind==15){double span=args[1]-args[0],scaled=span*args[2];if(!boundedNumber(span)||!boundedNumber(scaled))return 0;x=args[0]+scaled;}
        else if(kind==16){
            double input=args[2]-args[1],output=args[4]-args[3],delta=args[0]-args[1];
            if(input==0||!boundedNumber(input)||!boundedNumber(output)||!boundedNumber(delta))return 0;
            double fraction=delta/input,scaled=fraction*output;if(!boundedNumber(fraction)||!boundedNumber(scaled))return 0;x=args[3]+scaled;
        }
        else if(kind==17){
            if(!unitPair(ref))return 0;
            const FormulaUnit*from=&units[ref/16],*to=&units[ref%16];
            double scaled=args[0]*from->scale,canonical=scaled+from->offset,delta=canonical-to->offset;
            if(!boundedNumber(scaled)||!boundedNumber(canonical)||!boundedNumber(delta))return 0;x=delta/to->scale;
        }
        else{x=args[0];for(int k=1;k<count;k++){
            switch(kind){case 3:x+=args[k];break;case 4:x-=args[k];break;case 5:x*=args[k];break;case 6:if(args[k]==0)return 0;x/=args[k];break;case 7:if(args[k]<x)x=args[k];break;case 8:if(args[k]>x)x=args[k];break;default:return 0;}
            if(!boundedNumber(x))return 0;
        }}
    if(!boundedNumber(x))return 0;*out=x;return 1;
}
static int evaluate(const NumericFormula*f,int at,const double*values,const Intent*q,const IntentPayload*payload,double*out){
    const NumericFormulaNode*n=&f->nodes[at];double x=0;
    if(n->kind==0)x=n->value;
    else if(n->kind==1)x=values[n->ref];
    else if(n->kind==2){if(!q)return 0;switch(n->ref){case 0:x=q->value;break;case 1:x=(double)q->id;break;case 2:x=q->messageId;break;case 3:x=q->actionId;break;case 4:x=(double)q->messageSequence;break;case 5:x=(double)q->atUs;break;default:return 0;}}
    else if(n->kind==18){if(!q||!nrPayloadNumber(payload,f->intentPaths[at],&x))return 0;}
    else{
        double args[16];for(int k=0;k<n->childCount;k++)if(!evaluate(f,n->children[k],values,q,payload,&args[k]))return 0;
        return nrNumericOperation(n->kind,n->ref,args,n->childCount,out);
    }
    if(!boundedNumber(x))return 0;*out=x;return 1;
}
int nrEvalTriggerFormula(const NumericFormula*f,const double*values,const Intent*q,const IntentPayload*payload,double*out){
    return f->count>0&&evaluate(f,0,values,q,payload,out);
}
static int validNode(const State*s,const NumericFormula*f,int at,int depth,uint32_t*seen,int*intent){
    if(at<0||at>=f->count||depth>8||(*seen&(1u<<at)))return 0;*seen|=1u<<at;
    const NumericFormulaNode*n=&f->nodes[at];if(n->kind<0||n->kind>18||n->childCount<0||n->childCount>16)return 0;
    if(n->kind<=2||n->kind==18){if(n->childCount)return 0;
        if(n->kind==0){if(n->ref!=-1||!boundedNumber(n->value))return 0;}
        if(n->kind==1){if(n->ref<0||n->ref>=NR_VALUES||!s->values[n->ref].used||s->typedValues[n->ref].kind||n->value!=0)return 0;}
        if(n->kind==2){if(n->ref<0||n->ref>5||n->value!=0)return 0;*intent=1;}
        if(n->kind==18){if(n->ref!=-1||n->value!=0||!nrPayloadPathValid(f->intentPaths[at]))return 0;*intent=1;}
    }else{if(n->value!=0||(n->kind==17?!unitPair(n->ref):n->ref!=-1))return 0;
        int count=n->childCount;
        if((n->kind==9||n->kind==10||(n->kind>=12&&n->kind<=14)||n->kind==17)?count!=1:
           (n->kind==11||n->kind==15)?count!=3:n->kind==16?count!=5:
           (n->kind==4||n->kind==6)?count!=2:count<2)return 0;
        for(int k=0;k<count;k++)if(n->children[k]<=at||!validNode(s,f,n->children[k],depth+1,seen,intent))return 0;
    }
    if(n->kind!=18){for(int k=0;k<128;k++)if(f->intentPaths[at][k])return 0;}
    else{int end=-1;for(int k=0;k<128;k++)if(!f->intentPaths[at][k]){end=k;break;}if(end<0)return 0;for(int k=end;k<128;k++)if(f->intentPaths[at][k])return 0;}
    for(int k=n->childCount;k<16;k++)if(n->children[k])return 0;
    return 1;
}
int nrValidTriggerFormulas(const State*s){
    NumericFormula zero={0};NumericFormulaNode empty={0};
    for(int i=0;i<NR_TRIGGERS;i++){
        const NumericFormula*f=&s->triggerFormulas[i];if(f->count<0||f->count>31)return 0;
        if(!f->count){if(memcmp(f,&zero,sizeof(*f)))return 0;continue;}
        if(s->schema<NR_STATE_SCHEMA_GENERAL_API||!s->triggers[i].used)return 0;
        uint32_t seen=0;int intent=0;
        if(!validNode(s,f,0,1,&seen,&intent)||seen!=((1u<<f->count)-1)||intent!=f->usesIntent||(intent&&!s->triggers[i].eventPath[0]))return 0;
        for(int k=f->count;k<31;k++){if(memcmp(&f->nodes[k],&empty,sizeof(empty)))return 0;for(int n=0;n<128;n++)if(f->intentPaths[k][n])return 0;}
    }return 1;
}
