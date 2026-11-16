#include "internal.h"

/* The workbench keeps its established projection margins. Canvas makes the
 * actual output extent available; an enabled editor or inspector still owns
 * its visible space. Allocation limits are checked by nrValidViewport. */
void nrSceneViewport(const State*s,int*width,int*height){
    int w=(int)s->width-(s->selection?38:0);
    int h=(int)s->height-nrPromptRows(s)-3;
    if(s->canvasPresentation){
        h=(int)s->height;
        if(s->promptDocument.active){
            h=(int)s->height-nrPromptRows(s)-2;
            if(h<3)h=3;
            if(s->promptDocument.mode>=2)h=s->promptDocument.mode==3?3:h-2;
        }
    }
    if(s->promptFramed.enabled){
        NrPromptSourceInput input;NrPromptSourceLayout layout;
        if(nrPromptFramedLayout(s,&input,&layout)==0)h=layout.sceneHeight;
    }
    if(s->canvasPresentation||s->sceneArt.used){
        if(w<1)w=1;if(w>(int)s->width)w=(int)s->width;
        if(h<1)h=1;if(h>(int)s->height)h=(int)s->height;
    }else{if(w<20)w=20;if(h<6)h=6;}
    *width=w;*height=h;
}
