#include "../src/internal.h"
int nrTestCharacterPaint(void){
    NrCell original={.glyph='A',.foreground=0xffffff,.background=0,.id=NR_ID_WIDGET|7},out;
    CharacterPaint paint={0};
    if(nrCharacterPaintCell(&original,&paint,0,&out)||memcmp(&original,&out,sizeof(out)))return 1;
    paint.hasForeground=1;paint.foreground=0xff0000;paint.foregroundAlpha=65535;
    if(nrCharacterPaintCell(&original,&paint,0,&out)||out.foreground!=0xff0000||
       out.background||out.glyph!='A'||out.id!=original.id)return 2;
    paint.foregroundAlpha=0;
    if(nrCharacterPaintCell(&original,&paint,0,&out)||out.foreground!=original.background)return 3;
    paint.protectLocalInk=1;
    if(nrCharacterPaintCell(&original,&paint,1,&out)||out.foreground!=0xff0000)return 4;
    paint.hasForeground=0;paint.hasBackground=1;paint.background=0x0000ff;paint.backgroundAlpha=65535;
    if(nrCharacterPaintCell(&original,&paint,0,&out)||out.background!=0x0000ff||out.foreground!=0xffffff)return 5;
    uint32_t blocks[]={0x2580,0x2584,0x2591,0x2801};
    for(unsigned i=0;i<4;i++){
        NrCell block=original;block.glyph=blocks[i];
        if(nrCharacterPaintCell(&block,&paint,0,&out)||out.foreground!=0x0000ff||out.background!=0x0000ff||out.glyph!=blocks[i]||out.id!=block.id)return 6;
    }
    NrCell sentinel={.glyph=123,.foreground=456,.background=789,.id=42};out=sentinel;
    paint.backgroundAlpha=65536;
    if(nrCharacterPaintCell(&original,&paint,0,&out)!=-1||memcmp(&out,&sentinel,sizeof(out)))return 7;
    paint.backgroundAlpha=65535;paint.operation=13;
    if(nrCharacterPaintCell(&original,&paint,0,&out)!=-1||memcmp(&out,&sentinel,sizeof(out)))return 8;
    paint.operation=0;
    NrCell inPlace=original;
    if(nrCharacterPaintCell(&inPlace,&paint,0,&inPlace)||inPlace.background!=0x0000ff||inPlace.id!=original.id)return 9;
    uint32_t mixed[2],expected[]={0x808080,0xbcbcbc,0x636363,0x636363};
    for(uint32_t space=0;space<4;space++){
        if(nrCompositeInSpace(0,0xffffff,65535,32768,0,0,0,space,mixed)||mixed[0]!=expected[space]||mixed[1]!=65535)return 10;
        if(nrCompositeInSpace(0x123456,0xabcdef,65535,65535,0,0,0,space,mixed)||mixed[0]!=0xabcdef)return 11;
        if(nrCompositeInSpace(0x123456,0xabcdef,65535,0,0,0,0,space,mixed)||mixed[0]!=0x123456)return 12;
    }
    mixed[0]=123;mixed[1]=456;
    if(nrCompositeInSpace(0,0,65535,65535,0,0,0,4,mixed)!=-1||mixed[0]!=123||mixed[1]!=456)return 13;
    CharacterEffects foreground={.count=1},background={.count=1};
    foreground.entries[0]=(CharacterEffect){.type=0,.value=1};
    background.entries[0]=(CharacterEffect){.type=0,.value=1};
    memset(&paint,0,sizeof(paint));paint.backgroundAlpha=65535;
    if(nrCharacterPaintEffectsCell(&original,&paint,&foreground,&background,0,0,&out)||
       out.background!=0xffffff||out.foreground!=0||out.glyph!=original.glyph||out.id!=original.id)return 14;
    /* Foreground alpha effects resolve against the already transformed background. */
    foreground.entries[0]=(CharacterEffect){.type=1,.value=0};
    if(nrCharacterPaintEffectsCell(&original,&paint,&foreground,NULL,0,0,&out)||out.foreground!=0)return 15;
    paint.protectLocalInk=1;
    if(nrCharacterPaintEffectsCell(&original,&paint,&foreground,NULL,0,1,&out)||out.foreground!=0xffffff)return 16;
    foreground.entries[0]=(CharacterEffect){.type=0,.value=1,.where=1};
    if(nrCharacterPaintEffectsCell(&original,&paint,&foreground,NULL,0,0,&out)||out.foreground!=0xffffff)return 17;
    if(nrCharacterPaintEffectsCell(&original,&paint,&foreground,NULL,1,0,&out)||out.foreground!=0)return 18;
    foreground.entries[0].type=99;out=sentinel;
    if(nrCharacterPaintEffectsCell(&original,&paint,&foreground,&background,0,0,&out)!=-1||memcmp(&out,&sentinel,sizeof(out)))return 19;
    foreground.count=0;background.count=0;paint.space=4;out=sentinel;
    if(nrCharacterPaintEffectsCell(&original,&paint,&foreground,&background,0,0,&out)!=-1||memcmp(&out,&sentinel,sizeof(out)))return 20;
    paint.space=0;paint.hasForeground=2;
    if(nrCharacterPaintEffectsCell(&original,&paint,NULL,NULL,0,0,&out)!=-1||memcmp(&out,&sentinel,sizeof(out)))return 21;
    paint.hasForeground=0;inPlace=original;
    if(nrCharacterPaintEffectsCell(&inPlace,&paint,&foreground,&background,0,0,&inPlace)||memcmp(&inPlace,&original,sizeof(original)))return 22;
    return 0;
}
