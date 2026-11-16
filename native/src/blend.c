#include "internal.h"
static double lum(const double c[3]) {
    return .3*c[0]+.59*c[1]+.11*c[2];
}
static double min3(const double v[3]) {
    double a=v[0]<v[1]?v[0]:v[1];
    return a<v[2]?a:v[2];
}
static double max3(const double v[3]) {
    double a=v[0]>v[1]?v[0]:v[1];
    return a>v[2]?a:v[2];
}
static void setLum(double c[3],double l) {
    double d=l-lum(c);
    for(int i=0; i<3; i++)c[i]+=d;
    double n=min3(c),x=max3(c);
    l=lum(c);
    if(n<0)for(int i=0; i<3; i++)c[i]=l+(c[i]-l)*l/(l-n);
    if(x>1)for(int i=0; i<3; i++)c[i]=l+(c[i]-l)*(1-l)/(x-l);
}
static void setSat(double c[3],double sat) {
    double n=min3(c),x=max3(c);
    if(x>n)for(int i=0; i<3; i++)c[i]=(c[i]-n)*sat/(x-n);
    else for(int i=0; i<3; i++)c[i]=0;
}
static double channelBlend(double b,double s,int m) {
    switch(m) {
        case 1:return b*s;
        case 2:return b+s-b*s;
        case 3:return b<=.5?2*b*s:1-2*(1-b)*(1-s);
        case 4:return b<s?b:s;
        case 5:return b>s?b:s;
        case 6:return b==0?0:s>=1?1:nrClamp(b/(1-s),0,1);
        case 7:return b==1?1:s<=0?0:1-nrClamp((1-b)/s,0,1);
        case 8:return s<=.5?2*b*s:1-2*(1-b)*(1-s);
        case 9:if(s<=.5)return b-(1-2*s)*b*(1-b);
        return b+(2*s-1)*((b<=.25?((16*b-12)*b+4)*b:nrSqrt(b))-b);
        case 10:return nrAbs(b-s);
        case 11:return b+s-2*b*s;
        case 16:return nrClamp(b+s,0,1);
        case 17:return nrClamp(b-s,0,1);
        case 18:return s==0?1:nrClamp(b/s,0,1);
        case 19:return nrClamp(b+s-1,0,1);
        case 20:return nrClamp(b+2*s-1,0,1);
        case 21:return s<.5?channelBlend(b,2*s,7):channelBlend(b,2*s-1,6);
        case 22:return s<.5?(b<2*s?b:2*s):(b>2*s-1?b:2*s-1);
        case 23:return b+s<1?0:1;
        default:return s;
    }
}
int nrCompositeInSpace(uint32_t base,uint32_t source,uint32_t ba,uint32_t sa,uint32_t mode,uint32_t operation,uint32_t seed,uint32_t space,uint32_t*out) {
    if(!out||base>0xffffff||source>0xffffff||ba>65535||sa>65535||mode>27||operation>12||space>3)return -1;
    double b[3]= {
        ((base>>16)&255)/255.0,((base>>8)&255)/255.0,(base&255)/255.0
    },s[3]= {
        ((source>>16)&255)/255.0,((source>>8)&255)/255.0,(source&255)/255.0
    },bl[3],ab=ba/65535.0,as=sa/65535.0;
    if(mode==26) {
        as=nrRandom(seed,base,source)<as?1:0;
    }
    for(int i=0; i<3; i++)bl[i]=s[i];
    if(mode>=12&&mode<=15) {
        if(mode==12) {
            setSat(bl,max3(b)-min3(b));
            setLum(bl,lum(b));
        }
        if(mode==13) {
            for(int i=0; i<3; i++)bl[i]=b[i];
            setSat(bl,max3(s)-min3(s));
            setLum(bl,lum(b));
        }
        if(mode==14)setLum(bl,lum(b));
        if(mode==15) {
            for(int i=0; i<3; i++)bl[i]=b[i];
            setLum(bl,lum(s));
        }
    }
    else if(mode==24||mode==25) {
        int choose=mode==24?lum(s)<lum(b):lum(s)>lum(b);
        for(int i=0; i<3; i++)bl[i]=choose?s[i]:b[i];
    }
    else for(int i=0; i<3; i++)bl[i]=channelBlend(b[i],s[i],mode);
    double fa=1,fb=1-as;
    switch(operation) {
        case 1:fa=0;
        fb=0;
        break;
        case 2:fa=1;
        fb=0;
        break;
        case 3:fa=0;
        fb=1;
        break;
        case 4:fa=1-ab;
        fb=1;
        break;
        case 5:fa=ab;
        fb=0;
        break;
        case 6:fa=0;
        fb=as;
        break;
        case 7:fa=1-ab;
        fb=0;
        break;
        case 8:fa=0;
        fb=1-as;
        break;
        case 9:fa=ab;
        fb=1-as;
        break;
        case 10:fa=1-ab;
        fb=as;
        break;
        case 11:fa=1-ab;
        fb=1-as;
        break;
        case 12:fa=1;
        fb=1;
        break;
        default:break;
    }
    double alpha=as*fa+ab*fb,outColor[3];
    for(int i=0; i<3; i++) {
        double cs=(1-ab)*s[i]+ab*nrClamp(bl[i],0,1);
        double premul=as*fa*cs+ab*fb*b[i];
        outColor[i]=alpha>0?nrClamp(premul,0,1)/nrClamp(alpha,1e-12,1):0;
    }
    out[0]=nrRgb(outColor[0],outColor[1],outColor[2]);
    /* Blends retain encoded RGB algebra; only alpha interpolation changes
     * space. Additive composition retains its independent energy algebra. */
    if(space&&operation!=12&&alpha>0){
        double cs[3];for(int i=0;i<3;i++)cs[i]=(1-ab)*s[i]+ab*nrClamp(bl[i],0,1);
        out[0]=nrMixColorSpace(b,cs,as*fa/alpha,space);
    }
    out[1]=(uint32_t)(nrClamp(alpha,0,1)*65535+.5);
    return 0;
}
int nrComposite(uint32_t base,uint32_t source,uint32_t ba,uint32_t sa,uint32_t mode,uint32_t operation,uint32_t seed,uint32_t*out) {
    return nrCompositeInSpace(base,source,ba,sa,mode,operation,seed,0,out);
}
