/* Run under ASan+UBSan. Exercise buffer contracts, small geometry, and extremes. */
#include "nocturne.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
int main(void) {
    NsConfig config;
    NsCell *cells=malloc(sizeof(NsCell)*NS_MAX_CELLS);
    assert(cells);
    nsDefaultConfig(&config);
    assert(nsRender(NULL,0,NULL,0,cells,NS_MAX_CELLS)==-1);
    assert(nsRender(&config,0,NULL,1,cells,NS_MAX_CELLS)==-3);
    assert(nsRender(&config,0,NULL,0,cells,1)==-2);
    assert(nsRender(&config,0,NULL,0,NULL,NS_MAX_CELLS)==-2);
    for(int layout=0;layout<=4;layout++){
        for(int width=0;width<=100;width++){
            for(int height=0;height<=32;height++){
                config.values[NS_WIDTH]=width;
                config.values[NS_HEIGHT]=height;
                config.values[NS_LAYOUT]=layout;
                config.values[NS_EFFECT]=(width+height)%6;
                config.values[NS_PIXEL_MODE]=(width+height)%5;
                config.values[NS_COLOR_MODE]=(width+height)%3;
                config.values[NS_MODAL_OPEN]=1;
                config.values[NS_ORIGIN_X]=width%2?-1000000:1000000;
                config.values[NS_ORIGIN_Y]=height%2?-1000000:1000000;
                assert(nsRender(&config,UINT64_MAX,NULL,0,cells,NS_MAX_CELLS)==width*height);
            }
        }
    }
    config.values[NS_WIDTH]=512;config.values[NS_HEIGHT]=256;
    config.values[NS_LAYOUT]=1;config.values[NS_NEIGHBOR_SPEED_PERMILLE]=1;
    assert(nsRender(&config,UINT64_MAX,NULL,0,cells,NS_MAX_CELLS)==NS_MAX_CELLS);
    free(cells);
    puts("ASan+UBSan: 16665 geometry/material combinations and boundary contracts passed.");
    return 0;
}
