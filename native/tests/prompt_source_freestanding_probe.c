#include "prompt_source.h"

typedef struct { uint32_t glyphs, backgrounds; } ProbeCounts;
static void background(void *context,int32_t x,int32_t y,uint32_t rgb,double alpha,int kind,int owner){
    ProbeCounts *counts=context;(void)x;(void)y;(void)rgb;(void)alpha;(void)kind;(void)owner;counts->backgrounds++;
}
static void glyph(void *context,int32_t x,int32_t y,uint32_t scalar,uint32_t rgb,double alpha,int kind,int owner){
    ProbeCounts *counts=context;(void)x;(void)y;(void)scalar;(void)rgb;(void)alpha;(void)kind;(void)owner;counts->glyphs++;
}

int prompt_source_freestanding_probe(void){
    static const uint32_t text[]={'T','e','s','t'};
    static const uint32_t status[]={'E','s','c',' ','N','O','R','M','A','L'};
    NrPromptSourceInput input={0};
    input.scalars=text;input.scalarCount=4;input.caret=0;
    input.statusScalars=status;input.statusCount=sizeof(status)/sizeof(status[0]);
    input.width=100;input.height=40;input.mode=NR_PROMPT_SOURCE_MARQUEE;
    input.vimState=NR_PROMPT_SOURCE_VIM_NORMAL;
    input.options.alpha=.32;input.options.background=0x10161e;
    input.options.foreground=0xdedbd2;input.options.accent=0x8ccfc4;
    input.options.selectionColor=0x385763;input.options.border=NR_PROMPT_SOURCE_BORDER_ROUNDED;
    input.options.paddingX=1;input.options.margin=1;input.options.minRows=1;
    input.options.maxRows=7;input.options.inlineRows=12;input.options.inlineWidth=88;
    input.options.lineNumbers=1;input.options.active=1;input.options.huePeriodMs=1000;
    input.options.maxChars=65536;
    NrPromptSourceLayout layout;
    if(nrPromptSourceLayout(&input,&layout)||layout.rectX!=1||layout.rectY!=35||
       layout.rectWidth!=98||layout.rectHeight!=3||layout.innerX!=5||layout.innerY!=36)return 1;
    ProbeCounts counts={0};NrPromptSourceSink sink={&counts,background,glyph};
    if(nrPromptSourcePaint(&input,&layout,sink))return 2;
    return counts.glyphs>0&&counts.backgrounds>0?0:3;
}
