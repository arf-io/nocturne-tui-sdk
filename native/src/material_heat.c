#include "internal.h"
/* Owned material energy stays independent of legacy appearance-only p->heat. */
static int reject(NrContext*c,const char*why){size_t n=strlen(why);if(n>255)n=255;memcpy(c->error,why,n);c->error[n]=0;return -1;}
static int number(const Json*j,const char*key,double*out,double low,double high,int required){int field=nrField(j,0,key);if(field<0)return !required;return nrNumber(j,field,out)&&*out>=low&&*out<=high;}
int nrMaterialHeatCommand(NrContext*c,State*s,const Json*j){
    int remove=nrEqual(j,nrField(j,0,"op"),"remove-material-thermal");double id=0;
    if(s->schema<NR_STATE_SCHEMA_MATERIAL_HEAT||!nrAllowed(j,0,remove?"op id":"op id temperature capacity contactFraction conductance")||!number(j,"id",&id,0,NR_MATERIALS-1,1)||id!=(int)id||!s->materials[(int)id].used)return reject(c,"Invalid thermal material target");
    if(remove){memset(&s->materialHeat[(int)id],0,sizeof(HeatReservoir));return 0;}
    HeatReservoir value={.id=(uint32_t)id+1,.contactFraction=1};
    if(!number(j,"temperature",&value.temperature,0,10000,1)||!number(j,"capacity",&value.capacity,.000001,1000000,1)||!number(j,"contactFraction",&value.contactFraction,0,1,0)||!number(j,"conductance",&value.conductance,0,1000000,0))return reject(c,"Invalid thermal material reservoir");
    s->materialHeat[(int)id]=value;return 0;
}
static HeatReservoir* carrier(State*s,int family,int index){return family==0?&s->particleHeat[index]:family==1?&s->depositHeat[index]:&s->aggregateHeat[index];}
void nrHeatRelease(State*s,int family,int index){if(!family)memset(&s->novaOptics[index],0,sizeof(NovaOptics));HeatReservoir*r=carrier(s,family,index);if(r->id)s->materialHeatLedger.exported+=r->capacity*r->temperature;memset(r,0,sizeof(*r));if(family==2)memset(&s->aggregateProvenance[index],0,sizeof(AggregateProvenance));}
void nrHeatSpawn(State*s,int slot){
    HeatReservoir*r=&s->particleHeat[slot];memset(r,0,sizeof(*r));int material=s->particles[slot].material;
    if(material>=0&&material<NR_MATERIALS&&s->materialHeat[material].id){*r=s->materialHeat[material];r->id=s->particles[slot].id;r->generation=0;s->materialHeatLedger.initial+=r->capacity*r->temperature;}
}
void nrHeatDeposit(State*s,int slot,int family,int destination){
    HeatReservoir*r=&s->particleHeat[slot],*target=carrier(s,family,destination);if(!r->id)return;
    if(family==2&&target->id){double capacity=target->capacity+r->capacity;target->temperature=(target->capacity*target->temperature+r->capacity*r->temperature)/capacity;target->capacity=capacity;target->conductance+=r->conductance;}
    else{*target=*r;target->id=family==2?1:s->deposits[destination].id;target->generation=s->geometry.meshGeneration;}
    if(family==2)target->contactFraction=0;memset(r,0,sizeof(*r));
}
void nrHeatReentrain(State*s,int source,int slot){s->particleHeat[slot]=s->depositHeat[source];s->particleHeat[slot].generation=0;memset(&s->depositHeat[source],0,sizeof(HeatReservoir));}
void nrHeatMeshChanged(State*s,int append){if(append){for(int i=0;i<NR_DEPOSITS;i++)if(s->depositHeat[i].id&&s->depositHeat[i].generation==s->geometry.meshGeneration)s->depositHeat[i].generation=s->geometry.meshGeneration+1;for(int i=0;i<NR_TILES;i++)if(s->aggregateHeat[i].id&&s->aggregateHeat[i].generation==s->geometry.meshGeneration)s->aggregateHeat[i].generation=s->geometry.meshGeneration+1;}}
static void journal(State*s,int triangle,double energy){
    if(energy>=0){s->materialHeatLedger.transferred+=energy;s->thermalTransfers[triangle].incoming+=energy;}
    else{s->materialHeatLedger.imported-=energy;s->thermalTransfers[triangle].outgoing-=energy;}
}
int nrHeatContact(State*s,int slot,const GeometryHit*hit){
    HeatReservoir*r=&s->particleHeat[slot];if(!r->id||!r->contactFraction||!hit||hit->triangleIndex>=s->meshCount||!s->thermalCells[hit->triangleIndex].used)return 1;
    int i=(int)hit->triangleIndex;double thermal[4];nrThermalCell(s,i,thermal);if(!(thermal[0]>=0&&thermal[0]<=10000))return 0;
    double capacity=s->thermalCells[i].capacity,energy=r->contactFraction*(r->temperature-thermal[0])*r->capacity*capacity/(r->capacity+capacity);
    r->temperature-=energy/r->capacity;s->thermalCells[i].temperature=thermal[0]+energy/capacity;s->thermalCells[i].atUs=s->timeUs;s->thermalCells[i].appliedEnergy=thermal[2];s->thermalCells[i].environmentEnergy=thermal[3];journal(s,i,energy);return 1;
}
static int attached(const State*s,int family,int index){
    const HeatReservoir*r=family==1?&s->depositHeat[index]:&s->aggregateHeat[index];
    if(!r->id||!r->conductance||r->generation!=s->geometry.meshGeneration)return -1;
    uint32_t triangle=family==1?s->geometry.depositContacts[index].triangleIndex:s->geometry.tileSurfaces[index].triangleIndex;
    int used=family==1?s->geometry.depositContacts[index].used:s->geometry.tileSurfaces[index].surfaceId!=0;
    return used&&triangle<(uint32_t)s->meshCount&&s->thermalCells[triangle].used?(int)triangle:-1;
}
int nrHeatTick(State*s){
    double weight[NR_MESH]={0},weightedTemperature[NR_MESH]={0},thermal[NR_MESH][4],nextTemperature[NR_MESH];
    for(int family=1;family<=2;family++)for(int n=0;n<(family==1?NR_DEPOSITS:NR_TILES);n++){int triangle=attached(s,family,n);if(triangle<0)continue;HeatReservoir*r=carrier(s,family,n);double g=r->conductance/120,w=g/(1+g/r->capacity);weight[triangle]+=w;weightedTemperature[triangle]+=w*r->temperature;}
    for(int i=0;i<s->meshCount;i++)if(weight[i]){nrThermalCell(s,i,thermal[i]);if(!(thermal[i][0]>=0&&thermal[i][0]<=10000))return 0;nextTemperature[i]=(s->thermalCells[i].capacity*thermal[i][0]+weightedTemperature[i])/(s->thermalCells[i].capacity+weight[i]);}
    for(int family=1;family<=2;family++)for(int n=0;n<(family==1?NR_DEPOSITS:NR_TILES);n++){int triangle=attached(s,family,n);if(triangle<0)continue;HeatReservoir*r=carrier(s,family,n);double g=r->conductance/120,next=(r->capacity*r->temperature+g*nextTemperature[triangle])/(r->capacity+g),energy=r->capacity*(r->temperature-next);r->temperature=next;journal(s,triangle,energy);}
    for(int i=0;i<s->meshCount;i++)if(weight[i]){s->thermalCells[i].temperature=nextTemperature[i];s->thermalCells[i].atUs=s->timeUs;s->thermalCells[i].appliedEnergy=thermal[i][2];s->thermalCells[i].environmentEnergy=thermal[i][3];}
    return 1;
}
double nrHeatLiveEnergy(const State*s){double energy=0;for(int i=0;i<(int)NR_MAX_PARTICLES;i++)energy+=s->particleHeat[i].capacity*s->particleHeat[i].temperature;for(int i=0;i<NR_DEPOSITS;i++)energy+=s->depositHeat[i].capacity*s->depositHeat[i].temperature;for(int i=0;i<NR_TILES;i++)energy+=s->aggregateHeat[i].capacity*s->aggregateHeat[i].temperature;return energy;}
static int validReservoir(const HeatReservoir*r,int aggregate){
    if(!r->id)return !r->generation&&!r->capacity&&!r->temperature&&!r->contactFraction&&!r->conductance;
    return r->capacity>=.000001&&r->capacity<=(aggregate?1e15:1000000)&&r->temperature>=0&&r->temperature<=10000&&r->contactFraction>=0&&r->contactFraction<=1&&r->conductance>=0&&r->conductance<=(aggregate?1e15:1000000);
}
int nrValidMaterialHeat(const State*s){
    for(int i=0;i<NR_MATERIALS;i++){const HeatReservoir*r=&s->materialHeat[i];if(!validReservoir(r,0)||(r->id&&(s->schema<NR_STATE_SCHEMA_MATERIAL_HEAT||r->id!=(uint32_t)i+1||r->generation||!s->materials[i].used)))return 0;}
    for(int i=0;i<(int)NR_MAX_PARTICLES;i++){const HeatReservoir*r=&s->particleHeat[i];if(!validReservoir(r,0)||(r->id&&(!s->particles[i].state||r->id!=s->particles[i].id||r->generation||s->schema<NR_STATE_SCHEMA_MATERIAL_HEAT)))return 0;}
    for(int i=0;i<NR_DEPOSITS;i++){const HeatReservoir*r=&s->depositHeat[i];if(!validReservoir(r,0)||(r->id&&(!s->deposits[i].used||r->id!=s->deposits[i].id||r->generation>s->geometry.meshGeneration||s->schema<NR_STATE_SCHEMA_MATERIAL_HEAT)))return 0;}
    for(int i=0;i<NR_TILES;i++){const HeatReservoir*r=&s->aggregateHeat[i];if(!validReservoir(r,1)||(r->id&&(!s->tiles[i].used||r->id!=1||r->generation>s->geometry.meshGeneration||r->contactFraction||s->schema<NR_STATE_SCHEMA_MATERIAL_HEAT)))return 0;}
    double initial=s->materialHeatLedger.initial,imported=s->materialHeatLedger.imported,transferred=s->materialHeatLedger.transferred,exported=s->materialHeatLedger.exported;
    if(!(initial>=0&&initial<=1e15&&imported>=0&&imported<=1e15&&transferred>=0&&transferred<=1e15&&exported>=0&&exported<=1e15))return 0;
    return nrAbs(initial+imported-transferred-exported-nrHeatLiveEnergy(s))<=1e-8*(1+initial+imported);
}
