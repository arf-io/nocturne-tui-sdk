#include "internal.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct { unsigned char *bytes; uint32_t size; } Snapshot;
static unsigned rejectedSnapshots;
static uint32_t read32(const unsigned char*p) {
 return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);
}
static void resizeSnapshot(Snapshot*s,uint32_t size) {
 assert(size>=24);
 if(s->size!=size) {unsigned char*next=realloc(s->bytes,size);assert(next);s->bytes=next;s->size=size;}
}
static void checkWire(const Snapshot*s) {
 assert(s->size>=24&&!memcmp(s->bytes,"NRRC4SRC",8));
 assert(read32(s->bytes+8)==NR_ABI_VERSION&&read32(s->bytes+16)==s->size-24);
 assert(read32(s->bytes+20)==nrCrc(s->bytes+24,s->size-24));
}
static void saveSnapshot(const NrContext*c,Snapshot*s) {
 uint32_t needed=nrSnapshotSizeFor(c);assert(needed>=24);
 resizeSnapshot(s,needed);assert(nrSave(c,s->bytes,s->size)==0);checkWire(s);
}
static void equalSnapshots(const Snapshot*a,const Snapshot*b) {
 assert(a->size==b->size&&!memcmp(a->bytes,b->bytes,a->size));
}
static State* prepareMutation(const NrContext*c,Snapshot*before,Snapshot*input) {
 saveSnapshot(c,before);resizeSnapshot(input,before->size);memcpy(input->bytes,before->bytes,before->size);
 /* Only members in the serialized fixed prefix may be accessed through State.
  * The PromptRuntime suffix contains host pointers and is never wire data. */
 assert(input->size>=24+offsetof(State,dynamicPrompt)+nrPromptWireSize());
 return (State*)(void*)(input->bytes+24);
}
static void fixChecksum(Snapshot*s) {
 assert(s->size>=24&&read32(s->bytes+16)==s->size-24);
 uint32_t n=nrCrc(s->bytes+24,s->size-24);for(int i=0;i<4;i++)s->bytes[20+i]=(unsigned char)(n>>(8*i));
 checkWire(s);
}
static int loadMutation(NrContext*c,const Snapshot*input,const Snapshot*before,Snapshot*after) {
 checkWire(input);int result=nrLoad(c,input->bytes,input->size);saveSnapshot(c,after);
 if(result<0) {equalSnapshots(before,after);rejectedSnapshots++;}
 return result;
}
/* All typed corruption targets are fixed wire members, before runtime pointers. */
#define CHECK_FIXED(member) _Static_assert(offsetof(State,member)+sizeof(((State*)0)->member)<=offsetof(State,dynamicPrompt),"corruption target must be serialized")
CHECK_FIXED(particles);CHECK_FIXED(indicators);CHECK_FIXED(materials);CHECK_FIXED(nodes);
CHECK_FIXED(text);CHECK_FIXED(windows);CHECK_FIXED(widgets);CHECK_FIXED(messages);
CHECK_FIXED(intents);CHECK_FIXED(nextIntent);CHECK_FIXED(nextMessage);CHECK_FIXED(triggers);
CHECK_FIXED(emitters);CHECK_FIXED(floor);CHECK_FIXED(registeredStates);CHECK_FIXED(styleRules);CHECK_FIXED(mesh);
#undef CHECK_FIXED
static void viewportSafety(NrContext*c,Snapshot*snapshot) {
 Snapshot after={0};
 const char*window="{\"op\":\"window\",\"id\":1,\"title\":\"retained title\",\"text\":\"retained document\"}";
 assert(nrCommand(c,window,(uint32_t)strlen(window))==0);
 unsigned dims[][2]={{1,1},{3,5},{400,24},{80,180},{320,120},{65536,1}};
 unsigned char*owned=0;
 for(unsigned i=0;i<sizeof(dims)/sizeof(dims[0]);i++) {
  char resize[128];int length=snprintf(resize,sizeof(resize),"{\"op\":\"resize\",\"width\":%u,\"height\":%u}",dims[i][0],dims[i][1]);
  assert(nrCommand(c,resize,(uint32_t)length)==0);
  uint64_t required=nrRenderMemorySize(c);assert(required&&required<=SIZE_MAX-16);
  if(required>nrRenderMemoryCapacity(c))assert(nrRender(c)==0);
  unsigned char*next=malloc((size_t)required+16);assert(next);memset(next,0x77,(size_t)required+16);
  assert(nrSetRenderMemory(c,next,required-1)==-1);
  assert(nrSetRenderMemory(c,c,required)==-1);
  assert(nrSetRenderMemory(c,next+1,required)==-1);
  assert(nrSetRenderMemory(c,next,required)==0);free(owned);owned=next;
  saveSnapshot(c,snapshot);
  assert(nrRender(c)==dims[i][0]*dims[i][1]);
  saveSnapshot(c,&after);equalSnapshots(snapshot,&after);
  for(int k=0;k<16;k++)assert(next[required+k]==0x77);
 }
 const char*style="{\"op\":\"environment\",\"style\":\"contours\"}";
 assert(nrCommand(c,style,(uint32_t)strlen(style))==0);assert(nrRender(c)==65536);
 assert(nrInit(c,nrContextSize(),2030)==0);free(owned);
 uint32_t text[2048],out[6144];for(int i=0;i<2048;i++)text[i]=65;
 assert(nrGraphemeWidths(text,2048,1,out,2048)==2048);
 for(int i=0;i<2048;i++)assert(out[i*3]==(uint32_t)i&&out[i*3+1]==(uint32_t)i+1&&out[i*3+2]==1);
 uint32_t layout[2048*5+1];layout[2048*5]=0xdeadbeef;
 assert(nrGraphemeLayout(text,2048,1,1,layout,2048)==2048);
 for(int i=0;i<2048;i++)assert(layout[i*5]==(uint32_t)i&&layout[i*5+1]==(uint32_t)i+1&&layout[i*5+2]==0&&layout[i*5+3]==(uint32_t)i&&layout[i*5+4]==1);
 assert(layout[2048*5]==0xdeadbeef);
 layout[0]=0xdeadbeef;assert(nrGraphemeLayout(text,2048,1,0,layout,2048)==-1&&layout[0]==0xdeadbeef);
 for(int i=0;i<2048;i++)layout[i]=65;
 assert(nrGraphemeLayout(layout,2048,1,1,layout,2048)==2048);
 assert(layout[2048*5]==0xdeadbeef);
 const char*mode="{\"op\":\"prompt\",\"mode\":\"grow\"}";
 assert(nrCommand(c,mode,(uint32_t)strlen(mode))==0);
 char source[2049],draft[2200];memset(source,'a',2048);source[2047]='Q';source[2048]=0;
 int length=snprintf(draft,sizeof(draft),"{\"op\":\"draft\",\"text\":\"%s\",\"emitWeather\":false}",source);
 assert(length>0&&(size_t)length<sizeof(draft)&&nrCommand(c,draft,(uint32_t)length)==0);
 assert(c->state.promptDocument.count==2048&&c->state.promptDocument.glyphs[2047]=='Q');
 saveSnapshot(c,snapshot);assert(nrRender(c)==160*48);
 saveSnapshot(c,&after);equalSnapshots(snapshot,&after);
 int x,y;nrPromptCoordinate(&c->state,2047,&x,&y);
 assert(nrPromptHit(&c->state,x,y)==2047);
 assert(nrPromptVertical(&c->state,-1,0)==2048-(160-4));
 assert(nrPromptVertical(&c->state,-1,1)==2048-(160-4));
 assert(nrPromptVertical(&c->state,1,1)==2048);
 out[0]=0xdeadbeef;assert(nrGraphemeWidths(text,2049,1,out,2048)==-1&&out[0]==0xdeadbeef);
 text[0]=0x110000;assert(nrGraphemeWidths(text,2048,1,out,2048)==-1&&out[0]==0xdeadbeef);
 for(int i=0;i<2048;i++)out[i]=65;
 assert(nrGraphemeWidths(out,2048,2,out,2048)==2048);
 for(int i=0;i<2048;i++)assert(out[i*3]==(uint32_t)i&&out[i*3+1]==(uint32_t)i+1&&out[i*3+2]==1);
 /* This function owns its comparison snapshot; the caller owns *snapshot. */
 free(after.bytes);
}
int main(void){NrContext*c=malloc(nrContextSize());assert(c);assert(nrInit(c,nrContextSize(),2030)==0);Snapshot before={0},input={0},after={0};State*st=prepareMutation(c,&before,&input);
 /* A short output buffer must reject before writing any byte. */
 assert(nrSave(c,input.bytes,input.size-1)<0);equalSnapshots(&before,&input);
 st->particles[0].state=1;st->particles[0].emitterSlot=NR_MAX_EMITTERS+1;fixChecksum(&input);assert(loadMutation(c,&input,&before,&after)<0);
 st=prepareMutation(c,&before,&input);st->indicators[0].used=1;st->indicators[0].count=1;st->indicators[0].stepUs=0;fixChecksum(&input);assert(loadMutation(c,&input,&before,&after)<0);
 st=prepareMutation(c,&before,&input);st->materials[0].alpha.periodUs=0;fixChecksum(&input);assert(loadMutation(c,&input,&before,&after)<0);
 st=prepareMutation(c,&before,&input);st->nodes[0].used=1;st->nodes[0].id=1;memset(st->nodes[0].kind,'x',sizeof(st->nodes[0].kind));fixChecksum(&input);assert(loadMutation(c,&input,&before,&after)<0);
 st=prepareMutation(c,&before,&input);st->text[0].used=1;st->text[0].count=0x7fffffff;fixChecksum(&input);assert(loadMutation(c,&input,&before,&after)<0);
 st=prepareMutation(c,&before,&input);st->windows[0].polygonCount=0x7fffffff;fixChecksum(&input);assert(loadMutation(c,&input,&before,&after)<0);
 st=prepareMutation(c,&before,&input);st->widgets[0].dataCount=0x7fffffff;fixChecksum(&input);assert(loadMutation(c,&input,&before,&after)<0);
 /* Recomputed CRC cannot validate hostile action and intention metadata. */
 st=prepareMutation(c,&before,&input);st->messages[0].used=1;st->messages[0].actionCount=0x7fffffff;fixChecksum(&input);assert(loadMutation(c,&input,&before,&after)<0);
 st=prepareMutation(c,&before,&input);st->nextIntent=0;fixChecksum(&input);assert(loadMutation(c,&input,&before,&after)<0);
 st=prepareMutation(c,&before,&input);st->intents[0].used=1;st->intents[0].id=1;st->nextIntent=2;memset(st->intents[0].event,'x',sizeof(st->intents[0].event));fixChecksum(&input);assert(loadMutation(c,&input,&before,&after)<0);
 const char*notice="{\"op\":\"status\",\"id\":1,\"text\":\"Native action\",\"important\":true,\"durationMs\":0,\"actions\":[{\"id\":1,\"label\":\"Inspect\",\"event\":\"/inspect\"}]}";
 assert(nrCommand(c,notice,(uint32_t)strlen(notice))==0);
 const char*activate="{\"op\":\"notification-action\",\"id\":1,\"actionId\":1}";
 assert(nrCommand(c,activate,(uint32_t)strlen(activate))==0);
 st=prepareMutation(c,&before,&input);st->messages[0].actionMask=0x80000000u;fixChecksum(&input);assert(loadMutation(c,&input,&before,&after)<0);
 st=prepareMutation(c,&before,&input);st->intents[0].messageSequence=st->nextMessage+1;fixChecksum(&input);assert(loadMutation(c,&input,&before,&after)<0);
 const char*good[]={"{\"op\":\"emitter\",\"id\":1,\"effect\":\"weather/autumn-drift\",\"count\":32}","{\"op\":\"field\",\"effect\":\"surface-field/silk-tide\",\"x\":10,\"y\":10}","{\"op\":\"input\",\"text\":\"Immediate native text\"}"};for(int i=0;i<3;i++)assert(nrCommand(c,good[i],(uint32_t)strlen(good[i]))==0);
 for(int i=0;i<120;i++){char command[96];snprintf(command,sizeof(command),"{\"op\":\"time\",\"timeUs\":%d}",i*20000);assert(nrCommand(c,command,(uint32_t)strlen(command))==0);assert(nrRender(c)>0);}
 /* Hostile finite geometry is either clipped or rejected, never unbounded raster work. */
 for(int i=0;i<100;i++){char command[300];snprintf(command,sizeof(command),"{\"op\":\"camera\",\"position\":[%d,%d,%d],\"yaw\":%d,\"pitch\":%d}",(i*53)%400-200,(i*31)%200-100,(i*71)%400-200,i*53,(i%175)-87);assert(nrCommand(c,command,(uint32_t)strlen(command))==0);assert(nrRender(c)>0);}

 const char*plot="{\"op\":\"widget\",\"id\":31,\"kind\":\"donut\",\"width\":240,\"height\":100,\"data\":[9,1],\"sampling\":\"braille\"}";
 assert(nrCommand(c,plot,(uint32_t)strlen(plot))==0);assert(nrRender(c)>0);
 st=prepareMutation(c,&before,&input);st->widgets[0].sampling=99;fixChecksum(&input);assert(loadMutation(c,&input,&before,&after)<0);
 st=prepareMutation(c,&before,&input);st->widgets[0].innerRadius=1.1;fixChecksum(&input);assert(loadMutation(c,&input,&before,&after)<0);
 st=prepareMutation(c,&before,&input);st->widgets[0].revealAtUs=st->timeUs+1;fixChecksum(&input);assert(loadMutation(c,&input,&before,&after)<0);
 /* Keep original subsequent mutation workload independent of the added maximal plot. */
 const char*clearPlot="{\"op\":\"widget\",\"id\":31,\"kind\":\"box\",\"width\":1,\"height\":1}";
 assert(nrCommand(c,clearPlot,(uint32_t)strlen(clearPlot))==0);
 const char*rules[]={"{\"op\":\"define\",\"path\":\"/heat\",\"value\":0}","{\"op\":\"define\",\"path\":\"/out\",\"value\":0}","{\"op\":\"trigger\",\"id\":1,\"when\":{\"all\":[{\"path\":\"/heat\",\"comparison\":\"above\",\"value\":50}]},\"target\":\"/out\",\"value\":1}"};
 for(int i=0;i<3;i++)assert(nrCommand(c,rules[i],(uint32_t)strlen(rules[i]))==0);
 st=prepareMutation(c,&before,&input);st->triggers[0].conditions[0].end=0;fixChecksum(&input);assert(loadMutation(c,&input,&before,&after)<0);
 st=prepareMutation(c,&before,&input);st->triggers[0].conditions[0].children=NR_CONDITIONS+1;fixChecksum(&input);assert(loadMutation(c,&input,&before,&after)<0);
 st=prepareMutation(c,&before,&input);st->triggers[0].conditions[1].source=NR_VALUES;fixChecksum(&input);assert(loadMutation(c,&input,&before,&after)<0);
 st=prepareMutation(c,&before,&input);st->triggers[0].conditionCount=NR_CONDITIONS+1;fixChecksum(&input);assert(loadMutation(c,&input,&before,&after)<0);
 st=prepareMutation(c,&before,&input);st->emitters[0].surfaceAlpha=2;fixChecksum(&input);assert(loadMutation(c,&input,&before,&after)<0);
 st=prepareMutation(c,&before,&input);st->floor.sampling=99;fixChecksum(&input);assert(loadMutation(c,&input,&before,&after)<0);
 const char*styleCommands[]={
 "{\"op\":\"state-register\",\"id\":1,\"path\":\"/test/plot\",\"role\":\"control\",\"target\":{\"family\":\"widget\",\"id\":31}}",
 "{\"op\":\"style-rule\",\"id\":1,\"selector\":{\"family\":\"widget\"},\"style\":{\"alpha\":{\"path\":\"/heat\",\"inputMin\":0,\"inputMax\":100,\"outputMin\":0,\"outputMax\":1}},\"when\":{\"path\":\"/heat\",\"comparison\":\"above\",\"value\":0}}"};
 for(int i=0;i<2;i++)assert(nrCommand(c,styleCommands[i],(uint32_t)strlen(styleCommands[i]))==0);
 st=prepareMutation(c,&before,&input);st->registeredStates[0].family=999;fixChecksum(&input);assert(loadMutation(c,&input,&before,&after)<0);
 st=prepareMutation(c,&before,&input);memset(st->registeredStates[0].path,'x',128);fixChecksum(&input);assert(loadMutation(c,&input,&before,&after)<0);
 st=prepareMutation(c,&before,&input);st->styleRules[0].propertyMask=0xffffffffu;fixChecksum(&input);assert(loadMutation(c,&input,&before,&after)<0);
 st=prepareMutation(c,&before,&input);st->styleRules[0].properties[2].source=NR_VALUES;fixChecksum(&input);assert(loadMutation(c,&input,&before,&after)<0);
 st=prepareMutation(c,&before,&input);st->styleRules[0].properties[2].inputMax=0;fixChecksum(&input);assert(loadMutation(c,&input,&before,&after)<0);
 st=prepareMutation(c,&before,&input);st->styleRules[0].selector.stateMask=0x80000000u;fixChecksum(&input);assert(loadMutation(c,&input,&before,&after)<0);
 st=prepareMutation(c,&before,&input);st->styleRules[0].guard.conditions[0].source=NR_VALUES;fixChecksum(&input);assert(loadMutation(c,&input,&before,&after)<0);
 st=prepareMutation(c,&before,&input);st->styleRules[0].guard.conditionCount=NR_CONDITIONS+1;fixChecksum(&input);assert(loadMutation(c,&input,&before,&after)<0);
 const char*imported="{\"op\":\"model-import\",\"schema\":\"nocturne.model/v1\",\"units\":\"meters\",\"coordinates\":\"right-handed-y-up\",\"vertices\":[[0,0,0],[2,0,0],[0,2,0]],\"materials\":[{\"color\":1193046,\"alpha\":0.75}],\"triangles\":[{\"indices\":[0,1,2],\"material\":0}]}";
 assert(nrCommand(c,imported,(uint32_t)strlen(imported))==0);assert(nrRender(c)>0);
 st=prepareMutation(c,&before,&input);st->mesh[0].b=st->mesh[0].a;fixChecksum(&input);assert(loadMutation(c,&input,&before,&after)<0);
 unsigned seed=13;int accepted=0;for(int i=0;i<500;i++){st=prepareMutation(c,&before,&input);seed=seed*1664525u+1013904223u;uint32_t off=24+(seed%(input.size-24));input.bytes[off]^=(unsigned char)(1u<<(i%8));fixChecksum(&input);if(loadMutation(c,&input,&before,&after)==0){accepted++;assert(nrRender(c)>0);assert(nrInfo(c));}}
 viewportSafety(c,&before);
 printf("PASS: dynamic viewports/width metrics, hostile snapshots, 120 simulation/render frames, 100 camera configurations, 500 recomputed-checksum mutations (%d semantically valid, %u atomic rejections); exact pointer-free snapshot CRC/bounds\n",accepted,rejectedSnapshots);free(after.bytes);free(input.bytes);free(before.bytes);free(c);return 0;}
