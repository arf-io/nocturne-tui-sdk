#include <stddef.h>
#include <stdint.h>
char *strrchr(const char*s,int character) {
    const char*last=0;unsigned char sought=(unsigned char)character;
    do{if((unsigned char)*s==sought)last=s;}while(*s++);
    return (char*)last;
}
/* Every command copies the fixed State twice (state.c nrCommand); byte loops made those
 * copies the dominant per-command cost in browsers. With bulk memory (build.py passes
 * -mbulk-memory) the builtins lower to memory.copy and memory.fill, which engines run as
 * native memmove/memset; tests/test_wasm_memory_routines.py checks the lowering and the
 * results. Without the feature the builtins would call back into these functions, so the
 * original byte loops remain the fallback. */
#if defined(__wasm_bulk_memory__) || defined(__wasm_bulk_memory_opt__)
void *memcpy(void *d,const void *s,size_t n) {
    __builtin_memcpy(d,s,n);
    return d;
}
void *memmove(void*d,const void*s,size_t n) {
    __builtin_memmove(d,s,n);
    return d;
}
void *memset(void*d,int v,size_t n) {
    __builtin_memset(d,v,n);
    return d;
}
#else
void *memcpy(void *d,const void *s,size_t n) {
    unsigned char*a=d;
    const unsigned char*b=s;
    for(size_t i=0; i<n; i++)a[i]=b[i];
    return d;
}
void *memmove(void*d,const void*s,size_t n) {
    unsigned char*a=d;
    const unsigned char*b=s;
    if(a<b)for(size_t i=0; i<n; i++)a[i]=b[i];
    else for(size_t i=n; i; i--)a[i-1]=b[i-1];
    return d;
}
void *memset(void*d,int v,size_t n) {
    unsigned char*a=d;
    for(size_t i=0; i<n; i++)a[i]=(unsigned char)v;
    return d;
}
#endif
/* Equal 8-byte words are skipped (WASM loads need no alignment); the first differing
 * byte is still found and returned exactly as the byte loop returns it. */
int memcmp(const void*a,const void*b,size_t n) {
    const unsigned char*x=a,*y=b;
    size_t i=0;
    for(; i+8<=n; i+=8) {
        uint64_t p,q;
        __builtin_memcpy(&p,x+i,8);
        __builtin_memcpy(&q,y+i,8);
        if(p!=q)break;
    }
    for(; i<n; i++)if(x[i]!=y[i])return x[i]-y[i];
    return 0;
}
size_t strlen(const char*s) {
    size_t n=0;
    while(s[n])n++;
    return n;
}
int strcmp(const char*a,const char*b) {
    for(; *a&&*a==*b; a++,b++) {
    }
    return (unsigned char)*a-(unsigned char)*b;
}
int strncmp(const char*a,const char*b,size_t n) {
    for(size_t i=0; i<n; i++) {
        if(a[i]!=b[i])return (unsigned char)a[i]-(unsigned char)b[i];
        if(!a[i])return 0;
    }
    return 0;
}
extern unsigned char __heap_base;
static uint32_t cursor;
static uint32_t reserve(uint32_t p,uint32_t n) {
    uint64_t q=((uint64_t)p+n+7u)&~UINT64_C(7);
    if(q>UINT32_MAX)return 0;
    uint64_t size=(uint64_t)__builtin_wasm_memory_size(0)*65536u;
    if(q>size) {
        uint32_t pages=(uint32_t)((q-size+65535u)/65536u);
        if(__builtin_wasm_memory_grow(0,pages)==(size_t)-1)return 0;
    }
    cursor=(uint32_t)q;return p;
}
uint32_t nrAlloc(uint32_t n) {
    if(!cursor)cursor=((uint32_t)(uintptr_t)&__heap_base+7u)&~7u;
    return reserve(cursor,n);
}
/* Owned binding scratch is allocated last and grows in place. Failure preserves
 * cursor and the prior allocation; successful resizes do not leak old blocks. */
uint32_t nrGrowLast(uint32_t p,uint32_t oldSize,uint32_t newSize) {
    if(!p||newSize<oldSize||(((uint64_t)p+oldSize+7u)&~UINT64_C(7))!=cursor)return 0;
    return reserve(p,newSize);
}
