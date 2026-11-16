#include "internal.h"
static const char*types[]={"invert","alpha","grayscale","exposure","contrast","gamma","posterize","threshold","hue"};
int nrCompileCharacterEffects(const Json*j,int at,CharacterEffects*out){
    if(!out||(!j&&at>=0))return 0;
    CharacterEffects candidate;memset(&candidate,0,sizeof(candidate));
    if(at<0){*out=candidate;return 1;}
    if(j->tokens[at].type!=J_ARRAY||j->tokens[at].count>32)return 0;
    candidate.count=j->tokens[at].count;int child=at+1;
    for(int i=0;i<candidate.count;i++){
        if(!nrAllowed(j,child,"type value where"))return 0;
        CharacterEffect*e=&candidate.entries[i];e->type=-1;e->value=1;
        int type=nrField(j,child,"type"),where=nrField(j,child,"where"),value=nrField(j,child,"value");
        for(int k=0;k<9;k++)if(nrEqual(j,type,types[k]))e->type=k;
        if(e->type<0)return 0;
        if(where>=0){if(nrEqual(j,where,"all"))e->where=0;else if(nrEqual(j,where,"selected"))e->where=1;else if(nrEqual(j,where,"unselected"))e->where=2;else return 0;}
        if(value>=0&&!nrNumber(j,value,&e->value))return 0;
        double limit=e->type==8?360000:100;
        if(!(e->value>=-limit&&e->value<=limit)||
           (e->type==5&&e->value<=0)||
           (e->type==6&&(e->value<2||e->value!=(int)e->value)))return 0;
        child=j->tokens[child].next;
    }
    *out=candidate;return 1;
}
static double decode(double c){return c<=.04045?c/12.92:nrPowPositive((c+.055)/1.055,2.4);}
static double encode(double c){c=nrClamp(c,0,1);return c<=.0031308?12.92*c:1.055*nrPowPositive(c,1/2.4)-.055;}
int nrApplyCharacterEffects(const CharacterEffects*effects,int selected,const double*input,double*out){
    if(!effects||!input||!out||effects->count<0||effects->count>32)return -1;
    double color[4];
    for(int k=0;k<4;k++){if(!(input[k]>=0&&input[k]<=1))return -1;color[k]=input[k];}
    for(int i=0;i<effects->count;i++){
        const CharacterEffect*e=&effects->entries[i];double v=e->value,limit=e->type==8?360000:100;
        if(e->type<0||e->type>8||e->where<0||e->where>2||!(v>=-limit&&v<=limit)||
           (e->type==5&&v<=0)||(e->type==6&&(v<2||v!=(int)v)))return -1;
        if((e->where==1&&!selected)||(e->where==2&&selected))continue;
        if(e->type==1){color[3]*=nrClamp(v,0,1);continue;}
        if(e->type==8){double rotated[3];nrRotateColorHue(color,v,rotated);for(int k=0;k<3;k++)color[k]=rotated[k];continue;}
        double gray=0;if(e->type==2)gray=encode(.2126*decode(color[0])+.7152*decode(color[1])+.0722*decode(color[2]));
        for(int k=0;k<3;k++){
            double c=color[k];
            switch(e->type){
            case 0:c+=(1-2*c)*nrClamp(v,0,1);break;
            case 2:c+=(gray-c)*nrClamp(v,0,1);break;
            case 3:c=encode(decode(c)*nrPowPositive(2,v));break;
            case 4:c=nrClamp((c-.5)*v+.5,0,1);break;
            case 5:c=nrPowPositive(c,1/v);break;
            case 6:c=nrFloor(c*(v-1)+.5)/(v-1);break;
            case 7:c=c>=nrClamp(v,0,1)?1:0;break;
            }
            color[k]=c;
        }
    }
    for(int k=0;k<4;k++)out[k]=color[k];return 0;
}
