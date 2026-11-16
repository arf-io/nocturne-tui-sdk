#include "internal.h"
#include "document_bidi.h"
static void bidiPromptCoordinates(const State*,int [NR_MAX_TEXT+1][2]);
int nrPromptHardBreak(uint32_t g){return g==10||g==11||g==12||g==13||g==0x85||g==0x2028||g==0x2029;}
int nrPromptLogical(const State*s,uint32_t*out){
    if(NR_PROMPT_BIDI(s)){uint32_t*visual=s->dynamicPrompt.scratch+36*((size_t)s->dynamicPrompt.capacity+1);int n=nrPromptVisualRows(s,visual);for(int i=0;i<n;i++)memcpy(out+i*5,visual+i*7,5*sizeof(uint32_t));return n;}
    const Prompt*p=&s->promptDocument;int n=nrDocumentGraphemeLayout(p->glyphs,p->count,s->promptPresentation.ambiguous,nrPromptColumns(s),out,s->dynamicPrompt.capacity);
    if(p->mode==0){uint32_t x=0;for(int k=0;k<n;k++){uint32_t*r=out+5*k;r[2]=x;r[3]=0;if(p->glyphs[r[0]]==9)r[4]=4-x%4;x+=r[4];}}
    return n;
}
void nrPromptGraphemeCoordinates(const State*s,int out[NR_MAX_TEXT+1][2]){
    if(NR_PROMPT_BIDI(s)){bidiPromptCoordinates(s,out);return;}
    const Prompt*p=&s->promptDocument;uint32_t*rows=s->dynamicPrompt.scratch+31*((size_t)s->dynamicPrompt.capacity+1);int n=nrPromptLogical(s,rows),cols=nrPromptColumns(s),height=nrPromptRows(s),top=(int)s->height-height-2;if(top<3)top=3;
    for(int i=0;i<=p->count;i++){out[i][0]=0;out[i][1]=0;}
    for(int k=0;k<n;k++){uint32_t*r=rows+k*5;for(uint32_t i=r[0];i<r[1];i++){out[i][0]=r[2];out[i][1]=r[3];}out[r[1]][0]=r[2]+r[4];out[r[1]][1]=r[3];if(p->mode!=0&&nrPromptHardBreak(p->glyphs[r[0]])){out[r[1]][0]=0;out[r[1]][1]++;}}
    int origin=nrGraphemeFloor(p->glyphs,p->count,p->caret),first=0,start=0;
    if(p->mode==0){int minimum=out[origin][0]-cols;if(minimum>0){start=out[origin][0];for(int k=0;k<n;k++)if((int)rows[k*5+2]>=minimum){start=rows[k*5+2];break;}}}
    else {int caretRow=out[origin][1];first=caretRow>=height?caretRow-height+1:0;if(p->mode>=2)top=(p->mode==3?3:top-2)+2;}
    for(int i=0;i<=p->count;i++){out[i][0]+=2-start;out[i][1]+=top-first;}
}
static int promptTop(const State*s){int top=(int)s->height-nrPromptRows(s)-2;if(top<3)top=3;if(s->promptDocument.mode>=2)top=(s->promptDocument.mode==3?3:top-2)+2;return top;}
static int spanVisible(const State*s,int top,int x,int y,int width){return s->promptDocument.active&&width>0&&x>=2&&(int64_t)x+width<=(int64_t)s->width-1&&y>=top&&y<(int)s->height-2;}
int nrPromptSpanVisible(const State*s,int x,int y,int width){return spanVisible(s,promptTop(s),x,y,width);}
int nrPromptGraphemeHit(const State*s,int x,int y){
    if(NR_PROMPT_BIDI(s)){double*rows=(double*)(s->dynamicPrompt.scratch+2*((size_t)s->dynamicPrompt.capacity+1));int n=nrPromptVisualMap(s,rows),best=nrGraphemeFloor(s->promptDocument.glyphs,s->promptDocument.count,s->promptDocument.caret),bestRow=INT32_MAX,bestCol=INT32_MAX;
        for(int k=0;k<n;k++){double*r=rows+k*10;if(!r[7])continue;for(int end=0;end<2;end++){int edge=(((int)r[8]&1)?!end:end),dx=(int)r[5]+edge*(int)r[4]-x,dy=(int)r[6]-y,index=(int)r[end];if(dx<0)dx=-dx;if(dy<0)dy=-dy;if(dy<bestRow||(dy==bestRow&&(dx<bestCol||(dx==bestCol&&index>best)))){best=index;bestRow=dy;bestCol=dx;}}}return best;}
    uint32_t*rows=s->dynamicPrompt.scratch+43*((size_t)s->dynamicPrompt.capacity+1);int n=nrPromptLogical(s,rows);int(*map)[2]=(int(*)[2])(s->dynamicPrompt.scratch+29*((size_t)s->dynamicPrompt.capacity+1));nrPromptGraphemeCoordinates(s,map);
    int top=promptTop(s),best=nrGraphemeFloor(s->promptDocument.glyphs,s->promptDocument.count,s->promptDocument.caret),bestRow=INT32_MAX,bestCol=INT32_MAX;
    for(int k=0;k<n;k++){uint32_t*r=rows+k*5;int cx=map[r[0]][0],cy=map[r[0]][1];if(!spanVisible(s,top,cx,cy,r[4]))continue;
        for(int edge=0;edge<2;edge++){int dx=cx+(edge?r[4]:0)-x,dy=cy-y;if(dx<0)dx=-dx;if(dy<0)dy=-dy;int index=r[edge];if(dy<bestRow||(dy==bestRow&&(dx<bestCol||(dx==bestCol&&index>best)))){best=index;bestRow=dy;bestCol=dx;}}}
    return best;
}
int nrPromptLayout(const NrContext*c,double*out,uint32_t capacity){
    if(!c||c->state.magic!=NR_MAGIC)return -1;const State*s=&c->state;if(s->firstPromptSource.enabled||!s->promptPresentation.layout)return 0;
    double*rows=(double*)(s->dynamicPrompt.scratch+2*((size_t)s->dynamicPrompt.capacity+1));int n=nrPromptVisualMap(s,rows);if(n<0)return -1;if(!out&&!capacity)return n;
    if(!out||capacity<(uint32_t)n||((uintptr_t)out%8)||!nrExternalOutput(c,out,(size_t)n*8*sizeof(double)))return -1;
    for(int k=0;k<n;k++)memcpy(out+8*k,rows+10*k,8*sizeof(double));return n;
}

/* Visual geometry reuses the native paragraph resolver. Marquee retains each
 * paragraph's bidi resolution but flattens its completed visual rows. */
int nrPromptVisualRows(const State*s,uint32_t*out){
    if(NR_PROMPT_BIDI(s)){
        int n=nrDocumentBidiClusterLayout(s->promptDocument.glyphs,s->promptDocument.count,s->promptPresentation.ambiguous,
            s->promptDocument.mode==0?UINT32_MAX:(uint32_t)nrPromptColumns(s),NR_PROMPT_DIRECTION(s),out,s->dynamicPrompt.capacity,s->dynamicPrompt.scratch+64*((size_t)s->dynamicPrompt.capacity+1),40*((uint64_t)s->dynamicPrompt.capacity+1));
        if(s->promptDocument.mode==0){uint32_t x=0;for(int i=0;i<n;i++){uint32_t*r=out+7*i;r[2]=x;r[3]=0;x+=r[4];}}
        return n;
    }
    uint32_t*logical=s->dynamicPrompt.scratch+43*((size_t)s->dynamicPrompt.capacity+1);int n=nrPromptLogical(s,logical);
    for(int i=0;i<n;i++){memcpy(out+7*i,logical+5*i,5*sizeof(uint32_t));out[7*i+5]=0;out[7*i+6]=s->promptDocument.glyphs[logical[5*i]];}return n;
}
static void bidiPromptRaw(const State*s,const uint32_t*rows,int n,int map[NR_MAX_TEXT+1][2]){
    unsigned char*found=(unsigned char*)(s->dynamicPrompt.scratch+48*((size_t)s->dynamicPrompt.capacity+1));memset(found,0,(size_t)s->dynamicPrompt.capacity+1);
    for(int i=0;i<=s->promptDocument.count;i++){map[i][0]=0;map[i][1]=0;}
    /* Preceding-end affinity at ambiguous boundaries, following-start fallback.
     * Interior offsets map to the containing cluster's start edge. */
    for(int k=0;k<n;k++){const uint32_t*r=rows+k*7;int x=r[2]+((r[5]&1)?r[4]:0);
        for(uint32_t i=r[0];i<r[1];i++){if(!found[i]){map[i][0]=x;map[i][1]=r[3];found[i]=1;}}}
    for(int k=0;k<n;k++){const uint32_t*r=rows+k*7;int x=r[2]+((r[5]&1)?0:r[4]),y=r[3];
        if(s->promptDocument.mode!=0&&nrPromptHardBreak(s->promptDocument.glyphs[r[0]])){x=0;y++;}
        map[r[1]][0]=x;map[r[1]][1]=y;found[r[1]]=1;}
    for(int i=1;i<=s->promptDocument.count;i++)if(!found[i]){map[i][0]=map[i-1][0];map[i][1]=map[i-1][1];}
}
static void bidiPromptOffset(const State*s,const uint32_t*rows,int n,int*x,int*y){
    int(*map)[2]=(int(*)[2])(s->dynamicPrompt.scratch+49*((size_t)s->dynamicPrompt.capacity+1));bidiPromptRaw(s,rows,n,map);
    int height=nrPromptRows(s),top=(int)s->height-height-2;if(top<3)top=3;
    int origin=nrGraphemeFloor(s->promptDocument.glyphs,s->promptDocument.count,s->promptDocument.caret),start=0,first=0;
    if(s->promptDocument.mode==0){int minimum=map[origin][0]-nrPromptColumns(s);if(minimum>0){start=map[origin][0];for(int k=0;k<n;k++)if((int)rows[k*7+2]>=minimum){start=rows[k*7+2];break;}}}
    else {int caretRow=map[origin][1];first=caretRow>=height?caretRow-height+1:0;if(s->promptDocument.mode>=2)top=(s->promptDocument.mode==3?3:top-2)+2;}
    *x=2-start;*y=top-first;
}
static void bidiPromptCoordinates(const State*s,int map[NR_MAX_TEXT+1][2]){
    uint32_t*rows=s->dynamicPrompt.scratch+22*((size_t)s->dynamicPrompt.capacity+1);int n=nrPromptVisualRows(s,rows),x,y;bidiPromptRaw(s,rows,n,map);bidiPromptOffset(s,rows,n,&x,&y);
    for(int i=0;i<=s->promptDocument.count;i++){map[i][0]+=x;map[i][1]+=y;}
}
int nrPromptVisualMap(const State*s,double*out){
    uint32_t*rows=s->dynamicPrompt.scratch+22*((size_t)s->dynamicPrompt.capacity+1);int n=nrPromptVisualRows(s,rows);if(n<0)return -1;
    int dx=0,dy=0;int(*map)[2]=(int(*)[2])(s->dynamicPrompt.scratch+29*((size_t)s->dynamicPrompt.capacity+1));
    if(NR_PROMPT_BIDI(s))bidiPromptOffset(s,rows,n,&dx,&dy);else nrPromptGraphemeCoordinates(s,map);
    int top=promptTop(s);
    for(int i=0;i<n;i++){uint32_t*r=rows+7*i;int x=NR_PROMPT_BIDI(s)?(int)r[2]+dx:map[r[0]][0],y=NR_PROMPT_BIDI(s)?(int)r[3]+dy:map[r[0]][1];
        double row[10]={r[0],r[1],r[2],r[3],r[4],x,y,spanVisible(s,top,x,y,r[4]),r[5],r[6]};memcpy(out+i*10,row,sizeof(row));}return n;
}
int nrPromptVisualLayout(const NrContext*c,double*out,uint32_t capacity){
    if(!c||c->state.magic!=NR_MAGIC)return -1;if(c->state.firstPromptSource.enabled||!c->state.promptPresentation.layout)return 0;const State*s=&c->state;
    double*rows=(double*)(s->dynamicPrompt.scratch+2*((size_t)s->dynamicPrompt.capacity+1));int n=nrPromptVisualMap(&c->state,rows);if(n<0)return -1;if(!out&&!capacity)return n;
    if(!out||capacity<(uint32_t)n||((uintptr_t)out%8)||!nrExternalOutput(c,out,(size_t)n*10*sizeof(double)))return -1;
    memcpy(out,rows,(size_t)n*10*sizeof(double));return n;
}
