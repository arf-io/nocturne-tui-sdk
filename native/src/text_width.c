#include "internal.h"
#include "grapheme_cursor.h"
typedef struct {uint32_t first,last,flags;} WidthRange;
#include "unicode_width.inc"
static uint32_t widthFlags(uint32_t scalar) {
    size_t low=0,high=sizeof(widthRanges)/sizeof(widthRanges[0]);
    while(low<high) {
        size_t middle=low+(high-low)/2;
        if(scalar<widthRanges[middle].first)high=middle;
        else if(scalar>widthRanges[middle].last)low=middle+1;
        else return widthRanges[middle].flags;
    }
    return 0;
}
static uint32_t clusterWidth(const uint32_t*text,uint32_t first,uint32_t last,uint32_t ambiguous){
    uint32_t columns=0;
        for(uint32_t i=first;i<last;i++) {
            uint32_t flags=widthFlags(text[i]);
            if(flags&4)continue;
            uint32_t w=(flags&1)?2:(flags&2)?ambiguous:1;
            int textVariation=(flags&16)&&i+1<last&&text[i+1]==0xfe0e;
            int emojiVariation=(flags&16)&&i+1<last&&text[i+1]==0xfe0f;
            if(emojiVariation||((flags&8)&&!textVariation))w=2;
            if(w>columns)columns=w;
        }
        /* Keycap bases have an optional emoji selector before the enclosing mark. */
        if((text[first]=='#'||text[first]=='*'||(text[first]>='0'&&text[first]<='9'))&&
           ((last-first>=2&&text[first+1]==0x20e3)||
            (last-first>=3&&text[first+1]==0xfe0f&&text[first+2]==0x20e3)))columns=2;
    return columns;
}
int nrGraphemeWidths(const uint32_t*text,uint32_t count,uint32_t ambiguous,uint32_t*out,uint32_t capacity) {
    if(count>NR_MAX_TEXT||(ambiguous!=1&&ambiguous!=2)||(!out&&capacity))return -1;
    uint32_t boundaries[NR_MAX_TEXT+1],rows[NR_MAX_TEXT*3];
    int n=nrGraphemeBreaks(text,count,boundaries,NR_MAX_TEXT+1);
    if(n<0)return -1;
    uint32_t clusters=(uint32_t)n-1;
    if(!out&&!capacity)return (int)clusters;
    if(capacity<clusters)return -1;
    for(uint32_t c=0;c<clusters;c++) {
        uint32_t first=boundaries[c],last=boundaries[c+1],columns=clusterWidth(text,first,last,ambiguous);
        rows[c*3]=first;rows[c*3+1]=last;rows[c*3+2]=columns;
    }
    if(clusters)memcpy(out,rows,clusters*3*sizeof(uint32_t));
    return (int)clusters;
}
int nrGraphemeLayout(const uint32_t*text,uint32_t count,uint32_t ambiguous,uint32_t columns,uint32_t*out,uint32_t capacity) {
    if(!columns||(!out&&capacity))return -1;
    uint32_t metrics[NR_MAX_TEXT*3],rows[NR_MAX_TEXT*5];
    int n=nrGraphemeWidths(text,count,ambiguous,metrics,NR_MAX_TEXT);
    if(n<0)return -1;
    if(!out&&!capacity)return n;
    if(capacity<(uint32_t)n)return -1;
    uint32_t x=0,y=0;
    for(int i=0;i<n;i++) {
        uint32_t first=metrics[i*3],last=metrics[i*3+1],width=metrics[i*3+2],scalar=text[first];
        int newline=scalar==10||scalar==11||scalar==12||scalar==13||scalar==0x85||scalar==0x2028||scalar==0x2029;
        if(newline)width=0;
        else {
            if(scalar==9){width=4-x%4;if(width>columns)width=columns;}
            if(width&&x&&(uint64_t)x+width>columns) {
                x=0;y++;
                if(scalar==9)width=columns<4?columns:4;
            }
        }
        rows[i*5]=first;rows[i*5+1]=last;rows[i*5+2]=x;rows[i*5+3]=y;rows[i*5+4]=width;
        if(newline){x=0;y++;}else x+=width;
    }
    if(n)memcpy(out,rows,(size_t)n*5*sizeof(uint32_t));
    return n;
}

int nrGraphemeHit(const uint32_t*text,uint32_t count,uint32_t ambiguous,
                  uint32_t columns,uint32_t column,uint32_t row) {
    uint32_t layout[NR_MAX_TEXT*5];
    int n=nrGraphemeLayout(text,count,ambiguous,columns,layout,NR_MAX_TEXT);
    if(n<0)return -1;
    uint32_t selected=0;
    uint64_t bestRow=UINT64_MAX,bestColumn=UINT64_MAX;
    /* Evaluate both edges of every whole cluster, including the source end.
       Vertical proximity takes precedence; ties prefer the later boundary. */
    for(int i=0;i<n;i++) {
        uint32_t first=layout[i*5],last=layout[i*5+1];
        uint32_t x=layout[i*5+2],y=layout[i*5+3],width=layout[i*5+4];
        uint32_t scalar=text[first];
        int newline=scalar==10||scalar==11||scalar==12||scalar==13||scalar==0x85||scalar==0x2028||scalar==0x2029;
        for(int edge=0;edge<2;edge++) {
            uint32_t at=edge?last:first;
            uint64_t cx=edge?(newline?0:(uint64_t)x+width):x;
            uint64_t cy=(uint64_t)y+(edge&&newline);
            uint64_t dy=cy>row?cy-row:row-cy;
            uint64_t dx=cx>column?cx-column:column-cx;
            if(dy<bestRow||(dy==bestRow&&(dx<bestColumn||(dx==bestColumn&&at>selected)))) {
                bestRow=dy;bestColumn=dx;selected=at;
            }
        }
    }
    return (int)selected;
}

/* Two-pass traversal writes caller-owned rows with constant stack usage. */
int nrDocumentGraphemeLayout(const uint32_t*text,uint32_t count,uint32_t ambiguous,uint32_t columns,uint32_t*out,uint32_t capacity){
    if(!columns||(ambiguous!=1&&ambiguous!=2)||(!out&&capacity))return -1;
    int breaks=nrGraphemeBreaks(text,count,0,0);if(breaks<1)return -1;
    uint32_t n=(uint32_t)breaks-1;if(!out&&!capacity)return (int)n;
    if(capacity<n||nrGraphemeOutputOverlaps(text,count,out,(uint64_t)n*5))return -1;
    NrGraphemeCursor cursor={.text=text,.count=count};uint32_t first,last,x=0,y=0,index=0;
    nrGraphemeCursorNext(&cursor,&first);
    while(nrGraphemeCursorNext(&cursor,&last)){
        uint32_t width=clusterWidth(text,first,last,ambiguous),scalar=text[first];
        int newline=scalar==10||scalar==11||scalar==12||scalar==13||scalar==0x85||scalar==0x2028||scalar==0x2029;
        if(newline)width=0;
        else{if(scalar==9){width=4-x%4;if(width>columns)width=columns;}
            if(width&&x&&(uint64_t)x+width>columns){x=0;y++;if(scalar==9)width=columns<4?columns:4;}}
        uint32_t row[5]={first,last,x,y,width};memcpy(out+(size_t)index++*5,row,sizeof(row));
        if(newline){x=0;y++;}else x+=width;
        first=last;
    }return (int)n;
}
