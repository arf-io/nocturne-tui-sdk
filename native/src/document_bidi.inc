/* Caller-owned form of the existing Unicode17 bidi algorithms. */
static int documentParagraphLevel(const uint32_t*text,uint32_t count,uint32_t fallback) {
    if((!text&&count)||fallback>1)return -1;
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

static int documentExplicit(const uint32_t*text,uint32_t count,uint32_t direction,uint32_t*out,uint32_t capacity) {
    if((!text&&count)||direction>2||(!out&&capacity))return -1;
    for(uint32_t i=0;i<count;i++)if(!bidiScalar(text[i]))return -1;
    if(!out&&!capacity)return (int)count;
    if(capacity<count||((uintptr_t)out%_Alignof(uint32_t)))return -1;
    uint32_t *rows=out;BidiStatus stack[127];
    uint32_t base=direction==2?(uint32_t)documentParagraphLevel(text,count,0):direction;
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
            base=direction==2?(uint32_t)documentParagraphLevel(text+i+1,count-i-1,0):direction;
            stack[0]=(BidiStatus){base,-1,0};
        } else if(type==9)removed=1;
        else if(stack[top].override>=0)type=stack[top].override;
        rows[(size_t)i*4]=(uint32_t)original;rows[(size_t)i*4+1]=(uint32_t)type;
        rows[(size_t)i*4+2]=level;rows[(size_t)i*4+3]=removed;
    }
    return (int)count;
}

static int documentWeak(const uint32_t*text,uint32_t count,uint32_t direction,uint32_t*out,uint32_t capacity,uint32_t*scratch,size_t stride) {
    uint32_t *explicitRows=scratch,*rows=out;
    if(documentExplicit(text,count,direction,explicitRows,count)<0||(!out&&capacity))return -1;
    if(!out&&!capacity)return (int)count;
    if(capacity<count||((uintptr_t)out%_Alignof(uint32_t)))return -1;
    for(uint32_t i=0;i<count;i++) {
        memcpy(rows+i*7,explicitRows+i*4,4*sizeof(*rows));
        rows[(size_t)i*7+4]=UINT32_MAX;rows[(size_t)i*7+5]=rows[(size_t)i*7+6]=0;
    }
    for(uint32_t begin=0;begin<count;) {
        uint32_t end=begin;while(end<count&&rows[(size_t)end*7]!=10)end++;if(end<count)end++;
        uint32_t base=direction==2?(uint32_t)documentParagraphLevel(text+begin,end-begin,0):direction;
        int32_t *match=(int32_t*)(scratch+4*stride),*runAt=(int32_t*)(scratch+5*stride),*next=(int32_t*)(scratch+6*stride),*incoming=(int32_t*)(scratch+7*stride);
        uint32_t *isolateStack=scratch+8*stride,depth=0,*indices=scratch+9*stride,length=0;
        uint32_t *first=scratch+10*stride,*last=scratch+11*stride,runs=0;
        for(uint32_t i=begin;i<end;i++) {
            match[i]=-1;runAt[i]=-1;
            if(bidiInitiator(rows[(size_t)i*7]))isolateStack[depth++]=i;
            else if(rows[(size_t)i*7]==22&&depth){uint32_t start=isolateStack[--depth];match[start]=(int)i;}
            if(!rows[(size_t)i*7+3])indices[length++]=i;
        }
        for(uint32_t k=0;k<length;k++) {
            uint32_t i=indices[k];
            if(!runs||rows[(size_t)i*7+2]!=rows[indices[k-1]*7+2]) {
                first[runs]=k;last[runs]=k;next[runs]=-1;incoming[runs]=0;runs++;
            } else last[runs-1]=k;
            runAt[i]=(int)runs-1;
        }
        for(uint32_t r=0;r<runs;r++) {
            uint32_t i=indices[last[r]];
            if(bidiInitiator(rows[(size_t)i*7])&&match[i]>=0) {
                int target=runAt[match[i]];
                if(target>(int)r&&rows[indices[first[target]]*7+2]==rows[(size_t)i*7+2]){next[r]=target;incoming[target]=1;}
            }
        }
        for(uint32_t root=0;root<runs;root++)if(!incoming[root]) {
            uint32_t *order=scratch+12*stride,used=0,r=root;
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
    return (int)count;
}

static void documentResolveSequence(const uint32_t*text,uint32_t*rows,const uint32_t*order,uint32_t count,uint32_t*starts,uint32_t*ends) {
    uint32_t stack[63],closing[63],depth=0,pairs=0;
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

static int documentLevels(const uint32_t*text,uint32_t count,uint32_t direction,uint32_t*rows,uint32_t*scratch,size_t stride){
    if(documentWeak(text,count,direction,rows,count,scratch,stride)<0)return -1;
    uint32_t *heads=scratch,*next=scratch+stride,*order=scratch+2*stride;
    uint32_t *starts=scratch+3*stride,*ends=scratch+4*stride;
    for(uint32_t i=0;i<count;i++)heads[i]=UINT32_MAX;
    for(uint32_t i=count;i>0;){i--;if(rows[(size_t)i*7+3])continue;
        uint32_t root=rows[(size_t)i*7+4];if(root>=count)return -1;
        next[i]=heads[root];heads[root]=i;
    }
    for(uint32_t root=0;root<count;root++)if(heads[root]!=UINT32_MAX){
        uint32_t used=0;for(uint32_t i=heads[root];i!=UINT32_MAX;i=next[i])order[used++]=i;
        documentResolveSequence(text,rows,order,used,starts,ends);
    }return (int)count;
}

static int documentClusterLines(const uint32_t*text,uint32_t count,uint32_t direction,
                           const uint32_t*logical,int clusters,uint32_t*out,uint32_t capacity,uint32_t*scratch,size_t stride) {
    uint32_t *levels=scratch,*visual=scratch+7*stride;
    uint32_t *order=scratch+14*stride,*clusterLevels=scratch+15*stride,*firstKept=scratch+16*stride,used=0;
    if((!out&&capacity)||documentLevels(text,count,direction,levels,scratch+17*stride,stride)<0)return -1;
    uint32_t paragraphStart=0,paragraphEnd=0;
    for(uint32_t begin=0;begin<(uint32_t)clusters;) {
        uint32_t end=begin+1;while(end<(uint32_t)clusters&&logical[(size_t)end*5+3]==logical[(size_t)begin*5+3])end++;
        uint32_t startScalar=logical[(size_t)begin*5],endScalar=logical[(end-1)*5+1];
        while(paragraphEnd<=startScalar&&paragraphEnd<count) {
            paragraphStart=paragraphEnd;
            while(paragraphEnd<count&&nrBidiClass(text[paragraphEnd])!=10)paragraphEnd++;
            if(paragraphEnd<count)paragraphEnd++;
        }
        uint32_t base=direction==2?(uint32_t)documentParagraphLevel(text+paragraphStart,paragraphEnd-paragraphStart,0):direction;
        bidiLineReset(levels,startScalar,endScalar,base);
        uint32_t length=0,highest=0,lowestOdd=UINT32_MAX;
        for(uint32_t i=begin;i<end;i++) {
            uint32_t first=logical[(size_t)i*5],last=logical[(size_t)i*5+1],kept=first;
            while(kept<last&&levels[(size_t)kept*7+3])kept++;
            if(kept==last)continue;
            firstKept[i]=kept;clusterLevels[i]=levels[(size_t)kept*7+2];order[length++]=i;
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
            uint32_t i=order[k],level=clusterLevels[i],scalar=text[firstKept[i]],width=logical[(size_t)i*5+4];
            uint32_t*r=visual+used++*7;r[0]=logical[(size_t)i*5];r[1]=logical[(size_t)i*5+1];r[2]=x;
            r[3]=logical[(size_t)i*5+3];r[4]=width;r[5]=level;r[6]=(level&1u)?(uint32_t)nrBidiMirror(scalar):scalar;
            x+=width;
        }
        begin=end;
    }
    if(!out&&!capacity)return (int)used;
    if(capacity<used||((uintptr_t)out%_Alignof(uint32_t)))return -1;
    if(used)memcpy(out,visual,(size_t)used*7*sizeof(*out));return (int)used;
}

int nrDocumentBidiClusterLayout(const uint32_t*text,uint32_t count,uint32_t ambiguous,uint32_t columns,
    uint32_t direction,uint32_t*out,uint32_t capacity,uint32_t*scratch,uint64_t scratchWords){
    uint64_t required=((uint64_t)count+1)*40;
    if(count>INT32_MAX||direction>2||!columns||(ambiguous!=1&&ambiguous!=2)||(!text&&count)||(!out&&capacity))return -1;
    if(!count)return 0;
    if(!scratch||scratchWords<required||required>SIZE_MAX/4||((uintptr_t)scratch%4)||((uintptr_t)text%4)||((uintptr_t)out%4))return -1;
    if(nrGraphemeOutputOverlaps(text,count,scratch,required)||nrGraphemeOutputOverlaps(text,count,out,(uint64_t)capacity*7))return -1;
    uintptr_t a=(uintptr_t)scratch,b=(uintptr_t)out;uint64_t outputBytes=(uint64_t)capacity*7*4;
    if(out&&outputBytes&&(a<=b?(uint64_t)(b-a)<required*4:(uint64_t)(a-b)<outputBytes))return -1;
    size_t stride=(size_t)count+1;uint32_t*logical=scratch;
    int clusters=nrDocumentGraphemeLayout(text,count,ambiguous,columns,logical,count);
    if(clusters<0)return -1;
    return documentClusterLines(text,count,direction,logical,clusters,out,capacity,scratch+5*stride,stride);
}
