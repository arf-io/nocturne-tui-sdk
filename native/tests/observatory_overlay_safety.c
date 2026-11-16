#define _POSIX_C_SOURCE 200809L
#include "nocturne_native.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(int argc,char**argv){assert(argc==2);FILE*f=fopen(argv[1],"r");assert(f);NrContext*c=malloc(nrContextSize());assert(c);char*line=0;size_t cap=0;void*scratch=0;unsigned rows=0;ssize_t length;
while((length=getline(&line,&cap,f))>=0){while(length&&line[length-1]=='\n')line[--length]=0;
if(!strcmp(line,"@reset")){free(scratch);scratch=0;assert(nrInit(c,nrContextSize(),2030)==0);continue;}
if(!strcmp(line,"@render")){uint64_t needed=nrRenderMemorySize(c);assert(needed&&needed<=SIZE_MAX-16);if(needed>nrRenderMemoryCapacity(c)){void*p=malloc((size_t)needed+16);assert(p);memset(p,0x7d,(size_t)needed+16);assert(nrSetRenderMemory(c,p,needed)==0);free(scratch);scratch=p;}uint32_t size=nrSnapshotSizeFor(c);void*a=malloc(size),*b=malloc(size);assert(a&&b);assert(nrSave(c,a,size)==0);assert(nrRender(c)==nrWidth(c)*nrHeight(c));assert(nrSave(c,b,size)==0);assert(!memcmp(a,b,size));free(a);free(b);if(scratch)for(unsigned k=0;k<16;k++)assert(((unsigned char*)scratch)[needed+k]==0x7d);rows++;continue;}
int result;do{result=nrCommand(c,line,(uint32_t)length);}while(result==1);if(result<0){fprintf(stderr,"Rejected fixture command: %s\n",line);abort();}}
free(line);free(scratch);free(c);fclose(f);printf("PASS %u actual source rows through sanitized public API\n",rows);return 0;}
