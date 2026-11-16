#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include "nocturne_studio.h"
/* Additive function; legacy ABI must remain unchanged. */
extern int32_t nsFleetInkOpacity(uint32_t,uint32_t,int32_t,int32_t,int32_t);
int main(void){
 assert(nsStageConfigSize()==704);
 assert(nsFleetInkOpacity(0,420,2000,1500,760)==0);
 assert(nsFleetInkOpacity(420,420,0,1500,760)==760);
 assert(nsFleetInkOpacity(420,420,750,1500,760)==880);
 assert(nsFleetInkOpacity(420,420,1500,1500,760)==1000);
 assert(nsFleetInkOpacity(UINT32_MAX,420,1500,1500,760)==1000);
 assert(nsFleetInkOpacity(0,0,1500,1500,760)==1000);
 assert(nsFleetInkOpacity(100,420,0,-1,760)==-1);
 assert(nsFleetInkOpacity(100,420,0,1,1001)==-1);
 int count=0;
 for(int age=0;age<650;age+=13)for(int y=-256;y<2048;y+=37){int a=nsFleetInkOpacity(age,420,y,1536,760);assert(a>=0&&a<=1000);if(age>0)assert(a>=nsFleetInkOpacity(age-1,420,y,1536,760));count++;}
 printf("PASS fleet ink opacity: %d range/monotonic cases + boundary assertions\n",count);
 return 0;
}
