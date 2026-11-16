#include "internal.h"
#include "document_bidi.h"
#include "grapheme_cursor.h"
typedef struct {uint32_t first,last,value;} BidiRange;
typedef struct {uint32_t scalar,pair,type;} BidiPair;
#include "unicode_bidi.inc"
static int bidiScalar(uint32_t scalar){return scalar<=0x10ffffu&&(scalar<0xd800u||scalar>0xdfffu);}
int nrBidiClass(uint32_t scalar) {
    if(!bidiScalar(scalar))return -1;
    size_t low=0,high=sizeof(bidiRanges)/sizeof(bidiRanges[0]);
    while(low<high){size_t m=low+(high-low)/2;const BidiRange*r=&bidiRanges[m];
        if(scalar<r->first)high=m;else if(scalar>r->last)low=m+1;else return (int)r->value;}
    return 0;
}
static const BidiPair* bidiPair(const BidiPair*table,size_t count,uint32_t scalar) {
    size_t low=0,high=count;
    while(low<high){size_t m=low+(high-low)/2;
        if(scalar<table[m].scalar)high=m;else if(scalar>table[m].scalar)low=m+1;else return table+m;}
    return NULL;
}
int nrBidiBracket(uint32_t scalar,uint32_t*out,uint32_t capacity) {
    if(!bidiScalar(scalar)||!out||capacity<2||((uintptr_t)out%_Alignof(uint32_t)))return -1;
    const BidiPair*p=bidiPair(bidiBrackets,sizeof(bidiBrackets)/sizeof(bidiBrackets[0]),scalar);
    if(!p)return 0;out[0]=p->pair;out[1]=p->type;return 1;
}
int nrBidiMirror(uint32_t scalar) {
    if(!bidiScalar(scalar))return -1;
    const BidiPair*p=bidiPair(bidiMirrors,sizeof(bidiMirrors)/sizeof(bidiMirrors[0]),scalar);
    return (int)(p?p->pair:scalar);
}

int nrBidiParagraphLevel(const uint32_t*text,uint32_t count,uint32_t fallback) {
    if(count>NR_MAX_TEXT||(!text&&count)||fallback>1)return -1;
    /* Validate the entire input before returning a first-strong answer. */
    for(uint32_t i=0;i<count;i++)if(!bidiScalar(text[i]))return -1;
    uint32_t depth=0;
    for(uint32_t i=0;i<count;i++) {
        int type=nrBidiClass(text[i]);
        if(type==10)break; /* First paragraph only. */
        if(type==19||type==20||type==21){depth++;continue;}
        if(type==22){if(depth)depth--;continue;}
        if(depth)continue;
        if(type==0)return 0;
        if(type==1||type==2)return 1;
    }
    return (int)fallback;
}

typedef struct {uint32_t level;int override,isolate;} BidiStatus;
static int bidiIsolateDirection(const uint32_t*text,uint32_t count,uint32_t start) {
    uint32_t depth=0;
    for(uint32_t i=start;i<count;i++) {
        int type=nrBidiClass(text[i]);
        if(type==10)break;
        if(type==19||type==20||type==21){depth++;continue;}
        if(type==22){if(!depth)break;depth--;continue;}
        if(!depth){if(type==0)return 0;if(type==1||type==2)return 1;}
    }
    return 0;
}
int nrBidiExplicit(const uint32_t*text,uint32_t count,uint32_t direction,uint32_t*out,uint32_t capacity) {
    if(count>NR_MAX_TEXT||(!text&&count)||direction>2||(!out&&capacity))return -1;
    for(uint32_t i=0;i<count;i++)if(!bidiScalar(text[i]))return -1;
    if(!out&&!capacity)return (int)count;
    if(capacity<count||((uintptr_t)out%_Alignof(uint32_t)))return -1;
    uint32_t rows[NR_MAX_TEXT*4];BidiStatus stack[127];
    uint32_t base=direction==2?(uint32_t)nrBidiParagraphLevel(text,count,0):direction;
    uint32_t top=0,overflowIsolate=0,overflowEmbedding=0,validIsolate=0;
    stack[0]=(BidiStatus){base,-1,0};
    for(uint32_t i=0;i<count;i++) {
        int original=nrBidiClass(text[i]),type=original;
        uint32_t level=stack[top].level,removed=0;
        if(type==14||type==15||type==16||type==17) {
            int odd=type==16||type==17;
            uint32_t next=odd?(level+1)|1u:(level+2)&~1u;
            if(next<=125&&!overflowIsolate&&!overflowEmbedding)
                stack[++top]=(BidiStatus){next,type==15?0:type==17?1:-1,0};
            else if(!overflowIsolate)overflowEmbedding++;
            removed=1;
        } else if(type==19||type==20||type==21) {
            int odd=type==20||(type==21&&bidiIsolateDirection(text,count,i+1));
            if(stack[top].override>=0)type=stack[top].override;
            uint32_t next=odd?(level+1)|1u:(level+2)&~1u;
            if(next<=125&&!overflowIsolate&&!overflowEmbedding) {
                stack[++top]=(BidiStatus){next,-1,1};validIsolate++;
            } else overflowIsolate++;
        } else if(type==22) {
            if(overflowIsolate)overflowIsolate--;
            else if(validIsolate) {
                overflowEmbedding=0;
                while(top&&!stack[top].isolate)top--;
                if(top)top--;validIsolate--;
            }
            level=stack[top].level;
            if(stack[top].override>=0)type=stack[top].override;
        } else if(type==18) {
            if(!overflowIsolate) {
                if(overflowEmbedding)overflowEmbedding--;
                else if(top&&!stack[top].isolate)top--;
            }
            removed=1;
        } else if(type==10) {
            level=base;top=overflowIsolate=overflowEmbedding=validIsolate=0;
            base=direction==2?(uint32_t)nrBidiParagraphLevel(text+i+1,count-i-1,0):direction;
            stack[0]=(BidiStatus){base,-1,0};
        } else if(type==9)removed=1;
        else if(stack[top].override>=0)type=stack[top].override;
        rows[i*4]=(uint32_t)original;rows[i*4+1]=(uint32_t)type;
        rows[i*4+2]=level;rows[i*4+3]=removed;
    }
    if(count)memcpy(out,rows,(size_t)count*4*sizeof(*out));return (int)count;
}

static int bidiInitiator(uint32_t type){return type>=19&&type<=21;}
static void bidiWeakSequence(uint32_t*rows,const uint32_t*order,uint32_t count,uint32_t sos) {
    uint32_t previous=sos,strong=sos;
    for(uint32_t k=0;k<count;k++) {
        uint32_t*r=rows+order[k]*7;
        if(r[1]==8)r[1]=bidiInitiator(previous)||previous==22?13:previous;
        previous=r[1];
    }
    for(uint32_t k=0;k<count;k++) {
        uint32_t*r=rows+order[k]*7;
        if(r[1]==0||r[1]==1||r[1]==2)strong=r[1];
        else if(r[1]==3&&strong==2)r[1]=4;
    }
    for(uint32_t k=0;k<count;k++)if(rows[order[k]*7+1]==2)rows[order[k]*7+1]=1;
    for(uint32_t k=1;k+1<count;k++) {
        uint32_t*r=rows+order[k]*7,a=rows[order[k-1]*7+1],b=rows[order[k+1]*7+1];
        if(a==b&&((r[1]==5&&a==3)||(r[1]==7&&(a==3||a==4))))r[1]=a;
    }
    for(uint32_t k=0;k<count;) {
        if(rows[order[k]*7+1]!=6){k++;continue;}
        uint32_t first=k;while(k<count&&rows[order[k]*7+1]==6)k++;
        if((first&&rows[order[first-1]*7+1]==3)||(k<count&&rows[order[k]*7+1]==3))
            for(uint32_t j=first;j<k;j++)rows[order[j]*7+1]=3;
    }
    for(uint32_t k=0;k<count;k++){uint32_t*r=rows+order[k]*7;if(r[1]==5||r[1]==6||r[1]==7)r[1]=13;}
    strong=sos;
    for(uint32_t k=0;k<count;k++) {
        uint32_t*r=rows+order[k]*7;
        if(r[1]==0||r[1]==1)strong=r[1];else if(r[1]==3&&strong==0)r[1]=0;
    }
}
int nrBidiWeak(const uint32_t*text,uint32_t count,uint32_t direction,uint32_t*out,uint32_t capacity) {
    uint32_t explicitRows[NR_MAX_TEXT*4],rows[NR_MAX_TEXT*7];
    if(nrBidiExplicit(text,count,direction,explicitRows,NR_MAX_TEXT)<0||(!out&&capacity))return -1;
    if(!out&&!capacity)return (int)count;
    if(capacity<count||((uintptr_t)out%_Alignof(uint32_t)))return -1;
    for(uint32_t i=0;i<count;i++) {
        memcpy(rows+i*7,explicitRows+i*4,4*sizeof(*rows));
        rows[i*7+4]=UINT32_MAX;rows[i*7+5]=rows[i*7+6]=0;
    }
    for(uint32_t begin=0;begin<count;) {
        uint32_t end=begin;while(end<count&&rows[end*7]!=10)end++;if(end<count)end++;
        uint32_t base=direction==2?(uint32_t)nrBidiParagraphLevel(text+begin,end-begin,0):direction;
        int match[NR_MAX_TEXT],runAt[NR_MAX_TEXT],next[NR_MAX_TEXT],incoming[NR_MAX_TEXT];
        uint32_t isolateStack[NR_MAX_TEXT],depth=0,indices[NR_MAX_TEXT],length=0;
        uint32_t first[NR_MAX_TEXT],last[NR_MAX_TEXT],runs=0;
        for(uint32_t i=begin;i<end;i++) {
            match[i]=-1;runAt[i]=-1;
            if(bidiInitiator(rows[i*7]))isolateStack[depth++]=i;
            else if(rows[i*7]==22&&depth){uint32_t start=isolateStack[--depth];match[start]=(int)i;}
            if(!rows[i*7+3])indices[length++]=i;
        }
        for(uint32_t k=0;k<length;k++) {
            uint32_t i=indices[k];
            if(!runs||rows[i*7+2]!=rows[indices[k-1]*7+2]) {
                first[runs]=k;last[runs]=k;next[runs]=-1;incoming[runs]=0;runs++;
            } else last[runs-1]=k;
            runAt[i]=(int)runs-1;
        }
        for(uint32_t r=0;r<runs;r++) {
            uint32_t i=indices[last[r]];
            if(bidiInitiator(rows[i*7])&&match[i]>=0) {
                int target=runAt[match[i]];
                if(target>(int)r&&rows[indices[first[target]]*7+2]==rows[i*7+2]){next[r]=target;incoming[target]=1;}
            }
        }
        for(uint32_t root=0;root<runs;root++)if(!incoming[root]) {
            uint32_t order[NR_MAX_TEXT],used=0,r=root;
            while(1) {
                for(uint32_t k=first[r];k<=last[r];k++)order[used++]=indices[k];
                if(next[r]<0)break;r=(uint32_t)next[r];
            }
            uint32_t start=first[root],finish=last[r],a=rows[order[0]*7+2],b=start?rows[indices[start-1]*7+2]:base;
            uint32_t sos=(a>b?a:b)&1u;
            a=rows[order[used-1]*7+2];b=finish+1<length?rows[indices[finish+1]*7+2]:base;
            if(bidiInitiator(rows[order[used-1]*7]))b=base;
            uint32_t eos=(a>b?a:b)&1u;
            for(uint32_t k=0;k<used;k++){uint32_t*row=rows+order[k]*7;row[4]=order[0];row[5]=sos;row[6]=eos;}
            bidiWeakSequence(rows,order,used,sos);
        }
        begin=end;
    }
    if(count)memcpy(out,rows,(size_t)count*7*sizeof(*out));return (int)count;
}

static int bidiStrong(uint32_t type){return type==0?0:(type==1||type==3||type==4)?1:-1;}
static int bidiNeutral(uint32_t type){return type==10||type==11||type==12||type==13||type>=19;}
static uint32_t bidiCanonicalBracket(uint32_t scalar){return scalar==0x2329?0x3008:scalar==0x232a?0x3009:scalar;}
static void bidiResolveSequence(const uint32_t*text,uint32_t*rows,const uint32_t*order,uint32_t count) {
    uint32_t stack[63],closing[63],depth=0,starts[NR_MAX_TEXT],ends[NR_MAX_TEXT],pairs=0;
    for(uint32_t k=0;k<count;k++) {
        if(rows[order[k]*7+1]!=13)continue;
        const BidiPair*p=bidiPair(bidiBrackets,sizeof(bidiBrackets)/sizeof(bidiBrackets[0]),text[order[k]]);
        if(!p)continue;
        if(p->type==1){if(depth==63)break;stack[depth]=k;closing[depth++]=bidiCanonicalBracket(p->pair);}
        else {
            uint32_t scalar=bidiCanonicalBracket(text[order[k]]);
            for(uint32_t j=depth;j>0;j--)if(closing[j-1]==scalar){starts[pairs]=stack[j-1];ends[pairs++]=k;depth=j-1;break;}
        }
    }
    /* N0 pairs are processed in opening-source order, not closing order. */
    for(uint32_t k=1;k<pairs;k++) {
        uint32_t a=starts[k],b=ends[k],j=k;
        while(j&&starts[j-1]>a){starts[j]=starts[j-1];ends[j]=ends[j-1];j--;}
        starts[j]=a;ends[j]=b;
    }
    for(uint32_t p=0;p<pairs;p++) {
        uint32_t a=starts[p],b=ends[p],embedding=rows[order[a]*7+2]&1u;
        int resolved=-1,opposite=0;
        for(uint32_t k=a+1;k<b;k++) {
            int strong=bidiStrong(rows[order[k]*7+1]);
            if(strong==(int)embedding){resolved=(int)embedding;break;}
            if(strong>=0)opposite=1;
        }
        if(resolved<0&&opposite) {
            int preceding=(int)rows[order[0]*7+5];
            for(uint32_t k=a;k>0;k--){int strong=bidiStrong(rows[order[k-1]*7+1]);if(strong>=0){preceding=strong;break;}}
            resolved=preceding==(int)(embedding^1u)?preceding:(int)embedding;
        }
        if(resolved>=0) {
            rows[order[a]*7+1]=rows[order[b]*7+1]=(uint32_t)resolved;
            for(uint32_t edge=0;edge<2;edge++) {
                uint32_t k=(edge?b:a)+1;
                while(k<count&&rows[order[k]*7]==8)rows[order[k++]*7+1]=(uint32_t)resolved;
            }
        }
    }
    for(uint32_t k=0;k<count;) {
        if(!bidiNeutral(rows[order[k]*7+1])){k++;continue;}
        uint32_t first=k;while(k<count&&bidiNeutral(rows[order[k]*7+1]))k++;
        int before=first?bidiStrong(rows[order[first-1]*7+1]):(int)rows[order[0]*7+5];
        int after=k<count?bidiStrong(rows[order[k]*7+1]):(int)rows[order[count-1]*7+6];
        for(uint32_t j=first;j<k;j++)rows[order[j]*7+1]=before==after?(uint32_t)before:rows[order[j]*7+2]&1u;
    }
    for(uint32_t k=0;k<count;k++) {
        uint32_t*r=rows+order[k]*7;
        if(r[2]&1u){if(r[1]==0||r[1]==3||r[1]==4)r[2]++;}
        else {if(r[1]==1)r[2]++;else if(r[1]==3||r[1]==4)r[2]+=2;}
    }
}
int nrBidiLevels(const uint32_t*text,uint32_t count,uint32_t direction,uint32_t*out,uint32_t capacity) {
    uint32_t rows[NR_MAX_TEXT*7],order[NR_MAX_TEXT];
    if(nrBidiWeak(text,count,direction,rows,NR_MAX_TEXT)<0||(!out&&capacity))return -1;
    if(!out&&!capacity)return (int)count;
    if(capacity<count||((uintptr_t)out%_Alignof(uint32_t)))return -1;
    for(uint32_t root=0;root<count;root++)if(!rows[root*7+3]&&rows[root*7+4]==root) {
        uint32_t used=0;for(uint32_t i=root;i<count;i++)if(rows[i*7+4]==root)order[used++]=i;
        bidiResolveSequence(text,rows,order,used);
    }
    if(count)memcpy(out,rows,(size_t)count*7*sizeof(*out));return (int)count;
}

static void bidiLineReset(uint32_t*rows,uint32_t begin,uint32_t end,uint32_t base) {
    for(uint32_t i=begin;i<end;i++)if(rows[i*7]==10||rows[i*7]==11) {
        rows[i*7+2]=base;
        for(uint32_t j=i;j>begin;) {
            uint32_t*r=rows+(--j)*7;if(r[3])continue;
            if(r[0]!=12&&!bidiInitiator(r[0])&&r[0]!=22)break;r[2]=base;
        }
    }
    for(uint32_t j=end;j>begin;) {
        uint32_t*r=rows+(--j)*7;if(r[3])continue;
        if(r[0]!=12&&!bidiInitiator(r[0])&&r[0]!=22)break;r[2]=base;
    }
}
int nrBidiVisual(const uint32_t*text,uint32_t count,uint32_t direction,uint32_t*out,uint32_t capacity) {
    uint32_t rows[NR_MAX_TEXT*7],visual[NR_MAX_TEXT*4],order[NR_MAX_TEXT],used=0;
    if(nrBidiLevels(text,count,direction,rows,NR_MAX_TEXT)<0||(!out&&capacity))return -1;
    for(uint32_t begin=0;begin<count;) {
        uint32_t end=begin;while(end<count&&rows[end*7]!=10)end++;if(end<count)end++;
        uint32_t base=direction==2?(uint32_t)nrBidiParagraphLevel(text+begin,end-begin,0):direction;
        bidiLineReset(rows,begin,end,base);
        uint32_t length=0,highest=0,lowestOdd=UINT32_MAX;
        for(uint32_t i=begin;i<end;i++)if(!rows[i*7+3]) {
            order[length++]=i;uint32_t level=rows[i*7+2];if(level>highest)highest=level;
            if((level&1u)&&level<lowestOdd)lowestOdd=level;
        }
        if(lowestOdd!=UINT32_MAX)for(uint32_t level=highest;;level--) {
            for(uint32_t k=0;k<length;) {
                if(rows[order[k]*7+2]<level){k++;continue;}
                uint32_t first=k;while(k<length&&rows[order[k]*7+2]>=level)k++;
                for(uint32_t a=first,b=k-1;a<b;a++,b--){uint32_t swap=order[a];order[a]=order[b];order[b]=swap;}
            }
            if(level==lowestOdd)break;
        }
        for(uint32_t k=0;k<length;k++) {
            uint32_t i=order[k],level=rows[i*7+2];
            visual[used*4]=i;visual[used*4+1]=rows[i*7+1];visual[used*4+2]=level;
            visual[used*4+3]=(level&1u)?(uint32_t)nrBidiMirror(text[i]):text[i];used++;
        }
        begin=end;
    }
    if(!out&&!capacity)return (int)used;
    if(capacity<used||((uintptr_t)out%_Alignof(uint32_t)))return -1;
    if(used)memcpy(out,visual,(size_t)used*4*sizeof(*out));return (int)used;
}

static int bidiClusterLines(const uint32_t*text,uint32_t count,uint32_t direction,
                           const uint32_t*logical,int clusters,uint32_t*out,uint32_t capacity) {
    uint32_t levels[NR_MAX_TEXT*7],visual[NR_MAX_TEXT*7];
    uint32_t order[NR_MAX_TEXT],clusterLevels[NR_MAX_TEXT],firstKept[NR_MAX_TEXT],used=0;
    if((!out&&capacity)||nrBidiLevels(text,count,direction,levels,NR_MAX_TEXT)<0)return -1;
    uint32_t paragraphStart=0,paragraphEnd=0;
    for(uint32_t begin=0;begin<(uint32_t)clusters;) {
        uint32_t end=begin+1;while(end<(uint32_t)clusters&&logical[end*5+3]==logical[begin*5+3])end++;
        uint32_t startScalar=logical[begin*5],endScalar=logical[(end-1)*5+1];
        while(paragraphEnd<=startScalar&&paragraphEnd<count) {
            paragraphStart=paragraphEnd;
            while(paragraphEnd<count&&nrBidiClass(text[paragraphEnd])!=10)paragraphEnd++;
            if(paragraphEnd<count)paragraphEnd++;
        }
        uint32_t base=direction==2?(uint32_t)nrBidiParagraphLevel(text+paragraphStart,paragraphEnd-paragraphStart,0):direction;
        bidiLineReset(levels,startScalar,endScalar,base);
        uint32_t length=0,highest=0,lowestOdd=UINT32_MAX;
        for(uint32_t i=begin;i<end;i++) {
            uint32_t first=logical[i*5],last=logical[i*5+1],kept=first;
            while(kept<last&&levels[kept*7+3])kept++;
            if(kept==last)continue;
            firstKept[i]=kept;clusterLevels[i]=levels[kept*7+2];order[length++]=i;
            uint32_t level=clusterLevels[i];if(level>highest)highest=level;
            if((level&1u)&&level<lowestOdd)lowestOdd=level;
        }
        if(lowestOdd!=UINT32_MAX)for(uint32_t level=highest;;level--) {
            for(uint32_t k=0;k<length;) {
                if(clusterLevels[order[k]]<level){k++;continue;}
                uint32_t first=k;while(k<length&&clusterLevels[order[k]]>=level)k++;
                for(uint32_t a=first,b=k-1;a<b;a++,b--){uint32_t swap=order[a];order[a]=order[b];order[b]=swap;}
            }
            if(level==lowestOdd)break;
        }
        uint32_t x=0;
        for(uint32_t k=0;k<length;k++) {
            uint32_t i=order[k],level=clusterLevels[i],scalar=text[firstKept[i]],width=logical[i*5+4];
            uint32_t*r=visual+used++*7;r[0]=logical[i*5];r[1]=logical[i*5+1];r[2]=x;
            r[3]=logical[i*5+3];r[4]=width;r[5]=level;r[6]=(level&1u)?(uint32_t)nrBidiMirror(scalar):scalar;
            x+=width;
        }
        begin=end;
    }
    if(!out&&!capacity)return (int)used;
    if(capacity<used||((uintptr_t)out%_Alignof(uint32_t)))return -1;
    if(used)memcpy(out,visual,(size_t)used*7*sizeof(*out));return (int)used;
}

int nrBidiClusterLayout(const uint32_t*text,uint32_t count,uint32_t ambiguous,uint32_t columns,
                        uint32_t direction,uint32_t*out,uint32_t capacity) {
    uint32_t logical[NR_MAX_TEXT*5];
    int clusters=nrGraphemeLayout(text,count,ambiguous,columns,logical,NR_MAX_TEXT);
    if(clusters<0)return -1;
    return bidiClusterLines(text,count,direction,logical,clusters,out,capacity);
}

int nrBidiClusterLines(const uint32_t*text,uint32_t count,const uint32_t*ends,uint32_t lines,
                      uint32_t direction,uint32_t*out,uint32_t capacity) {
    uint32_t logical[NR_MAX_TEXT*5];
    if(lines>NR_MAX_TEXT||(lines&&(!ends||((uintptr_t)ends%4)))||(!lines&&count))return -1;
    int clusters=nrGraphemeLayout(text,count,1,UINT32_MAX,logical,NR_MAX_TEXT);
    if(clusters<0||(!count&&lines))return -1;
    uint32_t begin=0,cluster=0;
    for(uint32_t line=0;line<lines;line++) {
        uint32_t end=ends[line];if(end<=begin||end>count)return -1;
        uint32_t originalRow=logical[cluster*5+3];
        while(cluster<(uint32_t)clusters&&logical[cluster*5+1]<=end) {
            uint32_t*r=logical+cluster*5;
            if(r[3]!=originalRow)return -1;
            r[3]=line;cluster++;
        }
        if(!cluster||logical[(cluster-1)*5+1]!=end)return -1;
        begin=end;
    }
    if(begin!=count||cluster!=(uint32_t)clusters)return -1;
    return bidiClusterLines(text,count,direction,logical,clusters,out,capacity);
}

static void bidiClusterEdge(const uint32_t*text,const uint32_t*r,int end,uint32_t*out) {
    uint32_t scalar=text[r[0]];
    int newline=scalar==10||scalar==11||scalar==12||scalar==13||scalar==0x85||scalar==0x2028||scalar==0x2029;
    out[0]=newline?(end?0:r[2]):r[2]+(((r[5]&1u)?!end:end)?r[4]:0);
    out[1]=r[3]+(end&&newline);out[2]=r[5];
}
int nrBidiClusterHit(const uint32_t*text,uint32_t count,uint32_t ambiguous,uint32_t columns,
                     uint32_t direction,uint32_t column,uint32_t row) {
    uint32_t layout[NR_MAX_TEXT*7],selected=0;uint64_t bestRow=UINT64_MAX,bestColumn=UINT64_MAX;
    int n=nrBidiClusterLayout(text,count,ambiguous,columns,direction,layout,NR_MAX_TEXT);
    if(n<0)return -1;
    for(int i=0;i<n;i++)for(int end=0;end<2;end++) {
        uint32_t*r=layout+i*7,edge[3],at=r[end];bidiClusterEdge(text,r,end,edge);
        uint64_t dy=edge[1]>row?(uint64_t)edge[1]-row:(uint64_t)row-edge[1];
        uint64_t dx=edge[0]>column?(uint64_t)edge[0]-column:(uint64_t)column-edge[0];
        if(dy<bestRow||(dy==bestRow&&(dx<bestColumn||(dx==bestColumn&&at>selected)))){bestRow=dy;bestColumn=dx;selected=at;}
    }
    return (int)selected;
}
int nrBidiCaret(const uint32_t*text,uint32_t count,uint32_t ambiguous,uint32_t columns,
                 uint32_t direction,uint32_t offset,uint32_t affinity,uint32_t*out,uint32_t capacity) {
    uint32_t layout[NR_MAX_TEXT*7],chosen[3]={0,0,direction==1?1u:0u};
    if(!out||capacity<3||((uintptr_t)out%_Alignof(uint32_t))||offset>count||affinity>1)return -1;
    int n=nrBidiClusterLayout(text,count,ambiguous,columns,direction,layout,NR_MAX_TEXT);
    if(n<0||nrGraphemeFloor(text,(int)count,(int)offset)!=(int)offset)return -1;
    int found=0;
    for(int i=0;i<n;i++) {
        uint32_t*r=layout+i*7;
        for(int end=0;end<2;end++)if(r[end]==offset) {
            bidiClusterEdge(text,r,end,chosen);found=1;
            if(end==(affinity==0)){memcpy(out,chosen,sizeof(chosen));return 0;}
        }
    }
    if(!found&&n)return -1;
    memcpy(out,chosen,sizeof(chosen));return 0;
}

#include "document_bidi.inc"
