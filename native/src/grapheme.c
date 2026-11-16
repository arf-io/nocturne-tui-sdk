#include "internal.h"
#include "grapheme_cursor.h"
typedef struct {uint32_t first,last,flags;} UnicodeRange;
#include "unicode_grapheme.inc"
enum {G_OTHER,G_CR,G_LF,G_CONTROL,G_EXTEND,G_ZWJ,G_RI,G_PREPEND,G_SPACING,G_L,G_V,G_T,G_LV,G_LVT};
static uint32_t unicodeFlags(uint32_t scalar) {
    size_t low=0,high=sizeof(unicodeRanges)/sizeof(unicodeRanges[0]);
    while(low<high) {
        size_t middle=low+(high-low)/2;
        if(scalar<unicodeRanges[middle].first)high=middle;
        else if(scalar>unicodeRanges[middle].last)low=middle+1;
        else return unicodeRanges[middle].flags;
    }
    return 0;
}
static int control(int p){return p==G_CR||p==G_LF||p==G_CONTROL;}
int nrGraphemeCursorNext(NrGraphemeCursor*c,uint32_t*out) {
    if(!c->started){c->started=1;*out=0;return 1;}
    if(c->finished)return 0;
    while(c->index<c->count) {
        uint32_t i=c->index++,f=unicodeFlags(c->text[i]);
        int current=f&15,ep=(f&16)!=0,incb=(f>>5)&3,split=0;
        if(i) {
            int previous=c->previous;split=1;
            if(previous==G_CR&&current==G_LF)split=0;
            else if(control(previous)||control(current))split=1;
            else if(previous==G_L&&(current==G_L||current==G_V||current==G_LV||current==G_LVT))split=0;
            else if((previous==G_LV||previous==G_V)&&(current==G_V||current==G_T))split=0;
            else if((previous==G_LVT||previous==G_T)&&current==G_T)split=0;
            else if(current==G_EXTEND||current==G_ZWJ||current==G_SPACING)split=0;
            else if(previous==G_PREPEND)split=0;
            else if(incb==1&&c->indic==2)split=0;
            else if(previous==G_ZWJ&&c->previousZwjHasEp&&ep)split=0;
            else if(previous==G_RI&&current==G_RI&&(c->riRun&1u))split=0;
        }
        c->previousZwjHasEp=current==G_ZWJ&&c->epChain;
        if(ep)c->epChain=1;else if(current!=G_EXTEND)c->epChain=0;
        if(incb==1)c->indic=1;else if(incb==3&&c->indic)c->indic=2;else if(incb!=2&&incb!=3)c->indic=0;
        c->riRun=current==G_RI?c->riRun+1:0;c->previous=current;
        if(split){*out=i;return 1;}
    }
    c->finished=1;if(c->count){*out=c->count;return 1;}return 0;
}
int nrGraphemeBreaks(const uint32_t*text,uint32_t count,uint32_t*out,uint32_t capacity) {
    if((!text&&count)||(!out&&capacity))return -1;
    for(uint32_t i=0;i<count;i++)if(text[i]>0x10ffffu||(text[i]>=0xd800u&&text[i]<=0xdfffu))return -1;
    NrGraphemeCursor cursor={.text=text,.count=count};uint32_t at,used=0;
    while(nrGraphemeCursorNext(&cursor,&at)){if(used==INT32_MAX)return -1;used++;}
    if(!out&&!capacity)return (int)used;
    if(capacity<used||nrGraphemeOutputOverlaps(text,count,out,used))return -1;
    cursor=(NrGraphemeCursor){.text=text,.count=count};uint32_t index=0;
    while(nrGraphemeCursorNext(&cursor,&at))memcpy(out+index++,&at,sizeof(at));
    return (int)used;
}
/* Scalar offsets remain the source ABI. These helpers choose cluster boundaries. */
int nrGraphemeBefore(const uint32_t*text,int count,int caret) {
    if(count<0||nrGraphemeBreaks(text,(uint32_t)count,0,0)<0)return 0;
    NrGraphemeCursor cursor={.text=text,.count=(uint32_t)count};uint32_t at;int before=0;
    while(nrGraphemeCursorNext(&cursor,&at)){if((int)at>=caret)break;before=(int)at;}return before;
}
int nrGraphemeAfter(const uint32_t*text,int count,int caret) {
    if(count<0||nrGraphemeBreaks(text,(uint32_t)count,0,0)<0)return count;
    NrGraphemeCursor cursor={.text=text,.count=(uint32_t)count};uint32_t at;
    while(nrGraphemeCursorNext(&cursor,&at))if((int)at>caret)return (int)at;return count;
}
int nrGraphemeFloor(const uint32_t*text,int count,int caret) {
    if(caret==count)return count;
    return nrGraphemeBefore(text,count,caret+1);
}
