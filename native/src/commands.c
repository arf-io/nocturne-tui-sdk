#include "internal.h"
#include "scenic_native.h"
/* Default native small-word profile: ASCII identifiers and non-ASCII source
   scalars form keyword runs; ASCII punctuation forms separate runs. */
static int promptWordClass(uint32_t g) {
    if(g==32||g==9||g==10)return 0;
    if(g>=128||g=='_'||(g>='a'&&g<='z')||(g>='A'&&g<='Z')||(g>='0'&&g<='9'))return 1;
    return 2;
}
static int reject(NrContext*c,const char*e) {
    if(!strcmp(c->error,"Prompt storage required"))return -1;
    size_t n=strlen(e);
    if(n>255)n=255;
    memcpy(c->error,e,n);
    c->error[n]=0;
    return -1;
}
static int number(const Json*j,int o,const char*k,double*v,double lo,double hi) {
    int t=nrField(j,o,k);
    if(t<0)return 1;
    double x;
    if(!nrNumber(j,t,&x)||x<lo||x>hi)return 0;
    *v=x;
    return 1;
}
static int integer(const Json*j,int o,const char*k,int*v,int lo,int hi) {
    int t=nrField(j,o,k);
    if(t<0)return 1;
    double x;
    if(!nrNumber(j,t,&x)||x<lo||x>hi||(int)x!=x)return 0;
    *v=(int)x;
    return 1;
}
static int uinteger(const Json*j,int o,const char*k,uint32_t*v,uint32_t lo,uint32_t hi) {
    int t=nrField(j,o,k);
    if(t<0)return 1;
    double x;
    if(!nrNumber(j,t,&x)||x<lo||x>hi||(uint32_t)x!=x)return 0;
    *v=(uint32_t)x;
    return 1;
}
static int duration(const Json*j,int o,const char*k,uint64_t*v,uint64_t max,int scale) {
    int t=nrField(j,o,k);
    if(t<0)return 1;
    double x;
    if(!nrNumber(j,t,&x)||x<0||x>(double)max/scale)return 0;
    double y=x*scale;
    if(y!=(uint64_t)y)return 0;
    *v=(uint64_t)y;
    return 1;
}
static int graphTextRows(const uint32_t*text,int count,int width) {
    int rows=1,column=0;
    if(width<1)return rows;
    for(int i=0;i<count;i++) {
        if(text[i]=='\n') {
            rows++;
            column=0;
        }
        else {
            if(column>=width) {
                rows++;
                column=0;
            }
            column++;
        }
    }
    return rows;
}
static int graphInspectorContentRows(const State*s,const Node*n) {
    int rows=graphTextRows(n->label,n->labelCount,32)+1;
    rows+=((int)strlen(n->status)+31)/32;
    if(n->sha[0]) {
        rows++;
        rows+=(int)strlen(n->sha)/32+1;
    }
    if(n->detailCount)rows+=graphTextRows(n->detail,n->detailCount,32)+1;
    rows++; /* PARENTS heading */
    for(int e=0;e<s->edgeCount;e++)if(s->edges[e].to==n->id) {
        int i=nrFindNode(s,s->edges[e].from);
        if(i>=0)rows+=2+graphTextRows(s->nodes[i].label,s->nodes[i].labelCount,30);
    }
    rows++; /* CHILDREN heading */
    for(int e=0;e<s->edgeCount;e++)if(s->edges[e].from==n->id) {
        int i=nrFindNode(s,s->edges[e].to);
        if(i>=0)rows+=2+graphTextRows(s->nodes[i].label,s->nodes[i].labelCount,30);
    }
    return rows;
}
static int graphInspectorMaxScroll(const State*s) {
    int selected=nrFindNode(s,s->selection);
    if(selected<0)return 0;
    int promptTop=(int)s->height-nrPromptRows(s)-2;
    if(promptTop<3)promptTop=3;
    int visibleRows=promptTop-7;
    if(visibleRows<1)return 0;
    int maxScroll=graphInspectorContentRows(s,&s->nodes[selected])-visibleRows;
    return maxScroll>0?maxScroll:0;
}
static int boolean(const Json*j,int o,const char*k,int*v) {
    int t=nrField(j,o,k);
    return t<0||nrBoolean(j,t,v);
}
static int vector(const Json*j,int o,const char*k,Vec3*v,double lo,double hi) {
    int a=nrField(j,o,k);
    if(a<0)return 1;
    if(j->tokens[a].type!=J_ARRAY||j->tokens[a].count!=3)return 0;
    double x[3];
    int t=a+1;
    for(int i=0; i<3; i++) {
        if(!nrNumber(j,t,&x[i])||x[i]<lo||x[i]>hi)return 0;
        t=j->tokens[t].next;
    }
    *v=nrV(x[0],x[1],x[2]);
    return 1;
}
static int choice(const Json*j,int o,const char*k,int*v,const char*list) {
    int t=nrField(j,o,k);
    if(t<0)return 1;
    char b[96];
    if(nrString(j,t,b,sizeof(b))<0)return 0;
    int i=0;
    for(const char*p=list; *p; i++) {
        const char*q=p;
        while(*q&&*q!=' ')q++;
        if(strlen(b)==(size_t)(q-p)&&!memcmp(p,b,q-p)) {
            *v=i;
            return 1;
        }
        p=*q?q+1:q;
    }
    return 0;
}
static int text(const Json*j,int o,const char*k,uint32_t*out,int*count,int cap) {
    int t=nrField(j,o,k);
    if(t<0)return 1;
    int n=nrDecode(j,t,out,cap);
    if(n<0)return 0;
    for(int i=0; i<n; i++)if(out[i]<32&&out[i]!=10&&out[i]!=9&&out[i]!=11&&out[i]!=12&&out[i]!=13)return 0;
    *count=n;
    return 1;
}
static int string(const Json*j,int o,const char*k,char*out,int cap) {
    int t=nrField(j,o,k);
    return t<0||nrString(j,t,out,cap)>=0;
}
static int effect(const Json*j,int o,int*e,int family) {
    int t=nrField(j,o,"effect");
    if(t<0)return 1;
    char b[96];
    if(nrString(j,t,b,sizeof(b))<0)return 0;
    int id=nrEffectId(b);
    if(id<0||nrEffectFamily(id)!=family)return 0;
    *e=id;
    return 1;
}
static int track(const Json*j,int token,Track*t,double lo,double hi) {
    if(token<0)return 1;
    if(j->tokens[token].type==J_NUMBER) {
        double v=j->tokens[token].number;
        if(v<lo||v>hi)return 0;
        t->initial=v;
        t->rate=0;
        return 1;
    }
    if(!nrAllowed(j,token,"initial rate min max step periodMs boundary easing seed"))return 0;
    return number(j,token,"initial",&t->initial,lo,hi)&&number(j,token,"rate",&t->rate,-10000,10000)&&number(j,token,"min",&t->min,lo,hi)&&number(j,token,"max",&t->max,lo,hi)&&number(j,token,"step",&t->step,-10000,10000)&&duration(j,token,"periodMs",&t->periodUs,3600000000ull,1000)&&choice(j,token,"boundary",&t->boundary,"clamp loop reverse random smooth-random")&&choice(j,token,"easing",&t->easing,"linear ease-in ease-out smooth smoother sine step")&&uinteger(j,token,"seed",&t->seed,0,0xffffffffu)&&t->min<=t->max&&t->periodUs>0;
}
int nrFindEmitter(const State*s,int id) {
    for(int i=0; i<(int)NR_MAX_EMITTERS; i++)if(s->emitters[i].used&&(int)s->emitters[i].id==id)return i;
    return -1;
}
int nrFindNode(const State*s,int id) {
    for(int i=0; i<(int)NR_MAX_NODES; i++)if(s->nodes[i].used&&s->nodes[i].id==id)return i;
    return -1;
}
int nrFindWindow(const State*s,int id) {
    for(int i=0; i<(int)NR_MAX_WINDOWS; i++)if(s->windows[i].used&&s->windows[i].id==id)return i;
    return -1;
}
#define CHECK(e,msg) do{if(!(e))return reject(c,msg);}while(0)
#define NUM(k,v,l,h) CHECK(number(j,0,k,&(v),l,h),"Invalid numeric parameter: " k)
#define INT(k,v,l,h) CHECK(integer(j,0,k,&(v),l,h),"Invalid integer parameter: " k)
#define BOOL(k,v) CHECK(boolean(j,0,k,&(v)),"Invalid boolean parameter: " k)
#define VEC(k,v,l,h) CHECK(vector(j,0,k,&(v),l,h),"Invalid vector parameter: " k)
#define DUR(k,v,m,sc) CHECK(duration(j,0,k,&(v),m,sc),"Invalid duration: " k)
#define CHOICE(k,v,list) CHECK(choice(j,0,k,&(v),list),"Invalid choice: " k)
#define ALLOW(list) CHECK(nrAllowed(j,0,"op " list),"Unknown or unsupported parameter")
#define SLOT(array,N,id,idx) do {idx=-1;for(int z=0;z<(int)(N);z++)if((array)[z].used&&(array)[z].id==id){idx=z;break;}if(idx<0){for(int z=0;z<(int)(N);z++)if(!(array)[z].used){idx=z;break;}}CHECK(idx>=0,"Component capacity reached");}while(0)
static void emitterDefaults(Emitter*e,int id,int eff,uint32_t seed,uint64_t now) {
    memset(e,0,sizeof(*e));
    e->used=1;
    e->id=(uint32_t)id;
    e->effect=eff;
    e->seed=nrHash(seed^(uint32_t)id);
    e->startUs=now;
    e->count=100;
    e->material=1;
    e->shape=1;
    e->schedule=0;
    e->runningUs=8000000;
    e->lifeMinUs=8000000;
    e->lifeMaxUs=14000000;
    e->position=nrV(0,18,0);
    e->extent=nrV(28,6,22);
    e->velocity=nrV(0,-1,0);
    e->spread=nrV(1,1,1);
    e->gravity=nrV(0,-4,0);
    e->wind=nrV(1.5,0,.8);
    e->windVariation=nrV(.8,.15,1);
    e->tumble=nrV(45,65,90);
    e->shapeWeights=nrV(1,0,0);
    e->drag=1.4;
    e->lift=.3;
    e->flutterHz=1.4;
    e->flutterAmount=.5;
    e->sizeMin=.6;
    e->sizeMax=1.4;
    e->alpha=.95;
    e->collision=1;
    e->deposit=1;
    e->radius=6;
    e->heat=12;
    e->trailUs=120000;
    e->birthFadeUs=120000;
    e->deathFadeUs=700000;
    e->tailUs=3000000;
    e->windScale=12;
    e->windPeriod=6;
    e->coreUs=120000;
    e->cycles=1;e->nearDistance=.001;e->farDistance=10000;e->farFade=0;
    e->twoSided=1;e->veinContrast=.75;e->curl=0;e->backTint=.3;
    e->sampling=2;e->surfaceAlpha=.22;
    int a=nrEffectAlgorithm(eff);
    if(a==1) {
        e->count=800;
        e->velocity=nrV(1,-20,0);
        e->gravity=nrV(0,-9,0);
        e->sizeMin=.04;
        e->sizeMax=.18;
        e->drag=.12;
        e->deposit=0;
        e->material=2;
    }
    else if(a==2) {
        e->count=240;
        e->velocity=nrV(0,-.6,0);
        e->gravity=nrV(0,-1,0);
        e->drag=2.1;
        e->sizeMin=.16;
        e->sizeMax=.55;
        e->material=2;
    }
    else if(a==3) {
        e->count=240;
        e->position=nrV(0,.3,0);
        e->extent=nrV(3,.4,3);
        e->velocity=nrV(0,7,0);
        e->spread=nrV(2,4,2);
        e->gravity=nrV(0,-6,0);
        e->lifeMinUs=2000000;
        e->lifeMaxUs=9000000;
        e->sizeMin=.03;
        e->sizeMax=.16;
    }
    else if(a>=4) {
        e->runningUs=0;
        e->position=nrV(0,10,0);
        e->extent=nrV(.1,.1,.1);
        e->shape=0;
        e->collision=0;
        e->deposit=0;
        e->gravity=nrV(0,-1.5,0);
        e->drag=.16;
        e->lifeMinUs=2200000;
        e->lifeMaxUs=6000000;
        e->sizeMin=.07;
        e->sizeMax=.16;
        e->wind=nrV(0,0,0);
        if(a==5) {
            e->gravity=nrV(0,0,0);
            if(nrEffectProfile(eff)==1||nrEffectProfile(eff)==2){e->topology=5;e->drag=0;e->spread=nrV(0,0,0);}
            if(nrEffectProfile(eff)==1){e->birthFadeUs=0;e->deathFadeUs=0;}
            e->lifeMinUs=4500000;
            e->lifeMaxUs=7000000;
        }
        if(a==6) {
            e->count=24;
            e->lifeMinUs=500000;
            e->lifeMaxUs=1400000;
            e->gravity=nrV(0,0,0);
            e->extent=nrV(15,9,12);
            e->shape=1;
        }
    }
}
static int newField(State*s,double x,double y,int eff) {
    if(s->nextField==0xffffffffu){s->fieldOverflow++;return -1;}
    int slot=-1;
    for(int i=0; i<NR_FIELDS; i++)if(!s->fields[i].used) {
        slot=i;
        break;
    }
    if(slot<0) {
        s->fieldOverflow++;
        return -1;
    }
    Field*f=&s->fields[slot];
    memset(f,0,sizeof(*f));
    memset(&s->fieldControls[slot],0,sizeof(s->fieldControls[slot]));
    f->used=1;
    f->id=s->nextField++;
    f->seed=nrHash(s->seed^f->id);
    f->effect=eff;
    f->material=1;
    f->x=x;
    f->y=y;
    f->atUs=s->timeUs;
    f->lifeUs=3000000;
    f->width=1.4;
    f->speed=8;
    f->strength=.65;
    return slot;
}
static int vimWordDestination(const Prompt*p,char key,int unit,int operatorEnd){
                int motion=key>='a'&&key<='z'?key-32:key;
                int small=key>='a'&&key<='z';
                int at=unit?nrGraphemeFloor(p->glyphs,p->count,p->caret):p->caret;
                int destination=motion=='B'?0:p->count;
                if(!operatorEnd&&p->count&&p->glyphs[p->count-1]!=10)
                    destination=motion=='B'?0:unit?nrGraphemeBefore(p->glyphs,p->count,p->count):p->count-1;
                for(int i=0;i<=p->count;) {
                    int start=i,end=i,empty=0;
                    if(i==p->count) {
                        if(!i||p->glyphs[i-1]!=10)break;
                        empty=1;i++;
                    } else if(p->glyphs[i]==10&&(i==0||p->glyphs[i-1]==10)) {
                        empty=1;i++;
                    } else if(p->glyphs[i]==32||p->glyphs[i]==9||p->glyphs[i]==10) {i++;continue;}
                    else {
                        int kind=promptWordClass(p->glyphs[i]);
                        while(i<p->count&&promptWordClass(p->glyphs[i])&&(!small||promptWordClass(p->glyphs[i])==kind))i++;
                        end=i;
                    }
                    if(motion=='B') {if(start<at)destination=start;else break;}
                    else if(motion=='W') {if(start>at) {destination=start;break;}}
                    else if(!empty) {
                        int last=unit?nrGraphemeBefore(p->glyphs,p->count,end):end-1;
                        if(last>at||(operatorEnd==2&&last==at)) {destination=last;break;}
                    }
                }
                return unit?nrGraphemeFloor(p->glyphs,p->count,destination):destination;
}

static void vimCancelRegister(State*s){s->promptRegisters.pending=0;s->promptRegisters.selected=0;s->promptRegisters.append=0;}
static int vimStoreRegister(State*s,int a,int b,int linewise){
    int selected=s->promptRegisters.selected,append=s->promptRegisters.append;vimCancelRegister(s);
    if(b<=a||selected==-1)return 1;
    if(selected>0){
        int slot=selected-1,old=append?s->promptRegisters.slots[slot].count:0;
        int separator=old>0&&s->promptRegisters.slots[slot].glyphs[old-1]!=10&&(s->promptRegisters.slots[slot].linewise||linewise);
        if(!nrPromptRequire(s,(uint64_t)old+separator+b-a))return 0;
        if(!append){memset(s->promptRegisters.slots[slot].glyphs,0,(size_t)s->promptRegisters.slots[slot].count*4);s->promptRegisters.slots[slot].count=s->promptRegisters.slots[slot].linewise=0;}
        if(separator)s->promptRegisters.slots[slot].glyphs[old++]=10;
        memcpy(s->promptRegisters.slots[slot].glyphs+old,s->promptDocument.glyphs+a,(size_t)(b-a)*4);
        s->promptRegisters.slots[slot].count=old+b-a;s->promptRegisters.slots[slot].linewise=linewise||(append&&s->promptRegisters.slots[slot].linewise);
        memcpy(s->promptRegister.glyphs,s->promptRegisters.slots[slot].glyphs,(size_t)s->promptRegisters.slots[slot].count*4);s->promptRegister.count=s->promptRegisters.slots[slot].count;s->promptRegister.linewise=s->promptRegisters.slots[slot].linewise;return 1;
    }
    memset(s->promptRegister.glyphs,0,(size_t)s->promptRegister.count*4);s->promptRegister.count=s->promptRegister.linewise=0;memcpy(s->promptRegister.glyphs,s->promptDocument.glyphs+a,(size_t)(b-a)*4);s->promptRegister.count=b-a;s->promptRegister.linewise=linewise;return 1;
}
static int pushUndo(State*s) {
    Prompt*p=&s->promptDocument;int k=p->undoHead;
    if(!nrPromptHistorySet(s,k,p->glyphs,p->count,p->caret))return 0;
    /* New edits discard redo contents as well as their traversal metadata. */
    for(int i=1;i<s->editorRedo.count;i++)if(!nrPromptHistorySet(s,(k+i)%NR_PROMPT_HISTORY,NULL,0,0))return 0;
    s->editorRedo.count=0;memset(&s->repeatEdit,0,sizeof(s->repeatEdit));
    p->undoHead=(k+1)%NR_PROMPT_HISTORY;if(p->undoSize<NR_PROMPT_HISTORY)p->undoSize++;return 1;
}
static int travelHistory(State*s,int redo){
    Prompt*p=&s->promptDocument;if(redo?!s->editorRedo.count:!p->undoSize)return 1;
    int slot=redo?p->undoHead:(p->undoHead+NR_PROMPT_HISTORY-1)%NR_PROMPT_HISTORY;
    uint32_t*saved=s->dynamicPrompt.scratch;memcpy(saved,p->glyphs,(size_t)p->count*4);int count=p->count,caret=p->caret;
    memset(p->glyphs,0,(size_t)p->count*4);memcpy(p->glyphs,p->undo[slot],(size_t)p->undoCount[slot]*4);p->count=p->undoCount[slot];p->caret=p->undoCaret[slot];
    if(!nrPromptHistorySet(s,slot,saved,count,caret))return 0;
    if(redo){p->undoHead=(slot+1)%NR_PROMPT_HISTORY;p->undoSize++;s->editorRedo.count--;}else{p->undoHead=slot;p->undoSize--;s->editorRedo.count++;}
    p->anchor=-1;p->revision++;return 1;
}
static int promptScalarsEqual(const uint32_t *text,int count,const char *ascii){
    size_t n=strlen(ascii);if(n!=(size_t)count)return 0;
    for(int i=0;i<count;i++)if(text[i]!=(unsigned char)ascii[i])return 0;
    return 1;
}
static int promptCommandSpace(uint32_t c){
    return c==9||c==11||c==12||c==32||c==0xa0||c==0x1680||
        (c>=0x2000&&c<=0x200a)||c==0x2028||c==0x2029||c==0x202f||
        c==0x205f||c==0x3000||c==0xfeff;
}
static void promptSetMessage(PromptFramed *f,const uint32_t *text,uint32_t count){
    if(count>512)count=512;
    memset(f->message,0,sizeof(f->message));
    if(count&&text)memcpy(f->message,text,(size_t)count*sizeof(uint32_t));
    f->messageCount=count;
}
static void promptMessageAscii(PromptFramed *f,const char *text){
    uint32_t scalars[512];uint32_t count=0;
    while(text[count]&&count<512){scalars[count]=(unsigned char)text[count];count++;}
    promptSetMessage(f,scalars,count);
}
static void promptSaveCheckpoint(State *s){
    Prompt *p=&s->promptDocument;PromptFramed *f=&s->promptFramed;
    memset(s->dynamicPrompt.checkpoint,0,(size_t)s->dynamicPrompt.capacity*4);
    if(p->count>0)memcpy(s->dynamicPrompt.checkpoint,p->glyphs,(size_t)p->count*sizeof(uint32_t));
    f->checkpointValid=1;f->checkpointCount=(uint32_t)p->count;
    f->checkpointCaret=(uint32_t)p->caret;f->checkpointMode=(uint32_t)p->mode;
    f->checkpointNormalMode=f->normalMode;f->checkpointVimState=f->vimState;
    f->checkpointOptions=f->options;
}
static int promptSearchNext(Prompt *p,PromptFramed *f){
    if(!f->searchCount||!p->count)return 0;
    for(int step=1;step<=p->count;step++){
        int at=(p->caret+step)%p->count;
        if((uint32_t)at+f->searchCount>(uint32_t)p->count)continue;
        if(!memcmp(p->glyphs+at,f->search,(size_t)f->searchCount*sizeof(uint32_t))){p->caret=at;return 1;}
    }
    promptMessageAscii(f,"Pattern not found");return 0;
}
static int promptLineJump(Prompt *p,uint32_t line){
    if(!line)line=1;
    uint32_t lines=1;for(int i=0;i<p->count;i++)if(p->glyphs[i]=='\n')lines++;
    if(line>lines)line=lines;
    if(line==1){p->caret=0;return 1;}
    uint32_t current=1;for(int i=0;i<p->count;i++)if(p->glyphs[i]=='\n'&&++current==line){p->caret=i+1;return 1;}
    p->caret=p->count;return 1;
}
static int promptFramedEx(NrContext *c,State *s){
    Prompt *p=&s->promptDocument;PromptFramed *f=&s->promptFramed;
    int start=0,end=(int)f->commandCount;
    promptSetMessage(f,NULL,0);
    if(start<end&&f->command[start]==':')start++;
    while(start<end&&promptCommandSpace(f->command[start]))start++;
    while(end>start&&promptCommandSpace(f->command[end-1]))end--;
    const uint32_t *cmd=f->command+start;int count=end-start;
    if(promptScalarsEqual(cmd,count,"q")||promptScalarsEqual(cmd,count,"q!")||
       promptScalarsEqual(cmd,count,"wq")||promptScalarsEqual(cmd,count,"x")){
        if(promptScalarsEqual(cmd,count,"wq")||promptScalarsEqual(cmd,count,"x"))promptSaveCheckpoint(s);
        if(nrPromptFramedActivate(c,s,-4)<0)return -1;
        p=&s->promptDocument;f=&s->promptFramed;
    }else if(promptScalarsEqual(cmd,count,"w")){
        promptSaveCheckpoint(s);
        promptMessageAscii(f,"Checkpoint retained in memory; Export saves to a file.");
    }else if(promptScalarsEqual(cmd,count,"undo")){
        CHECK(travelHistory(s,0),"Prompt history storage");
    }else if(promptScalarsEqual(cmd,count,"redo")){
        CHECK(travelHistory(s,1),"Prompt history storage");
    }else if(promptScalarsEqual(cmd,count,"set number")||promptScalarsEqual(cmd,count,"set nu")){
        f->options.lineNumbers=1;p->revision++;
    }else if(promptScalarsEqual(cmd,count,"set nonumber")||promptScalarsEqual(cmd,count,"set nonu")){
        f->options.lineNumbers=0;p->revision++;
    }else if(promptScalarsEqual(cmd,count,"help")){
        promptMessageAscii(f,"i a o / h j k l w b e 0 $ gg G / dd yy p x u Ctrl-R / :w :q :set number. Close never discards.");
    }else if(count>0){
        uint64_t line=0;int numeric=1;
        for(int i=0;i<count;i++){
            uint32_t ch=cmd[i];if(ch<'0'||ch>'9'){numeric=0;break;}
            line=line*10+(ch-'0');if(line>INT32_MAX)line=INT32_MAX;
        }
        if(numeric)promptLineJump(p,(uint32_t)line);
        else{
            static const char prefix[]="Unsupported command: ";
            uint32_t message[512],n=0;
            for(size_t i=0;prefix[i]&&n<512;i++)message[n++]=(unsigned char)prefix[i];
            for(int i=0;i<count&&n<512;i++)message[n++]=cmd[i];
            promptSetMessage(f,message,n);
        }
    }else{
        promptMessageAscii(f,"Unsupported command: ");
    }
    f=&s->promptFramed;p=&s->promptDocument;
    memset(f->command,0,sizeof(f->command));f->commandCount=0;
    f->vimState=NR_PROMPT_SOURCE_VIM_NORMAL;p->vimMode=0;
    s->vimCount.count=0;s->vimOperator.key=0;
    p->revision++;
    return 0;
}
int nrPromptFramedKey(NrContext *c,State *s,const Json *j,int ctrl,int shift,int alt,int meta){
    if(!c||!s||!j||(!s->promptFramed.enabled||s->firstPromptSource.enabled)||s->promptDocument.mode<NR_PROMPT_SOURCE_VIM_INLINE)return 0;
    if(ctrl||alt||meta)return 0;
    char key[64]={0};if(nrString(j,nrField(j,0,"key"),key,sizeof(key))<0)return reject(c,"Key string");
    Prompt *p=&s->promptDocument;PromptFramed *f=&s->promptFramed;
    if(f->vimState==NR_PROMPT_SOURCE_VIM_COMMAND){
        if(!strcmp(key,"Escape")){
            memset(f->command,0,sizeof(f->command));f->commandCount=0;
            f->vimState=NR_PROMPT_SOURCE_VIM_NORMAL;p->vimMode=0;p->revision++;return 1;
        }
        if(!strcmp(key,"Enter")){
            if(f->commandCount&&f->command[0]=='/'){
                memset(f->search,0,sizeof(f->search));
                f->searchCount=f->commandCount-1;
                if(f->searchCount)memcpy(f->search,f->command+1,(size_t)f->searchCount*sizeof(uint32_t));
                promptSearchNext(p,f);
                memset(f->command,0,sizeof(f->command));f->commandCount=0;
                f->vimState=NR_PROMPT_SOURCE_VIM_NORMAL;p->vimMode=0;p->revision++;return 1;
            }
            if(promptFramedEx(c,s)<0)return -1;
            return 1;
        }
        if(!strcmp(key,"Backspace")){
            if(f->commandCount)f->command[--f->commandCount]=0;
            p->revision++;return 1;
        }
        uint32_t scalar[2];int n=nrDecode(j,nrField(j,0,"key"),scalar,2);
        if(n==1){
            uint32_t units=0;for(uint32_t i=0;i<f->commandCount;i++)units+=f->command[i]>0xffff?2:1;
            if(units<256&&f->commandCount<256)f->command[f->commandCount++]=scalar[0];
        }
        p->revision++;return 1;
    }
    if(p->vimMode)return 0;
    if(!strcmp(key,":")||!strcmp(key,"/")){
        memset(f->command,0,sizeof(f->command));f->command[0]=(uint32_t)key[0];
        f->commandCount=1;f->vimState=NR_PROMPT_SOURCE_VIM_COMMAND;p->revision++;return 1;
    }
    if(!strcmp(key,"n")){
        promptSearchNext(p,f);p->revision++;return 1;
    }
    (void)shift;
    return 0;
}
static int repeatKey(NrContext*c,State*s,int key,int unit){
    char command[]="{\"op\":\"key\",\"key\":\"x\",\"unit\":\"scalar\"}";
    const char*prefix="{\"op\":\"key\",\"key\":\"";int at=(int)strlen(prefix);command[at]=(char)key;
    char text[80];int length=0;memcpy(text,command,(size_t)(at+1));length=at+1;
    const char*tail=unit?"\",\"unit\":\"grapheme\"}":"\",\"unit\":\"scalar\"}";int n=(int)strlen(tail);memcpy(text+length,tail,n);length+=n;
    if(!nrParse(&c->repeatJson,text,length))return reject(c,"Invalid retained repeat command");
    return nrApply(c,s,&c->repeatJson);
}
int nrInput(State*s,const uint32_t*g,int n,int emit) {
    if(nrModalBlocking(s))return 1;
    Prompt*p=&s->promptDocument;
    int start=p->caret,end=p->caret;
    if(p->anchor>=0) {start=p->anchor<p->caret?p->anchor:p->caret;end=p->anchor>p->caret?p->anchor:p->caret;}
    if(n<0||!nrPromptAllowed(s,(uint64_t)p->count-(end-start)+n)||!nrPromptRequire(s,(uint64_t)p->count-(end-start)+n))return 0;
    if(!pushUndo(s))return 0;
    memmove(p->glyphs+start+n,p->glyphs+end,(size_t)(p->count-end)*4);
    if(n)memcpy(p->glyphs+start,g,(size_t)n*4);
    int old=p->count;p->count+=n-(end-start);
    if(p->count<old)memset(p->glyphs+p->count,0,(size_t)(old-p->count)*4);
    p->caret=start+n;p->anchor=-1;
    p->revision++;
    if(emit&&!nrPromptAppearanceInput(s,start,n,emit==2?2:0)&&!nrWindowApplicationInput(s,(uint64_t)old,(uint64_t)n)){int(*coordinates)[2]=(int(*)[2])(s->dynamicPrompt.scratch+57*((size_t)s->dynamicPrompt.capacity+1));nrPromptCoordinates(s,coordinates);
        for(int i=0;i<n;i++)if(p->glyphs[start+i]!=10)newField(s,coordinates[start+i][0],coordinates[start+i][1],nrEffectId("surface-field/silk-tide"));}
    return 1;
}
static int bindNew(Value*v,const Json*j,int t) {
    if(t<0)return 1;
    if(!nrAllowed(j,t,"family id field"))return 0;
    if(nrField(j,t,"family")<0)return 0;
    v->bindingFamily=0;
    int f=0;
    if(!choice(j,t,"family",&f,"material emitter widget camera window text area floor state node indicator prompt environment field flow surface surface-wave float-body surface-foam mesh triangle cell-art accessibility electrical-arc"))return 0;
    v->bindingFamily=f+1;
    if(v->bindingFamily==14){uint32_t id=0;
        if(!uinteger(j,t,"id",&id,1,0xffffffffu))return 0;
        v->bindingId=(int32_t)id;return string(j,t,"field",v->field,sizeof(v->field))&&nrResourceBindingShapeValid(v);}
    return integer(j,t,"id",&v->bindingId,0,65535)&&string(j,t,"field",v->field,sizeof(v->field))&&nrResourceBindingShapeValid(v);
}
static int weatherCopySubtree(Json*out,const Json*in,int token) {
    if(token<0||token>=in->count)return -1;
    int end=in->tokens[token].next;
    if(end<=token||end>in->count||out->count+end-token>NR_JSON_TOKENS)return -1;
    int base=out->count,shift=base-token;
    for(int i=token;i<end;i++) {
        JToken copy=in->tokens[i];
        copy.next+=shift;
        out->tokens[out->count++]=copy;
    }
    return base;
}
static int weatherCopyPair(Json*out,const Json*in,int key,int value,int aliasStart,int aliasEnd,int*copiedValue) {
    int copiedKey=weatherCopySubtree(out,in,key);
    if(copiedKey<0)return 0;
    if(aliasStart>=0) {
        out->tokens[copiedKey].start=aliasStart;
        out->tokens[copiedKey].end=aliasEnd;
    }
    int valueBase=weatherCopySubtree(out,in,value);
    if(valueBase<0)return 0;
    if(copiedValue)*copiedValue=valueBase;
    out->tokens[0].count++;
    return 1;
}
static int weatherAuthorProjection(NrContext*c,const Json*source,Json*out,char*text) {
    static const char*groupNames[]={"emission","birth","forces","particle","collision","lifecycle"};
    static const char*groupKeys[]={
        "seed count rate runningTimeMs startTimeUs cycles gapMs schedule",
        "shape distribution position extent velocity spread orientation initialOrientation angularVelocity",
        "gravity wind windVariation drag lift flutterHz flutterAmount tumble heat windScale windPeriodSeconds",
        "shapeWeights sizeMin sizeMax material alpha radius topology trailMs birthFadeMs deathFadeMs coreMs nearDistance farDistance farFadeDistance veinContrast curl backTint twoSided sampling surfaceAlpha",
        "enabled deposit",
        "lifetimeMinMs lifetimeMaxMs endStyle tailMs"
    };
    if(!nrAllowed(source,0,"op schema id effect emission birth forces particle collision lifecycle"))
        return reject(c,"Unknown weather-author envelope field");
    int schema=nrField(source,0,"schema"),id=nrField(source,0,"id"),eff=nrField(source,0,"effect");
    if(schema<0||!nrEqual(source,schema,"nocturne.weather-authoring/v1"))
        return reject(c,"Unknown weather-author schema");
    if(id<0||eff<0)return reject(c,"Weather author requires id and effect");
    int groups[6];
    for(int i=0;i<6;i++) {
        groups[i]=nrField(source,0,groupNames[i]);
        if(groups[i]>=0&&(source->tokens[groups[i]].type!=J_OBJECT||!nrAllowed(source,groups[i],groupKeys[i])))
            return reject(c,"Invalid or unknown weather-author group field");
    }
    memcpy(text,source->text,(size_t)source->length);
    int textLength=source->length;
    int collisionAlias=textLength;
    memcpy(text+textLength,"\"collision\"",11);
    textLength+=11;
    int orientationAlias=textLength;
    memcpy(text+textLength,"\"birthOrientation\"",18);
    textLength+=18;
    text[textLength]=0;
    memset(out,0,sizeof(*out));
    out->text=text;
    out->length=textLength;
    out->count=1;
    out->tokens[0].type=J_OBJECT;
    out->tokens[0].start=0;
    out->tokens[0].end=textLength;
    int op=nrField(source,0,"op");
    if(op<0||!weatherCopyPair(out,source,op-1,op,-1,-1,0))
        return reject(c,"Weather-author projection capacity");
    int topValues[]={id,eff};
    for(int i=0;i<2;i++)if(!weatherCopyPair(out,source,topValues[i]-1,topValues[i],-1,-1,0))
        return reject(c,"Weather-author projection capacity");
    for(int g=0;g<6;g++)if(groups[g]>=0) {
        for(int key=groups[g]+1;key<source->tokens[groups[g]].next;) {
            int value=key+1;
            int alias=-1;
            if(g==4&&nrEqual(source,key,"enabled"))alias=collisionAlias;
            if(g==1&&nrEqual(source,key,"orientation"))alias=orientationAlias;
            int aliasEnd=alias<0?-1:alias+(alias==collisionAlias?11:18);
            if(!weatherCopyPair(out,source,key,value,alias,aliasEnd,0))
                return reject(c,"Weather-author projection token capacity");
            key=source->tokens[value].next;
        }
    }
    out->tokens[0].next=out->count;
    return 0;
}
/* Source painter order is independent of selection. Compact only at the
 * int32 boundary; relative ordering survives indefinitely without overflow. */
static void compactWindowOrder(State*s){
    int slots[NR_MAX_WINDOWS],count=0;
    for(int i=0;i<(int)NR_MAX_WINDOWS;i++)if(s->windowPresentation[i].enabled||s->atelierWindows[i].enabled){
        int at=count;while(at>0&&s->windowSourceOrder[slots[at-1]]>s->windowSourceOrder[i]){slots[at]=slots[at-1];at--;}
        slots[at]=i;count++;
    }
    for(int i=0;i<count;i++)s->windowSourceOrder[slots[i]]=i+1;
}
static void selectWindow(State*s,int id){
    s->selectedWindow=id;int slot=nrFindWindow(s,id);
    if(slot<0||(!s->windowPresentation[slot].enabled&&!s->atelierWindows[slot].enabled))return;
    int32_t maximum=0;
    for(int i=0;i<(int)NR_MAX_WINDOWS;i++)if(s->windowSourceOrder[i]>maximum)maximum=s->windowSourceOrder[i];
    if(maximum==INT32_MAX){compactWindowOrder(s);maximum=NR_MAX_WINDOWS;}
    s->windowSourceOrder[slot]=maximum+1;
}
static int backgroundWindow(State*s,int slot){
    if(slot<0||!s->windowPresentation[slot].enabled)return 0;
    Window*w=&s->windows[slot];double z=w->position.z;int32_t order=s->windowSourceOrder[slot];
    for(int i=0;i<(int)NR_MAX_WINDOWS;i++)if(s->windows[i].used){
        if(s->windows[i].position.z<z)z=s->windows[i].position.z;
        if(s->windowPresentation[i].enabled&&s->windowSourceOrder[i]<order)order=s->windowSourceOrder[i];
    }
    if(z-3 < -16000)return 0;
    if(order==INT32_MIN){compactWindowOrder(s);order=1;}
    /* Historical windows look down +Z. Public positions stay canonical -Z. */
    w->position.z=z-3;s->windowSourceOrder[slot]=order-1;return 1;
}
/* ---------- plan/commit pairs (native/docs/TRANSACTIONS.md) ----------
 * A plan reads a const State and the command, performs every check the op makes, and either rejects with the op's
 * own error text or returns the values its commit stores. The copy transaction's handler and the direct path call
 * the same pair, so both reject with the same text and write the same bytes. */
typedef struct {int paused;} PausePlan;
static int planPause(NrContext*c,const State*s,const Json*j,PausePlan*p){
    ALLOW("paused");
    int v=s->paused;
    BOOL("paused",v);
    p->paused=v;return 0;
}
/* BOOL leaves 0 or 1, the only bound nrValidState places on `paused`, its only reader (TDD F8). */
static void commitPause(State*s,const PausePlan*p){s->paused=p->paused;}
typedef struct {uint64_t t;int budget;} TimePlan;
static int planTime(NrContext*c,const State*s,const Json*j,TimePlan*p){
    ALLOW("timeUs budget");
    uint64_t t=s->targetUs;
    DUR("timeUs",t,86400000000ull,1);
    CHECK(t>=s->timeUs,"Time must be monotonic; restore a checkpoint to seek backward");
    int budget=240;
    INT("budget",budget,1,4096);
    p->t=t;p->budget=budget;return 0;
}
/* The clock and every per-step subsystem. `direct` is set only inside timeDirectDomain (below), where the scheduled
 * queue has nothing due and the values tick has nothing to do: both calls are skipped, and every CHECK below is
 * unreachable (each callee's only failure needs a resource the domain excludes). */
static int stepTime(NrContext*c,State*s,const TimePlan*plan,int direct){
    if(s->paused)return 0;
    uint64_t t=plan->t;int budget=plan->budget;
    s->targetUs=t;
    uint32_t desired=nrStepAt(t);
    while(s->step<desired&&budget-->0) {
        s->step++;
        s->timeUs=((uint64_t)s->step*1000000)/120;
        /* Scheduled commands see the status lifecycle at this boundary, not the previous one. */
        nrStatusTick(s);
        if(!direct)CHECK(nrApplyScheduled(c,s)>=0,"Scheduled transaction rejected; cancel it or repair its target");
        CHECK(nrPathActorsTick(s),"Path travel target range exceeded");
        CHECK(nrSurfaceFluidsTick(s),"Finite water motion range exceeded; transaction rolled back");
        CHECK(nrThermalTransport(s),"Thermal conduction range or solver failure; transaction rolled back");
        CHECK(nrSimulate(s),"Moving surface contact solver budget exhausted; transaction rolled back");
        CHECK(nrFloatBodiesTick(s),"Floating body numeric range exceeded; transaction rolled back");
        nrFoamTick(s);
        if(!direct)CHECK(nrValuesTick(c,s),"Trigger target rejected; transaction rolled back");
    }
    if(s->step<desired)return 1;
    s->timeUs=t;
    CHECK(nrPathActorsTick(s),"Path travel target range exceeded");
    nrStatusTick(s);
    if(!direct)CHECK(nrValuesTick(c,s),"Trigger target rejected; transaction rolled back");
    return 0;
}
/* The domain in which `time` cannot fail after its first write (TRANSACTIONS.md, "time"):
 *  - nothing scheduled at or before t, so nrApplyScheduled finds nothing due at any step;
 *  - no trigger and no style rule, so nrValuesTick changes nothing: its trigger loop has no subject, nrStylesTick
 *    has no rule, and its sync is a fixed point on a settled State whose text sources no step writes;
 *  - no path actor (nrPathActorsTick), no surface fluid (nrSurfaceFluidsTick), no thermal link or cell
 *    (nrThermalTransport, nrHeatTick), no water link (nrSurfaceWaterTransport), no mesh (surfaceMotion), no float
 *    body (nrFloatBodiesTick) and no flow (the non-monotone clock reader of nrValidFlowSprays): every failing
 *    return of every callee needs one of these. */
static int timeDirectDomain(const State*s,uint64_t t){
    if(s->meshCount)return 0;
    for(int i=0;i<NR_TRIGGERS;i++)if(s->triggers[i].used)return 0;
    for(int i=0;i<NR_STYLE_RULES;i++)if(s->styleRules[i].used)return 0;
    for(int i=0;i<NR_PENDING;i++)if(s->pending[i].used&&s->pending[i].atUs<=t)return 0;
    for(int i=0;i<16;i++)if(s->pathActors[i].used)return 0;
    for(int i=0;i<NR_SURFACES;i++)if(s->surfaceFluids[i].used)return 0;
    for(int i=0;i<64;i++)if(s->thermalLinks[i].used||s->waterLinks[i].used)return 0;
    for(int i=0;i<NR_MESH;i++)if(s->thermalCells[i].used)return 0;
    for(int i=0;i<NR_FLOAT_BODIES;i++)if(s->floatBodies[i].used)return 0;
    for(int i=0;i<8;i++)if(s->flows[i].used)return 0;
    for(int i=0;i<(int)NR_MAX_EMITTERS;i++)if(s->flowSprays[i].flowId)return 0;
    for(int i=0;i<NR_SURFACES;i++)if(s->flowSinks[i].flowId||s->flowSurfaces[i].flowId)return 0;
    return 1;
}
/* One widget record: planned into a copy of its slot, committed by one assignment. The handler reads no other
 * widget and writes nothing else; nrValidState's widget clauses read only the record and the clock (nrValidWidget). */
static int planWidget(NrContext*c,const State*s,const Json*j,Widget*w,int*slot){
    ALLOW("id kind x y width height padding alpha border material backgroundMaterial enabled selected active text value min max data mode pulseMs sampling cellAspect innerRadius startAngle sweepAngle revealMs replay");
    int id=0;
    INT("id",id,1,65535);
    CHECK(id,"Widget id");
    int i;
    SLOT(s->widgets,NR_WIDGETS,id,i);
    *w=s->widgets[i];*slot=i;
    if(!w->used) {
        memset(w,0,sizeof(*w));
        w->used=1;
        w->id=id;
        w->width=20;
        w->height=3;
        w->enabled=1;
        w->max=1;
        w->alpha=.25;
        w->material=2;
        w->backgroundMaterial=-1;
        w->pulseUs=1000000;
        w->sampling=-1;w->cellAspect=2;w->innerRadius=.6164414002968976;
        w->startAngle=0;w->sweepAngle=360;w->revealAtUs=s->timeUs;
    }
    CHOICE("kind",w->kind,"text box rule button item cursor progress bars pie donut scatter line digits edge checkbox radio select scrollbar");
    INT("x",w->x,NR_LAYOUT_MIN,NR_LAYOUT_MAX);
    INT("y",w->y,NR_LAYOUT_MIN,NR_LAYOUT_MAX);
    INT("width",w->width,1,NR_LAYOUT_MAX);
    INT("height",w->height,1,NR_LAYOUT_MAX);
    INT("padding",w->padding,0,8);
    NUM("alpha",w->alpha,0,1);
    CHOICE("border",w->border,"none rounded square double heavy");
    INT("material",w->material,0,15);
    INT("backgroundMaterial",w->backgroundMaterial,-1,15);
    BOOL("enabled",w->enabled);
    BOOL("selected",w->selected);
    BOOL("active",w->active);
    CHECK(text(j,0,"text",w->text,&w->count,NR_MAX_TEXT),"Widget text capacity");
    double previous=w->value;
    NUM("value",w->value,-1000000,1000000);
    NUM("min",w->min,-1000000,1000000);
    NUM("max",w->max,-1000000,1000000);
    CHECK(w->max>w->min,"Widget max must exceed min");
    INT("mode",w->mode,0,15);
    DUR("pulseMs",w->pulseUs,60000000,1000);
    int isPlot=w->kind>=6&&w->kind<=13,isCircular=w->kind==8||w->kind==9;
    CHECK(isPlot||(nrField(j,0,"sampling")<0&&nrField(j,0,"revealMs")<0&&nrField(j,0,"replay")<0),"Plot sampling/reveal settings require a geometric widget");
    CHECK(isCircular||(nrField(j,0,"cellAspect")<0&&nrField(j,0,"startAngle")<0&&nrField(j,0,"sweepAngle")<0),"Circular shape settings require pie/donut");
    CHECK(w->kind==9||nrField(j,0,"innerRadius")<0,"innerRadius requires donut");
    int sample=w->sampling+1;
    CHOICE("sampling",sample,"inherit cell half braille hybrid");w->sampling=sample-1;
    NUM("cellAspect",w->cellAspect,.5,4);
    NUM("innerRadius",w->innerRadius,0,.98);
    NUM("startAngle",w->startAngle,-36000,36000);
    NUM("sweepAngle",w->sweepAngle,0,360);
    DUR("revealMs",w->revealUs,60000000,1000);
    int replay=0;BOOL("replay",replay);if(replay)w->revealAtUs=s->timeUs;

    if(w->value!=previous)w->changedUs=s->timeUs;
    int a=nrField(j,0,"data");
    if(a>=0) {
        CHECK(j->tokens[a].type==J_ARRAY&&j->tokens[a].count<=128,"Widget data capacity");
        w->dataCount=j->tokens[a].count;
        int t=a+1;
        for(int k=0; k<w->dataCount; k++) {
            CHECK(nrNumber(j,t,&w->data[k])&&w->data[k]>=-1000000&&w->data[k]<=1000000,"Widget data range");
            t=j->tokens[t].next;
        }
    }
    return 0;
}
/* Prompt `select` (no id): checks, then the caret and anchor; nothing when another surface owns input. */
typedef struct {int caret,anchor,apply;} SelectPlan;
static int planPromptSelect(NrContext*c,const State*s,const Json*j,SelectPlan*q){
    ALLOW("anchor caret unit");
    const Prompt*p=&s->promptDocument;int anchor=p->caret,caret=p->caret,unit=0;
    INT("anchor",anchor,0,p->count);INT("caret",caret,0,p->count);
    CHOICE("unit",unit,"scalar grapheme");
    CHECK(!unit||(nrGraphemeFloor(p->glyphs,p->count,anchor)==anchor&&nrGraphemeFloor(p->glyphs,p->count,caret)==caret),"Selection must use complete grapheme boundaries");
    q->apply=!nrInputOwner(s);q->caret=caret;q->anchor=anchor==caret?-1:anchor;return 0;
}
static void commitPromptSelect(State*s,const SelectPlan*q){
    if(q->apply){s->promptDocument.caret=q->caret;s->promptDocument.anchor=q->anchor;}
}
/* `set`: the checks every form shares, before any write. */
static int planSetTarget(NrContext*c,const State*s,const Json*j,int*slot,int*expressionToken,int*intentToken){
    ALLOW("path value expression intentId");
    char path[128]= {
        0
    };
    CHECK(string(j,0,"path",path,sizeof(path)),"Value path");
    int i=-1;
    for(int k=0; k<NR_VALUES; k++)if(s->values[k].used&&!strcmp(s->values[k].path,path))i=k;
    CHECK(i>=0&&!s->values[i].readonly,"Missing or readonly value");
    int expression=nrField(j,0,"expression"),intent=nrField(j,0,"intentId");
    CHECK(expression<0||nrField(j,0,"value")<0,"Choose value OR expression");
    CHECK(expression>=0||intent<0,"intentId requires an expression");
    *slot=i;*expressionToken=expression;*intentToken=intent;return 0;
}
/* `draft` (TRANSACTIONS.md, "draft"): every check precedes the first write. The plan holds the decoded text, which
 * lives in the prompt arena's scratch words (never State authority), and the values the commit needs. */
typedef struct {const uint32_t*buf;int n,caret,emit;} DraftPlan;
static int planDraftTail(NrContext*c,const State*s,const Json*j,const uint32_t*buf,int n,DraftPlan*p){
    CHECK(nrPromptAllowed(s,(uint32_t)n),"Authored prompt capacity");
    int caret=n,emit=1;
    INT("caret",caret,0,n);
    BOOL("emitWeather",emit);
    p->buf=buf;p->n=n;p->caret=caret;p->emit=emit;return 0;
}
static int pushUndo(State*s);
static int newField(State*s,double x,double y,int eff);
/* The draft's writes. Its only failing step is pushUndo's history storage request; the direct path checks that
 * capacity in its plan (draftHistoryFits), so there the commit cannot fail. */
static int commitDraft(NrContext*c,State*s,const DraftPlan*plan){
    const uint32_t*buf=plan->buf;int n=plan->n,caret=plan->caret,emit=plan->emit;
    Prompt*p=&s->promptDocument;
    int start=0;
    while(start<n&&start<p->count&&buf[start]==p->glyphs[start])start++;
    int tail=0;
    while(tail<n-start&&tail<p->count-start&&buf[n-tail-1]==p->glyphs[p->count-tail-1])tail++;
    uint64_t priorUtf16Units=0,nextUtf16Units=0;
    for(int i=0;i<p->count;i++)priorUtf16Units+=p->glyphs[i]>0xffff?2u:1u;
    for(int i=0;i<n;i++)nextUtf16Units+=buf[i]>0xffff?2u:1u;
    int64_t firstDifference=start<p->count?start:-1;
    CHECK(pushUndo(s),"Prompt history storage");
    memset(p->glyphs,0,(size_t)p->count*4);
    memcpy(p->glyphs,buf,(size_t)n*4);
    p->count=n;p->anchor=-1;
    p->caret=caret;
    p->revision++;
    if(emit&&!nrPromptAppearanceInput(s,start,n-tail-start,1)&&!nrWindowApplicationDraft(s,priorUtf16Units,nextUtf16Units,(uint64_t)n,firstDifference)){int(*coordinates)[2]=(int(*)[2])(s->dynamicPrompt.scratch+57*((size_t)s->dynamicPrompt.capacity+1));nrPromptCoordinates(s,coordinates);
        for(int i=start;i<n-tail;i++)if(p->glyphs[i]!=10)newField(s,coordinates[i][0],coordinates[i][1],nrEffectId("surface-field/silk-tide"));}
    return 0;
}
/* One node record, planned into a copy of its slot and committed by one assignment (TRANSACTIONS.md, "node"). */
static int planNode(NrContext*c,const State*s,const Json*j,Node*n,int*slot,int*created){
    ALLOW("id label detail kind status sha position pinned color minColumns maxColumns padding shaPrefix showKind showStatus showSha showDetail");
    int id=0;
    INT("id",id,1,65535);
    CHECK(id,"Node id required");
    int i;
    SLOT(s->nodes,NR_MAX_NODES,id,i);
    *n=s->nodes[i];*slot=i;
    int creating=!n->used;*created=creating;
    if(creating) {
        memset(n,0,sizeof(*n));
        n->used=1;
        n->id=id;
        n->position=nrV((i%3-1)*38,18-(i/3)*20,0);
        n->minColumns=22;n->maxColumns=44;n->padding=1;
        n->showKind=n->showStatus=n->showSha=n->showDetail=1;
    }
    CHECK(text(j,0,"label",n->label,&n->labelCount,256)&&text(j,0,"detail",n->detail,&n->detailCount,512)&&string(j,0,"kind",n->kind,sizeof(n->kind))&&string(j,0,"status",n->status,sizeof(n->status))&&string(j,0,"sha",n->sha,sizeof(n->sha)),"Node metadata capacity");
    VEC("position",n->position,-16000,16000);
    BOOL("pinned",n->pinned);
    CHECK(uinteger(j,0,"color",&n->color,0,0xffffff),"Node RGB");
    INT("minColumns",n->minColumns,8,NR_LAYOUT_MAX);INT("maxColumns",n->maxColumns,8,NR_LAYOUT_MAX);
    INT("padding",n->padding,0,8);INT("shaPrefix",n->shaPrefix,0,128);
    BOOL("showKind",n->showKind);BOOL("showStatus",n->showStatus);
    BOOL("showSha",n->showSha);BOOL("showDetail",n->showDetail);
    CHECK(n->minColumns<=n->maxColumns&&n->minColumns>2*(n->padding+1),"Node content width must exceed border and padding");
    /* A metadata edit must not teleport a card during a layout/selection
       transition. Only an explicit placement resets the target pose. */
    if(creating||nrField(j,0,"position")>=0) {
        n->from=n->to=n->position;n->durationUs=0;n->atUs=s->timeUs;
    }
    return 0;
}
static int applyCommand(NrContext*c,State*s,const Json*j) {
    char op[48];
    CHECK(nrString(j,nrField(j,0,"op"),op,sizeof(op))>0,"op string required");
    if(!strcmp(op,"scene-art")||!strcmp(op,"remove-scene-art"))return nrSceneArtCommand(c,s,j);
    if(!strcmp(op,"model-view")||!strcmp(op,"remove-model-view"))return nrModelViewCommand(c,s,j);
    if(!strcmp(op,"window-content")||!strcmp(op,"remove-window-content"))return nrWindowContentCommand(c,s,j);
    if(!strcmp(op,"window-texture")||!strcmp(op,"remove-window-texture"))return nrWindowTextureCommand(c,s,j);
    if(!strcmp(op,"source-modal"))return nrSourceModalCommand(c,s,j);
    if(!strcmp(op,"source-stage"))return nrSourceStageSceneCommand(c,s,j);
    if(!strcmp(op,"observatory-overlay"))return nrOriginalObservatoryOverlayCommand(c,s,j);
    if(!strcmp(op,"source-stage-component")||!strcmp(op,"remove-source-stage-component"))return nrSourceStageCommand(c,s,j);
    if(!strcmp(op,"weather-author")) {
        if(weatherAuthorProjection(c,j,&c->projectedJson,c->projectedText)<0)return -1;
        j=&c->projectedJson;
        memcpy(op,"emitter",sizeof("emitter"));
    }
    if(!strcmp(op,"cell-art")||!strcmp(op,"remove-cell-art")){
        int id=0;INT("id",id,1,65535);CHECK(id,"Cell art id required");int slot=-1;
        for(int i=0;i<4;i++)if(s->cellArt[i].used&&s->cellArt[i].id==id)slot=i;
        if(!strcmp(op,"remove-cell-art")){ALLOW("id");if(slot>=0)memset(&s->cellArt[slot],0,sizeof(s->cellArt[slot]));return 0;}
        ALLOW("id width height cells x y alpha layer");
        if(slot<0){for(int i=0;i<4;i++)if(!s->cellArt[i].used){slot=i;break;}CHECK(slot>=0,"Cell art resource capacity");
            memset(&s->cellArt[slot],0,sizeof(s->cellArt[slot]));s->cellArt[slot].used=1;s->cellArt[slot].id=id;s->cellArt[slot].alpha=1;}
        int oldWidth=s->cellArt[slot].width,oldHeight=s->cellArt[slot].height;
        INT("width",s->cellArt[slot].width,1,2048);INT("height",s->cellArt[slot].height,1,2048);
        CHECK(s->cellArt[slot].width>0&&s->cellArt[slot].height>0&&s->cellArt[slot].width*s->cellArt[slot].height<=2048,"Cell art dimensions/capacity");
        INT("x",s->cellArt[slot].x,NR_LAYOUT_MIN,NR_LAYOUT_MAX);INT("y",s->cellArt[slot].y,NR_LAYOUT_MIN,NR_LAYOUT_MAX);NUM("alpha",s->cellArt[slot].alpha,0,1);
        int layer=s->cellArt[slot].layer;CHOICE("layer",layer,"background overlay");s->cellArt[slot].layer=layer;
        int token=nrField(j,0,"cells"),count=s->cellArt[slot].width*s->cellArt[slot].height;
        if(token>=0){CHECK(j->tokens[token].type==J_ARRAY&&j->tokens[token].count==count,"Cell art cell count");int row=token+1;
            for(int k=0;k<count;k++){
                CHECK(j->tokens[row].type==J_ARRAY&&j->tokens[row].count==3,"Cell art row [scalar,foreground,background]");int v=row+1;
                for(int word=0;word<3;word++){double value;CHECK(nrNumber(j,v,&value)&&value>=0&&value<=(word?0xffffff:0x10ffff)&&value==(uint32_t)value,"Cell art integer word");s->cellArt[slot].cells[k][word]=(uint32_t)value;v=j->tokens[v].next;}
                uint32_t g=s->cellArt[slot].cells[k][0];CHECK((g==0||g>=32)&&!(g>=0xd800&&g<=0xdfff),"Cell art Unicode scalar");row=j->tokens[row].next;
            }
        }else CHECK(oldWidth==s->cellArt[slot].width&&oldHeight==s->cellArt[slot].height,"Cell art cells required for new dimensions");
        return 0;
    }
    if(!strcmp(op,"surface-thermal-link")||!strcmp(op,"remove-surface-thermal-link"))return nrThermalLinkCommand(c,s,j);
    if(!strcmp(op,"surface-thermal-transfer"))return nrThermalTransferCommand(c,s,j);
    if(!strcmp(op,"surface-thermal")||!strcmp(op,"surface-thermal-power")||!strcmp(op,"surface-thermal-settings"))return nrThermalCommand(c,s,j);
    if(!strcmp(op,"aggregate-reemit"))return nrAggregateReemitCommand(c,s,j);
    if(!strcmp(op,"surface-water-reemit"))return nrSurfaceWaterReemitCommand(c,s,j);
    if(!strcmp(op,"surface-water-link")||!strcmp(op,"remove-surface-water-link"))return nrSurfaceWaterLinkCommand(c,s,j);
    if(!strcmp(op,"surface-water-transfer"))return nrSurfaceWaterTransferCommand(c,s,j);
    if(!strcmp(op,"surface-water-thermal"))return nrLatentHeatCommand(c,s,j);
    if(!strcmp(op,"surface-water-settings"))return nrSurfaceWaterSettingsCommand(c,s,j);
    if(!strcmp(op,"surface-water-add"))return nrSurfaceWaterAddCommand(c,s,j);
    if(!strcmp(op,"surface-water"))return nrSurfaceWaterCommand(c,s,j);
    if(!strcmp(op,"flow-spray"))return nrFlowSprayCommand(c,s,j);
    if(!strcmp(op,"flow-sink"))return nrFlowSinkCommand(c,s,j);
    if(!strcmp(op,"flow-thickness")||!strcmp(op,"flow-thickness-settings")||!strcmp(op,"remove-flow-thickness"))return nrFlowThicknessCommand(c,s,j);
    if(!strcmp(op,"flow-surface")||!strcmp(op,"remove-flow-surface"))return nrFlowSurfaceCommand(c,s,j);
    if(!strcmp(op,"flow")||!strcmp(op,"flow-rate"))return nrFlowCommand(c,s,j);
    if(!strcmp(op,"electrical-arc")||!strcmp(op,"remove-electrical-arc"))return nrElectricalArcCommand(c,s,j);
    if(!strcmp(op,"studio-style")||!strcmp(op,"remove-studio-style"))return nrStudioNovaCommand(c,s,j);
    if(!strcmp(op,"world-style")||!strcmp(op,"remove-world-style"))return nrWorldSourceCommand(c,s,j);
    if(!strcmp(op,"thermal-style")||!strcmp(op,"remove-thermal-style"))return nrThermalSourceCommand(c,s,j);
    if(!strcmp(op,"atelier-style")||!strcmp(op,"remove-atelier-style"))return nrAtelierStyleCommand(c,s,j);
    if(!strcmp(op,"kinetic-style")||!strcmp(op,"remove-kinetic-style"))return nrKineticStyleCommand(c,s,j);
    if(!strcmp(op,"observatory-style")||!strcmp(op,"remove-observatory-style"))return nrObservatoryStyleCommand(c,s,j);
    if(!strcmp(op,"corona-style")||!strcmp(op,"remove-corona-style"))return nrCoronaStyleCommand(c,s,j);
    if(!strcmp(op,"burst-style"))return nrBurstStyleCommand(c,s,j);
    if(!strcmp(op,"path-travel")||!strcmp(op,"remove-path-travel"))return nrPathTravelCommand(c,s,j);
    if(!strcmp(op,"surface-foam-transport"))return nrFoamTransportCommand(c,s,j);
    if(!strcmp(op,"surface-foam")||!strcmp(op,"clear-surface-foam"))return nrFoamCommand(c,s,j);
    if(!strcmp(op,"surface-fluid-angular"))return nrSurfaceFluidAngularCommand(c,s,j);
    if(!strcmp(op,"surface-fluid")||!strcmp(op,"stop-surface-fluid")||!strcmp(op,"export-surface-fluid"))return nrSurfaceFluidCommand(c,s,j);
    if(!strcmp(op,"float-hull")||!strcmp(op,"remove-float-hull"))return nrFloatHullCommand(c,s,j);
    if(!strcmp(op,"float-body")||!strcmp(op,"remove-float-body"))return nrFloatBodyCommand(c,s,j);
    if(!strcmp(op,"mesh-style"))return nrMeshStyleCommand(c,s,j);
    if(!strcmp(op,"surface-waves"))return nrSurfaceWavesCommand(c,s,j);
    if(!strcmp(op,"surface")||!strcmp(op,"clear-surface")||!strcmp(op,"emitter-colliders")||!strcmp(op,"mesh")||!strcmp(op,"model-import")||!strcmp(op,"ribbon")||!strcmp(op,"waterfall"))
        return nrGeometryCommand(c,s,j);
    if(!strcmp(op,"state-register")||!strcmp(op,"state-update")||!strcmp(op,"state-unregister")||
       !strcmp(op,"style-rule")||!strcmp(op,"remove-style-rule"))return nrStyleCommand(c,s,j);
    if(!strcmp(op,"character-rule")||!strcmp(op,"remove-character-rule"))return nrCharacterRuleCommand(c,s,j);
    if(!strcmp(op,"character-region")||!strcmp(op,"remove-character-region"))return nrCharacterRegionCommand(c,s,j);
    if(!strcmp(op,"reset")) {
        ALLOW("seed preservePrompt");
        uint32_t seed=s->seed;int preserve=0;
        CHECK(uinteger(j,0,"seed",&seed,0,0xffffffffu),"seed uint32");
        BOOL("preservePrompt",preserve);
        if(preserve) {
            PromptFramed framed=s->promptFramed;
            nrPromptCopy(&c->promptResetBackup,&s->promptDocument);
            memcpy(c->promptCheckpointBackup,s->dynamicPrompt.checkpoint,(size_t)framed.checkpointCount*4);
            nrDefaults(s,seed);
            nrPromptCopy(&s->promptDocument,&c->promptResetBackup);
            memcpy(s->dynamicPrompt.checkpoint,c->promptCheckpointBackup,(size_t)framed.checkpointCount*4);
            s->promptFramed=framed;
        } else nrDefaults(s,seed);
        return 0;
    }
    if(!strcmp(op,"accessibility")) {
        ALLOW("reducedMotion screenReader");BOOL("reducedMotion",s->reducedMotion);BOOL("screenReader",s->screenReader);return 0;
    }
    if(!strcmp(op,"resize")) {
        ALLOW("width height");
        int w=s->width,h=s->height;
        INT("width",w,1,2147483647/2);
        INT("height",h,1,2147483647/4);
        CHECK(nrValidViewport((uint32_t)w,(uint32_t)h),"Viewport cannot be represented");
        s->width=(uint32_t)w;
        s->height=(uint32_t)h;
        nrPointerRelease(s);s->hoverHit=s->pressedHit=0;
        return 0;
    }
    if(!strcmp(op,"pause")) {
        PausePlan p;if(planPause(c,s,j,&p)<0)return -1;
        commitPause(s,&p);return 0;
    }
    if(!strcmp(op,"time")) {
        TimePlan p;if(planTime(c,s,j,&p)<0)return -1;
        return stepTime(c,s,&p,0);
    }
    if(!strcmp(op,"window-application")||!strcmp(op,"remove-window-application")||!strcmp(op,"window-application-event"))return nrWindowApplicationCommand(c,s,j);
    if(!strcmp(op,"camera-controls")||!strcmp(op,"camera-input"))return nrCameraControlsCommand(c,s,j);
    if(!strcmp(op,"camera-action")||(!strcmp(op,"camera")&&(s->originalCamera.enabled||nrField(j,0,"profile")>=0))||(!strcmp(op,"flight")&&nrField(j,0,"profile")>=0))return nrOriginalCameraCommand(c,s,j);
    if(!strcmp(op,"camera")) {
        ALLOW("position yaw pitch roll near far fov span orthographic");
        Camera current=nrCameraCarrierAt(s);Camera*q=&s->camera;
        *q=current;
        VEC("position",q->position,-16000,16000);
        NUM("yaw",q->yaw,-36000,36000);
        NUM("pitch",q->pitch,-89.9,89.9);
        NUM("roll",q->roll,-36000,36000);
        NUM("near",q->nearPlane,.001,100);
        NUM("far",q->farPlane,.01,1000000);
        NUM("fov",q->fov,10,150);
        NUM("span",q->span,.1,2000);
        BOOL("orthographic",q->orthographic);
        CHECK(q->nearPlane<q->farPlane,"Camera near must be less than far");
        nrCameraManualPose(s,&current,q);
        return 0;
    }
    if(!strcmp(op,"look")) {
        ALLOW("yaw pitch roll");
        Vec3 v= {
            0
        };
        NUM("yaw",v.x,-36000,36000);
        NUM("pitch",v.y,-180,180);
        NUM("roll",v.z,-36000,36000);
        if((s->flight.count||s->originalCamera.flightKind)&&!nrCameraPathOwned(s))s->flight.look=nrAdd(s->flight.look,v);
        else {
            s->camera.yaw+=v.x;
            s->camera.pitch=nrClamp(s->camera.pitch+v.y,-89.9,89.9);
            s->camera.roll+=v.z;
        }
        return 0;
    }
    if(!strcmp(op,"brake")) {
        ALLOW("");
        s->camera=nrCameraCarrierAt(s);
        memset(&s->flight,0,sizeof(s->flight));nrOriginalCameraStop(s);
        return 0;
    }
    if(!strcmp(op,"flight")) {
        ALLOW("steps");
        int a=nrField(j,0,"steps");
        CHECK(a>=0&&j->tokens[a].type==J_ARRAY&&j->tokens[a].count>0&&j->tokens[a].count<=NR_STEPS,"Flight steps capacity");
        Camera origin=nrCameraCarrierAt(s);
        memset(&s->flight,0,sizeof(s->flight));nrOriginalCameraStop(s);
        s->flight.origin=origin;
        s->flight.startUs=s->timeUs;
        s->flight.count=j->tokens[a].count;
        int t=a+1;
        for(int i=0; i<s->flight.count; i++) {
            Motion*m=&s->flight.steps[i];
            m->durationUs=1000000;
            m->radius=40;
            m->coordinated=1;
            CHECK(nrAllowed(j,t,"kind durationMs speed yaw pitch roll bank radius target coordinated")&&choice(j,t,"kind",&m->kind,"cruise turn climb dive roll orbit escape falling")&&duration(j,t,"durationMs",&m->durationUs,3600000000ull,1000)&&m->durationUs>0&&number(j,t,"speed",&m->speed,-100,100)&&number(j,t,"yaw",&m->yaw,-3600,3600)&&number(j,t,"pitch",&m->pitch,-89,89)&&number(j,t,"roll",&m->roll,-3600,3600)&&number(j,t,"bank",&m->bank,-85,85)&&number(j,t,"radius",&m->radius,1,2000)&&vector(j,t,"target",&m->target,-10000,10000)&&boolean(j,t,"coordinated",&m->coordinated),"Invalid flight step");
            t=j->tokens[t].next;
        }
        return 0;
    }
    if(!strcmp(op,"emitter")) {
        ALLOW("id effect seed count runningTimeMs startTimeUs position extent velocity spread birthOrientation initialOrientation angularVelocity gravity wind windVariation drag lift flutterHz flutterAmount tumble sizeMin sizeMax lifetimeMinMs lifetimeMaxMs material alpha deposit collision colliders shape distribution schedule endStyle tailMs topology heat radius trailMs birthFadeMs deathFadeMs windScale windPeriodSeconds shapeWeights coreMs cycles gapMs rate nearDistance farDistance farFadeDistance veinContrast curl backTint twoSided sampling surfaceAlpha");
        int id=0;
        INT("id",id,1,65535);
        CHECK(id,"Emitter id required");
        int slot=nrFindEmitter(s,id);
        CHECK(slot<0,"Emitter already exists; use forces/stop or clear before replacement");
        for(int i=0; i<(int)NR_MAX_EMITTERS; i++)if(!s->emitters[i].used) {
            slot=i;
            break;
        }
        CHECK(slot>=0,"Emitter capacity");
        int e=nrEffectId("weather/autumn-drift");
        CHECK(effect(j,0,&e,0),"Unknown native particle effect");
        Emitter*q=&s->emitters[slot];
        emitterDefaults(q,id,e,s->seed,s->timeUs);
        memset(&s->burstControls[slot],0,sizeof(BurstControls));
        memset(&s->coronaControls[slot],0,sizeof(CoronaControls));
        memset(&s->observatoryControls[slot],0,sizeof(ObservatoryControls));
        memset(&s->kineticControls[slot],0,sizeof(KineticControls));s->kineticPaint[slot]=0;
        memset(&s->atelierControls[slot],0,sizeof(AtelierControls));
        memset(&s->thermalSourceControls[slot],0,sizeof(ThermalSourceControls));
        memset(&s->worldSourceControls[slot],0,sizeof(WorldSourceControls));
        memset(&s->studioNovaControls[slot],0,sizeof(StudioNovaControls));
        s->birthOrientations[slot]=nrV(0,0,0);
        VEC("birthOrientation",s->birthOrientations[slot],-3600,3600);
        memset(&s->emitterMotions[slot],0,sizeof(s->emitterMotions[slot]));
        if(nrField(j,0,"initialOrientation")>=0||nrField(j,0,"angularVelocity")>=0) {
            CHECK(nrEffectAlgorithm(q->effect)==0||nrEffectAlgorithm(q->effect)==2,"Authored particle motion requires leaves or snow");
            s->emitterMotions[slot].authored=1;
            VEC("initialOrientation",s->emitterMotions[slot].orientation,-3600,3600);
            VEC("angularVelocity",s->emitterMotions[slot].angularVelocity,-720,720);
        }
        CHECK(s->nextEmitterGeneration<0xffffffffu,"Emitter generation capacity");
        q->generation=++s->nextEmitterGeneration;
        INT("count",q->count,0,100000);
        NUM("rate",q->rate,0,10000);
        CHECK(!(nrField(j,0,"rate")>=0&&nrField(j,0,"count")>=0),"Use rate or count, not both");
        INT("cycles",q->cycles,1,10000);
        DUR("gapMs",q->gapUs,60000000,1000);
        CHECK(!(q->rate>0&&q->cycles!=1),"Rate emission does not use repeat cycles");
        NUM("nearDistance",q->nearDistance,.001,1000);
        NUM("farDistance",q->farDistance,.01,10000);
        NUM("farFadeDistance",q->farFade,0,10000);
        CHECK(q->nearDistance<q->farDistance&&q->farFade<=q->farDistance-q->nearDistance,"Emitter distance fade bounds");
        NUM("veinContrast",q->veinContrast,0,1);NUM("curl",q->curl,-2,2);NUM("backTint",q->backTint,0,1);
        BOOL("twoSided",q->twoSided);
        CHOICE("sampling",q->sampling,"cell half braille hybrid");
        CHECK(nrField(j,0,"surfaceAlpha")<0||nrEffectAlgorithm(q->effect)==0,"surfaceAlpha is a leaf surface setting");
        NUM("surfaceAlpha",q->surfaceAlpha,0,1);
        CHECK(uinteger(j,0,"seed",&q->seed,0,0xffffffffu),"Seed uint32");
        DUR("runningTimeMs",q->runningUs,86400000000ull,1000);
        DUR("startTimeUs",q->startUs,86400000000ull,1);
        CHECK(q->startUs>=s->timeUs,"Emitter cannot be scheduled in the past");
        DUR("lifetimeMinMs",q->lifeMinUs,3600000000ull,1000);
        DUR("lifetimeMaxMs",q->lifeMaxUs,3600000000ull,1000);
        CHECK(q->lifeMinUs>=1000&&q->lifeMinUs<=q->lifeMaxUs,"Lifetime bounds");
        VEC("position",q->position,-16000,16000);
        VEC("extent",q->extent,0,2000);
        VEC("velocity",q->velocity,-256,256);
        VEC("spread",q->spread,0,128);
        VEC("gravity",q->gravity,-256,256);
        VEC("wind",q->wind,-256,256);
        VEC("windVariation",q->windVariation,0,128);
        VEC("tumble",q->tumble,-720,720);
        VEC("shapeWeights",q->shapeWeights,0,1);
        CHECK(q->shapeWeights.x+q->shapeWeights.y+q->shapeWeights.z>0,"Positive shape weight required");
        NUM("drag",q->drag,0,30);
        NUM("lift",q->lift,0,20);
        NUM("flutterHz",q->flutterHz,0,30);
        NUM("flutterAmount",q->flutterAmount,0,10);
        NUM("sizeMin",q->sizeMin,.005,64);
        NUM("sizeMax",q->sizeMax,.005,64);
        CHECK(q->sizeMin<=q->sizeMax,"Size bounds");
        NUM("alpha",q->alpha,0,1);
        NUM("heat",q->heat,0,64);
        NUM("radius",q->radius,.1,200);
        NUM("windScale",q->windScale,.1,1000);
        NUM("windPeriodSeconds",q->windPeriod,.1,120);
        INT("material",q->material,0,15);
        BOOL("deposit",q->deposit);
        BOOL("collision",q->collision);
        CHECK(!q->deposit||q->collision,"Deposition requires collision");
        CHECK(q->startUs+(q->runningUs+q->gapUs)*(uint64_t)(q->cycles-1)+q->runningUs<=86400000000ull,"Emission exceeds scene clock range");
        CHOICE("shape",q->shape,"point box sphere disc line");
        int distribution=0;CHOICE("distribution",distribution,"legacy uniform");
        q->shape+=5*distribution;
        CHOICE("schedule",q->schedule,"uniform seeded-jitter");
        CHOICE("endStyle",q->endStyle,"drain settle dissolve gust quench disperse");
        CHECK(nrEndStyleSupported(q->effect,q->endStyle),"Unsupported effect ending");
        DUR("tailMs",q->tailUs,3600000000ull,1000);
        INT("topology",q->topology,0,5);
        uint64_t d=q->trailUs;
        DUR("trailMs",d,2000000,1000);
        q->trailUs=(uint32_t)d;
        d=q->birthFadeUs;
        DUR("birthFadeMs",d,60000000,1000);
        q->birthFadeUs=(uint32_t)d;
        d=q->deathFadeUs;
        DUR("deathFadeMs",d,60000000,1000);
        q->deathFadeUs=(uint32_t)d;
        d=q->coreUs;
        DUR("coreMs",d,10000000,1000);
        q->coreUs=(uint32_t)d;
        return nrConfigureColliders(c,s,j,slot,0);
    }
    if(!strcmp(op,"emitter-style")) {
        ALLOW("id sampling surfaceAlpha veinContrast backTint twoSided");
        int id=0;INT("id",id,1,65535);int i=nrFindEmitter(s,id);
        CHECK(i>=0,"Emitter does not exist");Emitter*q=&s->emitters[i];
        CHECK(nrEffectAlgorithm(q->effect)==0 || (nrField(j,0,"surfaceAlpha")<0&&nrField(j,0,"veinContrast")<0&&nrField(j,0,"backTint")<0&&nrField(j,0,"twoSided")<0),"Leaf detail settings require a leaf emitter");
        CHOICE("sampling",q->sampling,"cell half braille hybrid");
        NUM("surfaceAlpha",q->surfaceAlpha,0,1);NUM("veinContrast",q->veinContrast,0,1);
        NUM("backTint",q->backTint,0,1);BOOL("twoSided",q->twoSided);
        return 0;
    }
    if(!strcmp(op,"resume")) {
        ALLOW("id");
        int id=0;INT("id",id,1,65535);
        int i=nrFindEmitter(s,id);CHECK(i>=0,"Emitter does not exist");
        Emitter*q=&s->emitters[i];
        if(!q->stopping)return 0;
        CHECK(q->endStyle==0,"Only stopped drain emission can resume");
        uint64_t elapsed=s->timeUs-q->stopUs;
        CHECK(elapsed<=86400000000ull-q->startUs,"Resumed schedule exceeds supported time range");
        q->startUs+=elapsed;q->stopUs=0;q->stopping=0;
        return 0;
    }
    if(!strcmp(op,"forces")||!strcmp(op,"stop")||!strcmp(op,"cancel")) {
        int cancel=!strcmp(op,"cancel"),stop=cancel||!strcmp(op,"stop");
        if(stop) {
            ALLOW("id style tailMs");
        }
        else {
            ALLOW("id wind windVariation gravity drag heat");
        }
        int id=0;
        INT("id",id,1,65535);
        int i=nrFindEmitter(s,id);
        CHECK(i>=0,"Emitter does not exist");
        Emitter*q=&s->emitters[i];
        if(stop) {
            int beginCancelTail=cancel&&q->stopping&&q->endStyle==0;
            int destructive=q->stopping&&q->endStyle!=0;
            if(cancel&&q->endStyle==0)q->endStyle=2;
            CHOICE("style",q->endStyle,"drain settle dissolve gust quench disperse");
            CHECK(!cancel||q->endStyle!=0,"Cancel requires a non-drain ending");
            /* A started destructive ending is final: drain would lift its deadline. */
            CHECK(!destructive||q->endStyle!=0,"Destructive ending cannot return to drain");
            CHECK(nrEndStyleSupported(q->effect,q->endStyle),"Unsupported effect ending");
            DUR("tailMs",q->tailUs,3600000000ull,1000);
            if(!q->stopping||beginCancelTail)q->stopUs=s->timeUs;
            q->stopping=1;
        }
        else {
            VEC("wind",q->wind,-256,256);
            VEC("windVariation",q->windVariation,0,128);
            VEC("gravity",q->gravity,-256,256);
            NUM("drag",q->drag,0,30);
            NUM("heat",q->heat,0,64);
        }
        return 0;
    }
    if(!strcmp(op,"clear-instance")) {
        ALLOW("id");int id=0;INT("id",id,1,65535);
        int slot=nrFindEmitter(s,id);CHECK(slot>=0,"Emitter not found");
        CHECK(!s->flowSprays[slot].flowId,"Cannot clear an allocated flow spray emitter");
        for(int i=0;i<(int)NR_MAX_PARTICLES;i++)if(s->particles[i].emitterId==(uint32_t)id) {
            nrHeatRelease(s,0,i);memset(&s->particles[i],0,sizeof(Particle));
            memset(&s->particleMotions[i],0,sizeof(s->particleMotions[i]));
            memset(&s->geometry.particleContacts[i],0,sizeof(SurfaceContact));
        }
        /* Scene deposits keep their own geometry/material/identity after removal. */
        memset(&s->burstControls[slot],0,sizeof(BurstControls));
        memset(&s->coronaControls[slot],0,sizeof(CoronaControls));
        memset(&s->observatoryControls[slot],0,sizeof(ObservatoryControls));
        memset(&s->kineticControls[slot],0,sizeof(KineticControls));s->kineticPaint[slot]=0;
        memset(&s->atelierControls[slot],0,sizeof(AtelierControls));
        memset(&s->thermalSourceControls[slot],0,sizeof(ThermalSourceControls));
        memset(&s->worldSourceControls[slot],0,sizeof(WorldSourceControls));
        memset(&s->studioNovaControls[slot],0,sizeof(StudioNovaControls));
        memset(&s->emitters[slot],0,sizeof(Emitter));s->geometry.emitterColliders[slot]=0;s->birthOrientations[slot]=nrV(0,0,0);memset(&s->emitterMotions[slot],0,sizeof(s->emitterMotions[slot]));return 0;
    }
    if(!strcmp(op,"clear-deposits")) {
        ALLOW("emitterId");int id=0;INT("emitterId",id,0,65535);
        for(int i=0;i<NR_DEPOSITS;i++)if(!id||s->deposits[i].emitterId==(uint32_t)id) {
            nrHeatRelease(s,1,i);memset(&s->deposits[i],0,sizeof(Deposit));memset(&s->geometry.depositContacts[i],0,sizeof(SurfaceContact));
        }
        for(int i=0;i<NR_TILES;i++)if(!id||s->tiles[i].emitterId==(uint32_t)id) {
            nrHeatRelease(s,2,i);memset(&s->tiles[i],0,sizeof(DepositTile));memset(&s->geometry.tileSurfaces[i],0,sizeof(SurfaceTile));
        }
        return 0;
    }
    if(!strcmp(op,"clear")) {
        ALLOW("scope");
        int scope=0;
        CHOICE("scope",scope,"weather deposits graph text status scene-art");
        if(scope==0) {
            for(int i=0;i<(int)NR_MAX_EMITTERS;i++)CHECK(!s->flowSprays[i].flowId,"Cannot clear allocated flow spray; reset the scene explicitly");
            for(int i=0;i<(int)NR_MAX_PARTICLES;i++)nrHeatRelease(s,0,i);
            memset(s->particles,0,sizeof(s->particles));
            memset(s->emitters,0,sizeof(s->emitters));
            memset(s->birthOrientations,0,sizeof(s->birthOrientations));
            memset(s->emitterMotions,0,sizeof(s->emitterMotions));
            memset(s->particleMotions,0,sizeof(s->particleMotions));
            memset(s->fields,0,sizeof(s->fields));
            memset(s->fieldControls,0,sizeof(s->fieldControls));
            memset(s->electricalArcs,0,sizeof(s->electricalArcs));
            memset(s->burstControls,0,sizeof(s->burstControls));
            memset(s->coronaControls,0,sizeof(s->coronaControls));
            memset(s->observatoryControls,0,sizeof(s->observatoryControls));
            memset(s->kineticControls,0,sizeof(s->kineticControls));memset(s->kineticPaint,0,sizeof(s->kineticPaint));
            memset(s->atelierControls,0,sizeof(s->atelierControls));
            memset(s->thermalSourceControls,0,sizeof(s->thermalSourceControls));
            memset(s->worldSourceControls,0,sizeof(s->worldSourceControls));
            memset(s->studioNovaControls,0,sizeof(s->studioNovaControls));
            memset(s->geometry.emitterColliders,0,sizeof(s->geometry.emitterColliders));
            memset(s->geometry.particleContacts,0,sizeof(s->geometry.particleContacts));
        }
        else if(scope==1) {
            for(int i=0;i<NR_DEPOSITS;i++)nrHeatRelease(s,1,i);for(int i=0;i<NR_TILES;i++)nrHeatRelease(s,2,i);
            memset(s->deposits,0,sizeof(s->deposits));
            memset(s->tiles,0,sizeof(s->tiles));
            memset(s->geometry.depositContacts,0,sizeof(s->geometry.depositContacts));
            memset(s->geometry.tileSurfaces,0,sizeof(s->geometry.tileSurfaces));
        }
        else if(scope==2) {
            memset(s->nodes,0,sizeof(s->nodes));memset(&s->sourceGraphLayout,0,sizeof(s->sourceGraphLayout));
            memset(s->edges,0,sizeof(s->edges));
            s->edgeCount=0;
            s->selection=0;
        }
        else if(scope==3){memset(s->text,0,sizeof(s->text));memset(s->textAlphabetTail,0,sizeof(s->textAlphabetTail));memset(s->textPhaseModel,0,sizeof(s->textPhaseModel));}
        else if(scope==5){CHECK(s->schema>=NR_STATE_SCHEMA_SCENE_ART,"Scene art requires current schema");memset(&s->sceneArt,0,sizeof(s->sceneArt));memset(&s->sceneArtClock,0,sizeof(s->sceneArtClock));}
        else {
            for(int i=0;i<NR_MESSAGES;i++)CHECK(!s->messages[i].used||!s->messages[i].important||s->messages[i].acknowledged,"Acknowledge important history before clear");
            memset(s->messages,0,sizeof(s->messages));
        }
        return 0;
    }
    if(!strcmp(op,"floor")) {
        ALLOW("enabled visible height restitution friction settleSpeed reentrainWindSpeed maxIndividual maxTiles overflow retentionMs cellSize alpha fadeMs evaporation sampling");
        Floor*q=&s->floor;
        CHOICE("sampling",q->sampling,"cell half braille hybrid");
        BOOL("enabled",q->enabled);
        BOOL("visible",q->visible);
        NUM("height",q->height,-1000,1000);
        NUM("restitution",q->restitution,0,1);
        NUM("friction",q->friction,0,1);
        NUM("settleSpeed",q->settleSpeed,0,30);
        NUM("reentrainWindSpeed",q->reentrain,0,256);
        INT("maxIndividual",q->maxIndividual,0,NR_DEPOSITS);
        INT("maxTiles",q->maxTiles,0,NR_TILES);
        CHOICE("overflow",q->overflow,"reject-new merge-to-field");
        DUR("retentionMs",q->retentionUs,86400000000ull,1000);
        DUR("fadeMs",q->fadeUs,60000000,1000);NUM("evaporation",q->evaporation,0,10);
        CHECK(q->overflow!=1||q->maxTiles>0,"Merge-to-field requires a bounded nonempty tile destination");
        CHECK(!q->retentionUs||q->fadeUs<=q->retentionUs,"Deposit fade must fit retention duration");
        NUM("cellSize",q->cellSize,.1,100);
        NUM("alpha",q->alpha,0,1);
        return 0;
    }
    if(!strcmp(op,"material-thermal")||!strcmp(op,"remove-material-thermal"))return nrMaterialHeatCommand(c,s,j);
    if(!strcmp(op,"material")) {
        ALLOW("id space channels alpha hueStep scope blend gradient spacing index colors pattern");
        int id=0;
        INT("id",id,0,15);
        Material*m=&s->materials[id];
        if(!m->used)nrInitMaterial(m,id);
        if(nrField(j,0,"pattern")>=0&&nrMaterialPatternCommand(c,s,j,id)<0)return -1;
        int sp=m->space;
        CHOICE("space",sp,"oklch oklab hsl hsb rgb linear-rgb cmyk indexed");
        if(sp!=m->space) {
            nrInitMaterial(m,id);
            m->space=sp;
            for(int k=0; k<4; k++)m->channel[k]=(Track) {
                .5,0,0,1,0,1000000,0,0,1
            };
            if(sp==1) {
                m->channel[1].min=m->channel[2].min=-.5;
                m->channel[1].max=m->channel[2].max=.5;
                m->channel[1].initial=m->channel[2].initial=0;
            }
            if(sp==2||sp==3) {
                m->channel[0].max=360;
                m->channel[0].initial=190;
                m->channel[0].boundary=1;
            }
            if(sp==7) {
                m->channel[0].initial=0;
                m->channel[0].max=64;
                m->channel[0].boundary=1;
            }
        }
        int channels=nrField(j,0,"channels");
        const char*keys[8][4]= {
            {
                "l","c","h","unused"
            }, {
                "l","a","b","unused"
            }, {
                "h","s","l","unused"
            }, {
                "h","s","v","unused"
            }, {
                "r","g","b","unused"
            }, {
                "r","g","b","unused"
            }, {
                "c","m","y","k"
            }, {
                "i","unused","unused","unused"
            }
        };
        const char*allowed[8]= {
            "l c h","l a b","h s l","h s v","r g b","r g b","c m y k","i"
        };
        if(channels>=0) {
            CHECK(nrAllowed(j,channels,allowed[sp]),"Color channel does not belong to selected color space");
            for(int k=0; k<4; k++) {
                double lo=(sp==1&&(k==1||k==2))?-.5:0,hi=(sp==0&&k==2)||((sp==2||sp==3)&&k==0)?360:sp==7&&k==0?64:sp==0&&k==1?.5:sp==1&&k>0?.5:1;
                CHECK(track(j,nrField(j,channels,keys[sp][k]),&m->channel[k],lo,hi),"Invalid channel track");
            }
        }
        CHECK(track(j,nrField(j,0,"alpha"),&m->alpha,0,1),"Invalid alpha track");
        NUM("hueStep",m->hueStep,-360,360);
        NUM("spacing",m->spacing,-100,100);
        CHOICE("scope",m->scope,"uniform characters");
        CHOICE("blend",m->blend,"normal multiply screen overlay darken lighten color-dodge color-burn hard-light soft-light difference exclusion hue saturation color luminosity additive subtractive divide linear-burn linear-light vivid-light pin-light hard-mix darker-color lighter-color dissolve none");
        CHECK(track(j,nrField(j,0,"index"),&m->index,-10000,10000),"Invalid gradient index track");
        int a=nrField(j,0,"gradient");
        if(a>=0) {
            CHECK(j->tokens[a].type==J_ARRAY&&j->tokens[a].count<=16,"Gradient stop capacity");
            m->gradientCount=j->tokens[a].count;
            int t=a+1;
            for(int i=0; i<m->gradientCount; i++) {
                CHECK(j->tokens[t].type==J_ARRAY&&j->tokens[t].count==3,"Gradient uses three channels");
                int z=t+1;
                for(int k=0; k<3; k++) {
                    CHECK(nrNumber(j,z,&m->stops[i][k])&&m->stops[i][k]>=0&&m->stops[i][k]<=(k==2&&sp==0?360:1),"Gradient channel bounds");
                    z=j->tokens[z].next;
                }
                t=j->tokens[t].next;
            }
        }
        a=nrField(j,0,"colors");
        if(a>=0) {
            CHECK(j->tokens[a].type==J_ARRAY&&j->tokens[a].count>0&&j->tokens[a].count<=64,"Indexed table capacity");
            m->colorCount=j->tokens[a].count;
            int t=a+1;
            for(int i=0; i<m->colorCount; i++) {
                double v;
                CHECK(nrNumber(j,t,&v)&&v>=0&&v<=0xffffff&&v==(uint32_t)v,"Indexed RGB bounds");
                m->colors[i]=(uint32_t)v;
                t=j->tokens[t].next;
            }
        }
        CHECK(sp!=7||m->colorCount>0,"Indexed paint requires colors");
        return 0;
    }
    if(!strcmp(op,"environment")) {
        ALLOW("background stars starFar sampling style presentation occlusionTint occludedDots starProfile worldSeed skyDensity skyRadius skyExposure trailMs textLightness textChroma");
        CHECK(!nrSourceSkyCommand(c,s,j),"Invalid original sky controls");
        if(nrField(j,0,"presentation")>=0){
            CHECK(s->schema>=NR_STATE_SCHEMA_CANVAS_PRESENTATION,"Canvas presentation requires current schema");
            int presentation=(int)s->canvasPresentation;
            CHOICE("presentation",presentation,"workbench canvas");s->canvasPresentation=(uint32_t)presentation;
        }
        CHECK(uinteger(j,0,"background",&s->background,0,0xffffff),"RGB background");
        INT("stars",s->stars,0,2000);
        NUM("starFar",s->starFar,20,1000);
        CHOICE("sampling",s->sampling,"cell half braille hybrid");
        CHOICE("style",s->style,"solid linear plasma wave caustic contours");
        /* A pending command restored from an older snapshot runs under that schema, which never had these fields. */
        CHECK((nrField(j,0,"occlusionTint")<0&&nrField(j,0,"occludedDots")<0)||s->schema>=NR_STATE_SCHEMA_OCCLUSION_CONTROLS,"Occlusion controls require schema97");
        if(nrField(j,0,"occlusionTint")>=0){
            double tint=0;CHECK(number(j,0,"occlusionTint",&tint,0,1),"occlusionTint must be a number from 0 to 1");
            s->occlusionControls.tintConfigured=1;s->occlusionControls.tint=tint+0.0;
        }
        if(nrField(j,0,"occludedDots")>=0){
            int dots=0;CHECK(choice(j,0,"occludedDots",&dots,"hidden merge"),"occludedDots must be \"hidden\" or \"merge\"");
            s->occlusionControls.occludedDots=(uint32_t)dots;
        }
        return 0;
    }
    if(!strcmp(op,"field")) {
        ALLOW("effect x y lifeMs speed width strength material seed continuous falloff frequency phase interference velocity surface rings optics paint");
        int e=nrEffectId("surface-field/silk-tide");
        CHECK(effect(j,0,&e,1),"Unknown native surface field");
        double x=s->width*.5,y=s->height*.5;
        NUM("x",x,NR_LAYOUT_MIN,NR_LAYOUT_MAX);
        NUM("y",y,NR_LAYOUT_MIN,NR_LAYOUT_MAX);
        int i=newField(s,x,y,e);
        CHECK(i>=0,"Field capacity");
        Field*f=&s->fields[i];
        int originalPaint=0;CHOICE("paint",originalPaint,"field source");
        int optics=originalPaint;CHOICE("optics",optics,"legacy source");
        CHECK(!originalPaint||optics,"Original field painting requires source optics");
        if(optics){int a=nrEffectAlgorithm(e);CHECK(s->schema>=NR_STATE_SCHEMA_SOURCE_OPTICS&&a>=0&&a<4,"Source field optics require current schema");nrFieldControlsInit(&s->fieldControls[i]);s->fieldControls[i].rings=(uint32_t)(a+1)<<8;
            const double widths[]={1.5,1.7,.25,1.2},speeds[]={10,12,48,20},strengths[]={.28,.38,.85,.8};const uint64_t lives[]={3200000,2400000,5000000,4200000};f->width=widths[a];f->speed=speeds[a];f->strength=strengths[a];f->lifeUs=lives[a];}
        if(originalPaint){CHECK(s->schema>=NR_STATE_SCHEMA_SURFACE_PAINT,"Original field painting requires schema86");int a=nrEffectAlgorithm(e);s->fieldControls[i].rings|=32u|(a==0?3u:0u);const double speeds[]={9,12,48,20},strengths[]={1,.6,.85,.8};const uint64_t lives[]={3600000,3200000,5000000,4200000};f->speed=speeds[a];f->strength=strengths[a];f->lifeUs=lives[a];f->seed=a<2?f->id:2030;}
        DUR("lifeMs",f->lifeUs,60000000,1000);
        NUM("speed",f->speed,0,100);
        NUM("width",f->width,.05,NR_LAYOUT_MAX);
        NUM("strength",f->strength,0,1);
        INT("material",f->material,0,15);
        CHECK(uinteger(j,0,"seed",&f->seed,0,0xffffffffu),"Seed uint32");
        FieldControls*q=&s->fieldControls[i];
        int rings=nrField(j,0,"rings");if(rings>=0){CHECK(s->schema>=NR_STATE_SCHEMA_SOFT_FRONTS,"Soft fronts require current schema");nrFieldControlsInit(q);int n=0;INT("rings",n,1,16);CHECK(!NR_FIELD_OPTICS(q)||NR_FIELD_OPTICS(q)==1,"Rings apply to smooth source optics only");q->rings=(q->rings&~31u)|(uint32_t)n;}
        const char*options[]={"continuous","falloff","frequency","phase","interference","velocity","surface","material"};
        for(int k=0;k<8;k++)if(nrField(j,0,options[k])>=0&&(k<7||s->schema>=NR_STATE_SCHEMA_COLOR_FIELDS))nrFieldControlsInit(q);
        if(q->used){
            CHECK(s->schema>=NR_STATE_SCHEMA_COLOR_FIELDS,"Color field controls require current authoring schema");
            BOOL("continuous",q->continuous);INT("falloff",q->falloff,1,8);
            NUM("frequency",q->frequency,0,1000);NUM("phase",q->phase,-3600,3600);NUM("interference",q->interference,0,1);
            int v=nrField(j,0,"velocity");if(v>=0){CHECK(j->tokens[v].type==J_ARRAY&&j->tokens[v].count==2,"Field velocity has two axes");int a=v+1,b=j->tokens[a].next;CHECK(nrNumber(j,a,&q->vx)&&nrNumber(j,b,&q->vy)&&q->vx>=-100&&q->vx<=100&&q->vy>=-100&&q->vy<=100,"Field velocity range");}
            int r=nrField(j,0,"surface");if(r>=0){CHECK(j->tokens[r].type==J_OBJECT&&nrAllowed(j,r,"x y width height")&&nrField(j,r,"x")>=0&&nrField(j,r,"y")>=0&&nrField(j,r,"width")>=0&&nrField(j,r,"height")>=0,"Declared field surface rectangle");q->surface=1;CHECK(number(j,r,"x",&q->x,NR_LAYOUT_MIN,NR_LAYOUT_MAX)&&number(j,r,"y",&q->y,NR_LAYOUT_MIN,NR_LAYOUT_MAX)&&number(j,r,"width",&q->width,.05,NR_LAYOUT_MAX)&&number(j,r,"height",&q->height,.05,NR_LAYOUT_MAX),"Field surface range");}
            q->materialAuthored=nrField(j,0,"material")>=0;
        }
        CHECK(nrValidOriginalField(s,i),"Invalid original field painting controls");
        return 0;
    }
    if(!strcmp(op,"remove-field")){
        ALLOW("id");uint32_t id=0;CHECK(s->schema>=NR_STATE_SCHEMA_COLOR_FIELDS&&uinteger(j,0,"id",&id,1,0xfffffffeu)&&id,"Field ID");
        for(int i=0;i<NR_FIELDS;i++)if(s->fields[i].used&&s->fields[i].id==id){memset(&s->fields[i],0,sizeof(s->fields[i]));memset(&s->fieldControls[i],0,sizeof(s->fieldControls[i]));return 0;}
        return reject(c,"Missing field");
    }
    if(!strcmp(op,"input")||!strcmp(op,"draft")||!strcmp(op,"paste")) {
        int draft=!strcmp(op,"draft");
        if(draft) {
            ALLOW("text caret emitWeather");
        }
        else {
            ALLOW("text");
        }
        uint32_t *buf=NULL;
        int n=nrPromptDecodeCommand(s,j,nrField(j,0,"text"),&buf);
        CHECK(n>=0,"Invalid text or capacity");
        if(!draft) {
            if(!strcmp(op,"paste")&&(nrInputOwner(s)||!n||(s->promptDocument.mode>=2&&!s->promptDocument.vimMode)))return 0;
            CHECK(nrInput(s,buf,n,!strcmp(op,"paste")?2:1),"Prompt capacity");
        }
        else {
            DraftPlan plan;if(planDraftTail(c,s,j,buf,n,&plan)<0)return -1;
            return commitDraft(c,s,&plan);
        }
        return 0;
    }
    if(!strcmp(op,"select")&&nrField(j,0,"id")<0) {
        SelectPlan p;if(planPromptSelect(c,s,j,&p)<0)return -1;
        commitPromptSelect(s,&p);return 0;
    }
    if(!strcmp(op,"prompt-appearance"))return nrPromptAppearanceCommand(c,s,j);
    if(!strcmp(op,"prompt-source"))return nrFirstPromptCommand(c,s,j);
    if(!strcmp(op,"prompt")) {
        return nrPromptFramedCommand(c,s,j);
    }
    if(!strcmp(op,"key")) {
        ALLOW("key ctrl shift alt meta unit");
        char key[64]= {
            0
        };
        CHECK(string(j,0,"key",key,sizeof(key)),"Key string");
        int ctrl=0,shift=0,alt=0,meta=0;
        BOOL("ctrl",ctrl);
        BOOL("shift",shift);
        BOOL("alt",alt);
        BOOL("meta",meta);
        int explicitCount=s->vimCount.revision==s->promptDocument.revision&&s->vimCount.count;
        int historyRepeats=explicitCount?s->vimCount.count:1;
        int unit=s->promptPresentation.layout!=0;CHOICE("unit",unit,"scalar grapheme");
        Prompt*p=&s->promptDocument;
        if((p->modal||nrModalBlocking(s))&&strcmp(key,"F1")&&strcmp(key,"Escape"))return 0;
        if(!p->modal&&s->sourceModal.depth&&!strcmp(key,"Escape")){nrModalDismiss(s);return 0;}
        if(ctrl||alt||meta){s->vimCount.count=0;s->vimOperator.key=0;vimCancelRegister(s);}
        if(!strcmp(key,"F6")) {
            s->vimCount.count=0;s->vimOperator.key=0;vimCancelRegister(s);
            int current=nrFindWindow(s,s->selectedWindow),chosen=-1;
            for(int k=1;k<=(int)NR_MAX_WINDOWS;k++){int i=(current+k)%(int)NR_MAX_WINDOWS;if(s->windows[i].used){chosen=i;break;}}
            if(chosen>=0){Window*w=&s->windows[chosen];w->reader=1;w->target=1;w->fromVisibility=1;w->atUs=s->timeUs;selectWindow(s,w->id);nrPointerRelease(s);}return 0;
        }
        if(!strcmp(key,"PageDown")||!strcmp(key,"PageUp")) {
            int i=nrFindWindow(s,s->selectedWindow);
            if(i>=0&&s->windows[i].reader&&s->windows[i].target){Window*w=&s->windows[i];int rows=nrWindowReaderPageRows(s);int first=(int)nrClamp(w->scrollRow,0,nrWindowReaderMaxScroll(s,w));w->scrollRow=(int)nrClamp(first+(!strcmp(key,"PageDown")?rows:-rows),0,nrWindowReaderMaxScroll(s,w));return 0;}
            if(s->selection){s->selectionScroll=(int)nrClamp(s->selectionScroll+(!strcmp(key,"PageDown")?(int)s->height-8:-(int)s->height+8),0,graphInspectorMaxScroll(s));return 0;}
        }
        if(!strcmp(key,"F1")) {
            s->vimCount.count=0;s->vimOperator.key=0;vimCancelRegister(s);
            p->modal=!p->modal;
            return 0;
        }
        if(!strcmp(key,"Escape")) {
            if(s->promptFramed.enabled&&p->mode>=NR_PROMPT_SOURCE_VIM_INLINE&&
               s->promptFramed.vimState==NR_PROMPT_SOURCE_VIM_COMMAND&&!ctrl&&!alt&&!meta){
                int framedKey=nrPromptFramedKey(c,s,j,ctrl,shift,alt,meta);
                if(framedKey<0)return -1;
                if(framedKey>0)return 0;
            }
            s->vimCount.count=0;s->vimOperator.key=0;vimCancelRegister(s);
            int reader=nrFindWindow(s,s->selectedWindow);
            if(p->modal)p->modal=0;
            else if(reader>=0&&s->windows[reader].reader&&s->windows[reader].target)s->windows[reader].reader=0;
            else if(p->anchor>=0) {p->anchor=-1;nrPointerRelease(s);}
            else if(p->mode>=2&&p->vimMode){p->vimMode=0;if(s->promptFramed.enabled)s->promptFramed.vimState=NR_PROMPT_SOURCE_VIM_NORMAL;}
            else s->selection=0;
            return 0;
        }
        if(p->modal)return 0;
        int reader=nrFindWindow(s,s->selectedWindow);
        if(reader>=0&&s->windows[reader].reader&&s->windows[reader].target) {
            Window*w=&s->windows[reader];
            int maximum=nrWindowReaderMaxScroll(s,w);
            int row=(int)nrClamp(w->scrollRow,0,maximum);
            if(!strcmp(key,"ArrowDown"))row++;
            else if(!strcmp(key,"ArrowUp"))row--;
            else if(!strcmp(key,"Home")||(ctrl&&!strcmp(key,"a")))row=0;
            else if(!strcmp(key,"End")||(ctrl&&!strcmp(key,"e")))row=maximum;
            else return 0; /* The reader owns keyboard focus, not its obscured prompt. */
            w->scrollRow=(int)nrClamp(row,0,maximum);
            return 0;
        }
        if(!strcmp(key,"SelectAll")) {
            CHECK(!ctrl&&!alt&&!meta,"SelectAll is an explicit unmodified command");
            p->anchor=p->count?0:-1;p->caret=p->count;return 0;
        }
        /* Host shortcuts cannot fall through into unmodified editor commands. */
        if((ctrl||alt||meta)&&!(ctrl&&!alt&&!meta&&
           (!strcmp(key,"a")||!strcmp(key,"e")||!strcmp(key,"z")||!strcmp(key,"r"))))
            return reject(c,"Unsupported modified prompt key");
        int framedKey=nrPromptFramedKey(c,s,j,ctrl,shift,alt,meta);
        if(framedKey<0)return -1;
        if(framedKey>0)return 0;
        if(!strcmp(key,"ArrowLeft")||!strcmp(key,"ArrowRight")||!strcmp(key,"ArrowUp")||!strcmp(key,"ArrowDown")||!strcmp(key,"Home")||!strcmp(key,"End")) {
            if(shift) {if(p->anchor<0)p->anchor=p->caret;}
            else if(p->anchor>=0) {
                int first=p->anchor<p->caret?p->anchor:p->caret,last=p->anchor>p->caret?p->anchor:p->caret;
                p->anchor=-1;
                if(!strcmp(key,"ArrowLeft")){p->caret=first;return 0;}
                if(!strcmp(key,"ArrowRight")){p->caret=last;return 0;}
            }
        }
        if(ctrl&&!strcmp(key,"a")) {
            p->anchor=-1;p->caret=0;
            return 0;
        }
        if(ctrl&&!strcmp(key,"e")) {
            p->anchor=-1;p->caret=p->count;
            return 0;
        }
        if(ctrl&&(!strcmp(key,"z")||!strcmp(key,"r"))){for(int i=0;i<historyRepeats;i++)CHECK(travelHistory(s,!strcmp(key,"r")||shift),"Prompt history storage");return 0;}
        int repeats=1;
        if(s->vimCount.revision!=p->revision)s->vimCount.count=0;
        if(s->vimOperator.revision!=p->revision)s->vimOperator.key=0;
        if(s->promptRegisters.revision!=p->revision)vimCancelRegister(s);
        if(p->mode>=2&&!p->vimMode&&!ctrl&&!alt&&!meta){
            if(s->promptRegisters.pending){
                CHECK(!key[1]&&((key[0]>='a'&&key[0]<='z')||(key[0]>='A'&&key[0]<='Z')||key[0]=='_'||key[0]=='"'),"Unsupported Vim register name");
                int upper=key[0]>='A'&&key[0]<='Z';s->promptRegisters.selected=key[0]=='_'?-1:key[0]=='"'?0:(upper?key[0]-'A':key[0]-'a')+1;
                s->promptRegisters.append=upper;s->promptRegisters.pending=0;s->promptRegisters.revision=p->revision;return 0;
            }
            if(!s->vimOperator.key&&!strcmp(key,"\"")){vimCancelRegister(s);s->promptRegisters.pending=1;s->promptRegisters.revision=p->revision;return 0;}
        }
        if(p->mode>=2&&!p->vimMode&&!ctrl&&!alt&&!meta){
            if(key[0]>='0'&&key[0]<='9'&&!key[1]&&(key[0]!='0'||s->vimCount.count)){
                int next=s->vimCount.count*10+key[0]-'0';CHECK(next<=9999,"Vim count exceeds 9999");s->vimCount.count=next;s->vimCount.revision=p->revision;return 0;
            }
            if(s->vimCount.count)repeats=s->vimCount.count;
        }
        s->vimCount.count=0;
        if(p->mode>=2&&!p->vimMode&&!ctrl&&!alt&&!meta){
            if(!s->vimOperator.key&&!strcmp(key,".")){
                RepeatEdit saved=s->repeatEdit;CHECK(saved.key,"No repeatable native deletion");
                int count=explicitCount?historyRepeats:saved.count;
                s->vimCount.count=count;s->vimCount.revision=p->revision;
                s->promptRegisters.selected=saved.selected;s->promptRegisters.append=saved.append;s->promptRegisters.pending=0;s->promptRegisters.revision=p->revision;
                CHECK(repeatKey(c,s,saved.key,saved.unit)>=0,"Repeated deletion rejected");
                if(saved.key=='d')CHECK(repeatKey(c,s,saved.motion,saved.unit)>=0,"Repeated deletion rejected");
                return 0;
            }
            if(!s->vimOperator.key&&(!strcmp(key,"p")||!strcmp(key,"P"))){
                int selected=s->promptRegisters.selected;uint32_t*source=s->promptRegister.glyphs;int n=s->promptRegister.count,linewise=s->promptRegister.linewise;
                if(selected>0){source=s->promptRegisters.slots[selected-1].glyphs;n=s->promptRegisters.slots[selected-1].count;linewise=s->promptRegisters.slots[selected-1].linewise;}
                vimCancelRegister(s);if(selected==-1||!n)return 0;
                int at=unit?nrGraphemeFloor(p->glyphs,p->count,p->caret):p->caret,prefix=0,suffix=0;
                int ends=source[n-1]==10;
                if(linewise){
                    if(key[0]=='P')while(at>0&&p->glyphs[at-1]!=10)at--;
                    else {while(at<p->count&&p->glyphs[at]!=10)at++;if(at<p->count)at++;else if(at>0&&p->glyphs[at-1]!=10)prefix=1;}
                    suffix=!ends&&at<p->count;
                }else if(key[0]=='p'&&at<p->count)at=unit?nrGraphemeAfter(p->glyphs,p->count,at):at+1;
                uint64_t proposed=(uint64_t)n*repeats+prefix+suffix+(linewise&&!ends?repeats-1:0);CHECK(proposed<=INT32_MAX,"Prompt index representation exhausted");int added=(int)proposed;
                CHECK(nrPromptAllowed(s,(uint64_t)p->count+added)&&nrPromptRequire(s,(uint64_t)p->count+added),"Prompt capacity");
                uint32_t*insert=s->dynamicPrompt.scratch;int used=0;if(prefix)insert[used++]=10;
                for(int i=0;i<repeats;i++){memcpy(insert+used,source,(size_t)n*4);used+=n;if(linewise&&!ends&&i+1<repeats)insert[used++]=10;}
                if(suffix)insert[used++]=10;CHECK(pushUndo(s),"Prompt history storage");p->anchor=-1;
                memmove(p->glyphs+at+added,p->glyphs+at,(size_t)(p->count-at)*4);memcpy(p->glyphs+at,insert,(size_t)added*4);p->count+=added;
                p->caret=linewise?at+prefix:unit?nrGraphemeFloor(p->glyphs,p->count,at+added-1):at+added-1;p->revision++;return 0;
            }
            if(!s->vimOperator.key&&(!strcmp(key,"d")||!strcmp(key,"c")||!strcmp(key,"y"))){s->vimOperator.key=key[0];s->vimOperator.count=repeats;s->vimOperator.revision=p->revision;return 0;}
            if(s->vimOperator.key){
                int operation=s->vimOperator.key,total=repeats*s->vimOperator.count;
                CHECK(total<=9999,"Vim combined count exceeds 9999");
                int origin=unit?nrGraphemeFloor(p->glyphs,p->count,p->caret):p->caret,a=origin,b=origin,linewise=!key[1]&&(key[0]==operation||key[0]=='j'||key[0]=='k'),registerA=-1,registerB=-1;
                if(linewise){
                    while(a>0&&p->glyphs[a-1]!=10)a--;
                    if(key[0]=='k'){
                        if(!a){s->vimOperator.key=0;vimCancelRegister(s);return 0;}
                        int previous=total;total=1;
                        while(previous-->0&&a>0){a--;while(a>0&&p->glyphs[a-1]!=10)a--;total++;}
                    }else if(key[0]=='j'){
                        int next=a;while(next<p->count&&p->glyphs[next]!=10)next++;
                        if(next==p->count){s->vimOperator.key=0;vimCancelRegister(s);return 0;}total++;
                    }
                    b=a;
                    for(int i=0;i<total&&b<p->count;i++){while(b<p->count&&p->glyphs[b]!=10)b++;if(b<p->count)b++;}
                    registerA=a;registerB=b;
                    if(operation=='c'){if(b>a&&p->glyphs[b-1]==10)b--;if(b>a&&p->glyphs[b-1]==13)b--;}
                    else if(operation=='d'&&b==p->count&&a>0&&(b==a||p->glyphs[b-1]!=10)){a--;if(a>0&&p->glyphs[a-1]==13)a--;}
                }else{
                    int word=!key[1]&&(key[0]=='w'||key[0]=='b'||key[0]=='e'||key[0]=='W'||key[0]=='B'||key[0]=='E');
                    CHECK(word||!strcmp(key,"h")||!strcmp(key,"l")||!strcmp(key,"0")||!strcmp(key,"^")||!strcmp(key,"$"),"Unsupported Vim operator motion");
                    char motion=key[0];int changeWord=operation=='c'&&(motion=='w'||motion=='W')&&origin<p->count&&promptWordClass(p->glyphs[origin]);int inclusive=motion=='e'||motion=='E'||motion=='$';
                    if(changeWord){motion=motion=='w'?'e':'E';inclusive=1;}
                    p->caret=origin;
                    for(int i=0;i<total;i++){
                        if(word)p->caret=vimWordDestination(p,motion,unit,changeWord&&i==0?2:1);
                        else if(motion=='h')p->caret=unit?nrGraphemeBefore(p->glyphs,p->count,p->caret):p->caret>0?p->caret-1:0;
                        else if(motion=='l')p->caret=unit?nrGraphemeAfter(p->glyphs,p->count,p->caret):p->caret<p->count?p->caret+1:p->count;
                        else if(motion=='$'){while(p->caret<p->count&&p->glyphs[p->caret]!=10&&p->glyphs[p->caret]!=13)p->caret++;inclusive=0;}
                        else {while(p->caret>0&&p->glyphs[p->caret-1]!=10&&p->glyphs[p->caret-1]!=13)p->caret--;if(motion=='^')while(p->caret<p->count&&(p->glyphs[p->caret]==32||p->glyphs[p->caret]==9))p->caret++;}
                    }
                    int destination=p->caret;p->caret=origin;
                    a=destination<origin?destination:origin;b=destination>origin?destination:origin;
                    if(inclusive&&b<p->count)b=unit?nrGraphemeAfter(p->glyphs,p->count,b):b+1;
                }
                RepeatEdit remembered={operation,key[0],total,unit,s->promptRegisters.selected,s->promptRegisters.append};
                s->vimOperator.key=0;
                CHECK(vimStoreRegister(s,registerA>=0&&operation!='c'?registerA:a,registerB>=0&&operation!='c'?registerB:b,linewise),"Vim register capacity");
                if(operation=='y')return 0;
                p->anchor=-1;
                if(b>a){CHECK(pushUndo(s),"Prompt history storage");memmove(p->glyphs+a,p->glyphs+b,(size_t)(p->count-b)*4);p->count-=b-a;memset(p->glyphs+p->count,0,(size_t)(b-a)*4);p->caret=a;p->revision++;if(operation=='d')s->repeatEdit=remembered;}
                if(operation=='c'){p->vimMode=1;if(s->promptFramed.enabled)s->promptFramed.vimState=NR_PROMPT_SOURCE_VIM_INSERT;}
                return 0;
            }
        }
        if(p->mode>=2&&!p->vimMode&&strcmp(key,"x")&&strcmp(key,"X")&&strcmp(key,"s")&&strcmp(key,"D")&&strcmp(key,"C"))vimCancelRegister(s);
        if(p->mode>=2&&!p->vimMode&&(!strcmp(key,"h")||!strcmp(key,"j")||!strcmp(key,"k")||!strcmp(key,"l")))p->anchor=-1;
        if(!strcmp(key,"ArrowLeft")||!strcmp(key,"Home")||(p->mode>=2&&!p->vimMode&&!strcmp(key,"h"))) {
            for(int repetition=0;repetition<repeats;repetition++)p->caret=!strcmp(key,"Home")?0:unit?nrGraphemeBefore(p->glyphs,p->count,p->caret):p->caret>0?p->caret-1:0;
            return 0;
        }
        if(!strcmp(key,"ArrowRight")||!strcmp(key,"End")||(p->mode>=2&&!p->vimMode&&!strcmp(key,"l"))) {
            for(int repetition=0;repetition<repeats;repetition++)p->caret=!strcmp(key,"End")?p->count:unit?nrGraphemeAfter(p->glyphs,p->count,p->caret):p->caret<p->count?p->caret+1:p->count;
            return 0;
        }
        if(!strcmp(key,"ArrowUp")||!strcmp(key,"ArrowDown")||
           (p->mode>=2&&!p->vimMode&&(!strcmp(key,"k")||!strcmp(key,"j")))) {
            for(int repetition=0;repetition<repeats;repetition++)p->caret=nrPromptVertical(s,(!strcmp(key,"ArrowUp")||!strcmp(key,"k"))?-1:1,unit);
            return 0;
        }
        if(!strcmp(key,"Backspace")||!strcmp(key,"Delete")) {
            if(p->anchor>=0&&p->anchor!=p->caret) {
                CHECK(nrInput(s,NULL,0,0),"Prompt capacity");return 0;
            }
            int back=!strcmp(key,"Backspace"),a=p->caret-back,b=a+1;
            if(unit) {
                a=back?nrGraphemeBefore(p->glyphs,p->count,p->caret):nrGraphemeFloor(p->glyphs,p->count,p->caret);
                b=back&&a==p->caret?p->caret:nrGraphemeAfter(p->glyphs,p->count,a);
                if(back&&!p->caret)b=a;
            }
            if(a>=0&&a<p->count&&b>a) {
                CHECK(pushUndo(s),"Prompt history storage");
                memmove(p->glyphs+a,p->glyphs+b,(size_t)(p->count-b)*4);
                p->count-=b-a;memset(p->glyphs+p->count,0,(size_t)(b-a)*4);
                p->caret=unit?nrGraphemeFloor(p->glyphs,p->count,a):a;
                p->revision++;
            }
            return 0;
        }
        if(p->mode>=2&&!p->vimMode) {
            if(!strcmp(key,"W")||!strcmp(key,"B")||!strcmp(key,"E")||!strcmp(key,"w")||!strcmp(key,"b")||!strcmp(key,"e")) {
                p->anchor=-1;
                /* WORDs are non-space/tab/LF runs; empty source lines are WORDs.
                   E skips empty lines. No authored text or simulation mutation. */
                for(int repetition=0;repetition<repeats;repetition++){
                p->caret=vimWordDestination(p,key[0],unit,0);
                }
                return 0;
            }
            if(!strcmp(key,"o")||!strcmp(key,"O")) {
                CHECK(nrPromptAllowed(s,(uint64_t)p->count+1)&&nrPromptRequire(s,(uint64_t)p->count+1),"Prompt capacity");
                int at=p->caret;
                if(key[0]=='O')while(at>0&&p->glyphs[at-1]!=10)at--;
                else while(at<p->count&&p->glyphs[at]!=10)at++;
                CHECK(pushUndo(s),"Prompt history storage");p->anchor=-1; /* Save authored caret before insertion. */
                memmove(p->glyphs+at+1,p->glyphs+at,(size_t)(p->count-at)*4);
                p->glyphs[at]=10;p->count++;
                p->caret=at+(key[0]=='o');p->vimMode=1;if(s->promptFramed.enabled)s->promptFramed.vimState=NR_PROMPT_SOURCE_VIM_INSERT;p->revision++;
                return 0;
            }
            if(!strcmp(key,"0")||!strcmp(key,"^")||!strcmp(key,"$")||!strcmp(key,"I")||!strcmp(key,"A")) {
                p->anchor=-1;int at=p->caret;
                if(at>0&&at<p->count&&p->glyphs[at]==10&&p->glyphs[at-1]==13)at--;
                int start=at,end=at;
                while(start>0&&p->glyphs[start-1]!=10&&p->glyphs[start-1]!=13)start--;
                while(end<p->count&&p->glyphs[end]!=10&&p->glyphs[end]!=13)end++;
                int first=start;
                while(first<end&&(p->glyphs[first]==32||p->glyphs[first]==9))first++;
                if(!strcmp(key,"0"))p->caret=start;
                else if(!strcmp(key,"^")||!strcmp(key,"I"))p->caret=first;
                else if(!strcmp(key,"A"))p->caret=end;
                else p->caret=end>start?(unit?nrGraphemeBefore(p->glyphs,p->count,end):end-1):start;
                if(unit)p->caret=nrGraphemeFloor(p->glyphs,p->count,p->caret);
                if(!strcmp(key,"I")||!strcmp(key,"A")){p->vimMode=1;if(s->promptFramed.enabled)s->promptFramed.vimState=NR_PROMPT_SOURCE_VIM_INSERT;}
                return 0;
            }
            if(!strcmp(key,"x")||!strcmp(key,"X")||!strcmp(key,"s")||!strcmp(key,"D")||!strcmp(key,"C")) {
                if(p->anchor>=0&&p->anchor!=p->caret) {
                    CHECK(vimStoreRegister(s,p->anchor<p->caret?p->anchor:p->caret,p->anchor>p->caret?p->anchor:p->caret,0),"Vim register capacity");
                    CHECK(nrInput(s,NULL,0,0),"Prompt capacity");
                    if(!strcmp(key,"s")||!strcmp(key,"C")){p->vimMode=1;if(s->promptFramed.enabled)s->promptFramed.vimState=NR_PROMPT_SOURCE_VIM_INSERT;}
                    return 0;
                }
                int back=!strcmp(key,"X"),tail=!strcmp(key,"D")||!strcmp(key,"C");
                int a=back?p->caret-1:p->caret,b=a+1;
                if(unit) {
                    a=back?nrGraphemeBefore(p->glyphs,p->count,p->caret):nrGraphemeFloor(p->glyphs,p->count,p->caret);
                    b=nrGraphemeAfter(p->glyphs,p->count,a);
                }
                if(tail) { b=a;while(b<p->count&&p->glyphs[b]!=10&&p->glyphs[b]!=13)b++; }
                if(!tail&&repeats>1){
                    if(back){
                        int cursor=a;for(int n=1;n<repeats&&cursor>0;n++){
                            int previous=unit?nrGraphemeBefore(p->glyphs,p->count,cursor):cursor-1;
                            int newline=0;for(int k=previous;k<cursor;k++)if(p->glyphs[k]==10||p->glyphs[k]==13)newline=1;
                            if(newline)break;cursor=previous;
                        }a=cursor;
                    }else{
                        int cursor=b;for(int n=1;n<repeats&&cursor<p->count;n++){
                            int next=unit?nrGraphemeAfter(p->glyphs,p->count,cursor):cursor+1;
                            int newline=0;for(int k=cursor;k<next;k++)if(p->glyphs[k]==10||p->glyphs[k]==13)newline=1;
                            if(newline)break;cursor=next;
                        }b=cursor;
                    }
                }
                /* Normal edits do not join source lines, including CRLF clusters. */
                int valid=(!back||p->caret>0)&&a>=0&&a<p->count&&b>a;
                for(int i=a;valid&&i<b;i++)if(p->glyphs[i]==10||p->glyphs[i]==13)valid=0;
                if(valid) {
                    RepeatEdit remembered={key[0],0,repeats,unit,s->promptRegisters.selected,s->promptRegisters.append};
                    CHECK(vimStoreRegister(s,a,b,0),"Vim register capacity");CHECK(pushUndo(s),"Prompt history storage");
                    memmove(p->glyphs+a,p->glyphs+b,(size_t)(p->count-b)*4);
                    p->count-=b-a;memset(p->glyphs+p->count,0,(size_t)(b-a)*4);
                    p->caret=unit?nrGraphemeFloor(p->glyphs,p->count,a):a;
                    p->revision++;if(key[0]=='x'||key[0]=='X'||key[0]=='D')s->repeatEdit=remembered;
                }
                if(!valid)vimCancelRegister(s);
                if(!strcmp(key,"s")||!strcmp(key,"C")){p->vimMode=1;if(s->promptFramed.enabled)s->promptFramed.vimState=NR_PROMPT_SOURCE_VIM_INSERT;}
                return 0;
            }
            if(!strcmp(key,"i")||!strcmp(key,"a")) {
                p->vimMode=1;if(s->promptFramed.enabled)s->promptFramed.vimState=NR_PROMPT_SOURCE_VIM_INSERT;
                if(key[0]=='a'&&p->caret<p->count)p->caret=unit?nrGraphemeAfter(p->glyphs,p->count,p->caret):p->caret+1;
                return 0;
            }
            if(!strcmp(key,"u")) {
                for(int repetition=0;repetition<repeats&&p->undoSize;repetition++)CHECK(travelHistory(s,0),"Prompt history storage");
                return 0;
            }
            return reject(c,"Unsupported Vim command; implemented subset: i a I A o O 0 ^ $ W B E h j k l u x X s D C and arrows");
        }
        if(!strcmp(key,"Enter")) {
            uint32_t g=10;
            CHECK(nrInput(s,&g,1,0),"Prompt capacity");
            return 0;
        }
        if(!ctrl&&!alt&&!meta) {
            uint32_t g[8];
            int n=nrDecode(j,nrField(j,0,"key"),g,8);
            if(n==1&&g[0]>=32) {
                CHECK(nrInput(s,g,1,1),"Prompt capacity");
                return 0;
            }
        }
        return reject(c,"Unsupported key");
    }
    if(!strcmp(op,"text")) {
        ALLOW("id text effect phase phaseModel local x y width durationMs staggerMs jitterMs batchSize distance scatter variation wind overshoot cycles scrambleHz hueSpread material seed alphabet easing delayMs reverseOrder randomOrder trailLength");
        int id=0;
        INT("id",id,1,65535);
        CHECK(id,"Text id required");
        int i;
        SLOT(s->text,NR_TEXTS,id,i);
        TextRun*q=&s->text[i];
        TextRun previous=*q;uint32_t previousAlphabetTail[128];memcpy(previousAlphabetTail,s->textAlphabetTail[i],sizeof(previousAlphabetTail));int wasUsed=q->used;
        int previousPhaseModel=(int)s->textPhaseModel[i];
        if(!q->used) {
            memset(q,0,sizeof(*q));
            memset(s->textAlphabetTail[i],0,sizeof(s->textAlphabetTail[i]));
            s->textPhaseModel[i]=0;
            q->used=1;
            q->id=id;
            q->effect=nrEffectId("text/ink-dissolve");
            q->x=8;
            q->y=12;
            q->width=100;
            q->durationUs=1200000;
            q->staggerUs=18000;
            q->distance=12;
            q->scatter=8;
            q->variation=.4;
            q->overshoot=.2;
            q->batchSize=1;
            q->scrambleHz=24;
            q->cycles=4;
            q->material=2;
            q->easing=3;
            q->seed=s->seed;
            const char*a=" ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
            for(; *a; a++)q->alphabet[q->alphabetCount++]=(uint8_t)*a;
        }
        CHECK(effect(j,0,&q->effect,2),"Unknown text effect");
        if(nrField(j,0,"phaseModel")>=0){
            CHECK(s->schema>=NR_STATE_SCHEMA_TEXT_PHASE_MODEL,"Text phase model requires schema67");
            int phaseModel=0;CHOICE("phaseModel",phaseModel,"source reverse-show source-paint");
            CHECK(phaseModel==2?1:nrTextSupportsPhaseModel(q->effect),"Text phase model requires source paint or glyph-fall/ash source phase");
            s->textPhaseModel[i]=(uint32_t)phaseModel+1;
            if(phaseModel==2&&!wasUsed&&nrField(j,0,"material")<0)q->material=15;
        }else if(s->textPhaseModel[i]==3?0:!nrTextSupportsPhaseModel(q->effect))s->textPhaseModel[i]=0;
        if(!wasUsed) {
            int profile=nrEffectProfile(q->effect);
            q->staggerUs=profile?28000:24000;q->jitterUs=profile?0:360000;
            q->distance=profile?13:18;q->scatter=profile?8:5;q->variation=profile?.55:.4;
            q->wind=profile?2:1.3;q->cycles=profile?1.5:3;q->overshoot=profile?1.2:.2;
            q->scrambleHz=profile?18:24;q->hueSpread=profile?110:10;q->trailLength=profile?2:0;
        }
        CHECK(text(j,0,"text",q->text,&q->count,NR_MAX_TEXT),"Text capacity");
        int alphabetToken=nrField(j,0,"alphabet");
        if(alphabetToken>=0){uint32_t alphabet[256]={0};int capacity=s->schema>=NR_STATE_SCHEMA_TEXT_ALPHABET?256:128;
            int count=nrDecode(j,alphabetToken,alphabet,capacity);CHECK(count>0,"Alphabet capacity");
            memset(q->alphabet,0,sizeof(q->alphabet));memset(s->textAlphabetTail[i],0,sizeof(s->textAlphabetTail[i]));
            memcpy(q->alphabet,alphabet,(size_t)(count<128?count:128)*sizeof(uint32_t));
            if(count>128)memcpy(s->textAlphabetTail[i],alphabet+128,(size_t)(count-128)*sizeof(uint32_t));q->alphabetCount=count;
        }
        CHOICE("phase",q->phase,"show hide");
        BOOL("local",q->local);
        INT("x",q->x,NR_LAYOUT_MIN,NR_LAYOUT_MAX);
        INT("y",q->y,NR_LAYOUT_MIN,NR_LAYOUT_MAX);
        INT("width",q->width,1,NR_LAYOUT_MAX);
        INT("material",q->material,0,15);
        INT("batchSize",q->batchSize,1,128);
        uint32_t textSeed;memcpy(&textSeed,&q->seed,sizeof(textSeed));
        CHECK(uinteger(j,0,"seed",&textSeed,0,s->schema>=NR_STATE_SCHEMA_TEXT_UINT32_SEED?0xffffffffu:2147483647u),"Text seed range");
        memcpy(&q->seed,&textSeed,sizeof(textSeed));
        DUR("durationMs",q->durationUs,60000000,1000);
        DUR("staggerMs",q->staggerUs,10000000,1000);
        DUR("jitterMs",q->jitterUs,10000000,1000);
        NUM("distance",q->distance,0,100);
        NUM("scatter",q->scatter,0,120);
        NUM("variation",q->variation,0,2);
        NUM("wind",q->wind,-100,100);
        NUM("overshoot",q->overshoot,0,3);
        NUM("cycles",q->cycles,0,50);
        NUM("scrambleHz",q->scrambleHz,0,120);
        NUM("hueSpread",q->hueSpread,-360,360);
        CHOICE("easing",q->easing,"linear ease-in ease-out smooth smoother sine step cubic back bounce");
        DUR("delayMs",q->delayUs,60000000,1000);BOOL("reverseOrder",q->reverseOrder);BOOL("randomOrder",q->randomOrder);INT("trailLength",q->trailLength,0,8);
        CHECK(q->count<=0||(uint64_t)s->nextGlyphIdentity+q->count<0xffffffffu,"Glyph identity capacity");
        nrPrepareTextWithModels(q,s->textAlphabetTail[i],(int)s->textPhaseModel[i],wasUsed?&previous:NULL,previousAlphabetTail,previousPhaseModel,s->timeUs,&s->nextGlyphIdentity);
        q->startUs=s->timeUs;
        return 0;
    }
    if(!strcmp(op,"window")) {
        ALLOW("id title text effect shape position yaw pitch roll width height alpha material durationMs group minColumns maxColumns anchorX anchorY overshoot scatter bend folds meshColumns meshRows seed polygon padding border fadeStartRatio fadeEndRatio chromeSize sourceGeometry sourcePresentation depthFade chrome controlWidth controlHeight customSide customOrder customGlyphs");
        int id=0;
        INT("id",id,1,65535);
        CHECK(id,"Window id required");
        int i;
        SLOT(s->windows,(s->schema<NR_STATE_SCHEMA_WINDOW_POOLS?12u:NR_MAX_WINDOWS),id,i);
        Window*w=&s->windows[i];
        if(!w->used) {
            memset(w,0,sizeof(*w));s->windowSourceGeometry[i]=0;memset(&s->windowPresentation[i],0,sizeof(s->windowPresentation[i]));
            w->used=1;
            w->id=id;
            w->effect=nrEffectId("window-transition/glass-dissolve");
            w->position=nrV((i%3-1)*24,8-(i/3)*20,0);
            w->width=28;
            w->height=22;
            w->alpha=.8;
            w->material=2;
            w->durationUs=600000;w->minColumns=30;w->maxColumns=78;
            w->anchorX=.5;w->anchorY=1.15;w->overshoot=.18;w->scatter=32;w->bend=9;
            w->folds=6;w->meshColumns=12;w->meshRows=8;w->seed=s->seed;
            w->target=1;
            w->padding=1;w->border=1;w->chromeSize=3;
            w->fadeStartRatio=1;w->fadeEndRatio=.22;
            w->atUs=s->timeUs;
        }
        INT("minColumns",w->minColumns,8,NR_LAYOUT_MAX);INT("maxColumns",w->maxColumns,8,NR_LAYOUT_MAX);
        INT("padding",w->padding,0,8);INT("chromeSize",w->chromeSize,1,5);
        CHOICE("border",w->border,"none rounded square double heavy");
        NUM("fadeStartRatio",w->fadeStartRatio,.001,8);NUM("fadeEndRatio",w->fadeEndRatio,0,8);
        CHECK(w->minColumns<=w->maxColumns&&w->minColumns>2*(w->padding+1),"Window column range and padding");
        CHECK(w->fadeEndRatio<w->fadeStartRatio,"Readable fade end must be below fade start");
        CHECK(text(j,0,"title",w->title,&w->titleCount,160)&&text(j,0,"text",w->text,&w->textCount,NR_MAX_TEXT),"Window document capacity");
        int sourceGeometry=(int)s->windowSourceGeometry[i];
        if(nrField(j,0,"sourceGeometry")>=0){CHECK(s->schema>=NR_STATE_SCHEMA_WINDOW_SOURCE,"Source window geometry requires schema66");BOOL("sourceGeometry",sourceGeometry);s->windowSourceGeometry[i]=(uint32_t)sourceGeometry;}
        CHECK(effect(j,0,&w->effect,3),"Unknown window transition");
        CHOICE("shape",w->shape,"rectangle rounded ellipse hexagon diamond capsule ticket squircle petal wave cloud polygon");
        NUM("anchorX",w->anchorX,-2,3);NUM("anchorY",w->anchorY,-2,3);
        NUM("overshoot",w->overshoot,0,1);NUM("scatter",w->scatter,0,100);NUM("bend",w->bend,-40,40);
        INT("folds",w->folds,1,32);INT("meshColumns",w->meshColumns,2,32);INT("meshRows",w->meshRows,2,24);
        CHECK(uinteger(j,0,"seed",&w->seed,0,0xffffffffu),"Window seed uint32");
        int polygon=nrField(j,0,"polygon");
        if(polygon>=0) {
            CHECK(j->tokens[polygon].type==J_ARRAY&&j->tokens[polygon].count>=3&&j->tokens[polygon].count<=32,"Polygon requires 3..32 UV points");
            w->polygonCount=j->tokens[polygon].count;int point=polygon+1;
            for(int k=0;k<w->polygonCount;k++) {
                CHECK(j->tokens[point].type==J_ARRAY&&j->tokens[point].count==2,"UV point requires two coordinates");
                int t=point+1;
                for(int axis=0;axis<2;axis++) {double v;CHECK(nrNumber(j,t,&v)&&v>=0&&v<=1,"UV coordinates must be normalized");w->polygon[k][axis]=v;t=j->tokens[t].next;}
                point=j->tokens[point].next;
            }
            double area=0;for(int k=0;k<w->polygonCount;k++){int n=(k+1)%w->polygonCount;area+=w->polygon[k][0]*w->polygon[n][1]-w->polygon[n][0]*w->polygon[k][1];}
            CHECK(nrAbs(area)>1e-8,"Degenerate polygon");
        }
        CHECK(w->shape!=11||w->polygonCount>=3,"Polygon shape requires polygon vertices");
        CHECK((!s->windowTextures.windows[i].width&&!s->windowContent[i].enabled)||w->shape<=9||s->atelierWindows[i].enabled,"Textured windows require an original source shape");
        VEC("position",w->position,-16000,16000);
        NUM("yaw",w->yaw,-36000,36000);
        NUM("pitch",w->pitch,-36000,36000);
        NUM("roll",w->roll,-36000,36000);
        NUM("width",w->width,1,NR_LAYOUT_MAX);
        NUM("height",w->height,1,NR_LAYOUT_MAX);
        NUM("alpha",w->alpha,0,1);
        WindowSourcePresentationState presentation;double sourceAlpha;
        int presentationStatus=nrWindowPresentationPatch(j,&s->windowPresentation[i],w->alpha,&presentation,&sourceAlpha);
        CHECK(presentationStatus>=0,"Invalid source window presentation");
        if(presentationStatus){
            CHECK(s->schema>=NR_STATE_SCHEMA_WINDOW_PRESENTATION,"Source window presentation requires current schema");
            s->windowPresentation[i]=presentation;w->alpha=sourceAlpha;
            if(!presentation.enabled)s->windowSourceOrder[i]=0;
        }
        INT("material",w->material,0,15);
        INT("group",w->group,0,65535);
        DUR("durationMs",w->durationUs,60000000,1000);
        selectWindow(s,id);
        return 0;
    }
    if(!strcmp(op,"window-action")) {
        ALLOW("id action dx dy forward yaw pitch roll durationMs effect group rows");
        int id=s->selectedWindow;
        INT("id",id,1,65535);
        int i=nrFindWindow(s,id);
        CHECK(i>=0,"Window not found");
        Window*w=&s->windows[i];
        int action=0;
        CHOICE("action",action,"restore minimize close maximize move rotate summon visit roll-up roll-down read scroll page-next page-prev background fade");
        if(action==15){DUR("durationMs",w->durationUs,60000000,1000);CHECK(nrAtelierWindowAction(s,i,15),"Fade requires original Atelier content");return 0;}
        if(action==14){CHECK(backgroundWindow(s,i),"Source background action requires a live source window and representable depth");return 0;}
        if(action>=10) {
            if(action==10){if(s->windowContent[i].enabled){WindowContent*q=&s->windowContent[i];q->visibilityFrom=q->visibilityTo=1;q->atUs=s->timeUs;q->visibilityDurationUs=0;}w->reader=1;w->target=1;w->fromVisibility=1;w->atUs=s->timeUs;nrPointerRelease(s);}
            else {int rows=0;INT("rows",rows,-2048,2048);if(action==12)rows=nrWindowReaderPageRows(s);if(action==13)rows=-nrWindowReaderPageRows(s);int maximum=w->reader?nrWindowReaderMaxScroll(s,w):(int)NR_MAX_TEXT;int first=(int)nrClamp(w->scrollRow,0,maximum);w->scrollRow=(int)nrClamp(first+rows,0,maximum);}
            selectWindow(s,id);return 0;
        }
        double current=nrWindowVisibility(w,s->timeUs);
        CHECK(effect(j,0,&w->effect,3),"Unknown transition");
        DUR("durationMs",w->durationUs,60000000,1000);
        INT("group",w->group,0,65535);
        if(nrWindowContentAction(s,i,action)){if(!s->atelierWindows[i].enabled||action==0||action==3)selectWindow(s,id);return 0;}
        if(action<4||action>=8) {
            w->fromVisibility=current;
            w->target=(action==0||action==3||action==9);
            w->atUs=s->timeUs;
            if(action==3)w->maximized=!w->maximized;
        }
        else if(action==4) {
            double dx=0,dy=0,forward=0;
            NUM("dx",dx,-1000,1000);
            NUM("dy",dy,-1000,1000);
            NUM("forward",forward,-1000,1000);
            Camera cam=nrCameraAt(s);
            Vec3 r,u,f;
            nrBasis(&cam,&r,&u,&f);
            w->position=nrAdd(w->position,nrAdd(nrAdd(nrScale(r,dx),nrScale(u,-dy)),nrScale(f,forward)));
        }
        else if(action==5) {
            double yaw=0,pitch=0,roll=0;
            NUM("yaw",yaw,-3600,3600);
            NUM("pitch",pitch,-3600,3600);
            NUM("roll",roll,-3600,3600);
            w->yaw+=yaw;
            w->pitch+=pitch;
            w->roll+=roll;
        }
        else if(action==6) {
            Camera cam=nrCameraAt(s);
            Vec3 r,u,f;
            nrBasis(&cam,&r,&u,&f);
            w->position=nrAdd(cam.position,nrScale(f,38));
            nrWindowContentAction(s,i,0);
            w->yaw=cam.yaw;
            w->pitch=cam.pitch;
            w->roll=cam.roll;
            w->fromVisibility=current;
            w->anchorX=.5;w->anchorY=1.15;w->overshoot=.18;w->scatter=32;w->bend=9;
            w->folds=6;w->meshColumns=12;w->meshRows=8;w->seed=s->seed;
            w->target=1;
            w->padding=1;w->border=1;w->chromeSize=3;
            w->fadeStartRatio=1;w->fadeEndRatio=.22;
            w->atUs=s->timeUs;
        }
        else {
            Camera cam=s->camera;
            cam.yaw=w->yaw;
            cam.pitch=nrClamp(w->pitch,-89,89);
            cam.roll=w->roll;
            Vec3 r,u,f;
            nrBasis(&cam,&r,&u,&f);
            cam.position=nrSub(w->position,nrScale(f,40));
            s->camera=cam;
            memset(&s->flight,0,sizeof(s->flight));nrOriginalCameraStop(s);
        }
        selectWindow(s,id);
        return 0;
    }
    if(!strcmp(op,"dock-page")) {
        ALLOW("page");INT("page",s->dockPage,0,11);return 0;
    }
    if(!strcmp(op,"gather")) {
        ALLOW("group");
        int group=0;
        INT("group",group,0,65535);
        Camera cam=nrCameraAt(s);
        Vec3 r,u,f;
        nrBasis(&cam,&r,&u,&f);
        int k=0;
        for(int i=0; i<(int)NR_MAX_WINDOWS; i++) {
            Window*w=&s->windows[i];
            if(!w->used||(group&&group!=w->group))continue;
            w->position=nrAdd(nrAdd(cam.position,nrScale(f,48)),nrAdd(nrScale(r,((k%3)-1)*25),nrScale(u,8-(k/3)*20)));
            w->yaw=cam.yaw;
            w->pitch=cam.pitch;
            w->roll=cam.roll;
            nrWindowContentAction(s,i,0);
            w->fromVisibility=nrWindowContentVisibility(s,i);
            w->anchorX=.5;w->anchorY=1.15;w->overshoot=.18;w->scatter=32;w->bend=9;
            w->folds=6;w->meshColumns=12;w->meshRows=8;w->seed=s->seed;
            w->target=1;
            w->padding=1;w->border=1;w->chromeSize=3;
            w->fadeStartRatio=1;w->fadeEndRatio=.22;
            w->atUs=s->timeUs;
            k++;
        }
        return 0;
    }
    if(!strcmp(op,"node")) {
        Node*n=&c->nodePlan;int slot,created;if(planNode(c,s,j,n,&slot,&created)<0)return -1;
        s->nodes[slot]=*n;return 0;
    }
    if(!strcmp(op,"edge")) {
        ALLOW("from to kind");
        int from=0,to=0,kind=0;
        INT("from",from,1,65535);
        INT("to",to,1,65535);
        CHOICE("kind",kind,"contains depends parent reference produces related");
        CHECK(nrFindNode(s,from)>=0&&nrFindNode(s,to)>=0,"Edge endpoints must exist");
        for(int i=0; i<s->edgeCount; i++)CHECK(s->edges[i].from!=from||s->edges[i].to!=to||s->edges[i].kind!=kind,"Duplicate typed edge");
        CHECK(s->edgeCount<NR_EDGES,"Edge capacity");
        s->edges[s->edgeCount++]=(Edge) {
            from,to,kind
        };
        return 0;
    }
    if(!strcmp(op,"layout")) {
        int profile=nrField(j,0,"profile");if(profile>=0){CHECK(nrEqual(j,profile,"source"),"Unknown graph layout profile");return nrGraphSourceLayout(c,s,j);}
        ALLOW("dimensions mode iterations spacing");
        int dims=s->dimensions,mode=s->layoutMode,it=80;
        double spacing=30;
        INT("dimensions",dims,2,3);
        CHOICE("mode",mode,"layered force radial");
        INT("iterations",it,1,512);
        NUM("spacing",spacing,5,120);
        nrGraphLayout(s,dims,mode,spacing,it);
        return 0;
    }
    if(!strcmp(op,"select")) {
        ALLOW("id durationMs");
        int id=0;
        INT("id",id,0,65535);
        uint64_t d=900000;
        DUR("durationMs",d,60000000,1000);
        CHECK(nrSelectNode(s,id,d),"Node not found");
        return 0;
    }
    if(!strcmp(op,"inspector-scroll")) {
        ALLOW("rows");int rows=0;INT("rows",rows,-8192,8192);CHECK(s->selection,"No selected graph node");
        s->selectionScroll=(int)nrClamp(s->selectionScroll+rows,0,graphInspectorMaxScroll(s));return 0;
    }
    if(!strcmp(op,"area")) {
        ALLOW("id parent x y width height padding margin alpha border hideEmpty speedX speedY material fadeMs gapMs layout");
        int id=0;
        INT("id",id,1,65535);
        CHECK(id,"Area id required");
        int i;
        SLOT(s->areas,NR_AREAS,id,i);
        Area*a=&s->areas[i];
        if(!a->used) {
            memset(a,0,sizeof(*a));
            a->used=1;
            a->id=id;
            a->width=80;
            a->height=4;
            a->border=1;
            a->padding=1;
            a->alpha=.4;
            a->material=2;
            a->speedX=8;
            a->speedY=1;
            a->fadeUs=500000;
            a->gapUs=300000;
        }
        INT("parent",a->parent,0,65535);
        CHECK(a->parent!=id,"Area cannot parent itself");
        if(a->parent) {
            int p=a->parent;
            for(int depth=0; p; depth++) {
                CHECK(depth<NR_AREAS&&p!=id,"Area cycle");
                int found=0;
                for(int z=0; z<NR_AREAS; z++)if(s->areas[z].used&&s->areas[z].id==p) {
                    p=s->areas[z].parent;
                    found=1;
                    break;
                }
                CHECK(found,"Area parent missing");
            }
        }
        INT("x",a->x,NR_LAYOUT_MIN,NR_LAYOUT_MAX);
        INT("y",a->y,NR_LAYOUT_MIN,NR_LAYOUT_MAX);
        INT("width",a->width,1,NR_LAYOUT_MAX);
        INT("height",a->height,1,NR_LAYOUT_MAX);
        INT("padding",a->padding,0,8);
        INT("margin",a->margin,0,8);
        NUM("alpha",a->alpha,0,1);
        NUM("speedX",a->speedX,-100,100);
        NUM("speedY",a->speedY,-30,30);
        CHOICE("border",a->border,"none rounded square double heavy");
        BOOL("hideEmpty",a->hideEmpty);
        INT("material",a->material,0,15);
        DUR("fadeMs",a->fadeUs,60000000,1000);
        DUR("gapMs",a->gapUs,60000000,1000);
        CHOICE("layout",a->layout,"ordered queue direct");
        nrStatusTick(s);return 0;
    }
    if(!strcmp(op,"status")) return nrNotificationCommand(c,s,j);
    if(!strcmp(op,"emit-intent"))return nrHostEventCommand(c,s,j);
    if(!strcmp(op,"notification-action")) {
        ALLOW("id actionId");int id=0,action=0;INT("id",id,1,65535);INT("actionId",action,1,65535);
        CHECK(id&&action,"Notification and action identities required");
        return nrNotificationActivate(c,s,id,action);
    }
    if(!strcmp(op,"ack-intent")) {
        ALLOW("id");double id=0;NUM("id",id,1,9007199254740991.0);CHECK(id>=1&&id==(uint64_t)id,"Intent id required");
        for(int i=0;i<NR_INTENTS;i++)if(s->intents[i].used&&s->intents[i].id==(uint64_t)id){memset(&s->intents[i],0,sizeof(Intent));memset(&s->intentPayloads[i],0,sizeof(IntentPayload));}
        return 0;
    }
    if(!strcmp(op,"ack-status")) {
        ALLOW("id");int id=0;INT("id",id,1,65535);CHECK(id,"Message id required");
        for(int i=0;i<NR_MESSAGES;i++)if(s->messages[i].used&&s->messages[i].id==id){s->messages[i].acknowledged=1;return 0;}
        CHECK(0,"Message not found");
    }
    if(!strcmp(op,"dismiss")||!strcmp(op,"purge-status")) {
        ALLOW("id");int id=0;INT("id",id,1,65535);CHECK(id,"Message id required");
        int found=-1;for(int i=0;i<NR_MESSAGES;i++)if(s->messages[i].used&&s->messages[i].id==id)found=i;
        CHECK(found>=0,"Message not found");Message*m=&s->messages[found];
        if(!strcmp(op,"purge-status")) {CHECK(m->state>=2,"Dismiss before purging a live message");CHECK(!m->important||m->acknowledged,"Acknowledge important record before purging");memset(m,0,sizeof(*m));}
        else {
            if(m->state==1)for(int i=0;i<NR_AREAS;i++)if(s->areas[i].used&&s->areas[i].id==m->area)s->areas[i].availableUs=s->timeUs+s->areas[i].gapUs;
            m->state=3;
        }
        nrStatusTick(s);return 0;
    }
    if(!strcmp(op,"indicator")) {
        ALLOW("id area x y sequence stepMs material cursor");
        int id=0;
        INT("id",id,1,65535);
        CHECK(id,"Indicator id");
        int i;
        SLOT(s->indicators,NR_INDICATORS,id,i);
        Indicator*a=&s->indicators[i];
        if(!a->used) {
            memset(a,0,sizeof(*a));
            a->used=1;
            a->id=id;
            a->stepUs=120000;
            a->count=4;
            a->glyphs[0]='/';
            a->glyphs[1]='|';
            a->glyphs[2]='\\';
            a->glyphs[3]='-';
            a->material=2;
        }
        CHECK(text(j,0,"sequence",a->glyphs,&a->count,128)&&a->count>0,"Indicator sequence");
        INT("area",a->area,0,65535);
        INT("x",a->x,NR_LAYOUT_MIN,NR_LAYOUT_MAX);
        INT("y",a->y,NR_LAYOUT_MIN,NR_LAYOUT_MAX);
        INT("material",a->material,0,15);
        DUR("stepMs",a->stepUs,60000000,1000);
        CHECK(a->stepUs>0,"Indicator step must be positive");
        BOOL("cursor",a->cursor);
        return 0;
    }
    if(!strcmp(op,"widget")) {
        Widget*w=&c->widgetPlan;int slot;if(planWidget(c,s,j,w,&slot)<0)return -1;
        s->widgets[slot]=*w;return 0;
    }
    if(!strcmp(op,"remove-trigger")) {
        ALLOW("id");int id=0;INT("id",id,1,65535);CHECK(id,"Trigger id required");
        for(int i=0;i<NR_TRIGGERS;i++)if(s->triggers[i].used&&s->triggers[i].id==id){memset(&s->triggers[i],0,sizeof(Trigger));memset(&s->triggerFormulas[i],0,sizeof(NumericFormula));memset(&s->triggerDataFormulas[i],0,sizeof(DataFormula));memset(&s->triggerGuardFormulas[i],0,sizeof(DataFormula));break;}return 0;
    }
    if(!strcmp(op,"remove-value")) {
        ALLOW("path");char path[128]={0};CHECK(string(j,0,"path",path,sizeof(path))&&path[0]=='/',"Absolute value path required");
        for(int i=0;i<NR_VALUES;i++){if(s->values[i].used&&!strcmp(s->values[i].path,path)){
            CHECK(!nrValueInUse(c,s,i),"Value still referenced by trigger, style rule or scheduled command");
            memset(&s->values[i],0,sizeof(Value));memset(&s->typedValues[i],0,sizeof(TypedValue));break;
        }}
        return 0;
    }
    if(!strcmp(op,"define")) {
        ALLOW("path value readonly binding type");
        char path[128]= {
            0
        };
        CHECK(string(j,0,"path",path,sizeof(path))&&path[0]=='/',"Absolute value path required");
        int i=-1;
        for(int k=0; k<NR_VALUES; k++) {
            CHECK(!s->values[k].used||strcmp(s->values[k].path,path),"Duplicate value path");
            if(!s->values[k].used&&i<0)i=k;
        }
        CHECK(i>=0,"Value capacity");
        Value*v=&s->values[i];
        memset(v,0,sizeof(*v));
        v->used=1;
        memcpy(v->path,path,strlen(path)+1);
        TypedValue*t=&s->typedValues[i];memset(t,0,sizeof(*t));
        int token=nrField(j,0,"value"),type=nrField(j,0,"type");
        if(type>=0){const char*names[]={"number","boolean","string","json"};t->kind=-1;
            for(int k=0;k<4;k++)if(nrEqual(j,type,names[k]))t->kind=k;CHECK(t->kind>=0,"Unknown value type");}
        else if(token>=0){int root=j->tokens[token].type;t->kind=root==J_NUMBER?0:(root==J_TRUE||root==J_FALSE)?1:root==J_STRING?2:3;}
        BOOL("readonly",v->readonly);
        CHECK(bindNew(v,j,nrField(j,0,"binding")),"Invalid value binding");
        if(t->kind){CHECK(token>=0&&nrTypedSet(s,i,j,token),"Typed value or binding rejected");}
        else{NUM("value",v->value,-1e12,1e12);CHECK(nrBindValue(s,v,v->value),"Invalid value binding");}
        return 0;
    }
    if(!strcmp(op,"bind")) {
        ALLOW("path binding");char path[128]={0};
        CHECK(string(j,0,"path",path,sizeof(path))&&path[0]=='/',"Absolute value path required");
        int slot=-1;for(int i=0;i<NR_VALUES;i++)if(s->values[i].used&&!strcmp(s->values[i].path,path))slot=i;
        CHECK(slot>=0,"Missing value path");int token=nrField(j,0,"binding");
        CHECK(token>=0,"Explicit binding or null required");
        Value candidate=s->values[slot];candidate.bindingFamily=0;candidate.bindingId=0;memset(candidate.field,0,sizeof(candidate.field));
        CHECK(j->tokens[token].type==J_NULL||bindNew(&candidate,j,token),"Invalid replacement binding");
        CHECK(s->typedValues[slot].kind?nrTypedApply(s,&candidate,&s->typedValues[slot]):nrBindValue(s,&candidate,candidate.value),"Replacement binding rejects retained value");
        s->values[slot]=candidate;return 0;
    }
    if(!strcmp(op,"set")) {
        int i,expression,intent;if(planSetTarget(c,s,j,&i,&expression,&intent)<0)return -1;
        double v=s->values[i].value;
        /* A dynamic queued expression may become unavailable after registration.
         * Import checks its grammar/references while leaving execution and its
         * output binding/type checks for the normal atomic clock transaction. */
        if(expression>=0&&nrPendingExpressionShape(c,s,j,expression,intent))return 0;
        if(s->typedValues[i].kind){
            CHECK(expression>=0?nrTypedExpression(c,s,i,j,expression,intent):nrTypedSet(s,i,j,nrField(j,0,"value")),"Typed value, expression or binding rejected");
        }else{
            if(expression>=0)CHECK(nrNumericExpression(s,j,expression,intent,&v)||nrDataNumericExpression(c,s,j,expression,intent,&v),"Invalid numeric expression or retained intention");
            else NUM("value",v,-1e12,1e12);
            CHECK(nrBindValue(s,&s->values[i],v),"Bound value rejected");s->values[i].value=v;
        }
        CHECK(nrEvaluateValues(c,s),"Trigger target rejected; transaction rolled back");
        return 0;
    }
    if(!strcmp(op,"trigger")) {
        ALLOW("id source target comparison threshold hysteresis value valueFrom expression action debounceMs cooldownMs when whenExpression edge event");
        int id=0;
        INT("id",id,1,65535);
        CHECK(id,"Trigger id");
        int i;
        SLOT(s->triggers,NR_TRIGGERS,id,i);
        Trigger*t=&s->triggers[i];
        int valueFromToken=nrField(j,0,"valueFrom");
        int valueToken=nrField(j,0,"value");
        int expressionToken=nrField(j,0,"expression");
        CHECK(expressionToken<0||(valueToken<0&&valueFromToken<0),"Choose expression OR value OR valueFrom");
        CHECK(valueFromToken<0||(valueToken<0&&nrEqual(j,valueFromToken,"intentValue")),"valueFrom must be intentValue and cannot be combined with value");
        int actionFromIntent=valueFromToken>=0;
        /* Reauthoring the guard must not replay a notification already accepted
         * by this stable rule/event subscription. Pending debounce restarts. */
        char previousEvent[128];memcpy(previousEvent,t->eventPath,sizeof(previousEvent));
        uint64_t acceptedIntent=t->lastIntent,lastFire=t->lastFireUs;
        uint32_t fireCount=t->fireCount;int hasFired=t->hasFired,wasUsed=t->used;
        memset(&s->triggerFormulas[i],0,sizeof(NumericFormula));
        memset(&s->triggerDataFormulas[i],0,sizeof(DataFormula));memset(&s->triggerGuardFormulas[i],0,sizeof(DataFormula));
        memset(t,0,sizeof(*t));
        t->used=1;
        t->id=id;
        t->source=t->target=-1;
        char a[128]= {
            0
        },b[128]= {
            0
        };
        CHECK(string(j,0,"target",b,sizeof(b))&&b[0],"Trigger target required");
        int when=nrField(j,0,"when"),whenExpression=nrField(j,0,"whenExpression");
        CHECK(when<0||whenExpression<0,"Choose condition tree OR typed guard expression");
        if(whenExpression>=0){
            CHECK(nrField(j,0,"source")<0&&nrField(j,0,"comparison")<0&&nrField(j,0,"threshold")<0&&nrField(j,0,"hysteresis")<0,"Choose guard expression OR scalar source");
            CHECK(nrCompileDataFormula(s,j,whenExpression,&s->triggerGuardFormulas[i]),"Invalid retained guard expression");
            t->conditionCount=1;t->conditions[0]=(Condition){.kind=5,.source=-1,.end=1};
        }else if(when>=0) {
            CHECK(nrField(j,0,"source")<0&&nrField(j,0,"comparison")<0&&nrField(j,0,"threshold")<0&&nrField(j,0,"hysteresis")<0,"Choose a condition tree OR scalar source configuration");
            CHECK(nrParseConditions(s,j,when,t),"Invalid condition tree, references, or capacity");
        } else CHECK(string(j,0,"source",a,sizeof(a))&&a[0],"Trigger source or condition tree required");
        for(int k=0; k<NR_VALUES; k++)if(s->values[k].used) {
            if(!strcmp(s->values[k].path,a))t->source=k;
            if(!strcmp(s->values[k].path,b))t->target=k;
        }
        CHECK((when>=0||whenExpression>=0||t->source>=0)&&t->target>=0&&!s->values[t->target].readonly&&(when>=0||whenExpression>=0||!s->typedValues[t->source].kind),"Trigger references");
        CHOICE("comparison",t->comparison,"above below equal");
        CHOICE("action",t->action,"set increment");
        NUM("threshold",t->threshold,-1000000,1000000);
        NUM("hysteresis",t->hysteresis,0,1000000);
        NUM("value",t->value,-1000000,1000000);
        DUR("debounceMs",t->debounceUs,86400000000ull,1000);
        DUR("cooldownMs",t->cooldownUs,86400000000ull,1000);
        CHOICE("edge",t->edge,"rising falling change level");
        CHECK(string(j,0,"event",t->eventPath,sizeof(t->eventPath)),"Event path length");
        CHECK(!t->eventPath[0]||(nrEventPath(t->eventPath)&&t->edge==0),"Event filters require a valid path and rising semantics");
        CHECK(!actionFromIntent||(t->eventPath[0]&&nrEventPath(t->eventPath)),"valueFrom intentValue requires an event path");
        if(wasUsed&&t->eventPath[0]&&!strcmp(previousEvent,t->eventPath)) {
            t->lastIntent=acceptedIntent;t->lastFireUs=lastFire;
            t->fireCount=fireCount;t->hasFired=hasFired;
        }
        if(when<0&&whenExpression<0) {
            t->conditionCount=1;
            t->conditions[0]=(Condition){.source=t->source,.comparison=t->comparison,.end=1,
                .low=t->threshold,.high=t->threshold,.hysteresis=t->hysteresis};
        }
        /* The scalar source has now been copied into Condition.source; the
         * trigger slot can record the separate dynamic action operand. */
        if(actionFromIntent)t->source=NR_TRIGGER_SOURCE_INTENT_VALUE;
        CHECK(!s->triggerGuardFormulas[i].tree.usesIntent||t->eventPath[0],"Intention guard requires an event path");
        if(s->typedValues[t->target].kind){
            CHECK(expressionToken>=0&&!t->action,"Typed trigger requires an expression and set action");
            CHECK(nrCompileDataFormula(s,j,expressionToken,&s->triggerDataFormulas[i]),"Invalid retained typed expression");
            CHECK(!s->triggerDataFormulas[i].tree.usesIntent||t->eventPath[0],"Intention formula requires an event path");
        }else if(expressionToken>=0){
            if(!nrCompileTriggerFormula(s,j,expressionToken,&s->triggerFormulas[i])){
                memset(&s->triggerFormulas[i],0,sizeof(NumericFormula));
                CHECK(nrCompileDataFormula(s,j,expressionToken,&s->triggerDataFormulas[i]),"Invalid retained numeric or conditional expression");
                CHECK(!s->triggerDataFormulas[i].tree.usesIntent||t->eventPath[0],"Intention formula requires an event path");
            }else CHECK(!s->triggerFormulas[i].usesIntent||t->eventPath[0],"Intention formula requires an event path");
        }
        return 0;
    }
    if(!strcmp(op,"wheel")||!strcmp(op,"pointer")) {
        CHECK(s->width==c->state.width&&s->height==c->state.height,"Resize must precede pointer transaction");
        CHECK(nrRenderMemorySize(c)<=c->renderMemoryBytes,"Viewport render memory required");
        int wheel=!strcmp(op,"wheel");
        if(wheel) {
            ALLOW("delta shift x y");
        }
        else {
            ALLOW("phase x y button shift alt");
        }
        double x=0,y=0,delta=0;
        int phase=0,shift=0,alt=0,button=0;
        NUM("x",x,-2147483647.0/2,2147483647.0/2);
        NUM("y",y,-2147483647.0/4,2147483647.0/4);
        BOOL("shift",shift);
        BOOL("alt",alt);
        if(wheel) {
            NUM("delta",delta,-100,100);
            if(s->promptDocument.modal||nrModalPointerOwns(s,x,y))return 0;
            int reader=nrFindWindow(s,s->selectedWindow);
            if(reader>=0&&s->windows[reader].reader&&s->windows[reader].target&&nrField(j,0,"x")>=0&&nrField(j,0,"y")>=0&&x>=1&&y>=1&&x<(int)s->width-1&&y<(int)s->height-1){Window*w=&s->windows[reader];int maximum=nrWindowReaderMaxScroll(s,w);int first=(int)nrClamp(w->scrollRow,0,maximum);w->scrollRow=(int)nrClamp(first-delta*3,0,maximum);return 0;}
            if(nrField(j,0,"y")>=0&&y>=c->promptTop)return 0;
            if(s->selection&&nrField(j,0,"x")>=0&&nrField(j,0,"y")>=0&&x>=(int)s->width-37&&x<(int)s->width-1&&y>=2&&y<c->promptTop-1){s->selectionScroll=(int)nrClamp(s->selectionScroll-delta*3,0,graphInspectorMaxScroll(s));return 0;}
            Camera cam=nrCameraAt(s);
            Vec3 r,u,f;
            nrBasis(&cam,&r,&u,&f);
            int wi=nrFindWindow(s,s->selectedWindow);
            if(shift&&wi>=0)s->windows[wi].position=nrAdd(s->windows[wi].position,nrScale(f,delta*2));
            else if(cam.orthographic&&(!s->cameraControls.configured||
                    (!s->cameraControls.inputTarget&&s->cameraControls.rig!=1&&s->cameraControls.axes[2].action==6))) {
                CameraControls*k=&s->cameraControls;
                const CameraAxisControl*a=&k->axes[2];
                if(nrCameraPathOwned(s)||(k->configured&&(!a->enabled||!a->sensitivity)))return 0;
                double amount=delta*(k->configured?a->sensitivity*(a->invert?-1:1):2);
                if(!amount)return 0;
                /* Reciprocal signed steps make opposite wheel input reversible.
                   Scaling view offset and span together holds the picked pixel. */
                double span=nrClamp(cam.span*(amount>0?1/(1+amount*.1):1-amount*.1),.1,2000);
                double ratio=span/cam.span;
                OriginalCamera grab=s->originalCamera;
                Vec3 pivot=k->configured&&k->anchorEnabled?k->anchor:
                    grab.grabActive?grab.grabbed:grab.enabled?grab.target:
                    nrAdd(cam.position,nrScale(f,cam.span));
                Vec3 translation=nrScale(nrSub(pivot,cam.position),1-ratio);
                Camera before=nrCameraCarrierAt(s),desired=before;
                desired.position=nrAdd(desired.position,translation);desired.span=span;
                if(k->configured&&k->rig==3){k->cranePivot=nrAdd(k->cranePivot,translation);k->craneBoom=nrSub(desired.position,k->cranePivot);}
                if(k->configured&&k->rig==4)k->followOffset=nrSub(desired.position,k->followReference);
                nrCameraManualPose(s,&before,&desired);
                if(grab.grabActive){s->originalCamera.grabActive=grab.grabActive;s->originalCamera.grabSource=grab.grabSource;s->originalCamera.grabWidth=grab.grabWidth;s->originalCamera.grabHeight=grab.grabHeight;s->originalCamera.grabbed=grab.grabbed;}
            }
            else if(s->cameraControls.configured)nrCameraControlInput(s,0,0,delta,0);
            else if(!nrCameraPathOwned(s)) {
                Camera before=cam;
                if(cam.orthographic)cam.span=nrClamp(cam.span-delta*2,1,2000);
                else cam.position=nrAdd(cam.position,nrScale(f,delta*2));
                nrCameraManualPose(s,&before,&cam);
            }
            return 0;
        }
        CHOICE("phase",phase,"down move up cancel");
        INT("button",button,0,2);
        if(s->promptDocument.modal||nrModalPointerOwns(s,x,y)){s->pointerActive=0;s->pressedHit=0;s->hoverHit=0;s->originalCamera.grabActive=0;if(!s->originalCamera.enabled)memset(&s->originalCamera,0,sizeof(s->originalCamera));return 0;}
        uint32_t currentHit=(x>=0&&y>=0&&x<s->width&&y<s->height)?c->cells[(int)y*s->width+(int)x].id:0;
        s->hoverHit=phase==3?0:currentHit;
        if(phase==0)s->pressedHit=s->promptDocument.modal?0:currentHit;
        if(phase>=2) {
            if(phase==2&&s->pointerActive&&s->pointerKind==0&&(x!=s->pointerX||y!=s->pointerY)&&!nrInputOwner(s)) {
                int at=s->promptFramed.enabled&&!s->firstPromptSource.enabled?nrPromptFramedHit(s,(int)x,(int)y):nrPromptHit(s,(int)x,(int)y);
                if(at>=0)s->promptDocument.caret=at;
            }
            if(s->promptDocument.anchor==s->promptDocument.caret)s->promptDocument.anchor=-1;
            s->pressedHit=0;
            s->pointerActive=0;s->originalCamera.grabActive=0;if(!s->originalCamera.enabled)memset(&s->originalCamera,0,sizeof(s->originalCamera));
            return 0;
        }
        if(phase==0) {
            if(x<0||y<0||x>=s->width||y>=s->height)return 0;
            if(s->promptDocument.modal) {
                s->pointerActive=0;
                return 0;
            }
            uint32_t cell=c->cells[(int)y*s->width+(int)x].id,id=cell&0xffff;
            uint32_t family=cell&0xff000000u;
            if(family==NR_ID_NOTIFICATION_ACTION) {
                int messageId=(int)((cell&0x00ffffffu)>>2),index=(int)(cell&3u);
                for(int i=0;i<NR_MESSAGES;i++)if(s->messages[i].used&&s->messages[i].id==messageId&&index<s->messages[i].actionCount)
                    return nrNotificationActivate(c,s,messageId,s->messages[i].actions[index].id);
                CHECK(0,"Notification action no longer exists");
            }
            /* Secondary drag pans before object activation. Modal, prompt,
             * source controls, inspector and reader retain input ownership. */
            int readerOwner=0;
            if(family==NR_ID_WINDOW){int wi=nrFindWindow(s,(int)id);readerOwner=wi>=0&&s->windows[wi].reader&&s->windows[wi].target&&s->selectedWindow==(int)id;}
            if(button==2&&family!=NR_ID_PROMPT&&family!=NR_ID_SOURCE_STAGE&&cell!=0x7fffffffu&&!readerOwner){
                s->pointerActive=1;s->pointerX=x;s->pointerY=y;
                s->pointerKind=2;s->pointerId=0;s->pointerAlt=alt;
                s->originalCamera.grabActive=0;
                if(!s->originalCamera.enabled)memset(&s->originalCamera,0,sizeof(s->originalCamera));
                return 0;
            }
            if(family==NR_ID_NODE&&button!=1) {
                CHECK(nrSelectNode(s,(int)id,900000),"Node no longer exists");
                return 0;
            }
            if(family==NR_ID_WINDOW_RETURN){int ai=nrFindWindow(s,(int)id);if(ai>=0&&s->atelierWindows[ai].enabled){nrAtelierWindowAction(s,ai,15);return 0;}CHECK(backgroundWindow(s,ai),"Source background action unavailable");return 0;}
            if(family==NR_ID_DOCK||family==NR_ID_CLOSE||family==NR_ID_MIN||family==NR_ID_MAX) {
                int wi=nrFindWindow(s,id);
                if(wi>=0) {
                    Window*w=&s->windows[wi];
                    if(family==NR_ID_DOCK&&!s->atelierWindows[wi].enabled&&s->windowApplication.enabled&&s->windowContent[wi].enabled&&s->windowContent[wi].visibilityTo>0&&s->windowContent[wi].visibilityTo!=.16){selectWindow(s,id);return 0;}
                    int sourceAction=family==NR_ID_DOCK?0:family==NR_ID_MAX?3:family==NR_ID_MIN?1:2;
                    if(nrWindowContentAction(s,wi,sourceAction)){if(!s->atelierWindows[wi].enabled||sourceAction==0||sourceAction==3)selectWindow(s,id);return 0;}
                    w->fromVisibility=nrWindowVisibility(w,s->timeUs);
                    w->target=family==NR_ID_DOCK||family==NR_ID_MAX;
                    w->atUs=s->timeUs;
                    if(family==NR_ID_MAX)w->maximized=!w->maximized;
                    selectWindow(s,id);
                }
                return 0;
            }
            if(family==NR_ID_WIDGET) {
                for(int i=0; i<NR_WIDGETS; i++)if(s->widgets[i].used&&s->widgets[i].id==(int)id&&s->widgets[i].enabled)s->widgets[i].selected=!s->widgets[i].selected;
                return 0;
            }
            if(family==NR_ID_SOURCE_STAGE){nrPointerRelease(s);return 0;}
            if(family==NR_ID_PROMPT) {
                if(nrInputOwner(s)||button!=0)return 0;
                int at=s->promptFramed.enabled&&!s->firstPromptSource.enabled?nrPromptFramedHit(s,(int)x,(int)y):nrPromptHit(s,(int)x,(int)y);
                if(s->promptFramed.enabled&&at<=-2)return nrPromptFramedActivate(c,s,at);
                if(at<0)return 0;
                if(!shift)s->promptDocument.anchor=at;
                else if(s->promptDocument.anchor<0)s->promptDocument.anchor=s->promptDocument.caret;
                nrPointerRelease(s);s->promptDocument.caret=at;s->pointerActive=1;s->pointerKind=0;
                s->pointerX=x;s->pointerY=y;
                return 0;
            }
            if(cell==0x7fffffffu)return 0;
            if(family==NR_ID_WINDOW){int wi=nrFindWindow(s,(int)id);if(wi>=0&&s->windows[wi].reader&&s->windows[wi].target&&s->selectedWindow==(int)id){nrPointerRelease(s);return 0;}}
            /* A new capture replaces the previous gesture; only a camera press picks again. */
            nrPointerRelease(s);
            s->pointerActive=1;
            s->pointerX=x;
            s->pointerY=y;
            s->pointerKind=family==NR_ID_WINDOW&&button==0?3:shift||button==2?2:1;
            s->pointerId=(int)id;
            s->pointerAlt=alt;
            if(family==NR_ID_WINDOW&&s->pointerKind==3)selectWindow(s,(int)id);
            if(s->pointerKind==1)nrOriginalCameraGrab(c,s,x,y);
            return 0;
        }
        if(!s->pointerActive||s->promptDocument.modal)return 0;
        if(s->pointerKind==0) {
            s->pointerX=x;s->pointerY=y;
            if(!nrInputOwner(s)) {
                int at=s->promptFramed.enabled&&!s->firstPromptSource.enabled?nrPromptFramedHit(s,(int)x,(int)y):nrPromptHit(s,(int)x,(int)y);
                if(at>=0)s->promptDocument.caret=at;
            }
            return 0;
        }
        double dx=x-s->pointerX,dy=y-s->pointerY;
        s->pointerX=x;
        s->pointerY=y;
        Camera cam=nrCameraAt(s);
        Vec3 r,u,f;
        nrBasis(&cam,&r,&u,&f);
        if(s->pointerKind==3) {
            int wi=nrFindWindow(s,s->pointerId);
            if(wi>=0) {
                Window*w=&s->windows[wi];
                if(s->pointerAlt) {
                    w->yaw=nrClamp(w->yaw+dx*2.4,-170,170);
                    w->pitch=nrClamp(w->pitch-dy*4.8,-89,89);
                }
                else {
                    double depth=nrDot(nrSub(w->position,cam.position),f);
                    double scale=cam.orthographic?cam.span/s->width:nrClamp(depth,1,2000)*nrSin(cam.fov*.5)/nrCos(cam.fov*.5)/(s->height*2);
                    w->position=nrAdd(w->position,nrAdd(nrScale(r,dx*2*scale),nrScale(u,-dy*4*scale)));
                }
            }
        }
        else if(s->cameraControls.configured)nrCameraControlInput(s,dx,dy,0,s->pointerKind==2);
        else if(s->originalCamera.enabled||s->pointerKind==1){nrOriginalCameraDrag(s,dx,dy,s->pointerKind==2);}
        else if(s->pointerKind==2) {
            if(nrCameraPathOwned(s))return 0;
            Camera before=cam;cam.position=nrAdd(cam.position,nrAdd(nrScale(r,-dx*.5),nrScale(u,dy*.6)));
            nrCameraManualPose(s,&before,&cam);
        }
        else if(s->flight.count) {
            s->flight.look.x+=dx*.65;
            s->flight.look.y=nrClamp(s->flight.look.y-dy*.65,-85,85);
        }
        else {
            s->camera.yaw+=dx*.65;
            s->camera.pitch=nrClamp(s->camera.pitch-dy*.65,-89,89);
        }
        return 0;
    }
    return reject(c,"Unknown or not-yet-implemented operation");
}

int nrApply(NrContext*c,State*s,const Json*j){
    int result=applyCommand(c,s,j);if(result<0)return result;
    if(!nrSyncTextIdentities(s)&&!nrProbeTextIdentities(c,s))return reject(c,"Persistent text identity capacity exhausted");return result;
}

#ifdef NR_BENCH_HOOKS
#include <time.h>
static double benchNow(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec*1e3+t.tv_nsec/1e6;}
#define BODY(c,expr) do{double benchStart=benchNow();expr;(c)->benchBodyMs+=benchNow()-benchStart;}while(0)
#else
#define BODY(c,expr) do{expr;}while(0)
#endif
/* ---------- the direct path (native/docs/TRANSACTIONS.md) ----------
 * Called by nrCommand only while the context is settled (internal.h). Returns NR_DIRECT_DECLINED, having written
 * nothing, for every op or State outside a plan's domain; otherwise the op's result, with the live State either
 * committed or, on a rejection, byte-identical to before. */
static int directPause(NrContext*c,State*s,const Json*j){
    PausePlan p;int r;BODY(c,r=planPause(c,s,j,&p));if(r<0)return -1;
    BODY(c,commitPause(s,&p));return 0;
}
static int directTime(NrContext*c,State*s,const Json*j){
    TimePlan p;int r;BODY(c,r=planTime(c,s,j,&p));if(r<0)return -1;
    if(s->paused)return 0;
    if(!timeDirectDomain(s,p.t))return NR_DIRECT_DECLINED;
    BODY(c,r=stepTime(c,s,&p,1));return r;
}
static int directWidget(NrContext*c,State*s,const Json*j){
    Widget*w=&c->widgetPlan;int slot,r;BODY(c,r=planWidget(c,s,j,w,&slot));if(r<0)return -1;
    /* nrValidState's only widget reader; no pipeline step reads a widget (TRANSACTIONS.md, "widget"). */
    if(!nrValidWidget(s,w))return reject(c,"State invariant rejected");
    BODY(c,s->widgets[slot]=*w);return 0;
}
/* pushUndo's only failure: the history arena cannot hold the pushed document (the later redo clears only shrink). */
static int draftHistoryFits(const State*s){
    const Prompt*p=&s->promptDocument;uint64_t total=0;
    for(int i=0;i<NR_PROMPT_HISTORY;i++)total+=(uint32_t)p->undoCount[i];
    return total-(uint32_t)p->undoCount[p->undoHead]+(uint32_t)p->count<=s->dynamicPrompt.historyCapacity;
}
static int directDraft(NrContext*c,State*s,const Json*j){
    ALLOW("text caret emitWeather");
    uint32_t*buf=NULL;int n,r;
    BODY(c,n=nrPromptDecodeCommand(s,j,nrField(j,0,"text"),&buf));
    CHECK(n>=0,"Invalid text or capacity");
    DraftPlan plan;BODY(c,r=planDraftTail(c,s,j,buf,n,&plan));if(r<0)return -1;
    /* Decided before the first write (TRANSACTIONS.md, "draft"): storage the commit would request, identities the
     * sync would allocate, and nrValidState's one new input, the document's scalars. */
    if(!draftHistoryFits(s))return NR_DIRECT_DECLINED;
    if(s->nextTextRunGeneration>=UINT32_MAX-1u||s->nextClusterIdentity>UINT32_MAX-(uint32_t)n-2u)return NR_DIRECT_DECLINED;
    if(!nrValidGlyphs(buf,n,(int)s->dynamicPrompt.capacity))return reject(c,"State invariant rejected");
    BODY(c,commitDraft(c,s,&plan));
    /* The pipeline's remaining work: the prompt's identity run, then its legacy mirror. */
    nrSyncPromptIdentity(s);nrPromptMirrorDocument(s);
    return 0;
}
/* No trigger and no style rule: nrValuesTick then writes nothing (its sync is a fixed point on a settled State). */
static int valuesTickIdle(const State*s){
    for(int i=0;i<NR_TRIGGERS;i++)if(s->triggers[i].used)return 0;
    for(int i=0;i<NR_STYLE_RULES;i++)if(s->styleRules[i].used)return 0;
    return 1;
}
/* `set` of an untyped, unbound value by literal (TRANSACTIONS.md, "set"): one double. nrBindValue checks the
 * number exactly as nrValidState's value clause (nrValueNumberValid) does, and writes nothing for an unbound value. */
static int directSet(NrContext*c,State*s,const Json*j){
    int i,expression,intent,r;BODY(c,r=planSetTarget(c,s,j,&i,&expression,&intent));if(r<0)return -1;
    if(expression>=0||s->typedValues[i].kind||s->values[i].bindingFamily||!valuesTickIdle(s))return NR_DIRECT_DECLINED;
    double v=s->values[i].value;
    NUM("value",v,-1e12,1e12);
    CHECK(nrBindValue(s,&s->values[i],v),"Bound value rejected");
    BODY(c,s->values[i].value=v);return 0;
}
/* Pointer, wheel and camera-input gestures (TRANSACTIONS.md, "pointer"). The domain predicate re-reads the
 * command's parameters (every parse precedes the handler's first write, so a malformed command is left to the
 * handler, which rejects it before writing) and accepts only the branches whose writes stay inside the gesture
 * records: the pointer fields, hover and pressed hits, the prompt caret and anchor, the camera, the flight, the
 * original camera and the camera controls. Branches that activate notifications, nodes, windows, widgets, source
 * stage components or the framed prompt, or that scroll a reader or the inspector, decline. */
static int gestureDomain(NrContext*c,const State*s,const Json*j,int wheel){
    double x=0,y=0,delta=0;int phase=0,shift=0,alt=0,button=0;
    if(!number(j,0,"x",&x,-2147483647.0/2,2147483647.0/2)||!number(j,0,"y",&y,-2147483647.0/4,2147483647.0/4)||!boolean(j,0,"shift",&shift)||!boolean(j,0,"alt",&alt))return 1;
    if(wheel){
        if(!number(j,0,"delta",&delta,-100,100))return 1;
        if(s->promptDocument.modal||nrModalPointerOwns(s,x,y))return 1;
        int reader=nrFindWindow(s,s->selectedWindow);
        if(reader>=0&&s->windows[reader].reader&&s->windows[reader].target&&nrField(j,0,"x")>=0&&nrField(j,0,"y")>=0&&x>=1&&y>=1&&x<(int)s->width-1&&y<(int)s->height-1)return 0;
        if(nrField(j,0,"y")>=0&&y>=c->promptTop)return 1;
        if(s->selection&&nrField(j,0,"x")>=0&&nrField(j,0,"y")>=0&&x>=(int)s->width-37&&x<(int)s->width-1&&y>=2&&y<c->promptTop-1)return 0;
        if(shift&&nrFindWindow(s,s->selectedWindow)>=0)return 0;
        return 1;
    }
    if(!choice(j,0,"phase",&phase,"down move up cancel")||!integer(j,0,"button",&button,0,2))return 1;
    if(s->promptDocument.modal||nrModalPointerOwns(s,x,y))return 1;
    if(phase>=2)return 1;
    if(phase==1)return !(s->pointerActive&&!s->promptDocument.modal&&s->pointerKind==3);
    if(x<0||y<0||x>=s->width||y>=s->height)return 1;
    uint32_t cell=c->cells[(int)y*s->width+(int)x].id,family=cell&0xff000000u;
    if(family==NR_ID_NOTIFICATION_ACTION||family==NR_ID_NODE||family==NR_ID_WINDOW_RETURN||family==NR_ID_DOCK||family==NR_ID_CLOSE||
       family==NR_ID_MIN||family==NR_ID_MAX||family==NR_ID_WIDGET||family==NR_ID_SOURCE_STAGE||family==NR_ID_PROMPT||family==NR_ID_WINDOW)return 0;
    return 1;
}
static int journalGesture(NrContext*c,State*s){
    Prompt*p=&s->promptDocument;
    return nrUndoSave(c,&s->camera,sizeof(s->camera))&&nrUndoSave(c,&s->flight,sizeof(s->flight))&&
        nrUndoSave(c,&s->originalCamera,sizeof(s->originalCamera))&&nrUndoSave(c,&s->cameraControls,sizeof(s->cameraControls))&&
        nrUndoSave(c,&s->pointerActive,(size_t)((char*)(&s->pointerY+1)-(char*)&s->pointerActive))&&
        nrUndoSave(c,&s->hoverHit,(size_t)((char*)(&s->pressedHit+1)-(char*)&s->hoverHit))&&
        nrUndoSave(c,&p->caret,(size_t)((char*)(&p->anchor+1)-(char*)&p->caret))&&
        nrUndoSave(c,&s->prompt.caret,(size_t)((char*)(&s->prompt.anchor+1)-(char*)&s->prompt.caret));
}
static int directGesture(NrContext*c,State*s,const Json*j,int wheel,int cameraInput){
    /* camera-input either rejects before writing or runs nrCameraControlInput, whose writes are the gesture records. */
    if(!cameraInput&&!gestureDomain(c,s,j,wheel))return NR_DIRECT_DECLINED;
    if(!journalGesture(c,s)){nrUndoRestore(c);return NR_DIRECT_DECLINED;}
    int caret=s->promptDocument.caret,anchor=s->promptDocument.anchor,r;
    /* The handler itself, in place: inside this domain its writes stay in the journaled records. */
    BODY(c,r=applyCommand(c,s,j));
    if(r<0){nrUndoRestore(c);return -1;}
    if(s->promptDocument.caret!=caret||s->promptDocument.anchor!=anchor)nrPromptMirrorCaret(s);
    if(!nrValidPointerCamera(s)){nrUndoRestore(c);return reject(c,"State invariant rejected");}
    return r;
}
/* Prompt `select`: INT bounds the caret and anchor to [0,count], nrValidState's only clauses on them; the legacy
 * mirror copies both (nrPromptMirrorCaret). */
static int directSelect(NrContext*c,State*s,const Json*j){
    SelectPlan p;int r;BODY(c,r=planPromptSelect(c,s,j,&p));if(r<0)return -1;
    BODY(c,commitPromptSelect(s,&p));nrPromptMirrorCaret(s);return 0;
}
/* `input` and `paste` (TRANSACTIONS.md, "draft"): nrInput's failing returns all precede its first write except
 * pushUndo's history request, which the plan checks; the rest is draft's pipeline remainder. */
static int directInput(NrContext*c,State*s,const Json*j,int paste){
    ALLOW("text");
    uint32_t *buf=NULL;int n;
    BODY(c,n=nrPromptDecodeCommand(s,j,nrField(j,0,"text"),&buf));
    CHECK(n>=0,"Invalid text or capacity");
    if(paste&&(nrInputOwner(s)||!n||(s->promptDocument.mode>=2&&!s->promptDocument.vimMode)))return 0;
    if(nrModalBlocking(s))return 0;
    const Prompt*p=&s->promptDocument;
    int start=p->caret,end=p->caret;
    if(p->anchor>=0){start=p->anchor<p->caret?p->anchor:p->caret;end=p->anchor>p->caret?p->anchor:p->caret;}
    uint64_t total=(uint64_t)p->count-(uint64_t)(end-start)+(uint64_t)n;
    /* nrInput rejects before writing: let it, for its own error and storage request. */
    if(!nrPromptAllowed(s,total)||total>s->dynamicPrompt.capacity){CHECK(nrInput(s,buf,n,paste?2:1),"Prompt capacity");return NR_DIRECT_DECLINED;}
    if(!draftHistoryFits(s))return NR_DIRECT_DECLINED;
    if(s->nextTextRunGeneration>=UINT32_MAX-1u||s->nextClusterIdentity>UINT32_MAX-(uint32_t)total-2u)return NR_DIRECT_DECLINED;
    if(!nrValidGlyphs(buf,n,(int)s->dynamicPrompt.capacity))return reject(c,"State invariant rejected");
    BODY(c,nrInput(s,buf,n,paste?2:1));
    nrSyncPromptIdentity(s);nrPromptMirrorDocument(s);
    return 0;
}
/* `node` updating an existing node: one record. Its id and used flag are unchanged, so the edge, graph-layout and
 * binding clauses that look nodes up by id still hold; nrValidNode is nrValidState's per-record node clause. A node
 * the command would create declines (the copy transaction places it). */
static int directNode(NrContext*c,State*s,const Json*j){
    Node*n=&c->nodePlan;int slot,created,r;BODY(c,r=planNode(c,s,j,n,&slot,&created));if(r<0)return -1;
    if(created)return NR_DIRECT_DECLINED;
    if(!nrValidNode(s,n))return reject(c,"State invariant rejected");
    BODY(c,s->nodes[slot]=*n);return 0;
}
int nrDirectApply(NrContext*c,const Json*j){
    State*s=&c->state;
    c->undo.count=c->undo.used=c->undo.journaled=0;
    if(s->schema!=NR_STATE_SCHEMA||c->checkingPending||c->executingPendingId)return NR_DIRECT_DECLINED;
    int op=nrField(j,0,"op");
    if(op<0||j->tokens[op].type!=J_STRING)return NR_DIRECT_DECLINED;
    if(nrEqual(j,op,"time"))return directTime(c,s,j);
    if(nrEqual(j,op,"pause"))return directPause(c,s,j);
    if(nrEqual(j,op,"widget"))return directWidget(c,s,j);
    if(nrEqual(j,op,"node"))return directNode(c,s,j);
    if(nrEqual(j,op,"draft"))return directDraft(c,s,j);
    if(nrEqual(j,op,"set"))return directSet(c,s,j);
    if(nrEqual(j,op,"pointer"))return directGesture(c,s,j,0,0);
    if(nrEqual(j,op,"wheel"))return directGesture(c,s,j,1,0);
    if(nrEqual(j,op,"camera-input"))return directGesture(c,s,j,0,1);
    if(nrEqual(j,op,"select")&&nrField(j,0,"id")<0)return directSelect(c,s,j);
    if(nrEqual(j,op,"input"))return directInput(c,s,j,0);
    if(nrEqual(j,op,"paste"))return directInput(c,s,j,1);
    return NR_DIRECT_DECLINED;
}
