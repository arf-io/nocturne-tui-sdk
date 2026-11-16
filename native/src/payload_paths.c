#include "internal.h"

int nrPayloadPathValid(const char*path){
    if(!path)return 0;
    int length=0;while(length<128&&path[length])length++;
    if(length==128||(length&&path[0]!='/'))return 0;
    for(int i=0;i<length;i++)if(path[i]=='~'){
        if(i+1>=length||(path[i+1]!='0'&&path[i+1]!='1'))return 0;
        i++;
    }
    return 1;
}

int nrPayloadResolve(const IntentPayload*p,const char*path,int*out){
    if(!p||!out||!p->count||p->count>128||!nrPayloadPathValid(path))return 0;
    int at=0,pos=0;
    while(path[pos]){
        char segment[128];int length=0;pos++;
        while(path[pos]&&path[pos]!='/'){
            char ch=path[pos++];
            if(ch=='~'){ch=path[pos++]=='0'?'~':'/';}
            segment[length++]=ch;
        }
        segment[length]=0;
        if(at<0||at>=(int)p->count)return 0;
        const JToken*t=&p->tokens[at];int found=-1;
        if(t->next<=at||t->next>(int)p->count)return 0;
        if(t->type==J_OBJECT){
            for(int key=at+1;key<t->next;){
                int value=key+1;char name[128];
                if(value>=t->next||p->tokens[key].type!=J_STRING)return 0;
                /* Cached payload strings are validated before storage/import.
                 * A key that cannot fit this bounded non-NUL pointer segment
                 * cannot match it; it must not hide later addressable keys. */
                int decoded=nrStringSpan(p->json,p->tokens[key].start,p->tokens[key].end,name,sizeof(name));
                if(decoded>=0&&!strcmp(segment,name)){found=value;break;}
                int next=p->tokens[value].next;
                if(next<=value||next>t->next)return 0;
                key=next;
            }
        }else if(t->type==J_ARRAY){
            if(!length||(length>1&&segment[0]=='0'))return 0;
            unsigned index=0;
            for(int k=0;k<length;k++){
                if(segment[k]<'0'||segment[k]>'9')return 0;
                index=index*10u+(unsigned)(segment[k]-'0');if(index>=128)return 0;
            }
            int child=at+1;
            for(unsigned k=0;k<index;k++){
                if(child>=t->next)return 0;
                int next=p->tokens[child].next;if(next<=child||next>t->next)return 0;
                child=next;
            }
            if(child<t->next)found=child;
        }
        if(found<0)return 0;
        at=found;
    }
    if(at<0||at>=(int)p->count)return 0;
    *out=at;return 1;
}
int nrPayloadNumber(const IntentPayload*p,const char*path,double*out){
    int at;if(!out||!nrPayloadResolve(p,path,&at)||p->tokens[at].type!=J_NUMBER)return 0;
    double value=p->tokens[at].number;
    if(!(value>=-1e12&&value<=1e12))return 0;
    *out=value;return 1;
}
