#include "internal.h"
/* Bounded atan2 approximation for authored camera orientation, no host libm. */
static double angle(double y,double x) {
    if(nrAbs(x)+nrAbs(y)<1e-12)return 0;
    double a=nrAbs(y)+1e-14,r,theta;
    if(x>=0) {
        r=(x-a)/(x+a);
        theta=45;
    }
    else {
        r=(x+a)/(a-x);
        theta=135;
    }
    theta+=(.1963*r*r-.9817)*r*180/NR_PI;
    return y<0?-theta:theta;
}
static Camera sampleMotion(Camera from,const Motion*m,double t) {
    Camera result=from;
    double total=m->durationUs/1e6,u=nrClamp(t/total,0,1);
    if(m->kind>=5) {
        Vec3 d=nrSub(from.position,m->target);
        double radial=nrSqrt(d.x*d.x+d.z*d.z);
        if(radial<.01)radial=m->radius;
        double start=angle(d.x,d.z),rotation=m->yaw?m->yaw:360;
        double r=radial+(m->radius-radial)*nrEase(u*5,3);
        if(m->kind==6)r*=1+u*1.8;
        if(m->kind==7)r*=1-u*.8;
        double a=start+rotation*u;
        result.position=nrAdd(m->target,nrV(nrSin(a)*r,d.y+nrSin(u*180)*m->pitch*.2,nrCos(a)*r));
        Vec3 f=nrSub(m->target,result.position);
        double targetYaw=angle(f.x,-f.z),diff=targetYaw-from.yaw;
        while(diff>180)diff-=360;
        while(diff< -180)diff+=360;
        result.yaw=from.yaw+diff*nrEase(u*8,3);
        result.pitch=nrClamp(angle(f.y,nrSqrt(f.x*f.x+f.z*f.z)),-89,89);
        result.roll=from.roll+nrSin(u*180)*m->bank;
        return result;
    }
    double yawDelta=m->kind==1?m->yaw:0,pitchDelta=m->kind==2?nrAbs(m->pitch):m->kind==3?-nrAbs(m->pitch):0;
    /* Position integral has a fixed quadrature independent of presentation count. */
    Vec3 distance=nrV(0,0,0);
    const int n=32;
    for(int i=0; i<=n; i++) {
        double v=u*i/n;
        Camera a=from;
        a.yaw+=yawDelta*nrEase(v,3);
        a.pitch=nrClamp(a.pitch+pitchDelta*nrEase(v,3),-89,89);
        Vec3 r,up,f;
        nrBasis(&a,&r,&up,&f);
        double w=(i==0||i==n)?1:(i&1)?4:2;
        distance=nrAdd(distance,nrScale(f,w));
    }
    distance=nrScale(distance,total*u*m->speed/(3*n));
    result.position=nrAdd(from.position,distance);
    result.yaw=from.yaw+yawDelta*nrEase(u,3);
    result.pitch=nrClamp(from.pitch+pitchDelta*nrEase(u,3),-89,89);
    result.roll=from.roll+(m->kind==4?m->roll*nrEase(u,3):m->coordinated?m->bank*nrSin(u*180):0);
    return result;
}
/* Camera path travel owns the carrier position while its actor exists. */
int nrCameraPathOwned(const State*s){for(int i=0;i<16;i++)if(s->pathActors[i].used&&!s->pathActors[i].family)return 1;return 0;}
Camera nrCameraCarrierAtTime(const State*s,uint64_t timeUs) {
    if(nrCameraPathOwned(s))return s->camera;
    if(!s->flight.count&&!s->originalCamera.flightKind)return s->camera;
    Camera c=s->originalCamera.flightKind?nrOriginalCameraAtTime(s,timeUs):s->flight.origin;
    uint64_t elapsed=timeUs>s->flight.startUs?timeUs-s->flight.startUs:0;
    for(int i=0; i<s->flight.count; i++) {
        const Motion*m=&s->flight.steps[i];
        uint64_t dt=elapsed<m->durationUs?elapsed:m->durationUs;
        c=sampleMotion(c,m,dt/1e6);
        if(elapsed<=m->durationUs)break;
        elapsed-=m->durationUs;
    }
    c.yaw+=s->flight.look.x;
    c.pitch=nrClamp(c.pitch+s->flight.look.y,s->schema>=NR_STATE_SCHEMA_CAMERA_CONTROLS?-90:-89.9,s->schema>=NR_STATE_SCHEMA_CAMERA_CONTROLS?90:89.9);
    c.roll+=s->flight.look.z;
    return c;
}
Camera nrCameraCarrierAt(const State*s){return nrCameraCarrierAtTime(s,s->timeUs);}
Camera nrCameraAtTime(const State*s,uint64_t timeUs){return nrCameraControlsCompose(s,nrCameraCarrierAtTime(s,timeUs),timeUs);}
Camera nrCameraAt(const State*s){return nrCameraAtTime(s,s->timeUs);}
double nrWindowVisibility(const Window*w,uint64_t now) {
    double p=w->durationUs?nrClamp((double)(now>=w->atUs?now-w->atUs:0)/w->durationUs,0,1):1;
    return w->fromVisibility+(w->target-w->fromVisibility)*nrEase(p,3);
}
Vec3 nrNodeAt(const Node*n,uint64_t now) {
    double p=n->durationUs?nrClamp((double)(now>=n->atUs?now-n->atUs:0)/n->durationUs,0,1):1;
    return nrAdd(n->from,nrScale(nrSub(n->to,n->from),nrEase(p,4)));
}
void nrGraphLayout(State*s,int dims,int mode,double spacing,int iterations) {
    memset(&s->sourceGraphLayout,0,sizeof(s->sourceGraphLayout));
    int n=0,indices[NR_MAX_NODES],rank[NR_MAX_NODES]= {
        0
    },indeg[NR_MAX_NODES]= {
        0
    },queue[NR_MAX_NODES],head=0,tail=0;
    for(int i=0; i<(int)NR_MAX_NODES; i++)if(s->nodes[i].used)indices[n++]=i;
    /* Card measurements are cells, not world units. Convert once at the authored
       camera/depth; do not let a distant camera collapse fixed-size readable cards. */
    Projection projection;int availableH=(int)s->height-nrPromptRows(s)-3;if(availableH<6)availableH=6;
    int viewportWidth=(int)s->width;
    if(s->canvasPresentation||s->sceneArt.used||s->promptFramed.enabled)nrSceneViewport(s,&viewportWidth,&availableH);
    nrProjection(s,viewportWidth,availableH,&projection);
    double depth=nrDot(nrSub(nrV(0,12,0),projection.position),projection.forward);
    if(depth<projection.nearPlane*2)depth=projection.nearPlane*2;
    double scale=projection.orthographic?projection.scale:projection.focal/depth;
    double measuredX=spacing*1.5,measuredY=spacing*.65;
    for(int k=0;k<n;k++){const Node*node=&s->nodes[indices[k]];double w=(nrNodeWidth(node)+4)*2/scale,h=(nrNodeHeight(node,nrNodeWidth(node))+2)*4/scale;if(w>measuredX)measuredX=w;if(h>measuredY)measuredY=h;}
    s->dimensions=dims;
    s->layoutMode=mode;
    s->cycleCount=0;
    if(!n)return;
    for(int e=0; e<s->edgeCount; e++) {
        int t=nrFindNode(s,s->edges[e].to);
        if(t>=0)indeg[t]++;
    }
    for(int k=0; k<n; k++)if(!indeg[indices[k]])queue[tail++]=indices[k];
    while(head<tail) {
        int i=queue[head++];
        for(int e=0; e<s->edgeCount; e++)if(s->edges[e].from==s->nodes[i].id) {
            int t=nrFindNode(s,s->edges[e].to);
            if(t>=0) {
                if(rank[t]<rank[i]+1)rank[t]=rank[i]+1;
                if(--indeg[t]==0)queue[tail++]=t;
            }
        }
    }
    s->cycleCount=n-tail;
    int maxRank=0;
    for(int k=0; k<n; k++) {
        int i=indices[k];
        if(indeg[i])rank[i]=1;
        if(rank[i]>maxRank)maxRank=rank[i];
    }
    int totals[NR_MAX_NODES]= {
        0
    },current[NR_MAX_NODES]= {
        0
    };
    for(int k=0; k<n; k++)totals[rank[indices[k]]]++;
    for(int k=0; k<n; k++) {
        Node*a=&s->nodes[indices[k]];
        a->from=nrNodeAt(a,s->timeUs);
        a->atUs=s->timeUs;
        a->durationUs=800000;
        Vec3 target;
        if(mode==2) {
            double angle0=k*360.0/n;
            double r=spacing*(1+rank[indices[k]]*.7);
            target=nrV(nrCos(angle0)*r,nrSin(angle0)*r*.65,dims==3?(rank[indices[k]]-maxRank*.5)*spacing*.4:0);
        }
        else if(mode==1) {
            target=nrV((nrRandom(s->seed,a->id,1)-.5)*spacing*n*.4,(nrRandom(s->seed,a->id,2)-.5)*spacing*n*.3,dims==3?(nrRandom(s->seed,a->id,3)-.5)*spacing*n*.2:0);
        }
        else {
            int r=rank[indices[k]],col=current[r]++;
            target=nrV((col-(totals[r]-1)*.5)*measuredX,12+(maxRank*.5-r)*measuredY,dims==3?(r%2)*spacing*.2:0);
        }
        a->to=a->pinned?a->position:target;
        a->position=a->to;
    }
    if(mode==1)for(int step=0; step<iterations; step++) {
        Vec3 delta[NR_MAX_NODES]= {
            {
                0
            }
        };
        for(int a=0; a<n; a++) {
            Node*na=&s->nodes[indices[a]];
            for(int b=a+1; b<n; b++) {
                Node*nb=&s->nodes[indices[b]];
                Vec3 d=nrSub(na->to,nb->to);
                double dist=nrSqrt(nrDot(d,d))+.5;
                Vec3 f=nrScale(d,spacing*spacing/(dist*dist*dist)*.3);
                delta[a]=nrAdd(delta[a],f);
                delta[b]=nrSub(delta[b],f);
            }
        }
        for(int e=0; e<s->edgeCount; e++) {
            int a=-1,b=-1;
            for(int k=0; k<n; k++) {
                if(s->nodes[indices[k]].id==s->edges[e].from)a=k;
                if(s->nodes[indices[k]].id==s->edges[e].to)b=k;
            }
            if(a>=0&&b>=0) {
                Vec3 d=nrSub(s->nodes[indices[b]].to,s->nodes[indices[a]].to);
                double dist=nrSqrt(nrDot(d,d))+.1;
                Vec3 f=nrScale(d,(dist-spacing)*.015/dist);
                delta[a]=nrAdd(delta[a],f);
                delta[b]=nrSub(delta[b],f);
            }
        }
        for(int k=0; k<n; k++)if(!s->nodes[indices[k]].pinned) {
            Node*a=&s->nodes[indices[k]];
            a->to=nrAdd(a->to,delta[k]);
            a->position=a->to;
        }
    }
    s->selection=0;
}
int nrSelectNode(State*s,int id,uint64_t duration) {
    int selected=nrFindNode(s,id);
    if(id&&selected<0)return 0;
    s->selection=id;
    s->selectionScroll=0;
    int classes[NR_MAX_NODES]= {
        0
    },counts[5]= {
        0
    };
    if(id) {
        for(int e=0; e<s->edgeCount; e++) {
            if(s->edges[e].to==id) {
                int i=nrFindNode(s,s->edges[e].from);
                if(i>=0)classes[i]=1;
            }
            if(s->edges[e].from==id) {
                int i=nrFindNode(s,s->edges[e].to);
                if(i>=0)classes[i]=2;
            }
        }
        for(int i=0; i<(int)NR_MAX_NODES; i++)if(classes[i]==1)for(int e=0; e<s->edgeCount; e++)if(s->edges[e].from==s->nodes[i].id&&s->edges[e].to!=id) {
            int k=nrFindNode(s,s->edges[e].to);
            if(k>=0&&!classes[k])classes[k]=3;
        }
        classes[selected]=4;
    }
    for(int i=0; i<(int)NR_MAX_NODES; i++)if(s->nodes[i].used)counts[classes[i]]++;
    int positions[5]= {0};
    Projection projection;int availableH=(int)s->height-nrPromptRows(s)-3;if(availableH<6)availableH=6;
    int sceneWidth=(int)s->width-38;if(sceneWidth<20)sceneWidth=20;
    if(s->canvasPresentation||s->sceneArt.used||s->promptFramed.enabled)nrSceneViewport(s,&sceneWidth,&availableH);
    nrProjection(s,sceneWidth,availableH,&projection);
    double depth=nrDot(nrSub(nrV(0,8,0),projection.position),projection.forward);
    if(depth<35)depth=35;if(depth>10000)depth=10000;
    double scale=projection.orthographic?projection.scale:projection.focal/depth;
    int cardW=22,cardH=3;
    for(int i=0;i<(int)NR_MAX_NODES;i++)if(s->nodes[i].used){int w=nrNodeWidth(&s->nodes[i]),h=nrNodeHeight(&s->nodes[i],w);if(w>cardW)cardW=w;if(h>cardH)cardH=h;}
    int columns=sceneWidth/(cardW+4);if(columns<1)columns=1;
    int parentRows=(counts[1]+columns-1)/columns,childRows=(counts[2]+columns-1)/columns,siblingRows=(counts[3]+columns-1)/columns;
    for(int i=0; i<(int)NR_MAX_NODES; i++) {
        Node*n=&s->nodes[i];
        if(!n->used)continue;
        n->from=nrNodeAt(n,s->timeUs);
        n->atUs=s->timeUs;
        n->durationUs=duration;
        if(!id) {
            n->to=n->position;
            continue;
        }
        int type=classes[i],k=positions[type]++;
        /* Explicit world-space retargeting in the current view basis. Overflow
           stays spatially present and pannable; never duplicate shared nodes. */
        int row=0,cols=counts[type]<columns?counts[type]:columns;
        if(type==4){row=0;cols=1;k=0;}
        else if(type==1)row=-parentRows+k/columns;
        else if(type==2)row=1+k/columns;
        else if(type==3)row=1+childRows+k/columns;
        else row=1+childRows+siblingRows+k/columns;
        double sx=((k%columns)-(cols-1)*.5)*(cardW+4);
        double sy=(availableH*.36-availableH*.5)+row*(cardH+2);
        n->to=nrAdd(projection.position,nrAdd(nrScale(projection.forward,depth),nrAdd(nrScale(projection.right,sx*2/scale),nrScale(projection.up,-sy*4/scale))));
        if(n->pinned)n->to=n->position;
    }
    return 1;
}
