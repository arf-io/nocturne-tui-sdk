#include "internal.h"
static double smooth(double value){value=nrClamp(value,0,1);return value*value*(3-2*value);}
int nrValidNovaOptics(const State*s){
    for(int i=0;i<(int)NR_MAX_PARTICLES;i++){
        const NovaOptics*n=&s->novaOptics[i];if(!n->profile)continue;
        if(n->profile!=1||s->schema<NR_STATE_SCHEMA_NOVA_OPTICS||!n->count||n->count>100000||n->index>=n->count||s->particles[i].state!=1||nrEffectAlgorithm(s->particles[i].effect)!=5||nrEffectProfile(s->particles[i].effect)!=1)return 0;
    }return 1;
}
int nrNovaAppearance(const State*s,int index,double out[4]){
    if(index<0||index>=(int)NR_MAX_PARTICLES)return 0;
    const NovaOptics*n=&s->novaOptics[index];const Particle*p=&s->particles[index];if(n->profile!=1||p->state!=1)return 0;
    double age=(s->step-p->bornStep+1)/120.0,life=p->lifeSteps/120.0;
    double latitude=1-2*(n->index+.5)/n->count,angle=n->index*137.50776405003785+n->seed*.0001*57.29577951308232;
    double sine=nrSin(2*angle+(9*latitude+n->seed)*57.29577951308232),clump=.3+.7*sine*sine;
    double a=nrHash(n->seed^((4*n->index+1)*0x9e3779b1u))/4294967296.0;
    out[0]=age*1000000;out[1]=clump;out[2]=smooth(age/.12)*smooth((1-age/life)*2)*clump;out[3]=25+260*age/life+60*a;return 1;
}
