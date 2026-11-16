#include "nocturne_studio.h"
#include <assert.h>
#include <stdio.h>
int main(void){
 assert(nsOklchColor(-1,1000,0)==-1);assert(nsOklchColor(1001,1000,0)==-1);
 assert(nsOklchColor(0,0,0)==0);assert(nsOklchColor(1000,0,0)==0xffffff);
 unsigned count=0;
 for(int l=100;l<=900;l+=100)for(int c=0;c<=4000;c+=400)for(int h=0;h<360000;h+=5000){
  int color=nsOklchColor(l,c,h);assert(color>=0&&color<=0xffffff);
  int light=nsOklchLightness((unsigned)color);assert(light>=l-5&&light<=l+5);count++;
 }
 printf("OKLCh: %u range and lightness cases\n",count);return 0;
}
