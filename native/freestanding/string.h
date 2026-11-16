#ifndef NR_STRING_H
#define NR_STRING_H
#include <stddef.h>
char *strrchr(const char*,int);
void *memcpy(void*,const void*,size_t);void *memmove(void*,const void*,size_t);void *memset(void*,int,size_t);int memcmp(const void*,const void*,size_t);size_t strlen(const char*);int strcmp(const char*,const char*);int strncmp(const char*,const char*,size_t);
#endif
