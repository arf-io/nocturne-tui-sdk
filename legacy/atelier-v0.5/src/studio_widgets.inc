/* Shared raster widgets. All language bindings consume identical node records. */
static uint32_t stNodeColor(const NsStageConfig *config,const NsNode *node,uint64_t t,int index){
 uint32_t c=(uint32_t)N(FG);
 if(N(COLOR_ANIMATION)==1)c=hsvI((int64_t)N(HUE_BASE)+(int64_t)index*N(HUE_STEP)+(int64_t)(t%360000)*N(HUE_SPEED)/1000,N(HUE_SATURATION),N(HUE_BRIGHTNESS));
 if(N(COLOR_ANIMATION)==2)c=stPalette(config,(int64_t)index*37+(int64_t)(t%360000)*N(HUE_SPEED)/350);
 if(N(COLOR_ANIMATION)==3)c=(uint32_t)nsOklchColor(N(HUE_BRIGHTNESS),N(HUE_SATURATION)*4,modI((int64_t)N(HUE_BASE)*1000+(int64_t)index*N(HUE_STEP)*1000+(int64_t)(t%360000)*N(HUE_SPEED),360000));
 return N(STATE)==3?mixI((uint32_t)S(BASE_COLOR),c,330):c;
}
static void stPut(const NsStageConfig *config,NsCell *cells,const NsNode *node,int x,int y,uint32_t g,uint32_t fg){
 if(x<0||y<0||x>=S(WIDTH)||y>=S(HEIGHT)||x<N(X)||y<N(Y)||x>=N(X)+N(WIDTH)||y>=N(Y)+N(HEIGHT)||!N(FG_OPACITY))return;
 NsCell *c=&cells[y*S(WIDTH)+x];c->bg=flattenedBg(c);c->fg=mixI(c->bg,fg,N(FG_OPACITY));c->glyph=stGlyph(g);if(N(ID))c->flags=(uint32_t)N(ID);
}
static void stFill(const NsStageConfig *config,NsCell *cells,const NsNode *node){
 int alpha=N(BG_OPACITY);if(!alpha)return;
 for(int y=clampI(N(Y),0,S(HEIGHT));y<clampI(N(Y)+N(HEIGHT),0,S(HEIGHT));y++)for(int x=clampI(N(X),0,S(WIDTH));x<clampI(N(X)+N(WIDTH),0,S(WIDTH));x++){
  NsCell *c=&cells[y*S(WIDTH)+x];uint32_t bg=mixI(flattenedBg(c),(uint32_t)N(BG),alpha);c->bg=bg;c->fg=mixI(c->fg,bg,alpha);if(alpha==1000)c->glyph=32;
 }
}
static void stText(const NsStageConfig *config,NsCell *cells,uint64_t t,const NsNode *node,int x,int y,const uint32_t *text){
 int start=x;uint64_t changed=stTime(&node->values[NTN_CHANGED_LO]),age=t>=changed?t-changed:0;
 uint32_t count=(uint32_t)N(TEXT_LENGTH);if(N(REVEAL_MS)>0&&age/(uint32_t)N(REVEAL_MS)<count)count=(uint32_t)(age/(uint32_t)N(REVEAL_MS));
 for(uint32_t k=0;k<count;k++){uint32_t g=text[(uint32_t)N(TEXT_OFFSET)+k];if(g=='\n'){x=start;y++;continue;}if(x>=N(X)+N(WIDTH)){x=start;y++;}if(y>=N(Y)+N(HEIGHT))break;stPut(config,cells,node,x++,y,g,stNodeColor(config,node,t,(int)k));}
}
static void stDot(const NsStageConfig *config,NsCell *cells,const NsNode *node,int px,int py,uint32_t fg){
 if(N(FG_OPACITY)==0||px<0||py<0||px>=N(WIDTH)*2||py>=N(HEIGHT)*4)return;
 int x=N(X)+px/2,y=N(Y)+py/4;if(x<0||y<0||x>=S(WIDTH)||y>=S(HEIGHT))return;
 static const uint32_t bits[8]={1,8,2,16,4,32,64,128};NsCell *c=&cells[y*S(WIDTH)+x];
 if(c->glyph<0x2800||c->glyph>0x28ff){c->bg=flattenedBg(c);c->glyph=0x2800;}
 c->glyph|=bits[(py%4)*2+px%2];c->fg=mixI(c->bg,fg,N(FG_OPACITY));if(N(ID))c->flags=N(ID);
}
static void stSegment(const NsStageConfig *config,NsCell *cells,const NsNode *node,int x0,int y0,int x1,int y1,uint32_t fg){
 int dx=stAbs(x1-x0),sx=x0<x1?1:-1,dy=-stAbs(y1-y0),sy=y0<y1?1:-1,err=dx+dy;
 for(int cap=0;cap<4096;cap++){stDot(config,cells,node,x0,y0,fg);if(x0==x1&&y0==y1)break;int e=err*2;if(e>=dy){err+=dy;x0+=sx;}if(e<=dx){err+=dx;y0+=sy;}}
}
static void stBox(const NsStageConfig *config,NsCell *cells,uint64_t t,const NsNode *node){
 if(N(WIDTH)<2||N(HEIGHT)<2)return;
 static const uint32_t styles[4][6]={{0x256d,0x256e,0x2570,0x256f,0x2500,0x2502},{0x250c,0x2510,0x2514,0x2518,0x2500,0x2502},{0x2554,0x2557,0x255a,0x255d,0x2550,0x2551},{0x250f,0x2513,0x2517,0x251b,0x2501,0x2503}};
 const uint32_t *g=styles[N(STYLE)%4];int x=N(X),y=N(Y),w=N(WIDTH),h=N(HEIGHT);
 for(int i=1;i<w-1;i++){stPut(config,cells,node,x+i,y,g[4],stNodeColor(config,node,t,i));stPut(config,cells,node,x+i,y+h-1,g[4],stNodeColor(config,node,t,w+h+i));}
 for(int j=1;j<h-1;j++){stPut(config,cells,node,x,y+j,g[5],stNodeColor(config,node,t,j));stPut(config,cells,node,x+w-1,y+j,g[5],stNodeColor(config,node,t,w+j));}
 stPut(config,cells,node,x,y,g[0],stNodeColor(config,node,t,0));stPut(config,cells,node,x+w-1,y,g[1],stNodeColor(config,node,t,w));stPut(config,cells,node,x,y+h-1,g[2],stNodeColor(config,node,t,h));stPut(config,cells,node,x+w-1,y+h-1,g[3],stNodeColor(config,node,t,w+h));
}
static int stSector(const int32_t *data,int count,int angle){
 if(count<1){return 0;}
 int64_t total=0;for(int i=0;i<count;i++)if(data[i]>0)total+=data[i];if(!total)return 0;
 int64_t target=(int64_t)angle*total,acc=0;for(int i=0;i<count;i++){if(data[i]>0)acc+=(int64_t)data[i]*1024;if(target<acc)return i;}return count-1;
}
static void stWidget(const NsStageConfig *config,NsCell *cells,uint64_t t,const NsNode *node,const uint32_t *text,const int32_t *allData){
 if(!N(WIDTH)||!N(HEIGHT))return;
 int x=N(X),y=N(Y),w=N(WIDTH),h=N(HEIGHT),kind=N(KIND);const int32_t *data=N(DATA_LENGTH)?allData+N(DATA_OFFSET):NULL;int count=N(DATA_LENGTH);
 uint64_t changed=stTime(&node->values[NTN_CHANGED_LO]),age=t>=changed?t-changed:0;
 int value=clampI(nsStageTween(N(FROM_VALUE),N(VALUE),age,(uint32_t)N(DURATION_MS),1),0,1000);
 stFill(config,cells,node);
 if(kind==NTK_TEXT){stText(config,cells,t,node,x,y,text);return;}
 if(kind==NTK_BOX||kind==NTK_BUTTON){stBox(config,cells,t,node);int tx=x+2,ty=kind==NTK_BUTTON?y+h/2:y;if(kind==NTK_BUTTON&&N(TEXT_LENGTH)<w-2)tx=x+(w-N(TEXT_LENGTH))/2;stText(config,cells,t,node,tx,ty,text);return;}
 if(kind==NTK_ITEM){uint32_t g=N(STATE)==2?0x25b6:N(STATE)==3?0xd7:N(STATE)==1?0x203a:0x25cb;stPut(config,cells,node,x,y,g,stNodeColor(config,node,t,0));stText(config,cells,t,node,x+2,y,text);return;}
 if(kind==NTK_RULE){
  int vertical=h>w,len=vertical?h:w;static const uint32_t sets[][4]={{0x2500,0x2500,0x2500,0x2500},{0x2501,0x2501,0x2501,0x2501},{0x2550,0x2550,0x2550,0x2550},{0xb7,0x22c5,0x2219,0xb7},{0x2801,0x2808,0x2810,0x2802},{0x2581,0x2582,0x2583,0x2582},{0x203a,0x203a,0x203a,32},{0x2580,0x2584,0x2580,0x2584},{0x2574,32,0x2576,32},{0x2571,0x2572,0x2571,0x2572},{32,0x2219,0x2022,0x2219},{0x25cb,0xb7,0x25cb,0xb7}};
  for(int i=0;i<len;i++){int style=N(STYLE)%12;uint32_t g=sets[style][modI((int64_t)i-(int64_t)(t/150),4)];if(vertical&&style<3)g=style==0?0x2502:style==1?0x2503:0x2551;stPut(config,cells,node,x+(vertical?0:i),y+(vertical?i:0),g,stNodeColor(config,node,t,i));}return;
 }
 if(kind==NTK_CURSOR){
  uint32_t color=stNodeColor(config,node,t,0);int pulse=(sinI((int64_t)(t%1600)*1024/1600)+1000)/2;
  uint32_t glyph=N(GLYPH)?(uint32_t)N(GLYPH):(N(STYLE)%5==0?0x2588:N(STYLE)%5==1?0x2581:N(STYLE)%5==2?0x258f:N(STYLE)%5==3?0x25b8:0x2800+(1u<<(t/120%8)));
  if(N(STYLE)%5==0&&x>=0&&y>=0&&x<S(WIDTH)&&y<S(HEIGHT)){NsCell *c=&cells[y*S(WIDTH)+x];if(c->glyph!=32&&c->glyph!=0x2580&&c->glyph!=0x258c){c->bg=mixI(flattenedBg(c),color,400+pulse/3);return;}}
  stPut(config,cells,node,x,y,glyph,mixI((uint32_t)S(BASE_COLOR),color,400+pulse*600/1000));return;
 }
 if(kind==NTK_PROGRESS){
  static const uint32_t blocks[9]={32,0x258f,0x258e,0x258d,0x258c,0x258b,0x258a,0x2589,0x2588};
  for(int i=0;i<w;i++){int q=clampI(value*w*8/1000-i*8,0,8);uint32_t g=N(STYLE)%3==1?(q?0x2584:0x2500):N(STYLE)%3==2?(q?0x25a0:0x25a1):blocks[q];stPut(config,cells,node,x+i,y+h/2,g,stNodeColor(config,node,t,i));}return;
 }
 if(kind==NTK_BARS){
  if(count<1){return;}
  int barW=w/count;if(barW<1)barW=1;
  for(int k=0;k<count&&k*barW<w;k++){int target=clampI(data[k],0,1000);int v=nsStageTween(0,target,age,(uint32_t)N(DURATION_MS),1);for(int j=0;j<h;j++){int fill=clampI(v*h*8/1000-(h-1-j)*8,0,8);for(int i=0;i<barW-(barW>2?1:0);i++)stPut(config,cells,node,x+k*barW+i,y+j,fill?0x2580+fill:32,stNodeColor(config,node,t,k*5+j));}}return;
 }
 if(kind==NTK_PIE||kind==NTK_DONUT){
  int64_t total=0;for(int k=0;k<count;k++)if(data[k]>0)total+=data[k];if(!total)return;
  int cx=w,cy=h*2,r=(w<h*2?w:h*2)-1;if(r<1)return;int reveal=nsStageTween(0,1024,age,(uint32_t)N(DURATION_MS),1);
  for(int py=0;py<h*4;py++)for(int px=0;px<w*2;px++){int dx=px-cx,dy=py-cy,rr=dx*dx+dy*dy;if(rr>r*r||(kind==NTK_DONUT&&rr<r*r*38/100))continue;int a=modI(stAngle(dx,dy)+256,1024);if(a>reveal)continue;int k=stSector(data,count,a);uint32_t color=count?stPalette(config,(int64_t)k*1024/(count?count:1)):stNodeColor(config,node,t,a/16);stDot(config,cells,node,px,py,color);}
  return;
 }
 if(kind==NTK_SCATTER){
  for(int k=0;k+1<count;k+=2){int px=clampI(data[k],0,1000)*(w*2-1)/1000,py=(1000-clampI(data[k+1],0,1000))*(h*4-1)/1000;uint32_t c=stNodeColor(config,node,t,k*7);stDot(config,cells,node,px,py,c);if(N(STYLE)%2){stDot(config,cells,node,px-1,py,c);stDot(config,cells,node,px+1,py,c);stDot(config,cells,node,px,py-1,c);stDot(config,cells,node,px,py+1,c);}}return;
 }
 if(kind==NTK_LINE||kind==NTK_EDGE){
  int points=kind==NTK_EDGE?count/2:count;if(points<1)return;int ox=0,oy=0;
  for(int k=0;k<points;k++){int px=kind==NTK_EDGE?clampI(data[k*2],0,1000)*(w*2-1)/1000:(points==1?0:k*(w*2-1)/(points-1));int py=kind==NTK_EDGE?clampI(data[k*2+1],0,1000)*(h*4-1)/1000:(1000-clampI(data[k],0,1000))*(h*4-1)/1000;uint32_t c=stNodeColor(config,node,t,k*2);if(k)stSegment(config,cells,node,ox,oy,px,py,c);else stDot(config,cells,node,px,py,c);ox=px;oy=py;}
  if(kind==NTK_EDGE&&points>=2){int phase=(int)(t%2400)*1000/2400,part=phase*(points-1)/1000,local=phase*(points-1)%1000;if(part>=points-1)part=points-2;int px=(data[part*2]+(data[(part+1)*2]-data[part*2])*local/1000)*(w*2-1)/1000;int py=(data[part*2+1]+(data[(part+1)*2+1]-data[part*2+1])*local/1000)*(h*4-1)/1000;stDot(config,cells,node,px,py,0xf2e6d4);stDot(config,cells,node,px+1,py,0xf2e6d4);}return;
 }
 if(kind==NTK_DIGITS){
  /* Original seven-segment geometry, not a distributed font asset. */
  static const unsigned masks[10]={119,36,93,109,46,107,123,37,127,111};int zoom=N(ZOOM);
  for(int k=0;k<N(TEXT_LENGTH);k++){uint32_t ch=text[N(TEXT_OFFSET)+k];int bx=x+k*5*zoom;unsigned mask=(ch>='0'&&ch<='9')?masks[ch-'0']:ch=='-'?8:0;
   for(int j=0;j<7;j++){if(!(mask&(1u<<j)))continue;int ax=j==1||j==4?0:j==2||j==5?3:1;int ay=j==0?0:j==1||j==2?1:j==3?2:j==4||j==5?3:4;int len=j==0||j==3||j==6?2:1;uint32_t g=j==0?0x2584:j==3?0x2584:j==6?0x2580:0x2588;
    for(int l=0;l<len;l++)for(int zy=0;zy<zoom;zy++)for(int zx=0;zx<zoom;zx++)stPut(config,cells,node,bx+(ax+l)*zoom+zx,y+ay*zoom+zy,g,stNodeColor(config,node,t,k*6+j));
   }
  }return;
 }
}
int32_t nsStageHit(const NsNode *nodes,uint32_t n,const int32_t *allData,uint32_t nd,int32_t x,int32_t y){
 if(n>NST_MAX_NODES||(n&&!nodes)||nd>NST_MAX_DATA||(nd&&!allData)||x<-4096||x>4096||y<-4096||y>4096)return -1;
 for(uint32_t i=0;i<n;i++){const NsNode *node=&nodes[i];if(N(WIDTH)<0||N(WIDTH)>512||N(HEIGHT)<0||N(HEIGHT)>256||N(X)<-4096||N(X)>4096||N(Y)<-4096||N(Y)>4096||N(DATA_OFFSET)<0||N(DATA_LENGTH)<0||(uint64_t)(uint32_t)N(DATA_OFFSET)+(uint32_t)N(DATA_LENGTH)>nd)return -1;}
 for(int i=(int)n-1;i>=0;i--){const NsNode *node=&nodes[i];if(!N(ID)||x<N(X)||y<N(Y)||x>=N(X)+N(WIDTH)||y>=N(Y)+N(HEIGHT))continue;
  if(N(STATE)==3){return 0;}
  int item=0,kind=N(KIND),count=N(DATA_LENGTH);const int32_t *data=count?allData+N(DATA_OFFSET):NULL;
  if(kind==NTK_PIE||kind==NTK_DONUT){int64_t total=0;for(int k=0;k<count;k++)if(data[k]>0)total+=data[k];if(!total)continue;int dx=(x-N(X))*2+1-N(WIDTH),dy=(y-N(Y))*4+2-N(HEIGHT)*2,r=(N(WIDTH)<N(HEIGHT)*2?N(WIDTH):N(HEIGHT)*2)-1,rr=dx*dx+dy*dy;if(r<1||rr>r*r||(kind==NTK_DONUT&&rr<r*r*38/100))continue;item=stSector(data,count,modI(stAngle(dx,dy)+256,1024));}
  else if(kind==NTK_BARS&&count){int bw=N(WIDTH)/count;if(bw<1)bw=1;item=(x-N(X))/bw;if(item>=count)continue;}
  else if(kind==NTK_LINE&&count){item=(x-N(X))*count/N(WIDTH);if(item>=count)item=count-1;}
  else if(kind==NTK_SCATTER&&count>=2){int best=2147483647;item=-1;for(int k=0;k+1<count;k+=2){int px=clampI(data[k],0,1000)*(N(WIDTH)*2-1)/1000,py=(1000-clampI(data[k+1],0,1000))*(N(HEIGHT)*4-1)/1000;int dx=(x-N(X))*2+1-px,dy=(y-N(Y))*4+2-py,d=dx*dx+dy*dy;if(d<best){best=d;item=k/2;}}if(best>36)continue;}
  return ((i+1)<<16)|(item+1);
 }
 return 0;
}
