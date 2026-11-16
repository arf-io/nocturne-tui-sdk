#include "internal.h"
#include "unicode_linebreak.inc"

static uint32_t lineClass(uint32_t scalar){
 size_t low=0,high=sizeof(lineBreakRanges)/sizeof(lineBreakRanges[0]);
 while(low<high){size_t mid=low+(high-low)/2;if(scalar<lineBreakRanges[mid].first)high=mid;else if(scalar>lineBreakRanges[mid].last)low=mid+1;else return lineBreakRanges[mid].kind;}
 return NR_LB_XX;
}
static uint32_t lineFlags(uint32_t scalar){
 size_t low=0,high=sizeof(lineBreakAuxiliary)/sizeof(lineBreakAuxiliary[0]);
 while(low<high){size_t mid=low+(high-low)/2;if(scalar<lineBreakAuxiliary[mid].first)high=mid;else if(scalar>lineBreakAuxiliary[mid].last)low=mid+1;else return lineBreakAuxiliary[mid].flags;}
 return 0;
}
/* Internal property inspection for the pending rule engine. Two words per
 * scalar: generated class ordinal and UAX14 auxiliary predicate bits.
 * These ordinals are internal, not an exported SDK property vocabulary. */
int nrLineBreakProperties(const uint32_t*text,uint32_t count,uint32_t*out,uint32_t capacity){
 if(count>NR_MAX_TEXT||(!text&&count)||(!out&&capacity)||((uintptr_t)text%4)||((uintptr_t)out%4))return -1;
 uint32_t rows[NR_MAX_TEXT*2];
 for(uint32_t i=0;i<count;i++){
  uint32_t scalar=text[i];if(scalar>0x10ffff||(scalar>=0xd800&&scalar<=0xdfff))return -1;
  rows[2*i]=lineClass(scalar);rows[2*i+1]=lineFlags(scalar);
 }
 if(!out)return (int)count;if(capacity<count)return -1;
 memcpy(out,rows,(size_t)count*2*sizeof(uint32_t));return (int)count;
}
typedef struct {uint32_t scalar,start,end;uint8_t kind,flags,lastZwj;} LineUnit;
static int hard(int k){return k==NR_LB_BK||k==NR_LB_CR||k==NR_LB_LF||k==NR_LB_NL;}
static int letters(int k){return k==NR_LB_AL||k==NR_LB_HL;}
static int hangul(int k){return k==NR_LB_JL||k==NR_LB_JV||k==NR_LB_JT||k==NR_LB_H2||k==NR_LB_H3;}
static int aksara(const LineUnit*u){return u->kind==NR_LB_AK||u->kind==NR_LB_AS||u->scalar==0x25cc;}
static int quoteContext(int k){return hard(k)||k==NR_LB_OP||k==NR_LB_QU||k==NR_LB_GL||k==NR_LB_SP||k==NR_LB_ZW;}
static int closingContext(int k){return (quoteContext(k)&&k!=NR_LB_OP)||k==NR_LB_WJ||k==NR_LB_CL||k==NR_LB_CP||k==NR_LB_EX||k==NR_LB_IS||k==NR_LB_SY;}
static int boundary(const LineUnit*u,int n,int at){
 const LineUnit*l=&u[at-1],*r=&u[at];int a=l->kind,b=r->kind;
 if(a==NR_LB_BK)return 1;
 if(a==NR_LB_CR&&b==NR_LB_LF)return 0;
 if(hard(a))return 1;if(hard(b))return 0;
 if(b==NR_LB_SP||b==NR_LB_ZW)return 0;
 int prior=at-1;while(prior>=0&&u[prior].kind==NR_LB_SP)prior--;
 if(prior>=0&&u[prior].kind==NR_LB_ZW)return 1;
 if(l->lastZwj)return 0;
 if(a==NR_LB_WJ||b==NR_LB_WJ||a==NR_LB_GL)return 0;
 if(b==NR_LB_GL&&a!=NR_LB_SP&&a!=NR_LB_BA&&a!=NR_LB_HY&&a!=NR_LB_HH)return 0;
 if(b==NR_LB_CL||b==NR_LB_CP||b==NR_LB_EX||b==NR_LB_SY)return 0;
 if(prior>=0&&u[prior].kind==NR_LB_OP)return 0;
 if(prior>=0&&u[prior].kind==NR_LB_QU&&(u[prior].flags&2)&&(prior==0||quoteContext(u[prior-1].kind)))return 0;
 if(b==NR_LB_QU&&(r->flags&4)&&(at+1==n||closingContext(u[at+1].kind)))return 0;
 if(a==NR_LB_SP&&b==NR_LB_IS&&at+1<n&&u[at+1].kind==NR_LB_NU)return 1;
 if(b==NR_LB_IS)return 0;
 if(prior>=0&&(u[prior].kind==NR_LB_CL||u[prior].kind==NR_LB_CP)&&b==NR_LB_NS)return 0;
 if(prior>=0&&u[prior].kind==NR_LB_B2&&b==NR_LB_B2)return 0;
 if(a==NR_LB_SP)return 1;
 if((b==NR_LB_QU&&!(r->flags&2))||(a==NR_LB_QU&&!(l->flags&4)))return 0;
 if(b==NR_LB_QU&&(!(l->flags&16)||at+1==n||!(u[at+1].flags&16)))return 0;
 if(a==NR_LB_QU&&(!(r->flags&16)||at==1||!(u[at-2].flags&16)))return 0;
 if(a==NR_LB_CB||b==NR_LB_CB)return 1;
 if((a==NR_LB_HY||a==NR_LB_HH)&&letters(b)&&(at==1||hard(u[at-2].kind)||u[at-2].kind==NR_LB_SP||u[at-2].kind==NR_LB_ZW||u[at-2].kind==NR_LB_CB||u[at-2].kind==NR_LB_GL))return 0;
 if(b==NR_LB_BA||b==NR_LB_HH||b==NR_LB_HY||b==NR_LB_NS||a==NR_LB_BB)return 0;
 if((a==NR_LB_HY||a==NR_LB_HH)&&at>=2&&u[at-2].kind==NR_LB_HL&&b!=NR_LB_HL)return 0;
 if(a==NR_LB_SY&&b==NR_LB_HL)return 0;if(b==NR_LB_IN)return 0;
 if((letters(a)&&b==NR_LB_NU)||(a==NR_LB_NU&&letters(b)))return 0;
 if((a==NR_LB_PR&&(b==NR_LB_ID||b==NR_LB_EB||b==NR_LB_EM))||((a==NR_LB_ID||a==NR_LB_EB||a==NR_LB_EM)&&b==NR_LB_PO))return 0;
 if(((a==NR_LB_PR||a==NR_LB_PO)&&letters(b))||(letters(a)&&(b==NR_LB_PR||b==NR_LB_PO)))return 0;
 int numeric=at-1;if(u[numeric].kind==NR_LB_CL||u[numeric].kind==NR_LB_CP)numeric--;
 while(numeric>=0&&(u[numeric].kind==NR_LB_SY||u[numeric].kind==NR_LB_IS))numeric--;
 if(numeric>=0&&u[numeric].kind==NR_LB_NU&&(b==NR_LB_PO||b==NR_LB_PR))return 0;
 if((a==NR_LB_PO||a==NR_LB_PR)&&(b==NR_LB_NU||(b==NR_LB_OP&&at+1<n&&(u[at+1].kind==NR_LB_NU||(u[at+1].kind==NR_LB_IS&&at+2<n&&u[at+2].kind==NR_LB_NU)))))return 0;
 if((a==NR_LB_HY||a==NR_LB_IS)&&b==NR_LB_NU)return 0;
 numeric=at-1;while(numeric>=0&&(u[numeric].kind==NR_LB_SY||u[numeric].kind==NR_LB_IS))numeric--;
 if(numeric>=0&&u[numeric].kind==NR_LB_NU&&b==NR_LB_NU)return 0;
 if(a==NR_LB_JL&&(b==NR_LB_JL||b==NR_LB_JV||b==NR_LB_H2||b==NR_LB_H3))return 0;
 if((a==NR_LB_JV||a==NR_LB_H2)&&(b==NR_LB_JV||b==NR_LB_JT))return 0;
 if((a==NR_LB_JT||a==NR_LB_H3)&&b==NR_LB_JT)return 0;
 if((hangul(a)&&b==NR_LB_PO)||(a==NR_LB_PR&&hangul(b)))return 0;
 if(letters(a)&&letters(b))return 0;
 if(a==NR_LB_AP&&aksara(r))return 0;
 if(aksara(l)&&(b==NR_LB_VF||b==NR_LB_VI))return 0;
 if(a==NR_LB_VI&&at>=2&&aksara(&u[at-2])&&(b==NR_LB_AK||r->scalar==0x25cc))return 0;
 if(aksara(l)&&aksara(r)&&at+1<n&&u[at+1].kind==NR_LB_VF)return 0;
 if(a==NR_LB_IS&&letters(b))return 0;
 if((letters(a)||a==NR_LB_NU)&&b==NR_LB_OP&&!(r->flags&16))return 0;
 if(a==NR_LB_CP&&!(l->flags&16)&&(letters(b)||b==NR_LB_NU))return 0;
 if(a==NR_LB_RI&&b==NR_LB_RI){int run=0;for(int k=at-1;k>=0&&u[k].kind==NR_LB_RI;k--)run++;if(run%2)return 0;}
 if(b==NR_LB_EM&&(a==NR_LB_EB||((l->flags&40)==40)))return 0;
 return 1;
}
int nrLineBreaks(const uint32_t*text,uint32_t count,uint32_t*out,uint32_t capacity){
 if(count>NR_MAX_TEXT||(!text&&count)||(!out&&capacity)||((uintptr_t)text%4)||((uintptr_t)out%4))return -1;
 LineUnit units[NR_MAX_TEXT];int used=0;
 for(uint32_t i=0;i<count;i++){
  uint32_t scalar=text[i];if(scalar>0x10ffff||(scalar>=0xd800&&scalar<=0xdfff))return -1;
  int kind=lineClass(scalar),flags=lineFlags(scalar),raw=kind;
  if(kind==NR_LB_AI||kind==NR_LB_SG||kind==NR_LB_XX)kind=NR_LB_AL;
  else if(kind==NR_LB_SA)kind=(flags&1)?NR_LB_CM:NR_LB_AL;
  else if(kind==NR_LB_CJ)kind=NR_LB_NS;
  if(kind==NR_LB_CM||kind==NR_LB_ZWJ){
   if(used&&!hard(units[used-1].kind)&&units[used-1].kind!=NR_LB_SP&&units[used-1].kind!=NR_LB_ZW){units[used-1].end=i+1;units[used-1].lastZwj=raw==NR_LB_ZWJ;continue;}
   kind=NR_LB_AL;flags=0;scalar=0x41;
  }
  units[used++]=(LineUnit){scalar,i,i+1,(uint8_t)kind,(uint8_t)flags,raw==NR_LB_ZWJ};
 }
 uint32_t offsets[NR_MAX_TEXT+1],size=0;
 for(int i=1;i<used;i++)if(boundary(units,used,i))offsets[size++]=units[i].start;
 offsets[size++]=count;
 if(!out)return (int)size;if(capacity<size)return -1;memcpy(out,offsets,size*sizeof(uint32_t));return (int)size;
}
int nrLineBreakDetails(const uint32_t*text,uint32_t count,uint32_t*out,uint32_t capacity){
 if((!out&&capacity)||((uintptr_t)out%4))return -1;
 uint32_t offsets[NR_MAX_TEXT+1],rows[(NR_MAX_TEXT+1)*2];
 int size=nrLineBreaks(text,count,offsets,NR_MAX_TEXT+1);if(size<0)return -1;
 for(int i=0;i<size;i++){
  uint32_t offset=offsets[i];rows[2*i]=offset;
  rows[2*i+1]=offset==count||(offset&&hard(lineClass(text[offset-1])));
 }
 if(!out)return size;if(capacity<(uint32_t)size)return -1;
 memcpy(out,rows,(size_t)size*2*sizeof(uint32_t));return size;
}
