#include "internal.h"
#include "window_source_math.h"
static double minimum(double a,double b){return a<b?a:b;}
static double maximum(double a,double b){return a>b?a:b;}
static double angleOf(double x,double y){
    if(x==0&&y==0)return 0;double ax=nrAbs(x),ay=nrAbs(y),lo=0,hi=90;
    for(int i=0;i<36;i++){double m=(lo+hi)*.5;if(ax*nrSin(m)<ay*nrCos(m))lo=m;else hi=m;}
    double a=(lo+hi)*.5;if(x<0)a=180-a;if(y<0)a=-a;return a;
}
Vec3 nrWindowSourcePoint(const Window*w,double u,double v,double visibility,double*opacity){
    double p=nrClamp(visibility,0,1),q=1-p,W=w->width,H=w->height;
    double x=(u-.5)*W,y=(.5-v)*H,z=0,alpha=1;
    int a=nrEffectAlgorithm(w->effect),profile=nrEffectProfile(w->effect);
    if(!profile){
        switch(a) {
        case 0:alpha=p;break;
        case 1:{double scale=p+w->overshoot*nrWindowSourceSinPrecise(p*NR_PI*3)*nrWindowSourceSinPrecise(p*NR_PI);x*=scale;y*=scale;alpha=minimum(1,p*4);break;}
        case 2:x=x*(p+q*(1-v)*(1-v)*(1-v)*.18)+(w->anchorX-.5)*W*q*(.2+.8*v);y=y*p+(.5-w->anchorY)*H*q;z=nrWindowSourceSinPrecise(v*NR_PI)*q*W*.3;alpha=minimum(1,p*5);break;
        case 3:case 4:y=a==3?H*.5-v*H*p:-H*.5+(1-v)*H*p;z=nrWindowSourceSinPrecise(v*NR_PI*2)*q*2;alpha=minimum(1,p*8);break;
        case 5:case 6:x=a==5?-W*.5+u*W*p:W*.5-(1-u)*W*p;alpha=minimum(1,p*6);break;
        case 7:case 8:y=a==7?H*.5-v*H*p:-H*.5+(1-v)*H*p;alpha=minimum(1,p*6);break;
        case 9:x*=p;y*=p;break;
        case 10:case 11:case 12:case 13:x=(a==10||a==12)?-W*.5+u*W*p:W*.5-(1-u)*W*p;y=(a==10||a==11)?H*.5-v*H*p:-H*.5+(1-v)*H*p;break;
        case 14:alpha=p;break;
        case 15:{int fu=(int)(u*6),fv=(int)(v*4);double angle=(double)fu*71+(double)fv*113+w->seed;angle-=360*nrFloor(angle/360);angle=angle*NR_PI/180;x+=nrWindowSourceCos(angle)*q*w->scatter;y+=nrWindowSourceSinPrecise(angle)*q*w->scatter*.7;z=q*((fu+fv)%3-1)*12;alpha=p*p;break;}
        case 16:y*=p;z=nrWindowSourceSinPrecise(v*NR_PI*w->folds)*q*W*.13;alpha=minimum(1,p*5);break;
        case 17:{double angle=q*NR_PI*2,ox=x;x=(x*nrWindowSourceCos(angle)-y*nrWindowSourceSinPrecise(angle))*p;y=(ox*nrWindowSourceSinPrecise(angle)+y*nrWindowSourceCos(angle))*p;z=q*30;alpha=minimum(1,p*3);break;}
        case 18:{double angle=q*NR_PI,ox=x;x=(x*nrWindowSourceCos(angle)-y*nrWindowSourceSinPrecise(angle))*p;y=(ox*nrWindowSourceSinPrecise(angle)+y*nrWindowSourceCos(angle))*p+nrWindowSourceSinPrecise(q*NR_PI)*H;z=nrWindowSourceSinPrecise(q*NR_PI)*W;alpha=nrSqrt(p);break;}
        case 19:{double stripe=nrFloor(v*w->folds),mid=(stripe+.5)/w->folds;y=(.5-mid)*H+(mid-v)*H*p;z=nrWindowSourceSinPrecise(q*NR_PI/2)*(v-mid)*H*2;alpha=p;break;}
        case 20:{double angle=q*(u-.5)*NR_PI*4;x*=p;y=y*p+nrWindowSourceSinPrecise(angle)*H*q*.5;z=nrWindowSourceCos(angle)*q*W*.3;alpha=minimum(1,p*4);break;}
        default:x*=p;y*=p;alpha=p;break;
        }
    }else{
        if(p<=0){*opacity=0;return nrV(x,y,z);}
        double U=u*(W-1),V=v*(H-1),cx=(W-1)*.5,cy=(H-1)*.5;
        double nx=(U-cx)/maximum(1,cx),ny=(V-cy)/maximum(1,cy);x=U;y=V;
        switch(a){
        case 0:alpha=p;break;
        case 9:case 10:case 11:case 12:case 13:{double ax=a==10||a==12?0:a==9||a==11||a==13?W-1:cx,ay=a==9||a==10||a==11?0:a==12||a==13?H-1:cy;x=ax+(U-ax)*p;y=ay+(V-ay)*p;alpha=minimum(1,p*2);break;}
        case 14:if(nrSqrt(nx*nx+ny*ny)>1.4142135623730950488*p){*opacity=0;return nrV((u-.5)*W,(.5-v)*H,0);}break;
        case 3:case 4:{double edge=a==3?0:H-1;y=edge+(V-edge)*p;if(V>1&&p<.08){*opacity=0;return nrV((u-.5)*W,(.5-v)*H,0);}alpha=minimum(1,p*4);break;}
        case 5:case 6:case 7:case 8:
            if(a==5)x=U-W*q;if(a==6)x=U+W*q;if(a==7)y=V-H*q;if(a==8)y=V+H*q;
            if(x<0||x>=W||y<0||y>=H){*opacity=0;return nrV((u-.5)*W,(.5-v)*H,0);}break;
        case 1:{double scale=p+nrSin(p*180)*w->overshoot;x=cx+(U-cx)*scale;y=H-1+(V-H+1)*scale;alpha=minimum(1,p*3);break;}
        case 2:{double row=V/H,scale=nrPowPositive(p,.5+row*1.4);x=cx+(U-cx)*scale+nrSin(row*180)*q*w->bend;y=H-1+(V-H+1)*p;alpha=minimum(1,p*3);break;}
        case 15:{double block=nrFloor(U/3)+nrFloor(V/2)*101;block-=4294967296.0*nrFloor(block/4294967296.0);uint32_t index=(uint32_t)block;
            double r=nrHash(w->seed^((index+1u)*2654435769u))/4294967296.0;x=U+nx*q*q*w->scatter+(r-.5)*q*6;y=V+ny*q*q*w->scatter*.5+q*q*8;alpha=p;break;}
        case 16:x=cx+(U-cx)*p;y=V+nrSin(U*.5*180/NR_PI)*q*3;alpha=p;break;
        case 21:{double fold=nx<0?-1:1;x=cx+(U-cx)*nrCos(q*90);y=V+nrAbs(nx)*nrSin(q*180)*H*.35*fold;alpha=p;break;}
        case 22:case 25:{double angle=q*(a==22?540:180),scale=p*p,dx=U-cx,dy=(V-cy)*2;x=cx+(dx*nrCos(angle)-dy*nrSin(angle))*scale;y=cy+(dx*nrSin(angle)+dy*nrCos(angle))*scale*.5;alpha=p;break;}
        case 23:{double t=nrClamp(p*1.6-V/H*.6,0,1);x=cx+(U-cx)*t;y=cy+(V-cy)*t+nrSin((V*.55+q*4)*180/NR_PI)*q*3;alpha=t;break;}
        case 24:{double petal=.78+.22*nrCos(angleOf(nx,ny)*6),scale=nrClamp(p/petal,0,1);x=cx+(U-cx)*scale;y=cy+(V-cy)*scale;alpha=scale;break;}
        default:break;
        }
        x=(x-cx)*W/maximum(1,W-1);y=(cy-y)*H/maximum(1,H-1);
    }
    *opacity=alpha;return nrV(x,y,z);
}
