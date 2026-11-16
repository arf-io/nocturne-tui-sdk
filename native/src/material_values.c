#include "internal.h"
int nrBindMaterialValue(State*s,const Value*v,double x){
    if(v->bindingId<0||v->bindingId>=NR_MATERIALS||!s->materials[v->bindingId].used)return 0;
    Material*m=&s->materials[v->bindingId];
    if(!strcmp(v->field,"hueStep")){if(x< -360||x>360)return 0;m->hueStep=x;return 1;}
    if(!strcmp(v->field,"spacing")){if(x< -100||x>100)return 0;m->spacing=x;return 1;}
    if(!strcmp(v->field,"scope")){if(x<0||x>1||x!=(int)x)return 0;m->scope=(int)x;return 1;}
    if(!strcmp(v->field,"blend")){if(x<0||x>27||x!=(int)x)return 0;m->blend=(int)x;return 1;}
    char base[32];memcpy(base,v->field,sizeof(base));const char*member="initial";
    char*dot=strrchr(base,'.');
    if(dot&&(strncmp(base,"channels.",9)||dot!=base+8)){member=v->field+(dot-base)+1;*dot=0;}
    Track*target=0;double lo=0,hi=1;
    if(!strcmp(base,"alpha"))target=&m->alpha;
    else if(!strcmp(base,"index")){target=&m->index;lo=-10000;hi=10000;}
    else{
        int channel=-1;
        if(!strcmp(base,"hue")){if(m->space==0)channel=2;else if(m->space==2||m->space==3)channel=0;}
        else if(!strcmp(base,"lightness")){if(m->space==0||m->space==1)channel=0;else if(m->space==2)channel=2;}
        else if(!strcmp(base,"brightness")){if(m->space==3)channel=2;}
        else if(!strncmp(base,"channels.",9)&&base[9]&&!base[10]){
            const char*names[]={"lch","lab","hsl","hsv","rgb","rgb","cmyk","i"};
            for(int k=0;names[m->space][k];k++)if(base[9]==names[m->space][k])channel=k;
        }
        if(channel<0)return 0;target=&m->channel[channel];
        if((m->space==0&&channel==2)||((m->space==2||m->space==3)&&channel==0))hi=360;
        if(m->space==0&&channel==1)hi=.5;
        if(m->space==1&&channel>0){lo=-.5;hi=.5;}
        if(m->space==7)hi=64;
    }
    Track q=*target;int matched=0;
#define NUM(name,field,low,high) if(!strcmp(member,name)){if(!(x>=low&&x<=high))return 0;q.field=x;matched=1;}
#define INT(name,field,low,high) if(!strcmp(member,name)){if(!(x>=low&&x<=high)||x!=(int)x)return 0;q.field=(int)x;matched=1;}
    NUM("initial",initial,lo,hi) NUM("min",min,lo,hi) NUM("max",max,lo,hi)
    NUM("rate",rate,-10000,10000) NUM("step",step,-10000,10000)
    INT("boundary",boundary,0,4) INT("easing",easing,0,6)
    if(!strcmp(member,"periodMs")){double us=x*1000;if(!(us>0&&us<=3600000000ull)||us!=(uint64_t)us)return 0;q.periodUs=(uint64_t)us;matched=1;}
    if(!strcmp(member,"seed")){if(!(x>=0&&x<=4294967295.0)||x!=(uint32_t)x)return 0;q.seed=(uint32_t)x;matched=1;}
    if(!matched||q.min>q.max||!q.periodUs)return 0;*target=q;return 1;
#undef NUM
#undef INT
}
