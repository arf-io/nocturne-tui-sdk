#include "internal.h"
int nrThermalSample(const NrContext*c,uint32_t index,double*out,uint32_t capacity){
    if(!c||c->state.magic!=NR_MAGIC||index>=(uint32_t)c->state.meshCount||!out||capacity<10||((uintptr_t)out%8))return -1;
    if(!c->state.thermalCells[index].used)return 0;
    if(!nrExternalOutput(c,out,10*sizeof(double)))return -1;
    const State*s=&c->state;double sample[4];nrThermalCell(s,(int)index,sample);
    double row[10]={sample[0],sample[1],s->thermalCells[index].initialEnergy,sample[2],sample[3],s->thermalTransfers[index].incoming,s->thermalTransfers[index].outgoing,s->thermalCells[index].capacity,s->thermalCells[index].power,s->thermalCells[index].ambient};
    memcpy(out,row,sizeof(row));return 1;
}
static double decay(double x){if(x>745)return 0;int squares=0;while(x>.125){x*=.5;squares++;}double result=1,term=1;for(int k=1;k<=20;k++){term*= -x/k;result+=term;}for(int k=0;k<squares;k++)result*=result;return result;}
static double fraction(double x){if(x>=.125)return 1-decay(x);double result=x,term=x;for(int k=2;k<=20;k++){term*= -x/k;result+=term;}return result;}
void nrThermalCell(const State*s,int index,double*out){
    double elapsed=(s->timeUs-s->thermalCells[index].atUs)/1000000.0,capacity=s->thermalCells[index].capacity,power=s->thermalCells[index].power,temperature=s->thermalCells[index].temperature;
    if(s->thermalCells[index].conductance){double x=s->thermalCells[index].conductance*elapsed/capacity,f=fraction(x);temperature+=(s->thermalCells[index].ambient-temperature)*f+power*elapsed/capacity*(x?f/x:1);}
    else temperature+=power*elapsed/capacity;
    double latent=s->latentHeat[index].coefficient;int waterId=s->surfaceWater.cells[index].surfaceId;
    if(latent>0&&waterId){uint64_t tauUs=s->surfaceWater.settings[waterId-1].evaporationUs;
        if(tauUs){double r=1000000.0/tauUs,k=s->thermalCells[index].conductance/capacity;
            double water=s->surfaceWater.cells[index].stored*decay(r*(s->thermalCells[index].atUs-s->surfaceWater.cells[index].atUs)/1000000.0);
            double difference=nrAbs(k-r),minimum=k<r?k:r;
            double convolution=difference?decay(minimum*elapsed)*fraction(difference*elapsed)/difference:elapsed*decay(k*elapsed);
            temperature-=latent*water/capacity*r*convolution;
        }
    }
    out[0]=temperature;out[1]=capacity*temperature;out[2]=s->thermalCells[index].appliedEnergy+power*elapsed;out[3]=s->thermalCells[index].environmentEnergy+out[1]-capacity*s->thermalCells[index].temperature-power*elapsed;
}
double nrLatentEnergy(const State*s,int index){
    double water[3];nrSurfaceWaterCell(s,index,water);
    return s->latentHeat[index].evaporatedEnergy+s->latentHeat[index].coefficient*(s->surfaceWater.cells[index].stored-water[1]);
}
void nrSettleWaterHeat(State*s,int index){
    if(!s->latentHeat[index].coefficient)return;
    double thermal[4],water[3];nrThermalCell(s,index,thermal);nrSurfaceWaterCell(s,index,water);
    s->latentHeat[index].evaporatedEnergy=nrLatentEnergy(s,index);
    s->thermalCells[index].temperature=thermal[0];s->thermalCells[index].appliedEnergy=thermal[2];s->thermalCells[index].environmentEnergy=thermal[3];s->thermalCells[index].atUs=s->timeUs;
    if(s->surfaceWater.cells[index].surfaceId){s->surfaceWater.cells[index].stored=water[1];s->surfaceWater.cells[index].atUs=s->timeUs;}
}
void nrThermalMeshChanged(State*s,int append,int base){
    if(append){for(int i=0;i<64;i++)if(s->thermalLinks[i].used)s->thermalLinks[i].generation=s->geometry.meshGeneration+1;}else memset(s->thermalLinks,0,sizeof(s->thermalLinks));
    if(append){memset(&s->thermalTransfers[base],0,(size_t)(s->meshCount-base)*sizeof(s->thermalTransfers[0]));memset(&s->thermalCells[base],0,(size_t)(s->meshCount-base)*sizeof(s->thermalCells[0]));return;}
    for(int i=0;i<NR_MESH;i++)if(s->thermalCells[i].used){double out[4];nrThermalCell(s,i,out);s->thermalHistory.initial+=s->thermalCells[i].initialEnergy;s->thermalHistory.applied+=out[2];s->thermalHistory.environment+=out[3];s->thermalHistory.exported+=out[1];s->thermalHistoricalTransfers.incoming+=s->thermalTransfers[i].incoming;s->thermalHistoricalTransfers.outgoing+=s->thermalTransfers[i].outgoing;}
    memset(s->thermalCells,0,sizeof(s->thermalCells));memset(s->thermalTransfers,0,sizeof(s->thermalTransfers));
}
int nrValidThermal(const State*s){
    if(!(s->historicalLatentEnergy>=0&&s->historicalLatentEnergy<=1e15))return 0;
    for(int i=0;i<NR_MESH;i++){double cp=s->latentHeat[i].coefficient,energy=s->latentHeat[i].evaporatedEnergy;
        if(!(cp>=0&&cp<=1e9)||!(energy>=0&&energy<=1e15)||((cp||energy)&&(i>=s->meshCount||!s->thermalCells[i].used)))return 0;
        if(cp){int id=s->geometry.triangleSurfaces[i];if(s->schema<NR_STATE_SCHEMA_LATENT_HEAT||id<1||id>NR_SURFACES||!s->surfaceWater.settings[id-1].used||s->thermalCells[i].atUs<s->surfaceWater.cells[i].atUs)return 0;}
        if(!(nrLatentEnergy(s,i)>=0&&nrLatentEnergy(s,i)<=1e15))return 0;
    }

    if(!(s->thermalHistoricalTransfers.incoming>=0&&s->thermalHistoricalTransfers.incoming<=1e15&&s->thermalHistoricalTransfers.outgoing>=0&&s->thermalHistoricalTransfers.outgoing<=1e15))return 0;
    for(int i=0;i<NR_MESH;i++)if(!(s->thermalTransfers[i].incoming>=0&&s->thermalTransfers[i].incoming<=1e15&&s->thermalTransfers[i].outgoing>=0&&s->thermalTransfers[i].outgoing<=1e15)||((s->thermalTransfers[i].incoming||s->thermalTransfers[i].outgoing)&&!s->thermalCells[i].used))return 0;
    if(!(s->thermalHistory.initial>=0&&s->thermalHistory.initial<=1e15&&s->thermalHistory.exported>=0&&s->thermalHistory.exported<=1e15&&s->thermalHistory.applied>=-1e15&&s->thermalHistory.applied<=1e15&&s->thermalHistory.environment>=-1e15&&s->thermalHistory.environment<=1e15)||nrAbs(s->thermalHistory.initial+s->thermalHistory.applied+s->thermalHistory.environment+s->thermalHistoricalTransfers.incoming-s->thermalHistoricalTransfers.outgoing-s->thermalHistory.exported)>1e-8*(1+s->thermalHistory.initial+nrAbs(s->thermalHistory.applied)))return 0;
    for(int i=0;i<NR_MESH;i++)if(s->thermalCells[i].used){
        if(i>=s->meshCount||s->thermalCells[i].used!=1||s->thermalCells[i].padding||s->thermalCells[i].atUs>s->timeUs||!(s->thermalCells[i].capacity>=.000001&&s->thermalCells[i].capacity<=1000000)||!(s->thermalCells[i].temperature>=0&&s->thermalCells[i].temperature<=10000)||!(s->thermalCells[i].ambient>=0&&s->thermalCells[i].ambient<=10000)||!(s->thermalCells[i].conductance>=0&&s->thermalCells[i].conductance<=1000000)||!(s->thermalCells[i].power>=-1000000&&s->thermalCells[i].power<=1000000)||!(s->thermalCells[i].initialEnergy>=0&&s->thermalCells[i].initialEnergy<=1e10)||!(s->thermalCells[i].appliedEnergy>=-1e15&&s->thermalCells[i].appliedEnergy<=1e15)||!(s->thermalCells[i].environmentEnergy>=-1e15&&s->thermalCells[i].environmentEnergy<=1e15))return 0;
        double out[4];nrThermalCell(s,i,out);if(!(out[0]>=0&&out[0]<=10000)||nrAbs(s->thermalCells[i].initialEnergy+out[2]+out[3]+s->thermalTransfers[i].incoming-s->thermalTransfers[i].outgoing-out[1])>1e-8*(1+s->thermalCells[i].initialEnergy+nrAbs(out[2])))return 0;
    }return 1;
}
static int reject(NrContext*c,const char*why){size_t n=strlen(why);if(n>255)n=255;memcpy(c->error,why,n);c->error[n]=0;return -1;}
static int number(const Json*j,const char*key,double*out,double low,double high,int required){int t=nrField(j,0,key);if(t<0)return !required;double value;if(!nrNumber(j,t,&value)||!(value>=low&&value<=high))return 0;*out=value;return 1;}
int nrLatentHeatCommand(NrContext*c,State*s,const Json*j){
    double triangle=0,coefficient=0;
    if(s->schema<NR_STATE_SCHEMA_LATENT_HEAT||!nrAllowed(j,0,"op triangleIndex latentHeatPerVolume")||!number(j,"triangleIndex",&triangle,0,s->meshCount-1,1)||triangle!=(int)triangle||!number(j,"latentHeatPerVolume",&coefficient,0,1e9,1))return reject(c,"Invalid latent heat configuration");
    int index=(int)triangle,id=s->geometry.triangleSurfaces[index];
    if(id<1||id>NR_SURFACES||!s->surfaceWater.settings[id-1].used||!s->thermalCells[index].used)return reject(c,"Latent heat requires water and thermal reservoirs");
    nrSettleWaterHeat(s,index);
    double thermal[4],water[3];nrThermalCell(s,index,thermal);nrSurfaceWaterCell(s,index,water);
    s->thermalCells[index].temperature=thermal[0];s->thermalCells[index].appliedEnergy=thermal[2];s->thermalCells[index].environmentEnergy=thermal[3];s->thermalCells[index].atUs=s->timeUs;
    if(s->surfaceWater.cells[index].surfaceId){s->surfaceWater.cells[index].stored=water[1];s->surfaceWater.cells[index].atUs=s->timeUs;}
    s->latentHeat[index].coefficient=coefficient;
    return nrValidThermal(s)?0:reject(c,"Latent heat ledger rejected");
}
int nrBindThermalValue(State*s,const Value*v,double x){
    int index=v->bindingId;
    if(index<0||index>=s->meshCount||!s->thermalCells[index].used)return 0;
    double*target=0;
    if(!strcmp(v->field,"thermal.power")&&x>=-1000000&&x<=1000000)target=&s->thermalCells[index].power;
    if(!strcmp(v->field,"thermal.ambientTemperature")&&x>=0&&x<=10000)target=&s->thermalCells[index].ambient;
    if(!strcmp(v->field,"thermal.conductance")&&x>=0&&x<=1000000)target=&s->thermalCells[index].conductance;
    if(!target)return 0;
    if(*target==x)return 1;
    unsigned char backup[sizeof(s->thermalCells[index])];memcpy(backup,&s->thermalCells[index],sizeof(backup));
    double sample[4];nrThermalCell(s,index,sample);
    s->thermalCells[index].temperature=sample[0];s->thermalCells[index].appliedEnergy=sample[2];s->thermalCells[index].environmentEnergy=sample[3];s->thermalCells[index].atUs=s->timeUs;*target=x;
    if(nrValidThermal(s))return 1;
    memcpy(&s->thermalCells[index],backup,sizeof(backup));return 0;
}
int nrThermalSettingsShape(const Json*j){
    double index=0,value=0;
    return nrEqual(j,nrField(j,0,"op"),"surface-thermal-settings")&&nrAllowed(j,0,"op triangleIndex ambientTemperature conductance power")&&
        number(j,"triangleIndex",&index,0,NR_MESH-1,1)&&index==(int)index&&
        (nrField(j,0,"ambientTemperature")>=0||nrField(j,0,"conductance")>=0||nrField(j,0,"power")>=0)&&
        number(j,"ambientTemperature",&value,0,10000,0)&&number(j,"conductance",&value,0,1000000,0)&&number(j,"power",&value,-1000000,1000000,0);
}
int nrThermalCommand(NrContext*c,State*s,const Json*j){
    if(nrEqual(j,nrField(j,0,"op"),"surface-thermal-settings")){
        if(!nrThermalSettingsShape(j))return reject(c,"Invalid thermal settings shape or domain");
        double triangle=0;nrNumber(j,nrField(j,0,"triangleIndex"),&triangle);int index=(int)triangle;
        if(index>=s->meshCount||!s->thermalCells[index].used)return reject(c,"Thermal settings cell unavailable");
        double sample[4];nrThermalCell(s,index,sample);
        s->thermalCells[index].temperature=sample[0];s->thermalCells[index].appliedEnergy=sample[2];s->thermalCells[index].environmentEnergy=sample[3];s->thermalCells[index].atUs=s->timeUs;
        number(j,"ambientTemperature",&s->thermalCells[index].ambient,0,10000,0);
        number(j,"conductance",&s->thermalCells[index].conductance,0,1000000,0);
        number(j,"power",&s->thermalCells[index].power,-1000000,1000000,0);
        return nrValidThermal(s)?0:reject(c,"Thermal settings energy or temperature out of range");
    }
    int change=nrEqual(j,nrField(j,0,"op"),"surface-thermal-power");double triangle=0,power=0;
    if(!nrAllowed(j,0,change?"op triangleIndex power":"op triangleIndex temperature capacity ambientTemperature conductance power")||!number(j,"triangleIndex",&triangle,0,s->meshCount-1,1)||triangle!=(int)triangle||!number(j,"power",&power,-1000000,1000000,change))return reject(c,"Invalid thermal command");int index=(int)triangle;
    if(change){if(!s->thermalCells[index].used)return reject(c,"Thermal cell not configured");double out[4];nrThermalCell(s,index,out);s->thermalCells[index].temperature=out[0];s->thermalCells[index].appliedEnergy=out[2];s->thermalCells[index].environmentEnergy=out[3];s->thermalCells[index].atUs=s->timeUs;s->thermalCells[index].power=power;}
    else{double temperature=0,capacity=0,ambient=293,conductance=0;if(s->thermalCells[index].used||!number(j,"temperature",&temperature,0,10000,1)||!number(j,"capacity",&capacity,.000001,1000000,1)||!number(j,"ambientTemperature",&ambient,0,10000,0)||!number(j,"conductance",&conductance,0,1000000,0))return reject(c,"Invalid thermal configuration");s->thermalCells[index].used=1;s->thermalCells[index].atUs=s->timeUs;s->thermalCells[index].temperature=temperature;s->thermalCells[index].capacity=capacity;s->thermalCells[index].ambient=ambient;s->thermalCells[index].conductance=conductance;s->thermalCells[index].power=power;s->thermalCells[index].initialEnergy=capacity*temperature;}
    return nrValidThermal(s)?0:reject(c,"Thermal energy or temperature out of range");
}

uint32_t nrThermalPaint(const State*s,int index,uint32_t rgb){
    if(!s->thermalCells[index].used)return rgb;double out[4];nrThermalCell(s,index,out);double difference=nrClamp((out[0]-s->thermalCells[index].ambient)/100,-1,1),r=(rgb>>16)&255,g=(rgb>>8)&255,b=rgb&255;
    if(difference>=0){r+=(255-r)*.2*difference;b*=1-.2*difference;}else{b+=(255-b)* -.2*difference;r*=1+.2*difference;}
    return ((uint32_t)r<<16)|((uint32_t)g<<8)|(uint32_t)b;
}

int nrTransferThermalEnergy(NrContext*c,State*s,int a,int b,double energy){
    if(a<0||b<0||a>=s->meshCount||b>=s->meshCount||a==b||!(energy>=0&&energy<=1e10))return reject(c,"Invalid heat transfer");
    if(!s->thermalCells[a].used||!s->thermalCells[b].used)return reject(c,"Heat transfer cells unavailable");double source[4],target[4];nrThermalCell(s,a,source);nrThermalCell(s,b,target);
    if(source[1]<energy||(target[1]+energy)/s->thermalCells[b].capacity>10000)return reject(c,"Heat transfer overdraw or target temperature out of range");
    for(int k=0;k<2;k++){int i=k?b:a;double*out=k?target:source;s->thermalCells[i].atUs=s->timeUs;s->thermalCells[i].appliedEnergy=out[2];s->thermalCells[i].environmentEnergy=out[3];s->thermalCells[i].temperature=(out[1]+(k?energy:-energy))/s->thermalCells[i].capacity;}
    s->thermalTransfers[a].outgoing+=energy;s->thermalTransfers[b].incoming+=energy;return nrValidThermal(s)?0:reject(c,"Heat transfer ledger rejected");
}
int nrThermalTransferCommand(NrContext*c,State*s,const Json*j){
    double from=0,to=0,energy=0;
    if(!nrAllowed(j,0,"op fromTriangle toTriangle energy")||!number(j,"fromTriangle",&from,0,s->meshCount-1,1)||from!=(int)from||!number(j,"toTriangle",&to,0,s->meshCount-1,1)||to!=(int)to||from==to||!number(j,"energy",&energy,.000000001,1e10,1))return reject(c,"Invalid heat transfer");
    return nrTransferThermalEnergy(c,s,(int)from,(int)to,energy);
}
int nrValidThermalLinks(const State*s){
    for(int i=0;i<64;i++)if(s->thermalLinks[i].used){int a=s->thermalLinks[i].from,b=s->thermalLinks[i].to;
        if(s->thermalLinks[i].used!=1||!s->thermalLinks[i].id||s->thermalLinks[i].id>65535||s->thermalLinks[i].generation!=s->geometry.meshGeneration||s->thermalLinks[i].padding||s->thermalLinks[i].startUs>s->timeUs||a<0||b<0||a>=s->meshCount||b>=s->meshCount||a==b||!s->thermalCells[a].used||!s->thermalCells[b].used||!(s->thermalLinks[i].conductance>0&&s->thermalLinks[i].conductance<=1000000))return 0;
        for(int j=0;j<i;j++)if(s->thermalLinks[j].used&&(s->thermalLinks[j].id==s->thermalLinks[i].id||(s->thermalLinks[j].from==a&&s->thermalLinks[j].to==b)||(s->thermalLinks[j].from==b&&s->thermalLinks[j].to==a)))return 0;
    }return 1;
}
int nrThermalLinkCommand(NrContext*c,State*s,const Json*j){
    int remove=nrEqual(j,nrField(j,0,"op"),"remove-surface-thermal-link");double id=0;
    if(!nrAllowed(j,0,remove?"op id":"op id fromTriangle toTriangle conductance")||!number(j,"id",&id,1,65535,1)||id!=(uint32_t)id)return reject(c,"Invalid thermal link id");int slot=-1,freeSlot=-1;
    for(int i=0;i<64;i++){if(s->thermalLinks[i].used&&s->thermalLinks[i].id==(uint32_t)id)slot=i;if(!s->thermalLinks[i].used&&freeSlot<0)freeSlot=i;}
    if(remove){if(slot>=0)memset(&s->thermalLinks[slot],0,sizeof(s->thermalLinks[slot]));return 0;}
    double a=0,b=0,k=0;if(!number(j,"fromTriangle",&a,0,s->meshCount-1,1)||a!=(int)a||!number(j,"toTriangle",&b,0,s->meshCount-1,1)||b!=(int)b||a==b||!number(j,"conductance",&k,.000000001,1000000,1))return reject(c,"Invalid thermal link parameters");
    if(slot<0)slot=freeSlot;if(slot<0)return reject(c,"Thermal link capacity");memset(&s->thermalLinks[slot],0,sizeof(s->thermalLinks[slot]));s->thermalLinks[slot].used=1;s->thermalLinks[slot].id=(uint32_t)id;s->thermalLinks[slot].generation=s->geometry.meshGeneration;s->thermalLinks[slot].from=(int)a;s->thermalLinks[slot].to=(int)b;s->thermalLinks[slot].conductance=k;s->thermalLinks[slot].startUs=s->timeUs;return nrValidThermalLinks(s)?0:reject(c,"Thermal link targets unavailable or duplicate");
}
static int root(int*parents,int index){while(parents[index]!=index)index=parents[index];return index;}
int nrThermalTransport(State*s){
    int parents[NR_MESH],touched[NR_MESH]={0},any=0;double weights[64]={0},freeState[NR_MESH][4];
    for(int i=0;i<NR_MESH;i++)parents[i]=i;
    for(int i=0;i<64;i++)if(s->thermalLinks[i].used){double start=(s->step-1)/120.0,epoch=s->thermalLinks[i].startUs/1000000.0;if(epoch>start)start=epoch;double elapsed=s->thermalLinks[i].startUs>=s->timeUs?0:nrClamp(s->step/120.0-start,0,1.0/120);weights[i]=s->thermalLinks[i].conductance*elapsed;if(weights[i]>0){int a=s->thermalLinks[i].from,b=s->thermalLinks[i].to,ra=root(parents,a),rb=root(parents,b);parents[rb]=ra;any=1;touched[a]=touched[b]=1;}}
    if(!any)return 1;
    for(int i=0;i<s->meshCount;i++)if(touched[i]){nrThermalCell(s,i,freeState[i]);if(!(freeState[i][0]>=0&&freeState[i][0]<=10000))return 0;}
    for(int component=0;component<s->meshCount;component++)if(touched[component]&&root(parents,component)==component){
        int nodes[128],map[NR_MESH],n=0;for(int i=0;i<NR_MESH;i++)map[i]=-1;
        for(int i=0;i<s->meshCount;i++)if(touched[i]&&root(parents,i)==component){if(n==128)return 0;map[i]=n;nodes[n++]=i;}
        double matrix[128][129]={{0}},solution[128],total=0,capacity=0;
        for(int i=0;i<n;i++){int cell=nodes[i];matrix[i][i]=s->thermalCells[cell].capacity;matrix[i][n]=freeState[cell][1];total+=freeState[cell][1];capacity+=s->thermalCells[cell].capacity;}
        for(int i=0;i<64;i++)if(weights[i]>0&&map[s->thermalLinks[i].from]>=0){int a=map[s->thermalLinks[i].from],b=map[s->thermalLinks[i].to];double k=weights[i];matrix[a][a]+=k;matrix[b][b]+=k;matrix[a][b]-=k;matrix[b][a]-=k;}
        for(int i=0;i<n;i++){int pivot=i;for(int k=i+1;k<n;k++)if(nrAbs(matrix[k][i])>nrAbs(matrix[pivot][i]))pivot=k;if(!(nrAbs(matrix[pivot][i])>0))return 0;if(pivot!=i)for(int j=i;j<=n;j++){double tmp=matrix[i][j];matrix[i][j]=matrix[pivot][j];matrix[pivot][j]=tmp;}for(int k=i+1;k<n;k++){double factor=matrix[k][i]/matrix[i][i];matrix[k][i]=0;for(int j=i+1;j<=n;j++)matrix[k][j]-=factor*matrix[i][j];}}
        for(int i=n-1;i>=0;i--){double value=matrix[i][n];for(int j=i+1;j<n;j++)value-=matrix[i][j]*solution[j];solution[i]=value/matrix[i][i];}
        double solved=0;for(int i=0;i<n;i++)solved+=solution[i]*s->thermalCells[nodes[i]].capacity;
        if(!(solved>=0)||nrAbs(solved-total)>1e-6*(1+total))return 0;double correction=(total-solved)/capacity;
        for(int i=0;i<n;i++){int cell=nodes[i];double temperature=solution[i]+correction;if(!(temperature>=0&&temperature<=10000))return 0;double energy=temperature*s->thermalCells[cell].capacity,delta=energy-freeState[cell][1];if(delta>=0)s->thermalTransfers[cell].incoming+=delta;else s->thermalTransfers[cell].outgoing-=delta;s->thermalCells[cell].temperature=temperature;s->thermalCells[cell].atUs=s->timeUs;s->thermalCells[cell].appliedEnergy=freeState[cell][2];s->thermalCells[cell].environmentEnergy=freeState[cell][3];}
    }return nrValidThermal(s);
}
