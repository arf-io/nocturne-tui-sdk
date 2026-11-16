#include "internal.h"
#include "unicode_scripts.inc"
static uint16_t script(uint32_t cp){
 size_t lo=0,hi=sizeof(scriptRanges)/sizeof(scriptRanges[0]);while(lo<hi){size_t mid=(lo+hi)/2;if(cp<scriptRanges[mid].first)hi=mid;else if(cp>scriptRanges[mid].last)lo=mid+1;else return scriptRanges[mid].script;}return NR_SCRIPT_UNKNOWN;
}
static void candidates(uint32_t cp,uint16_t primary,uint64_t*out){
 size_t lo=0,hi=sizeof(scriptExtensions)/sizeof(scriptExtensions[0]);while(lo<hi){size_t mid=(lo+hi)/2;if(cp<scriptExtensions[mid].first)hi=mid;else if(cp>scriptExtensions[mid].last)lo=mid+1;else{memcpy(out,scriptExtensions[mid].mask,4*sizeof(uint64_t));return;}}
 if(primary==NR_SCRIPT_COMMON||primary==NR_SCRIPT_INHERITED){for(int k=0;k<4;k++)out[k]=~(uint64_t)0;}
 else{memset(out,0,4*sizeof(uint64_t));out[primary/64]|=(uint64_t)1<<(primary%64);}
}
static int includes(const uint64_t*set,uint16_t index){return index<NR_SCRIPT_COUNT&&((set[index/64]>>(index%64))&1);}
int nrScriptRuns(const uint32_t*text,uint32_t count,uint32_t*out,uint32_t capacity){
 if(count>NR_MAX_TEXT||(count&&(!text||((uintptr_t)text%4)))||(!out&&capacity)||(out&&((uintptr_t)out%4)))return -1;
 uint32_t breaks[NR_MAX_TEXT+1],rows[NR_MAX_TEXT*3];int n=nrGraphemeBreaks(text,count,breaks,NR_MAX_TEXT+1);if(n<0)return -1;int clusters=n-1;
 uint64_t sets[NR_MAX_TEXT][4];uint16_t chosen[NR_MAX_TEXT];
 for(int i=0;i<clusters;i++){
  for(int k=0;k<4;k++)sets[i][k]=~(uint64_t)0;chosen[i]=256;
  for(uint32_t at=breaks[i];at<breaks[i+1];at++){
   uint16_t primary=script(text[at]);uint64_t set[4];candidates(text[at],primary,set);
   if(chosen[i]==256&&primary!=NR_SCRIPT_COMMON&&primary!=NR_SCRIPT_INHERITED)chosen[i]=primary;
   for(int k=0;k<4;k++)sets[i][k]&=set[k];
  }
  /* A mixed-script grapheme stays intact and uses its first strong script. */
 }
 for(int i=0;i<clusters;i++)if(chosen[i]==256){
  uint16_t previous=i?chosen[i-1]:256,next=256;for(int j=i+1;j<clusters;j++)if(chosen[j]!=256){next=chosen[j];break;}
  if(includes(sets[i],previous)&&previous!=NR_SCRIPT_COMMON&&previous!=NR_SCRIPT_INHERITED)chosen[i]=previous;
  else if(includes(sets[i],next)&&next!=NR_SCRIPT_COMMON&&next!=NR_SCRIPT_INHERITED)chosen[i]=next;
  else{
   int unrestricted=1;for(int k=0;k<4;k++)if(sets[i][k]!=~(uint64_t)0)unrestricted=0;
   if(unrestricted)chosen[i]=NR_SCRIPT_COMMON;
   else{for(uint16_t k=0;k<NR_SCRIPT_COUNT;k++)if(includes(sets[i],k)){chosen[i]=k;break;}if(chosen[i]==256)chosen[i]=NR_SCRIPT_COMMON;}
  }
 }
 uint32_t runs=0;for(int i=0;i<clusters;i++){
  uint32_t tag=scriptTags[chosen[i]];if(runs&&rows[(runs-1)*3+2]==tag)rows[(runs-1)*3+1]=breaks[i+1];
  else{rows[runs*3]=breaks[i];rows[runs*3+1]=breaks[i+1];rows[runs*3+2]=tag;runs++;}
 }
 if(!out&&!capacity)return (int)runs;if(capacity<runs)return -1;if(runs)memcpy(out,rows,runs*3*sizeof(uint32_t));return (int)runs;
}
