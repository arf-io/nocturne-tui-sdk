#include "internal.h"

/* Current C11 geometry and response, shared by every native binding and WASM.
 * The index is derived, pointer-free and verified against authored triangles on
 * restore. No import or collision query executes host code or reads an asset. */
static int reject(NrContext*c,const char*message) {
    size_t n=strlen(message);if(n>255)n=255;
    memcpy(c->error,message,n);c->error[n]=0;return -1;
}
static int flag(int n) {return n==0||n==1;}
static int bounded(double n,double low,double high) {return n>=low&&n<=high;}
static int scalar(const Json*j,int object,const char*key,double*value,double low,double high) {
    int t=nrField(j,object,key);double n;
    if(t<0)return 1;
    if(!nrNumber(j,t,&n)||!bounded(n,low,high))return 0;
    *value=n;return 1;
}
static int integer(const Json*j,int object,const char*key,int*value,int low,int high) {
    int t=nrField(j,object,key);double n;
    if(t<0)return 1;
    if(!nrNumber(j,t,&n)||!bounded(n,low,high)||n!=(int)n)return 0;
    *value=(int)n;return 1;
}
static int boolean(const Json*j,int object,const char*key,int*value) {
    int t=nrField(j,object,key);return t<0||nrBoolean(j,t,value);
}
static int duration(const Json*j,const char*key,uint64_t*value,uint64_t maximum) {
    int t=nrField(j,0,key);double n;
    if(t<0)return 1;
    if(!nrNumber(j,t,&n)||n<0||n>maximum/1000.0||n*1000!=(uint64_t)(n*1000))return 0;
    *value=(uint64_t)(n*1000);return 1;
}
static int vector(const Json*j,int object,const char*key,Vec3*value) {
    int t=nrField(j,object,key);double p[3];
    if(t<0||j->tokens[t].type!=J_ARRAY||j->tokens[t].count!=3)return 0;
    t++;
    for(int k=0;k<3;k++) {
        if(!nrNumber(j,t,&p[k])||!bounded(p[k],-16000,16000))return 0;
        t=j->tokens[t].next;
    }
    *value=nrV(p[0],p[1],p[2]);return 1;
}
static int validPoint(Vec3 p) {
    return bounded(p.x,-32760,32760)&&bounded(p.y,-32760,32760)&&bounded(p.z,-32760,32760);
}
static int validNormal(Vec3 p) {
    return bounded(p.x,-1,1)&&bounded(p.y,-1,1)&&bounded(p.z,-1,1)&&bounded(nrDot(p,p),.999999,1.000001);
}
static int zeroVector(Vec3 p) {return p.x==0&&p.y==0&&p.z==0;}
static double axis(Vec3 p,int dimension) {return dimension==0?p.x:dimension==1?p.y:p.z;}
static Vec3 minimum(Vec3 a,Vec3 b) {return nrV(a.x<b.x?a.x:b.x,a.y<b.y?a.y:b.y,a.z<b.z?a.z:b.z);}
static Vec3 maximum(Vec3 a,Vec3 b) {return nrV(a.x>b.x?a.x:b.x,a.y>b.y?a.y:b.y,a.z>b.z?a.z:b.z);}
static Vec3 center(const Triangle*t) {return nrScale(nrAdd(nrAdd(t->a,t->b),t->c),1.0/3);}

static int buildNode(const State*s,GeometryIndex*out,int first,int count) {
    if(out->nodeCount>=NR_BVH_NODES)return -1;
    int slot=out->nodeCount++;
    CollisionNode*n=&out->nodes[slot];
    n->first=first;n->count=count;n->left=n->right=-1;
    n->minimum=n->maximum=s->mesh[out->order[first]].a;
    Vec3 low=center(&s->mesh[out->order[first]]),high=low;
    for(int i=first;i<first+count;i++) {
        const Triangle*t=&s->mesh[out->order[i]];
        n->minimum=minimum(n->minimum,minimum(t->a,minimum(t->b,t->c)));
        n->maximum=maximum(n->maximum,maximum(t->a,maximum(t->b,t->c)));
        int surface=s->geometry.triangleSurfaces[out->order[i]];
        if(surface>0) {
            double amplitude=0;for(uint32_t w=0;w<s->surfaceWaves[surface-1].count;w++)amplitude+=nrAbs(s->surfaceWaves[surface-1].waves[w][0]);
            Vec3 a=minimum(t->a,minimum(t->b,t->c)),b=maximum(t->a,maximum(t->b,t->c));a.y-=amplitude;b.y+=amplitude;
            n->minimum=minimum(n->minimum,a);n->maximum=maximum(n->maximum,b);
            if(s->surfaceFluids[surface-1].used){Vec3 offset=s->surfaceFluids[surface-1].offset;n->minimum=minimum(n->minimum,nrAdd(a,offset));n->maximum=maximum(n->maximum,nrAdd(b,offset));}
            const SurfaceFluidPose*pose=&s->surfacePoses[surface-1];
            if(pose->used){
                /* Transform all corners of the authored envelope. This also
                 * encloses wave displacement in the rotated authored Y axis.
                 * Flow extrusion extends below its authored top surface. */
                if(s->flowThickness[surface-1].used){
                    Vec3 extrusion=nrScale(s->flowThickness[surface-1].direction,s->flowThickness[surface-1].maxDepth);
                    Vec3 originalA=a,originalB=b;a=minimum(a,nrSub(originalA,extrusion));b=maximum(b,nrSub(originalB,extrusion));
                }
                double corners[24],bounds[6];int corner=0;
                for(int x=0;x<2;x++)for(int y=0;y<2;y++)for(int z=0;z<2;z++){
                    corners[corner++]=x?b.x:a.x;corners[corner++]=y?b.y:a.y;corners[corner++]=z?b.z:a.z;
                }
                if(!nrSurfacePoseBounds(pose->orientation,pose->pivot,s->surfaceFluids[surface-1].offset,nrV(0,0,0),nrV(0,0,0),corners,8,0,bounds))return -1;
                n->minimum=minimum(n->minimum,nrV(bounds[0],bounds[1],bounds[2]));n->maximum=maximum(n->maximum,nrV(bounds[3],bounds[4],bounds[5]));
            }
        }
        Vec3 c=center(t);low=minimum(low,c);high=maximum(high,c);
    }
    if(count<=4)return slot;
    Vec3 span=nrSub(high,low);int dimension=0;
    if(span.y>span.x)dimension=1;
    if(span.z>axis(span,dimension))dimension=2;
    /* Stable insertion sort is bounded at 256 entries. Equal centers use source
     * ordinal; no libc qsort implementation or platform-dependent tie order. */
    for(int i=first+1;i<first+count;i++) {
        int item=out->order[i],j=i;
        double value=axis(center(&s->mesh[item]),dimension);
        while(j>first) {
            int previous=out->order[j-1];double other=axis(center(&s->mesh[previous]),dimension);
            if(other<value||(other==value&&previous<item))break;
            out->order[j]=previous;j--;
        }
        out->order[j]=item;
    }
    n->left=buildNode(s,out,first,count/2);
    n->right=buildNode(s,out,first+count/2,count-count/2);
    if(n->left<0||n->right<0)return -1;
    return slot;
}

/** Derive the complete bounded BVH from authored mesh assignments. */
int nrBuildGeometry(const State*s,GeometryIndex*out) {
    memset(out,0,sizeof(*out));
    if(s->meshCount<0||s->meshCount>NR_MESH)return 0;
    for(int i=0;i<s->meshCount;i++) {
        int id=s->geometry.triangleSurfaces[i];
        if(id<0||id>NR_SURFACES)return 0;
        if(id) {
            if(!s->geometry.surfaces[id-1].used)return 0;
            out->order[out->triangleCount++]=i;
        }
    }
    return !out->triangleCount||buildNode(s,out,0,out->triangleCount)==0;
}

uint32_t nrEmitterColliderMask(const State*s,int slot) {
    uint32_t mask=s->geometry.emitterColliders[slot];
    return mask&NR_COLLIDERS_EXPLICIT?mask&NR_COLLIDER_BITS:1u;
}

int nrConfigureColliders(NrContext*c,State*s,const Json*j,int slot,int required) {
    int object=nrField(j,0,"colliders");
    if(slot<0||slot>=(int)NR_MAX_EMITTERS)return reject(c,"Emitter collider owner does not exist");
    if(object<0) {
        if(required)return reject(c,"Collider selection object required");
        s->geometry.emitterColliders[slot]=0;return 0;
    }
    if(s->schema<NR_STATE_SCHEMA_GENERAL_API)return reject(c,"Collider selection requires the current geometry schema");
    if(!nrAllowed(j,object,"floor surfaces"))return reject(c,"Unknown collider selection setting");
    int floor=0;
    if(!boolean(j,object,"floor",&floor))return reject(c,"Collider floor must be boolean");
    uint32_t mask=floor?1u:0u;int a=nrField(j,object,"surfaces");
    if(a>=0) {
        if(j->tokens[a].type!=J_ARRAY||j->tokens[a].count>NR_SURFACES)return reject(c,"Bounded collider surface array required");
        int t=a+1;
        for(int k=0;k<j->tokens[a].count;k++) {
            double n;
            if(!nrNumber(j,t,&n)||!bounded(n,1,NR_SURFACES)||n!=(int)n)return reject(c,"Invalid collider surface id");
            int id=(int)n;
            if(!s->geometry.surfaces[id-1].used)return reject(c,"Collider surface does not exist");
            if(mask&(1u<<id))return reject(c,"Duplicate collider surface id");
            mask|=1u<<id;t=j->tokens[t].next;
        }
    }
    if(s->emitters[slot].deposit&&!mask)return reject(c,"Deposition requires a selected collider");
    s->geometry.emitterColliders[slot]=mask|NR_COLLIDERS_EXPLICIT;return 0;
}

static int slab(const CollisionNode*n,Vec3 from,Vec3 delta,double end) {
    double low=0,high=end;
    for(int k=0;k<3;k++) {
        double origin=axis(from,k),direction=axis(delta,k);
        double a=axis(n->minimum,k)-1e-9,b=axis(n->maximum,k)+1e-9;
        if(direction==0) {if(origin<a||origin>b)return 0;continue;}
        double x=(a-origin)/direction,y=(b-origin)/direction;
        if(x>y){double q=x;x=y;y=q;}
        if(x>low)low=x;if(y<high)high=y;
        if(low>high)return 0;
    }
    return 1;
}
static int triangleHit(const Triangle*t,Vec3 from,Vec3 delta,double*fraction,Vec3*normal) {
    Vec3 e1=nrSub(t->b,t->a),e2=nrSub(t->c,t->a),p=nrCross(delta,e2);
    double determinant=nrDot(e1,p);
    double scale=nrSqrt(nrDot(e1,e1)*nrDot(e2,e2)*nrDot(delta,delta));
    if(nrAbs(determinant)<=scale*1e-12)return 0;
    Vec3 offset=nrSub(from,t->a);double inverse=1/determinant;
    double u=nrDot(offset,p)*inverse;
    if(u< -1e-10||u>1+1e-10)return 0;
    Vec3 q=nrCross(offset,e1);double v=nrDot(delta,q)*inverse;
    if(v< -1e-10||u+v>1+1e-10)return 0;
    double at=nrDot(e2,q)*inverse;
    if(at<0||at>1)return 0;
    *fraction=at;*normal=nrNormal(nrCross(e1,e2));
    if(nrDot(*normal,delta)>0)*normal=nrScale(*normal,-1);
    return 1;
}

/** Pure earliest swept-center contact. Ties use source order; plane is ordinal -1. */
int nrGeometryHit(const State*s,uint32_t mask,Vec3 from,Vec3 to,GeometryHit*out,uint32_t*tested) {
    Vec3 delta=nrSub(to,from);int found=0;
    *tested=0;memset(out,0,sizeof(*out));out->fraction=2;out->triangleIndex=-1;
    if(nrDot(delta,delta)==0)return 0;
    if((mask&1u)&&s->floor.enabled&&to.y<=s->floor.height) {
        double at=from.y<=s->floor.height?0:(from.y-s->floor.height)/(from.y-to.y);
        out->fraction=nrClamp(at,0,1);out->normal=nrV(0,1,0);found=1;
    }
    const GeometryIndex*index=&s->geometry.index;
    if(index->nodeCount<0||index->nodeCount>NR_BVH_NODES)return 0;
    int stack[NR_BVH_NODES],count=0,visited=0;
    if(index->nodeCount&&(mask&~1u))stack[count++]=0;
    while(count&&visited++<NR_BVH_NODES) {
        int slot=stack[--count];
        if(slot<0||slot>=index->nodeCount)return 0;
        const CollisionNode*n=&index->nodes[slot];
        if(!slab(n,from,delta,out->fraction<1?out->fraction+1e-12:1))continue;
        if(n->left>=0) {
            if(count+2>NR_BVH_NODES)return 0;
            stack[count++]=n->right;stack[count++]=n->left;continue;
        }
        for(int k=n->first;k<n->first+n->count;k++) {
            int triangle=index->order[k],id=s->geometry.triangleSurfaces[triangle];
            if(!(mask&(1u<<id))||!s->geometry.surfaces[id-1].collisionEnabled)continue;
            double at;Vec3 normal;(*tested)++;
            Triangle displaced=s->mesh[triangle];if(nrFlowThicknessTriangleAt(s,triangle,s->timeUs,&displaced)==2)continue;nrDisplaceSurfaceTriangle(s,triangle,&displaced);
            if(!triangleHit(&displaced,from,delta,&at,&normal))continue;
            if(at<out->fraction-1e-12||(nrAbs(at-out->fraction)<=1e-12&&triangle<out->triangleIndex)) {
                out->fraction=at;out->normal=normal;out->triangleIndex=triangle;out->surfaceId=id;found=1;
            }
        }
    }
    if(found) {
        out->position=nrAdd(from,nrScale(delta,out->fraction));
        if(!out->surfaceId)out->position.y=s->floor.height;
        else out->surfaceVelocity=nrSurfaceTriangleVelocity(s,out->triangleIndex,out->position);
    }
    return found;
}

int nrGeometryHitTimed(const State*s,uint32_t mask,Vec3 from,Vec3 to,double start,double duration,GeometryHit*out,uint32_t*tested) {
    uint32_t staticMask=mask;
    for(int id=1;id<=NR_SURFACES;id++)if(s->surfaceWaves[id-1].count||s->flowThickness[id-1].used||s->surfaceFluids[id-1].used)staticMask&=~(1u<<id);
    int found=nrGeometryHit(s,staticMask,from,to,out,tested);
    if(duration<=0)return found;
    for(int index=0;index<s->meshCount;index++) {
        int id=s->geometry.triangleSurfaces[index];
        if(id<=0||!(mask&(1u<<id))||(!s->surfaceWaves[id-1].count&&!s->flowThickness[id-1].used&&!s->surfaceFluids[id-1].used)||!s->geometry.surfaces[id-1].collisionEnabled)continue;
        GeometryHit hit;(*tested)++;
        if(s->surfacePoses[id-1].used){
            int result=nrRotatingSurfaceHit(s,index,from,to,start,duration,found?out->fraction:1,&hit);
            if(result<0)return -1;
            if(result&&(!found||hit.fraction<out->fraction-1e-12||(nrAbs(hit.fraction-out->fraction)<=1e-12&&index<out->triangleIndex))){*out=hit;found=1;}
            continue;
        }
        const SurfaceFluid*f=&s->surfaceFluids[id-1];Vec3 startOffset=nrV(0,0,0),endOffset=nrV(0,0,0);
        Vec3 fluidVelocity=f->used==1?f->velocity:nrV(0,0,0);
        if(f->used){startOffset=nrAdd(f->offset,nrScale(fluidVelocity,start-s->timeUs/1000000.0));endOffset=nrAdd(startOffset,nrScale(fluidVelocity,duration));}
        Vec3 localFrom=nrSub(from,startOffset),localTo=nrSub(to,endOffset);
        int result=s->flowThickness[id-1].used?nrFlowThicknessHit(s,index,localFrom,localTo,start,duration,found?out->fraction:1,&hit):nrWaveTriangleHit(s,index,localFrom,localTo,start,duration,found?out->fraction:1,&hit);
        if(result>0&&f->used){hit.position=nrAdd(hit.position,nrAdd(startOffset,nrScale(nrSub(endOffset,startOffset),hit.fraction)));hit.surfaceVelocity=nrAdd(hit.surfaceVelocity,fluidVelocity);}
        if(result<0)return -1;
        if(result&&( !found||hit.fraction<out->fraction-1e-12||(nrAbs(hit.fraction-out->fraction)<=1e-12&&index<out->triangleIndex))) {*out=hit;found=1;}
    }
    return found;
}

void nrSurfaceBasis(Vec3 normal,Vec3*tangent,Vec3*bitangent) {
    Vec3 reference=nrAbs(normal.y)>.9?nrV(0,0,1):nrV(0,1,0);
    *tangent=nrNormal(nrCross(normal,reference));
    *bitangent=nrNormal(nrCross(normal,*tangent));
}

void nrSurfaceTick(State*s) {
    for(int i=0;i<NR_SURFACES;i++)if(s->geometry.surfaces[i].used) {
        Surface*q=&s->geometry.surfaces[i];
        q->wetness=nrClamp(q->wetness-(q->evaporation+q->thermalEvaporation*q->heat)/120,0,1);
        q->heat=nrClamp(q->heat-q->cooling/120,0,1);
    }
}

void nrSurfaceImpact(State*s,int id,const Particle*p,int algorithm) {
    if(!id)return;
    Surface*q=&s->geometry.surfaces[id-1];q->impacts++;
    if(algorithm==1)q->wetness=nrClamp(q->wetness+p->size*q->wetnessGain,0,1);
    if(algorithm==3)q->heat=nrClamp(q->heat+p->size*q->heatGain*p->heat,0,1);
}

int nrSurfaceTriangle(const State*s,int index,Triangle*out) {
    *out=s->mesh[index];if(nrFlowThicknessTriangleAt(s,index,s->timeUs,out)==2)return 0;nrDisplaceSurfaceTriangle(s,index,out);int id=s->geometry.triangleSurfaces[index];
    if(!id)return 1;
    const Surface*q=&s->geometry.surfaces[id-1];if(!q->renderVisible)return 0;
    out->color=nrMix(out->color,0,q->wetness*q->wetnessDarkening);
    out->color=nrMix(out->color,q->heatColor,q->heat*q->heatTintStrength);
    if(s->foam.settings[id-1].used)out->color=nrMix(out->color,s->foam.settings[id-1].color,s->foam.cells[index].density);
    return 1;
}

static int validContact(const State*s,const SurfaceContact*c) {
    if(!flag(c->used))return 0;
    /* Floor deposits consume surfaceId even when no explicit mesh contact is
     * stored. Inactive records must therefore remain canonical zero payloads. */
    if(!c->used)return !c->surfaceId&&!c->triangleIndex&&zeroVector(c->normal);
    if(c->surfaceId<0||c->surfaceId>NR_SURFACES||!validNormal(c->normal))return 0;
    if(!c->surfaceId)return c->triangleIndex==-1;
    return s->geometry.surfaces[c->surfaceId-1].used&&c->triangleIndex>=0&&c->triangleIndex<NR_MESH;
}

/** Validate every extension reference before traversal, then compare derived BVH. */
int nrValidGeometry(const State*s) {
    const GeometryState*g=&s->geometry;
    if(s->schema<NR_STATE_SCHEMA_GENERAL_API&&s->schema!=NR_STATE_SCHEMA_THERMAL_LINK&&s->schema!=NR_STATE_SCHEMA_THERMAL_TRANSFER&&s->schema!=NR_STATE_SCHEMA_THERMAL&&s->schema!=NR_STATE_SCHEMA_WATER_REEMIT&&s->schema!=NR_STATE_SCHEMA_WATER_LINK&&s->schema!=NR_STATE_SCHEMA_WATER_TRANSFER&&s->schema!=NR_STATE_SCHEMA_SURFACE_WATER&&s->schema!=NR_STATE_SCHEMA_SPRAY_PARTICLES&&s->schema!=NR_STATE_SCHEMA_FLOW_SPRAY&&s->schema!=NR_STATE_SCHEMA_FLOW_SINK&&s->schema!=NR_STATE_SCHEMA_FLOW_SURFACE&&s->schema!=NR_STATE_SCHEMA_FLOW&&s->schema!=NR_STATE_SCHEMA_REPEAT_EDIT&&s->schema!=NR_STATE_SCHEMA_EDITOR_REDO&&s->schema!=NR_STATE_SCHEMA_NAMED_REGISTERS&&s->schema!=NR_STATE_SCHEMA_VIM_REGISTER&&s->schema!=NR_STATE_SCHEMA_VIM_OPERATOR&&s->schema!=NR_STATE_SCHEMA_VIM_COUNT&&s->schema!=NR_STATE_SCHEMA_PATH_ACTORS&&s->schema!=NR_STATE_SCHEMA_FOAM&&s->schema!=NR_STATE_SCHEMA_FLOAT_BODIES&&s->schema!=NR_STATE_SCHEMA_SURFACE_WAVES&&s->schema!=NR_STATE_SCHEMA_PARTICLE_MOTION&&s->schema!=NR_STATE_SCHEMA_BIRTH_FRAME&&s->schema!=NR_STATE_SCHEMA_GEOMETRY) {
        const unsigned char*p=(const unsigned char*)g;
        for(size_t i=0;i<sizeof(*g);i++)if(p[i])return 0;
        return 1;
    }
    if(g->contactBudgetExhausted>100000000000000ull||g->collisionQueries>100000000000000ull||g->triangleTests>100000000000000ull)return 0;
    for(int i=0;i<NR_SURFACES;i++) {
        const Surface*q=&g->surfaces[i];if(!flag(q->used))return 0;if(!q->used)continue;
        if(!flag(q->collisionEnabled)||!flag(q->renderVisible)||!flag(q->overflow)||
           q->maxIndividual<0||q->maxIndividual>NR_DEPOSITS||q->maxTiles<0||q->maxTiles>NR_TILES||
           (q->overflow&&!q->maxTiles)||!bounded(q->restitution,0,1)||!bounded(q->friction,0,1)||
           !bounded(q->settleSpeed,0,30)||!bounded(q->reentrain,0,256)||q->retentionUs>86400000000ull||
           q->fadeUs>60000000||(q->retentionUs&&q->fadeUs>q->retentionUs)||
           !bounded(q->wetnessGain,0,10)||!bounded(q->evaporation,0,10)||!bounded(q->heatGain,0,10)||
           !bounded(q->cooling,0,10)||!bounded(q->thermalEvaporation,0,10)||
           !bounded(q->wetnessDarkening,0,1)||!bounded(q->heatTintStrength,0,1)||q->heatColor>0xffffffu||
           !bounded(q->wetness,0,1)||!bounded(q->heat,0,1)||
           q->impacts>100000000000000ull||q->rejectedDeposits>100000000000000ull)return 0;
    }
    for(int i=0;i<(int)NR_MAX_EMITTERS;i++) {
        uint32_t mask=g->emitterColliders[i];
        if(mask&&(!(mask&NR_COLLIDERS_EXPLICIT)||(mask&~(NR_COLLIDERS_EXPLICIT|NR_COLLIDER_BITS))||!s->emitters[i].used))return 0;
        if(mask&NR_COLLIDERS_EXPLICIT) {
            if(s->emitters[i].deposit&&!(mask&NR_COLLIDER_BITS))return 0;
            for(int id=1;id<=NR_SURFACES;id++)if((mask&(1u<<id))&&!g->surfaces[id-1].used)return 0;
        }
    }
    for(int i=0;i<(int)NR_MAX_PARTICLES;i++)if(!validContact(s,&g->particleContacts[i]))return 0;
    for(int i=0;i<NR_DEPOSITS;i++)if(!validContact(s,&g->depositContacts[i]))return 0;
    for(int i=0;i<NR_TILES;i++) {
        const SurfaceTile*t=&g->tileSurfaces[i];
        if(t->surfaceId<0||t->surfaceId>NR_SURFACES)return 0;
        if(!t->surfaceId) {
            if(t->triangleIndex||t->meshGeneration||!zeroVector(t->normal)||
               !zeroVector(t->a)||!zeroVector(t->b)||!zeroVector(t->c))return 0;
            continue;
        }
        /* Expiration may retain captured named geometry in an inactive tile.
         * Validate that payload as well; only zero-owner floor tiles are empty. */
        if(!g->surfaces[t->surfaceId-1].used||t->triangleIndex<0||t->triangleIndex>=NR_MESH||
           !t->meshGeneration||t->meshGeneration>g->meshGeneration||!validNormal(t->normal)||
           !validPoint(t->a)||!validPoint(t->b)||!validPoint(t->c))return 0;
    }
    for(int i=s->meshCount;i<NR_MESH;i++)if(g->triangleSurfaces[i])return 0;
    GeometryIndex expected;
    return nrBuildGeometry(s,&expected)&&!memcmp(&expected,&g->index,sizeof(expected));
}

static int surfaceId(NrContext*c,const State*s,const Json*j,int requiredExisting) {
    int id=0;
    if(!integer(j,0,"id",&id,1,NR_SURFACES)||!id)return reject(c,"Surface id must be 1..16");
    if(requiredExisting&&!s->geometry.surfaces[id-1].used)return reject(c,"Surface does not exist");
    return id;
}

/* All geometry authoring shares mesh generations and foam-cell lifetime. */
static int finishMesh(NrContext*c,State*s,int append,int base,const char*failure){
    if(append&&s->meshCount==base)return 0;
    if(s->geometry.meshGeneration==0xffffffffu)return reject(c,"Mesh generation capacity reached");
    nrHeatMeshChanged(s,append);
    nrSurfaceWaterMeshChanged(s,append,base);
    nrThermalMeshChanged(s,append,base);
    if(append)for(int i=0;i<NR_TILES;i++)if(s->tiles[i].used&&s->geometry.tileSurfaces[i].surfaceId&&s->geometry.tileSurfaces[i].meshGeneration==s->geometry.meshGeneration)s->geometry.tileSurfaces[i].meshGeneration++;
    s->geometry.meshGeneration++;
    if(append){memset(&s->foamTransfers[base],0,(size_t)(s->meshCount-base)*sizeof(s->foamTransfers[0]));memset(&s->foam.cells[base],0,(size_t)(s->meshCount-base)*sizeof(FoamCell));s->foam.meshGeneration=s->geometry.meshGeneration;}else nrFoamMeshChanged(s);
    return nrValidFoamTransport(s)&&nrBuildGeometry(s,&s->geometry.index)?0:reject(c,failure);
}

int nrFinishFlowThicknessMesh(NrContext*c,State*s,int append,int base){return finishMesh(c,s,append,base,"Flow thickness collision index");}

/* Inline model documents are data only. The caller owns any file/network asset
 * resolution. Imported static materials become canonical triangle RGB/alpha. */
static int modelVector(const Json*j,int t,Vec3*out,double low,double high) {
    double v[3];
    if(t<0||j->tokens[t].type!=J_ARRAY||j->tokens[t].count!=3)return 0;
    t++;
    for(int k=0;k<3;k++) {if(!nrNumber(j,t,&v[k])||!bounded(v[k],low,high))return 0;t=j->tokens[t].next;}
    *out=nrV(v[0],v[1],v[2]);return 1;
}
static Vec3 modelRotate(Vec3 v,Vec3 angles) {
    double c=nrCos(angles.x),s=nrSin(angles.x);v=nrV(v.x,c*v.y-s*v.z,s*v.y+c*v.z);
    c=nrCos(angles.y);s=nrSin(angles.y);v=nrV(c*v.x+s*v.z,v.y,-s*v.x+c*v.z);
    c=nrCos(angles.z);s=nrSin(angles.z);return nrV(c*v.x-s*v.y,s*v.x+c*v.y,v.z);
}
static int importModel(NrContext*c,State*s,const Json*j) {
    if(!nrAllowed(j,0,"op schema units coordinates vertices materials triangles transform sampling append"))return reject(c,"Unknown model field");
    if(!nrEqual(j,nrField(j,0,"schema"),"nocturne.model/v1")||!nrEqual(j,nrField(j,0,"coordinates"),"right-handed-y-up"))return reject(c,"Explicit model schema and coordinates required");
    int append=0;if(!boolean(j,0,"append",&append))return reject(c,"Model append must be boolean");int base=append?s->meshCount:0;
    double units=1;int u=nrField(j,0,"units");
    if(nrEqual(j,u,"centimeters"))units=.01;
    else if(nrEqual(j,u,"millimeters"))units=.001;
    else if(!nrEqual(j,u,"meters"))return reject(c,"Explicit model units required");
    Vec3 position=nrV(0,0,0),orientation=nrV(0,0,0),scale=nrV(1,1,1);
    int transform=nrField(j,0,"transform");
    if(transform>=0) {
        if(j->tokens[transform].type!=J_OBJECT||!nrAllowed(j,transform,"position orientation scale"))return reject(c,"Invalid model transform");
        int p=nrField(j,transform,"position"),o=nrField(j,transform,"orientation"),z=nrField(j,transform,"scale");
        if((p>=0&&!modelVector(j,p,&position,-16000,16000))||(o>=0&&!modelVector(j,o,&orientation,-3600,3600))||(z>=0&&!modelVector(j,z,&scale,.000001,1000)))return reject(c,"Model transform bounds");
    }
    int vertices=nrField(j,0,"vertices"),materials=nrField(j,0,"materials"),triangles=nrField(j,0,"triangles");
    if(vertices<0||j->tokens[vertices].type!=J_ARRAY||j->tokens[vertices].count<3||j->tokens[vertices].count>1024||materials<0||j->tokens[materials].type!=J_ARRAY||j->tokens[materials].count<1||j->tokens[materials].count>32||triangles<0||j->tokens[triangles].type!=J_ARRAY||j->tokens[triangles].count>NR_MESH)return reject(c,"Model pool capacity");
    Vec3 points[1024];uint32_t colors[32];double alphas[32];int t=vertices+1;
    for(int k=0;k<j->tokens[vertices].count;k++) {
        Vec3 p;if(!modelVector(j,t,&p,-16000,16000))return reject(c,"Model vertex bounds");
        p=nrV(p.x*scale.x*units,p.y*scale.y*units,p.z*scale.z*units);
        p=nrAdd(position,modelRotate(p,orientation));
        if(!bounded(p.x,-16000,16000)||!bounded(p.y,-16000,16000)||!bounded(p.z,-16000,16000))return reject(c,"Transformed model vertex bounds");
        points[k]=p;t=j->tokens[t].next;
    }
    t=materials+1;
    for(int k=0;k<j->tokens[materials].count;k++) {
        int color=0;double alpha=1;
        if(j->tokens[t].type!=J_OBJECT||!nrAllowed(j,t,"color alpha")||nrField(j,t,"color")<0||!integer(j,t,"color",&color,0,0xffffff)||!scalar(j,t,"alpha",&alpha,0,1))return reject(c,"Model material validation");
        colors[k]=(uint32_t)color;alphas[k]=alpha;t=j->tokens[t].next;
    }
    int sampling=nrField(j,0,"sampling");
    if(sampling>=0) {
        if(nrEqual(j,sampling,"cell"))s->meshSampling=0;
        else if(nrEqual(j,sampling,"half"))s->meshSampling=1;
        else if(nrEqual(j,sampling,"braille"))s->meshSampling=2;
        else if(nrEqual(j,sampling,"hybrid"))s->meshSampling=3;
        else return reject(c,"Invalid model sampling");
    }
    int count=j->tokens[triangles].count;if(base+count>NR_MESH)return reject(c,"Combined model triangle capacity");
    s->meshCount=base+count;t=triangles+1;
    if(!append)memset(s->geometry.triangleSurfaces,0,sizeof(s->geometry.triangleSurfaces));
    for(int k=0;k<count;k++) {
        int material=0,surface=0,index[3],a=nrField(j,t,"indices");
        if(j->tokens[t].type!=J_OBJECT||!nrAllowed(j,t,"indices material surfaceId")||a<0||j->tokens[a].type!=J_ARRAY||j->tokens[a].count!=3||nrField(j,t,"material")<0||!integer(j,t,"material",&material,0,j->tokens[materials].count-1)||!integer(j,t,"surfaceId",&surface,0,NR_SURFACES)||(surface&&!s->geometry.surfaces[surface-1].used))return reject(c,"Model triangle references");
        int ix=a+1;
        for(int n=0;n<3;n++) {double v;if(!nrNumber(j,ix,&v)||!bounded(v,0,j->tokens[vertices].count-1)||v!=(int)v)return reject(c,"Model vertex reference");index[n]=(int)v;ix=j->tokens[ix].next;}
        Triangle*q=&s->mesh[base+k];memset(q,0,sizeof(*q));q->a=points[index[0]];q->b=points[index[1]];q->c=points[index[2]];q->color=colors[material];q->alpha=alphas[material];
        Vec3 normal=nrCross(nrSub(q->b,q->a),nrSub(q->c,q->a));
        if(nrDot(normal,normal)<=1e-16)return reject(c,"Degenerate imported triangle");
        s->geometry.triangleSurfaces[base+k]=surface;t=j->tokens[t].next;
    }
    return finishMesh(c,s,append,base,"Imported collision index");
}

/* Compile path data directly to canonical mesh; all hosts share these joins. */
static Vec3 catmullPoint(Vec3 a,Vec3 b,Vec3 c,Vec3 d,double t){
    Vec3 first=nrScale(b,2),second=nrScale(nrSub(c,a),t);
    Vec3 third=nrScale(nrAdd(nrSub(nrScale(a,2),nrScale(b,5)),nrSub(nrScale(c,4),d)),t*t);
    Vec3 fourth=nrScale(nrAdd(nrSub(nrScale(b,3),a),nrSub(d,nrScale(c,3))),t*t*t);
    return nrScale(nrAdd(nrAdd(first,second),nrAdd(third,fourth)),.5);
}
static int ribbon(NrContext*c,State*s,const Json*j) {
    if(!nrAllowed(j,0,"op points width widths up closed miterLimit color alpha surfaceId sampling append interpolation subdivisions"))return reject(c,"Unknown ribbon setting");
    int a=nrField(j,0,"points"),closed=0,color=0x809caa,surface=0;double width=1,alpha=1,limit=4;Vec3 up=nrV(0,1,0);
    if(a<0||j->tokens[a].type!=J_ARRAY||!boolean(j,0,"closed",&closed)||!scalar(j,0,"width",&width,.000001,1000)||!scalar(j,0,"alpha",&alpha,0,1)||!scalar(j,0,"miterLimit",&limit,1,100)||!integer(j,0,"color",&color,0,0xffffff)||!integer(j,0,"surfaceId",&surface,0,NR_SURFACES)||(surface&&!s->geometry.surfaces[surface-1].used))return reject(c,"Invalid ribbon parameters");
    int append=0;if(!boolean(j,0,"append",&append))return reject(c,"Ribbon append must be boolean");
    int base=append?s->meshCount:0;
    int n=j->tokens[a].count,segments=n-1+closed;
    if(n<(closed?3:2)||segments>NR_MESH/2||base+segments*2>NR_MESH)return reject(c,"Ribbon point capacity");
    int u=nrField(j,0,"up");if(u>=0&&!modelVector(j,u,&up,-16000,16000))return reject(c,"Invalid ribbon up");
    if(nrDot(up,up)<1e-16)return reject(c,"Ribbon up cannot be zero");up=nrNormal(up);
    Vec3 points[129],sides[128],left[129],right[129];double widths[129];int t=a+1;
    for(int i=0;i<n;i++){if(!modelVector(j,t,&points[i],-16000,16000))return reject(c,"Ribbon point bounds");widths[i]=width;t=j->tokens[t].next;}
    int w=nrField(j,0,"widths");if(w>=0){
        if(j->tokens[w].type!=J_ARRAY||j->tokens[w].count!=n||nrField(j,0,"width")>=0)return reject(c,"Ribbon widths must match points and exclude width");
        t=w+1;for(int i=0;i<n;i++){if(!nrNumber(j,t,&widths[i])||!bounded(widths[i],.000001,1000))return reject(c,"Ribbon width bounds");t=j->tokens[t].next;}
    }
    int interpolation=nrField(j,0,"interpolation"),curved=0,subdivisions=8;
    if(interpolation>=0){if(nrEqual(j,interpolation,"catmull-rom"))curved=1;else if(!nrEqual(j,interpolation,"linear"))return reject(c,"Unknown ribbon interpolation");}
    if(!integer(j,0,"subdivisions",&subdivisions,1,16)||(!curved&&nrField(j,0,"subdivisions")>=0))return reject(c,"Ribbon subdivisions require catmull-rom");
    if(curved){
        int sampledSegments=segments*subdivisions,sampledCount=sampledSegments+(closed?0:1);
        if(sampledSegments>NR_MESH/2||base+sampledSegments*2>NR_MESH)return reject(c,"Spline ribbon capacity");
        Vec3 sampled[129];double sampledWidths[129];
        for(int i=0;i<segments;i++)for(int k=0;k<subdivisions;k++){
            int previous=closed?(i+n-1)%n:(i?i-1:0),next=(i+1)%n,after=closed?(i+2)%n:(i+2<n?i+2:n-1),index=i*subdivisions+k;double fraction=(double)k/subdivisions;
            sampled[index]=k?catmullPoint(points[previous],points[i],points[next],points[after],fraction):points[i];
            sampledWidths[index]=widths[i]+(widths[next]-widths[i])*fraction;
            if(!bounded(sampled[index].x,-16000,16000)||!bounded(sampled[index].y,-16000,16000)||!bounded(sampled[index].z,-16000,16000))return reject(c,"Spline sample bounds");
        }
        if(!closed){sampled[sampledCount-1]=points[n-1];sampledWidths[sampledCount-1]=widths[n-1];}
        n=sampledCount;segments=sampledSegments;memcpy(points,sampled,(size_t)n*sizeof(Vec3));memcpy(widths,sampledWidths,(size_t)n*sizeof(double));
    }
    for(int i=0;i<segments;i++){
        Vec3 tangent=nrSub(points[(i+1)%n],points[i]),side=nrCross(up,tangent);
        if(nrDot(side,side)<1e-16)return reject(c,"Ribbon segment is zero or parallel to up");sides[i]=nrNormal(side);
    }
    for(int i=0;i<n;i++){
        Vec3 side;double factor=1;
        if(!closed&&i==0)side=sides[0];else if(!closed&&i==n-1)side=sides[segments-1];else{
            Vec3 incoming=sides[(i+segments-1)%segments],outgoing=sides[i%segments],sum=nrAdd(incoming,outgoing);
            if(nrDot(sum,sum)<1e-16)return reject(c,"Ribbon reverses direction");side=nrNormal(sum);double alignment=nrDot(side,outgoing);
            if(alignment<=0||1/alignment>limit)return reject(c,"Ribbon miter exceeds limit");factor=1/alignment;
        }
        Vec3 offset=nrScale(side,widths[i]*.5*factor);left[i]=nrAdd(points[i],offset);right[i]=nrSub(points[i],offset);
        if(!bounded(left[i].x,-16000,16000)||!bounded(left[i].y,-16000,16000)||!bounded(left[i].z,-16000,16000)||!bounded(right[i].x,-16000,16000)||!bounded(right[i].y,-16000,16000)||!bounded(right[i].z,-16000,16000))return reject(c,"Ribbon edge bounds");
    }
    int sampling=nrField(j,0,"sampling");if(sampling>=0){
        if(nrEqual(j,sampling,"cell"))s->meshSampling=0;else if(nrEqual(j,sampling,"half"))s->meshSampling=1;else if(nrEqual(j,sampling,"braille"))s->meshSampling=2;else if(nrEqual(j,sampling,"hybrid"))s->meshSampling=3;else return reject(c,"Invalid ribbon sampling");
    }
    if(!append)memset(s->geometry.triangleSurfaces,0,sizeof(s->geometry.triangleSurfaces));s->meshCount=base+segments*2;
    for(int i=0;i<segments;i++){
        int next=(i+1)%n;Triangle*q=&s->mesh[base+i*2];memset(q,0,2*sizeof(*q));
        q[0].a=left[i];q[0].b=right[i];q[0].c=left[next];q[1].a=right[i];q[1].b=right[next];q[1].c=left[next];
        for(int k=0;k<2;k++){Vec3 normal=nrCross(nrSub(q[k].b,q[k].a),nrSub(q[k].c,q[k].a));if(nrDot(normal,normal)<=1e-16)return reject(c,"Degenerate ribbon triangle");q[k].color=color;q[k].alpha=alpha;s->geometry.triangleSurfaces[base+i*2+k]=surface;}
    }
    return finishMesh(c,s,append,base,"Ribbon collision index");
}

/* Native assembly compiles to ordinary mesh and flow bindings; no private engine. */
static int waterfall(NrContext*c,State*s,const Json*j){
    if(!nrAllowed(j,0,"op channelSurfaceId sheetSurfaceId flowId channelStage sheetStage referenceFlux drop color alpha"))return reject(c,"Unknown waterfall field");
    int channel=0,sheet=0,flowId=0,color=0x809caa;double drop=0,reference=0,alpha=1;char channelName[32],sheetName[32];
    if(!integer(j,0,"channelSurfaceId",&channel,1,NR_SURFACES)||!integer(j,0,"sheetSurfaceId",&sheet,1,NR_SURFACES)||!channel||!sheet||channel==sheet||!s->geometry.surfaces[channel-1].used||!s->geometry.surfaces[sheet-1].used||!integer(j,0,"flowId",&flowId,1,65535)||!flowId||!scalar(j,0,"drop",&drop,.000001,16000)||!drop||!scalar(j,0,"referenceFlux",&reference,.000001,1000000)||!reference||!integer(j,0,"color",&color,0,0xffffff)||!scalar(j,0,"alpha",&alpha,0,1)||!nrString(j,nrField(j,0,"channelStage"),channelName,32)||!nrString(j,nrField(j,0,"sheetStage"),sheetName,32))return reject(c,"Invalid waterfall parameters");
    int flow=-1,cs=-1,ss=-1;for(int i=0;i<8;i++)if(s->flows[i].used&&s->flows[i].id==(uint32_t)flowId)flow=i;
    if(flow<0)return reject(c,"Unknown waterfall flow");for(int k=0;k<s->flows[flow].count;k++){if(!strcmp(channelName,s->flows[flow].stages[k].name))cs=k;if(!strcmp(sheetName,s->flows[flow].stages[k].name))ss=k;}
    if(cs<0||ss<=cs)return reject(c,"Waterfall stages must follow channel then sheet");
    int end=-1;for(int i=0;i<s->meshCount;i++)if(s->geometry.triangleSurfaces[i]==channel)end=i;
    if(end<1||s->geometry.triangleSurfaces[end-1]!=channel||s->meshCount+2>NR_MESH)return reject(c,"Waterfall needs a channel ribbon lip and mesh capacity");
    Triangle a=s->mesh[end-1],b=s->mesh[end];
    if(nrDot(nrSub(a.b,b.a),nrSub(a.b,b.a))||nrDot(nrSub(a.c,b.c),nrSub(a.c,b.c)))return reject(c,"Channel end is not a shared ribbon pair");
    Vec3 left=a.c,right=b.b,down=nrV(0,-drop,0),bottomLeft=nrAdd(left,down),bottomRight=nrAdd(right,down);
    Vec3 normal=nrCross(nrSub(right,left),down);if(nrDot(normal,normal)<=1e-16||bottomLeft.y< -16000||bottomRight.y< -16000)return reject(c,"Invalid falling sheet geometry");
    int base=s->meshCount;s->mesh[base]=(Triangle){left,right,bottomLeft,(uint32_t)color,alpha};s->mesh[base+1]=(Triangle){right,bottomRight,bottomLeft,(uint32_t)color,alpha};
    s->geometry.triangleSurfaces[base]=s->geometry.triangleSurfaces[base+1]=sheet;s->meshCount+=2;
    s->flowSurfaces[channel-1].flowId=s->flowSurfaces[sheet-1].flowId=(uint32_t)flowId;
    s->flowSurfaces[channel-1].stage=cs;s->flowSurfaces[sheet-1].stage=ss;s->flowSurfaces[channel-1].referenceFlux=s->flowSurfaces[sheet-1].referenceFlux=reference;
    return finishMesh(c,s,1,base,"Waterfall collision index");
}

static Vec3 subdivisionPoint(const Triangle*t,int i,int j,int n){
    /* Reuse exact parent corners. Integer weights make reversed shared edges
     * evaluate the same two products; one lattice owns all internal vertices. */
    if(!i&&!j)return t->a;if(i==n)return t->b;if(j==n)return t->c;
    return nrScale(nrAdd(nrScale(t->a,n-i-j),nrAdd(nrScale(t->b,i),nrScale(t->c,j))),1.0/n);
}
static int appendSubdivision(State*s,const Triangle*source,int surface,int n){
    if(n==1){s->mesh[s->meshCount]=*source;s->geometry.triangleSurfaces[s->meshCount++]=surface;return 1;}
    Vec3 lattice[17][17];
    for(int i=0;i<=n;i++)for(int j=0;j<=n-i;j++)lattice[i][j]=subdivisionPoint(source,i,j,n);
    for(int i=0;i<n;i++)for(int j=0;j<n-i;j++)for(int inverted=0;inverted<(i+j<n-1?2:1);inverted++){
        Triangle child=*source;
        if(!inverted){child.a=lattice[i][j];child.b=lattice[i+1][j];child.c=lattice[i][j+1];}
        else{child.a=lattice[i+1][j];child.b=lattice[i+1][j+1];child.c=lattice[i][j+1];}
        Vec3 normal=nrCross(nrSub(child.b,child.a),nrSub(child.c,child.a));
        if(nrDot(normal,normal)<=1e-16)return 0;
        s->mesh[s->meshCount]=child;s->geometry.triangleSurfaces[s->meshCount++]=surface;
    }return 1;
}
int nrGeometryCommand(NrContext*c,State*s,const Json*j) {
    if(!nrFlowThicknessGeometryEditAllowed(s,j))return reject(c,"Remove owned flow thickness before replacing geometry");
    int op=nrField(j,0,"op");
    if(nrEqual(j,op,"waterfall"))return waterfall(c,s,j);
    if(nrEqual(j,op,"surface")) {
        if(s->schema<NR_STATE_SCHEMA_GENERAL_API)return reject(c,"Surface requires the current geometry schema");
        if(!nrAllowed(j,0,"op id collisionEnabled renderVisible restitution friction settleSpeed reentrainWindSpeed maxIndividual maxTiles overflow retentionMs fadeMs wetnessGain evaporation heatGain cooling thermalEvaporation wetnessDarkening heatColor heatTintStrength"))return reject(c,"Unknown surface setting");
        int id=surfaceId(c,s,j,0);if(id<0)return -1;
        Surface*q=&s->geometry.surfaces[id-1];
        if(!q->used) {
            memset(q,0,sizeof(*q));q->used=1;q->collisionEnabled=q->renderVisible=1;
            q->restitution=.18;q->friction=.65;q->settleSpeed=.6;q->reentrain=6;
            q->maxIndividual=256;q->maxTiles=128;q->overflow=1;
            q->wetnessGain=.03;q->evaporation=.04;q->heatGain=.02;q->cooling=.1;
            q->thermalEvaporation=.25;q->wetnessDarkening=.35;q->heatColor=0xff8844;q->heatTintStrength=.4;
        }
        int color=(int)q->heatColor;
        if(!boolean(j,0,"collisionEnabled",&q->collisionEnabled)||!boolean(j,0,"renderVisible",&q->renderVisible)||
           !integer(j,0,"maxIndividual",&q->maxIndividual,0,NR_DEPOSITS)||!integer(j,0,"maxTiles",&q->maxTiles,0,NR_TILES)||
           !integer(j,0,"heatColor",&color,0,0xffffff)||
           !scalar(j,0,"restitution",&q->restitution,0,1)||!scalar(j,0,"friction",&q->friction,0,1)||
           !scalar(j,0,"settleSpeed",&q->settleSpeed,0,30)||!scalar(j,0,"reentrainWindSpeed",&q->reentrain,0,256)||
           !scalar(j,0,"wetnessGain",&q->wetnessGain,0,10)||!scalar(j,0,"evaporation",&q->evaporation,0,10)||
           !scalar(j,0,"heatGain",&q->heatGain,0,10)||!scalar(j,0,"cooling",&q->cooling,0,10)||
           !scalar(j,0,"thermalEvaporation",&q->thermalEvaporation,0,10)||
           !scalar(j,0,"wetnessDarkening",&q->wetnessDarkening,0,1)||!scalar(j,0,"heatTintStrength",&q->heatTintStrength,0,1)||
           !duration(j,"retentionMs",&q->retentionUs,86400000000ull)||!duration(j,"fadeMs",&q->fadeUs,60000000))return reject(c,"Invalid bounded surface setting");
        q->heatColor=(uint32_t)color;int overflow=nrField(j,0,"overflow");
        if(overflow>=0) {
            if(nrEqual(j,overflow,"reject-new"))q->overflow=0;
            else if(nrEqual(j,overflow,"merge-to-field"))q->overflow=1;
            else return reject(c,"Unknown surface overflow policy");
        }
        if(q->overflow&&!q->maxTiles)return reject(c,"Surface aggregation requires a bounded nonempty tile destination");
        if(q->retentionUs&&q->fadeUs>q->retentionUs)return reject(c,"Surface fade must fit retention");
        return 0;
    }
    if(nrEqual(j,op,"clear-surface")) {
        if(s->schema<NR_STATE_SCHEMA_GENERAL_API||!nrAllowed(j,0,"op id scope"))return reject(c,"Invalid surface clear");
        int id=surfaceId(c,s,j,1);if(id<0)return -1;
        int scope=nrField(j,0,"scope"),response=nrEqual(j,scope,"response"),deposits=nrEqual(j,scope,"deposits");
        if(nrEqual(j,scope,"all"))response=deposits=1;
        if(!response&&!deposits)return reject(c,"Surface clear scope required");
        if(response)s->geometry.surfaces[id-1].wetness=s->geometry.surfaces[id-1].heat=0;
        if(deposits) {
            for(int i=0;i<NR_DEPOSITS;i++)if(s->geometry.depositContacts[i].surfaceId==id) {
                nrHeatRelease(s,1,i);memset(&s->deposits[i],0,sizeof(Deposit));memset(&s->geometry.depositContacts[i],0,sizeof(SurfaceContact));
            }
            for(int i=0;i<NR_TILES;i++)if(s->geometry.tileSurfaces[i].surfaceId==id) {
                nrHeatRelease(s,2,i);memset(&s->tiles[i],0,sizeof(DepositTile));memset(&s->geometry.tileSurfaces[i],0,sizeof(SurfaceTile));
            }
        }
        return 0;
    }
    if(nrEqual(j,op,"emitter-colliders")) {
        if(!nrAllowed(j,0,"op id colliders"))return reject(c,"Unknown emitter collider setting");
        int id=0;
        if(!integer(j,0,"id",&id,1,65535)||!id)return reject(c,"Emitter id required");
        return nrConfigureColliders(c,s,j,nrFindEmitter(s,id),1);
    }
    if(nrEqual(j,op,"model-import"))return importModel(c,s,j);
    if(nrEqual(j,op,"ribbon"))return ribbon(c,s,j);
    if(!nrEqual(j,op,"mesh"))return -2;
    if(!nrAllowed(j,0,"op triangles sampling append subdivisions"))return reject(c,"Unknown mesh setting");
    int subdivisions=1;
    if(!integer(j,0,"subdivisions",&subdivisions,1,16))return reject(c,"Mesh subdivisions must be integer1..16");
    if(nrField(j,0,"subdivisions")>=0&&s->schema<NR_STATE_SCHEMA_MESH_SUBDIVISION)return reject(c,"Mesh subdivision requires current authoring schema");
    int append=0;if(!boolean(j,0,"append",&append))return reject(c,"Mesh append must be boolean");int base=append?s->meshCount:0;
    int sampling=nrField(j,0,"sampling");
    if(sampling>=0) {
        if(nrEqual(j,sampling,"cell"))s->meshSampling=0;
        else if(nrEqual(j,sampling,"half"))s->meshSampling=1;
        else if(nrEqual(j,sampling,"braille"))s->meshSampling=2;
        else if(nrEqual(j,sampling,"hybrid"))s->meshSampling=3;
        else return reject(c,"Invalid mesh sampling");
    }
    int a=nrField(j,0,"triangles");
    if(a<0)return sampling>=0&&nrField(j,0,"subdivisions")<0?0:reject(c,"Mesh subdivision needs triangles");
    if(j->tokens[a].type!=J_ARRAY||base+j->tokens[a].count*subdivisions*subdivisions>NR_MESH)return reject(c,"Expanded triangle capacity");
    int count=j->tokens[a].count;s->meshCount=base;int t=a+1;
    if(!append)memset(s->geometry.triangleSurfaces,0,sizeof(s->geometry.triangleSurfaces));
    for(int i=0;i<count;i++) {
        Triangle input,*q=&input;int id=0,color=0x809caa;
        memset(q,0,sizeof(*q));q->alpha=1;
        if(!nrAllowed(j,t,"a b c color alpha surfaceId")||!vector(j,t,"a",&q->a)||!vector(j,t,"b",&q->b)||!vector(j,t,"c",&q->c)||
           !integer(j,t,"color",&color,0,0xffffff)||!scalar(j,t,"alpha",&q->alpha,0,1)||
           !integer(j,t,"surfaceId",&id,0,NR_SURFACES))return reject(c,"Triangle validation");
        if(nrField(j,t,"surfaceId")>=0&&s->schema<NR_STATE_SCHEMA_GENERAL_API)return reject(c,"Mesh surface assignment requires the current geometry schema");
        if(id&&!s->geometry.surfaces[id-1].used)return reject(c,"Triangle surface does not exist");
        Vec3 normal=nrCross(nrSub(q->b,q->a),nrSub(q->c,q->a));
        if(nrDot(normal,normal)<=1e-16)return reject(c,"Degenerate triangle");
        q->color=(uint32_t)color;
        if(!appendSubdivision(s,q,id,subdivisions))return reject(c,"Degenerate subdivided triangle");
        t=j->tokens[t].next;
    }
    if(s->schema>=NR_STATE_SCHEMA_GENERAL_API)return finishMesh(c,s,append,base,"Invalid mesh collision index");
    return nrBuildGeometry(s,&s->geometry.index)?0:reject(c,"Invalid mesh collision index");
}

int nrWaterHeight(const State*s,int id,double x,double z,double*out) {
    int found=0;double highest=-1e30;
    for(int i=0;i<s->meshCount;i++)if(s->geometry.triangleSurfaces[i]==id) {
        Triangle t=s->mesh[i];if(nrFlowThicknessTriangleAt(s,i,s->timeUs,&t)==2)continue;nrDisplaceSurfaceTriangle(s,i,&t);
        Vec3 ab=nrSub(t.b,t.a),ac=nrSub(t.c,t.a);double det=ab.x*ac.z-ab.z*ac.x;
        double scale=nrSqrt((ab.x*ab.x+ab.z*ab.z)*(ac.x*ac.x+ac.z*ac.z));
        if(nrAbs(det)<=1e-12*(1+scale))continue;
        double u=((x-t.a.x)*ac.z-(z-t.a.z)*ac.x)/det,v=(ab.x*(z-t.a.z)-ab.z*(x-t.a.x))/det;
        if(u< -1e-10||v< -1e-10||u+v>1+1e-10)continue;
        Vec3 normal=nrNormal(nrCross(ab,ac));if(normal.y<0)normal=nrScale(normal,-1);
        /* Reciprocal multiplication can round an axis normal one ULP outside
         * [-1,1]. Keep generated samples within the retained normal domain. */
        normal=nrV(nrClamp(normal.x,-1,1),nrClamp(normal.y,-1,1),nrClamp(normal.z,-1,1));
        Vec3 point=nrV(x,t.a.y+u*ab.y+v*ac.y,z),velocity=nrSurfaceTriangleVelocity(s,i,point);
        if(found&&point.y<=highest)continue;highest=point.y;found=1;
        out[0]=point.y;out[1]=normal.x;out[2]=normal.y;out[3]=normal.z;out[4]=velocity.y;
    }
    return found;
}
static int validFloatBody(const State*s,const FloatBody*b) {
    return b->id&&b->id<=65535&&b->surfaceId>=1&&b->surfaceId<=NR_SURFACES&&s->geometry.surfaces[b->surfaceId-1].used&&
        flag(b->visible)&&!b->padding&&validPoint(b->position)&&validPoint(b->velocity)&&validNormal(b->normal)&&
        bounded(b->mass,.001,1000000)&&bounded(b->radius,.005,64)&&bounded(b->density,0,100000)&&
        bounded(b->gravity,0,256)&&bounded(b->drag,0,1000)&&bounded(b->immersion,0,1)&&bounded(b->buoyantForce,0,1e16)&&b->color<=0xffffff;
}
int nrValidFloatBodies(const State*s) {
    for(int i=0;i<NR_FLOAT_BODIES;i++) {
        const FloatBody*b=&s->floatBodies[i];if(!flag(b->used))return 0;if(!b->used)continue;
        if(!validFloatBody(s,b))return 0;
        for(int k=0;k<i;k++)if(s->floatBodies[k].used&&s->floatBodies[k].id==b->id)return 0;
    }
    return 1;
}
int nrFloatBodyCommand(NrContext*c,State*s,const Json*j) {
    double id;int tok=nrField(j,0,"id"),slot=-1;
    if(tok<0||!nrNumber(j,tok,&id)||id<1||id>65535||id!=(int)id)return reject(c,"Float body id 1..65535 required");
    for(int i=0;i<NR_FLOAT_BODIES;i++)if(s->floatBodies[i].used&&s->floatBodies[i].id==(uint32_t)id)slot=i;
    if(nrEqual(j,nrField(j,0,"op"),"remove-float-body")) {
        if(!nrAllowed(j,0,"op id"))return reject(c,"Unknown float body removal setting");
        if(slot>=0){memset(&s->floatBodies[slot],0,sizeof(FloatBody));memset(&s->floatHulls[slot],0,sizeof(FloatHull));}return 0;
    }
    if(!nrAllowed(j,0,"op id surfaceId position velocity mass radius fluidDensity gravity drag visible color"))return reject(c,"Unknown float body setting");
    if(slot<0){for(int i=0;i<NR_FLOAT_BODIES;i++)if(!s->floatBodies[i].used){slot=i;break;}}
    if(slot<0)return reject(c,"Float body capacity");
    FloatBody*b=&s->floatBodies[slot];
    if(!b->used){memset(b,0,sizeof(*b));b->used=b->visible=1;b->id=(uint32_t)id;b->mass=1000;b->radius=1;b->density=1000;b->gravity=9.81;b->drag=2;b->normal=nrV(0,1,0);b->color=0xd9aa66;}
    int surface=(int)b->surfaceId,color=(int)b->color;
    if(!integer(j,0,"surfaceId",&surface,1,NR_SURFACES)||!integer(j,0,"color",&color,0,0xffffff)||
       !scalar(j,0,"mass",&b->mass,.001,1000000)||!scalar(j,0,"radius",&b->radius,.005,64)||
       !scalar(j,0,"fluidDensity",&b->density,0,100000)||!scalar(j,0,"gravity",&b->gravity,0,256)||
       !scalar(j,0,"drag",&b->drag,0,1000)||!boolean(j,0,"visible",&b->visible))return reject(c,"Invalid float body scalar");
    b->surfaceId=surface;b->color=color;
    if((nrField(j,0,"position")>=0&&!vector(j,0,"position",&b->position))||(nrField(j,0,"velocity")>=0&&!vector(j,0,"velocity",&b->velocity)))return reject(c,"Float body vector");
    return validFloatBody(s,b)?0:reject(c,"Float body requires a valid named surface");
}
int nrFloatBodiesTick(State*s) {
    const double dt=1.0/120;
    for(int i=0;i<NR_FLOAT_BODIES;i++)if(s->floatBodies[i].used) {
        FloatBody*b=&s->floatBodies[i];double sample[5],volume=0;Vec3 waterVelocity=nrV(0,0,0);
        if(s->floatHulls[i].used){if(!nrFloatHullTick(s,i)||!validFloatBody(s,b))return 0;continue;}
        b->normal=nrV(0,1,0);b->immersion=b->buoyantForce=0;
        if(nrWaterHeight(s,b->surfaceId,b->position.x,b->position.z,sample)) {
            b->normal=nrV(sample[1],sample[2],sample[3]);
            double cap=nrClamp(b->radius-(b->position.y-sample[0])*b->normal.y,0,2*b->radius);
            volume=NR_PI*cap*cap*(b->radius-cap/3);
            b->immersion=volume/(4*NR_PI*b->radius*b->radius*b->radius/3);
            b->immersion=nrClamp(b->immersion,0,1);b->buoyantForce=b->density*b->gravity*volume;
            waterVelocity.y=sample[4];
        }
        Vec3 acceleration=nrV(0,b->buoyantForce/b->mass-b->gravity,0);
        double drag=b->drag*b->immersion*dt;
        Vec3 freeVelocity=nrAdd(b->velocity,nrScale(acceleration,dt));int coupled=nrSurfaceFluidExchange(s,b,freeVelocity,dt);if(coupled<0)return 0;
        if(!coupled)b->velocity=nrScale(nrAdd(freeVelocity,nrScale(waterVelocity,drag)),1/(1+drag));
        b->position=nrAdd(b->position,nrScale(b->velocity,dt));
        if(!validFloatBody(s,b))return 0;
    }
    return 1;
}
int nrFloatBody(const NrContext*c,uint32_t id,double*out,uint32_t capacity) {
    if(!c||c->state.magic!=NR_MAGIC||id<1||id>65535||!out||capacity<12||((uintptr_t)out%8)||!nrExternalOutput(c,out,12*sizeof(double)))return -1;
    for(int i=0;i<NR_FLOAT_BODIES;i++)if(c->state.floatBodies[i].used&&c->state.floatBodies[i].id==id) {
        const FloatBody*b=&c->state.floatBodies[i];double values[12]={b->position.x,b->position.y,b->position.z,b->velocity.x,b->velocity.y,b->velocity.z,b->normal.x,b->normal.y,b->normal.z,b->immersion,b->buoyantForce,b->mass};
        memcpy(out,values,sizeof(values));return 1;
    }
    return 0;
}
void nrDrawFloatBodies(NrContext*c,const Projection*p) {
    for(int i=0;i<NR_FLOAT_BODIES;i++)if(c->state.floatBodies[i].used&&c->state.floatBodies[i].visible) {
        const FloatBody*b=&c->state.floatBodies[i];
        const FloatHull*h=&c->state.floatHulls[i];
        if(h->used){
            Vec3 hullVertices[128];for(uint32_t k=0;k<h->vertexCount;k++)hullVertices[k]=nrFloatHullVertex(b,h,k);
            c->paintOwner=0x41000000u|b->id;
            for(uint32_t k=0;k<h->faceCount;k++)nrTriangle(c,p,(Triangle){hullVertices[h->faces[k][0]],hullVertices[h->faces[k][1]],hullVertices[h->faces[k][2]],b->color,1});
            continue;
        }
        Vec3 vertices[6];
        vertices[0]=nrAdd(b->position,nrV(b->radius,0,0));vertices[1]=nrAdd(b->position,nrV(0,0,b->radius));
        vertices[2]=nrAdd(b->position,nrV(-b->radius,0,0));vertices[3]=nrAdd(b->position,nrV(0,0,-b->radius));
        vertices[4]=nrAdd(b->position,nrV(0,b->radius,0));vertices[5]=nrAdd(b->position,nrV(0,-b->radius,0));
        c->paintOwner=0x41000000u|b->id;
        for(int k=0;k<4;k++)for(int pole=4;pole<6;pole++)nrTriangle(c,p,(Triangle){vertices[k],vertices[(k+1)%4],vertices[pole],b->color,1});
    }
}

static void addFoam(FoamCell*c,double amount) {
    c->generated+=amount;c->density+=amount;
    if(c->density>1){c->saturated+=c->density-1;c->density=1;}
}
void nrFoamMeshChanged(State*s) {memset(s->foamTransfers,0,sizeof(s->foamTransfers));memset(s->foam.cells,0,sizeof(s->foam.cells));s->foam.meshGeneration=s->geometry.meshGeneration;}
int nrFoamCommand(NrContext*c,State*s,const Json*j) {
    int id=0;if(!integer(j,0,"surfaceId",&id,1,NR_SURFACES)||id<1||!s->geometry.surfaces[id-1].used)return reject(c,"Foam requires named surfaceId");
    if(nrEqual(j,nrField(j,0,"op"),"clear-surface-foam")) {
        if(!nrAllowed(j,0,"op surfaceId"))return reject(c,"Unknown foam clear setting");
        for(int i=0;i<s->meshCount;i++)if(s->geometry.triangleSurfaces[i]==id){memset(&s->foam.cells[i],0,sizeof(FoamCell));memset(&s->foamTransfers[i],0,sizeof(s->foamTransfers[i]));}return 0;
    }
    if(!nrAllowed(j,0,"op surfaceId enabled sourceRate curvatureThreshold decay impactGain color"))return reject(c,"Unknown foam setting");
    FoamSettings*f=&s->foam.settings[id-1];if(!f->used){*f=(FoamSettings){.used=1,.enabled=1,.sourceRate=.1,.threshold=1,.decay=1,.impactGain=.001,.color=0xf0f4ef};}
    int color=f->color;
    if(!boolean(j,0,"enabled",&f->enabled)||!integer(j,0,"color",&color,0,0xffffff)||
       !scalar(j,0,"sourceRate",&f->sourceRate,0,1000)||!scalar(j,0,"curvatureThreshold",&f->threshold,0,1000000)||
       !scalar(j,0,"decay",&f->decay,0,1000)||!scalar(j,0,"impactGain",&f->impactGain,0,1000))return reject(c,"Invalid foam scalar");
    f->color=color;return 0;
}
void nrFoamImpact(State*s,const GeometryHit*hit,const Particle*p,Vec3 velocity) {
    if(hit->surfaceId<=0||hit->triangleIndex<0)return;
    const FoamSettings*f=&s->foam.settings[hit->surfaceId-1];if(!f->used||!f->enabled)return;
    double speed=nrAbs(nrDot(nrSub(velocity,hit->surfaceVelocity),hit->normal));
    addFoam(&s->foam.cells[hit->triangleIndex],f->impactGain*p->size*p->size*speed);
}
void nrFoamTick(State*s) {
    for(int i=0;i<s->meshCount;i++) {
        int id=s->geometry.triangleSurfaces[i];if(id<=0)continue;
        const FoamSettings*f=&s->foam.settings[id-1];if(!f->used)continue;
        FoamCell*c=&s->foam.cells[i];
        if(f->enabled&&f->sourceRate>0) {
            Vec3 point=center(&s->mesh[i]);double sample[6];
            if(nrWaveSample(&s->surfaceWaves[id-1].waves[0][0],s->surfaceWaves[id-1].count,point.x,point.z,s->timeUs/1000000.0,sample,6)==1) {
                double excess=nrAbs(sample[5])-f->threshold;if(excess>0)addFoam(c,f->sourceRate*excess/(1+excess)/120);
            }
        }
        double density=c->density/(1+f->decay/120);c->decayed+=c->density-density;c->density=density;
    }
    nrFoamTransportTick(s);
}
int nrValidFoam(const State*s) {
    if(!nrValidFoamTransport(s))return 0;
    if(s->foam.padding||((s->schema>=NR_STATE_SCHEMA_GENERAL_API||s->schema==NR_STATE_SCHEMA_THERMAL_LINK||s->schema==NR_STATE_SCHEMA_THERMAL_TRANSFER||s->schema==NR_STATE_SCHEMA_THERMAL||s->schema==NR_STATE_SCHEMA_WATER_REEMIT||s->schema==NR_STATE_SCHEMA_WATER_LINK||s->schema==NR_STATE_SCHEMA_WATER_TRANSFER||s->schema==NR_STATE_SCHEMA_SURFACE_WATER||s->schema==NR_STATE_SCHEMA_SPRAY_PARTICLES||s->schema==NR_STATE_SCHEMA_FLOW_SPRAY||s->schema==NR_STATE_SCHEMA_FLOW_SINK||s->schema==NR_STATE_SCHEMA_FLOW_SURFACE||s->schema==NR_STATE_SCHEMA_FLOW||s->schema==NR_STATE_SCHEMA_REPEAT_EDIT||s->schema==NR_STATE_SCHEMA_EDITOR_REDO||s->schema==NR_STATE_SCHEMA_NAMED_REGISTERS||s->schema==NR_STATE_SCHEMA_VIM_REGISTER||s->schema==NR_STATE_SCHEMA_VIM_OPERATOR||s->schema==NR_STATE_SCHEMA_VIM_COUNT||s->schema==NR_STATE_SCHEMA_PATH_ACTORS||s->schema==NR_STATE_SCHEMA_FOAM)&&s->foam.meshGeneration!=s->geometry.meshGeneration))return 0;
    for(int i=0;i<NR_SURFACES;i++) {
        const FoamSettings*f=&s->foam.settings[i];if(!flag(f->used)||!flag(f->enabled)||f->padding)return 0;
        if(f->used&&(!s->geometry.surfaces[i].used||!bounded(f->sourceRate,0,1000)||!bounded(f->threshold,0,1000000)||!bounded(f->decay,0,1000)||!bounded(f->impactGain,0,1000)||f->color>0xffffff))return 0;
    }
    for(int i=0;i<NR_MESH;i++) {
        const FoamCell*c=&s->foam.cells[i];
        if(!bounded(c->density,0,1)||!bounded(c->generated,0,1e14)||!bounded(c->decayed,0,1e14)||!bounded(c->saturated,0,1e14))return 0;
        if(c->density||c->generated||c->decayed||c->saturated||s->foamTransfers[i].incoming||s->foamTransfers[i].outgoing) {
            if(i>=s->meshCount||s->geometry.triangleSurfaces[i]<=0||!s->foam.settings[s->geometry.triangleSurfaces[i]-1].used)return 0;
            if(nrAbs(c->generated+s->foamTransfers[i].incoming-c->density-c->decayed-c->saturated-s->foamTransfers[i].outgoing)>1e-8*(1+c->generated+s->foamTransfers[i].incoming+s->foamTransfers[i].outgoing))return 0;
        }
    }
    return 1;
}
int nrSurfaceFoam(const NrContext*c,uint32_t id,double*out,uint32_t capacity) {
    if(!c||c->state.magic!=NR_MAGIC||id<1||id>NR_SURFACES||!c->state.geometry.surfaces[id-1].used||(!out&&capacity)||((uintptr_t)out%8))return -1;
    int count=0;for(int i=0;i<c->state.meshCount;i++)if(c->state.geometry.triangleSurfaces[i]==(int)id)count++;
    if(!out)return count;if(capacity<(uint32_t)count||!nrExternalOutput(c,out,(size_t)count*5*sizeof(double)))return -1;
    int row=0;for(int i=0;i<c->state.meshCount;i++)if(c->state.geometry.triangleSurfaces[i]==(int)id) {
        const FoamCell*f=&c->state.foam.cells[i];double values[5]={i,f->density,f->generated,f->decayed,f->saturated};memcpy(out+row*5,values,sizeof(values));row++;
    }
    return count;
}

static int applyFloatBodyField(FloatBody*body,const Value*v,double x){
    FloatBody q=*body;int matched=0;
#define NUM(name,member,lo,hi) if(!strcmp(v->field,name)){if(!(x>=lo&&x<=hi))return 0;q.member=x;matched=1;}
        NUM("mass",mass,.001,1000000) NUM("radius",radius,.005,64)
        NUM("fluidDensity",density,0,100000) NUM("gravity",gravity,0,256) NUM("drag",drag,0,1000)
        NUM("position.x",position.x,-16000,16000) NUM("position.y",position.y,-16000,16000) NUM("position.z",position.z,-16000,16000)
        NUM("velocity.x",velocity.x,-16000,16000) NUM("velocity.y",velocity.y,-16000,16000) NUM("velocity.z",velocity.z,-16000,16000)
        if(!strcmp(v->field,"visible")){if(x!=0&&x!=1)return 0;q.visible=(int)x;matched=1;}
        if(!strcmp(v->field,"color")){if(!(x>=0&&x<=0xffffff)||x!=(uint32_t)x)return 0;q.color=(uint32_t)x;matched=1;}
        if(!strcmp(v->field,"surfaceId")){if(!(x>=1&&x<=NR_SURFACES)||x!=(int)x)return 0;q.surfaceId=(uint32_t)x;matched=1;}
    if(!matched)return 0;*body=q;return 1;
#undef NUM
}
int nrFloatBodyNumberValid(const Value*v,double x){
    if(!strncmp(v->field,"hull.",5))return nrFloatHullNumberValid(v,x);
    if(v->bindingFamily!=18||!nrResourceBindingShapeValid(v))return 0;
    FloatBody body;memset(&body,0,sizeof(body));
    body.used=body.visible=1;body.id=body.surfaceId=1;body.mass=body.radius=body.density=1;
    body.normal=nrV(0,1,0);
    return applyFloatBodyField(&body,v,x);
}
int nrBindFloatBodyValue(State*s,const Value*v,double x){
    if(!strncmp(v->field,"hull.",5))return nrBindFloatHullValue(s,v,x);
    for(int i=0;i<NR_FLOAT_BODIES;i++)if(s->floatBodies[i].used&&s->floatBodies[i].id==(uint32_t)v->bindingId){
        FloatBody q=s->floatBodies[i];
        if(!applyFloatBodyField(&q,v,x)||!validFloatBody(s,&q))return 0;
        s->floatBodies[i]=q;return 1;
    }return 0;
}

int nrBindFoamValue(State*s,const Value*v,double x){
    if(v->bindingId<1||v->bindingId>NR_SURFACES||!s->geometry.surfaces[v->bindingId-1].used||!s->foam.settings[v->bindingId-1].used)return 0;
    if(!strcmp(v->field,"velocity.x")||!strcmp(v->field,"velocity.z")){
        if(!(x>=-1000&&x<=1000))return 0;
        if(!strcmp(v->field,"velocity.x"))s->foamVelocity[v->bindingId-1].x=x;
        else s->foamVelocity[v->bindingId-1].z=x;
        return nrValidFoamTransport(s);
    }
    FoamSettings q=s->foam.settings[v->bindingId-1];int matched=0;
#define NUM(name,member,lo,hi) if(!strcmp(v->field,name)){if(!(x>=lo&&x<=hi))return 0;q.member=x;matched=1;}
    NUM("sourceRate",sourceRate,0,1000) NUM("curvatureThreshold",threshold,0,1000000)
    NUM("decay",decay,0,1000) NUM("impactGain",impactGain,0,1000)
    if(!strcmp(v->field,"enabled")){if(x!=0&&x!=1)return 0;q.enabled=(int)x;matched=1;}
    if(!strcmp(v->field,"color")){if(!(x>=0&&x<=0xffffff)||x!=(uint32_t)x)return 0;q.color=(uint32_t)x;matched=1;}
    if(!matched)return 0;s->foam.settings[v->bindingId-1]=q;return 1;
#undef NUM
}

int nrBindMeshAppearance(State*s,const Value*v,double x){
    int first=0,end=s->meshCount;
    if(v->bindingFamily==20){if(v->bindingId)return 0;}
    else if(v->bindingFamily==21){if(v->bindingId<0||v->bindingId>=end)return 0;first=v->bindingId;end=first+1;}
    else return 0;
    if(!strcmp(v->field,"sampling")){
        if(v->bindingFamily!=20||x<0||x>3||x!=(int)x)return 0;s->meshSampling=(int)x;return 1;
    }
    if(!strcmp(v->field,"alpha")){
        if(!(x>=0&&x<=1))return 0;for(int i=first;i<end;i++)s->mesh[i].alpha=x;return 1;
    }
    if(!strcmp(v->field,"color")){
        if(!(x>=0&&x<=0xffffff)||x!=(uint32_t)x)return 0;for(int i=first;i<end;i++)s->mesh[i].color=(uint32_t)x;return 1;
    }return 0;
}
int nrMeshStyleCommand(NrContext*c,State*s,const Json*j){
    if(!nrAllowed(j,0,"op triangleIndex alpha color sampling"))return reject(c,"Unknown mesh style setting");
    Value v;memset(&v,0,sizeof(v));v.bindingFamily=20;
    int target=nrField(j,0,"triangleIndex");double x;
    if(target>=0){if(!nrNumber(j,target,&x)||x<0||x>=s->meshCount||x!=(int)x)return reject(c,"Unknown mesh triangle");v.bindingFamily=21;v.bindingId=(int)x;}
    const char*fields[]={"alpha","color","sampling"};int changed=0;
    for(int i=0;i<3;i++){
        int token=nrField(j,0,fields[i]);if(token<0)continue;changed=1;
        if(i==2){const char*names[]={"cell","half","braille","hybrid"};int choice=-1;for(int k=0;k<4;k++)if(nrEqual(j,token,names[k]))choice=k;if(choice<0)return reject(c,"Invalid mesh sampling");x=choice;}
        else if(!nrNumber(j,token,&x))return reject(c,"Invalid mesh appearance scalar");
        memcpy(v.field,fields[i],strlen(fields[i])+1);if(!nrBindMeshAppearance(s,&v,x))return reject(c,"Invalid mesh appearance setting");
    }return changed?0:reject(c,"Mesh appearance setting required");
}
