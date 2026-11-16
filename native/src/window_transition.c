#include "internal.h"
/* Pure geometry operators. Preset profile changes coefficients/optical geometry,
 * never document ownership, focus or lifecycle: those belong to one Window. */
static double minimum(double a,double b){return a<b?a:b;}
static double maximum(double a,double b){return a>b?a:b;}
static double polar(double x,double y) {
    double a=nrAbs(x),b=nrAbs(y),lo=0,hi=90;
    for(int i=0;i<24;i++){double m=(lo+hi)*.5;if(a*nrSin(m)<b*nrCos(m))lo=m;else hi=m;}
    double angle=(lo+hi)*.5;if(x<0)angle=180-angle;if(y<0)angle=-angle;return angle;
}
int nrWindowMask(const Window*w,double u,double v) {
    if(u<0||u>1||v<0||v>1)return 0;
    double x=nrAbs(u-.5)*2,y=nrAbs(v-.5)*2;
    switch(w->shape) {
    case 0:return 1;
    case 1:{double a=maximum(x-.78,0)/.22,b=maximum(y-.65,0)/.35;return a*a+b*b<=1;}
    case 2:return x*x+y*y<=1;
    case 3:return x<=1-y*.32;
    case 4:return x+y<=1;
    case 5:return x<.5||((x-.5)*2)*((x-.5)*2)+y*y<=1;
    case 6:return !((u<.075||u>.925)&&nrAbs(v-.5)<.14);
    case 7:return x*x*x*x+y*y*y*y<=1;
    case 8:return x*x+y*y<=.78+.22*nrCos(polar(u-.5,v-.5)*6);
    case 9:return v>.04+.04*nrSin(u*13*180/NR_PI)&&v<.94+.035*nrCos(u*15*180/NR_PI);
    case 10:{double X=(u-.5)*2,Y=(v-.5)*2;return X*X/.81+Y*Y/.49<=1||(X+.48)*(X+.48)+(Y+.28)*(Y+.28)<.3||(X-.34)*(X-.34)+(Y+.3)*(Y+.3)<.38;}
    case 11:{int inside=0;for(int i=0,j=w->polygonCount-1;i<w->polygonCount;j=i++){
        double ax=w->polygon[i][0],ay=w->polygon[i][1],bx=w->polygon[j][0],by=w->polygon[j][1];
        if((ay>v)!=(by>v)&&u<(bx-ax)*(v-ay)/(by-ay)+ax)inside=!inside;
    }return inside;}
    }
    return 0;
}
Vec3 nrWindowPoint(const Window*w,double u,double v,double visibility,double*opacity) {
    double p=nrClamp(visibility,0,1),q=1-p,W=w->width,H=w->height;
    double x=(u-.5)*W,y=(.5-v)*H,z=0,alpha=1;
    int a=nrEffectAlgorithm(w->effect),profile=nrEffectProfile(w->effect);
    if(p<=0){*opacity=0;return nrV(x,y,z);}
    if(p>=1){*opacity=1;return nrV(x,y,z);}
    if(profile) {
        double dx=(u-.5)*W,dy=(v-.5)*H;
        switch(a) {
        case 0:alpha=p;break;
        case 1:{double scale=p+nrSin(p*180)*w->overshoot;x=dx*scale;y=-H*.5+(1-v)*H*scale;alpha=minimum(1,p*3);break;}
        case 2:{double scale=nrPowPositive(p,.5+v*1.4);
            x=dx*scale+nrSin(v*180)*q*w->bend;y=-H*.5+(1-v)*H*p;alpha=minimum(1,p*3);break;}
        case 3:case 4:y=(a==3?H*.5-v*H*p:-H*.5+(1-v)*H*p);alpha=minimum(1,p*4);break;
        case 5:case 6:x=dx+(a==5?-1:1)*W*q;if(x< -W*.5||x>W*.5)alpha=0;break;
        case 7:case 8:y=-dy+(a==7?1:-1)*H*q;if(y< -H*.5||y>H*.5)alpha=0;break;
        case 9:x*=p;y*=p;alpha=minimum(1,p*2);break;
        case 10:case 11:case 12:case 13:{double ax=(a==10||a==12)?-W*.5:W*.5,ay=(a==10||a==11)?H*.5:-H*.5;x=ax+(x-ax)*p;y=ay+(y-ay)*p;alpha=minimum(1,p*2);break;}
        case 14:if(nrSqrt((2*u-1)*(2*u-1)+(2*v-1)*(2*v-1))>nrSqrt(2)*p)alpha=0;break;
        case 15:{uint32_t block=(uint32_t)(u*W/3)+(uint32_t)(v*H/2)*101;double r=nrRandom(w->seed,block,22);x=dx+(2*u-1)*q*q*w->scatter+(r-.5)*q*6;y=-dy-(2*v-1)*q*q*w->scatter*.5-q*q*8;alpha=p;break;}
        case 16:x*=p;y-=nrSin(u*W*.5*180/NR_PI)*q*3;alpha=p;break;
        case 21:x*=nrCos(q*90);y-=nrAbs(2*u-1)*nrSin(q*180)*H*.35*(u<.5?-1:1);alpha=p;break;
        case 22:case 25:{double angle=q*(a==22?540:180),scale=p*p;x=(dx*nrCos(angle)-dy*2*nrSin(angle))*scale;y=-(dx*nrSin(angle)+dy*2*nrCos(angle))*scale*.5;alpha=p;break;}
        case 23:{double t=nrClamp(p*1.6-v*.6,0,1);x=dx*t;y=-dy*t-nrSin((v*H*.55+q*4)*180/NR_PI)*q*3;alpha=t;break;}
        case 24:{double petal=.78+.22*nrCos(polar(2*u-1,2*v-1)*6),scale=nrClamp(p/petal,0,1);x*=scale;y*=scale;alpha=scale;break;}
        default:x*=p;y*=p;alpha=p;break;
        }
    } else {
        switch(a) {
        case 0:alpha=p;break;
        case 1:{double scale=p+w->overshoot*nrSin(p*540)*nrSin(p*180);x*=scale;y*=scale;alpha=minimum(1,p*4);break;}
        case 2:x=x*(p+q*(1-v)*(1-v)*(1-v)*.18)+(w->anchorX-.5)*W*q*(.2+.8*v);y=y*p+(.5-w->anchorY)*H*q;z=nrSin(v*180)*q*W*.3;alpha=minimum(1,p*5);break;
        case 3:case 4:y=a==3?H*.5-v*H*p:-H*.5+(1-v)*H*p;z=nrSin(v*360)*q*2;alpha=minimum(1,p*8);break;
        case 5:case 6:x=a==5?-W*.5+u*W*p:W*.5-(1-u)*W*p;alpha=minimum(1,p*6);break;
        case 7:case 8:y=a==7?H*.5-v*H*p:-H*.5+(1-v)*H*p;alpha=minimum(1,p*6);break;
        case 9:x*=p;y*=p;break;
        case 10:case 11:case 12:case 13:x=(a==10||a==12)?-W*.5+u*W*p:W*.5-(1-u)*W*p;y=(a==10||a==11)?H*.5-v*H*p:-H*.5+(1-v)*H*p;break;
        case 14:alpha=p;break;
        case 15:{int fu=(int)(u*6),fv=(int)(v*4);double angle=(fu*71+fv*113+w->seed)%360;x+=nrCos(angle)*q*w->scatter;y+=nrSin(angle)*q*w->scatter*.7;z=q*((fu+fv)%3-1)*12;alpha=p*p;break;}
        case 16:y*=p;z=nrSin(v*180*w->folds)*q*W*.13;alpha=minimum(1,p*5);break;
        case 17:{double angle=q*360,ox=x;x=(x*nrCos(angle)-y*nrSin(angle))*p;y=(ox*nrSin(angle)+y*nrCos(angle))*p;z=q*30;alpha=minimum(1,p*3);break;}
        case 18:{double angle=q*180,ox=x;x=(x*nrCos(angle)-y*nrSin(angle))*p;y=(ox*nrSin(angle)+y*nrCos(angle))*p+nrSin(q*180)*H;z=nrSin(q*180)*W;alpha=nrSqrt(p);break;}
        case 19:{double stripe=nrFloor(v*w->folds),mid=(stripe+.5)/w->folds;y=(.5-mid)*H+(mid-v)*H*p;z=nrSin(q*90)*(v-mid)*H*2;alpha=p;break;}
        case 20:{double angle=q*(u-.5)*720;x*=p;y=y*p+nrSin(angle)*H*q*.5;z=nrCos(angle)*q*W*.3;alpha=minimum(1,p*4);break;}
        default:x*=p;y*=p;alpha=p;break;
        }
    }
    *opacity=nrClamp(alpha,0,1);return nrV(x,y,z);
}
static Vec3 pointFor(const State*s,int slot,double u,double v,double visibility,double*opacity){
    return s->windowSourceGeometry[slot]?nrWindowSourcePoint(&s->windows[slot],u,v,visibility,opacity):nrWindowPoint(&s->windows[slot],u,v,visibility,opacity);
}
static Vec3 transform(const Window*w,Vec3 v) {
    Camera orientation={.yaw=w->yaw,.pitch=w->pitch,.roll=w->roll};Vec3 right,up,forward;
    nrBasis(&orientation,&right,&up,&forward);
    return nrAdd(w->position,nrAdd(nrScale(right,v.x),nrAdd(nrScale(up,v.y),nrScale(forward,-v.z))));
}
double nrWindowOpacity(const State*s,int slot){
    const Window*w=&s->windows[slot];double opacity=w->alpha;
    if(s->windowPresentation[slot].enabled){
        NrWindowSourcePresentationOptions options=s->windowPresentation[slot].options;
        /* Appearance rules may change alpha in render scratch only. */
        options.opacity=w->alpha;
        nrWindowSourcePresentationOpacity(&options,-w->position.z,&opacity);
    }
    return opacity;
}
void nrDrawWindowsGeometry(NrContext*c,const Projection*projection) {
    const State*s=nrView(c);
    for(int i=0;i<(int)NR_MAX_WINDOWS;i++) {
        const Window*w=&s->windows[i];if(!w->used||s->windowTextures.windows[i].width||s->windowContent[i].enabled)continue;
        double visibility=s->reducedMotion?w->target:nrWindowVisibility(w,s->timeUs);
        if(visibility<.001)continue;
        nrUseMaterial(c,w->material);
        double alpha;uint32_t color=nrPaint(s,w->material,s->timeUs,i,&alpha);
        uint32_t previousPattern=c->paintMaterialId;c->paintMaterialId=s->materialPatterns[w->material].used?(uint32_t)w->material+1:0;
        for(int row=0;row<w->meshRows;row++)for(int col=0;col<w->meshColumns;col++) {
            double u0=col/(double)w->meshColumns,u1=(col+1)/(double)w->meshColumns,v0=row/(double)w->meshRows,v1=(row+1)/(double)w->meshRows;
            if(!nrWindowMask(w,(u0+u1)*.5,(v0+v1)*.5))continue;
            double a[4];Vec3 p[4]={pointFor(s,i,u0,v0,visibility,&a[0]),pointFor(s,i,u1,v0,visibility,&a[1]),pointFor(s,i,u1,v1,visibility,&a[2]),pointFor(s,i,u0,v1,visibility,&a[3])};
            for(int j=0;j<4;j++)p[j]=transform(w,p[j]);
            double opacity=(a[0]+a[1]+a[2]+a[3])*.25*nrWindowOpacity(s,i)*alpha;
            if(opacity<.001)continue;
            nrTriangle(c,projection,(Triangle){p[0],p[1],p[2],color,opacity*.28});
            nrTriangle(c,projection,(Triangle){p[0],p[2],p[3],color,opacity*.28});
            if(row==0||!nrWindowMask(w,(u0+u1)*.5,v0-.5/w->meshRows))nrLine(c,projection,p[0],p[1],color,opacity*.8);
            if(col==0||!nrWindowMask(w,u0-.5/w->meshColumns,(v0+v1)*.5))nrLine(c,projection,p[0],p[3],color,opacity*.8);
            if(row==w->meshRows-1||!nrWindowMask(w,(u0+u1)*.5,v1+.5/w->meshRows))nrLine(c,projection,p[3],p[2],color,opacity*.8);
            if(col==w->meshColumns-1||!nrWindowMask(w,u1+.5/w->meshColumns,(v0+v1)*.5))nrLine(c,projection,p[1],p[2],color,opacity*.8);
        }
        c->paintMaterialId=previousPattern;
    }
}
int nrWindowSample(const NrContext*c,uint32_t id,uint32_t u,uint32_t v,uint32_t visibility,int32_t*words,uint32_t capacity) {
    if(!c||c->state.magic!=NR_MAGIC||!words||capacity<5||u>1000000||v>1000000||visibility>1000000||id>65535)return -1;
    int i=nrFindWindow(&c->state,(int)id);if(i<0)return -1;
    const Window*w=&c->state.windows[i];double alpha;Vec3 p=pointFor(&c->state,i,u/1e6,v/1e6,visibility/1e6,&alpha);QVec3 q=nrQuantize(p);
    words[0]=q.x;words[1]=q.y;words[2]=q.z;words[3]=(int32_t)(alpha*1e6+.5);words[4]=nrWindowMask(w,u/1e6,v/1e6);return 0;
}
