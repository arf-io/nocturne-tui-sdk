#include "../src/internal.h"
static int compile(const char*source,CharacterEffects*out){
    static Json json;char wrapped[4096];size_t length=strlen(source);
    if(length+13>sizeof(wrapped))return 0;
    memcpy(wrapped,"{\"effects\":",11);memcpy(wrapped+11,source,length);wrapped[11+length]='}';wrapped[12+length]=0;
    return nrParse(&json,wrapped,(int)length+12)&&nrCompileCharacterEffects(&json,nrField(&json,0,"effects"),out);
}
int nrTestCharacterEffects(void){
    CharacterEffects effects;double source[]={.25,.5,.75,.8},out[4];
    if(!compile("[{\"type\":\"invert\"},{\"type\":\"alpha\",\"value\":0.5}]",&effects)||nrApplyCharacterEffects(&effects,0,source,out))return 1;
    if(out[0]!=.75||out[1]!=.5||out[2]!=.25||out[3]!=.4)return 2;
    if(!compile("[{\"type\":\"invert\",\"where\":\"selected\"}]",&effects)||nrApplyCharacterEffects(&effects,0,source,out))return 3;
    if(memcmp(source,out,sizeof(source)))return 4;
    if(nrApplyCharacterEffects(&effects,1,source,out)||out[0]!=.75)return 5;
    if(!compile("[{\"type\":\"contrast\",\"value\":2},{\"type\":\"threshold\",\"value\":0.5}]",&effects)||nrApplyCharacterEffects(&effects,0,source,out))return 6;
    if(out[0]!=0||out[1]!=1||out[2]!=1||out[3]!=.8)return 7;
    if(!compile("[{\"type\":\"gamma\",\"value\":2},{\"type\":\"posterize\",\"value\":3}]",&effects)||nrApplyCharacterEffects(&effects,0,source,out))return 8;
    if(out[0]!=.5||out[1]!=.5||out[2]!=1||out[3]!=.8)return 9;
    const char*invalid[]={"[{\"type\":\"unknown\"}]","[{\"type\":\"gamma\",\"value\":0}]","[{\"type\":\"posterize\"}]","[{\"type\":\"posterize\",\"value\":2.5}]","[{\"type\":\"alpha\",\"where\":\"hover\"}]","[{\"type\":\"invert\",\"other\":1}]","[{\"type\":\"contrast\",\"value\":101}]","[{\"type\":\"hue\",\"value\":360001}]"};
    CharacterEffects before=effects;
    if(nrCompileCharacterEffects(NULL,0,&effects)||memcmp(&effects,&before,sizeof(before)))return 22;
    if(nrCompileCharacterEffects(NULL,-1,NULL))return 23;
    for(unsigned i=0;i<sizeof(invalid)/sizeof(invalid[0]);i++)if(compile(invalid[i],&effects)||memcmp(&effects,&before,sizeof(before)))return 10;
    if(!compile("[{\"type\":\"grayscale\"}]",&effects)||nrApplyCharacterEffects(&effects,0,source,out))return 11;
    if(out[0]!=out[1]||out[1]!=out[2]||out[3]!=.8)return 12;
    if(!compile("[{\"type\":\"exposure\",\"value\":0},{\"type\":\"hue\",\"value\":0}]",&effects)||nrApplyCharacterEffects(&effects,0,source,out))return 13;
    for(int k=0;k<4;k++)if(nrAbs(out[k]-source[k])>1e-6)return 14;
    double sentinel[]={.1,.2,.3,.4};memcpy(out,sentinel,sizeof(out));effects.entries[0].value=101;
    if(nrApplyCharacterEffects(&effects,0,source,out)!=-1||memcmp(out,sentinel,sizeof(out)))return 15;
    if(!compile("[{\"type\":\"gamma\",\"value\":2},{\"type\":\"invert\"}]",&effects)||nrApplyCharacterEffects(&effects,0,source,out))return 16;
    const double gammaFirst[]={.5,.2928932188134525,.1339745962155614,.8};
    for(int k=0;k<4;k++)if(nrAbs(out[k]-gammaFirst[k])>1e-6)return 17;
    if(!compile("[{\"type\":\"invert\"},{\"type\":\"gamma\",\"value\":2}]",&effects)||nrApplyCharacterEffects(&effects,0,source,out))return 18;
    const double invertFirst[]={.8660254037844386,.7071067811865475,.5,.8};
    for(int k=0;k<4;k++)if(nrAbs(out[k]-invertFirst[k])>1e-6)return 19;
    double inPlace[4];memcpy(inPlace,source,sizeof(source));
    if(nrApplyCharacterEffects(&effects,0,inPlace,inPlace))return 20;
    for(int k=0;k<4;k++)if(nrAbs(inPlace[k]-invertFirst[k])>1e-6)return 21;
    return 0;
}
