#ifndef NOCTURNE_CHARACTER_TEST_CONTEXT_H
#define NOCTURNE_CHARACTER_TEST_CONTEXT_H
/* Test-owned contexts and pointer-free purity snapshots. No runtime substitutes. */
#include "../src/internal.h"
#include <assert.h>
#include <stdlib.h>
typedef struct {
    NrContext *context;
    unsigned char *before,*after;
    uint32_t beforeSize,afterSize;
} CharacterTestContext;
static uint32_t characterTestU32(const unsigned char*p){return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);}
static void characterTestSnapshot(NrContext*c,unsigned char**buffer,uint32_t*size){
    uint32_t needed=nrSnapshotSizeFor(c);assert(needed>=24);
    if(needed!=*size){unsigned char*next=realloc(*buffer,needed);assert(next);*buffer=next;*size=needed;}
    assert(nrSave(c,*buffer,*size)==0);
    assert(!memcmp(*buffer,"NRRC4SRC",8)&&characterTestU32(*buffer+16)==*size-24);
    assert(characterTestU32(*buffer+20)==nrCrc(*buffer+24,*size-24));
}
static void characterTestRemember(CharacterTestContext*f){characterTestSnapshot(f->context,&f->before,&f->beforeSize);}
static int characterTestUnchanged(CharacterTestContext*f){
    characterTestSnapshot(f->context,&f->after,&f->afterSize);
    return f->beforeSize==f->afterSize&&!memcmp(f->before,f->after,f->beforeSize);
}
static int characterTestReset(CharacterTestContext*f){
    int result=nrInit(f->context,nrContextSize(),42);if(result)return result;
    const char*draft="{\"op\":\"draft\",\"text\":\"Owned character fixture\",\"emitWeather\":false}";
    return nrCommand(f->context,draft,(uint32_t)strlen(draft));
}
static int characterTestRun(int(*checks)(CharacterTestContext*)){
    CharacterTestContext fixture={0};fixture.context=malloc(nrContextSize());assert(fixture.context);
    int result=characterTestReset(&fixture);
    if(!result){
        /* Detect an aliased-baseline bug: changing pointed-to prompt scalars must
         * change the saved wire even though every runtime pointer stays equal. */
        characterTestRemember(&fixture);Prompt*p=&fixture.context->state.promptDocument;
        assert(p->count>0);uint32_t saved=p->glyphs[0];p->glyphs[0]='X';
        assert(!characterTestUnchanged(&fixture));p->glyphs[0]=saved;assert(characterTestUnchanged(&fixture));
        result=checks(&fixture);
    }
    free(fixture.after);free(fixture.before);free(fixture.context);return result;
}
#endif
