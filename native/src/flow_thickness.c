#include "internal.h"
/* One retained volume compiler serves channels, ribbons and falling sheets.
 * Authored mesh contains the maximum prism; sampling uses the retained flux. */
static int fail(NrContext*c,const char*message){size_t n=strlen(message);if(n>255)n=255;memcpy(c->error,message,n);c->error[n]=0;return -1;}
static Vec3 point(const Triangle*t,int k){return k==0?t->a:k==1?t->b:t->c;}
static int same(Vec3 a,Vec3 b){return a.x==b.x&&a.y==b.y&&a.z==b.z;}
static int flowSlot(const State*s,int id){for(int i=0;i<8;i++)if(s->flows[i].used&&s->flows[i].id==s->flowSurfaces[id-1].flowId)return i;return -1;}
static double depthAt(const State*s,int id,uint64_t timeUs,double*flux){
    const FlowThickness*q=&s->flowThickness[id-1];int slot=flowSlot(s,id);
    *flux=0;if(!q->used||slot<0)return 0;
    *flux=nrFlowStageFluxAt(s,slot,s->flowSurfaces[id-1].stage,timeUs);
    return nrClamp(*flux/(q->width*q->speed),0,q->maxDepth);
}
static void triangleAtDepth(const State*s,int index,double depth,Triangle*out){
    int id=s->geometry.triangleSurfaces[index];const FlowThickness*q=&s->flowThickness[id-1];
    *out=s->mesh[index];Vec3*v[3]={&out->a,&out->b,&out->c};
    for(int k=0;k<3;k++)if(s->flowThicknessTriangles[index].weight[k])*v[k]=nrAdd(*v[k],nrScale(q->direction,depth-q->maxDepth));
}
int nrFlowThicknessTriangleAt(const State*s,int index,uint64_t timeUs,Triangle*out){
    if(index<0||index>=s->meshCount||!s->flowThicknessTriangles[index].role)return 0;
    int id=s->geometry.triangleSurfaces[index];if(id<1||id>NR_SURFACES||!s->flowThickness[id-1].used)return 0;
    double flux,depth=depthAt(s,id,timeUs,&flux);triangleAtDepth(s,index,depth,out);return depth>0?1:2;
}
int nrValidFlowThickness(const State*s){
    if(s->meshCount<0||s->meshCount>NR_MESH)return 0;
    for(int id=1;id<=NR_SURFACES;id++){
        const FlowThickness*q=&s->flowThickness[id-1];
        if(!q->used){const unsigned char*bytes=(const unsigned char*)q;for(size_t k=0;k<sizeof(*q);k++)if(bytes[k])return 0;continue;}
        if(q->used!=1||q->padding||s->schema<NR_STATE_SCHEMA_FLOW_THICKNESS||!s->geometry.surfaces[id-1].used||s->surfaceWaves[id-1].count||
           !(q->width>=.000001&&q->width<=10000&&q->speed>=.000001&&q->speed<=10000&&q->maxDepth>=.000001&&q->maxDepth<=64)||
           !(nrDot(q->direction,q->direction)>=.999999&&nrDot(q->direction,q->direction)<=1.000001))return 0;
        int slot=flowSlot(s,id);if(slot<0||s->flowSurfaces[id-1].stage<0||s->flowSurfaces[id-1].stage>=s->flows[slot].count)return 0;
        const Flow*f=&s->flows[slot];if(f->epochs<1||f->epochs>128)return 0;
        for(int k=0;k<f->epochs;k++)if(f->changes[k].rate>q->width*q->speed*q->maxDepth)return 0;
        int bottom=0,top=0,side=0;
        for(int i=0;i<s->meshCount;i++)if(s->geometry.triangleSurfaces[i]==id){
            const FlowThicknessTriangle*t=&s->flowThicknessTriangles[i];
            if(t->role==1||t->role==4)bottom++;else if(t->role==2)top++;else if(t->role==3)side++;else return 0;
        }
        if(!bottom||bottom!=top||!side||side%2)return 0;
    }
    for(int i=0;i<NR_MESH;i++){
        const FlowThicknessTriangle*t=&s->flowThicknessTriangles[i];
        if(!t->role){if(t->weight[0]||t->weight[1]||t->weight[2])return 0;continue;}
        int id=i<s->meshCount?s->geometry.triangleSurfaces[i]:0;
        if(id<1||id>NR_SURFACES||!s->flowThickness[id-1].used||t->role>4)return 0;
        int sum=0;for(int k=0;k<3;k++){if(t->weight[k]>1)return 0;sum+=t->weight[k];}
        if(((t->role==1||t->role==4)&&sum)||(t->role==2&&sum!=3)||(t->role==3&&(sum<1||sum>2)))return 0;
        const Triangle*face=&s->mesh[i];Vec3 normal=nrCross(nrSub(face->b,face->a),nrSub(face->c,face->a));double length=nrSqrt(nrDot(normal,normal));
        double alignment=nrDot(normal,s->flowThickness[id-1].direction);
        if(!(length>1e-8)||((t->role==1||t->role==4)&&alignment>=-length*1e-12)||(t->role==2&&alignment<=length*1e-12)||(t->role==3&&nrAbs(alignment)>length*1e-10))return 0;
        for(int edge=0;edge<3;edge++){
            Vec3 a=point(face,edge),b=point(face,(edge+1)%3);int matches=0;
            for(int other=0;other<s->meshCount;other++)if(other!=i&&s->geometry.triangleSurfaces[other]==id)
                for(int k=0;k<3;k++)if(same(a,point(&s->mesh[other],(k+1)%3))&&same(b,point(&s->mesh[other],k)))matches++;
            if(matches!=1)return 0;
        }

    }
    return 1;
}
static void reverse(Triangle*t,FlowThicknessTriangle*record){Vec3 p=t->b;t->b=t->c;t->c=p;uint32_t w=record->weight[1];record->weight[1]=record->weight[2];record->weight[2]=w;}
int nrBindFlowThicknessValue(State*s,const Value*v,double x){
    if(s->schema<NR_STATE_SCHEMA_FLOW_SETTINGS||v->bindingId<1||v->bindingId>NR_SURFACES||!(x>=.000001&&x<=10000))return 0;
    FlowThickness*q=&s->flowThickness[v->bindingId-1];if(!q->used)return 0;FlowThickness old=*q;
    if(!strcmp(v->field,"thickness.width"))q->width=x;else if(!strcmp(v->field,"thickness.speed"))q->speed=x;else return 0;
    if(!nrValidFlowThickness(s)){*q=old;return 0;}return 1;
}
int nrFlowThicknessSettingsShape(const Json*j){
    if(!nrEqual(j,nrField(j,0,"op"),"flow-thickness-settings")||!nrAllowed(j,0,"op surfaceId width speed"))return 0;
    double id;if(!nrNumber(j,nrField(j,0,"surfaceId"),&id)||id<1||id>NR_SURFACES||id!=(int)id)return 0;
    int fields=0;const char*names[2]={"width","speed"};for(int k=0;k<2;k++){
        int at=nrField(j,0,names[k]);if(at>=0){double x;if(!nrNumber(j,at,&x)||!(x>=.000001&&x<=10000))return 0;fields++;}
    }return fields>0;
}
int nrFlowThicknessCommand(NrContext*c,State*s,const Json*j){
    if(nrEqual(j,nrField(j,0,"op"),"flow-thickness-settings")){
        if(!nrFlowThicknessSettingsShape(j))return fail(c,"Invalid hydraulic settings shape or dimensions");
        double id;nrNumber(j,nrField(j,0,"surfaceId"),&id);FlowThickness*target=&s->flowThickness[(int)id-1];
        if(!target->used)return fail(c,"Flow thickness does not exist");
        FlowThickness old=*target,candidate=old;int at=nrField(j,0,"width");if(at>=0)nrNumber(j,at,&candidate.width);
        at=nrField(j,0,"speed");if(at>=0)nrNumber(j,at,&candidate.speed);*target=candidate;
        if(!nrValidFlowThickness(s)){*target=old;return fail(c,"Hydraulic settings exceed retained flux capacity");}
        return 0;
    }
    int remove=nrEqual(j,nrField(j,0,"op"),"remove-flow-thickness");double number;
    if(!nrAllowed(j,0,remove?"op surfaceId":"op surfaceId width speed maxDepth direction")||!nrNumber(j,nrField(j,0,"surfaceId"),&number)||number<1||number>NR_SURFACES||number!=(int)number)return fail(c,"Invalid flow thickness target");
    int id=(int)number,target=id-1;
    if(remove){
        if(!s->flowThickness[target].used)return fail(c,"Flow thickness does not exist");
        int count=0;
        for(int i=0;i<s->meshCount;i++){
            FlowThicknessTriangle record=s->flowThicknessTriangles[i];Triangle triangle=s->mesh[i];int surface=s->geometry.triangleSurfaces[i];
            if(surface==id&&(record.role==2||record.role==3))continue;
            if(surface==id){if(record.role==4)reverse(&triangle,&record);memset(&record,0,sizeof(record));}
            s->mesh[count]=triangle;s->geometry.triangleSurfaces[count]=surface;s->flowThicknessTriangles[count]=record;count++;
        }
        memset(&s->mesh[count],0,(NR_MESH-count)*sizeof(s->mesh[0]));memset(&s->geometry.triangleSurfaces[count],0,(NR_MESH-count)*sizeof(int));
        memset(&s->flowThicknessTriangles[count],0,(NR_MESH-count)*sizeof(s->flowThicknessTriangles[0]));s->meshCount=count;memset(&s->flowThickness[target],0,sizeof(FlowThickness));
        return nrFinishFlowThicknessMesh(c,s,0,0);
    }
    if(s->flowThickness[target].used||!s->geometry.surfaces[target].used||!s->flowSurfaces[target].flowId||s->surfaceWaves[target].count)return fail(c,"Thickness requires an unowned surface with a flow binding and no wave field");
    FlowThickness q={.used=1,.direction={0,1,0}};
    if(!nrNumber(j,nrField(j,0,"width"),&q.width)||!nrNumber(j,nrField(j,0,"speed"),&q.speed)||!nrNumber(j,nrField(j,0,"maxDepth"),&q.maxDepth))return fail(c,"Thickness requires width, speed and maxDepth");
    int vector=nrField(j,0,"direction");if(vector>=0){
        if(j->tokens[vector].type!=J_ARRAY||j->tokens[vector].count!=3)return fail(c,"Thickness direction requires XYZ");
        double*v[3]={&q.direction.x,&q.direction.y,&q.direction.z};int at=vector+1;
        for(int k=0;k<3;k++){if(!nrNumber(j,at,v[k])||!(*v[k]>=-1&&*v[k]<=1))return fail(c,"Invalid thickness direction");at=j->tokens[at].next;}
    }
    double length=nrSqrt(nrDot(q.direction,q.direction));if(!(length>.000001))return fail(c,"Thickness direction must be nonzero");q.direction=nrScale(q.direction,1/length);
    if(!(q.width>=.000001&&q.width<=10000&&q.speed>=.000001&&q.speed<=10000&&q.maxDepth>=.000001&&q.maxDepth<=64))return fail(c,"Thickness dimensions exceed range");
    Triangle sources[NR_MESH];int indices[NR_MESH],count=0,edges[NR_MESH][3]={{0}},boundary=0;
    for(int i=0;i<s->meshCount;i++)if(s->geometry.triangleSurfaces[i]==id){sources[count]=s->mesh[i];indices[count++]=i;}
    if(!count)return fail(c,"Thickness needs authored surface triangles");
    for(int i=0;i<count;i++){
        Vec3 normal=nrCross(nrSub(sources[i].b,sources[i].a),nrSub(sources[i].c,sources[i].a));
        if(nrAbs(nrDot(normal,q.direction))<=1e-12*nrSqrt(nrDot(normal,normal)))return fail(c,"Thickness direction lies in a source face");
        for(int edge=0;edge<3;edge++){
            Vec3 a=point(&sources[i],edge),b=point(&sources[i],(edge+1)%3);int matches=0;
            for(int other=0;other<count;other++)if(other!=i)for(int k=0;k<3;k++){
                Vec3 u=point(&sources[other],k),v=point(&sources[other],(k+1)%3);
                if((same(a,u)&&same(b,v))||(same(a,v)&&same(b,u)))matches++;
            }
            if(matches>1)return fail(c,"Thickness requires manifold source edges");
            if(!matches){edges[i][edge]=1;boundary++;}
        }
    }
    if(!boundary||s->meshCount+count+2*boundary>NR_MESH)return fail(c,"Thickness mesh capacity or missing boundary");
    int base=s->meshCount;s->flowThickness[target]=q;
    for(int i=0;i<count;i++){
        Triangle original=sources[i];Vec3 normal=nrCross(nrSub(original.b,original.a),nrSub(original.c,original.a));int positive=nrDot(normal,q.direction)>0;
        FlowThicknessTriangle bottom={.role=positive?4:1};if(positive)reverse(&s->mesh[indices[i]],&bottom);s->flowThicknessTriangles[indices[i]]=bottom;
        Triangle top=original;Vec3 offset=nrScale(q.direction,q.maxDepth);top.a=nrAdd(top.a,offset);top.b=nrAdd(top.b,offset);top.c=nrAdd(top.c,offset);
        FlowThicknessTriangle topRecord={.role=2,.weight={1,1,1}};if(!positive)reverse(&top,&topRecord);
        int index=s->meshCount++;s->mesh[index]=top;s->geometry.triangleSurfaces[index]=id;s->flowThicknessTriangles[index]=topRecord;
        for(int edge=0;edge<3;edge++)if(edges[i][edge]){
            Vec3 a=point(&original,edge),b=point(&original,(edge+1)%3),A=nrAdd(a,offset),B=nrAdd(b,offset);
            Triangle faces[2]={{a,b,A,original.color,original.alpha},{b,B,A,original.color,original.alpha}};
            FlowThicknessTriangle records[2]={{.role=3,.weight={0,0,1}},{.role=3,.weight={0,1,1}}};
            Vec3 inward=nrSub(nrScale(nrAdd(nrAdd(original.a,original.b),original.c),1.0/3),a);
            if(nrDot(nrCross(nrSub(b,a),offset),inward)>0){reverse(&faces[0],&records[0]);reverse(&faces[1],&records[1]);}
            for(int k=0;k<2;k++){index=s->meshCount++;s->mesh[index]=faces[k];s->geometry.triangleSurfaces[index]=id;s->flowThicknessTriangles[index]=records[k];}
        }
    }
    return nrValidFlowThickness(s)?nrFinishFlowThicknessMesh(c,s,1,base):fail(c,"Flow thickness ownership or capacity rejected");
}
int nrFlowThicknessGeometryEditAllowed(const State*s,const Json*j){
    int active=0;for(int i=0;i<NR_SURFACES;i++)if(s->flowThickness[i].used)active=1;if(!active)return 1;
    int op=nrField(j,0,"op");if(nrEqual(j,op,"surface")||nrEqual(j,op,"clear-surface"))return 1;
    /* Waterfall always appends, and has no public append flag. It may add an
     * independent assembly while preserving existing owned volume indices. */
    if(nrEqual(j,op,"waterfall")){
        double channel,sheet;
        if(!nrNumber(j,nrField(j,0,"channelSurfaceId"),&channel)||!(channel>=1&&channel<=NR_SURFACES)||channel!=(int)channel||
           !nrNumber(j,nrField(j,0,"sheetSurfaceId"),&sheet)||!(sheet>=1&&sheet<=NR_SURFACES)||sheet!=(int)sheet)return 0;
        return !s->flowThickness[(int)channel-1].used&&!s->flowThickness[(int)sheet-1].used;
    }
    int append=0;if(!nrBoolean(j,nrField(j,0,"append"),&append)||!append)return 0;
    /* Appending foreign geometry preserves all owned indices. Full validation
     * rejects appending an unowned face to an extruded surface. */
    return !nrEqual(j,op,"waterfall");
}
int nrFlowThickness(const NrContext*c,uint32_t id,double*out,uint32_t capacity){
    if(!c||c->state.magic!=NR_MAGIC||id<1||id>NR_SURFACES||!out||capacity<6||((uintptr_t)out%8)||!nrExternalOutput(c,out,6*sizeof(double)))return -1;
    const FlowThickness*q=&c->state.flowThickness[id-1];if(!q->used)return 0;double flux,depth=depthAt(&c->state,id,c->state.timeUs,&flux);
    double values[6]={flux,depth,q->width*depth,q->width,q->speed,q->maxDepth};memcpy(out,values,sizeof(values));return 1;
}
int nrSurfaceTriangles(const NrContext*c,uint32_t id,double*out,uint32_t capacity){
    if(!c||c->state.magic!=NR_MAGIC||id<1||id>NR_SURFACES||!c->state.geometry.surfaces[id-1].used||(!out&&capacity)||((uintptr_t)out%8))return -1;
    int active=c->state.flowThickness[id-1].used;double flux,depth=active?depthAt(&c->state,id,c->state.timeUs,&flux):0;
    if(active&&depth<=0)return 0;
    int count=0;for(int i=0;i<c->state.meshCount;i++)if(c->state.geometry.triangleSurfaces[i]==(int)id)count++;
    if(!out)return count;if(capacity<(uint32_t)count||!nrExternalOutput(c,out,(size_t)count*12*sizeof(double)))return -1;int row=0;
    for(int i=0;i<c->state.meshCount;i++)if(c->state.geometry.triangleSurfaces[i]==(int)id){
        Triangle t=c->state.mesh[i];nrDisplaceSurfaceTriangle(&c->state,i,&t);
        double values[12]={i,t.a.x,t.a.y,t.a.z,t.b.x,t.b.y,t.b.z,t.c.x,t.c.y,t.c.z,t.color,t.alpha};memcpy(out+12*row,values,sizeof(values));row++;
    }return count;
}
/* Extrusion top/bottom faces translate rigidly; wall planes stay fixed while
 * their edge lengths vary. Thus one linear-step plane solve is sufficient. */
int nrFlowThicknessHit(const State*s,int index,Vec3 from,Vec3 to,double start,double duration,double maximum,GeometryHit*out){
    if(duration<=0||index<0||index>=s->meshCount||!s->flowThicknessTriangles[index].role)return 0;
    uint64_t beginUs=s->step?((uint64_t)(s->step-1)*1000000)/120:s->timeUs,endUs=((uint64_t)s->step*1000000)/120;
    Triangle a,b;int first=nrFlowThicknessTriangleAt(s,index,beginUs,&a),last=nrFlowThicknessTriangleAt(s,index,endUs,&b);if(first==2&&last==2)return 0;
    double window=s->step?(s->step-1)/120.0:start,low=(start-window)*120,high=low+duration*120;
    if(low<0)low=0;if(high>1)high=1;
    Vec3 va[3]={a.a,a.b,a.c},vb[3]={b.a,b.b,b.c},left[3],right[3];
    for(int k=0;k<3;k++){Vec3 d=nrSub(vb[k],va[k]);left[k]=nrAdd(va[k],nrScale(d,low));right[k]=nrAdd(va[k],nrScale(d,high));}
    Vec3 normal=nrCross(nrSub(right[1],right[0]),nrSub(right[2],right[0]));
    if(nrDot(normal,normal)<=1e-20)normal=nrCross(nrSub(left[1],left[0]),nrSub(left[2],left[0]));
    double length=nrSqrt(nrDot(normal,normal));if(length<=1e-10)return 0;normal=nrScale(normal,1/length);
    Vec3 delta=nrSub(to,from),faceDelta=nrSub(right[0],left[0]);double relative=nrDot(normal,nrSub(delta,faceDelta));
    if(nrAbs(relative)<=1e-12)return 0;double at=nrDot(normal,nrSub(left[0],from))/relative;
    if(at<=1e-10||at>maximum)return 0;
    Vec3 vertices[3];for(int k=0;k<3;k++)vertices[k]=nrAdd(left[k],nrScale(nrSub(right[k],left[k]),at));
    Vec3 position=nrAdd(from,nrScale(delta,at)),ab=nrSub(vertices[1],vertices[0]),ac=nrSub(vertices[2],vertices[0]),ap=nrSub(position,vertices[0]);
    double aa=nrDot(ab,ab),bb=nrDot(ac,ac),cross=nrDot(ab,ac),den=aa*bb-cross*cross;if(den<=1e-20)return 0;
    double u=(nrDot(ap,ab)*bb-nrDot(ap,ac)*cross)/den,v=(nrDot(ap,ac)*aa-nrDot(ap,ab)*cross)/den;
    if(u< -1e-10||v< -1e-10||u+v>1+1e-10)return 0;
    Vec3 velocity=nrV(0,0,0);double weights[3]={1-u-v,u,v};
    for(int k=0;k<3;k++)velocity=nrAdd(velocity,nrScale(nrSub(right[k],left[k]),weights[k]/duration));
    if(nrDot(normal,nrSub(nrScale(delta,1/duration),velocity))>0)normal=nrScale(normal,-1);
    memset(out,0,sizeof(*out));out->fraction=at;out->position=position;out->normal=normal;out->surfaceVelocity=velocity;
    out->triangleIndex=index;out->surfaceId=s->geometry.triangleSurfaces[index];return 1;
}
Vec3 nrFlowThicknessVelocity(const State*s,int index,Vec3 position){
    if(!s->step||index<0||index>=s->meshCount||!s->flowThicknessTriangles[index].role)return nrV(0,0,0);
    Triangle current;nrFlowThicknessTriangleAt(s,index,s->timeUs,&current);
    Vec3 ab=nrSub(current.b,current.a),ac=nrSub(current.c,current.a),ap=nrSub(position,current.a);
    double aa=nrDot(ab,ab),bb=nrDot(ac,ac),cross=nrDot(ab,ac),den=aa*bb-cross*cross;if(den<=1e-20)return nrV(0,0,0);
    double u=(nrDot(ap,ab)*bb-nrDot(ap,ac)*cross)/den,v=(nrDot(ap,ac)*aa-nrDot(ap,ab)*cross)/den;
    uint64_t begin=((uint64_t)(s->step-1)*1000000)/120;
    if(s->timeUs<=begin)return nrV(0,0,0);
    double span=(s->timeUs-begin)/1000000.0;
    int id=s->geometry.triangleSurfaces[index];double flux,before=depthAt(s,id,begin,&flux),after=depthAt(s,id,s->timeUs,&flux);
    const FlowThicknessTriangle*t=&s->flowThicknessTriangles[index];double weight=(1-u-v)*t->weight[0]+u*t->weight[1]+v*t->weight[2];
    return nrScale(s->flowThickness[id-1].direction,(after-before)/span*weight);
}
