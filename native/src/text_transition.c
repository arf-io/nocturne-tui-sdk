#include "internal.h"
#include "window_source_math.h"
#include "window_palette_source.h"
static double textSin(int source,double degrees){return source?nrWindowSourceSin(degrees*NR_PI/180):nrSin(degrees);}
static double textCos(int source,double degrees){return source?nrWindowSourceCos(degrees*NR_PI/180):nrCos(degrees);}
static uint32_t alphabetAt(const TextRun*q,const uint32_t*tail,int index){return index<128?q->alphabet[index]:tail[index-128];}
static double rnd(uint32_t seed,uint32_t index){return nrHash(seed^((index+1)*0x9e3779b9u))/4294967296.0;}
static double min(double a,double b){return a<b?a:b;}
static double max(double a,double b){return a>b?a:b;}
static double ease(double p,int kind,double overshoot,int sourcePaint){
    p=nrClamp(p,0,1);
    if(kind==7)return p<.5?4*p*p*p:1-nrPowPositive(-2*p+2,3)*.5;
    if(kind==8){double q=p-1;return 1+(overshoot+1)*q*q*q+overshoot*q*q;}
    if(kind==9){double a=7.5625,b=2.75;if(p<1/b)return a*p*p;if(p<2/b){p-=1.5/b;return a*p*p+.75;}if(p<2.5/b){p-=2.25/b;return a*p*p+.9375;}p-=2.625/b;return a*p*p+.984375;}
    if(sourcePaint&&kind==5)return (1-nrWindowSourceCos(NR_PI*p))/2;
    return nrEase(p,kind);
}
static void timing(const TextRun*q,int i,double*delay,double*duration,int sourcePaint){
    int alg=nrEffectAlgorithm(q->effect),profile=nrEffectProfile(q->effect);
    int ordered=alg==5||alg==6||alg==14;
    *delay=q->delayUs/1000.0+(q->rank[i]/q->batchSize)*q->staggerUs/1000.0;
    if(!profile&&!ordered)*delay+=rnd(q->seed,i+171)*q->jitterUs/1000.0;
    if(profile){double variation=1+q->variation*(rnd(q->seed,i*7+3)*2-1);*duration=q->durationUs/1000.0*(sourcePaint?variation:max(.1,variation));}
    else *duration=q->durationUs/1000.0/(ordered?1:max(.1,1+(rnd(q->seed,i+227)-.5)*2*q->variation));
}
static TextPose canonicalModel(const TextRun*q,const uint32_t*tail,int i,uint64_t now,int reduced,int phaseModel){
    int sourcePaint=phaseModel==3,sourceModel=phaseModel==1||sourcePaint;
    TextPose out={q->x+q->column[i],q->y+q->row[i],1,0,q->text[i]};
    int alg=nrEffectAlgorithm(q->effect),profile=nrEffectProfile(q->effect),hide=q->phase;
    if(sourcePaint&&profile){out.x=q->x+i;out.y=q->y;}
    double age=(now>=q->startUs?now-q->startUs:0)/1000.0,delay,duration;timing(q,i,&delay,&duration,sourcePaint);
    double raw=age<delay?0:duration==0?1:nrClamp((age-delay)/duration,0,1),p=ease(raw,q->easing,q->overshoot,sourcePaint),away=hide?p:1-p;
    if(!profile)out.hue=i*q->hueSpread;
    if(sourcePaint&&(out.glyph<32||(out.glyph>=127&&out.glyph<=159)))out.glyph=profile||out.glyph==10?32:'?';
    if(q->local||reduced||alg==0){out.alpha=q->local?1:hide?0:1;return out;}
    if(raw>=1){out.alpha=hide?0:1;return out;}
    double r=rnd(q->seed,profile?i*7:i+811),b=rnd(q->seed,profile?i*7+1:i+1901),tx=out.x,ty=out.y;
    out.alpha=hide?1-p:p;
    if(profile){
        double visibility=hide?1-raw:raw,sign=hide?1:-1;
        out.alpha=visibility;
        switch(alg){
        case 1:out.alpha=nrEase(visibility,3);break;
        case 2:out.x+=(r-.5)*q->scatter*away+textSin(sourcePaint,raw*180)*(b-.5)*q->wind;out.y+=sign*q->distance*(.4+b*.6)*away;out.alpha=hide?min(1,(1-raw)*2):min(1,raw*3);break;
        case 3:if(age>=delay)out.glyph=alphabetAt(q,tail,(int)(rnd(q->seed^(uint32_t)i,(uint32_t)((age-delay)*q->scrambleHz/1000))*q->alphabetCount));out.alpha=hide?1-raw:min(1,raw*5);break;
        case 4:{uint32_t targetGlyph=hide?' ':out.glyph;int target=-1,n=q->alphabetCount;for(int k=0;k<n;k++)if(alphabetAt(q,tail,k)==targetGlyph){target=k;break;}if(target<0){target=n;n++;}
            int total=(int)(duration*q->scrambleHz/1000+.999999);if(total<1)total=1;int steps=(int)(max(0,age-delay)*q->scrambleHz/1000),start=((target-total)%n+n)%n,index=(start+(steps<total?steps:total))%n;
            out.glyph=index==q->alphabetCount?targetGlyph:alphabetAt(q,tail,index);out.y+=textSin(sourcePaint,max(0,age-delay)*q->scrambleHz*.18)*away*.35;out.alpha=hide?1-raw:min(1,raw*7);break;}
        case 5:case 6:out.x+=(alg==5?-1:1)*q->scatter*away;out.alpha=nrEase(visibility,3);break;
        case 18:case 16:out.y+=(alg==18?1:-1)*q->distance*away*(hide?-1:1);out.alpha=nrEase(visibility,3);break;
        case 7:out.x+=(hide?-1:1)*(q->count+q->scatter)*away;break;
        case 19:out.x=q->x+(q->count-1)*.5+((sourcePaint?i:q->column[i])-(q->count-1)*.5)*(1-away);break;
        case 9:{double a=r*360+away*q->cycles*360;out.x+=textCos(sourcePaint,a)*q->scatter*away;out.y+=textSin(sourcePaint,a)*q->distance*away;out.hue=q->hueSpread*away;break;}
        case 20:out.x+=textSin(sourcePaint,(i%3)*120+away*360)*q->scatter*away;out.y+=(i%2?1:-1)*q->distance*away;out.hue=(i%3-1)*q->hueSpread*away;break;
        case 21:out.y+=textSin(sourcePaint,i*.55*180/NR_PI-away*360)*q->distance*away;out.x+=q->wind*away;break;
        case 22:out.x-=q->scatter*away;out.y-=textSin(sourcePaint,raw*180)*q->distance*(.4+r*.6);out.hue=away*q->hueSpread;break;
        case 8:out.x+=textSin(sourcePaint,away*q->cycles*360)*q->scatter*away;out.y+=textCos(sourcePaint,away*q->cycles*360)*q->distance*away;break;
        case 23:out.x+=(i%2?1:-1)*q->scatter*away;out.y-=q->distance*textSin(sourcePaint,away*90);break;
        case 24:out.x+=(i%2?1:-1)*q->scatter*away*.4;out.y+=(i%2?1:-1)*q->distance*away;break;
        default:break;
        }
    } else {
        switch(alg){
        case 1:break;
        case 2:out.x+=(r-.5)*q->scatter*2*away+textSin(sourcePaint,raw*180)*q->wind*(b-.5);out.y-=q->distance*(.4+.6*b)*away;out.alpha=hide?1-p:min(1,p*2);break;
        case 16:{double travel=sourceModel?p:hide?p:1-p;out.x+=(r-.5)*q->scatter*travel+q->wind*travel*travel;out.y+=q->distance*(.45+.55*b)*travel*travel;out.alpha=sourceModel?1-p:hide?1-p:p;break;}
        case 3:{uint32_t tick=(uint32_t)(max(0,age-delay)*q->scrambleHz/1000);out.glyph=alphabetAt(q,tail,(int)(rnd(q->seed^((uint32_t)(i+1)*919u),tick)*q->alphabetCount));out.alpha=hide?1-p:min(1,p*4);break;}
        case 4:{int n=q->alphabetCount,start=(int)(r*n),target=0;uint32_t glyph=hide?' ':out.glyph;for(int k=0;k<n;k++)if(alphabetAt(q,tail,k)==glyph){target=k;break;}
            double steps=n*q->cycles+(target-start+n)%n,pos=start+raw*steps;out.glyph=alphabetAt(q,tail,(int)pos%n);double flip=.18+.82*nrAbs(textCos(sourcePaint,(pos-nrFloor(pos))*180));out.alpha=(hide?1-p:min(1,p*4))*(.65+.35*flip);break;}
        case 5:case 6:case 14:out.alpha=age<delay?(hide?1:0):(hide?0:1);break;
        case 7:out.x+=(hide?-1:1)*(q->width+q->scatter)*away;out.alpha=hide?1-p:min(1,p*3);break;
        case 8:{double a=r*360+raw*360*q->cycles;out.x+=textCos(sourcePaint,a)*q->scatter*away;out.y+=textSin(sourcePaint,a)*q->distance*away*.5;out.alpha=hide?1-p:min(1,p*2);break;}
        case 9:out.x+=(textCos(sourcePaint,r*360)*q->width*.7+q->width*.5-q->column[i])*away;out.y+=textSin(sourcePaint,r*360)*q->distance*away;out.alpha=hide?1-p:min(1,p*3);break;
        case 17:{double travel=sourceModel?p:hide?p:1-p;out.x+=(r-.5)*q->scatter*travel+textSin(sourcePaint,(travel*7+b*5)*180/NR_PI)*travel;out.y+=-q->distance*travel*(.3+.7*b)+q->distance*travel*travel*.8;static const uint32_t ash[]={0xb7,0x2219,0x2801,0x2808};if(travel>.3)out.glyph=ash[i%4];out.alpha=sourceModel?1-p:hide?1-p:p;break;}
        case 10:out.x+=(i%2?-1:1)*q->scatter*away;out.y+=(i%2?1:-1)*q->distance*away*.3;out.hue+=textSin(sourcePaint,raw*180)*80;break;
        case 11:out.x+=textSin(sourcePaint,raw*180*(2+q->cycles)+r*360)*q->scatter*away+q->wind*away;out.y+=(hide?1:-1)*q->distance*(.5+.5*b)*(hide?p*p:1-p);out.alpha=hide?1-p:min(1,p*2.5);break;
        case 12:out.x+=(i%2?1:-1)*2*away;if(raw<.18)out.glyph=0x2500;out.alpha=hide?1-p:min(1,p*5);break;
        case 13:out.y+=(hide?1:-1)*q->distance*away+textSin(sourcePaint,raw*540)*q->overshoot*q->distance*(1-raw);break;
        case 15:out.x+=((sourcePaint?i%q->width:q->column[i])<q->width*.5?-1:1)*q->scatter*away;out.alpha=hide?1-p:min(1,p*2);break;
        default:break;
        }
    }
    if(age<delay){if(profile){out.alpha=hide?1:0;if(hide){out.x=tx;out.y=ty;out.glyph=sourcePaint&&(q->text[i]<32||(q->text[i]>=127&&q->text[i]<=159))?32:q->text[i];if(sourcePaint)out.hue=0;}else if(alg==4)out.glyph=' ';}else if(!hide)out.alpha=0;}
    out.alpha=nrClamp(out.alpha,0,1);return out;
}
static TextPose canonical(const TextRun*q,const uint32_t*tail,int i,uint64_t now,int reduced){
    return canonicalModel(q,tail,i,now,reduced,0);
}
static TextPose applyRetarget(const TextRun*q,int i,TextPose p,int reduced,uint64_t now){
    if(q->retargeted&&!reduced&&!q->local){
        double age=now>=q->startUs?(double)(now-q->startUs):0,remaining=1-nrEase(q->totalUs?age/q->totalUs:1,3);
        p.x+=q->origin[i].dx*remaining;p.y+=q->origin[i].dy*remaining;p.alpha=nrClamp(p.alpha+q->origin[i].da*remaining,0,1);p.hue+=q->origin[i].dh*remaining;
        if(age==0)p.glyph=q->origin[i].glyph;
    }
    return p;
}
TextPose nrTextPose(const TextRun*q,const uint32_t*tail,int i,uint64_t now,int reduced){
    return applyRetarget(q,i,canonical(q,tail,i,now,reduced),reduced,now);
}
TextPose nrTextPoseWithModel(const TextRun*q,const uint32_t*tail,int i,uint64_t now,int reduced,int phaseModel){
    return applyRetarget(q,i,canonicalModel(q,tail,i,now,reduced,phaseModel),reduced,now);
}
int nrTextSupportsPhaseModel(int effect){
    int algorithm=nrEffectAlgorithm(effect);
    return nrEffectFamily(effect)==2&&!nrEffectProfile(effect)&&(algorithm==16||algorithm==17);
}
void nrPrepareTextWithModels(TextRun*q,const uint32_t*tail,int phaseModel,const TextRun*old,const uint32_t*oldTail,int oldPhaseModel,uint64_t now,uint32_t*next){
    int prefix=0,suffix=0;
    if(old){while(prefix<old->count&&prefix<q->count&&old->text[prefix]==q->text[prefix])prefix++;
        while(suffix<old->count-prefix&&suffix<q->count-prefix&&old->text[old->count-1-suffix]==q->text[q->count-1-suffix])suffix++;}
    /* Preserve identity only for complete clusters in both old and new source. */
    if(old){
        uint32_t a[NR_MAX_TEXT+1],b[NR_MAX_TEXT+1];
        unsigned char oldBoundary[NR_MAX_TEXT+1]={0},newBoundary[NR_MAX_TEXT+1]={0};
        int an=nrGraphemeBreaks(old->text,(uint32_t)old->count,a,NR_MAX_TEXT+1);
        int bn=nrGraphemeBreaks(q->text,(uint32_t)q->count,b,NR_MAX_TEXT+1);
        for(int k=0;k<an;k++)oldBoundary[a[k]]=1;
        for(int k=0;k<bn;k++)newBoundary[b[k]]=1;
        while(prefix&&(!oldBoundary[prefix]||!newBoundary[prefix]))prefix--;
        while(suffix&&(!oldBoundary[old->count-suffix]||!newBoundary[q->count-suffix]))suffix--;
    }
    q->retargeted=0;q->startUs=now;q->totalUs=0;int row=0,col=0;
    for(int i=0;i<q->count;i++) {
        if(col>=q->width){row++;col=0;}q->column[i]=(uint16_t)col;q->row[i]=(uint16_t)row;
        if(q->text[i]==10){row++;col=0;}else col++;
        int rank=i;
        if(q->randomOrder){rank=0;double key=rnd(q->seed,i);for(int k=0;k<q->count;k++){double other=rnd(q->seed,k);if(other<key||(other==key&&k<i))rank++;}}
        else if(nrEffectAlgorithm(q->effect)==6||(phaseModel==3&&nrEffectProfile(q->effect)&&nrEffectAlgorithm(q->effect)==22&&q->reverseOrder))rank=q->count-1-rank;
        if(q->reverseOrder&&!(phaseModel==3&&nrEffectProfile(q->effect)&&nrEffectAlgorithm(q->effect)==22))rank=q->count-1-rank;q->rank[i]=(uint16_t)rank;
        memset(&q->origin[i],0,sizeof(TextOrigin));int from=i<prefix?i:i>=q->count-suffix?old->count-(q->count-i):-1;
        q->origin[i].identity=from>=0?old->origin[from].identity:++(*next);
        double d,t;timing(q,i,&d,&t,phaseModel==3);uint64_t end=(uint64_t)((d+t)*1000+.999999);if(end>q->totalUs)q->totalUs=end;
        if(from>=0){TextPose previous=nrTextPoseWithModel(old,oldTail,from,now,0,oldPhaseModel),base=canonicalModel(q,tail,i,now,0,phaseModel);
            q->origin[i].dx=previous.x-base.x;q->origin[i].dy=previous.y-base.y;q->origin[i].da=previous.alpha-base.alpha;q->origin[i].dh=previous.hue-base.hue;q->origin[i].glyph=previous.glyph;
        }else q->origin[i].glyph=q->text[i];
    }
    q->retargeted=old!=NULL;
}
void nrPrepareText(TextRun*q,const uint32_t*tail,const TextRun*old,const uint32_t*oldTail,uint64_t now,uint32_t*next){
    nrPrepareTextWithModels(q,tail,0,old,oldTail,0,now,next);
}
int nrTextTrailPose(const State*s,int slot,int index,int trail,TextPose*out){
    if(!out||slot<0||slot>=NR_TEXTS||index<0||trail<0)return 0;const TextRun*q=&s->text[slot];
    if(!q->used||index>=q->count||(q->text[index]==10&&s->textPhaseModel[slot]!=3)||trail>=q->trailLength||s->reducedMotion||q->local)return 0;
    int algorithm=nrEffectAlgorithm(q->effect),profile=nrEffectProfile(q->effect);
    if(algorithm!=2&&algorithm!=22&&algorithm!=9&&algorithm!=8&&algorithm!=20)return 0;
    double delay,duration;timing(q,index,&delay,&duration,s->textPhaseModel[slot]==3);double age=(s->timeUs>=q->startUs?s->timeUs-q->startUs:0)/1000.0;
    double raw=age<delay?0:duration==0?1:nrClamp((age-delay)/duration,0,1);
    if(profile&&raw>=1)return 0;
    double progress=profile?ease(raw,q->easing,q->overshoot,0):raw,away=q->phase?progress:1-progress;
    TextPose pose=nrTextPoseWithModel(q,s->textAlphabetTail[slot],index,s->timeUs,s->reducedMotion,(int)s->textPhaseModel[slot]);int ordinal=trail+1;
    pose.x-=q->wind*ordinal*.15;pose.y-=(q->phase?1:-1)*ordinal*.45;
    pose.alpha=nrClamp(pose.alpha*away/(ordinal+2),0,1);*out=pose;return 1;
}
static void visibleTextGlyph(NrContext*c,double x,double y,uint32_t glyph,uint32_t color,double alpha,uint32_t index,int material){
    x=nrFloor(x+.5);y=nrFloor(y+.5);
    const State*s=nrView(c);
    if(x>=0&&x<s->width&&y>=0&&y<s->height){
        if(material>=0&&material<NR_MATERIALS&&s->materialPatterns[material].used){double ignored;color=nrPaintAt(s,material,s->timeUs,(int32_t)x*256,(int32_t)y*256,index,&ignored);}
        nrIndexedGlyph(c,(int)x,(int)y,glyph,color,alpha,0,index);
    }
}
static uint32_t sourceMix(uint32_t a,uint32_t b,double amount){
    amount=nrClamp(amount,0,1);uint32_t out=0;
    for(int k=0;k<=16;k+=8){double av=(a>>k)&255,bv=(b>>k)&255;out|=(uint32_t)nrFloor(av*(1-amount)+bv*amount+.5)<<k;}return out;
}
static void sourceTextGlyph(NrContext*c,const TextRun*q,int index,TextPose pose,int trail){
    const State*s=nrView(c);
    if(nrEffectProfile(q->effect)){int wrap=(int)s->width-10;if(wrap<10)wrap=10;pose.x=pose.x-index+index%wrap;pose.y+=(index/wrap)*3;if(pose.y<5||pose.y>=s->height-8)return;}
    double x=nrFloor(pose.x),y=nrFloor(pose.y);
    if(x<0||y<0||x>=s->width||y>=s->height||!nrInClip(c,(int)x,(int)y))return;
    const Material*m=&s->materials[q->material];double alpha;uint32_t color;
    if(!m->used){
        nrWindowPaletteSourceTextInk(.83,.1,index*13+(trail?0:s->timeUs*12/1000000.0)+pose.hue,&color);alpha=1;
    }else if(m->space==0&&!m->gradientCount&&!s->materialPatterns[q->material].used){
        double n=m->scope?index:0,l=nrTrack(&m->channel[0],s->timeUs,n),chroma=nrTrack(&m->channel[1],s->timeUs,n);
        double hue=(trail?0:nrTrack(&m->channel[2],s->timeUs,n))+m->hueStep*n+pose.hue;
        /* The original converter supports chroma up to .4; native materials
         * accept .5, whose source-paint extension saturates at this boundary. */
        nrWindowPaletteSourceTextInk(l,nrClamp(chroma,0,.4),hue,&color);
        alpha=nrClamp(nrTrack(&m->alpha,s->timeUs,n),0,1);
    }else color=nrHueShift(nrPaint(s,q->material,s->timeUs,index,&alpha),pose.hue);
    size_t at=(size_t)y*s->width+(size_t)x;NrCell*cell=&c->cells[at];
    uint32_t bg=cell->background;if(cell->glyph==0x2580||cell->glyph==0x2584||cell->glyph==0x258c||cell->glyph==0x2590)bg=sourceMix(cell->foreground,cell->background,.5);
    cell->glyph=pose.glyph;cell->foreground=sourceMix(bg,color,pose.alpha*alpha);cell->background=bg;cell->id=0;
    c->characterIndices[at]=(uint32_t)index;c->characterOwners[at]=c->characterOwner;
}
void nrDrawTextTransitions(NrContext*c){
    const State*s=nrView(c);
    uint32_t previousOwner=c->characterOwner;
    for(int t=0;t<NR_TEXTS;t++){const TextRun*q=&s->text[t];if(!q->used)continue;nrUseMaterial(c,q->material);
        c->characterOwner=(4u<<16)|(uint32_t)q->id;
        for(int i=0;i<q->count;i++){if(q->text[i]==10&&s->textPhaseModel[t]!=3)continue;TextPose p=nrTextPoseWithModel(q,s->textAlphabetTail[t],i,s->timeUs,s->reducedMotion,(int)s->textPhaseModel[t]);
            if(s->textPhaseModel[t]==3){
                if(nrEffectProfile(q->effect))for(int trail=0;trail<q->trailLength;trail++){TextPose tail;if(nrTextTrailPose(s,t,i,trail,&tail)){tail.glyph=0xb7;sourceTextGlyph(c,q,i,tail,1);}}
                if(p.alpha>0)sourceTextGlyph(c,q,i,p,0);continue;
            }
            if(p.alpha<=0)continue;
            double alpha;uint32_t color=nrHueShift(nrPaint(s,q->material,s->timeUs,i,&alpha),p.hue);
            for(int trail=q->trailLength-1;trail>=0;trail--){TextPose tail;
                if(nrTextTrailPose(s,t,i,trail,&tail))visibleTextGlyph(c,tail.x,tail.y,tail.glyph,color,tail.alpha*alpha,(uint32_t)i,q->material);
            }
            visibleTextGlyph(c,p.x,p.y,p.glyph,color,p.alpha*alpha,(uint32_t)i,q->material);
        }
    }
    c->characterOwner=previousOwner;
}
int nrTextTrailSample(const NrContext*c,uint32_t id,uint32_t index,uint32_t trail,int32_t*out,uint32_t capacity){
    if(!c||c->state.magic!=NR_MAGIC||!out||capacity<8||id<1||id>65535||index>=NR_MAX_TEXT||trail>=8||(uintptr_t)out%_Alignof(int32_t))return -1;
    uintptr_t first=(uintptr_t)out,context=(uintptr_t)c;if(first>UINTPTR_MAX-8*sizeof(*out)||(first<context+sizeof(*c)&&context<first+8*sizeof(*out)))return -1;
    for(int slot=0;slot<NR_TEXTS;slot++){const TextRun*q=&c->state.text[slot];if(!q->used||(uint32_t)q->id!=id)continue;TextPose pose;
        if(!nrTextTrailPose(&c->state,slot,(int)index,(int)trail,&pose))return -1;QVec3 p=nrQuantize(nrV(pose.x,pose.y,0));
        int32_t result[8]={(int32_t)q->origin[index].identity,(int32_t)pose.glyph,(int32_t)trail+1,p.x,p.y,(int32_t)(pose.alpha*1e6+.5),(int32_t)(pose.hue*1000),c->state.timeUs-q->startUs>=q->totalUs};
        memcpy(out,result,sizeof(result));return 0;
    }return -1;
}

int nrTextSample(const NrContext*c,uint32_t id,uint32_t index,int32_t*out,uint32_t capacity){
    if(!c||c->state.magic!=NR_MAGIC||!out||capacity<8)return -1;
    for(int i=0;i<NR_TEXTS;i++){const TextRun*q=&c->state.text[i];if(!q->used||q->id!=(int)id)continue;if(index>=(uint32_t)q->count)return -1;
        TextPose p=nrTextPoseWithModel(q,c->state.textAlphabetTail[i],(int)index,c->state.timeUs,c->state.reducedMotion,(int)c->state.textPhaseModel[i]);QVec3 pos=nrQuantize(nrV(p.x,p.y,0));
        out[0]=(int32_t)p.glyph;out[1]=(int32_t)q->text[index];out[2]=(int32_t)q->origin[index].identity;out[3]=pos.x;out[4]=pos.y;out[5]=(int32_t)(p.alpha*1e6+.5);out[6]=(int32_t)(p.hue*1000);out[7]=c->state.timeUs-q->startUs>=q->totalUs;return 0;
    }return -1;
}

int nrTextClusterSample(const NrContext*c,uint32_t id,uint32_t index,int32_t*out,uint32_t capacity){
    if(!c||c->state.magic!=NR_MAGIC||!out||capacity<8||
       (uintptr_t)out%_Alignof(int32_t))return -1;
    uintptr_t first=(uintptr_t)out,context=(uintptr_t)c;
    if(first>UINTPTR_MAX-8*sizeof(*out)||
       (first<context+sizeof(*c)&&context<first+8*sizeof(*out)))return -1;
    for(int i=0;i<NR_TEXTS;i++){
        const TextRun*q=&c->state.text[i];if(!q->used||(uint32_t)q->id!=id)continue;
        uint32_t breaks[NR_MAX_TEXT+1];int n=nrGraphemeBreaks(q->text,(uint32_t)q->count,breaks,NR_MAX_TEXT+1);
        if(n<1||index>=(uint32_t)(n-1))return -1;
        uint32_t start=breaks[index],end=breaks[index+1];
        TextPose p=nrTextPoseWithModel(q,c->state.textAlphabetTail[i],(int)start,c->state.timeUs,c->state.reducedMotion,(int)c->state.textPhaseModel[i]);
        QVec3 pos=nrQuantize(nrV(p.x,p.y,0));
        int32_t result[8]={(int32_t)q->origin[start].identity,(int32_t)start,(int32_t)end,
            pos.x,pos.y,(int32_t)(p.alpha*1e6+.5),(int32_t)(p.hue*1000),
            c->state.timeUs-q->startUs>=q->totalUs};
        memcpy(out,result,sizeof(result));return 0;
    }return -1;
}
