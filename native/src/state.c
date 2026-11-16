#include "internal.h"
_Static_assert(offsetof(State,nextParticle)==28u,"persistent particle identity prefix");
_Static_assert(offsetof(State,nextField)==32u,"persistent field identity prefix");
_Static_assert(sizeof(NrCell)==16, "canonical cell ABI requires 16 bytes");
_Static_assert(sizeof(NrCharacterCellInfo)==408u,"character cell inspection ABI");
_Static_assert(sizeof(double)==8, "numeric contract requires binary64 storage");
_Static_assert(sizeof(Vec3)==24, "vector ABI requires three binary64 values");
_Static_assert(offsetof(State,geometry)==4498608u, "pre-geometry snapshot prefix must remain unchanged");
_Static_assert(offsetof(State,birthOrientations)==4642648u, "schema-06 snapshot prefix must remain unchanged");
_Static_assert(offsetof(State,emitterMotions)==4643032u,"schema-07 prefix remains unchanged");
_Static_assert(offsetof(State,surfaceWaves)==4758616u,"schema-08 prefix remains unchanged");
_Static_assert(offsetof(State,floatBodies)==4779224u,"schema-09 prefix remains unchanged");
_Static_assert(offsetof(State,foam)==4788952u,"schema-10 prefix remains unchanged");
_Static_assert(offsetof(State,pathActors)==4797920u,"schema-11 prefix remains unchanged");
_Static_assert(offsetof(State,vimCount)==4848352u,"schema-12 prefix remains unchanged");
_Static_assert(offsetof(State,vimOperator)==4848368u,"schema-13 prefix remains unchanged");
_Static_assert(offsetof(State,vimRegister)==4848384u,"schema-14 prefix remains unchanged");
_Static_assert(offsetof(State,namedRegisters)==4856584u,"schema-15 prefix remains unchanged");
_Static_assert(offsetof(State,editorRedo)==5069808u,"schema-16 prefix remains unchanged");
_Static_assert(offsetof(State,repeatEdit)==5069816u,"schema-17 prefix remains unchanged");
_Static_assert(offsetof(State,flows)==5069840u,"schema-18 prefix remains unchanged");
_Static_assert(offsetof(State,flowSurfaces)==5089424u,"schema-19 prefix remains unchanged");
_Static_assert(offsetof(State,flowSinks)==5089680u,"schema-20 prefix remains unchanged");
_Static_assert(offsetof(State,flowSprays)==5090576u,"schema-21 prefix remains unchanged");
_Static_assert(offsetof(State,sprayParticles)==5091472u,"schema-22 prefix remains unchanged");
_Static_assert(offsetof(State,surfaceWater)==5124752u,"schema-23 prefix remains unchanged");
_Static_assert(offsetof(State,waterTransfers)==5133712u,"schema-24 prefix remains unchanged");
_Static_assert(offsetof(State,waterLinks)==5138064u,"schema-25 prefix remains unchanged");
_Static_assert(offsetof(State,sprayReentrained)==5140624u,"schema-26 prefix remains unchanged");
_Static_assert(offsetof(State,thermalCells)==5140752u,"schema-27 prefix remains unchanged");
_Static_assert(offsetof(State,thermalTransfers)==5161264u,"schema-28 prefix remains unchanged");
_Static_assert(offsetof(State,thermalLinks)==5165376u,"schema-29 prefix remains unchanged");
_Static_assert(offsetof(State,cellArt)==5167936u,"schema-30 prefix remains unchanged");
_Static_assert(offsetof(State,triggerFormulas)==5266400u,"schema-31 exact snapshot prefix size");
_Static_assert(offsetof(State,intentPayloads)==5433312u,"schema-32 retained formula prefix size");
_Static_assert(sizeof(IntentPayload)==8200u,"schema-32 intent payload size");
_Static_assert(offsetof(State,typedValues)==5958112u,"schema-32 event payload prefix size");
_Static_assert(sizeof(TypedValue)==8208u,"schema-32 typed value slot size");
_Static_assert(offsetof(State,triggerDataFormulas)==6483424u,"schema-32 typed value prefix size");
_Static_assert(sizeof(DataFormula)==13416u,"schema-32 compiled data formula size");
_Static_assert(offsetof(State,styleGuardFormulas)==7342048u,"schema-32 typed trigger prefix size");
_Static_assert(offsetof(State,characterRules)==7771360u,"schema-32 data formula prefix");
_Static_assert(sizeof(CharacterRuleSource)==4104u,"schema-32 retained character rule source");
_Static_assert(offsetof(State,characterRegions)==8296672u,"schema-32 retained rule prefix");
_Static_assert(offsetof(State,foamVelocity)==12499168u,"schema-32 exact snapshot prefix size");
_Static_assert(offsetof(State,flowThickness)==12503520u,"schema-33 exact snapshot prefix");
_Static_assert(sizeof(FlowThickness)==56u,"flow thickness setting wire size");
_Static_assert(offsetof(State,nextClusterIdentity)==12508512u,"schema-34 exact snapshot prefix");
_Static_assert(sizeof(TextIdentityRun)==16400u,"persistent run wire size");
_Static_assert(offsetof(State,floatHulls)==12918520u,"schema-35 exact snapshot prefix");
_Static_assert(sizeof(FloatHull)==6272u,"retained hull wire size");
_Static_assert(offsetof(State,surfaceFluids)==13319928u,"schema-36 exact snapshot prefix");
_Static_assert(sizeof(SurfaceFluid)==128u,"finite water motion wire size");
_Static_assert(offsetof(State,fluidHistory)==13321976u,"schema-37 exact snapshot prefix");
_Static_assert(sizeof(SurfaceFluidHistory)==112u,"fluid export history wire size");
_Static_assert(offsetof(State,angularFluids)==13323768u,"schema-38 exact snapshot prefix");
_Static_assert(offsetof(State,angularHistory)==13325432u,"schema-39 exact snapshot prefix");
_Static_assert(offsetof(State,surfacePoses)==13327224u,"schema-40 exact snapshot prefix");
_Static_assert(offsetof(State,waterLinkHeatCapacity)==13328248u,"schema-41 exact snapshot prefix");
_Static_assert(offsetof(State,latentHeat)==13328760u,"schema-42 exact snapshot prefix");
_Static_assert(offsetof(State,materialHeat)==13332864u,"schema-43 exact snapshot prefix");
_Static_assert(sizeof(HeatReservoir)==40u,"owned thermal reservoir layout");
_Static_assert(offsetof(State,aggregateProvenance)==13446176u,"schema-44 exact snapshot prefix");
_Static_assert(sizeof(AggregateProvenance)==128u,"aggregate provenance wire size");
_Static_assert(offsetof(State,fieldControls)==13478952u,"schema-46 exact snapshot prefix");
_Static_assert(sizeof(FieldControls)==96u,"retained field controls wire size");
_Static_assert(offsetof(State,promptPresentation)==13497384u,"schema49 exact prefix");
_Static_assert(offsetof(State,electricalArcs)==13497392u,"schema51 exact snapshot prefix");
_Static_assert(sizeof(ElectricalArc)==1112u,"electrical graph wire size");
_Static_assert(offsetof(State,burstControls)==13515184u,"schema52 exact snapshot prefix");
_Static_assert(sizeof(BurstControls)==48u,"burst controls wire size");
_Static_assert(offsetof(State,novaOptics)==13515952u,"schema53 exact snapshot prefix");
_Static_assert(sizeof(NovaOptics)==16u,"captured nova optics wire size");
_Static_assert(offsetof(State,coronaControls)==13548720u,"schema56 exact snapshot prefix");
_Static_assert(sizeof(CoronaControls)==48u,"corona controls wire size");
_Static_assert(offsetof(State,observatoryControls)==13549488u,"schema57 exact snapshot prefix");
_Static_assert(sizeof(ObservatoryControls)==48u,"Observatory controls wire size");
_Static_assert(offsetof(State,kineticControls)==13550256u,"schema58 exact snapshot prefix");
_Static_assert(sizeof(KineticControls)==408u,"Kinetic controls wire size");
_Static_assert(offsetof(State,atelierControls)==13556784u,"schema59 exact snapshot prefix");
_Static_assert(sizeof(AtelierControls)==152u,"Atelier controls wire size");
_Static_assert(offsetof(State,thermalSourceControls)==13559216u,"schema60 exact snapshot prefix");
_Static_assert(sizeof(ThermalSourceControls)==32u,"thermal source controls wire size");
_Static_assert(offsetof(State,worldSourceControls)==13559728u,"schema61 exact snapshot prefix");
_Static_assert(sizeof(WorldSourceControls)==48u,"world source controls wire size");
_Static_assert(offsetof(State,studioNovaControls)==13560496u,"schema62 exact snapshot prefix");
_Static_assert(sizeof(StudioNovaControls)==384u,"Studio nova controls wire size");
_Static_assert(offsetof(State,textAlphabetTail)==13566640u,"schema63 exact snapshot prefix");
_Static_assert(offsetof(State,legacyWindowSourceGeometry)==13578928u,"schema64/65 exact snapshot prefix");
_Static_assert(offsetof(State,textPhaseModel)==13578976u,"schema66 exact snapshot prefix");
_Static_assert(offsetof(State,promptFramed)==13579072u,"source text phase footer size");
_Static_assert(sizeof(PromptFramed)==266576u,"framed prompt controls and source checkpoint");
_Static_assert(sizeof(MaterialPattern)==264u,"source material pattern record size");
_Static_assert(offsetof(State,materialPatterns)==13845648u,"source prompt footer size");
_Static_assert(sizeof(SceneArt)==136u,"retained source scene record size");
_Static_assert(offsetof(State,sceneArt)==13849872u,"source material footer size");
_Static_assert(offsetof(State,canvasPresentation)==13850008u,"source scenic footer size");
_Static_assert(sizeof(WindowSourcePresentationState)==72u,"source window presentation record size");
_Static_assert(offsetof(State,legacyWindowPresentation)==13850016u,"canvas presentation footer size");
_Static_assert(offsetof(State,legacyWindowSourceOrder)==13850880u,"window presentation footer size");
_Static_assert(offsetof(State,sourceStage)==13850928u,"window order footer size");
_Static_assert(sizeof(SourceStageState)==270352u,"retained source stage pool size");
_Static_assert(offsetof(State,legacyWindowTextures)==14121280u,"schema67 exact snapshot prefix");
_Static_assert(sizeof(LegacyWindowTextures)==1048776u,"window texture pool size");
_Static_assert(offsetof(State,legacyWindowContent)==15170056u,"raw texture footer offset");
_Static_assert(sizeof(WindowContent)==18208u,"generated source window record");
_Static_assert(offsetof(State,promptFixed70)==15388552u,"schema68 generated window snapshot prefix");
_Static_assert(sizeof(WindowApplication)==20384u,"schema69 application footer size");
_Static_assert(sizeof(OriginalCamera)==2904u,"original camera pointer-free record size");
_Static_assert(sizeof(NumericFormulaNode)==40u,"schema-32 formula node size");
_Static_assert(sizeof(NumericFormula)==5216u,"schema-32 formula slot size");
/* Persistence schema is deliberately different from the uploaded binary. It is
 * a reconstruction, not ABI-compatible recovery of that binary's private state. */
static const uint8_t SNAP_MAGIC[8]= {
    'N','R','R','C','4','S','R','C'
};
static void u32write(uint8_t*p,uint32_t x) {
    p[0]=(uint8_t)x;
    p[1]=(uint8_t)(x>>8);
    p[2]=(uint8_t)(x>>16);
    p[3]=(uint8_t)(x>>24);
}
static uint32_t u32read(const uint8_t*p) {
    return p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;
}
void nrDefaults(State*s,uint32_t seed) {
    memset(s,0,offsetof(State,dynamicPrompt));
    nrPromptRuntimeClear(s);
    s->magic=NR_MAGIC;
    s->schema=NR_STATE_SCHEMA;
    s->seed=seed;
    s->width=160;
    s->height=48;
    s->camera=(Camera) {
        .position= {
            0,10,48
        },.pitch=-8,.nearPlane=.15,.farPlane=500,.fov=65,.span=65
    };
    s->background=0x111018;
    s->stars=150;
    s->starFar=150;
    s->sampling=3; /* Restore authored mixed background defaults; geometry owns its style. */
    s->meshSampling=1;
    s->style=0;
    s->nextParticle=1;
    s->nextField=1;
    s->nextIntent=1;
    s->nextMessageId=1;
    for(int i=0; i<4; i++)nrInitMaterial(&s->materials[i],i);
    s->floor=(Floor) {
        .enabled=1,.visible=0,.sampling=1,.maxIndividual=256,.maxTiles=128,.overflow=1,
        .height=0,.restitution=.18,.friction=.65,.settleSpeed=.6,.reentrain=6,.cellSize=3,.alpha=.15,.evaporation=.04
    };
    s->promptPresentation.ambiguous=1;
    s->promptDocument.active=1;
    s->promptDocument.minRows=1;
    s->promptDocument.maxRows=8;
    s->promptDocument.alpha=.22;
    s->promptDocument.border=1;
    s->promptDocument.anchor=-1;
    s->dimensions=3;
    nrSyncTextIdentities(s);
    s->legacyTextIdentities[0]=s->textIdentities[0];
}
uint32_t nrContextSize(void) {
    return (uint32_t)sizeof(NrContext);
}
int nrValidViewport(uint32_t w,uint32_t h) {
    /* Raster coordinates are signed 32-bit; the public cell count is uint32.
     * These are representation checks, not terminal size or allocation policy. */
    return w&&h&&w<=2147483647u/2&&h<=2147483647u/4&&(uint64_t)w*h<=UINT32_MAX;
}
static uint64_t renderBytes(uint32_t width,uint32_t height) {
    if(!nrValidViewport(width,height))return 0;
    uint64_t cells=(uint64_t)width*height;
    /* Each of the twelve sections is aligned independently. Worst case is seven padding bytes
     * per section; all products fit uint64 for representable cell counts. */
    uint64_t sizes[]={cells*sizeof(NrCell),cells*8*NR_LAYERS*sizeof(Fragment),cells*8,cells*8*sizeof(uint32_t),cells,cells*8*sizeof(uint32_t),cells*sizeof(uint32_t),cells*sizeof(uint32_t),cells*8*sizeof(int32_t),cells*sizeof(double),cells*8*sizeof(uint32_t),cells*8*sizeof(int32_t)},total=0;
    for(size_t i=0;i<sizeof(sizes)/sizeof(sizes[0]);i++)total+=(sizes[i]+7u)&~UINT64_C(7);
    return total;
}
static void bindRenderMemory(NrContext*c,void*memory,uint64_t capacity,uint32_t width,uint32_t height) {
    uint8_t*p=memory;size_t cells=(size_t)width*height;
    c->cells=(NrCell*)p;p+=((cells*sizeof(NrCell)+7u)&~(size_t)7);
    c->fragments=(Fragment(*)[NR_LAYERS])p;p+=((cells*8*NR_LAYERS*sizeof(Fragment)+7u)&~(size_t)7);
    c->fragmentCounts=p;p+=((cells*8+7u)&~(size_t)7);
    c->backgroundPixels=(uint32_t*)p;p+=((cells*8*sizeof(uint32_t)+7u)&~(size_t)7);
    c->plotMask=p;p+=((cells+7u)&~(size_t)7);
    c->plotColor=(uint32_t(*)[8])p;p+=((cells*8*sizeof(uint32_t)+7u)&~(size_t)7);
    c->characterIndices=(uint32_t*)p;p+=((cells*sizeof(uint32_t)+7u)&~(size_t)7);
    c->characterOwners=(uint32_t*)p;p+=((cells*sizeof(uint32_t)+7u)&~(size_t)7);
    c->sourceDepth=(int32_t*)p;p+=((cells*8*sizeof(int32_t)+7u)&~(size_t)7);
    c->windowDepth=(double*)p;p+=((cells*sizeof(double)+7u)&~(size_t)7);
    c->legacyFragmentOverflow=(uint32_t*)p;p+=((cells*8*sizeof(uint32_t)+7u)&~(size_t)7);
    c->sourcePickDepth=(int32_t*)p;
    c->renderMemoryBytes=capacity;
}
int nrInit(void*memory,uint32_t cap,uint32_t seed) {
    const uint16_t endian=1;
    if(*(const uint8_t*)&endian!=1)return -1; /* Explicit LE-only snapshot/cell contract. */
    if(!memory||((uintptr_t)memory&7u)||cap<sizeof(NrContext))return -1;
    NrContext*c=memory;
    memset(c,0,sizeof(*c));
    c->valid=NR_MAGIC;
    c->capacity=cap;
    c->commandPathLimit=nrCommandPathInitialLimit();
    nrPromptBindInitial(c);
    nrDefaults(&c->state,seed);
    bindRenderMemory(c,c->inlineRenderMemory,sizeof(c->inlineRenderMemory),c->state.width,c->state.height);
    return 0;
}
static int valid(const NrContext*c) {
    return c&&c->valid==NR_MAGIC&&c->capacity>=sizeof(*c);
}
uint64_t nrRenderMemorySize(const NrContext*c) {return valid(c)?renderBytes(c->state.width,c->state.height):0;}
uint64_t nrRenderMemoryCapacity(const NrContext*c) {return valid(c)?c->renderMemoryBytes:0;}
int nrSetRenderMemory(NrContext*c,void*memory,uint64_t capacity) {
    if(!valid(c)||!memory||((uintptr_t)memory&7u)||capacity>SIZE_MAX)return -1;
    uint64_t required=nrRenderMemorySize(c);
    uintptr_t first=(uintptr_t)memory,context=(uintptr_t)c;
    if(!required||capacity<required||capacity>UINTPTR_MAX-first)return -1;
    if(first<context+sizeof(*c)&&context<first+(uintptr_t)capacity)return -1;
    uintptr_t prompt=(uintptr_t)c->promptMemory,model=(uintptr_t)c->modelMemory;
    if(c->promptMemoryBytes&&first<prompt+c->promptMemoryBytes&&prompt<first+(uintptr_t)capacity)return -1;
    if(c->modelMemoryBytes&&first<model+c->modelMemoryBytes&&model<first+(uintptr_t)capacity)return -1;
    uintptr_t modal=(uintptr_t)c->modalMemory;
    if(c->modalMemoryBytes&&first<modal+c->modalMemoryBytes&&modal<first+(uintptr_t)capacity)return -1;
    bindRenderMemory(c,memory,capacity,c->state.width,c->state.height);c->characterFrameValid=0;return 0;
}
uint32_t nrWidth(const NrContext*c) {
    return valid(c)?c->state.width:0;
}
uint32_t nrHeight(const NrContext*c) {
    return valid(c)?c->state.height:0;
}
const NrCell*nrCells(const NrContext*c) {
    return valid(c)?c->cells:0;
}
int nrInspectCharacterCell(const NrContext*c,int32_t x,int32_t y,NrCharacterCellInfo*out,uint32_t capacity){
    if(!valid(c)||!out||capacity<sizeof(*out)||!nrExternalOutput(c,out,sizeof(*out))||x<0||y<0||(uint32_t)x>=c->state.width||(uint32_t)y>=c->state.height)return -1;
    if(!c->characterFrameValid)return -2;
    size_t at=(size_t)y*c->state.width+(uint32_t)x;NrCharacterCellInfo result;memset(&result,0,sizeof(result));
    result.cell=c->cells[at];result.index=c->characterIndices[at];if(result.index==UINT32_MAX)result.index=(uint32_t)at;
    const char*role,*state,*path;nrCharacterCellOwner(c,at,&role,&state,&path);
    memcpy(result.role,role,strlen(role)+1);memcpy(result.state,state,strlen(state)+1);memcpy(result.path,path,strlen(path)+1);
    *out=result;return 0;
}
const char*nrError(const NrContext*c) {
    return valid(c)?c->error:"Invalid context";
}
int nrCommand(NrContext*c,const char*text,uint32_t len) {
    if(!valid(c)||!text||len>INT32_MAX||!nrExternalOutput(c,text,len))return -1;
    c->error[0]=0;
    if(!nrParse(&c->json,text,(int)len)) {
        memcpy(c->error,c->json.error,sizeof(c->json.error));
        return -1;
    }
    if(nrEqual(&c->json,nrField(&c->json,0,"op"),"pointer")||nrEqual(&c->json,nrField(&c->json,0,"op"),"wheel")){
        /* The hit test reads the current frame. With direct transactions enabled, a frame rendered since the State last
         * changed is reused: rendering is a pure function of the State and the render memory, so a second render
         * would write the same cells (TRANSACTIONS.md, "pointer"; the verification build re-renders and compares). */
        if(!(c->commandPathLimit&NR_PATH_DIRECT)||!c->characterFrameValid){if(!nrRender(c))return -1;}
#if defined(NR_SHADOW_CHECK)&&!defined(__wasm__) /* the verification build is native only */
        else nrShadowFrame(c);
#endif
    }
    /* Direct transactions (native/docs/TRANSACTIONS.md): plan against the live State, commit in place. A declined
     * plan wrote nothing; the copy transaction below then runs exactly as it always has. */
    if((c->commandPathLimit&NR_PATH_DIRECT)&&c->settled){
#if defined(NR_SHADOW_CHECK)&&!defined(__wasm__) /* the verification build is native only */
        int result=nrShadowDirect(c);
#else
        int result=nrDirectApply(c,&c->json);
#endif
        if(result!=NR_DIRECT_DECLINED){c->counters.direct++;if(result>=0)c->characterFrameValid=0;return result;}
    }
    return nrCopyTransaction(c,&c->state);
}
/* The copy transaction: copy the State into the trial, apply, run the post-command pipeline and validate the whole
 * trial, then copy it back. `live` is c->state, or c->probe in the verification build's reference run. */
int nrCopyTransaction(NrContext*c,State*live){
    c->counters.fallback++;
    nrStateCopy(&c->trial,live);
    int result=nrTransaction(c,&c->trial,&c->json);
    if(result<0)return -1;
    if(!nrSyncTextIdentities(&c->trial)){memcpy(c->error,"Persistent text identity capacity exhausted",sizeof("Persistent text identity capacity exhausted"));return -1;}
    if(!nrStylesTick(c,&c->trial)){memcpy(c->error,"Appearance guard rejected",26);return -1;}
    nrPromptStorageMirror(&c->trial);
    c->counters.comparedBytes+=sizeof(live->characterRules)+sizeof(live->characterRegions);c->counters.fullValidations++;
    int characterRulesChanged=memcmp(live->characterRules,c->trial.characterRules,sizeof(live->characterRules))!=0;
    int characterRegionsChanged=memcmp(live->characterRegions,c->trial.characterRegions,sizeof(live->characterRegions))!=0;
    if(!nrValidState(&c->trial)||!nrValidateIntentPayloads(c,&c->trial)||
       (characterRulesChanged&&!nrValidateCharacterRules(c,&c->trial))||
       (characterRegionsChanged&&!nrValidateCharacterRegions(c,&c->trial))) {
        if(strcmp(c->error,"Prompt storage required"))memcpy(c->error,"State invariant rejected",25);
        return -1;
    }
    nrStateCopy(live,&c->trial);
    if(live==&c->state){
        if(characterRulesChanged)nrCacheCharacterRules(c);
        if(characterRegionsChanged)nrCacheCharacterRegions(c);
        c->characterFrameValid=0;
        /* The trial just ran the whole pipeline and passed every validator: the State is settled. */
        c->settled=1;
    }
    return result;
}
uint32_t nrRender(NrContext*c) {
    if(!valid(c))return 0;
    c->characterFrameValid=0;
    uint64_t needed=nrRenderMemorySize(c);
    if(!needed||needed>c->renderMemoryBytes||needed>SIZE_MAX) {
        memcpy(c->error,"Viewport render memory required",32);return 0;
    }
    /* A resize or restore changes section offsets even when capacity is reused. */
    bindRenderMemory(c,c->cells,c->renderMemoryBytes,c->state.width,c->state.height);
    c->fragmentOverflow=0;
    c->contentNeedsReader=0;
    c->clippedPrimitives=0;
    nrPrepareAppearance(c);
    nrRenderAll(c);
    nrDrawCharacterRegions(c);
    nrDrawCharacterRules(c);
    c->rendering=0;
    c->characterFrameValid=1;
    return c->state.width*c->state.height;
}
uint32_t nrSnapshotSize(void) {return (uint32_t)offsetof(State,dynamicPrompt)+24+nrPromptWireSize();}
uint32_t nrSnapshotSizeFor(const NrContext*c) {
    if(!valid(c))return 0;uint32_t dynamic=nrPromptPayloadSize(&c->state);uint64_t size=(uint64_t)offsetof(State,dynamicPrompt)+24+dynamic+(uint64_t)c->state.sourceModel.count*sizeof(NrModelTriangle)+(uint64_t)c->state.sourceModal.scalars*4;
    return !dynamic||size>UINT32_MAX?0:(uint32_t)size;
}
int nrSave(const NrContext*c,void*d,uint32_t cap) {
    uint32_t needed=nrSnapshotSizeFor(c);if(!needed||!d||cap<needed||!nrExternalOutput(c,d,needed))return -1;
    uint8_t*p=d;uint32_t fixed=(uint32_t)offsetof(State,dynamicPrompt);
    memcpy(p,SNAP_MAGIC,8);u32write(p+8,NR_ABI_VERSION);u32write(p+12,NR_STATE_SCHEMA);u32write(p+16,needed-24);
    memcpy(p+24,&c->state,fixed);uint32_t promptBytes=nrPromptPayloadSize(&c->state);
    if(nrPromptSavePayload(&c->state,p+24+fixed,promptBytes))return -1;
    if(c->state.sourceModel.count)memcpy(p+24+fixed+promptBytes,c->state.modelRecords,(size_t)c->state.sourceModel.count*sizeof(NrModelTriangle));
    if(c->state.sourceModal.scalars)memcpy(p+24+fixed+promptBytes+(size_t)c->state.sourceModel.count*sizeof(NrModelTriangle),c->state.modalScalars,(size_t)c->state.sourceModal.scalars*4);
    u32write(p+20,nrCrc(p+24,needed-24));return 0;
}
typedef enum { SNAP_LAYOUT_INVALID=0, SNAP_LAYOUT_LOCAL=1, SNAP_LAYOUT_CONTRACTS7=2, SNAP_LAYOUT_UNION=3, SNAP_LAYOUT_GEOMETRY=4, SNAP_LAYOUT_BIRTH_FRAME=5, SNAP_LAYOUT_PARTICLE_MOTION=6, SNAP_LAYOUT_SURFACE_WAVES=7, SNAP_LAYOUT_FLOAT_BODIES=8, SNAP_LAYOUT_FOAM=9, SNAP_LAYOUT_PATH_ACTORS=10, SNAP_LAYOUT_VIM_COUNT=11, SNAP_LAYOUT_VIM_OPERATOR=12, SNAP_LAYOUT_VIM_REGISTER=13, SNAP_LAYOUT_NAMED_REGISTERS=14, SNAP_LAYOUT_EDITOR_REDO=15, SNAP_LAYOUT_REPEAT_EDIT=16, SNAP_LAYOUT_FLOW=17, SNAP_LAYOUT_FLOW_SURFACE=18, SNAP_LAYOUT_FLOW_SINK=19, SNAP_LAYOUT_FLOW_SPRAY=20, SNAP_LAYOUT_SPRAY_PARTICLES=21, SNAP_LAYOUT_SURFACE_WATER=22, SNAP_LAYOUT_WATER_TRANSFER=23, SNAP_LAYOUT_WATER_LINK=24, SNAP_LAYOUT_WATER_REEMIT=25, SNAP_LAYOUT_THERMAL=26, SNAP_LAYOUT_THERMAL_TRANSFER=27, SNAP_LAYOUT_THERMAL_LINK=28, SNAP_LAYOUT_CELL_ART=29, SNAP_LAYOUT_TRIGGER_FORMULAS=30, SNAP_LAYOUT_FOAM_TRANSPORT=31, SNAP_LAYOUT_FLOW_THICKNESS=32, SNAP_LAYOUT_TEXT_IDENTITIES=33, SNAP_LAYOUT_FLOAT_HULLS=34, SNAP_LAYOUT_SURFACE_FLUID=35, SNAP_LAYOUT_FLUID_HISTORY=36, SNAP_LAYOUT_ANGULAR_FLUID=37, SNAP_LAYOUT_ANGULAR_HISTORY=38, SNAP_LAYOUT_SURFACE_POSE=39, SNAP_LAYOUT_HYDRAULIC_HEAT=40, SNAP_LAYOUT_LATENT_HEAT=41, SNAP_LAYOUT_MATERIAL_HEAT=42, SNAP_LAYOUT_AGGREGATE_REEMIT=43, SNAP_LAYOUT_MESH_SUBDIVISION=44, SNAP_LAYOUT_COLOR_FIELDS=45, SNAP_LAYOUT_PROMPT_PRESENTATION=46, SNAP_LAYOUT_ELECTRICAL_ARCS=47, SNAP_LAYOUT_BURST_CONTROLS=48, SNAP_LAYOUT_NOVA_OPTICS=49, SNAP_LAYOUT_CORONA=50, SNAP_LAYOUT_OBSERVATORY=51, SNAP_LAYOUT_KINETIC=52, SNAP_LAYOUT_ATELIER=53, SNAP_LAYOUT_THERMAL_PROFILES=54, SNAP_LAYOUT_WORLD_PROFILES=55, SNAP_LAYOUT_STUDIO_NOVA=56, SNAP_LAYOUT_TEXT_ALPHABET=57, SNAP_LAYOUT_WINDOW_SOURCE=58, SNAP_LAYOUT_TEXT_PHASE_MODEL=59, SNAP_LAYOUT_WINDOW_TEXTURE=60, SNAP_LAYOUT_PROMPT_CAPACITY=61, SNAP_LAYOUT_WINDOW_APPLICATION=62, SNAP_LAYOUT_COMBINED=63, SNAP_LAYOUT_ORIGINAL_WINDOW_POOLS=64, SNAP_LAYOUT_WINDOW_POOLS=65, SNAP_LAYOUT_ORIGINAL_CAMERA=66, SNAP_LAYOUT_ATELIER_WINDOWS=67, SNAP_LAYOUT_ATELIER_APP_PARTICLES=68 } SnapshotLayout;
typedef struct { uint32_t schema,payloadBytes; SnapshotLayout layout; } SnapshotLayoutEntry;
static uint32_t legacyStateBytes(void) {
    const size_t oldSplit=offsetof(State,triggers)+sizeof(((State*)0)->triggers);
    const size_t newTail=offsetof(State,mesh);
    return (uint32_t)(oldSplit+offsetof(State,geometry)-newTail);
}
static SnapshotLayout snapshotLayout(uint32_t schema,uint32_t payloadBytes) {
    const SnapshotLayoutEntry known[]={
        {NR_STATE_SCHEMA_OLDEST,0, SNAP_LAYOUT_LOCAL},
        {NR_STATE_SCHEMA_LOCAL_SELECTOR,0,SNAP_LAYOUT_LOCAL},
        {NR_STATE_SCHEMA_LOCAL_ACTION,0,SNAP_LAYOUT_LOCAL},
        {NR_STATE_SCHEMA_CONTRACTS7,0,SNAP_LAYOUT_CONTRACTS7},
        {NR_STATE_SCHEMA_PRE_GEOMETRY,0,SNAP_LAYOUT_UNION},
        {NR_STATE_SCHEMA_GEOMETRY,0,SNAP_LAYOUT_GEOMETRY},
        {NR_STATE_SCHEMA_BIRTH_FRAME,0,SNAP_LAYOUT_BIRTH_FRAME},
        {NR_STATE_SCHEMA_PARTICLE_MOTION,0,SNAP_LAYOUT_PARTICLE_MOTION},
        {NR_STATE_SCHEMA_SURFACE_WAVES,0,SNAP_LAYOUT_SURFACE_WAVES},
        {NR_STATE_SCHEMA_FLOAT_BODIES,0,SNAP_LAYOUT_FLOAT_BODIES},
        {NR_STATE_SCHEMA_FOAM,0,SNAP_LAYOUT_FOAM},
        {NR_STATE_SCHEMA_PATH_ACTORS,0,SNAP_LAYOUT_PATH_ACTORS},
        {NR_STATE_SCHEMA_VIM_COUNT,0,SNAP_LAYOUT_VIM_COUNT},
        {NR_STATE_SCHEMA_VIM_OPERATOR,0,SNAP_LAYOUT_VIM_OPERATOR},
        {NR_STATE_SCHEMA_VIM_REGISTER,0,SNAP_LAYOUT_VIM_REGISTER},
        {NR_STATE_SCHEMA_NAMED_REGISTERS,0,SNAP_LAYOUT_NAMED_REGISTERS},
        {NR_STATE_SCHEMA_EDITOR_REDO,0,SNAP_LAYOUT_EDITOR_REDO},
        {NR_STATE_SCHEMA_REPEAT_EDIT,0,SNAP_LAYOUT_REPEAT_EDIT},
        {NR_STATE_SCHEMA_FLOW,0,SNAP_LAYOUT_FLOW},
        {NR_STATE_SCHEMA_FLOW_SURFACE,0,SNAP_LAYOUT_FLOW_SURFACE},
        {NR_STATE_SCHEMA_FLOW_SINK,0,SNAP_LAYOUT_FLOW_SINK},
        {NR_STATE_SCHEMA_FLOW_SPRAY,0,SNAP_LAYOUT_FLOW_SPRAY},
        {NR_STATE_SCHEMA_SPRAY_PARTICLES,0,SNAP_LAYOUT_SPRAY_PARTICLES},
        {NR_STATE_SCHEMA_SURFACE_WATER,0,SNAP_LAYOUT_SURFACE_WATER},
        {NR_STATE_SCHEMA_WATER_TRANSFER,0,SNAP_LAYOUT_WATER_TRANSFER},
        {NR_STATE_SCHEMA_WATER_LINK,0,SNAP_LAYOUT_WATER_LINK},
        {NR_STATE_SCHEMA_WATER_REEMIT,0,SNAP_LAYOUT_WATER_REEMIT},
        {NR_STATE_SCHEMA_THERMAL,0,SNAP_LAYOUT_THERMAL},
        {NR_STATE_SCHEMA_THERMAL_TRANSFER,0,SNAP_LAYOUT_THERMAL_TRANSFER},
        {NR_STATE_SCHEMA_THERMAL_LINK,0,SNAP_LAYOUT_THERMAL_LINK},
        {NR_STATE_SCHEMA_CELL_ART,0,SNAP_LAYOUT_CELL_ART},
        {NR_STATE_SCHEMA_GENERAL_API,0,SNAP_LAYOUT_TRIGGER_FORMULAS},
        {NR_STATE_SCHEMA_FOAM_TRANSPORT,0,SNAP_LAYOUT_FOAM_TRANSPORT},
        {NR_STATE_SCHEMA_FLOW_THICKNESS,0,SNAP_LAYOUT_FLOW_THICKNESS},
        {NR_STATE_SCHEMA_TEXT_IDENTITIES,0,SNAP_LAYOUT_TEXT_IDENTITIES},
        {NR_STATE_SCHEMA_FLOAT_HULLS,0,SNAP_LAYOUT_FLOAT_HULLS},
        {NR_STATE_SCHEMA_SURFACE_FLUID,0,SNAP_LAYOUT_SURFACE_FLUID},
        {NR_STATE_SCHEMA_FLUID_HISTORY,0,SNAP_LAYOUT_FLUID_HISTORY},
        {NR_STATE_SCHEMA_ANGULAR_FLUID,0,SNAP_LAYOUT_ANGULAR_FLUID},
        {NR_STATE_SCHEMA_ANGULAR_HISTORY,0,SNAP_LAYOUT_ANGULAR_HISTORY},
        {NR_STATE_SCHEMA_SURFACE_POSE,0,SNAP_LAYOUT_SURFACE_POSE},
        {NR_STATE_SCHEMA_HYDRAULIC_HEAT,0,SNAP_LAYOUT_HYDRAULIC_HEAT},
        {NR_STATE_SCHEMA_LATENT_HEAT,0,SNAP_LAYOUT_LATENT_HEAT},
        {NR_STATE_SCHEMA_MATERIAL_HEAT,0,SNAP_LAYOUT_MATERIAL_HEAT},
        {NR_STATE_SCHEMA_AGGREGATE_REEMIT,0,SNAP_LAYOUT_AGGREGATE_REEMIT},
        {NR_STATE_SCHEMA_MESH_SUBDIVISION,0,SNAP_LAYOUT_MESH_SUBDIVISION},
        {NR_STATE_SCHEMA_COLOR_FIELDS,0,SNAP_LAYOUT_COLOR_FIELDS},
        {NR_STATE_SCHEMA_SOFT_FRONTS,0,SNAP_LAYOUT_COLOR_FIELDS},
        {NR_STATE_SCHEMA_SOURCE_OPTICS,0,SNAP_LAYOUT_COLOR_FIELDS},
        {NR_STATE_SCHEMA_PROMPT_PRESENTATION,0,SNAP_LAYOUT_PROMPT_PRESENTATION},
        {NR_STATE_SCHEMA_BIDI_PROMPT,0,SNAP_LAYOUT_PROMPT_PRESENTATION},
        {NR_STATE_SCHEMA_ELECTRICAL_ARCS,13515184u,SNAP_LAYOUT_ELECTRICAL_ARCS},
        {NR_STATE_SCHEMA_BURST_CONTROLS,13515952u,SNAP_LAYOUT_BURST_CONTROLS},
        {NR_STATE_SCHEMA_NOVA_OPTICS,13548720u,SNAP_LAYOUT_NOVA_OPTICS},
        {NR_STATE_SCHEMA_RESOURCE_ANIMATION,13548720u,SNAP_LAYOUT_NOVA_OPTICS},
        {NR_STATE_SCHEMA_WIDE_UNBOUND_VALUES,13548720u,SNAP_LAYOUT_NOVA_OPTICS},
        {NR_STATE_SCHEMA_CORONA,13549488u,SNAP_LAYOUT_CORONA},
        {NR_STATE_SCHEMA_OBSERVATORY,13550256u,SNAP_LAYOUT_OBSERVATORY},
        {NR_STATE_SCHEMA_KINETIC,13556784u,SNAP_LAYOUT_KINETIC},
        {NR_STATE_SCHEMA_ATELIER,13559216u,SNAP_LAYOUT_ATELIER},
        {NR_STATE_SCHEMA_THERMAL_PROFILES,13559728u,SNAP_LAYOUT_THERMAL_PROFILES},
        {NR_STATE_SCHEMA_WORLD_PROFILES,13560496u,SNAP_LAYOUT_WORLD_PROFILES},
        {NR_STATE_SCHEMA_STUDIO_NOVA,13566640u,SNAP_LAYOUT_STUDIO_NOVA},
        {NR_STATE_SCHEMA_TEXT_ALPHABET,13578928u,SNAP_LAYOUT_TEXT_ALPHABET},
        {NR_STATE_SCHEMA_TEXT_UINT32_SEED,13578928u,SNAP_LAYOUT_TEXT_ALPHABET},
        {NR_STATE_SCHEMA_WINDOW_SOURCE,13578976u,SNAP_LAYOUT_WINDOW_SOURCE},
        {NR_STATE_SCHEMA_TEXT_PHASE_MODEL,14121280u,SNAP_LAYOUT_TEXT_PHASE_MODEL},
        {NR_STATE_SCHEMA_WINDOW_TEXTURE,15388552u,SNAP_LAYOUT_WINDOW_TEXTURE},
        {NR_STATE_SCHEMA_PROMPT_CAPACITY,0,SNAP_LAYOUT_PROMPT_CAPACITY},
        {NR_STATE_SCHEMA_WINDOW_APPLICATION,15408936u,SNAP_LAYOUT_WINDOW_APPLICATION},
        {0x20261071u,0,SNAP_LAYOUT_COMBINED},
        {NR_STATE_SCHEMA_WINDOW_POOLS,18416192u,SNAP_LAYOUT_ORIGINAL_WINDOW_POOLS},
        {NR_STATE_SCHEMA_WINDOW_POOLS,0,SNAP_LAYOUT_WINDOW_POOLS},
        {NR_STATE_SCHEMA_CAMERA_ORIGINAL,18419096u,SNAP_LAYOUT_ORIGINAL_CAMERA},
        {NR_STATE_SCHEMA_ATELIER_WINDOWS,18426008u,SNAP_LAYOUT_ATELIER_WINDOWS},
        {NR_STATE_SCHEMA_ATELIER_APP_PARTICLES,18426160u,SNAP_LAYOUT_ATELIER_APP_PARTICLES}
    };
    int matches=0;SnapshotLayout selected=SNAP_LAYOUT_INVALID;
    for(size_t i=0;i<sizeof(known)/sizeof(known[0]);i++) {
        uint32_t expected=known[i].layout==SNAP_LAYOUT_LOCAL?legacyStateBytes():
            known[i].layout==SNAP_LAYOUT_ATELIER_APP_PARTICLES?18426160u:
            known[i].layout==SNAP_LAYOUT_ATELIER_WINDOWS?18426008u:
            known[i].layout==SNAP_LAYOUT_ORIGINAL_CAMERA?18419096u:
            known[i].layout==SNAP_LAYOUT_WINDOW_POOLS?30475272u:
            known[i].layout==SNAP_LAYOUT_ORIGINAL_WINDOW_POOLS?18416192u:
            known[i].layout==SNAP_LAYOUT_COMBINED?(uint32_t)offsetof(State,windows):
            known[i].layout==SNAP_LAYOUT_WINDOW_APPLICATION?15408936u:
            known[i].layout==SNAP_LAYOUT_PROMPT_CAPACITY?(uint32_t)offsetof(State,windowApplication):
            known[i].layout==SNAP_LAYOUT_WINDOW_TEXTURE?(uint32_t)offsetof(State,promptFixed70):
            known[i].layout==SNAP_LAYOUT_TEXT_PHASE_MODEL?(uint32_t)offsetof(State,legacyWindowTextures):
            known[i].layout==SNAP_LAYOUT_WINDOW_SOURCE?(uint32_t)offsetof(State,textPhaseModel):
            known[i].layout==SNAP_LAYOUT_TEXT_ALPHABET?(uint32_t)offsetof(State,legacyWindowSourceGeometry):
            known[i].layout==SNAP_LAYOUT_STUDIO_NOVA?(uint32_t)offsetof(State,textAlphabetTail):
            known[i].layout==SNAP_LAYOUT_WORLD_PROFILES?(uint32_t)offsetof(State,studioNovaControls):
            known[i].layout==SNAP_LAYOUT_THERMAL_PROFILES?(uint32_t)offsetof(State,worldSourceControls):
            known[i].layout==SNAP_LAYOUT_ATELIER?(uint32_t)offsetof(State,thermalSourceControls):
            known[i].layout==SNAP_LAYOUT_KINETIC?(uint32_t)offsetof(State,atelierControls):
            known[i].layout==SNAP_LAYOUT_OBSERVATORY?(uint32_t)offsetof(State,kineticControls):
            known[i].layout==SNAP_LAYOUT_CORONA?(uint32_t)offsetof(State,observatoryControls):
            known[i].layout==SNAP_LAYOUT_NOVA_OPTICS?(uint32_t)offsetof(State,coronaControls):
            known[i].layout==SNAP_LAYOUT_BURST_CONTROLS?(uint32_t)offsetof(State,novaOptics):
            known[i].layout==SNAP_LAYOUT_ELECTRICAL_ARCS?(uint32_t)offsetof(State,burstControls):
            known[i].layout==SNAP_LAYOUT_PROMPT_PRESENTATION?(uint32_t)offsetof(State,electricalArcs):
            known[i].layout==SNAP_LAYOUT_COLOR_FIELDS?(uint32_t)offsetof(State,promptPresentation):
            (known[i].layout==SNAP_LAYOUT_MESH_SUBDIVISION||known[i].layout==SNAP_LAYOUT_AGGREGATE_REEMIT)?(uint32_t)offsetof(State,fieldControls):
            known[i].layout==SNAP_LAYOUT_MATERIAL_HEAT?(uint32_t)offsetof(State,aggregateProvenance):
            known[i].layout==SNAP_LAYOUT_LATENT_HEAT?(uint32_t)offsetof(State,materialHeat):
            known[i].layout==SNAP_LAYOUT_HYDRAULIC_HEAT?(uint32_t)offsetof(State,latentHeat):
            known[i].layout==SNAP_LAYOUT_SURFACE_POSE?(uint32_t)offsetof(State,waterLinkHeatCapacity):
            known[i].layout==SNAP_LAYOUT_ANGULAR_HISTORY?(uint32_t)offsetof(State,surfacePoses):
            known[i].layout==SNAP_LAYOUT_ANGULAR_FLUID?(uint32_t)offsetof(State,angularHistory):
            known[i].layout==SNAP_LAYOUT_FLUID_HISTORY?(uint32_t)offsetof(State,angularFluids):
            known[i].layout==SNAP_LAYOUT_SURFACE_FLUID?(uint32_t)offsetof(State,fluidHistory):
            known[i].layout==SNAP_LAYOUT_FLOAT_HULLS?(uint32_t)offsetof(State,surfaceFluids):
            known[i].layout==SNAP_LAYOUT_TEXT_IDENTITIES?(uint32_t)offsetof(State,floatHulls):
            known[i].layout==SNAP_LAYOUT_FLOW_THICKNESS?(uint32_t)offsetof(State,nextClusterIdentity):
            known[i].layout==SNAP_LAYOUT_FOAM_TRANSPORT?(uint32_t)offsetof(State,flowThickness):
            known[i].layout==SNAP_LAYOUT_TRIGGER_FORMULAS?(uint32_t)offsetof(State,foamVelocity):
            known[i].layout==SNAP_LAYOUT_CELL_ART?(uint32_t)offsetof(State,triggerFormulas):
            known[i].layout==SNAP_LAYOUT_THERMAL_LINK?(uint32_t)offsetof(State,cellArt):
            known[i].layout==SNAP_LAYOUT_THERMAL_TRANSFER?(uint32_t)offsetof(State,thermalLinks):
            known[i].layout==SNAP_LAYOUT_THERMAL?(uint32_t)offsetof(State,thermalTransfers):
            known[i].layout==SNAP_LAYOUT_WATER_REEMIT?(uint32_t)offsetof(State,thermalCells):
            known[i].layout==SNAP_LAYOUT_WATER_LINK?(uint32_t)offsetof(State,sprayReentrained):
            known[i].layout==SNAP_LAYOUT_WATER_TRANSFER?(uint32_t)offsetof(State,waterLinks):
            known[i].layout==SNAP_LAYOUT_SURFACE_WATER?(uint32_t)offsetof(State,waterTransfers):
            known[i].layout==SNAP_LAYOUT_SPRAY_PARTICLES?(uint32_t)offsetof(State,surfaceWater):
            known[i].layout==SNAP_LAYOUT_FLOW_SPRAY?(uint32_t)offsetof(State,sprayParticles):
            known[i].layout==SNAP_LAYOUT_FLOW_SINK?(uint32_t)offsetof(State,flowSprays):
            known[i].layout==SNAP_LAYOUT_FLOW_SURFACE?(uint32_t)offsetof(State,flowSinks):
            known[i].layout==SNAP_LAYOUT_FLOW?(uint32_t)offsetof(State,flowSurfaces):
            known[i].layout==SNAP_LAYOUT_REPEAT_EDIT?(uint32_t)offsetof(State,flows):
            known[i].layout==SNAP_LAYOUT_EDITOR_REDO?(uint32_t)offsetof(State,repeatEdit):
            known[i].layout==SNAP_LAYOUT_NAMED_REGISTERS?(uint32_t)offsetof(State,editorRedo):
            known[i].layout==SNAP_LAYOUT_VIM_REGISTER?(uint32_t)offsetof(State,namedRegisters):
            known[i].layout==SNAP_LAYOUT_VIM_OPERATOR?(uint32_t)offsetof(State,vimRegister):
            known[i].layout==SNAP_LAYOUT_VIM_COUNT?(uint32_t)offsetof(State,vimOperator):
            known[i].layout==SNAP_LAYOUT_PATH_ACTORS?(uint32_t)offsetof(State,vimCount):
            known[i].layout==SNAP_LAYOUT_FOAM?(uint32_t)offsetof(State,pathActors):
            known[i].layout==SNAP_LAYOUT_FLOAT_BODIES?(uint32_t)offsetof(State,foam):
            known[i].layout==SNAP_LAYOUT_SURFACE_WAVES?(uint32_t)offsetof(State,floatBodies):
            known[i].layout==SNAP_LAYOUT_PARTICLE_MOTION?(uint32_t)offsetof(State,surfaceWaves):
            known[i].layout==SNAP_LAYOUT_BIRTH_FRAME?(uint32_t)offsetof(State,emitterMotions):
            known[i].layout==SNAP_LAYOUT_GEOMETRY?(uint32_t)offsetof(State,birthOrientations):(uint32_t)offsetof(State,geometry);
        if(known[i].schema==schema&&expected==payloadBytes){selected=known[i].layout;matches++;}
    }
    return matches==1?selected:SNAP_LAYOUT_INVALID;
}
/* Stable individual identity is unique across airborne and deposited ownership.
 * A bounded hash set is used only on restore, never per-frame validation. Zero is
 * already rejected by state validation and therefore denotes an empty bucket. */
static int snapshotIndividualIdentitiesValid(const State*s) {
    uint32_t ids[4096]={0};
    for(int family=0;family<2;family++) {
        int count=family?NR_DEPOSITS:NR_MAX_PARTICLES;
        for(int i=0;i<count;i++) {
            int used=family?s->deposits[i].used:s->particles[i].state;
            if(!used)continue;
            uint32_t id=family?s->deposits[i].id:s->particles[i].id;
            uint32_t slot=nrHash(id)&4095u;
            while(ids[slot]) {
                if(ids[slot]==id)return 0;
                slot=(slot+1u)&4095u;
            }
            ids[slot]=id;
        }
    }
    return 1;
}
static int snapshotSourceSemanticsValid(const State*s,SnapshotLayout layout) {
    if(!snapshotIndividualIdentitiesValid(s))return 0;
    if(layout==SNAP_LAYOUT_LOCAL) {
        /* These binding families and their effects were added by Contracts 7. */
        for(int i=0;i<NR_VALUES;i++)if(s->values[i].used&&s->values[i].bindingFamily>4)return 0;
    } else if(layout==SNAP_LAYOUT_CONTRACTS7) {
        /* Incoming schema 03 predates local intent-payload predicates and actions. */
        for(int i=0;i<NR_TRIGGERS;i++)if(s->triggers[i].used) {
            const Trigger*t=&s->triggers[i];if(t->source==NR_TRIGGER_SOURCE_INTENT_VALUE)return 0;
            for(int n=0;n<t->conditionCount;n++)if(t->conditions[n].kind==4)return 0;
        }
        for(int i=0;i<NR_STYLE_RULES;i++)if(s->styleRules[i].used) {
            const Trigger*t=&s->styleRules[i].guard;if(t->source==NR_TRIGGER_SOURCE_INTENT_VALUE)return 0;
            for(int n=0;n<t->conditionCount;n++)if(t->conditions[n].kind==4)return 0;
        }
    }
    return 1;
}
static void migrateLocalState(State*dst,const uint8_t*payload) {
    const size_t split=offsetof(State,triggers)+sizeof(((State*)0)->triggers);
    const size_t expandedTail=offsetof(State,mesh);
    const size_t tailBytes=offsetof(State,geometry)-expandedTail;
    memset(dst,0,offsetof(State,dynamicPrompt));
    memcpy(dst,payload,split);
    memcpy((uint8_t*)dst+expandedTail,payload+split,tailBytes);
}
int nrLoad(NrContext*c,const void*s,uint32_t len) {
    if(!valid(c)||!s||len<24u||!nrExternalOutput(c,s,len))return -1;
    /* A restore validates, then promotes without the post-command pipeline: never settled (TRANSACTIONS.md). */
    c->settled=0;
    c->error[0]=0;const uint8_t*p=s;
    if(memcmp(p,SNAP_MAGIC,8)||u32read(p+8)!=NR_ABI_VERSION)return -1;
    uint32_t schema=u32read(p+12),payloadBytes=u32read(p+16);
    if(payloadBytes>len-24u||payloadBytes!=len-24u)return -1;
    /* Only actually published source layouts, never a guessed future prefix. */
    const struct {uint32_t schema,prefix;} dynamicLayouts[]={
        {0x20261073u,27447632u},{0x20261073u,30475272u},
        {0x20261075u,27447632u},{0x20261076u,30475336u},
        {0x20261077u,30475336u},{0x20261077u,30478240u},
        {0x20261078u,27447632u},{0x20261078u,30478240u},
        {0x20261079u,27447632u},{0x20261079u,30478240u},
        {0x20261081u,27447632u},{0x20261081u,30478240u},
        {0x20261083u,27447632u},{0x20261083u,30478240u},
        {0x20261084u,27447632u},{0x20261084u,30478240u},
        {0x20261085u,30485152u},{0x20261086u,30478240u},
        {0x20261087u,30485304u},{0x20261088u,30488792u},
        {0x20261089u,30489248u},{0x20261090u,30489392u},{0x20261091u,30494208u},{0x20261092u,30494248u},{0x20261093u,30499432u},{0x20261094u,30499728u},
        {NR_STATE_SCHEMA_SCENE_ART_CLOCK,30499744u},
        {NR_STATE_SCHEMA_PROMPT_APPEARANCE,30502400u},
        {NR_STATE_SCHEMA_OCCLUSION_CONTROLS,30502416u},
        {NR_STATE_SCHEMA,(uint32_t)offsetof(State,dynamicPrompt)}
    };
    uint32_t modelBytes=0,modalBytes=0;
    if(schema>=NR_STATE_SCHEMA_SOURCE_MODAL&&schema<=NR_STATE_SCHEMA){uint32_t modalFixed=schema==NR_STATE_SCHEMA_SOURCE_MODAL?30499432u:schema==NR_STATE_SCHEMA_CAMERA_CONTROLS?30499728u:schema==NR_STATE_SCHEMA_SCENE_ART_CLOCK?30499744u:schema==NR_STATE_SCHEMA_PROMPT_APPEARANCE?30502400u:schema==NR_STATE_SCHEMA_OCCLUSION_CONTROLS?30502416u:(uint32_t)offsetof(State,dynamicPrompt);if(payloadBytes<modalFixed)return -1;uint64_t n=(uint64_t)u32read(p+24+offsetof(State,sourceModal)+offsetof(SourceModalState,scalars))*4;if(n>payloadBytes-modalFixed)return -1;modalBytes=(uint32_t)n;}
    if(schema>=NR_STATE_SCHEMA_SOURCE_MODEL&&schema<=NR_STATE_SCHEMA){
        uint32_t modelFixed=schema==NR_STATE_SCHEMA_SOURCE_MODEL?30489392u:schema==NR_STATE_SCHEMA_SOURCE_STAGE_SCENE?30494208u:schema==NR_STATE_SCHEMA_OBSERVATORY_OVERLAY?30494248u:schema==NR_STATE_SCHEMA_SOURCE_MODAL?30499432u:schema==NR_STATE_SCHEMA_CAMERA_CONTROLS?30499728u:schema==NR_STATE_SCHEMA_SCENE_ART_CLOCK?30499744u:schema==NR_STATE_SCHEMA_PROMPT_APPEARANCE?30502400u:schema==NR_STATE_SCHEMA_OCCLUSION_CONTROLS?30502416u:(uint32_t)offsetof(State,dynamicPrompt);
        if(payloadBytes<modelFixed)return -1;
        uint32_t count=u32read(p+24+offsetof(State,sourceModel));uint64_t bytes=(uint64_t)count*sizeof(NrModelTriangle);
        if(bytes>payloadBytes-modelFixed)return -1;modelBytes=(uint32_t)bytes;
    }
    int dynamic=0;unsigned matches=0;uint32_t dynamicFixed=0;
    for(unsigned i=0;i<sizeof(dynamicLayouts)/sizeof(dynamicLayouts[0]);i++){
        if(schema!=dynamicLayouts[i].schema)continue;
        dynamic=1;uint32_t prefix=dynamicLayouts[i].prefix;
        if(payloadBytes>=prefix&&(uint64_t)modelBytes+modalBytes<=payloadBytes-prefix&&nrPromptPayloadShape(p+24+prefix,payloadBytes-prefix-modelBytes-modalBytes,schema)){dynamicFixed=prefix;matches++;}
    }
    if(dynamic&&matches!=1)return -1;
    SnapshotLayout layout=dynamic?(dynamicFixed==27447632u?SNAP_LAYOUT_PROMPT_CAPACITY:SNAP_LAYOUT_WINDOW_POOLS):snapshotLayout(schema,payloadBytes);
    if(layout==SNAP_LAYOUT_INVALID||nrCrc(p+24,payloadBytes)!=u32read(p+20))return -1;
    if(layout==SNAP_LAYOUT_LOCAL)migrateLocalState(&c->trial,p+24);
    else {
        uint32_t fixed=(uint32_t)offsetof(State,dynamicPrompt);
        if(dynamic&&payloadBytes<dynamicFixed)return -1;
        memset(&c->trial,0,fixed);
        if(layout==SNAP_LAYOUT_WINDOW_APPLICATION||layout==SNAP_LAYOUT_ORIGINAL_WINDOW_POOLS||layout==SNAP_LAYOUT_ORIGINAL_CAMERA||layout==SNAP_LAYOUT_ATELIER_WINDOWS||layout==SNAP_LAYOUT_ATELIER_APP_PARTICLES){
            memcpy(&c->trial,p+24,15388552u);
            memcpy(&c->trial.windowApplication,p+24+15388552u,sizeof(WindowApplication));
            if(layout==SNAP_LAYOUT_ORIGINAL_WINDOW_POOLS||layout==SNAP_LAYOUT_ORIGINAL_CAMERA||layout==SNAP_LAYOUT_ATELIER_WINDOWS||layout==SNAP_LAYOUT_ATELIER_APP_PARTICLES)memcpy(&c->trial.windows,p+24+15408936u,18416192u-15408936u);
            if(layout==SNAP_LAYOUT_ORIGINAL_CAMERA||layout==SNAP_LAYOUT_ATELIER_WINDOWS||layout==SNAP_LAYOUT_ATELIER_APP_PARTICLES)memcpy(&c->trial.originalCamera,p+24+18416192u,sizeof(OriginalCamera));
            if(layout==SNAP_LAYOUT_ATELIER_WINDOWS||layout==SNAP_LAYOUT_ATELIER_APP_PARTICLES)memcpy(c->trial.atelierWindows,p+24+18419096u,sizeof(c->trial.atelierWindows));
            if(layout==SNAP_LAYOUT_ATELIER_APP_PARTICLES)memcpy(&c->trial.atelierApplicationParticles,p+24+18426008u,sizeof(AtelierControls));
        }else memcpy(&c->trial,p+24,dynamic?dynamicFixed:payloadBytes);
        if(dynamic&&nrPromptLoadPayload(&c->trial,p+24+dynamicFixed,payloadBytes-dynamicFixed-modelBytes-modalBytes,schema)<0)return -1;
        if(schema>=NR_STATE_SCHEMA_SOURCE_MODEL&&schema<=NR_STATE_SCHEMA&&nrModelLoadPayload(&c->trial,p+24+payloadBytes-modelBytes-modalBytes,modelBytes)<0)return -1;
        if(schema>=NR_STATE_SCHEMA_SOURCE_MODAL&&schema<=NR_STATE_SCHEMA&&nrModalLoadPayload(&c->trial,p+24+payloadBytes-modalBytes,modalBytes)<0)return -1;
    }
    if(layout<SNAP_LAYOUT_ORIGINAL_WINDOW_POOLS){
        State*s=&c->trial;
        memcpy(s->windows,s->legacyWindows,sizeof(s->legacyWindows));
        memcpy(s->textIdentities,s->legacyTextIdentities,13*sizeof(TextIdentityRun));
        memcpy(s->textIdentities+1+NR_MAX_WINDOWS,s->legacyTextIdentities+13,12*sizeof(TextIdentityRun));
        memcpy(s->windowSourceGeometry,s->legacyWindowSourceGeometry,sizeof(s->legacyWindowSourceGeometry));
        memcpy(s->windowPresentation,s->legacyWindowPresentation,sizeof(s->legacyWindowPresentation));
        memcpy(s->windowSourceOrder,s->legacyWindowSourceOrder,sizeof(s->legacyWindowSourceOrder));
        s->windowTextures.count=s->legacyWindowTextures.count;s->windowTextures.reserved=s->legacyWindowTextures.reserved;
        memcpy(s->windowTextures.windows,s->legacyWindowTextures.windows,sizeof(s->legacyWindowTextures.windows));
        memcpy(s->windowTextures.cells,s->legacyWindowTextures.cells,sizeof(s->legacyWindowTextures.cells));
        memcpy(s->windowContent,s->legacyWindowContent,sizeof(s->legacyWindowContent));
    }
    if(!dynamic){
        int legacyPrompt=schema<NR_STATE_SCHEMA_PROMPT_CAPACITY||layout==SNAP_LAYOUT_ORIGINAL_WINDOW_POOLS||layout==SNAP_LAYOUT_ORIGINAL_CAMERA||layout==SNAP_LAYOUT_ATELIER_WINDOWS||layout==SNAP_LAYOUT_ATELIER_APP_PARTICLES;
        uint32_t needed=nrPromptLegacyRequired(&c->trial,legacyPrompt?NR_STATE_SCHEMA_WINDOW_TEXTURE:schema);
        if(needed>NR_MAX_PROMPT||!nrPromptRequire(&c->trial,needed))return -1;
        if(!(legacyPrompt?nrPromptStoragePromote(&c->trial):nrPromptPromote70(&c->trial)))return -1;
    }
    if(c->trial.schema!=schema||!nrCountedValidState(c,&c->trial)||!nrValidateIntentPayloads(c,&c->trial)||!nrValidateCharacterRules(c,&c->trial)||!nrValidateCharacterRegions(c,&c->trial)||!snapshotSourceSemanticsValid(&c->trial,layout)||!nrCheckPending(c,&c->trial))return -1;
    /* Promotion occurs only after the source layout and semantics validate.
     * Input bytes and all fields in the decoded state remain unchanged. */
    if(layout<SNAP_LAYOUT_FOAM)c->trial.foam.meshGeneration=c->trial.geometry.meshGeneration;
    nrFlowSprayPromote(&c->trial);
    if(layout<SNAP_LAYOUT_SURFACE_POSE)for(int i=0;i<NR_SURFACES;i++)if(c->trial.angularFluids[i].used){c->trial.surfacePoses[i].used=1;c->trial.surfacePoses[i].orientation[3]=1;}
    if(layout<SNAP_LAYOUT_PROMPT_PRESENTATION)c->trial.promptPresentation.ambiguous=1;
    if((schema<NR_STATE_SCHEMA_ATELIER_APP_PARTICLES||(dynamic&&dynamicFixed<30485304u))&&c->trial.windowApplication.enabled&&!c->trial.windowApplication.eventCount&&c->trial.windowApplication.eventSerial==0)c->trial.windowApplication.eventSerial=6;
    c->trial.schema=NR_STATE_SCHEMA;nrPromptStorageMirror(&c->trial);
    if(layout<SNAP_LAYOUT_SURFACE_POSE&&!nrBuildGeometry(&c->trial,&c->trial.geometry.index))return -1;
    if(!nrSyncTextIdentities(&c->trial))return -1;
    nrStateCopy(&c->state,&c->trial);
    nrCacheCharacterRules(c);
    nrCacheCharacterRegions(c);
    c->characterFrameValid=0;
    return 0;
}
int nrParticle(const NrContext*c,uint32_t i,int32_t*w,uint32_t cap) {
    if(!valid(c)||i>=NR_MAX_PARTICLES||!w||cap<12)return -1;
    const Particle*p=&c->state.particles[i];
    if(!p->state)return 0;
    int32_t out[12]= {
        (int32_t)p->id,(int32_t)p->emitterId,p->state,p->position.x,p->position.y,p->position.z,p->velocity.x,p->velocity.y,p->velocity.z,(int32_t)p->bornStep,(int32_t)(c->state.step-p->bornStep),(int32_t)p->lifeSteps
    };
    memcpy(w,out,sizeof(out));
    return 1;
}
int nrParticleMotion(const NrContext*c,uint32_t i,double*out,uint32_t cap) {
    if(!valid(c)||i>=NR_MAX_PARTICLES||!out||cap<6)return -1;
    Vec3 orientation,angular;
    if(!nrParticlePose(&c->state,(int)i,&orientation,&angular))return 0;
    double values[6]={orientation.x,orientation.y,orientation.z,angular.x,angular.y,angular.z};
    memcpy(out,values,sizeof(values));return 1;
}
/* Bounded JSON writer: no sprintf locale or format-string surface. */
typedef struct {
    char*p;
    uint32_t used,cap;
    int failed;
    uint32_t skip,crc;
    int paged;
}
Writer;
static void put(Writer*w,const char*s) {
    /* Reflected IEEE CRC32, nibble table. Paged output retains a byte window,
     * not a UTF-8 string. Each call still measures the complete formatter. */
    static const uint32_t crc4[16]={
        0x00000000u,0x1db71064u,0x3b6e20c8u,0x26d930acu,
        0x76dc4190u,0x6b6b51f4u,0x4db26158u,0x5005713cu,
        0xedb88320u,0xf00f9344u,0xd6d6a3e8u,0xcb61b38cu,
        0x9b64c2b0u,0x86d3d2d4u,0xa00ae278u,0xbdbdf21cu
    };
    if(w->failed)return;
    if(w->paged) {
        for(;*s;s++) {
            if(w->used==UINT32_MAX) {w->failed=1;return;}
            uint32_t q=w->crc^(uint8_t)*s;
            q=(q>>4)^crc4[q&15u];
            w->crc=(q>>4)^crc4[q&15u];
            if(w->used>=w->skip&&w->used-w->skip<w->cap)
                w->p[w->used-w->skip]=*s;
            w->used++;
        }
        return;
    }
    for(; *s; s++) {
        if(w->used+1>=w->cap) {
            w->failed=1;
            return;
        }
        w->p[w->used++]=*s;
    }
    w->p[w->used]=0;
}
static void integer(Writer*w,int64_t n) {
    char b[32];
    int i=0;
    uint64_t v=n<0?(uint64_t)(-(n+1))+1:(uint64_t)n;
    if(n<0)put(w,"-");
    do {
        b[i++]=(char)('0'+v%10);
        v/=10;
    }
    while(v);
    while(i) {
        char q[2]= {
            b[--i],0
        };
        put(w,q);
    }
}
static void number(Writer*w,double v) {
    int64_t n=(int64_t)(v*1000000+(v<0?-.5:.5));
    if(n<0) {
        put(w,"-");
        n=-n;
    }
    integer(w,n/1000000);
    put(w,".");
    int64_t k=100000;
    for(int i=0; i<6; i++,k/=10) {
        char q[2]= {
            (char)('0'+(n/k)%10),0
        };
        put(w,q);
    }
}
static void exactNumber(Writer*w,double value) {
    char encoded[1200];
    if(nrJsonNumber(value,encoded,sizeof(encoded))<0)w->failed=1;
    else put(w,encoded);
}
static void glyphString(Writer*w,const uint32_t*g,int n) {
    put(w,"\"");
    for(int i=0; i<n; i++) {
        uint32_t v=g[i];
        if(v=='"')put(w,"\\\"");
        else if(v=='\\')put(w,"\\\\");
        else if(v=='\n')put(w,"\\n");
        else if(v=='\r')put(w,"\\r");
        else if(v=='\t')put(w,"\\t");
        else if(v==11)put(w,"\\u000b");
        else if(v==12)put(w,"\\f");
        else if(v<32)put(w," ");
        else {
            char b[5]= {
                0
            };
            if(v<128)b[0]=(char)v;
            else if(v<2048) {
                b[0]=(char)(0xc0|(v>>6));
                b[1]=(char)(0x80|(v&63));
            }
            else if(v<65536) {
                b[0]=(char)(0xe0|(v>>12));
                b[1]=(char)(0x80|((v>>6)&63));
                b[2]=(char)(0x80|(v&63));
            }
            else {
                b[0]=(char)(0xf0|(v>>18));
                b[1]=(char)(0x80|((v>>12)&63));
                b[2]=(char)(0x80|((v>>6)&63));
                b[3]=(char)(0x80|(v&63));
            }
            put(w,b);
        }
    }
    put(w,"\"");
}
static void modalGlyphString(Writer*w,const uint32_t*g,int n) {
    put(w,"\"");
    for(int i=0; i<n; i++) {
        uint32_t v=g[i];
        if(v=='"')put(w,"\\\"");
        else if(v=='\\')put(w,"\\\\");
        else if(v=='\n')put(w,"\\n");
        else if(v=='\r')put(w,"\\r");
        else if(v=='\t')put(w,"\\t");
        else if(v==11)put(w,"\\u000b");
        else if(v==12)put(w,"\\f");
        else if(v<32){static const char hex[]="0123456789abcdef";char escaped[]={92,117,48,48,hex[v>>4],hex[v&15],0};put(w,escaped);}
        else {
            char b[5]= {
                0
            };
            if(v<128)b[0]=(char)v;
            else if(v<2048) {
                b[0]=(char)(0xc0|(v>>6));
                b[1]=(char)(0x80|(v&63));
            }
            else if(v<65536) {
                b[0]=(char)(0xe0|(v>>12));
                b[1]=(char)(0x80|((v>>6)&63));
                b[2]=(char)(0x80|(v&63));
            }
            else {
                b[0]=(char)(0xf0|(v>>18));
                b[1]=(char)(0x80|((v>>12)&63));
                b[2]=(char)(0x80|((v>>6)&63));
                b[3]=(char)(0x80|(v&63));
            }
            put(w,b);
        }
    }
    put(w,"\"");
}
static void string(Writer*w,const char*s) {
    put(w,"\"");
    for(; *s; s++) {
        if(*s=='"'||*s=='\\')put(w,"\\");
        char b[2]= {
            *s,0
        };
        if((uint8_t)*s<32)b[0]=' ';
        put(w,b);
    }
    put(w,"\"");
}
static void intentPayloadRecord(Writer*w,const State*s,const Intent*q){
    if(q->messageId)return;
    const IntentPayload*p=&s->intentPayloads[q-s->intents];
    put(w,",\"origin\":\"host\"");
    if(p->length){put(w,",\"payload\":");put(w,p->json);}
}
static void intentRecord(Writer*w,const State*s,const Intent*q) {
    put(w,"{\"id\":");integer(w,(int64_t)q->id);put(w,",\"event\":");string(w,q->event);
    put(w,",\"messageId\":");integer(w,(int64_t)q->messageId);put(w,",\"actionId\":");integer(w,(int64_t)q->actionId);
    put(w,",\"messageSequence\":");integer(w,(int64_t)q->messageSequence);put(w,",\"atUs\":");integer(w,(int64_t)q->atUs);
    put(w,",\"value\":");number(w,q->value);intentPayloadRecord(w,s,q);put(w,"}");
}
static const Intent*intentById(const State*s,uint64_t id) {
    if(!id)return 0;
    for(int i=0;i<NR_INTENTS;i++)if(s->intents[i].used&&s->intents[i].id==id)return &s->intents[i];
    return 0;
}
static void vec(Writer*w,Vec3 v) {
    put(w,"[");
    number(w,v.x);
    put(w,",");
    number(w,v.y);
    put(w,",");
    number(w,v.z);
    put(w,"]");
}
static const char*bindingFamilies[]={"","material","emitter","widget","camera","window","text","area","floor","state","node","indicator","prompt","environment","field","flow","surface","surface-wave","float-body","surface-foam","mesh","triangle","cell-art","accessibility","electrical-arc"};
static void heatRecord(Writer*w,const HeatReservoir*r,int id){
    put(w,"{\"id\":");integer(w,id);put(w,",\"capacity\":");number(w,r->capacity);put(w,",\"temperature\":");number(w,r->temperature);put(w,",\"energy\":");number(w,r->capacity*r->temperature);put(w,",\"contactFraction\":");number(w,r->contactFraction);put(w,",\"conductance\":");number(w,r->conductance);put(w,"}");
}
static void promptSourceOptions(Writer*w,const NrPromptSourceOptions*o){
    static const char*borders[]={"none","rounded","square","double","heavy"};
    put(w,"{\"alpha\":");number(w,o->alpha);
    put(w,",\"background\":");integer(w,o->background);
    put(w,",\"foreground\":");integer(w,o->foreground);
    put(w,",\"accent\":");integer(w,o->accent);
    put(w,",\"selectionColor\":");integer(w,o->selectionColor);
    put(w,",\"border\":");string(w,borders[o->border]);
    put(w,",\"paddingX\":");integer(w,o->paddingX);put(w,",\"paddingY\":");integer(w,o->paddingY);
    put(w,",\"margin\":");integer(w,o->margin);
    put(w,",\"minRows\":");integer(w,o->minRows);put(w,",\"maxRows\":");integer(w,o->maxRows);
    put(w,",\"inlineRows\":");integer(w,o->inlineRows);put(w,",\"inlineWidth\":");integer(w,o->inlineWidth);
    put(w,",\"lineNumbers\":");put(w,o->lineNumbers?"true":"false");
    put(w,",\"active\":");put(w,o->active?"true":"false");
    put(w,",\"selected\":");put(w,o->selected?"true":"false");
    put(w,",\"hueStep\":");number(w,o->hueStep);put(w,",\"hueSpeed\":");number(w,o->hueSpeed);
    put(w,",\"huePeriodMs\":");integer(w,o->huePeriodMs);put(w,",\"maxChars\":");integer(w,o->maxChars);
    put(w,"}");
}
static void materialPatternRecord(Writer*w,int id,const NrSourceMaterialSampler*q){
    static const char*kinds[]={"solid","linear","diagonal","wave","rotating-linear","plasma","concentric","moire","aurora","interference","chevrons","diamond"};
    static const char*focus[]={"none","row","column","radial","diagonal-band"};
    static const char*rotation[]={"fixed","continuous","pendulum"};
    static const char*wrap[]={"loop","mirror","hard-stops"};
    static const char*interpolation[]={"linear","eased"};
    static const char*color[]={"palette","hsv","rgb-sine"};
    put(w,"{\"id\":");integer(w,id);
    put(w,",\"kind\":");string(w,kinds[q->pattern]);
    put(w,",\"focusMode\":");string(w,focus[q->focusMode]);
#define PATTERN_INT(member) put(w,",\"" #member "\":");integer(w,q->member)
    PATTERN_INT(focusXQ8);PATTERN_INT(focusYQ8);PATTERN_INT(periodMs);
    PATTERN_INT(saturationMilli);PATTERN_INT(brightnessMilli);PATTERN_INT(speedFalloffMilli);
    PATTERN_INT(saturationFalloffMilli);PATTERN_INT(brightnessFalloffMilli);PATTERN_INT(cellAspectMilli);
    PATTERN_INT(scaleQ8);PATTERN_INT(angleMilliDegrees);PATTERN_INT(pivotXQ8);PATTERN_INT(pivotYQ8);
    PATTERN_INT(rotationPeriodMs);PATTERN_INT(swingMilliDegrees);PATTERN_INT(phase1024);PATTERN_INT(seed);
    PATTERN_INT(baseRgb);PATTERN_INT(inkRgb);PATTERN_INT(hueOffsetDegrees);
    PATTERN_INT(originXCells);PATTERN_INT(originYCells);PATTERN_INT(waveAmplitudeMilli);
#undef PATTERN_INT
    put(w,",\"rotationMode\":");string(w,rotation[q->rotationMode]);
    put(w,",\"gradientWrap\":");string(w,wrap[q->gradientWrap]);
    put(w,",\"interpolation\":");string(w,interpolation[q->interpolation]);
    put(w,",\"colorMode\":");string(w,color[q->colorMode]);
    put(w,",\"motion\":");put(w,q->motion?"true":"false");
    put(w,",\"reverse\":");put(w,q->reverse?"true":"false");
    put(w,",\"palette\":[");
    for(uint32_t i=0;i<q->paletteCount;i++){if(i)put(w,",");integer(w,q->palette[i]);}
    put(w,"]}");
}
static void scenicVector(Writer*w,const int32_t*world,const int32_t*detail){
    static const char*worldNames[]={"width","height","scene","cameraX","cameraY","cameraZ","yaw","pitch","roll","fov","projection","span","flow","travel","seed","redshift","discTilt","detail","waterAlpha","background","ink","accent","secondary","sampling"};
    static const int worldScales[]={1,1,1,256,256,256,256,256,256,256,1,256,1000,256,1,1000,256,1,1000,1,1,1,1,1};
    static const char*detailNames[]={"waveHeight","wavelength","windAngle","crossSwell","choppiness","foam","waveSpeed","joinRiver"};
    static const int detailScales[]={256,256,256,1000,1000,1000,1000,1};
    put(w,"\"worldQ\":[");for(int i=0;i<24;i++){if(i)put(w,",");integer(w,world[i]);}
    put(w,"],\"detailQ\":[");for(int i=0;i<8;i++){if(i)put(w,",");integer(w,detail[i]);}
    put(w,"],\"controls\":{");
    for(int i=0;i<24;i++){if(i)put(w,",");string(w,worldNames[i]);put(w,":");exactNumber(w,(double)world[i]/worldScales[i]);}
    put(w,"},\"detail\":{");
    for(int i=0;i<8;i++){if(i)put(w,",");string(w,detailNames[i]);put(w,":");exactNumber(w,(double)detail[i]/detailScales[i]);}
    put(w,"}");
}
static void cameraControlsInfo(Writer*w,const State*s){
    const CameraControls*q=&s->cameraControls;
    const char*rigs[]={"orbit","head","dolly","crane","follow","spacecraft"};
    const char*modes[]={"orbit","pan","fly"};
    const char*actions[]={"disabled","orbit-x","orbit-y","orbit-z","pan-x","pan-y","pan-z","look-x","look-y","look-z"};
    put(w,"{\"enabled\":");put(w,q->configured?"true":"false");
    put(w,",\"rig\":");string(w,rigs[q->rig]);put(w,",\"mode\":");string(w,modes[q->mode]);
    put(w,",\"inputTarget\":");string(w,q->inputTarget?"head":"body");
    put(w,",\"inputAxes\":{");
    for(int i=0;i<3;i++){if(i)put(w,",");string(w,(const char*[]){"x","y","z"}[i]);put(w,":{\"action\":");string(w,actions[q->axes[i].action]);put(w,",\"sensitivity\":");number(w,q->axes[i].sensitivity);put(w,",\"enabled\":");put(w,q->axes[i].enabled?"true":"false");put(w,",\"invert\":");put(w,q->axes[i].invert?"true":"false");put(w,"}");}
    put(w,"},\"head\":{\"position\":");vec(w,q->headPosition);put(w,",\"rotation\":");vec(w,q->headRotation);
    put(w,"},\"crane\":{\"pivot\":");vec(w,q->cranePivot);put(w,",\"boom\":");vec(w,q->craneBoom);
    put(w,"},\"follow\":{\"target\":{");
    if(q->followKind){put(w,"\"kind\":\"node\",\"id\":");integer(w,q->followId);}else{put(w,"\"kind\":\"point\",\"point\":");vec(w,q->followPoint);}
    put(w,"},\"offset\":");vec(w,q->followOffset);put(w,",\"track\":");put(w,q->followTrack?"true":"false");
    put(w,"},\"anchor\":");if(q->anchorEnabled)vec(w,q->anchor);else put(w,"null");put(w,"}");
}
static void sceneArtInfo(Writer*w,const State*s){
    if(!s->sceneArt.used){put(w,"null");return;}
    static const char*names[]={"pearl-cascade","copper-causeway","red-shift","tidal-glass","silt"};
    put(w,"{\"scene\":");string(w,names[s->sceneArt.world[NR_WORLD_SCENE]]);
    put(w,",\"hasWorldDetail\":");put(w,s->sceneArt.hasWorldDetail?"true":"false");
    put(w,",\"timeMs\":");if(s->sceneArtClock.enabled)exactNumber(w,s->sceneArtClock.timeMs);else put(w,"null");
    put(w,",");scenicVector(w,s->sceneArt.world,s->sceneArt.detail);
    put(w,",\"effective\":");int width,height;nrSceneViewport(s,&width,&height);NrScenicArtConfig config;
    if(nrSceneArtEffective(s,width,height,&config)){
        put(w,"{\"width\":");integer(w,width);put(w,",\"height\":");integer(w,height);
        put(w,",\"timeMs\":");exactNumber(w,s->sceneArtClock.enabled?s->sceneArtClock.timeMs:(double)(s->timeUs/1000));
        put(w,",");scenicVector(w,config.world,config.detail);put(w,"}");
    }else put(w,"null");
    put(w,"}");
}
static void sourceModelInfo(Writer*w,const State*s){
    put(w,"{\"triangles\":");integer(w,s->sourceModel.count);put(w,",\"view\":");
    if(!s->sourceModel.view.used)put(w,"null");
    else{put(w,"{");scenicVector(w,s->sourceModel.view.world,s->sourceModel.view.detail);put(w,"}");}
    put(w,"}");
}
_Static_assert(sizeof(SourceStageScene)==4816u,"Stage scene appendix");
_Static_assert(offsetof(State,sourceStageScene)==30489392u,"preserved90 fixed prefix");
_Static_assert(sizeof(OriginalObservatoryOverlay)==40u,"originalObservatoryOverlay appendix");
_Static_assert(offsetof(State,observatoryOverlay)==30494208u,"preserved91 fixed prefix");
_Static_assert(sizeof(SourceModalState)==5184u,"sourceModal appendix");
_Static_assert(offsetof(State,sourceModal)==30494248u,"preserved92 fixed prefix");
_Static_assert(offsetof(State,cameraControls)==30499432u,"preserved93 fixed prefix");
_Static_assert(offsetof(State,sceneArtClock)==30499728u,"preserved94 fixed prefix");
_Static_assert(sizeof(SceneArtClock)==16u,"scenic clock95 appendix");
_Static_assert(offsetof(State,promptAppearance)==30499744u,"preserved scenic clock prefix");
_Static_assert(offsetof(State,occlusionControls)==30499744u+sizeof(PromptAppearance)&&offsetof(State,occlusionControls)==30502400u,"preserved prompt appearance96 prefix");
_Static_assert(sizeof(OcclusionControls)==16u,"occlusion controls97 wire size");
_Static_assert(offsetof(State,promptSourceLayer)==30502400u+sizeof(OcclusionControls)&&offsetof(State,promptSourceLayer)==30502416u,"preserved occlusion controls97 prefix");
_Static_assert(sizeof(PromptSourceLayer)==56u,"prompt source layer98 wire size");
_Static_assert(offsetof(State,dynamicPrompt)==30502416u+sizeof(PromptSourceLayer),"prompt source layer98 fixed prefix");
static void modalText(Writer*w,const State*s,SourceModalString q){modalGlyphString(w,q.count?s->modalScalars+q.offset:0,(int)q.count);}
static void sourceModalInfo(Writer*w,const State*s){const SourceModalState*q=&s->sourceModal;const SourceModalEntry*top=q->depth?&q->entries[q->depth-1]:0;
 put(w,"{\"depth\":");integer(w,q->depth);put(w,",\"revision\":");integer(w,q->revision);put(w,",\"blocking\":");put(w,nrModalBlocking(s)?"true":"false");put(w,",\"associated\":");put(w,nrModalAssociationReady(s)?"true":"false");put(w,",\"workspace\":");modalText(w,s,q->workspace);put(w,",\"context\":");modalText(w,s,top?top->context:q->context);put(w,",\"query\":");modalText(w,s,top?top->query:q->query);put(w,",\"selected\":");integer(w,top?top->selected:q->selected);put(w,",\"entries\":[");
 for(uint32_t i=0;i<q->depth;i++){const SourceModalEntry*e=&q->entries[i];if(i)put(w,",");put(w,"{\"id\":");string(w,e->id);put(w,",\"kind\":");string(w,nrModalKind(e->kind));put(w,",\"title\":");modalText(w,s,e->title);put(w,",\"body\":");modalText(w,s,e->body);put(w,",\"context\":");modalText(w,s,e->context);put(w,",\"query\":");modalText(w,s,e->query);put(w,",\"selected\":");integer(w,e->selected);put(w,",\"atMs\":");exactNumber(w,e->atMs);put(w,",\"dismissible\":");put(w,e->dismissible?"true":"false");put(w,"}");}put(w,"],\"componentIds\":[");for(uint32_t i=0;i<q->ownedCount;i++){if(i)put(w,",");integer(w,q->ownedIds[i]);}put(w,"]}");
}
static void observatoryOverlayInfo(Writer*w,const State*s){
 const OriginalObservatoryOverlay*q=&s->observatoryOverlay;put(w,"{\"enabled\":");put(w,q->enabled?"true":"false");
 if(q->enabled){put(w,",\"kind\":");string(w,(const char*[]){"","text","dag","spatial-menu","warp"}[q->kind]);put(w,",\"flatNavigation\":");put(w,q->flatNavigation?"true":"false");put(w,",\"fallMs\":");number(w,q->fallMs);put(w,",\"hueStep\":");number(w,q->hueStep);put(w,",\"textHueSpeed\":");number(w,q->textHueSpeed);}put(w,"}");
}
static void sourceStageSceneInfo(Writer*w,const State*s){
 const SourceStageScene*q=&s->sourceStageScene;
 put(w,"{\"enabled\":");put(w,q->enabled?"true":"false");put(w,",\"timeMs\":");integer(w,q->timeMs);
 put(w,",\"config\":{\"values\":{");
 if(0)put(w,",");put(w,"\"width\":");integer(w,s->width);
 if(1)put(w,",");put(w,"\"height\":");integer(w,s->height);
 if(2)put(w,",");put(w,"\"pattern\":");integer(w,q->values[2]);
 if(3)put(w,",");put(w,"\"focusMode\":");integer(w,q->values[3]);
 if(4)put(w,",");put(w,"\"focusX\":");integer(w,q->values[4]);
 if(5)put(w,",");put(w,"\"focusY\":");integer(w,q->values[5]);
 if(6)put(w,",");put(w,"\"periodMs\":");integer(w,q->values[6]);
 if(7)put(w,",");put(w,"\"saturation\":");integer(w,q->values[7]);
 if(8)put(w,",");put(w,"\"brightness\":");integer(w,q->values[8]);
 if(9)put(w,",");put(w,"\"speedFalloff\":");integer(w,q->values[9]);
 if(10)put(w,",");put(w,"\"saturationFalloff\":");integer(w,q->values[10]);
 if(11)put(w,",");put(w,"\"brightnessFalloff\":");integer(w,q->values[11]);
 if(12)put(w,",");put(w,"\"cellAspect\":");integer(w,q->values[12]);
 if(13)put(w,",");put(w,"\"scale\":");integer(w,q->values[13]);
 if(14)put(w,",");put(w,"\"angle\":");integer(w,q->values[14]);
 if(15)put(w,",");put(w,"\"pivotX\":");integer(w,q->values[15]);
 if(16)put(w,",");put(w,"\"pivotY\":");integer(w,q->values[16]);
 if(17)put(w,",");put(w,"\"rotationPeriodMs\":");integer(w,q->values[17]);
 if(18)put(w,",");put(w,"\"rotationMode\":");integer(w,q->values[18]);
 if(19)put(w,",");put(w,"\"swing\":");integer(w,q->values[19]);
 if(20)put(w,",");put(w,"\"phase\":");integer(w,q->values[20]);
 if(21)put(w,",");put(w,"\"pixelMode\":");integer(w,q->values[21]);
 if(22)put(w,",");put(w,"\"seed\":");integer(w,q->values[22]);
 if(23)put(w,",");put(w,"\"baseColor\":");integer(w,q->values[23]);
 if(24)put(w,",");put(w,"\"inkColor\":");integer(w,q->values[24]);
 if(25)put(w,",");put(w,"\"paletteCount\":");integer(w,q->values[25]);
 if(26)put(w,",");put(w,"\"gradientWrap\":");integer(w,q->values[26]);
 if(27)put(w,",");put(w,"\"interpolation\":");integer(w,q->values[27]);
 if(28)put(w,",");put(w,"\"colorMode\":");integer(w,q->values[28]);
 if(29)put(w,",");put(w,"\"hueOffset\":");integer(w,q->values[29]);
 if(30)put(w,",");put(w,"\"stars\":");integer(w,q->values[30]);
 if(31)put(w,",");put(w,"\"starDensity\":");integer(w,q->values[31]);
 if(32)put(w,",");put(w,"\"starMinMs\":");integer(w,q->values[32]);
 if(33)put(w,",");put(w,"\"starRangeMs\":");integer(w,q->values[33]);
 if(34)put(w,",");put(w,"\"starDuty\":");integer(w,q->values[34]);
 if(35)put(w,",");put(w,"\"starPeak\":");integer(w,q->values[35]);
 if(36)put(w,",");put(w,"\"starGlyphCount\":");integer(w,q->values[36]);
 if(37)put(w,",");put(w,"\"starColorCount\":");integer(w,q->values[37]);
 if(38)put(w,",");put(w,"\"novaChance\":");integer(w,q->values[38]);
 if(39)put(w,",");put(w,"\"novaCycleMs\":");integer(w,q->values[39]);
 if(40)put(w,",");put(w,"\"novaDurationMs\":");integer(w,q->values[40]);
 if(41)put(w,",");put(w,"\"novaGlyphCount\":");integer(w,q->values[41]);
 if(42)put(w,",");put(w,"\"rippleSpeed\":");integer(w,q->values[42]);
 if(43)put(w,",");put(w,"\"rippleWidth\":");integer(w,q->values[43]);
 if(44)put(w,",");put(w,"\"rippleLifeMs\":");integer(w,q->values[44]);
 if(45)put(w,",");put(w,"\"rippleOpacity\":");integer(w,q->values[45]);
 if(46)put(w,",");put(w,"\"rippleRings\":");integer(w,q->values[46]);
 if(47)put(w,",");put(w,"\"motion\":");integer(w,q->values[47]);
 if(48)put(w,",");put(w,"\"quantize\":");integer(w,q->values[48]);
 if(49)put(w,",");put(w,"\"originX\":");integer(w,q->values[49]);
 if(50)put(w,",");put(w,"\"originY\":");integer(w,q->values[50]);
 if(51)put(w,",");put(w,"\"waveAmplitude\":");integer(w,q->values[51]);
 if(52)put(w,",");put(w,"\"starAttack\":");integer(w,q->values[52]);
 if(53)put(w,",");put(w,"\"reverse\":");integer(w,q->values[53]);

 put(w,"}");const char*names[]={"palette","starPalette","glyphs","novaGlyphs"};const uint32_t*arrays[]={q->palette,q->starPalette,q->glyphs,q->novaGlyphs};const int keys[]={25,37,36,41};
 for(int a=0;a<4;a++){put(w,",");string(w,names[a]);put(w,":[");for(int i=0;i<q->values[keys[a]];i++){if(i)put(w,",");integer(w,arrays[a][i]);}put(w,"]");}
 put(w,"},\"events\":[");for(uint32_t i=0;i<q->eventCount;i++){const int32_t*e=q->events[i];if(i)put(w,",");put(w,"{\"x\":");number(w,e[0]/256.0);put(w,",\"y\":");number(w,e[1]/256.0);put(w,",\"strength\":");integer(w,e[2]);put(w,",\"kind\":");integer(w,e[3]);put(w,",\"atMs\":");integer(w,((uint64_t)(uint32_t)e[5]<<32)|(uint32_t)e[4]);put(w,",\"id\":");integer(w,e[6]);put(w,"}");}put(w,"]}");
}
static void sourceStageInfo(Writer*w,const SourceStageState*s){
    static const char*kinds[]={"text","box","rule","button","item","cursor","progress","bars","pie","donut","scatter","line","digits","edge"};
    put(w,"[");
    for(uint32_t i=0;i<s->count;i++){
        const SourceStageComponentRecord*q=&s->components[i];const int32_t*n=q->node;
        if(i)put(w,",");put(w,"{\"id\":");integer(w,q->id);
        put(w,",\"materialId\":");integer(w,q->materialId);put(w,",\"kind\":");string(w,kinds[n[0]]);
        put(w,",\"legacyFlags\":");integer(w,n[1]);put(w,",\"node\":[");
        for(int k=0;k<32;k++){if(k)put(w,",");integer(w,n[k]);}
        put(w,"],\"text\":");glyphString(w,s->text+n[17],n[18]);
        put(w,",\"data\":[");for(int k=0;k<n[20];k++){if(k)put(w,",");integer(w,s->data[n[19]+k]);}
        put(w,"]}");
    }
    put(w,"]");
}
static void windowPresentationInfo(Writer*w,const State*s,int slot){
    const WindowSourcePresentationState*p=&s->windowPresentation[slot];
    put(w,",\"sourcePresentation\":");put(w,p->enabled?"true":"false");
    put(w,",\"sourceOrder\":");integer(w,s->windowSourceOrder[slot]);
    put(w,",\"sourceOptions\":");
    if(!p->enabled)put(w,"null");else{
        const NrWindowSourcePresentationOptions*q=&p->options;
        static const char*chromes[]={"mac","windows","gnome","custom"};
        static const char*actions[]={"close","minimize","maximize","background"};
        put(w,"{\"opacity\":");number(w,q->opacity);put(w,",\"depthFade\":");number(w,q->depthFade);
        put(w,",\"chrome\":");string(w,chromes[q->chrome]);
        put(w,",\"controlWidth\":");integer(w,q->controlWidth);put(w,",\"controlHeight\":");integer(w,q->controlHeight);
        put(w,",\"customSide\":");string(w,q->customSide?"right":"left");
        put(w,",\"customOrder\":[");for(int i=0;i<4;i++){if(i)put(w,",");string(w,actions[q->customOrder[i]]);}
        put(w,"],\"customGlyphs\":[");for(int i=0;i<4;i++){if(i)put(w,",");integer(w,q->customGlyphs[i]);}
        put(w,"]}");
    }
    double opacity=s->windows[slot].alpha;
    if(p->enabled)nrWindowSourcePresentationOpacity(&p->options,-s->windows[slot].position.z,&opacity);
    put(w,",\"effectiveOpacity\":");number(w,opacity);
}
static void windowContentInfo(Writer*w,const State*s,int slot){
    const WindowContent*q=&s->windowContent[slot];const NrWindowPaletteSourceConfig*p=&q->palette;
    put(w,",\"content\":");if(!q->enabled){put(w,"null");return;}
    put(w,"{\"label\":");glyphString(w,q->label,(int)q->labelCount);
    put(w,",\"sourceIndex\":");integer(w,q->sourceIndex);
    const SourceAtelierWindow*a=&s->atelierWindows[slot];put(w,",\"profile\":");string(w,a->enabled?"atelier":"kinetic");
    if(a->enabled){const char*chromes[]={"mac","windows","gnome","custom"},*modes[]={"normal","minimized","closed"};put(w,",\"chrome\":");string(w,chromes[a->chrome]);put(w,",\"mode\":");string(w,modes[a->mode]);put(w,",\"toolWidth\":");integer(w,a->toolWidth);put(w,",\"toolHeight\":");integer(w,a->toolHeight);put(w,",\"fadeFloor\":");exactNumber(w,a->fadeFloor);put(w,",\"fade\":");exactNumber(w,nrAtelierWindowTween(s,slot,2));put(w,",\"bodyScale\":");exactNumber(w,nrAtelierWindowTween(s,slot,3));}

    put(w,",\"text\":");glyphString(w,q->text,(int)q->textCount);
    put(w,",\"colors\":[");for(uint32_t i=0;i<p->colorCount;i++){if(i)put(w,",");integer(w,p->colors[i]);}
    put(w,"],\"stopWidths\":[");for(uint32_t i=0;i<p->weightCount;i++){if(i)put(w,",");exactNumber(w,p->weights[i]);}
    put(w,"],\"background\":");integer(w,p->backgroundRgb);put(w,",\"ink\":");integer(w,p->inkRgb);
    put(w,",\"lockLightness\":");put(w,p->lockLightness?"true":"false");
    struct Field{const char*name;double value;}fields[]={
        {"lightness",p->lightness},{"chroma",p->chroma},{"brightness",p->brightness},
        {"hueOffset",p->hueOffsetDegrees},{"feather",p->feather},{"textLightness",p->textLightness},{"textChroma",p->textChroma},
        {"visibility",nrWindowContentVisibility(s,slot)},{"maximized",nrWindowContentMaximized(s,slot)}};
    for(size_t i=0;i<sizeof(fields)/sizeof(fields[0]);i++){put(w,",");string(w,fields[i].name);put(w,":");exactNumber(w,fields[i].value);}
    put(w,",\"waveform\":[");for(int i=0;i<128;i++){if(i)put(w,",");exactNumber(w,q->waveform[i]);}put(w,"]}");
}
static void windowApplicationInfo(Writer*w,const State*s){
 const WindowApplication*a=&s->windowApplication;
 if(!a->enabled){put(w,"null");return;}
 put(w,"{\"paletteWindowId\":");integer(w,a->paletteWindowId);
 const AtelierControls*b=&s->atelierApplicationParticles;put(w,",\"atelierParticles\":");if(!b->used)put(w,"null");else{put(w,"{\"count\":");integer(w,b->count);put(w,",\"branches\":");integer(w,b->branches);put(w,",\"seed\":");integer(w,b->seed);put(w,",\"reducedMotion\":");put(w,b->reducedMotion?"true":"false");struct P{const char*n;double v;}fields[]={{"lifeMs",b->lifeMs},{"speed",b->speed},{"gravity",b->gravity},{"rise",b->rise},{"drag",b->drag},{"turbulence",b->turbulence},{"glitterHz",b->glitterHz},{"trailMs",b->trailMs},{"jaggedness",b->jaggedness},{"coreMs",b->coreMs},{"coreRadius",b->coreRadius},{"ejecta",b->ejecta},{"shockwave",b->shockwave},{"intensity",b->intensity}};for(unsigned k=0;k<sizeof(fields)/sizeof(fields[0]);k++){put(w,",");string(w,fields[k].n);put(w,":");exactNumber(w,fields[k].v);}put(w,"}");}

 {const char*names[]={"windows","shapes","atelier-windows","observatory"};put(w,",\"scene\":");string(w,names[a->scene]);}
 {const char*names[]={"embers","sparks","nova","rain","snow","ripples"};put(w,",\"weatherStyle\":");string(w,names[a->reserved?a->reserved-1:a->scene==2?1:5]);}
 {const char*names[]={"linear","double-axis","wave","plasma","caustics","vortex","contours","aurora","woven","moire","tunnel","diamond","bilinear","checker","warp"};put(w,",\"backgroundStyle\":");string(w,names[a->backgroundStyle]);}
 {const char*names[]={"half","vertical","braille","cell"};put(w,",\"sampling\":");string(w,names[a->sampling]);}
 {const char*names[]={"spin","pendulum"};put(w,",\"orbitMode\":");string(w,names[a->orbitMode]);}
 put(w,",\"motion\":");put(w,a->motion?"true":"false");
 put(w,",\"starGlyphs\":");glyphString(w,a->starGlyphs,a->starGlyphCount);
 put(w,",\"fps\":");exactNumber(w,a->fps);
 put(w,",\"gradientScreens\":");exactNumber(w,a->gradientScreens);
 put(w,",\"gradientAngle\":");exactNumber(w,a->gradientAngle);
 put(w,",\"gradientSpeed\":");exactNumber(w,a->gradientSpeed);
 put(w,",\"gradientPhase\":");exactNumber(w,a->gradientPhase);
 put(w,",\"pivotX\":");exactNumber(w,a->pivotX);
 put(w,",\"pivotY\":");exactNumber(w,a->pivotY);
 put(w,",\"axisPitch\":");exactNumber(w,a->axisPitch);
 put(w,",\"rotationSpeed\":");exactNumber(w,a->rotationSpeed);
 put(w,",\"secondAxisSpeed\":");exactNumber(w,a->secondAxisSpeed);
 put(w,",\"swingAngle\":");exactNumber(w,a->swingAngle);
 put(w,",\"swingSeconds\":");exactNumber(w,a->swingSeconds);
 put(w,",\"starDensity\":");exactNumber(w,a->starDensity);
 put(w,",\"weatherIntensity\":");exactNumber(w,a->weatherIntensity);
 if(a->scene==3){put(w,",\"weatherLifeMs\":");exactNumber(w,a->particles.lifeMs);put(w,",\"weatherSpeed\":");exactNumber(w,a->particles.launchSpeed);}
 put(w,",\"novaStrength\":");exactNumber(w,a->novaStrength);
 put(w,",\"novaRegularity\":");exactNumber(w,a->novaRegularity);
 put(w,",\"starCount\":");exactNumber(w,a->starCount);
 put(w,",\"starSpeed\":");exactNumber(w,a->starSpeed);
 put(w,",\"trailMs\":");exactNumber(w,a->trailMs);
 put(w,",\"travelYaw\":");exactNumber(w,a->travelYaw);
 put(w,",\"travelPitch\":");exactNumber(w,a->travelPitch);
 put(w,",\"particles\":{\"glyphs\":");glyphString(w,a->particles.glyphs,a->particles.glyphCount);
 put(w,",\"count\":");exactNumber(w,a->particles.count);
 put(w,",\"lifeMs\":");exactNumber(w,a->particles.lifeMs);
 put(w,",\"launchSpeed\":");exactNumber(w,a->particles.launchSpeed);
 put(w,",\"gravity\":");exactNumber(w,a->particles.gravity);
 put(w,",\"drag\":");exactNumber(w,a->particles.drag);
 put(w,",\"wind\":");exactNumber(w,a->particles.wind);
 put(w,",\"flickerHz\":");exactNumber(w,a->particles.flickerHz);
 put(w,",\"trailMs\":");exactNumber(w,a->particles.trailMs);
 put(w,",\"branches\":");exactNumber(w,a->particles.branches);
 put(w,",\"arcSegments\":");exactNumber(w,a->particles.arcSegments);
 put(w,",\"arcJitter\":");exactNumber(w,a->particles.arcJitter);
 put(w,",\"coreMs\":");exactNumber(w,a->particles.coreMs);
 put(w,",\"shockwave\":");exactNumber(w,a->particles.shockwave);
 put(w,",\"explosionForce\":");exactNumber(w,a->particles.explosionForce);
 put(w,",\"seed\":");exactNumber(w,a->particles.seed);
 put(w,",\"brightness\":");exactNumber(w,a->particles.brightness);
 put(w,",\"emberSpread\":");exactNumber(w,a->particles.emberSpread);
 put(w,",\"arcReach\":");exactNumber(w,a->particles.arcReach);
 put(w,"},\"events\":[");
 const char*kinds[]={"embers","sparks","nova","rain","snow","ripples"};
 for(uint32_t i=0;i<a->eventCount;i++){const NrSourceWeatherEvent*e=&a->events[i];if(i)put(w,",");put(w,"{\"kind\":");string(w,kinds[e->kind]);
 put(w,",\"id\":");exactNumber(w,e->id);
 put(w,",\"x\":");exactNumber(w,e->x);
 put(w,",\"y\":");exactNumber(w,e->y);
 put(w,",\"atMs\":");exactNumber(w,e->atMs);
 put(w,"}");}
 put(w,"]}");
}
static Writer infoWrite(NrContext*c,Writer w) {
    const State*s=&c->state;
    const char*arcPhases[]={"waiting","leader","hold","fade","finished"};
    int active=0,dep=0,agg=0;
    for(int i=0; i<(int)NR_MAX_PARTICLES; i++)active+=s->particles[i].state!=0;
    for(int i=0; i<NR_DEPOSITS; i++)dep+=s->deposits[i].used!=0;
    for(int i=0; i<NR_TILES; i++)agg+=s->tiles[i].used?s->tiles[i].count:0;
    put(&w,"{\"build\":\"1.0.0\",\"contract\":{\"metadataProfile\":\"nocturne.metadata/v1\",\"commandProfile\":\"nocturne.commands/v1\",\"abiVersion\":");integer(&w,NR_ABI_VERSION);
    put(&w,",\"snapshotSchema\":");integer(&w,NR_STATE_SCHEMA);
    put(&w,",\"sourceSchema\":");integer(&w,s->schema);
    put(&w,",\"snapshotCapacityBytes\":");integer(&w,nrSnapshotSizeFor(c));
    put(&w,",\"bindingFamilies\":[");
    for(unsigned family=1;family<sizeof(bindingFamilies)/sizeof(bindingFamilies[0]);family++){if(family>1)put(&w,",");string(&w,bindingFamilies[family]);}
    put(&w,"],\"features\":[\"typed-values\",\"host-payloads\",\"character-rules\",\"character-regions\",\"queued-transactions\",\"panel-metadata\",\"graph-readback\",\"electrical-graphs\",\"firework-stages\",\"resource-animation-bindings\",\"electrical-selectors\",\"character-cell-inspection\",\"surface-foam-transport\",\"flow-thickness\",\"surface-geometry-inspection\",\"mesh-cell-refinement\",\"declared-color-fields\",\"resolved-area-geometry\",\"persistent-run-clusters\",\"thermal-cell-inspection\",\"thermal-response-settings\",\"thermal-value-bindings\",\"shortcut-negotiation\",\"water-cell-inspection\",\"water-volume-authoring\",\"water-response-settings\",\"water-value-bindings\",\"retained-convex-hulls\",\"hull-pose-inspection\",\"hull-value-bindings\",\"finite-water-motion\",\"reciprocal-fluid-drag\",\"finite-water-ledger\",\"script-itemization\",\"explicit-bidi-lines\",\"unicode-line-breaks\",\"source-scene-art\",\"canvas-presentation\",\"source-stage-components\",\"source-window-presentation\",\"window-cell-textures\",\"source-window-content\"],\"queryContracts\":{\"nrAreaGeometry\":{\"capacityUnit\":\"double\",\"rowWords\":12,\"alignmentBytes\":8,\"ownedBindings\":true,\"pure\":true,\"absentReturn\":0,\"presentReturn\":1,\"invalidReturn\":-1,\"contextOverlapAllowed\":false,\"coordinates\":\"screen-cells\",\"fields\":[\"x\",\"y\",\"width\",\"height\",\"clipX\",\"clipY\",\"clipWidth\",\"clipHeight\",\"contentX\",\"contentY\",\"contentWidth\",\"contentHeight\"]},\"nrFieldSample\":{\"capacityUnit\":\"double\",\"rowWords\":4,\"alignmentBytes\":8,\"ownedBindings\":true,\"pure\":true,\"absentReturn\":0,\"presentReturn\":1,\"invalidReturn\":-1,\"contextOverlapAllowed\":false,\"coordinates\":\"screen-cells\",\"fields\":[\"intensity\",\"rgb\",\"centerX\",\"centerY\"]},\"nrLineBreaks\":{\"capacityUnit\":\"offset\",\"rowWords\":1,\"alignmentBytes\":4,\"maxSourceScalars\":2048,\"ownedBindings\":true,\"pure\":true,\"invalidReturn\":-1,\"invalidOutputUnchanged\":true,\"inputOutputAliasAllowed\":true,\"nullOutputSizeProbe\":true,\"profile\":\"unicode-17.0.0-uax14-55-default\",\"offsetUnit\":\"unicode-scalar\",\"endOfTextIncluded\":true,\"fields\":[\"offset\"]},\"nrLineBreakDetails\":{\"capacityUnit\":\"row\",\"rowWords\":2,\"alignmentBytes\":4,\"maxSourceScalars\":2048,\"ownedBindings\":true,\"pure\":true,\"invalidReturn\":-1,\"invalidOutputUnchanged\":true,\"inputOutputAliasAllowed\":true,\"nullOutputSizeProbe\":true,\"profile\":\"unicode-17.0.0-uax14-55-default\",\"offsetUnit\":\"unicode-scalar\",\"endOfTextIncluded\":true,\"fields\":[\"offset\",\"mandatory\"],\"mandatoryValues\":[0,1]},\"nrSurfaceWaveSample\":{\"capacityUnit\":\"double\",\"rowWords\":6,\"alignmentBytes\":8,\"ownedBindings\":true,\"pure\":true,\"presentReturn\":1,\"invalidReturn\":-1,\"contextOverlapAllowed\":false,\"invalidOutputUnchanged\":true,\"fields\":[\"height\",\"normal.x\",\"normal.y\",\"normal.z\",\"verticalVelocity\",\"laplacian\"],\"modeSelector\":\"surfaceFluidAngular[].pose\",\"analyticMode\":{\"coverage\":\"infinite-authored-wave-field\",\"normalFrame\":\"world-unrotated\",\"verticalVelocity\":\"wave-plus-reservoir-vertical-translation\",\"laplacian\":\"analytic-authored-xz\"},\"posedMode\":{\"coverage\":\"topmost-world-facet\",\"normalFrame\":\"world-upward\",\"verticalVelocity\":\"material-world-y\",\"laplacian\":\"within-facet-zero\",\"equalHeightTie\":\"source-order\",\"verticalFacet\":\"no-height\",\"uncoveredReturn\":-1}},\"nrSurfaceFluidAngular\":{\"capacityUnit\":\"double\",\"rowWords\":12,\"alignmentBytes\":8,\"ownedBindings\":true,\"pure\":true,\"invalidReturn\":-1,\"presentReturn\":1,\"absentReturn\":0,\"contextOverlapAllowed\":false,\"frame\":\"world\",\"inertiaModel\":\"isotropic\",\"fields\":[\"inertia\",\"omega.x\",\"omega.y\",\"omega.z\",\"initialMomentum.x\",\"initialMomentum.y\",\"initialMomentum.z\",\"bodyImpulse.x\",\"bodyImpulse.y\",\"bodyImpulse.z\",\"dissipatedEnergy\",\"initialEnergy\"]},\"nrAngularDragExchange\":{\"capacityUnit\":\"double\",\"rowWords\":10,\"alignmentBytes\":8,\"ownedBindings\":true,\"pure\":true,\"invalidReturn\":-1,\"presentReturn\":1,\"inputOutputAliasAllowed\":true,\"frame\":\"explicit-shared-principal\",\"fields\":[\"bodyOmega.x\",\"bodyOmega.y\",\"bodyOmega.z\",\"waterOmega.x\",\"waterOmega.y\",\"waterOmega.z\",\"waterAngularImpulse.x\",\"waterAngularImpulse.y\",\"waterAngularImpulse.z\",\"dissipatedEnergy\"]},\"nrHullImmersionPlane\":{\"capacityUnit\":\"double\",\"rowWords\":5,\"alignmentBytes\":8,\"ownedBindings\":true,\"pure\":true,\"invalidReturn\":-1,\"presentReturn\":1,\"inputOutputAliasAllowed\":true,\"fields\":[\"totalVolume\",\"submergedVolume\",\"centroid.x\",\"centroid.y\",\"centroid.z\"]},\"nrHullBuoyancyPlane\":{\"capacityUnit\":\"double\",\"rowWords\":11,\"alignmentBytes\":8,\"ownedBindings\":true,\"pure\":true,\"invalidReturn\":-1,\"presentReturn\":1,\"inputOutputAliasAllowed\":true,\"liftDirection\":\"vertical\",\"fields\":[\"totalVolume\",\"submergedVolume\",\"centroid.x\",\"centroid.y\",\"centroid.z\",\"netForce.x\",\"netForce.y\",\"netForce.z\",\"torque.x\",\"torque.y\",\"torque.z\"]},\"nrFluidDragExchange\":{\"capacityUnit\":\"double\",\"rowWords\":10,\"alignmentBytes\":8,\"ownedBindings\":true,\"pure\":true,\"invalidReturn\":-1,\"presentReturn\":1,\"inputOutputAliasAllowed\":true,\"fields\":[\"bodyVelocity.x\",\"bodyVelocity.y\",\"bodyVelocity.z\",\"waterVelocity.x\",\"waterVelocity.y\",\"waterVelocity.z\",\"waterImpulse.x\",\"waterImpulse.y\",\"waterImpulse.z\",\"dissipatedEnergy\"]},\"nrScriptRuns\":{\"capacityUnit\":\"row\",\"rowWords\":3,\"alignmentBytes\":4,\"maxSourceScalars\":2048,\"ownedBindings\":true,\"pure\":true,\"invalidReturn\":-1,\"inputOutputAliasAllowed\":true,\"profile\":\"nr-script-grapheme-v1\",\"fields\":[\"start\",\"end\",\"iso15924TagBigEndian\"]},\"nrBidiClusterLines\":{\"capacityUnit\":\"row\",\"rowWords\":7,\"alignmentBytes\":4,\"maxSourceScalars\":2048,\"ownedBindings\":true,\"pure\":true,\"invalidReturn\":-1,\"inputOutputAliasAllowed\":true,\"fullParagraphResolution\":true,\"wholeGraphemeLines\":true,\"crossHardBreakAllowed\":false,\"widthUnit\":\"terminalCellAnnotation\",\"fields\":[\"start\",\"end\",\"column\",\"line\",\"width\",\"level\",\"mappedFirstScalar\"]},\"nrThermalSample\":{\"capacityUnit\":\"double\",\"rowWords\":10,\"alignmentBytes\":8,\"ownedBindings\":true,\"pure\":true,\"absentReturn\":0,\"presentReturn\":1,\"invalidReturn\":-1,\"contextOverlapAllowed\":false,\"fields\":[\"temperature\",\"energy\",\"initialEnergy\",\"appliedEnergy\",\"environmentEnergy\",\"importedEnergy\",\"transferredEnergy\",\"capacity\",\"power\",\"ambientTemperature\"]},\"nrWaterSample\":{\"capacityUnit\":\"double\",\"rowWords\":8,\"alignmentBytes\":8,\"ownedBindings\":true,\"pure\":true,\"absentReturn\":0,\"presentReturn\":1,\"invalidReturn\":-1,\"contextOverlapAllowed\":false,\"fields\":[\"surfaceId\",\"receivedVolume\",\"retainedVolume\",\"wetness\",\"importedVolume\",\"transferredVolume\",\"evaporatedVolume\",\"capacity\"]},\"nrFloatHull\":{\"capacityUnit\":\"double\",\"rowWords\":14,\"alignmentBytes\":8,\"ownedBindings\":true,\"pure\":true,\"absentReturn\":0,\"presentReturn\":1,\"invalidReturn\":-1,\"contextOverlapAllowed\":false,\"fields\":[\"orientation.x\",\"orientation.y\",\"orientation.z\",\"orientation.w\",\"angularVelocity.x\",\"angularVelocity.y\",\"angularVelocity.z\",\"inertia.x\",\"inertia.y\",\"inertia.z\",\"centerOfMass.x\",\"centerOfMass.y\",\"centerOfMass.z\",\"volume\"]},\"nrSurfaceFluid\":{\"capacityUnit\":\"double\",\"rowWords\":15,\"alignmentBytes\":8,\"ownedBindings\":true,\"pure\":true,\"absentReturn\":0,\"presentReturn\":1,\"invalidReturn\":-1,\"contextOverlapAllowed\":false,\"fields\":[\"mass\",\"velocity.x\",\"velocity.y\",\"velocity.z\",\"offset.x\",\"offset.y\",\"offset.z\",\"initialMomentum.x\",\"initialMomentum.y\",\"initialMomentum.z\",\"bodyImpulse.x\",\"bodyImpulse.y\",\"bodyImpulse.z\",\"dissipatedEnergy\",\"initialEnergy\"],\"lifecycleProperty\":\"surfaceFluids[].active\",\"stoppedRecordPresent\":true}}},\"textProfile\":\"nr-cell-scalar-v1\",\"graphemeProfile\":\"unicode-17.0.0-uax29-47\",\"widthProfile\":\"nr-grapheme-cell-width-v1-unicode-17.0.0\",\"clock\":{\"timeUs\":");
    integer(&w,s->timeUs);
    put(&w,",\"targetUs\":");
    integer(&w,s->targetUs);
    put(&w,",\"step\":");
    integer(&w,s->step);
    put(&w,",\"paused\":");
    put(&w,s->paused?"true":"false");
    put(&w,"},\"particles\":{\"active\":");
    integer(&w,active);
    put(&w,",\"deposited\":");
    integer(&w,dep);
    put(&w,",\"aggregated\":");
    integer(&w,agg);
    put(&w,",\"born\":");
    integer(&w,s->births);
    put(&w,",\"rejected\":");
    integer(&w,s->rejectedBirths);
    put(&w,",\"depositRejected\":");
    integer(&w,s->depositsRejected);
    put(&w,"},\"sourceSky\":");if(!s->sourceSky.enabled)put(&w,"null");else{const SourceSky*a=&s->sourceSky;put(&w,"{\"worldSeed\":");integer(&w,a->seed);put(&w,",\"skyDensity\":");integer(&w,a->density);put(&w,",\"skyRadius\":");number(&w,a->radius);put(&w,",\"skyExposure\":");number(&w,a->exposure);put(&w,",\"trailMs\":");number(&w,a->trailMs);put(&w,",\"textLightness\":");number(&w,a->textLightness);put(&w,",\"textChroma\":");number(&w,a->textChroma);put(&w,"}");}
    put(&w,",\"graph\":{\"dimensions\":");integer(&w,s->dimensions);
    put(&w,",\"layoutMode\":");string(&w,s->layoutMode==1?"force":s->layoutMode==2?"radial":"layered");
    put(&w,",\"lastLayoutUnresolvedNodes\":");integer(&w,s->cycleCount);
    put(&w,",\"layoutProfile\":");string(&w,s->sourceGraphLayout.enabled?"source":"measured");put(&w,",\"sourceLayout\":");
    if(!s->sourceGraphLayout.enabled)put(&w,"null");else{const SourceGraphLayout*g=&s->sourceGraphLayout;const SourceGraphOptions*o=&g->options;put(&w,"{\"seed\":");integer(&w,o->seed);put(&w,",\"dimensions\":");integer(&w,o->dimensions);put(&w,",\"mode\":");string(&w,(const char*[]){"layered","force","radial"}[o->mode]);put(&w,",\"iterations\":");integer(&w,o->iterations);put(&w,",\"sweeps\":");integer(&w,o->sweeps);put(&w,",\"orientation\":");string(&w,o->lr?"LR":"TB");
    put(&w,",\"nodeGap\":");number(&w,o->nodeGap);
    put(&w,",\"layerGap\":");number(&w,o->layerGap);
    put(&w,",\"depthGap\":");number(&w,o->depthGap);
    put(&w,",\"repulsion\":");number(&w,o->repulsion);
    put(&w,",\"spring\":");number(&w,o->spring);
    put(&w,",\"linkLength\":");number(&w,o->linkLength);
    put(&w,",\"damping\":");number(&w,o->damping);
    put(&w,",\"timeStep\":");number(&w,o->timeStep);
    put(&w,",\"collision\":");number(&w,o->collision);
    put(&w,",\"nodeSizes\":[");int comma=0;for(int i=0;i<NR_MAX_NODES;i++)if(g->nodeIds[i]){if(comma++)put(&w,",");put(&w,"{\"id\":");integer(&w,g->nodeIds[i]);put(&w,",\"width\":");number(&w,g->widths[i]);put(&w,",\"height\":");number(&w,g->heights[i]);put(&w,"}");}put(&w,"],\"edgeWeights\":[");comma=0;for(int i=0;i<s->edgeCount;i++)if(g->edgeWeights[i]){if(comma++)put(&w,",");put(&w,"{\"from\":");integer(&w,s->edges[i].from);put(&w,",\"to\":");integer(&w,s->edges[i].to);put(&w,",\"kind\":");string(&w,(const char*[]){"contains","depends","parent","reference","produces","related"}[s->edges[i].kind]);put(&w,",\"weight\":");number(&w,g->edgeWeights[i]);put(&w,"}");}put(&w,"]}");}

    put(&w,",\"edges\":[");const char *edgeNames[]={"contains","depends","parent","reference","produces","related"};
    for(int e=0;e<s->edgeCount;e++){if(e)put(&w,",");put(&w,"{\"from\":");integer(&w,s->edges[e].from);put(&w,",\"to\":");integer(&w,s->edges[e].to);put(&w,",\"kind\":");string(&w,edgeNames[s->edges[e].kind]);put(&w,"}");}
    put(&w,"]");
    put(&w,"},\"camera\":{\"position\":");
    Camera camera=nrCameraAt(s);
    vec(&w,camera.position);
    put(&w,",\"yaw\":");
    number(&w,camera.yaw);
    put(&w,",\"pitch\":");
    number(&w,camera.pitch);
    put(&w,",\"roll\":");
    number(&w,camera.roll);
    put(&w,",\"near\":");number(&w,camera.nearPlane);
    put(&w,",\"far\":");number(&w,camera.farPlane);
    put(&w,",\"fov\":");number(&w,camera.fov);
    put(&w,",\"span\":");number(&w,camera.span);
    put(&w,",\"orthographic\":");put(&w,camera.orthographic?"true":"false");
    put(&w,",\"flightActive\":");
    put(&w,(s->flight.count||s->originalCamera.flightKind)?"true":"false");
    put(&w,",\"profile\":");string(&w,s->originalCamera.enabled?"original":"default");
    if(s->originalCamera.enabled){put(&w,",\"navigation\":");string(&w,(const char*[]){"orbit","fly","pan"}[s->originalCamera.navigation]);put(&w,",\"target\":");vec(&w,s->originalCamera.target);put(&w,",\"moveSpeed\":");number(&w,s->originalCamera.moveSpeed);put(&w,",\"turnSpeed\":");number(&w,s->originalCamera.turnSpeed);put(&w,",\"sensitivity\":");number(&w,s->originalCamera.sensitivity);}put(&w,",\"grabbed\":");if(s->originalCamera.grabActive)vec(&w,s->originalCamera.grabbed);else put(&w,"null");
    put(&w,",\"controls\":");cameraControlsInfo(&w,s);
    Camera carrier=nrCameraCarrierAt(s);put(&w,",\"carrier\":{\"position\":");vec(&w,carrier.position);
    put(&w,",\"yaw\":");number(&w,carrier.yaw);put(&w,",\"pitch\":");number(&w,carrier.pitch);put(&w,",\"roll\":");number(&w,carrier.roll);put(&w,"}");
    put(&w,"},\"environment\":{\"background\":");integer(&w,s->background);
    put(&w,",\"stars\":");integer(&w,s->stars);put(&w,",\"starFar\":");number(&w,s->starFar);
    put(&w,",\"sampling\":");string(&w,(const char*[]){"cell","half","braille","hybrid"}[s->sampling]);
    put(&w,",\"style\":");string(&w,(const char*[]){"solid","linear","plasma","wave","caustic","contours"}[s->style]);
    put(&w,",\"presentation\":");string(&w,s->canvasPresentation?"canvas":"workbench");
    put(&w,",\"occlusionTint\":");exactNumber(&w,NR_OCCLUSION_TINT(s));
    put(&w,",\"occludedDots\":");string(&w,s->occlusionControls.occludedDots?"merge":"hidden");
    put(&w,"},\"sceneArt\":");sceneArtInfo(&w,s);
    put(&w,",\"sourceModel\":");sourceModelInfo(&w,s);
    put(&w,",\"sourceStage\":");sourceStageSceneInfo(&w,s);
    put(&w,",\"sourceModal\":");sourceModalInfo(&w,s);
    put(&w,",\"observatoryOverlay\":");observatoryOverlayInfo(&w,s);
    put(&w,",\"sourceStageComponents\":");sourceStageInfo(&w,&s->sourceStage);
    put(&w,",\"prompt\":{\"layout\":");string(&w,NR_PROMPT_BIDI(s)?"bidi":s->promptPresentation.layout?"grapheme":"scalar");
    put(&w,",\"direction\":");string(&w,NR_PROMPT_BIDI(s)?(NR_PROMPT_DIRECTION(s)==0?"ltr":NR_PROMPT_DIRECTION(s)==1?"rtl":"auto"):"ltr");
    put(&w,",\"ambiguousWidth\":");integer(&w,s->promptPresentation.ambiguous?s->promptPresentation.ambiguous:1);
    put(&w,",\"firstPromptSource\":");
    if(!s->firstPromptSource.enabled)put(&w,"null");else{
        int lx,ly,lw,lh,placed=nrFirstPromptViewport(s,&lx,&ly,&lw,&lh);
        put(&w,"{\"values\":[");for(int i=0;i<64;i++){if(i)put(&w,",");integer(&w,i==0?lw:i==1?lh:s->firstPromptSource.values[i]);}put(&w,"],\"palette\":[");for(int i=0;i<8;i++){if(i)put(&w,",");integer(&w,s->firstPromptSource.values[64+i]);}put(&w,"],\"starPalette\":[");for(int i=0;i<8;i++){if(i)put(&w,",");integer(&w,s->firstPromptSource.values[72+i]);}put(&w,"],\"glyphs\":[");for(int i=0;i<32;i++){if(i)put(&w,",");integer(&w,s->firstPromptSource.values[80+i]);}int start,end,x,y;nrFirstPromptGeometry(s,&start,&end,&x,&y);put(&w,"],\"visibleStart\":");integer(&w,start);put(&w,",\"visibleEnd\":");integer(&w,end);put(&w,",\"column\":");integer(&w,x);put(&w,",\"row\":");integer(&w,y);
        const PromptSourceLayer*l=&s->promptSourceLayer;put(&w,",\"layer\":{\"region\":");
        if(l->placement==NR_PROMPT_SOURCE_CELLS){put(&w,"{\"x\":");integer(&w,l->x);put(&w,",\"y\":");integer(&w,l->y);put(&w,",\"width\":");integer(&w,l->width);put(&w,",\"height\":");integer(&w,l->height);put(&w,"}");}
        else if(l->placement==NR_PROMPT_SOURCE_PROMPT)string(&w,"prompt");
        else if(l->placement==NR_PROMPT_SOURCE_WIDGET){put(&w,"{\"widget\":");integer(&w,l->widget);put(&w,"}");}
        else put(&w,"null");
        put(&w,",\"bounds\":");if(placed){put(&w,"{\"x\":");integer(&w,lx);put(&w,",\"y\":");integer(&w,ly);put(&w,",\"width\":");integer(&w,lw);put(&w,",\"height\":");integer(&w,lh);put(&w,"}");}else put(&w,"null");
        put(&w,",\"z\":\"above\",\"order\":0,\"alpha\":{\"fg\":");exactNumber(&w,NR_PROMPT_SOURCE_ALPHA_FG(s));put(&w,",\"bg\":");exactNumber(&w,NR_PROMPT_SOURCE_ALPHA_BG(s));put(&w,"}");put(&w,",\"frame\":");string(&w,l->frame?"visible":"invisible");put(&w,"}}");
    }
    {const PromptAppearance*q=&s->promptAppearance;const char*shapes[]={"inherit","none","block","half","underline","bar","braille","custom"},*modes[]={"fixed","pulse","cycle"},*styles[]={"off","embers","sparks","nova","rain","snow","ripples"},*pastes[]={"each","burst","off"};
    put(&w,",\"appearance\":{\"cursor\":{\"shape\":");string(&w,shapes[q->cursorConfigured?q->cursorShape:0]);put(&w,",\"glyph\":");uint32_t glyph=q->cursorConfigured?q->cursorGlyph:0x2502;glyphString(&w,&glyph,1);
    const uint32_t rgb[]={q->cursorConfigured?q->cursorColor:0xa3cabe,q->cursorConfigured?q->cursorColor2:0xc7aed7};const char*keys[]={",\"color\":",",\"secondaryColor\":"};for(int i=0;i<2;i++){char text[8]={'#',0};const char*hex="0123456789abcdef";for(int k=0;k<6;k++)text[k+1]=hex[(rgb[i]>>((5-k)*4))&15];put(&w,keys[i]);string(&w,text);}
    put(&w,",\"blinkMs\":");number(&w,q->cursorConfigured?q->blinkMs:600);put(&w,",\"duty\":");number(&w,q->cursorConfigured?q->duty:.5);put(&w,",\"colorMode\":");string(&w,modes[q->colorMode]);put(&w,",\"colorPeriodMs\":");number(&w,q->cursorConfigured?q->colorPeriodMs:2000);
    put(&w,"},\"weather\":{\"style\":");string(&w,styles[q->weatherStyle]);put(&w,",\"intensity\":");number(&w,q->weatherConfigured?q->weatherIntensity:.65);put(&w,",\"lifeMs\":");number(&w,q->weatherConfigured?q->weatherLifeMs:1600);put(&w,",\"speed\":");number(&w,q->weatherConfigured?q->weatherSpeed:12);put(&w,",\"paste\":");string(&w,pastes[q->pastePolicy]);put(&w,",\"eventCount\":");integer(&w,q->eventCount);put(&w,",\"eventSerial\":");integer(&w,q->eventSerial);put(&w,"}}");}
    put(&w,",\"presentation\":");string(&w,s->promptFramed.enabled?"framed":"compact");
    put(&w,",\"sourceVimState\":");integer(&w,s->promptFramed.vimState);
    put(&w,",\"minimizedRestoreMode\":");integer(&w,s->promptFramed.minimizedRestoreMode);
    put(&w,",\"normalMode\":");integer(&w,s->promptFramed.normalMode);
    put(&w,",\"sourceOptions\":");
    if(s->promptFramed.enabled)promptSourceOptions(&w,&s->promptFramed.options);
    else put(&w,"null");
    put(&w,",\"sourceCommand\":");glyphString(&w,s->promptFramed.command,s->promptFramed.commandCount);
    put(&w,",\"sourceSearch\":");glyphString(&w,s->promptFramed.search,s->promptFramed.searchCount);
    put(&w,",\"sourceMessage\":");glyphString(&w,s->promptFramed.message,s->promptFramed.messageCount);
    put(&w,",\"sourceCheckpoint\":");
    if(s->promptFramed.checkpointValid){
        const PromptFramed*f=&s->promptFramed;
        static const char*modes[]={"marquee","grow","vim-inline","vim-full"};
        static const char*vim[]={"normal","insert","visual","command"};
        put(&w,"{\"version\":1,\"text\":");glyphString(&w,s->dynamicPrompt.checkpoint,f->checkpointCount);
        put(&w,",\"caret\":");integer(&w,f->checkpointCaret);
        put(&w,",\"mode\":");string(&w,modes[f->checkpointMode]);
        put(&w,",\"normalMode\":");string(&w,modes[f->checkpointNormalMode]);
        put(&w,",\"vimState\":");string(&w,vim[f->checkpointVimState]);
        put(&w,",\"options\":");promptSourceOptions(&w,&f->checkpointOptions);
        put(&w,"}");
    }else put(&w,"null");
    put(&w,",\"text\":");
    glyphString(&w,s->promptDocument.glyphs,s->promptDocument.count);
    put(&w,",\"caret\":");
    integer(&w,s->promptDocument.caret);
    put(&w,",\"anchor\":");integer(&w,s->promptDocument.anchor);
    put(&w,",\"mode\":");
    integer(&w,s->promptDocument.mode);
    put(&w,",\"vimMode\":");string(&w,s->promptDocument.vimMode?"insert":"normal");
    put(&w,",\"revision\":");
    integer(&w,s->promptDocument.revision);
    if(s->editorRedo.count){put(&w,",\"redoAvailable\":");integer(&w,s->editorRedo.count);}
    put(&w,"}");
    put(&w,",\"materialPatterns\":[");
    int patternFirst=1;
    for(int i=0;i<NR_MATERIALS;i++)if(s->materialPatterns[i].used){
        if(!patternFirst)put(&w,",");patternFirst=0;
        materialPatternRecord(&w,i,&s->materialPatterns[i].sampler);
    }
    put(&w,"]");
    if(s->promptRegister.count){put(&w,",\"vimRegister\":{\"text\":");glyphString(&w,s->promptRegister.glyphs,s->promptRegister.count);put(&w,",\"linewise\":");put(&w,s->promptRegister.linewise?"true":"false");put(&w,"}");}
    int hasNamedRegister=0;for(int i=0;i<26;i++)if(s->promptRegisters.slots[i].count)hasNamedRegister=1;
    if(hasNamedRegister){put(&w,",\"namedRegisters\":{");int firstRegister=1;for(int i=0;i<26;i++)if(s->promptRegisters.slots[i].count){
        if(!firstRegister)put(&w,",");firstRegister=0;char name[2]={(char)('a'+i),0};string(&w,name);put(&w,":{\"text\":");glyphString(&w,s->promptRegisters.slots[i].glyphs,s->promptRegisters.slots[i].count);put(&w,",\"linewise\":");put(&w,s->promptRegisters.slots[i].linewise?"true":"false");put(&w,"}");
    }put(&w,"}");}
    put(&w,",\"selection\":");
    integer(&w,s->selection);
    put(&w,",\"inspectorScroll\":");integer(&w,s->selectionScroll);
    put(&w,",\"selectedWindow\":");integer(&w,s->selectedWindow);
    put(&w,",\"modal\":");
    integer(&w,s->promptDocument.modal);
    put(&w,",\"inputOwner\":");string(&w,nrInputOwner(s)==1?"modal":nrInputOwner(s)==2?"reader":"prompt");
    put(&w,",\"render\":{\"fragmentOverflow\":");
    integer(&w,c->fragmentOverflow);
    put(&w,",\"contentNeedsReader\":");
    integer(&w,c->contentNeedsReader);
    put(&w,"},\"fields\":[");
    int first=1,count=0;
    for(int i=0; i<NR_FIELDS; i++) {
        const Field*f=&s->fields[i];
        if(!f->used)continue;
        if(!first)put(&w,",");
        first=0;
        count++;
        put(&w,"{\"id\":");
        integer(&w,f->id);
        put(&w,",\"x\":");
        number(&w,f->x);
        put(&w,",\"y\":");
        number(&w,f->y);
        put(&w,",\"atUs\":");
        integer(&w,f->atUs);
        put(&w,",\"width\":");
        number(&w,f->width);
        put(&w,",\"lifeUs\":");integer(&w,f->lifeUs);
        put(&w,",\"speed\":");number(&w,f->speed);
        put(&w,",\"strength\":");number(&w,f->strength);
        put(&w,",\"material\":");integer(&w,f->material);
        const FieldControls*q=&s->fieldControls[i];
        put(&w,",\"continuous\":");put(&w,q->continuous?"true":"false");
        put(&w,",\"falloff\":");integer(&w,q->used?q->falloff:2);
        put(&w,",\"rings\":");integer(&w,NR_FIELD_RINGS(q)?NR_FIELD_RINGS(q):NR_FIELD_OPTICS(q)==1?2:0);
        put(&w,",\"optics\":");string(&w,NR_FIELD_OPTICS(q)?"source":"legacy");
        put(&w,",\"paint\":");string(&w,NR_FIELD_SOURCE_PAINT(q)?"source":"field");
        put(&w,",\"frequency\":");number(&w,q->used?q->frequency:100);
        put(&w,",\"phase\":");number(&w,q->phase);
        put(&w,",\"interference\":");number(&w,q->interference);
        put(&w,",\"materialAuthored\":");put(&w,q->materialAuthored?"true":"false");
        put(&w,",\"velocity\":[");number(&w,q->vx);put(&w,",");number(&w,q->vy);put(&w,"]");
        put(&w,",\"surface\":");if(q->surface){put(&w,"{\"x\":");number(&w,q->x);put(&w,",\"y\":");number(&w,q->y);put(&w,",\"width\":");number(&w,q->width);put(&w,",\"height\":");number(&w,q->height);put(&w,"}");}else put(&w,"null");
        put(&w,"}");
    }
    put(&w,"],\"fieldCount\":");
    integer(&w,count);
    put(&w,",\"textRuns\":[");
    first=1;
    for(int i=0;i<NR_TEXTS;i++) {
        const TextRun*q=&s->text[i];
        if(!q->used)continue;
        if(!first)put(&w,",");first=0;
        put(&w,"{\"id\":");integer(&w,q->id);
        put(&w,",\"text\":");glyphString(&w,q->text,q->count);
        uint32_t alphabet[256];for(int k=0;k<q->alphabetCount;k++)alphabet[k]=k<128?q->alphabet[k]:s->textAlphabetTail[i][k-128];
        put(&w,",\"seed\":");integer(&w,(uint32_t)q->seed);
        put(&w,",\"alphabet\":");glyphString(&w,alphabet,q->alphabetCount);put(&w,",\"alphabetCount\":");integer(&w,q->alphabetCount);
        put(&w,",\"local\":");put(&w,q->local?"true":"false");
        put(&w,",\"phase\":");string(&w,q->phase?"hide":"show");
        put(&w,",\"phaseModel\":");string(&w,s->textPhaseModel[i]==3?"source-paint":s->textPhaseModel[i]==1?"source":"reverse-show");
        put(&w,",\"phaseModelExplicit\":");put(&w,s->textPhaseModel[i]?"true":"false");
        uint32_t trailCount=0;TextPose trailPose;
        for(int glyph=0;glyph<q->count;glyph++)for(int ordinal=0;ordinal<q->trailLength;ordinal++)if(nrTextTrailPose(s,i,glyph,ordinal,&trailPose))trailCount++;
        put(&w,",\"trailCount\":");integer(&w,trailCount);put(&w,",\"trailSampleLimit\":16,\"trails\":[");uint32_t written=0;
        for(int glyph=0;glyph<q->count&&written<16;glyph++)for(int ordinal=0;ordinal<q->trailLength&&written<16;ordinal++)if(nrTextTrailPose(s,i,glyph,ordinal,&trailPose)){
            if(written++)put(&w,",");put(&w,"[");integer(&w,glyph);put(&w,",");integer(&w,ordinal+1);put(&w,",");integer(&w,trailPose.glyph);
            put(&w,",");number(&w,trailPose.x);put(&w,",");number(&w,trailPose.y);put(&w,",");number(&w,trailPose.alpha);put(&w,",");number(&w,trailPose.hue);put(&w,",");integer(&w,q->origin[glyph].identity);put(&w,"]");
        }put(&w,"]");

        put(&w,"}");
    }
    put(&w,"],\"windows\":[");
    first=1;
    for(int i=0; i<(int)NR_MAX_WINDOWS; i++) {
        const Window*q=&s->windows[i];
        if(!q->used)continue;
        if(!first)put(&w,",");
        first=0;
        put(&w,"{\"id\":");
        integer(&w,q->id);
        put(&w,",\"title\":");
        glyphString(&w,q->title,q->titleCount);
        put(&w,",\"sourceGeometry\":");put(&w,s->windowSourceGeometry[i]?"true":"false");
        windowPresentationInfo(&w,s,i);
        put(&w,",\"texture\":");
        const WindowTextureRecord*texture=&s->windowTextures.windows[i];
        if(!texture->width)put(&w,"null");
        else{
            put(&w,"{\"width\":");integer(&w,texture->width);put(&w,",\"height\":");integer(&w,texture->height);
            put(&w,",\"cells\":[");
            for(uint32_t k=0;k<texture->width*texture->height;k++){
                if(k)put(&w,",");put(&w,"[");
                for(int word=0;word<3;word++){if(word)put(&w,",");integer(&w,s->windowTextures.cells[texture->offset+k][word]);}
                put(&w,"]");
            }put(&w,"]}");
        }
        put(&w,",\"text\":");
        int documentCount;const uint32_t*document=nrWindowDocument(s,q,&documentCount);
        glyphString(&w,document,documentCount);
        windowContentInfo(&w,s,i);
        put(&w,",\"position\":");
        vec(&w,q->position);
        put(&w,",\"visible\":");
        number(&w,nrWindowContentVisibility(s,i));
        put(&w,",\"width\":");number(&w,q->width);
        put(&w,",\"height\":");number(&w,q->height);
        put(&w,",\"alpha\":");number(&w,q->alpha);
        put(&w,",\"material\":");integer(&w,q->material);
        put(&w,",\"group\":");integer(&w,q->group);
        put(&w,",\"shape\":");integer(&w,q->shape);
        put(&w,",\"yaw\":");number(&w,q->yaw);
        put(&w,",\"pitch\":");number(&w,q->pitch);
        put(&w,",\"roll\":");number(&w,q->roll);
        put(&w,",\"minColumns\":");integer(&w,q->minColumns);
        put(&w,",\"maxColumns\":");integer(&w,q->maxColumns);
        put(&w,",\"anchorX\":");number(&w,q->anchorX);
        put(&w,",\"anchorY\":");number(&w,q->anchorY);
        put(&w,",\"overshoot\":");number(&w,q->overshoot);
        put(&w,",\"scatter\":");number(&w,q->scatter);
        put(&w,",\"bend\":");number(&w,q->bend);
        put(&w,",\"folds\":");integer(&w,q->folds);
        put(&w,",\"meshColumns\":");integer(&w,q->meshColumns);
        put(&w,",\"meshRows\":");integer(&w,q->meshRows);
        put(&w,",\"atUs\":");integer(&w,q->atUs);
        put(&w,",\"durationUs\":");integer(&w,q->durationUs);
        put(&w,",\"reader\":");put(&w,q->reader?"true":"false");
        put(&w,",\"scrollRow\":");integer(&w,q->scrollRow);
        put(&w,",\"readability\":{\"padding\":");integer(&w,q->padding);
        put(&w,",\"border\":");integer(&w,q->border);
        put(&w,",\"chromeSize\":");integer(&w,q->chromeSize);
        put(&w,",\"fadeStartRatio\":");number(&w,q->fadeStartRatio);
        put(&w,",\"fadeEndRatio\":");number(&w,q->fadeEndRatio);
        put(&w,"}}");
    }
    put(&w,"],\"windowApplication\":");windowApplicationInfo(&w,s);put(&w,",\"nodes\":[");
    first=1;
    for(int i=0; i<(int)NR_MAX_NODES; i++) {
        const Node*n=&s->nodes[i];
        if(!n->used)continue;
        if(!first)put(&w,",");
        first=0;
        put(&w,"{\"id\":");
        integer(&w,n->id);
        put(&w,",\"label\":");
        glyphString(&w,n->label,n->labelCount);
        put(&w,",\"detail\":");
        glyphString(&w,n->detail,n->detailCount);
        put(&w,",\"kind\":");
        string(&w,n->kind);
        put(&w,",\"status\":");
        string(&w,n->status);
        put(&w,",\"sha\":");
        string(&w,n->sha);
        put(&w,",\"position\":");
        vec(&w,nrNodeAt(n,s->timeUs));
        put(&w,",\"pinned\":");put(&w,n->pinned?"true":"false");
        put(&w,",\"targetPosition\":");vec(&w,n->position);
        put(&w,",\"card\":{\"minColumns\":");integer(&w,n->minColumns);
        put(&w,",\"maxColumns\":");integer(&w,n->maxColumns);
        put(&w,",\"padding\":");integer(&w,n->padding);
        put(&w,",\"shaPrefix\":");integer(&w,n->shaPrefix);
        put(&w,",\"showKind\":");put(&w,n->showKind?"true":"false");
        put(&w,",\"showStatus\":");put(&w,n->showStatus?"true":"false");
        put(&w,",\"showSha\":");put(&w,n->showSha?"true":"false");
        put(&w,",\"showDetail\":");put(&w,n->showDetail?"true":"false");
        put(&w,",\"width\":");integer(&w,nrNodeWidth(n));
        put(&w,",\"height\":");integer(&w,nrNodeHeight(n,nrNodeWidth(n)));
        put(&w,"}}");
    }
    put(&w,"],\"widgets\":[");
    first=1;
    for(int i=0; i<NR_WIDGETS; i++) {
        const Widget*q=&s->widgets[i];
        if(!q->used)continue;
        if(!first)put(&w,",");
        first=0;
        put(&w,"{\"id\":");
        integer(&w,q->id);
        put(&w,",\"text\":");
        glyphString(&w,q->text,q->count);
        put(&w,",\"value\":");
        exactNumber(&w,q->value);
        put(&w,",\"kind\":");integer(&w,q->kind);
        put(&w,",\"x\":");integer(&w,q->x);
        put(&w,",\"y\":");integer(&w,q->y);
        put(&w,",\"width\":");integer(&w,q->width);
        put(&w,",\"height\":");integer(&w,q->height);
        put(&w,",\"padding\":");integer(&w,q->padding);
        put(&w,",\"border\":");integer(&w,q->border);
        put(&w,",\"material\":");integer(&w,q->material);
        put(&w,",\"backgroundMaterial\":");integer(&w,q->backgroundMaterial);
        put(&w,",\"alpha\":");exactNumber(&w,q->alpha);
        put(&w,",\"enabled\":");put(&w,q->enabled?"true":"false");
        put(&w,",\"selected\":");put(&w,q->selected?"true":"false");
        put(&w,",\"active\":");put(&w,q->active?"true":"false");
        put(&w,",\"min\":");exactNumber(&w,q->min);
        put(&w,",\"max\":");exactNumber(&w,q->max);
        put(&w,",\"mode\":");integer(&w,q->mode);
        put(&w,",\"pulseUs\":");integer(&w,q->pulseUs);
        put(&w,",\"changedUs\":");integer(&w,q->changedUs);
        put(&w,",\"data\":[");
        for(int entry=0;entry<q->dataCount;entry++){if(entry)put(&w,",");exactNumber(&w,q->data[entry]);}
        put(&w,"]");
        put(&w,",\"plot\":{\"sampling\":");string(&w,q->sampling<0?"inherit":q->sampling==0?"cell":q->sampling==1?"half":q->sampling==2?"braille":"hybrid");
        put(&w,",\"cellAspect\":");exactNumber(&w,q->cellAspect);
        put(&w,",\"innerRadius\":");exactNumber(&w,q->innerRadius);
        put(&w,",\"startAngle\":");exactNumber(&w,q->startAngle);
        put(&w,",\"sweepAngle\":");exactNumber(&w,q->sweepAngle);
        put(&w,",\"revealUs\":");integer(&w,q->revealUs);
        put(&w,",\"revealAtUs\":");integer(&w,q->revealAtUs);
        put(&w,"}}");
    }
    put(&w,"],\"areas\":[");first=1;
    for(int i=0;i<NR_AREAS;i++)if(s->areas[i].used){
        const Area*q=&s->areas[i];if(!first)put(&w,",");first=0;
        put(&w,"{\"id\":");integer(&w,q->id);
        put(&w,",\"parent\":");integer(&w,q->parent);
        put(&w,",\"x\":");integer(&w,q->x);
        put(&w,",\"y\":");integer(&w,q->y);
        put(&w,",\"width\":");integer(&w,q->width);
        put(&w,",\"height\":");integer(&w,q->height);
        put(&w,",\"padding\":");integer(&w,q->padding);
        put(&w,",\"margin\":");integer(&w,q->margin);
        put(&w,",\"border\":");integer(&w,q->border);
        put(&w,",\"hideEmpty\":");put(&w,q->hideEmpty?"true":"false");
        put(&w,",\"material\":");integer(&w,q->material);
        put(&w,",\"alpha\":");number(&w,q->alpha);
        put(&w,",\"speedX\":");number(&w,q->speedX);
        put(&w,",\"speedY\":");number(&w,q->speedY);
        put(&w,",\"layout\":");string(&w,q->layout==0?"ordered":q->layout==1?"queue":"direct");
        put(&w,",\"fadeUs\":");integer(&w,q->fadeUs);
        put(&w,",\"gapUs\":");integer(&w,q->gapUs);
        put(&w,",\"availableUs\":");integer(&w,q->availableUs);put(&w,"}");
    }
    put(&w,"],\"messages\":[");
    first=1;
    for(int i=0; i<NR_MESSAGES; i++) {
        const Message*q=&s->messages[i];
        if(!q->used)continue;
        if(!first)put(&w,",");
        first=0;
        put(&w,"{\"id\":");
        integer(&w,q->id);
        put(&w,",\"text\":");
        glyphString(&w,q->text,q->count);
        put(&w,",\"state\":");string(&w,q->state==0?"queued":q->state==1?"active":q->state==2?"expired":"dismissed");
        put(&w,",\"area\":");integer(&w,q->area);
        put(&w,",\"priority\":");integer(&w,q->priority);
        put(&w,",\"readyUs\":");integer(&w,q->readyUs);
        put(&w,",\"startUs\":");integer(&w,q->startUs);
        put(&w,",\"durationUs\":");integer(&w,q->durationUs);
        put(&w,",\"sequence\":");integer(&w,q->sequence);
        put(&w,",\"key\":");string(&w,q->key);
        put(&w,",\"occurrences\":");integer(&w,q->occurrences);
        put(&w,",\"replacements\":");integer(&w,q->replacements);
        put(&w,",\"important\":");put(&w,q->important?"true":"false");
        put(&w,",\"acknowledged\":");put(&w,q->acknowledged?"true":"false");
        put(&w,",\"actions\":[");
        for(int a=0;a<q->actionCount;a++) {
            if(a)put(&w,",");const NotificationAction*n=&q->actions[a];
            put(&w,"{\"id\":");integer(&w,n->id);put(&w,",\"label\":");glyphString(&w,n->label,n->labelCount);
            put(&w,",\"event\":");string(&w,n->event);put(&w,",\"value\":");number(&w,n->value);put(&w,",\"dismiss\":");put(&w,n->dismiss?"true":"false");put(&w,",\"activated\":");put(&w,(q->actionMask&(1u<<a))?"true":"false");put(&w,"}");
        }
        put(&w,"]}");
    }
    put(&w,"],\"intents\":[");
    uint64_t previous=0;
    for(int count=0;count<NR_INTENTS;count++) {
        const Intent*chosen=0;
        for(int i=0;i<NR_INTENTS;i++)if(s->intents[i].used&&s->intents[i].id>previous&&(!chosen||s->intents[i].id<chosen->id))chosen=&s->intents[i];
        if(!chosen)break;if(count)put(&w,",");previous=chosen->id;
        put(&w,"{\"id\":");integer(&w,chosen->id);put(&w,",\"messageId\":");integer(&w,chosen->messageId);
        put(&w,",\"actionId\":");integer(&w,chosen->actionId);put(&w,",\"messageSequence\":");integer(&w,chosen->messageSequence);
        put(&w,",\"event\":");string(&w,chosen->event);put(&w,",\"value\":");number(&w,chosen->value);
        put(&w,",\"atUs\":");integer(&w,chosen->atUs);intentPayloadRecord(&w,s,chosen);put(&w,"}");
    }
    put(&w,"],\"registeredStates\":[");first=1;
    for(int i=0;i<NR_REGISTERED_STATES;i++) {
        const RegisteredState *r=&s->registeredStates[i];if(!r->used)continue;
        if(!first)put(&w,",");first=0;Appearance base,effective;
        int exists=nrAuthoredAppearance(s,r,&base);nrEffectiveAppearance(s,r,&effective);
        put(&w,"{\"id\":");integer(&w,r->id);put(&w,",\"path\":");string(&w,r->path);
        put(&w,",\"role\":");string(&w,r->role);put(&w,",\"family\":");string(&w,nrStyleFamilyName(r->family));
        put(&w,",\"targetId\":");integer(&w,r->targetId);put(&w,",\"exists\":");put(&w,exists?"true":"false");
        put(&w,",\"states\":{");unsigned flags=nrRegisteredFlags(s,r);
        for(int k=0;k<NR_STYLE_STATES;k++){if(k)put(&w,",");string(&w,nrStyleStateName(k));put(&w,":");put(&w,flags&(1u<<k)?"true":"false");}
        for(int view=0;view<2;view++) {
            put(&w,view?"},\"effective\":{":"},\"authored\":{");const Appearance *a=view?&effective:&base;int comma=0;
            for(int k=0;k<NR_STYLE_PROPERTIES;k++)if(a->mask&(1u<<k)){if(comma++)put(&w,",");string(&w,nrStylePropertyName(k));put(&w,":");number(&w,a->value[k]);}
        }
        put(&w,"}}");
    }
    put(&w,"],\"styleRules\":[");first=1;
    for(int i=0;i<NR_STYLE_RULES;i++){const StyleRule *r=&s->styleRules[i];if(!r->used)continue;
        if(!first)put(&w,",");first=0;put(&w,"{\"id\":");integer(&w,r->id);put(&w,",\"priority\":");integer(&w,r->priority);
        put(&w,",\"enabled\":");put(&w,r->enabled?"true":"false");put(&w,",\"guard\":");put(&w,r->guard.lastTruth?"true":"false");
        put(&w,",\"conditionNodes\":");integer(&w,r->guard.conditionCount);if(s->styleGuardFormulas[i].tree.count){put(&w,",\"guardExpressionNodes\":");integer(&w,s->styleGuardFormulas[i].tree.count);}put(&w,"}");}
    put(&w,"],\"characterRules\":[");first=1;
    for(int i=0;i<128;i++)if(s->characterRules[i].used){if(!first)put(&w,",");first=0;put(&w,s->characterRules[i].json);}
    put(&w,"],\"characterRegions\":[");first=1;
    for(int i=0;i<1024;i++)if(s->characterRegions[i].used){if(!first)put(&w,",");first=0;put(&w,s->characterRegions[i].json);}
    put(&w,"],\"values\":{");
    first=1;
    for(int i=0; i<NR_VALUES; i++) {
        const Value*v=&s->values[i];
        if(!v->used)continue;
        if(!first)put(&w,",");
        first=0;
        string(&w,v->path);
        put(&w,":");
        if(s->typedValues[i].kind)put(&w,s->typedValues[i].data.json);else{char encoded[1200];int length=nrJsonNumber(v->value,encoded,sizeof(encoded));if(length>=0)put(&w,encoded);else w.failed=1;}
    }
    put(&w,"}");
    int hasTyped=0;for(int i=0;i<NR_VALUES;i++)if(s->typedValues[i].kind)hasTyped=1;
    if(hasTyped){put(&w,",\"valueTypes\":{");first=1;const char*names[]={"number","boolean","string","json"};
        for(int i=0;i<NR_VALUES;i++)if(s->values[i].used&&s->typedValues[i].kind){if(!first)put(&w,",");first=0;string(&w,s->values[i].path);put(&w,":");string(&w,names[s->typedValues[i].kind]);}
        put(&w,"}");
    }
    put(&w,",\"valueDescriptors\":{");first=1;
    const char*valueKinds[]={"number","boolean","string","json"};
    for(int i=0;i<NR_VALUES;i++)if(s->values[i].used){
        const Value*v=&s->values[i];if(!first)put(&w,",");first=0;string(&w,v->path);
        put(&w,":{\"type\":");string(&w,valueKinds[s->typedValues[i].kind]);
        put(&w,",\"readonly\":");put(&w,v->readonly?"true":"false");put(&w,",\"binding\":");
        if(!v->bindingFamily)put(&w,"null");
        else{put(&w,"{\"family\":");string(&w,bindingFamilies[v->bindingFamily]);put(&w,",\"id\":");
            integer(&w,v->bindingFamily==14?(uint32_t)v->bindingId:v->bindingId);put(&w,",\"field\":");string(&w,v->field);put(&w,"}");}
        put(&w,"}");
    }
    put(&w,"}");
    put(&w,",\"triggers\":[");first=1;
    for(int i=0;i<NR_TRIGGERS;i++)if(s->triggers[i].used) {
        const Trigger*t=&s->triggers[i];if(!first)put(&w,",");first=0;
        put(&w,"{\"id\":");integer(&w,t->id);put(&w,",\"conditionNodes\":");integer(&w,t->conditionCount);
        put(&w,",\"truth\":");put(&w,t->lastTruth?"true":"false");put(&w,",\"pending\":");put(&w,t->pending?"true":"false");
        put(&w,",\"fireCount\":");integer(&w,t->fireCount);put(&w,",\"lastFireUs\":");integer(&w,t->lastFireUs);
        put(&w,",\"event\":");string(&w,t->eventPath);put(&w,",\"lastIntent\":");integer(&w,t->lastIntent);
        put(&w,",\"pendingIntent\":");integer(&w,t->pendingIntent);
        put(&w,",\"valueSource\":");string(&w,(s->triggerFormulas[i].count||s->triggerDataFormulas[i].tree.count)?"expression":t->source==NR_TRIGGER_SOURCE_INTENT_VALUE?"intentValue":"constant");
        put(&w,",\"expressionNodes\":");integer(&w,s->triggerFormulas[i].count+s->triggerDataFormulas[i].tree.count);
        if(s->triggerGuardFormulas[i].tree.count){put(&w,",\"guardExpressionNodes\":");integer(&w,s->triggerGuardFormulas[i].tree.count);}
        put(&w,",\"lastIntentSource\":");const Intent*accepted=intentById(s,t->lastIntent);
        if(accepted)intentRecord(&w,s,accepted);else put(&w,"null");
        put(&w,",\"intentCandidate\":");
        const Intent*candidate=0;uint64_t candidateId=0;
        if(t->eventPath[0])for(int k=0;k<NR_INTENTS;k++) {
            const Intent*q=&s->intents[k];
            if(q->used&&q->id>t->lastIntent&&!strcmp(q->event,t->eventPath)&&(!candidateId||q->id<candidateId)) {
                candidate=q;candidateId=q->id;
            }
        }
        if(candidate)intentRecord(&w,s,candidate);else put(&w,"null");
        put(&w,"}");
    }
    put(&w,"],\"accessibility\":{\"reducedMotion\":");put(&w,s->reducedMotion?"true":"false");
    put(&w,",\"screenReader\":");put(&w,s->screenReader?"true":"false");
    put(&w,"},\"floor\":{\"wetness\":");number(&w,s->floor.wetness);
    put(&w,",\"collisionEnabled\":");put(&w,s->floor.enabled?"true":"false");
    put(&w,",\"renderVisible\":");put(&w,s->floor.visible?"true":"false");
    put(&w,"},\"geometry\":{\"triangles\":");integer(&w,s->meshCount);
    put(&w,",\"collisionTriangles\":");integer(&w,s->geometry.index.triangleCount);
    put(&w,",\"bvhNodes\":");integer(&w,s->geometry.index.nodeCount);
    put(&w,",\"meshGeneration\":");integer(&w,s->geometry.meshGeneration);
    put(&w,",\"contactBudgetExhausted\":");integer(&w,s->geometry.contactBudgetExhausted);
    put(&w,",\"collisionQueries\":");integer(&w,s->geometry.collisionQueries);
    put(&w,",\"triangleTests\":");integer(&w,s->geometry.triangleTests);
    put(&w,"},\"surfaces\":[");first=1;
    for(int i=0;i<NR_SURFACES;i++)if(s->geometry.surfaces[i].used) {
        const Surface*q=&s->geometry.surfaces[i];int individual=0,tiles=0;uint64_t aggregate=0;
        for(int k=0;k<NR_DEPOSITS;k++)if(s->deposits[k].used&&s->geometry.depositContacts[k].surfaceId==i+1)individual++;
        for(int k=0;k<NR_TILES;k++)if(s->tiles[k].used&&s->geometry.tileSurfaces[k].surfaceId==i+1) {tiles++;aggregate+=s->tiles[k].count;}
        if(!first)put(&w,",");first=0;
        put(&w,"{\"id\":");integer(&w,i+1);
        put(&w,",\"collisionEnabled\":");put(&w,q->collisionEnabled?"true":"false");
        put(&w,",\"renderVisible\":");put(&w,q->renderVisible?"true":"false");
        put(&w,",\"restitution\":");number(&w,q->restitution);
        put(&w,",\"friction\":");number(&w,q->friction);
        put(&w,",\"settleSpeed\":");number(&w,q->settleSpeed);
        put(&w,",\"reentrainWindSpeed\":");number(&w,q->reentrain);
        put(&w,",\"maxIndividual\":");integer(&w,q->maxIndividual);
        put(&w,",\"maxTiles\":");integer(&w,q->maxTiles);
        put(&w,",\"overflow\":");string(&w,q->overflow?"merge-to-field":"reject-new");
        put(&w,",\"retentionUs\":");integer(&w,q->retentionUs);
        put(&w,",\"fadeUs\":");integer(&w,q->fadeUs);
        put(&w,",\"wetnessGain\":");number(&w,q->wetnessGain);
        put(&w,",\"evaporation\":");number(&w,q->evaporation);
        put(&w,",\"heatGain\":");number(&w,q->heatGain);
        put(&w,",\"cooling\":");number(&w,q->cooling);
        put(&w,",\"thermalEvaporation\":");number(&w,q->thermalEvaporation);
        put(&w,",\"wetnessDarkening\":");number(&w,q->wetnessDarkening);
        put(&w,",\"heatColor\":");integer(&w,q->heatColor);
        put(&w,",\"heatTintStrength\":");number(&w,q->heatTintStrength);
        put(&w,",\"wetness\":");number(&w,q->wetness);
        put(&w,",\"heat\":");number(&w,q->heat);
        put(&w,",\"impacts\":");integer(&w,q->impacts);
        put(&w,",\"rejectedDeposits\":");integer(&w,q->rejectedDeposits);
        put(&w,",\"individualDeposits\":");integer(&w,individual);
        put(&w,",\"aggregateDeposits\":");integer(&w,aggregate);
        put(&w,",\"aggregateTiles\":");integer(&w,tiles);put(&w,"}");
    }
    put(&w,"]");int hasFloatBody=0;for(int i=0;i<NR_FLOAT_BODIES;i++)if(s->floatBodies[i].used)hasFloatBody=1;
    if(hasFloatBody) {
        put(&w,",\"floatBodies\":[");first=1;
        for(int i=0;i<NR_FLOAT_BODIES;i++)if(s->floatBodies[i].used) {
            const FloatBody*b=&s->floatBodies[i];if(!first)put(&w,",");first=0;
            put(&w,"{\"id\":");integer(&w,b->id);put(&w,",\"surfaceId\":");integer(&w,b->surfaceId);
            put(&w,",\"position\":");vec(&w,b->position);put(&w,",\"velocity\":");vec(&w,b->velocity);put(&w,",\"normal\":");vec(&w,b->normal);
            put(&w,",\"mass\":");number(&w,b->mass);put(&w,",\"radius\":");number(&w,b->radius);put(&w,",\"fluidDensity\":");number(&w,b->density);
            put(&w,",\"gravity\":");number(&w,b->gravity);put(&w,",\"drag\":");number(&w,b->drag);put(&w,",\"immersion\":");number(&w,b->immersion);put(&w,",\"buoyantForce\":");number(&w,b->buoyantForce);
            const FloatHull*h=&s->floatHulls[i];if(h->used){
                put(&w,",\"hull\":{\"vertexCount\":");integer(&w,h->vertexCount);put(&w,",\"faceCount\":");integer(&w,h->faceCount);
                put(&w,",\"volume\":");number(&w,h->volume);put(&w,",\"orientation\":[");for(int k=0;k<4;k++){if(k)put(&w,",");number(&w,h->orientation[k]);}put(&w,"]");
                put(&w,",\"angularVelocity\":");vec(&w,h->angularVelocity);put(&w,",\"inertia\":");vec(&w,h->inertia);put(&w,",\"centerOfMass\":");vec(&w,h->centerOfMass);put(&w,"}");
            }
            put(&w,",\"visible\":");put(&w,b->visible?"true":"false");put(&w,",\"color\":");integer(&w,b->color);put(&w,"}");
        }put(&w,"]");
    }
    int hasSurfaceFluid=0;for(int i=0;i<NR_SURFACES;i++)if(s->surfaceFluids[i].used)hasSurfaceFluid=1;
    if(hasSurfaceFluid){put(&w,",\"surfaceFluids\":[");first=1;for(int i=0;i<NR_SURFACES;i++)if(s->surfaceFluids[i].used){
        const SurfaceFluid*f=&s->surfaceFluids[i];if(!first)put(&w,",");first=0;put(&w,"{\"surfaceId\":");integer(&w,i+1);put(&w,",\"active\":");put(&w,f->used==1?"true":"false");put(&w,",\"mass\":");number(&w,f->mass);
        put(&w,",\"velocity\":");vec(&w,f->velocity);put(&w,",\"offset\":");vec(&w,f->offset);put(&w,",\"initialMomentum\":");vec(&w,f->initialMomentum);put(&w,",\"bodyImpulse\":");vec(&w,f->bodyImpulse);put(&w,",\"dissipatedEnergy\":");number(&w,f->dissipatedEnergy);put(&w,",\"initialEnergy\":");number(&w,f->initialEnergy);put(&w,",\"exported\":");put(&w,f->used==3?"true":"false");
        const SurfaceFluidHistory*h=&s->fluidHistory[i];put(&w,",\"history\":{\"mass\":");number(&w,h->mass);put(&w,",\"energy\":");number(&w,h->energy);put(&w,",\"momentum\":");vec(&w,h->momentum);put(&w,",\"initialMomentum\":");vec(&w,h->initialMomentum);put(&w,",\"bodyImpulse\":");vec(&w,h->bodyImpulse);put(&w,",\"initialEnergy\":");number(&w,h->initialEnergy);put(&w,",\"dissipatedEnergy\":");number(&w,h->dissipatedEnergy);put(&w,",\"exports\":");integer(&w,h->exports);put(&w,"}}");}put(&w,"]");}
    int hasAngular=0;for(int i=0;i<NR_SURFACES;i++)if(s->angularFluids[i].used||s->angularHistory[i].exports)hasAngular=1;
    if(hasAngular){put(&w,",\"surfaceFluidAngular\":[");first=1;for(int i=0;i<NR_SURFACES;i++)if(s->angularFluids[i].used||s->angularHistory[i].exports){
        const SurfaceFluidAngular*f=&s->angularFluids[i];const SurfaceFluidAngularHistory*h=&s->angularHistory[i];
        if(!first)put(&w,",");first=0;put(&w,"{\"surfaceId\":");integer(&w,i+1);put(&w,",\"recordPresent\":");put(&w,f->used?"true":"false");
        put(&w,",\"active\":");put(&w,f->used&&s->surfaceFluids[i].used==1?"true":"false");put(&w,",\"exported\":");put(&w,f->used&&s->surfaceFluids[i].used==3?"true":"false");
        put(&w,",\"inertia\":");number(&w,f->inertia);put(&w,",\"omega\":");vec(&w,f->omega);put(&w,",\"initialMomentum\":");vec(&w,f->initialMomentum);put(&w,",\"bodyImpulse\":");vec(&w,f->bodyImpulse);
        const SurfaceFluidPose*pose=&s->surfacePoses[i];put(&w,",\"pose\":");
        if(pose->used){put(&w,"{\"orientation\":[");for(int axis=0;axis<4;axis++){if(axis)put(&w,",");number(&w,pose->orientation[axis]);}put(&w,"],\"pivot\":");vec(&w,pose->pivot);put(&w,"}");}else put(&w,"null");
        put(&w,",\"dissipatedEnergy\":");number(&w,f->dissipatedEnergy);put(&w,",\"initialEnergy\":");number(&w,f->initialEnergy);
        put(&w,",\"history\":{\"inertia\":");number(&w,h->inertia);put(&w,",\"energy\":");number(&w,h->energy);put(&w,",\"momentum\":");vec(&w,h->momentum);put(&w,",\"initialMomentum\":");vec(&w,h->initialMomentum);put(&w,",\"bodyImpulse\":");vec(&w,h->bodyImpulse);
        put(&w,",\"initialEnergy\":");number(&w,h->initialEnergy);put(&w,",\"dissipatedEnergy\":");number(&w,h->dissipatedEnergy);put(&w,",\"exports\":");integer(&w,h->exports);put(&w,"}}");
    }put(&w,"]");}
    int hasPathActor=0;for(int i=0;i<16;i++)if(s->pathActors[i].used)hasPathActor=1;
    if(hasPathActor){put(&w,",\"pathActors\":[");first=1;for(int i=0;i<16;i++)if(s->pathActors[i].used){
        if(!first)put(&w,",");first=0;put(&w,"{\"id\":");integer(&w,s->pathActors[i].id);put(&w,",\"targetId\":");integer(&w,s->pathActors[i].targetId);
        put(&w,",\"family\":");string(&w,(const char*[]){"camera","emitter","window","node"}[s->pathActors[i].family]);
        put(&w,",\"speed\":");number(&w,s->pathActors[i].speed);put(&w,",\"distance\":");number(&w,s->pathActors[i].distance);put(&w,",\"startUs\":");integer(&w,s->pathActors[i].startUs);
        Vec3 position;put(&w,",\"position\":");if(nrPathTargetPosition(s,i,&position))vec(&w,position);else put(&w,"null");put(&w,"}");
    }put(&w,"]");}
    int hasFlow=0;for(int i=0;i<8;i++)if(s->flows[i].used)hasFlow=1;
    if(hasFlow){put(&w,",\"flows\":[");first=1;for(int i=0;i<8;i++)if(s->flows[i].used){
        double volumes[18];nrFlowVolumes(s,i,volumes);if(!first)put(&w,",");first=0;
        put(&w,"{\"id\":");integer(&w,s->flows[i].id);
        put(&w,",\"injectedVolume\":");number(&w,volumes[0]);
        put(&w,",\"flux\":");number(&w,volumes[9]);
        put(&w,",\"outletFlux\":");number(&w,volumes[9+s->flows[i].count]);
        put(&w,",\"deliveredVolume\":");number(&w,volumes[s->flows[i].count]);
        put(&w,",\"storedVolume\":");number(&w,volumes[0]-volumes[s->flows[i].count]);
        put(&w,",\"stages\":[");for(int k=0;k<s->flows[i].count;k++){if(k)put(&w,",");put(&w,"{\"name\":");string(&w,s->flows[i].stages[k].name);put(&w,",\"deliveredVolume\":");number(&w,volumes[k+1]);put(&w,",\"flux\":");number(&w,volumes[10+k]);put(&w,",\"storedVolume\":");number(&w,volumes[k]-volumes[k+1]);put(&w,"}");}put(&w,"]}");
    }put(&w,"]");}
    int hasSink=0;for(int i=0;i<NR_SURFACES;i++)if(s->flowSinks[i].flowId)hasSink=1;
    if(hasSink){put(&w,",\"flowSinks\":[");first=1;for(int i=0;i<NR_SURFACES;i++)if(s->flowSinks[i].flowId){double out[4];nrFlowSinkVolumes(s,i,out);if(!first)put(&w,",");first=0;put(&w,"{\"surfaceId\":");integer(&w,i+1);put(&w,",\"flowId\":");integer(&w,s->flowSinks[i].flowId);put(&w,",\"receivedVolume\":");number(&w,out[0]);put(&w,",\"retainedVolume\":");number(&w,out[1]);put(&w,",\"evaporatedVolume\":");number(&w,out[2]);put(&w,",\"wetness\":");number(&w,out[3]);put(&w,"}");}put(&w,"]");}
    int hasSpray=0;for(int i=0;i<(int)NR_MAX_EMITTERS;i++)if(s->flowSprays[i].flowId)hasSpray=1;
    if(hasSpray){put(&w,",\"flowSprays\":[");first=1;for(int i=0;i<(int)NR_MAX_EMITTERS;i++)if(s->flowSprays[i].flowId){double out[3];nrFlowSprayVolumes(s,i,out);if(!first)put(&w,",");first=0;put(&w,"{\"emitterId\":");integer(&w,s->emitters[i].id);put(&w,",\"flowId\":");integer(&w,s->flowSprays[i].flowId);put(&w,",\"receivedVolume\":");number(&w,out[0]);put(&w,",\"flowReceivedVolume\":");number(&w,out[0]-s->sprayReentrained[i]);put(&w,",\"reentrainedVolume\":");number(&w,s->sprayReentrained[i]);put(&w,",\"emittedVolume\":");number(&w,out[1]);put(&w,",\"pendingVolume\":");number(&w,out[2]);double life[5];nrFlowSprayLifecycle(s,i,life);put(&w,",\"liveVolume\":");number(&w,life[0]);put(&w,",\"expiredVolume\":");number(&w,life[1]);put(&w,",\"impactedVolume\":");number(&w,life[2]);put(&w,",\"exportedVolume\":");number(&w,life[3]);put(&w,",\"legacyUnresolvedVolume\":");number(&w,life[4]);put(&w,"}");}put(&w,"]");}
    int hasWater=0;for(int i=0;i<NR_SURFACES;i++)if(s->surfaceWater.settings[i].used)hasWater=1;
    if(hasWater){put(&w,",\"surfaceWater\":[");first=1;for(int i=0;i<NR_SURFACES;i++)if(s->surfaceWater.settings[i].used){double out[6];nrSurfaceWaterTotals(s,i,out);if(!first)put(&w,",");first=0;put(&w,"{\"surfaceId\":");integer(&w,i+1);put(&w,",\"receivedVolume\":");number(&w,out[0]);put(&w,",\"retainedVolume\":");number(&w,out[1]);put(&w,",\"evaporatedVolume\":");number(&w,out[2]);put(&w,",\"exportedVolume\":");number(&w,out[3]);put(&w,",\"importedVolume\":");number(&w,out[4]);put(&w,",\"transferredVolume\":");number(&w,out[5]);put(&w,",\"cells\":[");int firstCell=1;for(int k=0;k<s->meshCount;k++)if(s->geometry.triangleSurfaces[k]==i+1){double cell[3];nrSurfaceWaterCell(s,k,cell);if(!firstCell)put(&w,",");firstCell=0;put(&w,"{\"triangleIndex\":");integer(&w,k);put(&w,",\"receivedVolume\":");number(&w,cell[0]-s->waterTransfers[k].incoming);put(&w,",\"importedVolume\":");number(&w,s->waterTransfers[k].incoming);put(&w,",\"transferredVolume\":");number(&w,s->waterTransfers[k].outgoing);put(&w,",\"retainedVolume\":");number(&w,cell[1]);put(&w,",\"wetness\":");number(&w,cell[2]);put(&w,"}");}put(&w,"]}");}put(&w,"]");}
    int hasFlowThickness=0;for(int i=0;i<NR_SURFACES;i++)if(s->flowThickness[i].used)hasFlowThickness=1;
    if(hasFlowThickness){put(&w,",\"flowThickness\":[");first=1;for(int i=0;i<NR_SURFACES;i++)if(s->flowThickness[i].used){double values[6];nrFlowThickness(c,i+1,values,6);if(!first)put(&w,",");first=0;put(&w,"{\"surfaceId\":");integer(&w,i+1);put(&w,",\"flux\":");number(&w,values[0]);put(&w,",\"depth\":");number(&w,values[1]);put(&w,",\"area\":");number(&w,values[2]);put(&w,",\"width\":");number(&w,values[3]);put(&w,",\"speed\":");number(&w,values[4]);put(&w,",\"maxDepth\":");number(&w,values[5]);put(&w,",\"direction\":");vec(&w,s->flowThickness[i].direction);put(&w,"}");}put(&w,"]");}
    int hasFoamTransport=0;for(int i=0;i<NR_SURFACES;i++)if(s->foamVelocity[i].x||s->foamVelocity[i].z)hasFoamTransport=1;
    if(hasFoamTransport){put(&w,",\"foamTransport\":[");first=1;for(int i=0;i<NR_SURFACES;i++)if(s->foamVelocity[i].x||s->foamVelocity[i].z){if(!first)put(&w,",");first=0;put(&w,"{\"surfaceId\":");integer(&w,i+1);put(&w,",\"velocity\":[");number(&w,s->foamVelocity[i].x);put(&w,",");number(&w,s->foamVelocity[i].z);put(&w,"]}");}put(&w,"]");}
    int hasWaterLink=0;for(int i=0;i<64;i++)if(s->waterLinks[i].used)hasWaterLink=1;
    if(hasWaterLink){put(&w,",\"waterLinks\":[");first=1;for(int i=0;i<64;i++)if(s->waterLinks[i].used){if(!first)put(&w,",");first=0;put(&w,"{\"id\":");integer(&w,s->waterLinks[i].id);put(&w,",\"fromTriangle\":");integer(&w,s->waterLinks[i].from);put(&w,",\"toTriangle\":");integer(&w,s->waterLinks[i].to);put(&w,",\"rate\":");number(&w,s->waterLinks[i].rate);if(s->waterLinkHeatCapacity[i]>0){put(&w,",\"heatCapacityPerVolume\":");number(&w,s->waterLinkHeatCapacity[i]);}put(&w,",\"startUs\":");integer(&w,s->waterLinks[i].startUs);put(&w,"}");}put(&w,"]");}
    int hasMaterialHeat=s->materialHeatLedger.initial||s->materialHeatLedger.imported||s->materialHeatLedger.transferred||s->materialHeatLedger.exported;
    for(int i=0;i<NR_MATERIALS;i++)if(s->materialHeat[i].id)hasMaterialHeat=1;
    for(int i=0;i<(int)NR_MAX_PARTICLES;i++)if(s->particleHeat[i].id)hasMaterialHeat=1;
    for(int i=0;i<NR_DEPOSITS;i++)if(s->depositHeat[i].id)hasMaterialHeat=1;
    for(int i=0;i<NR_TILES;i++)if(s->aggregateHeat[i].id)hasMaterialHeat=1;
    if(hasMaterialHeat){put(&w,",\"materialThermal\":{\"initialEnergy\":");number(&w,s->materialHeatLedger.initial);put(&w,",\"liveEnergy\":");number(&w,nrHeatLiveEnergy(s));put(&w,",\"importedEnergy\":");number(&w,s->materialHeatLedger.imported);put(&w,",\"transferredEnergy\":");number(&w,s->materialHeatLedger.transferred);put(&w,",\"exportedEnergy\":");number(&w,s->materialHeatLedger.exported);
        for(int family=0;family<4;family++){put(&w,family==0?",\"materials\":[":family==1?",\"particles\":[":family==2?",\"deposits\":[":",\"aggregates\":[");first=1;int count=family==0?NR_MATERIALS:family==1?(int)NR_MAX_PARTICLES:family==2?NR_DEPOSITS:NR_TILES;
            for(int i=0;i<count;i++){const HeatReservoir*r=family==0?&s->materialHeat[i]:family==1?&s->particleHeat[i]:family==2?&s->depositHeat[i]:&s->aggregateHeat[i];if(!r->id)continue;if(!first)put(&w,",");first=0;heatRecord(&w,r,family==0||family==3?i:(int)r->id);}put(&w,"]");}
        put(&w,"}");}
    int hasThermal=s->thermalHistory.initial!=0||s->thermalHistory.applied!=0||s->thermalHistory.environment!=0||s->thermalHistory.exported!=0;for(int i=0;i<NR_MESH;i++)if(s->thermalCells[i].used)hasThermal=1;
    if(hasThermal){put(&w,",\"surfaceThermal\":{\"exportedEnergy\":");number(&w,s->thermalHistory.exported);put(&w,",\"historicalLatentEnergy\":");number(&w,s->historicalLatentEnergy);put(&w,",\"historicalInitialEnergy\":");number(&w,s->thermalHistory.initial);put(&w,",\"historicalAppliedEnergy\":");number(&w,s->thermalHistory.applied);put(&w,",\"historicalEnvironmentEnergy\":");number(&w,s->thermalHistory.environment);put(&w,",\"historicalImportedEnergy\":");number(&w,s->thermalHistoricalTransfers.incoming);put(&w,",\"historicalTransferredEnergy\":");number(&w,s->thermalHistoricalTransfers.outgoing);put(&w,",\"cells\":[");first=1;for(int i=0;i<NR_MESH;i++)if(s->thermalCells[i].used){double out[4];nrThermalCell(s,i,out);if(!first)put(&w,",");first=0;put(&w,"{\"triangleIndex\":");integer(&w,i);put(&w,",\"temperature\":");number(&w,out[0]);put(&w,",\"energy\":");number(&w,out[1]);put(&w,",\"initialEnergy\":");number(&w,s->thermalCells[i].initialEnergy);put(&w,",\"appliedEnergy\":");number(&w,out[2]);put(&w,",\"environmentEnergy\":");number(&w,out[3]);put(&w,",\"importedEnergy\":");number(&w,s->thermalTransfers[i].incoming);put(&w,",\"transferredEnergy\":");number(&w,s->thermalTransfers[i].outgoing);put(&w,",\"latentHeatPerVolume\":");number(&w,s->latentHeat[i].coefficient);put(&w,",\"evaporatedEnergy\":");number(&w,nrLatentEnergy(s,i));put(&w,"}");}put(&w,"]}");}
    int hasThermalLink=0;for(int i=0;i<64;i++)if(s->thermalLinks[i].used)hasThermalLink=1;
    if(hasThermalLink){put(&w,",\"thermalLinks\":[");first=1;for(int i=0;i<64;i++)if(s->thermalLinks[i].used){if(!first)put(&w,",");first=0;put(&w,"{\"id\":");integer(&w,s->thermalLinks[i].id);put(&w,",\"fromTriangle\":");integer(&w,s->thermalLinks[i].from);put(&w,",\"toTriangle\":");integer(&w,s->thermalLinks[i].to);put(&w,",\"conductance\":");number(&w,s->thermalLinks[i].conductance);put(&w,",\"startUs\":");integer(&w,s->thermalLinks[i].startUs);put(&w,"}");}put(&w,"]");}
    int hasArt=0;for(int i=0;i<4;i++)if(s->cellArt[i].used)hasArt=1;
    if(hasArt){put(&w,",\"cellArt\":[");first=1;for(int i=0;i<4;i++)if(s->cellArt[i].used){
        if(!first)put(&w,",");first=0;put(&w,"{\"id\":");integer(&w,s->cellArt[i].id);
        put(&w,",\"width\":");integer(&w,s->cellArt[i].width);put(&w,",\"height\":");integer(&w,s->cellArt[i].height);
        put(&w,",\"x\":");integer(&w,s->cellArt[i].x);put(&w,",\"y\":");integer(&w,s->cellArt[i].y);
        put(&w,",\"alpha\":");number(&w,s->cellArt[i].alpha);put(&w,",\"layer\":\"");put(&w,s->cellArt[i].layer?"overlay":"background");put(&w,"\",\"cells\":[");
        for(int k=0;k<s->cellArt[i].width*s->cellArt[i].height;k++){if(k)put(&w,",");put(&w,"[");for(int word=0;word<3;word++){if(word)put(&w,",");integer(&w,s->cellArt[i].cells[k][word]);}put(&w,"]");}put(&w,"]}");
    }put(&w,"]");}
    put(&w,",\"aggregateReemittedCount\":");integer(&w,s->aggregateReemittedCount);
    put(&w,",\"electricalArcs\":[");first=1;
    for(int i=0;i<16;i++)if(s->electricalArcs[i].id){
        const ElectricalArc*a=&s->electricalArcs[i];double rows[31][7],opacity;int phase;uint64_t cycle;
        int count=nrElectricalSegments(s,a,rows,&opacity,&phase,&cycle);
        if(!first)put(&w,",");first=0;
        put(&w,"{\"id\":");integer(&w,a->id);put(&w,",\"seed\":");integer(&w,a->seed);put(&w,",\"material\":");integer(&w,a->material);
        put(&w,",\"startUs\":");integer(&w,a->startUs);put(&w,",\"speed\":");number(&w,a->speed);
        put(&w,",\"jitter\":");number(&w,a->jitter);put(&w,",\"flicker\":");number(&w,a->flicker);put(&w,",\"alpha\":");number(&w,a->alpha);
        put(&w,",\"delayUs\":");integer(&w,a->delayUs);put(&w,",\"holdUs\":");integer(&w,a->holdUs);put(&w,",\"fadeUs\":");integer(&w,a->fadeUs);put(&w,",\"repeatUs\":");integer(&w,a->periodUs);
        put(&w,",\"phase\":\"");put(&w,arcPhases[phase]);put(&w,"\",\"cycle\":");integer(&w,cycle);put(&w,",\"opacity\":");number(&w,opacity);
        put(&w,",\"points\":[");for(uint32_t k=0;k<a->count;k++){if(k)put(&w,",");put(&w,"{\"position\":");vec(&w,a->points[k].position);put(&w,",\"parent\":");integer(&w,a->points[k].parent);put(&w,"}");}
        put(&w,"],\"segments\":[");for(int k=0;k<count;k++){if(k)put(&w,",");put(&w,"[");for(int word=0;word<7;word++){if(word)put(&w,",");number(&w,rows[k][word]);}put(&w,"]");}put(&w,"]}");
    }put(&w,"]");
    put(&w,",\"aggregateMaterials\":[");first=1;
    for(int i=0;i<NR_TILES;i++)if(s->tiles[i].used){const AggregateProvenance*r=&s->aggregateProvenance[i];if(!first)put(&w,",");first=0;
        put(&w,"{\"tileIndex\":");integer(&w,i);put(&w,",\"count\":");integer(&w,s->tiles[i].count);put(&w,",\"emitterId\":");integer(&w,s->tiles[i].emitterId);
        put(&w,",\"emitterGeneration\":");integer(&w,r->generation);put(&w,",\"material\":");integer(&w,r->material);put(&w,",\"seed\":");integer(&w,r->seed);put(&w,",\"emissionOrdinal\":");integer(&w,r->emitted);
        int ei=nrFindEmitter(s,(int)s->tiles[i].emitterId);const SurfaceTile*g=&s->geometry.tileSurfaces[i];int available=r->used&&ei>=0&&s->emitters[ei].generation==r->generation&&(!g->surfaceId||g->meshGeneration==s->geometry.meshGeneration);
        put(&w,",\"canReemit\":");put(&w,available?"true":"false");put(&w,"}");
    }put(&w,"]");
    put(&w,",\"contacts\":[");first=1;
    for(int i=0;i<(int)NR_MAX_PARTICLES;i++)if(s->particles[i].state&&s->geometry.particleContacts[i].used) {
        const SurfaceContact*q=&s->geometry.particleContacts[i];if(!first)put(&w,",");first=0;
        put(&w,"{\"particleId\":");integer(&w,s->particles[i].id);
        put(&w,",\"surfaceId\":");integer(&w,q->surfaceId);
        put(&w,",\"triangleIndex\":");integer(&w,q->triangleIndex);
        put(&w,",\"normal\":");vec(&w,q->normal);put(&w,"}");
    }
    put(&w,"],\"surfaceTiles\":[");first=1;
    for(int i=0;i<NR_TILES;i++)if(s->tiles[i].used&&s->geometry.tileSurfaces[i].surfaceId) {
        const SurfaceTile*q=&s->geometry.tileSurfaces[i];if(!first)put(&w,",");first=0;
        put(&w,"{\"surfaceId\":");integer(&w,q->surfaceId);
        put(&w,",\"emitterId\":");integer(&w,s->tiles[i].emitterId);
        put(&w,",\"triangleIndex\":");integer(&w,q->triangleIndex);
        put(&w,",\"meshGeneration\":");integer(&w,q->meshGeneration);
        put(&w,",\"count\":");integer(&w,s->tiles[i].count);
        put(&w,",\"normal\":");vec(&w,q->normal);
        put(&w,",\"a\":");vec(&w,q->a);put(&w,",\"b\":");vec(&w,q->b);put(&w,",\"c\":");vec(&w,q->c);put(&w,"}");
    }
    put(&w,"],\"pending\":[");first=1;
    for(int i=0;i<NR_PENDING;i++)if(s->pending[i].used) {
        const PendingCommand*q=&s->pending[i];if(!first)put(&w,",");first=0;
        put(&w,"{\"id\":");integer(&w,q->id);put(&w,",\"atUs\":");integer(&w,q->atUs);
        put(&w,",\"sequence\":");integer(&w,q->sequence);put(&w,",\"command\":");put(&w,q->command);put(&w,"}");
    }
    put(&w,"],\"emitters\":[");first=1;
    for(int i=0;i<(int)NR_MAX_EMITTERS;i++)if(s->emitters[i].used) {
        const Emitter*q=&s->emitters[i];int live=0,deposited=0;
        for(int k=0;k<(int)NR_MAX_PARTICLES;k++)if(s->particles[k].state&&s->particles[k].emitterId==q->id)live++;
        for(int k=0;k<NR_DEPOSITS;k++)if(s->deposits[k].used&&s->deposits[k].emitterId==q->id)deposited++;
        for(int k=0;k<NR_TILES;k++)if(s->tiles[k].used&&s->tiles[k].emitterId==q->id)deposited+=(int)s->tiles[k].count;
        uint64_t end=q->startUs+(q->runningUs+q->gapUs)*(uint64_t)(q->cycles-1)+q->runningUs;
        int pendingBurst=q->rate==0&&!q->runningUs&&q->born<q->count*q->cycles;
        const char*phase=!q->stopping&&s->timeUs<q->startUs?"scheduled":!q->stopping&&(pendingBurst||(q->rate>0&&!q->runningUs)||s->timeUs<end)?"emitting":live?"draining":deposited?"settled":"terminal";
        if(!first)put(&w,",");first=0;
        put(&w,"{\"id\":");integer(&w,q->id);put(&w,",\"effect\":");string(&w,nrEffectName(q->effect));
        put(&w,",\"alpha\":");number(&w,q->alpha);
        put(&w,",\"phase\":");string(&w,phase);put(&w,",\"attemptedBirths\":");integer(&w,q->born);
        put(&w,",\"active\":");integer(&w,live);put(&w,",\"deposited\":");integer(&w,deposited);
        put(&w,",\"rate\":");number(&w,q->rate);put(&w,",\"count\":");integer(&w,q->count);
        put(&w,",\"cycles\":");integer(&w,q->cycles);put(&w,",\"shapeWeights\":");vec(&w,q->shapeWeights);put(&w,",\"sampling\":");string(&w,q->sampling==0?"cell":q->sampling==1?"half":q->sampling==2?"braille":"hybrid");put(&w,",\"surfaceAlpha\":");number(&w,q->surfaceAlpha);
        put(&w,",\"distribution\":");string(&w,q->shape>=5?"uniform":"legacy");
        if(nrEffectAlgorithm(q->effect)==4){
            BurstControls b=nrBurstControls(s,i);int total=0,samples=0;double stage[4];
            for(int k=0;k<(int)NR_MAX_PARTICLES;k++)if(s->particles[k].emitterSlot==i&&nrBurstAppearance(s,k,stage))total++;
            put(&w,",\"burstStages\":{\"sampleLimit\":16,\"activeBurstParticles\":");integer(&w,total);
            put(&w,",\"glitterHz\":");number(&w,b.glitterHz);put(&w,",\"glitterDepth\":");number(&w,b.glitterDepth);
            put(&w,",\"coreAlpha\":");number(&w,b.coreAlpha);put(&w,",\"coreUs\":");integer(&w,q->coreUs);
            put(&w,",\"residualUs\":");integer(&w,b.residualUs);put(&w,",\"residualAlpha\":");number(&w,b.residualAlpha);
            put(&w,",\"samples\":[");for(int k=0;k<(int)NR_MAX_PARTICLES&&samples<16;k++)if(s->particles[k].emitterSlot==i&&nrBurstAppearance(s,k,stage)){
                if(samples++)put(&w,",");put(&w,"[");integer(&w,s->particles[k].id);put(&w,",");integer(&w,s->particles[k].seed);
                for(int word=0;word<4;word++){put(&w,",");number(&w,stage[word]);}put(&w,"]");
            }put(&w,"]}");
        }
        if(nrEffectAlgorithm(q->effect)==5&&(nrEffectProfile(q->effect)==1||nrEffectProfile(q->effect)==2)){
            put(&w,",\"worldShellProfile\":{\"shape\":\"");put(&w,nrEffectProfile(q->effect)==1?"clumpy-fibonacci":"uniform-fibonacci");
            put(&w,"\",\"active\":");put(&w,q->topology==5?"true":"false");
            put(&w,",\"radiusAtBirth\":");number(&w,q->radius);put(&w,",\"radialExpansionRate\":");number(&w,q->radius*4.2);put(&w,"}");
        }
        if(nrEffectAlgorithm(q->effect)==5&&nrEffectProfile(q->effect)==1){
            int total=0,samples=0;double v[4];
            for(int k=0;k<(int)NR_MAX_PARTICLES;k++)if(s->particles[k].emitterSlot==i&&s->novaOptics[k].profile&&s->particles[k].state==1)total++;
            put(&w,",\"novaOptics\":{\"sampleLimit\":16,\"activeCapturedParticles\":");integer(&w,total);put(&w,",\"samples\":[");
            for(int k=0;k<(int)NR_MAX_PARTICLES&&samples<16;k++)if(s->particles[k].emitterSlot==i&&nrNovaAppearance(s,k,v)){
                const NovaOptics*n=&s->novaOptics[k];if(samples++)put(&w,",");put(&w,"[");integer(&w,s->particles[k].id);put(&w,",");integer(&w,n->seed);put(&w,",");integer(&w,n->count);put(&w,",");integer(&w,n->index);
                for(int word=0;word<4;word++){put(&w,",");number(&w,v[word]);}put(&w,"]");
            }put(&w,"]}");
        }
        if(s->studioNovaControls[i].used){
            const StudioNovaControls*b=&s->studioNovaControls[i];StudioNovaSample sample;nrStudioNovaSample(s,i,&sample);double center[3]={0};int visible=nrStudioNovaCenter(s,i,center);
            put(&w,",\"studioNova\":{\"paint\":");string(&w,b->used==2?"source":"material");put(&w,",\"elapsedUs\":");integer(&w,s->timeUs-b->startUs);put(&w,",\"visible\":");put(&w,visible?"true":"false");
            put(&w,",\"center\":[");for(int k=0;k<3;k++){if(k)put(&w,",");number(&w,center[k]);}put(&w,"]");
            put(&w,",\"envelope\":");integer(&w,sample.envelope);
            put(&w,",\"glyph\":");integer(&w,sample.glyph);
            put(&w,",\"glyphIndex\":");integer(&w,sample.glyphIndex);
            put(&w,",\"coreColor\":");integer(&w,sample.coreColor);
            put(&w,",\"radialSamples\":[");for(int k=0;k<16;k++){if(k)put(&w,",");put(&w,"[");integer(&w,k*256);put(&w,",");integer(&w,nrStudioNovaRing(b,(s->timeUs-b->startUs)/1000,k*256,0));put(&w,",");integer(&w,nrStudioNovaRingColor(b,k*256,0));put(&w,"]");}put(&w,"],\"controls\":{");
            put(&w,"\"seed\":");integer(&w,b->seed);
            put(&w,",\"novaDurationMs\":");integer(&w,b->novaDurationMs);
            put(&w,",\"rippleSpeed\":");integer(&w,b->rippleSpeed);
            put(&w,",\"rippleWidth\":");integer(&w,b->rippleWidth);
            put(&w,",\"rippleOpacity\":");integer(&w,b->rippleOpacity);
            put(&w,",\"rippleRings\":");integer(&w,b->rippleRings);
            put(&w,",\"cellAspect\":");integer(&w,b->cellAspect);
            put(&w,",\"strength\":");integer(&w,b->strength);
            put(&w,",\"waveScale\":");integer(&w,b->waveScale);
            put(&w,",\"glyphs\":");glyphString(&w,b->glyphs,(int)b->glyphCount);
            put(&w,",\"palette\":[");for(uint32_t k=0;k<b->paletteCount;k++){if(k)put(&w,",");integer(&w,b->palette[k]);}put(&w,"]");
            put(&w,",\"starPalette\":[");for(uint32_t k=0;k<b->starPaletteCount;k++){if(k)put(&w,",");integer(&w,b->starPalette[k]);}put(&w,"]");
            put(&w,"}}");
        }
        if(s->worldSourceControls[i].used){
            const WorldSourceControls*b=&s->worldSourceControls[i];WorldSourceSample sample;nrWorldSourceSample(s,i,&sample);
            int width,height;nrSceneViewport(s,&width,&height);
            Projection projection;nrProjection(s,width,height,&projection);if(b->used==2)nrWorldOriginalProjection(s,&projection,&projection);
            put(&w,",\"worldSource\":{\"paint\":");string(&w,b->used==2?"source":"material");put(&w,",\"profile\":");string(&w,(const char*[]){"firework","sparks","embers","leaves","rain","snow","nova","ripples"}[nrWorldSourceProfile(s,i)]);
            put(&w,",\"seed\":");integer(&w,b->seed);put(&w,",\"elapsedUs\":");integer(&w,s->timeUs-b->startUs);
            put(&w,",\"controls\":{\"lifeMs\":");number(&w,b->lifeMs);put(&w,",\"count\":");integer(&w,b->count);put(&w,",\"scale\":");number(&w,b->scale);put(&w,",\"gravity\":");number(&w,b->gravity);put(&w,"}");
            if(b->used==2&&nrWorldSourceProfile(s,i)==7){put(&w,",\"ripplePlane\":{\"eventId\":");integer(&w,q->id);put(&w,",\"speed\":2048,\"width\":384,\"opacity\":600,\"rings\":4,\"cellAspect\":2000,\"unitsPerCell\":");number(&w,b->scale);put(&w,",\"birthOrientation\":");vec(&w,s->birthOrientations[i]);put(&w,"}");}
            put(&w,",\"pointsCount\":");integer(&w,sample.pointCount);
            put(&w,",\"points\":[");for(uint32_t index=0;index<sample.pointCount&&index<16;index++){if(index)put(&w,",");put(&w,"[");for(int k=0;k<6;k++){if(k)put(&w,",");number(&w,sample.points[index][k]);}put(&w,"]");}put(&w,"]");
            put(&w,",\"segmentsCount\":");integer(&w,sample.segmentCount);
            put(&w,",\"segments\":[");for(uint32_t index=0;index<sample.segmentCount&&index<16;index++){if(index)put(&w,",");put(&w,"[");for(int k=0;k<8;k++){if(k)put(&w,",");number(&w,sample.segments[index][k]);}put(&w,"]");}put(&w,"]");
            uint32_t projectedCount=0;double row[6];for(uint32_t index=0;index<sample.segmentCount;index++)if((b->used==2?nrThermalOriginalProjectSegment(&projection,q->position,sample.segments[index],row):nrThermalSourceProjectSegment(&projection,q->position,sample.segments[index],row)))projectedCount++;
            put(&w,",\"sampleLimit\":16,\"projectedSegmentsCount\":");integer(&w,projectedCount);put(&w,",\"projectedSegments\":[");
            uint32_t written=0;for(uint32_t index=0;index<sample.segmentCount&&written<16;index++)if((b->used==2?nrThermalOriginalProjectSegment(&projection,q->position,sample.segments[index],row):nrThermalSourceProjectSegment(&projection,q->position,sample.segments[index],row))){
                if(written++)put(&w,",");put(&w,"[");for(int k=0;k<6;k++){if(k)put(&w,",");number(&w,row[k]);}put(&w,"]");
            }put(&w,"]}");
        }
        if(s->thermalSourceControls[i].used){
            const ThermalSourceControls*b=&s->thermalSourceControls[i];ThermalSourceSample sample;nrThermalSourceSample(s,i,&sample);
            int width,height;nrSceneViewport(s,&width,&height);
            Projection projection;nrProjection(s,width,height,&projection);
            put(&w,",\"thermalSource\":{\"paint\":");string(&w,b->reserved?"source":"material");put(&w,",\"profile\":");string(&w,nrThermalSourceProfile(s,i)==0?"embers":"leaves");
            put(&w,",\"seed\":");integer(&w,b->seed);put(&w,",\"elapsedUs\":");integer(&w,s->timeUs-b->startUs);
            put(&w,",\"controls\":{\"lifeMs\":");number(&w,b->lifeMs);put(&w,"}");
            put(&w,",\"pointsCount\":");integer(&w,sample.pointCount);
            put(&w,",\"points\":[");for(uint32_t index=0;index<sample.pointCount&&index<16;index++){if(index)put(&w,",");put(&w,"[");for(int k=0;k<6;k++){if(k)put(&w,",");number(&w,sample.points[index][k]);}put(&w,"]");}put(&w,"]");
            put(&w,",\"segmentsCount\":");integer(&w,sample.segmentCount);
            put(&w,",\"segments\":[");for(uint32_t index=0;index<sample.segmentCount&&index<16;index++){if(index)put(&w,",");put(&w,"[");for(int k=0;k<8;k++){if(k)put(&w,",");number(&w,sample.segments[index][k]);}put(&w,"]");}put(&w,"]");
            uint32_t projectedCount=0;double row[6];for(uint32_t index=0;index<sample.segmentCount;index++)if((b->reserved?nrThermalOriginalProjectSegment(&projection,q->position,sample.segments[index],row):nrThermalSourceProjectSegment(&projection,q->position,sample.segments[index],row)))projectedCount++;
            put(&w,",\"sampleLimit\":16,\"projectedSegmentsCount\":");integer(&w,projectedCount);put(&w,",\"projectedSegments\":[");
            uint32_t written=0;for(uint32_t index=0;index<sample.segmentCount&&written<16;index++)if((b->reserved?nrThermalOriginalProjectSegment(&projection,q->position,sample.segments[index],row):nrThermalSourceProjectSegment(&projection,q->position,sample.segments[index],row))){
                if(written++)put(&w,",");put(&w,"[");for(int k=0;k<6;k++){if(k)put(&w,",");number(&w,row[k]);}put(&w,"]");
            }put(&w,"]}");
        }
        if(s->atelierControls[i].used){
            const AtelierControls*b=&s->atelierControls[i];AtelierSample sample;double center[3]={0};
            nrAtelierSample(s,i,&sample);int visible=nrAtelierCenter(s,i,center);
            put(&w,",\"atelier\":{\"paint\":");string(&w,b->reserved?"source":"material");put(&w,",\"profile\":");string(&w,(const char*[]){"nova","sparks","embers","rain","snow"}[nrAtelierProfile(s,i)]);
            put(&w,",\"seed\":");integer(&w,b->seed);put(&w,",\"eventId\":");integer(&w,b->eventId);
            put(&w,",\"elapsedUs\":");integer(&w,s->timeUs-b->startUs);
            put(&w,",\"visible\":");put(&w,visible?"true":"false");put(&w,",\"center\":[");for(int k=0;k<3;k++){if(k)put(&w,",");number(&w,center[k]);}put(&w,"]");
            put(&w,",\"pointsCount\":");integer(&w,sample.pointCount);
            put(&w,",\"segmentsCount\":");integer(&w,sample.segmentCount);
            put(&w,",\"glowsCount\":");integer(&w,sample.glowCount);
            put(&w,",\"sampleLimit\":16");
            put(&w,",\"points\":[");for(uint32_t index=0;index<sample.pointCount&&index<16;index++){if(index)put(&w,",");put(&w,"[");for(int k=0;k<5;k++){if(k)put(&w,",");number(&w,sample.points[index][k]);}put(&w,"]");}put(&w,"]");
            put(&w,",\"segments\":[");for(uint32_t index=0;index<sample.segmentCount&&index<16;index++){if(index)put(&w,",");put(&w,"[");for(int k=0;k<6;k++){if(k)put(&w,",");number(&w,sample.segments[index][k]);}put(&w,"]");}put(&w,"]");
            put(&w,",\"glows\":[");for(uint32_t index=0;index<sample.glowCount&&index<16;index++){if(index)put(&w,",");put(&w,"[");for(int k=0;k<6;k++){if(k)put(&w,",");number(&w,sample.glows[index][k]);}put(&w,"]");}put(&w,"]");
            put(&w,",\"controls\":{");
            put(&w,"\"lifeMs\":");number(&w,b->lifeMs);
            put(&w,",\"count\":");integer(&w,b->count);
            put(&w,",\"speed\":");number(&w,b->speed);
            put(&w,",\"gravity\":");number(&w,b->gravity);
            put(&w,",\"rise\":");number(&w,b->rise);
            put(&w,",\"drag\":");number(&w,b->drag);
            put(&w,",\"turbulence\":");number(&w,b->turbulence);
            put(&w,",\"glitterHz\":");number(&w,b->glitterHz);
            put(&w,",\"trailMs\":");number(&w,b->trailMs);
            put(&w,",\"branches\":");integer(&w,b->branches);
            put(&w,",\"jaggedness\":");number(&w,b->jaggedness);
            put(&w,",\"coreMs\":");number(&w,b->coreMs);
            put(&w,",\"coreRadius\":");number(&w,b->coreRadius);
            put(&w,",\"ejecta\":");number(&w,b->ejecta);
            put(&w,",\"shockwave\":");number(&w,b->shockwave);
            put(&w,",\"intensity\":");number(&w,b->intensity);
            put(&w,",\"reducedMotion\":");put(&w,b->reducedMotion?"true":"false");put(&w,"}}");
        }
        if(s->kineticControls[i].used){
            const KineticControls*b=&s->kineticControls[i];KineticSample sample;double center[3]={0};
            nrKineticSample(s,i,&sample);int visible=nrKineticCenter(s,i,center);
            put(&w,",\"kinetic\":{\"profile\":");string(&w,(const char*[]){"embers","sparks","nova","rain","snow"}[nrKineticProfile(s,i)]);
            put(&w,",\"paint\":");string(&w,s->kineticPaint[i]?"source":"material");
            put(&w,",\"seed\":");integer(&w,b->seed);put(&w,",\"eventId\":");integer(&w,b->eventId);
            put(&w,",\"elapsedUs\":");integer(&w,s->timeUs-b->startUs);
            put(&w,",\"visible\":");put(&w,visible?"true":"false");put(&w,",\"center\":[");for(int k=0;k<3;k++){if(k)put(&w,",");number(&w,center[k]);}put(&w,"]");
            put(&w,",\"core\":");number(&w,sample.core);put(&w,",\"radius\":");number(&w,sample.radius);put(&w,",\"shockwave\":");number(&w,sample.shockwave);
            put(&w,",\"pointsCount\":");integer(&w,sample.pointCount);put(&w,",\"segmentsCount\":");integer(&w,sample.segmentCount);
            put(&w,",\"sampleLimit\":16,\"points\":[");
            for(uint32_t index=0;index<sample.pointCount&&index<16;index++){if(index)put(&w,",");put(&w,"[");for(int k=0;k<6;k++){if(k)put(&w,",");number(&w,sample.points[index][k]);}put(&w,"]");}
            put(&w,"],\"segments\":[");for(uint32_t index=0;index<sample.segmentCount&&index<16;index++){if(index)put(&w,",");put(&w,"[");for(int k=0;k<7;k++){if(k)put(&w,",");number(&w,sample.segments[index][k]);}put(&w,"]");}
            put(&w,"],\"controls\":{\"count\":");integer(&w,b->count);put(&w,",\"branches\":");integer(&w,b->branches);put(&w,",\"arcSegments\":");integer(&w,b->arcSegments);
            put(&w,",\"lifeMs\":");number(&w,b->lifeMs);
            put(&w,",\"launchSpeed\":");number(&w,b->launchSpeed);
            put(&w,",\"gravity\":");number(&w,b->gravity);
            put(&w,",\"drag\":");number(&w,b->drag);
            put(&w,",\"wind\":");number(&w,b->wind);
            put(&w,",\"flickerHz\":");number(&w,b->flickerHz);
            put(&w,",\"trailMs\":");number(&w,b->trailMs);
            put(&w,",\"arcJitter\":");number(&w,b->arcJitter);
            put(&w,",\"coreMs\":");number(&w,b->coreMs);
            put(&w,",\"shockwave\":");number(&w,b->shockwave);
            put(&w,",\"explosionForce\":");number(&w,b->explosionForce);
            put(&w,",\"brightness\":");number(&w,b->brightness);
            put(&w,",\"emberSpread\":");number(&w,b->emberSpread);
            put(&w,",\"arcReach\":");number(&w,b->arcReach);
            put(&w,",\"glyphs\":");glyphString(&w,b->glyphs,(int)b->glyphCount);put(&w,"}}");
        }
        if(s->observatoryControls[i].used){
            const ObservatoryControls*b=&s->observatoryControls[i];double center[3]={0},row[5];int visible=nrObservatoryCenter(s,i,center);
            put(&w,",\"observatory\":{\"paint\":");string(&w,b->reserved?"source":"material");put(&w,",\"profile\":");string(&w,(const char*[]){"rain","snow","embers","sparks"}[nrObservatoryProfile(s,i)]);
            put(&w,",\"seed\":");integer(&w,b->seed);put(&w,",\"speed\":");number(&w,b->speed);put(&w,",\"intensity\":");number(&w,b->intensity);
            put(&w,",\"durationUs\":");integer(&w,b->durationUs);put(&w,",\"elapsedUs\":");integer(&w,s->timeUs-b->startUs);
            int count=(int)(16+24*b->intensity+.5);put(&w,",\"count\":");integer(&w,count);
            put(&w,",\"visible\":");put(&w,visible?"true":"false");put(&w,",\"center\":[");for(int k=0;k<3;k++){if(k)put(&w,",");number(&w,center[k]);}
            put(&w,"],\"sampleLimit\":16,\"samples\":[");int samples=0;
            for(int index=0;index<count&&index<16;index++)if(nrObservatorySample(s,i,index,row)){
                if(samples++)put(&w,",");put(&w,"[");for(int k=0;k<5;k++){if(k)put(&w,",");number(&w,row[k]);}put(&w,"]");}
            put(&w,"]}");
        }
        if(s->coronaControls[i].used){
            const CoronaControls*b=&s->coronaControls[i];double sample[5],center[3]={0};
            nrCoronaAppearance(s,i,0,sample);int visible=nrCoronaCenter(s,i,center);
            put(&w,",\"corona\":{\"paint\":");string(&w,b->used==2?"source":"material");put(&w,",\"speed\":");number(&w,b->speed);
            put(&w,",\"width\":");number(&w,b->width);put(&w,",\"intensity\":");number(&w,b->intensity);
            put(&w,",\"durationUs\":");integer(&w,b->durationUs);put(&w,",\"elapsedUs\":");integer(&w,(uint64_t)sample[0]);
            put(&w,",\"radius\":");number(&w,sample[1]);put(&w,",\"envelope\":");number(&w,sample[2]);
            put(&w,",\"coreGlyph\":");integer(&w,(uint32_t)sample[3]);
            put(&w,",\"visible\":");put(&w,visible?"true":"false");put(&w,",\"center\":[");
            for(int k=0;k<3;k++){if(k)put(&w,",");number(&w,center[k]);}put(&w,"],\"radialSamples\":[");
            double distances[3]={0,sample[1],sample[1]+b->width};
            for(int k=0;k<3;k++){nrCoronaAppearance(s,i,distances[k],sample);if(k)put(&w,",");put(&w,"[");number(&w,distances[k]);put(&w,",");number(&w,sample[4]);put(&w,"]");}
            put(&w,"]}");
        }
        put(&w,",\"birthOrientation\":");vec(&w,s->birthOrientations[i]);
        put(&w,",\"authoredMotion\":");integer(&w,s->emitterMotions[i].authored);
        put(&w,",\"initialOrientation\":");vec(&w,s->emitterMotions[i].orientation);
        put(&w,",\"angularVelocity\":");vec(&w,s->emitterMotions[i].angularVelocity);
        uint32_t mask=nrEmitterColliderMask(s,i);put(&w,",\"colliders\":{\"floor\":");put(&w,mask&1u?"true":"false");put(&w,",\"surfaces\":[");int surfaceFirst=1;
        for(int id=1;id<=NR_SURFACES;id++)if(mask&(1u<<id)) {if(!surfaceFirst)put(&w,",");surfaceFirst=0;integer(&w,id);}
        put(&w,"]}}");
    }
    put(&w,"],\"deposits\":[");first=1;
    for(int i=0;i<NR_DEPOSITS;i++)if(s->deposits[i].used) {
        const Deposit*q=&s->deposits[i];if(!first)put(&w,",");first=0;
        put(&w,"{\"id\":");integer(&w,q->id);put(&w,",\"emitterId\":");integer(&w,q->emitterId);
        put(&w,",\"shape\":");integer(&w,q->leafShape);put(&w,",\"position\":");vec(&w,q->position);
        const SurfaceContact*contact=&s->geometry.depositContacts[i];
        put(&w,",\"surfaceId\":");integer(&w,contact->surfaceId);
        put(&w,",\"normal\":");vec(&w,contact->used?contact->normal:nrV(0,1,0));put(&w,"}");
    }
    put(&w,"]}");
    return w;
}
const char*nrInfo(NrContext*c) {
    if(!valid(c))return "{}";
    Writer w=infoWrite(c,(Writer){.p=c->info,.cap=sizeof(c->info)});
    if(w.failed)return "{\"error\":\"metadata capacity exceeded\"}";
    return c->info;
}
static int infoRangesOverlap(const void*a,size_t n,const void*b,size_t m) {
    uintptr_t x=(uintptr_t)a,y=(uintptr_t)b;
    return n&&m&&(x<=y?y-x<n:x-y<m);
}
int nrInfoPage(NrContext*c,uint32_t offset,void*destination,uint32_t capacity,
               uint32_t*words,uint32_t wordCapacity) {
    /* Only four words are written, even when the supplied capacity is larger.
     * Stage in private scratch so an invalid offset cannot clobber outputs. */
    if(!valid(c)||capacity>NR_INFO_PAGE_MAX||(!destination&&capacity)||
       !words||wordCapacity<4||((uintptr_t)words%_Alignof(uint32_t))||
       capacity>UINTPTR_MAX-(uintptr_t)destination||
       4*sizeof(*words)>UINTPTR_MAX-(uintptr_t)words||
       !nrExternalOutput(c,destination,capacity)||!nrExternalOutput(c,words,4*sizeof(*words))||
       infoRangesOverlap(destination,capacity,c,sizeof(*c))||
       infoRangesOverlap(words,4*sizeof(*words),c,sizeof(*c))||
       infoRangesOverlap(destination,capacity,words,4*sizeof(*words)))return -1;
    Writer w=infoWrite(c,(Writer){.p=c->info,.cap=capacity,.skip=offset,
                                  .crc=UINT32_MAX,.paged=1});
    if(w.failed||offset>w.used)return -1;
    uint32_t count=w.used-offset;
    if(count>capacity)count=capacity;
    uint32_t result[4]={w.used,count,offset+count,w.crc^UINT32_MAX};
    if(count)memcpy(destination,c->info,count);
    memcpy(words,result,sizeof(result));
    return result[2]<w.used?1:0;
}

int nrPromptSelection(NrContext*c,uint32_t*out,uint32_t capacity) {
    if(!valid(c)||(!out&&capacity))return -1;
    const State*s=&c->state;const Prompt*p=&s->promptDocument;
    if(nrInputOwner(s)||p->anchor<0)return 0;
    int first=p->anchor<p->caret?p->anchor:p->caret,last=p->anchor>p->caret?p->anchor:p->caret;
    uint32_t count=(uint32_t)(last-first);
    if(!out&&!capacity)return (int)count;
    if(capacity<count||!nrExternalOutput(c,out,(size_t)count*4))return -1;
    if(count)memcpy(out,p->glyphs+first,(size_t)count*4);
    return (int)count;
}

/* Authored IDs are stable across reflow; kinds disambiguate overlapping namespaces. */
static const uint32_t* textRunSource(const State*s,uint32_t kind,uint32_t id,uint32_t*count) {
    if(kind==0&&id==0){*count=(uint32_t)s->promptDocument.count;return s->promptDocument.glyphs;}
    if(kind==1)for(int i=0;i<NR_TEXTS;i++)if(s->text[i].used&&(uint32_t)s->text[i].id==id){*count=(uint32_t)s->text[i].count;return s->text[i].text;}
    if(kind==2||kind==3)for(int i=0;i<(int)NR_MAX_WINDOWS;i++)if(s->windows[i].used&&(uint32_t)s->windows[i].id==id){
        const Window*w=&s->windows[i];if(kind==2){int length;const uint32_t*document=nrWindowDocument(s,w,&length);*count=(uint32_t)length;return document;}*count=(uint32_t)w->titleCount;return w->title;
    }
    return NULL;
}
int nrTextRunSource(NrContext*c,uint32_t kind,uint32_t id,uint32_t*out,uint32_t capacity) {
    if(!valid(c)||(!out&&capacity))return -1;
    uint32_t count;const uint32_t*source=textRunSource(&c->state,kind,id,&count);
    if(!source)return -1;
    if(!out&&!capacity)return (int)count;
    if(capacity<count||((uintptr_t)out%_Alignof(uint32_t))||
       !nrExternalOutput(c,out,(size_t)count*sizeof(*out)))return -1;
    if(count)memcpy(out,source,(size_t)count*sizeof(*out));return (int)count;
}
int nrTextRunLayout(NrContext*c,uint32_t kind,uint32_t id,uint32_t ambiguous,uint32_t columns,uint32_t*out,uint32_t capacity) {
    if(!valid(c)||(!out&&capacity))return -1;
    uint32_t count,*layout=c->documentLayout;const uint32_t*source=textRunSource(&c->state,kind,id,&count);
    if(!source)return -1;
    int n=nrDocumentGraphemeLayout(source,count,ambiguous,columns,layout,c->state.dynamicPrompt.capacity);
    if(n<0)return -1;
    if(!out&&!capacity)return n;
    if(capacity<(uint32_t)n||((uintptr_t)out%_Alignof(uint32_t))||
       !nrExternalOutput(c,out,(size_t)n*7*sizeof(*out)))return -1;
    for(int i=0;i<n;i++) {
        out[i*7]=id;memcpy(out+i*7+1,layout+i*5,5*sizeof(*out));out[i*7+6]=kind;
    }
    return n;
}

int nrTextRunHit(NrContext*c,uint32_t kind,uint32_t id,uint32_t ambiguous,
                 uint32_t columns,uint32_t column,uint32_t row) {
    if(!valid(c))return -1;
    uint32_t count;const uint32_t*source=textRunSource(&c->state,kind,id,&count);
    if(!source)return -1;
    uint32_t*layout=c->documentLayout;int n=nrDocumentGraphemeLayout(source,count,ambiguous,columns,layout,c->state.dynamicPrompt.capacity);if(n<0)return -1;
    uint32_t selected=0;uint64_t bestRow=UINT64_MAX,bestColumn=UINT64_MAX;
    for(int i=0;i<n;i++){
        uint32_t*line=layout+i*5;int newline=nrPromptHardBreak(source[line[0]]);
        for(int edge=0;edge<2;edge++){
            uint32_t at=line[edge];uint64_t x=edge?(newline?0:(uint64_t)line[2]+line[4]):line[2],y=(uint64_t)line[3]+(edge&&newline);
            uint64_t dx=x>column?x-column:column-x,dy=y>row?y-row:row-y;
            if(dy<bestRow||(dy==bestRow&&(dx<bestColumn||(dx==bestColumn&&at>selected)))){bestRow=dy;bestColumn=dx;selected=at;}
        }
    }return (int)selected;
}

int nrTextRunClip(NrContext*c,uint32_t kind,uint32_t id,uint32_t ambiguous,
                  uint32_t columns,uint32_t x,uint32_t y,uint32_t width,uint32_t height,
                  uint32_t*out,uint32_t capacity) {
    if(!valid(c)||(!out&&capacity))return -1;
    uint32_t count,*layout=c->documentLayout,*rows=c->documentClip;
    const uint32_t*source=textRunSource(&c->state,kind,id,&count);
    if(!source)return -1;
    int n=nrDocumentGraphemeLayout(source,count,ambiguous,columns,layout,c->state.dynamicPrompt.capacity);
    if(n<0)return -1;
    uint64_t right=(uint64_t)x+width,bottom=(uint64_t)y+height;
    uint32_t used=0;
    if(width&&height)for(int i=0;i<n;i++) {
        uint32_t cx=layout[i*5+2],cy=layout[i*5+3],cw=layout[i*5+4];
        uint64_t end=(uint64_t)cx+cw;
        if(!cw||cy<y||(uint64_t)cy>=bottom||end<=x||(uint64_t)cx>=right)continue;
        uint64_t first=cx>x?cx:x,last=end<right?end:right;
        uint32_t*r=rows+used*9;r[0]=id;memcpy(r+1,layout+i*5,5*sizeof(*r));r[6]=kind;
        r[7]=(uint32_t)(first-cx);r[8]=(uint32_t)(last-first);used++;
    }
    if(!out&&!capacity)return (int)used;
    if(capacity<used||((uintptr_t)out%_Alignof(uint32_t))||
       !nrExternalOutput(c,out,(size_t)used*9*sizeof(*out)))return -1;
    if(used)memcpy(out,rows,(size_t)used*9*sizeof(*out));return (int)used;
}

_Static_assert(sizeof(JToken)==32u,"canonical payload token size");
