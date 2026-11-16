#include "internal.h"
/* Pure owned-cell transform for the encoded RGB composition stage. Glyphs and
 * hit IDs are immutable. This kernel does not claim the complete rule language. */
static int validPaint(const NrCell*input,const CharacterPaint*paint){
    if(!input||!paint||input->foreground>0xffffff||input->background>0xffffff||
       paint->foreground>0xffffff||paint->background>0xffffff||
       paint->foregroundAlpha>65535||paint->backgroundAlpha>65535||
       paint->foregroundBlend>27||paint->backgroundBlend>27||paint->operation>12||paint->space>3||
       paint->hasForeground<0||paint->hasForeground>1||paint->hasBackground<0||paint->hasBackground>1||
       paint->protectLocalInk<0||paint->protectLocalInk>1)return 0;
    return 1;
}
int nrCharacterPaintCell(const NrCell*input,const CharacterPaint*paint,int userText,NrCell*out){
    if(!out||!validPaint(input,paint))return -1;
    NrCell result=*input;uint32_t colors[2];
    if(paint->hasBackground){
        if(nrCompositeInSpace(result.background,paint->background,65535,paint->backgroundAlpha,
                       paint->backgroundBlend,paint->operation,paint->seed,paint->space,colors))return -1;
        result.background=colors[0];
        if((result.glyph>=0x2580&&result.glyph<=0x259f)||(result.glyph>=0x2800&&result.glyph<=0x28ff)){
            if(nrCompositeInSpace(result.foreground,paint->background,65535,paint->backgroundAlpha,
                           paint->backgroundBlend,paint->operation,paint->seed,paint->space,colors))return -1;
            result.foreground=colors[0];
        }
    }
    if(paint->hasForeground){
        if(nrCompositeInSpace(result.foreground,paint->foreground,65535,65535,
                       paint->foregroundBlend,paint->operation,paint->seed,paint->space,colors))return -1;
        uint32_t alpha=userText&&paint->protectLocalInk?65535:paint->foregroundAlpha;
        if(nrCompositeInSpace(result.background,colors[0],65535,alpha,0,0,paint->seed,paint->space,colors))return -1;
        result.foreground=colors[0];
    }
    *out=result;return 0;
}
static void unpack(uint32_t color,uint32_t alpha,double*out){
    out[0]=((color>>16)&255)/255.0;out[1]=((color>>8)&255)/255.0;
    out[2]=(color&255)/255.0;out[3]=alpha/65535.0;
}
int nrCharacterPaintEffectsCell(const NrCell*input,const CharacterPaint*paint,const CharacterEffects*foreground,const CharacterEffects*background,int selected,int userText,NrCell*out){
    if(!out||!validPaint(input,paint))return -1;
    CharacterPaint sampled=*paint;NrCell result;
    if(background&&background->count){
        double source[4],changed[4];
        unpack(paint->hasBackground?paint->background:input->background,65535,source);
        if(nrApplyCharacterEffects(background,selected,source,changed))return -1;
        sampled.hasBackground=1;
        sampled.background=nrRgb(changed[0],changed[1],changed[2]);
        sampled.backgroundAlpha=(uint32_t)(changed[3]*paint->backgroundAlpha+.5);
    }else if(background){double source[4]={0,0,0,1},changed[4];if(nrApplyCharacterEffects(background,selected,source,changed))return -1;}
    if(nrCharacterPaintCell(input,&sampled,userText,&result))return -1;
    if(foreground&&foreground->count){
        double source[4],changed[4];unpack(result.foreground,65535,source);
        if(nrApplyCharacterEffects(foreground,selected,source,changed))return -1;
        uint32_t color=nrRgb(changed[0],changed[1],changed[2]);
        uint32_t alpha=userText&&paint->protectLocalInk?65535:(uint32_t)(changed[3]*65535+.5);
        uint32_t mixed[2];
        if(nrCompositeInSpace(result.background,color,65535,alpha,0,0,paint->seed,paint->space,mixed))return -1;
        result.foreground=mixed[0];
    }
    *out=result;return 0;
}
