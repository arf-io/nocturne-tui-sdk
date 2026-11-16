#include "internal.h"
#include "original_math.h"

static int bad(NrContext*c,const char*m){size_t n=strlen(m);if(n>255)n=255;memcpy(c->error,m,n);c->error[n]=0;return -1;}
static int bounded(double n,double lo,double hi){return n==n&&n>=lo&&n<=hi;}
static double tween(const NrAtelierTween*t,uint64_t now){double p=t->durationUs?nrClamp((double)(now>=t->atUs?now-t->atUs:0)/t->durationUs,0,1):1;return t->from+(t->to-t->from)*p*p*(3-2*p);}
double nrAtelierWindowTween(const State*s,int slot,int value){const SourceAtelierWindow*a=&s->atelierWindows[slot];const NrAtelierTween*t=value==0?&a->visibility:value==1?&a->maximize:value==2?&a->fade:&a->body;return s->reducedMotion?t->to:tween(t,nrWindowApplicationTimeUs(s));}
static void set(NrAtelierTween*t,double to,uint64_t now,uint64_t duration){t->from=tween(t,now);t->to=to;t->atUs=now;t->durationUs=duration;}
static int number(const Json*j,const char*key,double*out,double lo,double hi){int t=nrField(j,0,key);return t<0||(nrNumber(j,t,out)&&bounded(*out,lo,hi));}
static int integer(const Json*j,const char*key,uint32_t*out,uint32_t lo,uint32_t hi){int t=nrField(j,0,key);double n;if(t<0)return 1;if(!nrNumber(j,t,&n)||!bounded(n,lo,hi)||n!=(uint32_t)n)return 0;*out=(uint32_t)n;return 1;}
static int choice(const Json*j,const char*key,const char*const*names,int n,uint32_t*out){int t=nrField(j,0,key);if(t<0)return 1;for(int k=0;k<n;k++)if(nrEqual(j,t,names[k])){*out=k;return 1;}return 0;}
static int glyph(uint32_t g){return (g>=32&&g<=126)||(g>=161&&g<=767&&g!=173)||(g>=880&&g<=1023)||(g>=8208&&g<=8231)||(g>=8592&&g<=8959)||(g>=9472&&g<=9724)||(g>=10240&&g<=10495)||g==8962||g==8976||g==9733||g==9734||g==9744||g==9745||g==10022||g==10023||g==10038||g==10041;}
int nrAtelierWindowPatch(NrContext*c,State*s,const Json*j,int slot){
 SourceAtelierWindow*a=&s->atelierWindows[slot];int profile=nrField(j,0,"profile");
 if(profile>=0&&!nrEqual(j,profile,"atelier"))return bad(c,"Unknown generated window profile");
 if(!a->enabled&&profile<0)return 0;
 if(s->schema<NR_STATE_SCHEMA_ATELIER_WINDOWS)return bad(c,"Atelier content requires current schema");
 if(!a->enabled){Window*w=&s->windows[slot];if(!w->polygonCount){const double points[6][2]={{.05,.2},{.35,0},{.9,.12},{1,.8},{.65,1},{0,.85}};memcpy(w->polygon,points,sizeof(points));w->polygonCount=6;}memset(a,0,sizeof(*a));a->enabled=1;a->toolWidth=6;a->toolHeight=2;a->customSide=1;a->fadeFloor=.16;uint32_t gs[]={0x2013,0x25a1,0x25cc,0xd7},cs[]={0xe9bf65,0x7fd3ab,0xbb9ae5,0xef8b99};for(int i=0;i<4;i++){a->order[i]=i;a->glyphs[i]=gs[i];a->colors[i]=cs[i];}a->visibility.from=a->visibility.to=1;a->fade.from=a->fade.to=1;a->body.from=a->body.to=1;s->windowSourceOrder[slot]=slot+1;}
 static const char*chromes[]={"mac","windows","gnome","custom"},*sides[]={"left","right"};
 if(!choice(j,"chrome",chromes,4,&a->chrome)||!choice(j,"customSide",sides,2,&a->customSide)||!integer(j,"toolWidth",&a->toolWidth,5,10)||!integer(j,"toolHeight",&a->toolHeight,2,4)||!number(j,"fadeFloor",&a->fadeFloor,0,1))return bad(c,"Invalid Atelier tool control");
 int t=nrField(j,0,"customGlyphs");if(t>=0){if(j->tokens[t].type!=J_ARRAY||j->tokens[t].count!=4)return bad(c,"Four Atelier tool glyphs required");int i=0;for(int k=t+1;k<j->tokens[t].next;k=j->tokens[k].next){uint32_t g[2];if(nrDecode(j,k,g,2)!=1||!glyph(g[0]))return bad(c,"Invalid Atelier tool glyph");a->glyphs[i++]=g[0];}}
 t=nrField(j,0,"customOrder");if(t>=0){static const char*names[]={"minimize","maximize","fade","close"};if(j->tokens[t].type!=J_ARRAY||j->tokens[t].count!=4)return bad(c,"Four Atelier actions required");int i=0,mask=0;for(int k=t+1;k<j->tokens[t].next;k=j->tokens[k].next){int aidx=-1;for(int n=0;n<4;n++)if(nrEqual(j,k,names[n]))aidx=n;if(aidx<0||(mask&(1<<aidx)))return bad(c,"Invalid Atelier action order");mask|=1<<aidx;a->order[i++]=aidx;}}
 t=nrField(j,0,"toolColors");if(t>=0){static const char*names[]={"minimize","maximize","fade","close"};if(!nrAllowed(j,t,"minimize maximize fade close"))return bad(c,"Invalid Atelier tool colors");for(int k=0;k<4;k++){int token=nrField(j,t,names[k]);double n;if(token>=0){if(!nrNumber(j,token,&n)||!bounded(n,0,0xffffff)||n!=(uint32_t)n)return bad(c,"Invalid Atelier RGB");a->colors[k]=(uint32_t)n;}}}
 return 0;
}
int nrValidAtelierWindows(const State*s){
 for(int slot=0;slot<NR_MAX_WINDOWS;slot++){const SourceAtelierWindow*a=&s->atelierWindows[slot];if(!a->enabled){SourceAtelierWindow zero={0};if(memcmp(a,&zero,sizeof(zero)))return 0;continue;}
 if(a->enabled!=1||s->schema<NR_STATE_SCHEMA_ATELIER_WINDOWS||!s->windows[slot].used||!s->windowContent[slot].enabled||a->mode>2||a->rolled>1||a->chrome>3||a->customSide>1||a->toolWidth<5||a->toolWidth>10||a->toolHeight<2||a->toolHeight>4||a->reserved||s->windows[slot].width<30||s->windows[slot].width>120||s->windows[slot].height<16||s->windows[slot].height>120||!bounded(a->fadeFloor,0,1))return 0;
 int mask=0;for(int k=0;k<4;k++){if(a->order[k]>3||(mask&(1<<a->order[k]))||!glyph(a->glyphs[k])||a->colors[k]>0xffffff)return 0;mask|=1<<a->order[k];}
 const NrAtelierTween*t[]={&a->visibility,&a->fade,&a->maximize,&a->body};for(int k=0;k<4;k++)if(!bounded(t[k]->from,0,1)||!bounded(t[k]->to,0,1)||t[k]->atUs>s->timeUs||t[k]->durationUs>60000000)return 0;
 }return 1;
}
int nrAtelierWindowAction(State*s,int slot,int action){
 SourceAtelierWindow*a=&s->atelierWindows[slot];Window*w=&s->windows[slot];if(!a->enabled)return 0;uint64_t now=nrWindowApplicationTimeUs(s),duration=w->durationUs;
 if(action==0){set(&a->visibility,1,now,duration);set(&a->fade,1,now,duration);set(&a->body,1,now,duration);a->mode=0;a->rolled=0;}
 else if(action==1||action==2){set(&a->visibility,0,now,duration);a->mode=action==1?1:2;}
 else if(action==3){set(&a->maximize,w->maximized?0:1,now,duration);w->maximized=!w->maximized;set(&a->visibility,1,now,duration);a->mode=0;}
 else if(action==8||action==9){set(&a->body,action==8?0:1,now,duration);a->rolled=action==8;}
 else if(action==15)set(&a->fade,a->fade.to>.5?a->fadeFloor:1,now,duration);
 else return 0;
 w->target=a->visibility.to>0;w->reader=0;return 1;
}
static uint32_t mix(uint32_t a,uint32_t b,double t){t=nrClamp(t,0,1);uint32_t out=0;for(int k=0;k<24;k+=8){double av=(a>>k)&255,bv=(b>>k)&255;out|=(uint32_t)nrFloor(av*(1-t)+bv*t+.5)<<k;}return out;}
static uint32_t flat(const NrCell*v){return v->glyph==0x2580||v->glyph==0x2584||v->glyph==0x258c||v->glyph==0x2590?mix(v->foreground,v->background,.5):v->background;}
static void bg(NrCell*c,int width,int height,double x,double y,uint32_t color,double alpha,uint32_t id){x=nrFloor(x);y=nrFloor(y);if(x<0||y<0||x>=width||y>=height)return;int xx=(int)x,yy=(int)y;NrCell*v=&c[yy*width+xx];v->glyph=32;v->foreground=color;v->background=mix(v->background,color,alpha);v->id=id;}
static void put(NrCell*c,int width,int height,double x,double y,uint32_t g,uint32_t color,double alpha,uint32_t id){x=nrFloor(x);y=nrFloor(y);if(x<0||y<0||x>=width||y>=height)return;int xx=(int)x,yy=(int)y;NrCell*v=&c[yy*width+xx];uint32_t b=flat(v);*v=(NrCell){g,mix(b,color,alpha),b,id};}
static void text(NrCell*c,int width,int height,double x,double y,const uint32_t*t,int n,uint32_t color,double alpha,uint32_t id){for(int k=0;k<n;k++)put(c,width,height,x+k,y,t[k],color,alpha,id);}
static void ascii(NrCell*c,int width,int height,double x,double y,const char*t,uint32_t color,double alpha,uint32_t id,int limit){for(int k=0;t[k]&&k<limit;k++)put(c,width,height,x+k,y,(unsigned char)t[k],color,alpha,id);}
static void dot(NrCell*c,int width,int height,double px,double py,uint32_t color,double alpha,uint32_t id){int x=(int)nrFloor(px+.5),y=(int)nrFloor(py+.5);if(x<0||y<0||x>=width*2||y>=height*4)return;static const unsigned bits[]={1,8,2,16,4,32,64,128};NrCell*v=&c[(y/4)*width+x/2];if(v->glyph<0x2800||v->glyph>0x28ff){v->background=flat(v);v->glyph=0x2800;}v->glyph|=bits[y%4*2+x%2];v->foreground=mix(v->background,color,alpha);if(id)v->id=id;}
static const NrWindowPaletteSourcePrepared*palette(NrContext*c,int slot){const WindowContent*q=&nrView(c)->windowContent[slot];if(!c->windowPaletteValid[slot]||memcmp(&q->palette,&c->windowPaletteConfig[slot],sizeof(q->palette))){if(nrWindowPaletteSourcePrepare(&q->palette,&c->windowPalette[slot]))return 0;c->windowPaletteConfig[slot]=q->palette;c->windowPaletteValid[slot]=1;}return &c->windowPalette[slot];}
static uint32_t ink(const NrWindowPaletteSourcePrepared*p,double hue){uint32_t out=0;nrWindowPaletteSourceInk(p,hue,&out);return out;}
static uint32_t toolId(uint32_t id,int action){return id+(const uint32_t[]){NR_ID_MIN,NR_ID_MAX,NR_ID_WINDOW_RETURN,NR_ID_CLOSE}[action];}
static double maximum(double a,double b){return a>b?a:b;}static double minimum(double a,double b){return a<b?a:b;}
static int mask(const Window*w,double u,double v){double x=(u-.5)*2,y=(v-.5)*2;if(u<0||u>1||v<0||v>1)return 0;switch(w->shape){case 0:return 1;case 1:{double a=maximum(nrAbs(x)-.82,0),b=maximum(nrAbs(y)-.72,0);return a*a+b*b<=.0784;}case 2:return x*x+y*y<=1;case 3:return nrAbs(x)<=1-maximum(0,nrAbs(y)-.45)*.45;case 4:return nrAbs(x)+nrAbs(y)<=1;case 5:{double a=maximum(nrAbs(x)-.62,0)/.38;return a*a+y*y<=1;}case 10:return x*x/(.9*.9)+y*y/(.7*.7)<=1||(x+.48)*(x+.48)+(y+.28)*(y+.28)<.3||(x-.34)*(x-.34)+(y+.3)*(y+.3)<.38;case 6:return nrSqrt(u*u+(v-.5)*(v-.5))>.105&&nrSqrt((1-u)*(1-u)+(v-.5)*(v-.5))>.105;default:return nrWindowMask(w,u,v);}}
static int warp(const Window*w,double u,double v,double W,double H,double p,double*x,double*y,double*alpha){
 p=nrClamp(p,0,1);if(p<=0)return 0;double q=1-p,cx=(W-1)/2,cy=(H-1)/2,nx=(u-cx)/maximum(1,cx),ny=(v-cy)/maximum(1,cy);*x=u;*y=v;*alpha=1;int a=nrEffectAlgorithm(w->effect);
 switch(a){case 0:*alpha=p;break;case 9:case 10:case 11:case 12:case 13:{double ax=a==10||a==12?0:a==9||a==11||a==13?W-1:cx,ay=a==9||a==10||a==11?0:a==12||a==13?H-1:cy;*x=ax+(u-ax)*p;*y=ay+(v-ay)*p;*alpha=minimum(1,p*2);break;}
 case 14:if(nrSqrt(nx*nx+ny*ny)>1.4142135623730951*p)return 0;break;
 case 3:case 4:{double e=a==3?0:H-1;*y=e+(v-e)*p;if(v>1&&p<.08)return 0;*alpha=minimum(1,p*4);break;}
 case 5:case 6:case 7:case 8:if(a==5)*x=u-W*q;if(a==6)*x=u+W*q;if(a==7)*y=v-H*q;if(a==8)*y=v+H*q;if(*x<0||*x>=W||*y<0||*y>=H)return 0;break;
 case 1:{double s=p+nrOriginalSin(p*NR_PI)*w->overshoot;*x=cx+(u-cx)*s;*y=H-1+(v-H+1)*s;*alpha=minimum(1,p*3);break;}
 case 2:{double row=v/H,s=nrPowPositive(p,.5+row*1.4);*x=cx+(u-cx)*s+nrOriginalSin(row*NR_PI)*q*w->bend;*y=H-1+(v-H+1)*p;*alpha=minimum(1,p*3);break;}
 case 15:{uint32_t index=(uint32_t)(nrFloor(u/3)+nrFloor(v/2)*101);double r=nrHash(w->seed^((index+1u)*2654435769u))/4294967296.0;*x=u+nx*q*q*w->scatter+(r-.5)*q*6;*y=v+ny*q*q*w->scatter*.5+q*q*8;*alpha=p;break;}
 case 16:*x=cx+(u-cx)*p;*y=v+nrOriginalSin(u*.5)*q*3;*alpha=p;break;
 case 21:*x=cx+(u-cx)*nrOriginalCos(q*NR_PI/2);*y=v+nrAbs(nx)*nrOriginalSin(q*NR_PI)*H*.35*(nx<0?-1:1);*alpha=p;break;
 case 22:case 25:{double angle=q*NR_PI*(a==22?3:1),s=p*p,dx=u-cx,dy=(v-cy)*2;*x=cx+(dx*nrOriginalCos(angle)-dy*nrOriginalSin(angle))*s;*y=cy+(dx*nrOriginalSin(angle)+dy*nrOriginalCos(angle))*s*.5;*alpha=p;break;}
 case 23:{double t=nrClamp(p*1.6-v/H*.6,0,1);*x=cx+(u-cx)*t;*y=cy+(v-cy)*t+nrOriginalSin(v*.55+q*4)*q*3;*alpha=t;break;}
 case 24:{double angle=nrOriginalAtan2(ny,nx),petal=.78+.22*nrOriginalCos(angle*6),z=nrClamp(p/petal,0,1);*x=cx+(u-cx)*z;*y=cy+(v-cy)*z;*alpha=z;break;}}
 return 1;
}
typedef struct {const State*s;const Window*w;Camera camera;double W,H,visibility,bodyScale;Vec3 center;double cy,sy,cp,sp,cr,sr,anchorX,anchorY;int anchor;} Mapping;
static int map(const Mapping*m,double u,double v,double*x,double*y,double*z,double*alpha){double xx,yy;v=v<m->s->atelierWindows[m->w-m->s->windows].toolHeight?v:m->s->atelierWindows[m->w-m->s->windows].toolHeight+(v-m->s->atelierWindows[m->w-m->s->windows].toolHeight)*m->bodyScale;if(!warp(m->w,u,v,m->W,m->H,m->visibility,&xx,&yy,alpha))return 0;double dx=xx-m->W/2,dy=-(yy-m->H/2)*2,dz=0,a=dx*m->cy+dz*m->sy;dz=-dx*m->sy+dz*m->cy;dx=a;a=dy*m->cp-dz*m->sp;dz=dy*m->sp+dz*m->cp;dy=a;a=dx*m->cr-dy*m->sr;dy=dx*m->sr+dy*m->cr;dx=a;if(!nrWindowSourceProject(m->s,&m->camera,nrAdd(m->center,nrV(dx,dy,-dz)),x,y,z))return 0;if(m->anchor){*x+=m->anchorX*(1-m->visibility);*y+=m->anchorY*(1-m->visibility);}return 1;}
int nrDrawAtelierWindow(NrContext*c,int slot){
 const State*s=nrView(c);const Window*w=&s->windows[slot];const SourceAtelierWindow*a=&s->atelierWindows[slot];uint64_t now=nrWindowApplicationTimeUs(s);double visibility=s->reducedMotion?a->visibility.to:tween(&a->visibility,now);if(visibility<=0)return 1;double p=s->reducedMotion?a->maximize.to:tween(&a->maximize,now),fade=s->reducedMotion?a->fade.to:tween(&a->fade,now),body=s->reducedMotion?a->body.to:tween(&a->body,now);
 double baseH=w->height/2,baseX=w->position.x-w->width/2+s->width/2.0,baseY=s->height/2.0-w->position.y/2-baseH/2,x=baseX+(3-baseX)*p,y=baseY+(6-baseY)*p;int width=(int)maximum(30,nrFloor(w->width+(s->width-6-w->width)*p+.5)),height=(int)maximum(8,nrFloor(baseH+(s->height-15-baseH)*p+.5));
 size_t count=(size_t)width*height;if(count>7200&&count>(size_t)s->width*s->height*2)return 1;NrCell*local=count<=7200?(NrCell*)c->windowContentCells:(NrCell*)c->plotColor;const NrWindowPaletteSourcePrepared*pal=palette(c,slot);if(!pal)return 1;const WindowContent*content=&s->windowContent[slot];uint32_t bodyId=NR_ID_WINDOW+w->id;
 for(int yy=0;yy<height;yy++)for(int xx=0;xx<width;xx++)local[yy*width+xx]=(NrCell){32,content->palette.inkRgb,mix(content->palette.backgroundRgb,ink(pal,235+w->id*35),.07+yy/(double)height*.035),bodyId};
 int side=a->chrome==0||(a->chrome==3&&a->customSide==0);uint32_t gs[4]={0x2013,0x2197,0x25cc,0xd7};if(a->chrome==1){gs[0]='_';gs[1]=0x25a1;}if(a->chrome==2){gs[0]=0x2014;gs[1]=0x25a1;gs[2]=0x25d0;}if(a->chrome==3)memcpy(gs,a->glyphs,sizeof(gs));
 for(int i=0;i<4;i++){int action=a->chrome==3?a->order[i]:a->chrome==0?(i+3)%4:i;int tx=side?1+i*a->toolWidth:(int)maximum(1,width-1-(int)a->toolWidth*4)+i*a->toolWidth;uint32_t hit=toolId(w->id,action);for(int yy=0;yy<(int)a->toolHeight;yy++)for(int xx=tx;xx<tx+(int)a->toolWidth;xx++)bg(local,width,height,xx,yy,a->colors[action],.22,hit);put(local,width,height,tx+a->toolWidth/2,a->toolHeight/2,gs[action],a->colors[action],1,hit);}
 uint32_t title[192];int n=w->titleCount;memcpy(title,w->title,n*sizeof(uint32_t));if(s->selectedWindow==w->id){const char*suf=" / FOCUSED";while(*suf)title[n++]=(unsigned char)*suf++;}if(n>nrFloor(width*.68))n=(int)nrFloor(width*.68);text(local,width,height,maximum(2,nrFloor(width*.16)),a->toolHeight+1,title,n,ink(pal,190),1,0);
 for(int xx=2;xx<width-2;xx++)put(local,width,height,xx,a->toolHeight+3,0x2500,ink(pal,230+xx*2),.5,bodyId);
 if(w->id==1){for(int k=0;k<width-8;k++){double phase=k*.22+now/1000.0*.0013,yy=a->toolHeight+8+nrOriginalSin(phase)*2+nrOriginalSin(k*.67-phase*.6);dot(local,width,height,(4+k)*2,yy*4,ink(pal,170+k*2),.88,bodyId);}ascii(local,width,height,4,height-4,"PEARL / 60 Hz PRESENTATION",ink(pal,180),.9,bodyId,100);}else{const char*lines[]={"SOURCE     STATE        RATE","atlas      running      67/s","iris       evidence     12/s","pearl      synthesis    49/s"," Shared parents / one identity"};for(int k=0;k<5&&k<height-9;k++)ascii(local,width,height,3,a->toolHeight+6+k,lines[k],ink(pal,190+k*17),.85,bodyId,width-6);}
 Mapping m={.s=s,.w=w,.camera=nrCameraAt(s),.W=width,.H=height,.visibility=visibility,.bodyScale=body,.center={x+width/2.0-s->width/2.0,(s->height/2.0-y-height/2.0)*2,w->position.z*(1-p)}};double yaw=w->yaw*(1-p)*NR_PI/180,pitch=w->pitch*(1-p)*NR_PI/180,roll=w->roll*(1-p)*NR_PI/180;m.cy=nrOriginalCos(yaw);m.sy=nrOriginalSin(yaw);m.cp=nrOriginalCos(pitch);m.sp=nrOriginalSin(pitch);m.cr=nrOriginalCos(roll);m.sr=nrOriginalSin(roll);
 if(nrEffectAlgorithm(w->effect)==2){int windows=0,index=0;for(int k=0;k<NR_MAX_WINDOWS;k++)if(s->atelierWindows[k].enabled){if(s->windowContent[k].sourceIndex<content->sourceIndex)index++;windows++;}double ax,ay,az;if(nrWindowSourceProject(s,&m.camera,nrV(x+width/2.0-s->width/2.0,(s->height/2.0-y-height)*2,w->position.z*(1-p)),&ax,&ay,&az)){m.anchor=1;m.anchorX=3+(index+.5)*(s->width-6)/windows-ax;m.anchorY=s->height-6-ay;}}
 for(int pass=0;pass<2;pass++)for(int yy=0;yy<height;yy++)for(int xx=0;xx<width;xx++){if(body<.015&&yy>=(int)a->toolHeight)continue;if(yy>=(int)a->toolHeight&&!mask(w,(xx+.5)/width,(yy+.5)/height))continue;double px,py,z,alpha;if(!map(&m,xx+.5,yy+.5,&px,&py,&z,&alpha)||py<4||py>=(double)s->height-7||px< -3||px>=s->width+3)continue;const NrCell*v=&local[yy*width+xx];uint32_t hit=v->id?v->id:bodyId;if(pass){if(v->glyph!=32)put(c->cells,s->width,s->height,px,py,v->glyph,v->foreground,fade*alpha,hit);continue;}double ax,ay,az,aa,sx=1,sy=1;if(map(&m,xx+1.5,yy+1.5,&ax,&ay,&az,&aa)){sx=minimum(5,nrAbs(ax-px));sy=minimum(4,nrAbs(ay-py));}int y0=(int)nrFloor(py-sy/2+1e-7),y1=(int)maximum(y0,-nrFloor(-(py+sy/2-1e-7))-1),x0=(int)nrFloor(px-sx/2+1e-7),x1=(int)maximum(x0,-nrFloor(-(px+sx/2-1e-7))-1);for(int ry=y0;ry<=y1;ry++)for(int rx=x0;rx<=x1;rx++){if(ry<4||ry>=(double)s->height-7)continue;bg(c->cells,s->width,s->height,rx,ry,v->background,fade*w->alpha*alpha,hit);if(rx>=0&&rx<(int)s->width)c->windowDepth[(size_t)ry*s->width+rx]=z;}}
 return 1;
}
static double randomAt(uint32_t seed,uint32_t i){return nrHash(seed^((i+1u)*2654435769u))/4294967296.0;}
static uint32_t coordinateHash(int x,int y){char chars[32];int n=0;unsigned v=x;do{chars[n++]='0'+v%10;v/=10;}while(v);uint32_t h=2166136261u;while(n)h=(h^(unsigned char)chars[--n])*16777619u;h=(h^':')*16777619u;v=y;do{chars[n++]='0'+v%10;v/=10;}while(v);while(n)h=(h^(unsigned char)chars[--n])*16777619u;return nrHash(h);}
void nrAtelierApplicationStars(NrContext*c,const NrWindowPaletteSourcePrepared*p){const State*s=nrView(c);const WindowApplication*a=&s->windowApplication;double time=nrWindowApplicationTimeUs(s)/1000000.0;for(int y=4;y<(int)s->height-6;y++)for(int x=0;x<(int)s->width;x++){uint32_t seed=coordinateHash(x,y);if(randomAt(seed,0)>a->starDensity)continue;double period=3+randomAt(seed,2)*6,phase=time/period+randomAt(seed,3);phase-=nrFloor(phase);double alpha=nrOriginalSin(phase*NR_PI);alpha*=alpha;alpha*=alpha;alpha*=alpha;alpha*=.7;put(c->cells,s->width,s->height,x,y,a->starGlyphs[seed%a->starGlyphCount],ink(p,seed%360),alpha,0);}}
void nrAtelierApplicationChrome(NrContext*c){const State*s=nrView(c);int ps=nrFindWindow(s,s->windowApplication.paletteWindowId);if(ps<0)return;const NrWindowPaletteSourcePrepared*p=palette(c,ps);if(!p)return;int W=s->width,H=s->height,slots[NR_MAX_WINDOWS],count=0;for(int k=0;k<NR_MAX_WINDOWS;k++)if(s->atelierWindows[k].enabled)slots[count++]=k;for(int i=1;i<count;i++){int key=slots[i],j=i;while(j&&s->windowContent[slots[j-1]].sourceIndex>s->windowContent[key].sourceIndex){slots[j]=slots[j-1];j--;}slots[j]=key;}int size=count?(int)maximum(12,nrFloor((W-6)/(double)count)):12;
 for(int i=0;i<count;i++){int k=slots[i],x=3+i*size,y=H-7;const Window*w=&s->windows[k];const SourceAtelierWindow*a=&s->atelierWindows[k];uint32_t id=NR_ID_DOCK+w->id;for(int yy=y;yy<y+2;yy++)for(int xx=x;xx<W-2&&xx<x+size-1;xx++)bg(c->cells,W,H,xx,yy,s->selectedWindow==w->id?0x34464b:0x222230,.97,id);uint32_t title[164];title[0]=a->mode?0x25b1:0x25a3;title[1]=' ';memcpy(title+2,w->title,w->titleCount*sizeof(uint32_t));int n=w->titleCount+2;if(n>size-3)n=size-3;text(c->cells,W,H,x+1,y,title,n,ink(p,a->mode?55:185),1,id);ascii(c->cells,W,H,x+1,y+1,a->mode==0?"FOCUS / RESTORE":a->mode==1?"MINIMIZED / RESTORE":"CLOSED / RESTORE",ink(p,280),.65,id,100);}
 for(int y=0;y<4&&y<H;y++)for(int x=0;x<W;x++)bg(c->cells,W,H,x,y,0x0d0f17,1,0);for(int y=H-5;y<H;y++)for(int x=0;x<W;x++)bg(c->cells,W,H,x,y,0x10131d,1,0);
 ascii(c->cells,W,H,2,1,"NOCTURNE / SPATIAL ATELIER",ink(p,180),1,0,100);if(W>100){uint32_t textValue[64];int n=0;const char*pre="";while(*pre)textValue[n++]=*pre++;int fps=(int)nrFloor(s->windowApplication.fps+.5);if(fps>=100)textValue[n++]='0'+fps/100;if(fps>=10)textValue[n++]='0'+fps/10%10;textValue[n++]='0'+fps%10;const char*end=" FPS TARGET   OKLCh";while(*end)textValue[n++]=*end++;text(c->cells,W,H,W-54,1,textValue,n,ink(p,285),.85,0);}
 ascii(c->cells,W,H,2,3,"Windows, surfaces and tools.",ink(p,210),.65,0,W-4);put(c->cells,W,H,3,H-4,'>',ink(p,185),1,0);int countDraft=s->promptDocument.count,start=countDraft-maximum(1,W-10);if(start<0)start=0;for(int i=start;i<countDraft;i++)put(c->cells,W,H,5+i-start,H-4,s->promptDocument.glyphs[i],ink(p,(i-start)*13+s->windowContent[ps].palette.hueOffsetDegrees),1,0);put(c->cells,W,H,5+countDraft-start,H-4,0x258f,ink(p,180),1,0);ascii(c->cells,W,H,3,H-2,"SPACE pause on stage  /  H home  /  ? controls",ink(p,215),.52,0,W-6);for(size_t i=0;i<(size_t)W*H;i++)if(!glyph(c->cells[i].glyph))c->cells[i].glyph='?';
}

/* Original AtelierRenderer.particles uses the shared application event queue. */
static AtelierControls particleDefaults(void){return (AtelierControls){.used=1,.seed=4711,.count=64,.branches=7,.lifeMs=4200,.speed=20,.gravity=9,.rise=10,.drag=.22,.turbulence=1.3,.glitterHz=14,.trailMs=100,.jaggedness=2.2,.coreMs=280,.coreRadius=3,.ejecta=1,.shockwave=0,.intensity=.8};}
static int particleValid(const AtelierControls*b){
 if(b->used!=1||b->generation||b->eventId||b->reserved||b->startUs||b->count>256||b->branches<1||b->branches>20||b->reducedMotion>1)return 0;
 return bounded(b->lifeMs,200,10000)&&bounded(b->speed,0,70)&&bounded(b->gravity,0,35)&&bounded(b->rise,0,40)&&bounded(b->drag,0,3)&&bounded(b->turbulence,0,8)&&bounded(b->glitterHz,1,30)&&bounded(b->trailMs,0,400)&&bounded(b->jaggedness,0,8)&&bounded(b->coreMs,0,600)&&bounded(b->coreRadius,0,6)&&bounded(b->ejecta,0,2)&&bounded(b->shockwave,0,1)&&bounded(b->intensity,0,1);
}
int nrValidAtelierApplicationParticles(const State*s){const AtelierControls*b=&s->atelierApplicationParticles;if(!b->used){AtelierControls z={0};return !memcmp(b,&z,sizeof(z));}return s->schema>=NR_STATE_SCHEMA_ATELIER_APP_PARTICLES&&s->windowApplication.enabled&&particleValid(b);}
int nrAtelierApplicationParticlePatch(NrContext*c,State*s,const Json*j,int token){
 AtelierControls b=s->atelierApplicationParticles;if(!b.used)b=particleDefaults();
 if(token>=0){
  if(!nrAllowed(j,token,"lifeMs count speed gravity rise drag turbulence glitterHz trailMs branches jaggedness coreMs coreRadius ejecta shockwave intensity seed reducedMotion"))return bad(c,"Unknown Atelier particle control");
  struct F{const char*n;double*p;}fs[]={{"lifeMs",&b.lifeMs},{"speed",&b.speed},{"gravity",&b.gravity},{"rise",&b.rise},{"drag",&b.drag},{"turbulence",&b.turbulence},{"glitterHz",&b.glitterHz},{"trailMs",&b.trailMs},{"jaggedness",&b.jaggedness},{"coreMs",&b.coreMs},{"coreRadius",&b.coreRadius},{"ejecta",&b.ejecta},{"shockwave",&b.shockwave},{"intensity",&b.intensity}};
  for(unsigned k=0;k<sizeof(fs)/sizeof(fs[0]);k++){int t=nrField(j,token,fs[k].n);if(t>=0&&!nrNumber(j,t,fs[k].p))return bad(c,"Invalid Atelier particle number");}
  const char*names[]={"seed","count","branches"};uint32_t*values[]={&b.seed,&b.count,&b.branches};for(int k=0;k<3;k++){int t=nrField(j,token,names[k]);double d;if(t>=0){if(!nrNumber(j,t,&d)||!bounded(d,0,4294967295.0)||d!=(uint32_t)d)return bad(c,"Invalid Atelier particle integer");*values[k]=(uint32_t)d;}}
  int t=nrField(j,token,"reducedMotion"),motion=b.reducedMotion;if(t>=0&&!nrBoolean(j,t,&motion))return bad(c,"Invalid Atelier particle motion");b.reducedMotion=motion;
 }
 if(!particleValid(&b))return bad(c,"Atelier particle bounds");s->atelierApplicationParticles=b;return 0;
}
static uint32_t particleHeat(uint32_t kind,double heat){double q=nrFloor(nrClamp(heat,0,1)*127+.5)/127;double l=kind==0?520+q*340:kind==1?690+q*270:570+q*370;int c=kind==0?1600:kind==1?600:900;double h=kind==0?(20+q*42)*1000:kind==1?245000:(35+q*45)*1000;return nrWindowPaletteSourceFixedOklch((int32_t)nrFloor(l+.5),c,(int32_t)nrFloor(h+.5));}
static void particleLine(NrContext*c,double x0,double y0,double x1,double y1,uint32_t color,double alpha){
 const State*s=nrView(c);x0*=2;x1*=2;y0*=4;y1*=4;double dx=x1-x0,dy=y1-y0,lo=0,hi=1,ps[]={-dx,dx,-dy,dy},qs[]={x0,s->width*2.0-1-x0,y0,s->height*4.0-1-y0};
 for(int k=0;k<4;k++){if(!ps[k]&&qs[k]<0)return;if(!ps[k])continue;double v=qs[k]/ps[k];if(ps[k]<0)lo=maximum(lo,v);else hi=minimum(hi,v);if(lo>hi)return;}
 double ax=nrFloor(x0+lo*dx+.5),ay=nrFloor(y0+lo*dy+.5),bx=nrFloor(x0+hi*dx+.5),by=nrFloor(y0+hi*dy+.5),n=maximum(maximum(nrAbs(bx-ax),nrAbs(by-ay)),1);
 for(int k=0;k<=n;k++)dot(c->cells,s->width,s->height,ax+(bx-ax)*k/n,ay+(by-ay)*k/n,color,alpha,0);
}
static void particleEvent(NrContext*c,const NrSourceWeatherEvent*event,const AtelierControls*options,double time){
 const State*s=nrView(c);if(event->kind>5)return;AtelierControls b=*options;double integerId=event->id<0?-nrFloor(-event->id):nrFloor(event->id);integerId-=nrFloor(integerId/4294967296.0)*4294967296.0;b.eventId=(uint32_t)integerId;AtelierSample sample;static const int kinds[]={2,1,0,3,4,5};if(!nrAtelierSampleAt(&b,kinds[event->kind],time-event->atMs,&sample))return;
 for(uint32_t k=0;k<sample.glowCount;k++){const double*g=sample.glows[k];double gx=event->x+g[0],gy=event->y+g[1],r=minimum(120,g[2]);uint32_t color=nrWindowPaletteSourceFixedOklch((int32_t)nrFloor(660+g[4]*280+.5),700,(int32_t)nrFloor((25+g[4]*45)*1000+.5));
  double top=maximum(4,nrFloor(gy-r/2-2)),bottom=minimum((double)s->height-7,gy+r/2+2),left=maximum(0,nrFloor(gx-r-2)),right=minimum(s->width,gx+r+2);if(top>=bottom||left>=right)continue;
  for(int y=(int)top;y<bottom;y++)for(int x=(int)left;x<right;x++){
   double d=nrOriginalHypot(x-gx,(y-gy)*2,0),q;if(g[5]){double t=(d-r)/1.1;q=nrOriginalExp(-t*t);}else q=nrOriginalExp(-d*d/maximum(.1,r*r));NrCell*v=&c->cells[(size_t)y*s->width+x];v->background=mix(v->background,color,q*g[3]);if(v->glyph==0x2580)v->foreground=mix(v->foreground,color,q*g[3]);
  }
 }
 for(uint32_t k=0;k<sample.segmentCount;k++){const double*p=sample.segments[k];particleLine(c,event->x+p[0],event->y+p[1],event->x+p[2],event->y+p[3],particleHeat(event->kind,p[5]),p[4]);}
 for(uint32_t k=0;k<sample.pointCount;k++){const double*p=sample.points[k];double y=event->y+p[1];if(y>=4&&y<(double)s->height-7)put(c->cells,s->width,s->height,event->x+p[0],y,(uint32_t)p[2],particleHeat(event->kind,p[4]),p[3],0);}
}
void nrAtelierApplicationParticles(NrContext*c){
 const State*s=nrView(c);const WindowApplication*a=&s->windowApplication;if(a->scene!=2||s->schema<NR_STATE_SCHEMA_ATELIER_APP_PARTICLES)return;AtelierControls options=s->atelierApplicationParticles;if(!options.used)options=particleDefaults();double time=nrWindowApplicationTimeUs(s)/1000.0;int slots[128],count=0;
 for(uint32_t k=0;k<a->eventCount;k++)if(a->events[k].atMs<=time&&time-a->events[k].atMs<options.lifeMs)slots[count++]=k;
 for(int k=count>16?count-16:0;k<count;k++)particleEvent(c,&a->events[slots[k]],&options,time);
 if(a->novaRegularity>0){double period=60000/a->novaRegularity;uint32_t n=(uint32_t)nrFloor(time/period),first=n>1?n-1:1;for(uint32_t i=first;i<=n;i++)if(time-i*period<options.lifeMs){NrSourceWeatherEvent e={.kind=2,.id=900000+i,.x=10+randomAt(1,i)*((double)s->width-20),.y=8+randomAt(3,i)*((double)s->height-20),.atMs=i*period};particleEvent(c,&e,&options,time);}}
}
