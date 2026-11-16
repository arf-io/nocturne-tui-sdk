#include "internal.h"
static int list(const Json*j,int at,uint32_t*out,int*count){
    if(at<0)return 1;if(j->tokens[at].type!=J_ARRAY||j->tokens[at].count>4096)return 0;
    *count=j->tokens[at].count;int child=at+1;
    for(int i=0;i<*count;i++){double n;if(!nrNumber(j,child,&n)||!(n>=0&&n<=4294967295.0)||n!=(uint32_t)n)return 0;out[i]=(uint32_t)n;child=j->tokens[child].next;}return 1;
}
int nrCompileCharacterRegion(const Json*j,int at,CharacterRegion*out){
    if(!j||!out)return 0;
    CharacterRegion candidate;memset(&candidate,0,sizeof(candidate));
    if(!nrAllowed(j,at,"id role state path rect cells indices"))return 0;
    if(nrString(j,nrField(j,at,"id"),candidate.id,sizeof(candidate.id))<1||
       nrString(j,nrField(j,at,"path"),candidate.path,sizeof(candidate.path))<1||candidate.path[0]!='/')return 0;
    memcpy(candidate.role,"component",10);memcpy(candidate.state,"inactive",9);
    int role=nrField(j,at,"role"),state=nrField(j,at,"state");
    if((role>=0&&nrString(j,role,candidate.role,sizeof(candidate.role))<0)||(state>=0&&nrString(j,state,candidate.state,sizeof(candidate.state))<0))return 0;
    int cells=nrField(j,at,"cells"),indices=nrField(j,at,"indices"),rect=nrField(j,at,"rect");
    candidate.hasCells=cells>=0;candidate.hasRect=rect>=0;
    if(!list(j,cells,candidate.cells,&candidate.cellCount)||!list(j,indices,candidate.indices,&candidate.indexCount))return 0;
    if(indices>=0&&(cells<0||candidate.indexCount!=candidate.cellCount))return 0;
    if(rect>=0){
        if(!nrAllowed(j,rect,"x y width height"))return 0;
        const char*names[]={"x","y","width","height"};int*targets[]={&candidate.x,&candidate.y,&candidate.width,&candidate.height};
        for(int i=0;i<4;i++){double n;if(!nrNumber(j,nrField(j,rect,names[i]),&n)||!(n>=(i<2?NR_LAYOUT_MIN:0)&&n<=NR_LAYOUT_MAX)||n!=(int)n)return 0;*targets[i]=(int)n;}
    }
    *out=candidate;return 1;
}
void nrDrawCharacterRegions(NrContext*c){
    const State*s=nrView(c);uint64_t count=(uint64_t)s->width*s->height;
    for(int i=0;i<c->characterRegionCount;i++){
        const CharacterRegion*r=&c->characterRegionCache[i];uint32_t owner=0x80000000u|(uint32_t)i;
        if(r->hasCells){
            for(int k=0;k<r->cellCount;k++)if(r->cells[k]<count){size_t at=r->cells[k];c->characterOwners[at]=owner;c->characterIndices[at]=r->indexCount?r->indices[k]:(uint32_t)k;}
        }else{
            int64_t x=r->hasRect?r->x:0,y=r->hasRect?r->y:0,right=r->hasRect?x+r->width:s->width,bottom=r->hasRect?y+r->height:s->height;
            if(x<0)x=0;if(y<0)y=0;if(right>s->width)right=s->width;if(bottom>s->height)bottom=s->height;
            uint32_t index=0;
            for(int64_t yy=y;yy<bottom;yy++)for(int64_t xx=x;xx<right;xx++){
                size_t at=(size_t)yy*s->width+(size_t)xx;c->characterOwners[at]=owner;c->characterIndices[at]=index++;
            }
        }
    }
}
void nrCharacterCellOwner(const NrContext*c,size_t at,const char**role,const char**state,const char**path){
    uint32_t key=c->characterOwners[at];
    *role=c->cells[at].glyph==32?"background":"system-text";*state="inactive";*path="/screen/background";
    if(key&0x80000000u){uint32_t slot=key&0x7fffffffu;if(slot<(uint32_t)c->characterRegionCount){const CharacterRegion*r=&c->characterRegionCache[slot];*role=r->role;*state=r->state;*path=r->path;}return;}
    const State*s=nrView(c);const RegisteredState*owner=nrCharacterSemanticOwner(s,key);
    if(owner){*role=owner->role;*path=owner->path;unsigned flags=nrRegisteredFlags(s,owner);
        *state=flags&16u?"disabled":flags&8u?"pressed":flags&4u?"hover":flags&2u?"selected":flags&1u?"active":"inactive";
    }
}
