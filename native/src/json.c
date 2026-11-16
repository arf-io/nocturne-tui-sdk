#include "internal.h"
static int fail(Json*j,const char*e) {
    size_t n=strlen(e);
    if(n>127)n=127;
    memcpy(j->error,e,n);
    j->error[n]=0;
    return -1;
}
static void ws(Json*j) {
    while(j->pos<j->length&&(j->text[j->pos]==' '||j->text[j->pos]=='\t'||j->text[j->pos]=='\r'||j->text[j->pos]=='\n'))j->pos++;
}
static int hex(int c) {
    if(c>='0'&&c<='9')return c-'0';
    if(c>='a'&&c<='f')return c-'a'+10;
    if(c>='A'&&c<='F')return c-'A'+10;
    return -1;
}
static int scalar(const char*s,int end,int*p,uint32_t*out) {
    if(*p>=end)return 0;
    uint32_t c=(uint8_t)s[(*p)++];
    if(c=='\\') {
        if(*p>=end)return 0;
        int a=s[(*p)++];
        switch(a) {
            case '"':c='"';
            break;
            case '\\':c='\\';
            break;
            case '/':c='/';
            break;
            case 'b':c=8;
            break;
            case 'f':c=12;
            break;
            case 'n':c=10;
            break;
            case 'r':c=13;
            break;
            case 't':c=9;
            break;
            case 'u':c=0;
            for(int i=0; i<4; i++) {
                if(*p>=end)return 0;
                int n=hex(s[(*p)++]);
                if(n<0)return 0;
                c=c*16+(uint32_t)n;
            }
            if(c>=0xd800&&c<=0xdbff) {
                if(*p+6>end||s[*p]!='\\'||s[*p+1]!='u')return 0;
                *p+=2;
                uint32_t low=0;
                for(int i=0; i<4; i++) {
                    int n=hex(s[(*p)++]);
                    if(n<0)return 0;
                    low=low*16+(uint32_t)n;
                }
                if(low<0xdc00||low>0xdfff)return 0;
                c=0x10000+((c-0xd800)<<10)+low-0xdc00;
            }
            else if(c>=0xdc00&&c<=0xdfff)return 0;
            break;
            default:return 0;
        }
    }
    else if(c>=128) {
        int n=0;
        uint32_t min=0;
        if(c>=0xc2&&c<=0xdf) {
            n=1;
            min=128;
            c&=31;
        }
        else if(c>=0xe0&&c<=0xef) {
            n=2;
            min=2048;
            c&=15;
        }
        else if(c>=0xf0&&c<=0xf4) {
            n=3;
            min=65536;
            c&=7;
        }
        else return 0;
        for(int i=0; i<n; i++) {
            if(*p>=end)return 0;
            uint32_t b=(uint8_t)s[(*p)++];
            if((b&0xc0)!=0x80)return 0;
            c=(c<<6)|(b&63);
        }
        if(c<min||c>0x10ffff||(c>=0xd800&&c<=0xdfff))return 0;
    }
    else if(c<32)return 0;
    *out=c;
    return 1;
}
int nrDecodeSpan(const char*text,int start,int end,uint32_t*out,int cap){
    if(!text||(!out&&cap)||start<0||end<=start+1||text[start]!='"'||text[end-1]!='"')return -1;
    int p=start+1,n=0;
    while(p<end-1){uint32_t value;if(!scalar(text,end-1,&p,&value)||(out&&n>=cap))return -1;if(out)out[n]=value;n++;}
    return n;
}
int nrDecode(const Json*j,int token,uint32_t*out,int cap) {
    if(token<0||token>=j->count||j->tokens[token].type!=J_STRING)return -1;
    return nrDecodeSpan(j->text,j->tokens[token].start,j->tokens[token].end,out,cap);
}
int nrStringSpan(const char*text,int start,int end,char*out,int cap) {
    if(!text||!out||cap<=0||start<0||end<=start+1||text[start]!='"'||text[end-1]!='"')return -1;
    uint32_t v[512];int n=0,at=start+1;
    while(at<end-1){if(n>=512||!scalar(text,end-1,&at,&v[n]))return -1;n++;}
    int k=0;
    for(int i=0; i<n; i++) {
        uint32_t c=v[i];
        if(c==0)return -1;
        int need=c<128?1:c<2048?2:c<65536?3:4;
        if(k+need>=cap)return -1;
        if(need==1)out[k++]=(char)c;
        else {
            if(need==2)out[k++]=(char)(0xc0|(c>>6));
            else if(need==3) {
                out[k++]=(char)(0xe0|(c>>12));
                out[k++]=(char)(0x80|((c>>6)&63));
            }
            else {
                out[k++]=(char)(0xf0|(c>>18));
                out[k++]=(char)(0x80|((c>>12)&63));
                out[k++]=(char)(0x80|((c>>6)&63));
            }
            out[k++]=(char)(0x80|(c&63));
        }
    }
    out[k]=0;
    return k;
}
int nrString(const Json*j,int token,char*out,int cap) {
    if(token<0||token>=j->count||j->tokens[token].type!=J_STRING)return -1;
    return nrStringSpan(j->text,j->tokens[token].start,j->tokens[token].end,out,cap);
}
int nrEqual(const Json*j,int i,const char*s) {
    char buf[128];
    return nrString(j,i,buf,sizeof(buf))>=0&&!strcmp(buf,s);
}
/* Object data keys are JSON strings, not native C identifiers. Compare decoded
 * scalar streams without a short temporary buffer or NUL truncation. Native
 * authoring fields still enforce their own identifier/string capacities. */
static int validKey(const Json*j,int token){
    const JToken*t=&j->tokens[token];int at=t->start+1;
    while(at<t->end-1){uint32_t value;if(!scalar(j->text,t->end-1,&at,&value))return 0;}
    return 1;
}
static int keysEqual(const Json*j,int a,int b){
    const JToken*left=&j->tokens[a],*right=&j->tokens[b];int x=left->start+1,y=right->start+1;
    while(x<left->end-1&&y<right->end-1){uint32_t p,q;
        if(!scalar(j->text,left->end-1,&x,&p)||!scalar(j->text,right->end-1,&y,&q)||p!=q)return 0;
    }
    return x==left->end-1&&y==right->end-1;
}
static int parseValue(Json*j) {
    ws(j);
    if(j->depth++>=24||j->count>=NR_JSON_TOKENS)return fail(j,"JSON depth/token capacity");
    if(j->pos>=j->length)return fail(j,"Missing JSON value");
    int i=j->count++;
    JToken*t=&j->tokens[i];
    memset(t,0,sizeof(*t));
    t->start=j->pos;
    char c=j->text[j->pos++];
    if(c=='{'||c=='[') {
        t->type=c=='{'?J_OBJECT:J_ARRAY;
        ws(j);
        char close=c=='{'?'}':']';
        if(j->pos<j->length&&j->text[j->pos]==close)j->pos++;
        else for(;; ) {
            if(c=='{') {
                int key=parseValue(j);
                if(key<0||j->tokens[key].type!=J_STRING)return fail(j,"Object key must be string");
                if(!validKey(j,key))return fail(j,"Invalid object key");
                for(int k=i+1; k<key; ) {
                    if(keysEqual(j,k,key))return fail(j,"Duplicate object key");
                    k=j->tokens[k+1].next;
                }
                ws(j);
                if(j->pos>=j->length||j->text[j->pos++]!=':')return fail(j,"Missing colon");
            }
            if(parseValue(j)<0)return -1;
            t->count++;
            ws(j);
            if(j->pos>=j->length)return fail(j,"Unclosed container");
            char sep=j->text[j->pos++];
            if(sep==close)break;
            if(sep!=',')return fail(j,"Missing comma");
        }
    }
    else if(c=='"') {
        int p=j->pos;
        for(;; ) {
            if(p>=j->length)return fail(j,"Unclosed string");
            if(j->text[p]=='"') {
                j->pos=p+1;
                break;
            }
            uint32_t value;
            if(!scalar(j->text,j->length,&p,&value))return fail(j,"Invalid Unicode or JSON escape");
        }
        t->type=J_STRING;
    }
    else if(c=='t'||c=='f'||c=='n') {
        const char*word=c=='t'?"true":c=='f'?"false":"null";
        int length=(int)strlen(word);
        if(t->start+length>j->length||memcmp(j->text+t->start,word,(size_t)length))return fail(j,"Invalid literal");
        j->pos=t->start+length;
        t->type=c=='t'?J_TRUE:c=='f'?J_FALSE:J_NULL;
    }
    else {
        int p=t->start;
        if(j->text[p]=='-')p++;
        if(p>=j->length)return fail(j,"Invalid number");
        if(j->text[p]=='0')p++;
        else{
            if(j->text[p]<'1'||j->text[p]>'9')return fail(j,"Invalid number");
            while(p<j->length&&j->text[p]>='0'&&j->text[p]<='9')p++;
        }
        if(p<j->length&&j->text[p]=='.'){
            p++;if(p>=j->length||j->text[p]<'0'||j->text[p]>'9')return fail(j,"Invalid decimal");
            while(p<j->length&&j->text[p]>='0'&&j->text[p]<='9')p++;
        }
        if(p<j->length&&(j->text[p]=='e'||j->text[p]=='E')){
            p++;if(p<j->length&&(j->text[p]=='-'||j->text[p]=='+'))p++;
            if(p>=j->length||j->text[p]<'0'||j->text[p]>'9')return fail(j,"Invalid exponent");
            while(p<j->length&&j->text[p]>='0'&&j->text[p]<='9')p++;
        }
        double value;if(!nrDecimalNumber(j->text+t->start,p-t->start,&value))return fail(j,"Nonfinite number or numeric range");
        t->type=J_NUMBER;t->number=value;
        j->pos=p;
    }
    t->end=j->pos;
    t->next=j->count;
    j->depth--;
    return i;
}
int nrParse(Json*j,const char*s,int n) {
    j->text=s;
    j->length=n;
    j->count=0;
    j->pos=0;
    j->depth=0;
    j->error[0]=0;
    if(n<=0){fail(j,"Command byte length");return 0;}
    if(parseValue(j)<0)return 0;
    ws(j);
    if(j->pos!=n||j->tokens[0].type!=J_OBJECT) {
        fail(j,"Expected exactly one JSON object");
        return 0;
    }
    return 1;
}
int nrField(const Json*j,int o,const char*key) {
    if(o<0||o>=j->count||j->tokens[o].type!=J_OBJECT)return -1;
    for(int k=o+1; k<j->tokens[o].next; ) {
        if(nrEqual(j,k,key))return k+1;
        k=j->tokens[k+1].next;
    }
    return -1;
}
int nrAllowed(const Json*j,int o,const char*allowed) {
    if(o<0||j->tokens[o].type!=J_OBJECT)return 0;
    for(int k=o+1; k<j->tokens[o].next; ) {
        char name[128];
        if(nrString(j,k,name,sizeof(name))<0)return 0;
        const char*p=allowed;
        int found=0;
        size_t len=strlen(name);
        while(*p) {
            const char*q=p;
            while(*q&&*q!=' ')q++;
            if((size_t)(q-p)==len&&!memcmp(p,name,len))found=1;
            p=*q?q+1:q;
        }
        if(!found)return 0;
        k=j->tokens[k+1].next;
    }
    return 1;
}
int nrNumber(const Json*j,int i,double*v) {
    if(i<0||i>=j->count||j->tokens[i].type!=J_NUMBER)return 0;
    *v=j->tokens[i].number;
    return 1;
}
int nrBoolean(const Json*j,int i,int*v) {
    if(i<0||i>=j->count)return 0;
    if(j->tokens[i].type==J_TRUE) {
        *v=1;
        return 1;
    }
    if(j->tokens[i].type==J_FALSE) {
        *v=0;
        return 1;
    }
    return 0;
}
