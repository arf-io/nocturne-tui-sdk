#include "internal.h"

static int fail(NrContext*c,const char*m){size_t n=strlen(m);if(n>=sizeof(c->error))n=sizeof(c->error)-1;memcpy(c->error,m,n);c->error[n]=0;return -1;}
static int bounded(double x,double a,double b){return x>=a&&x<=b;}
static int choice(const Json*j,int owner,const char*key,const char*const*names,int count,uint32_t*out){int t=nrField(j,owner,key);if(t<0)return 1;for(int k=0;k<count;k++)if(nrEqual(j,t,names[k])){*out=k;return 1;}return 0;}
static int number(const Json*j,int owner,const char*key,double*out,double lo,double hi){int t=nrField(j,owner,key);return t<0||(nrNumber(j,t,out)&&bounded(*out,lo,hi));}
static int color(const Json*j,int owner,const char*key,uint32_t*out){int t=nrField(j,owner,key);if(t<0)return 1;char text[8];if(nrString(j,t,text,sizeof(text))!=7||text[0]!='#')return 0;uint32_t rgb=0;for(int i=1;i<7;i++){int v=text[i]>='0'&&text[i]<='9'?text[i]-'0':text[i]>='a'&&text[i]<='f'?text[i]-'a'+10:text[i]>='A'&&text[i]<='F'?text[i]-'A'+10:-1;if(v<0)return 0;rgb=(rgb<<4)|(uint32_t)v;}*out=rgb;return 1;}
static void cursorDefaults(PromptAppearance*q){q->cursorConfigured=1;q->cursorShape=5;q->cursorGlyph=0x2502;q->cursorColor=0xa3cabe;q->cursorColor2=0xc7aed7;q->colorMode=0;q->blinkMs=600;q->duty=.5;q->colorPeriodMs=2000;}
static void clearCursor(PromptAppearance*q){q->cursorConfigured=q->cursorShape=q->cursorGlyph=q->cursorColor=q->cursorColor2=q->colorMode=0;q->blinkMs=q->duty=q->colorPeriodMs=0;}
static void weatherDefaults(PromptAppearance*q){q->weatherConfigured=1;q->weatherStyle=0;q->weatherIntensity=.65;q->weatherLifeMs=1600;q->weatherSpeed=12;q->pastePolicy=0;}
int nrValidPromptAppearance(const State*s){
 const PromptAppearance*q=&s->promptAppearance;
 if(q->cursorConfigured>1||q->weatherConfigured>1||q->cursorShape>7||q->colorMode>2||q->weatherStyle>6||q->pastePolicy>2||q->eventCount>64||q->eventSerial>9007199254740991ull)return 0;
 if(q->cursorConfigured){if(q->cursorColor>0xffffff||q->cursorColor2>0xffffff||q->cursorGlyph<32||q->cursorGlyph>0x10ffff||(q->cursorGlyph>=0xd800&&q->cursorGlyph<=0xdfff)||q->cursorGlyph==127||!(q->blinkMs==0||bounded(q->blinkMs,40,60000))||!bounded(q->duty,0,1)||!bounded(q->colorPeriodMs,40,60000))return 0;}
 else if(q->cursorShape||q->cursorGlyph||q->cursorColor||q->cursorColor2||q->colorMode||q->blinkMs||q->duty||q->colorPeriodMs)return 0;
 if(q->weatherConfigured){if(!bounded(q->weatherIntensity,0,1)||!bounded(q->weatherLifeMs,200,8000)||!bounded(q->weatherSpeed,1,50))return 0;}
 else if(q->weatherStyle||q->weatherIntensity||q->weatherLifeMs||q->weatherSpeed||q->pastePolicy||q->eventCount||q->eventSerial)return 0;
 for(uint32_t k=0;k<64;k++){const NrSourceWeatherEvent*e=&q->events[k];if(k<q->eventCount){if(e->kind>5||!bounded(e->id,1,(double)q->eventSerial)||!bounded(e->x,-100000,100000)||!bounded(e->y,-100000,100000)||!bounded(e->atMs,0,(double)s->timeUs/1000))return 0;}else{NrSourceWeatherEvent z={0};if(memcmp(e,&z,sizeof(z)))return 0;}}
 return 1;
}
int nrPromptAppearanceCommand(NrContext*c,State*s,const Json*j){
 if(!nrAllowed(j,0,"op cursor weather"))return fail(c,"Unknown prompt appearance field");
 PromptAppearance q=s->promptAppearance;int at=nrField(j,0,"cursor");
 if(at>=0){
  if(!nrAllowed(j,at,"shape glyph color secondaryColor blinkMs duty colorMode colorPeriodMs"))return fail(c,"Unknown cursor field");
  if(!q.cursorConfigured)cursorDefaults(&q);
  static const char*shapes[]={"inherit","none","block","half","underline","bar","braille","custom"};static const char*colors[]={"fixed","pulse","cycle"};
  if(!choice(j,at,"shape",shapes,8,&q.cursorShape)||!choice(j,at,"colorMode",colors,3,&q.colorMode)||!color(j,at,"color",&q.cursorColor)||!color(j,at,"secondaryColor",&q.cursorColor2)||!number(j,at,"blinkMs",&q.blinkMs,0,60000)||!(q.blinkMs==0||q.blinkMs>=40)||!number(j,at,"duty",&q.duty,0,1)||!number(j,at,"colorPeriodMs",&q.colorPeriodMs,40,60000))return fail(c,"Invalid cursor setting");
  int g=nrField(j,at,"glyph");if(g>=0){uint32_t glyph[2];if(nrDecode(j,g,glyph,2)!=1||glyph[0]<32||glyph[0]==127)return fail(c,"Cursor glyph must be one printable Unicode scalar");q.cursorGlyph=glyph[0];}
  if(!q.cursorShape)clearCursor(&q);
 }
 at=nrField(j,0,"weather");if(at>=0){
  if(!nrAllowed(j,at,"style intensity lifeMs speed paste"))return fail(c,"Unknown typing weather field");
  if(!q.weatherConfigured)weatherDefaults(&q);
  static const char*styles[]={"off","embers","sparks","nova","rain","snow","ripples"};static const char*pastes[]={"each","burst","off"};
  if(!choice(j,at,"style",styles,7,&q.weatherStyle)||!choice(j,at,"paste",pastes,3,&q.pastePolicy)||!number(j,at,"intensity",&q.weatherIntensity,0,1)||!number(j,at,"lifeMs",&q.weatherLifeMs,200,8000)||!number(j,at,"speed",&q.weatherSpeed,1,50))return fail(c,"Invalid typing weather setting");
  if(!q.weatherStyle){q.eventCount=0;memset(q.events,0,sizeof(q.events));}
 }
 s->promptAppearance=q;return 0;
}
int nrPromptAppearanceInput(State*s,int start,int count,int origin){
 PromptAppearance*q=&s->promptAppearance;if(!q->weatherConfigured)return 0;
 if(!q->weatherStyle||!count||q->weatherIntensity==0||(origin==2&&q->pastePolicy==2))return 1;
 const Prompt*p=&s->promptDocument;int(*positions)[2]=(int(*)[2])(s->dynamicPrompt.scratch+57*((size_t)s->dynamicPrompt.capacity+1));nrPromptCoordinates(s,positions);
 int first=count>64?count-64:0;if(origin==2&&q->pastePolicy==1)first=count-1;
 for(int i=first;i<count;i++){int index=start+i;if(index<0||index>=p->count||p->glyphs[index]==10||p->glyphs[index]==13)continue;
  int x=positions[index][0],y=positions[index][1];if(x<0||x>=(int)s->width||y<0||y>=(int)s->height){x=positions[p->caret][0];y=positions[p->caret][1];}if(x<0)x=0;if(x>=(int)s->width)x=(int)s->width-1;if(y<0)y=0;if(y>=(int)s->height)y=(int)s->height-1;
  if(q->eventSerial>=9007199254740991ull)break;
  if(q->eventCount==64){memmove(q->events,q->events+1,63*sizeof(*q->events));q->eventCount--;}
  NrSourceWeatherEvent*e=&q->events[q->eventCount++];memset(e,0,sizeof(*e));e->kind=q->weatherStyle-1;e->id=(double)++q->eventSerial;e->x=x;e->y=y;e->atMs=(double)s->timeUs/1000;
 }
 return 1;
}
void nrPromptAppearanceWeather(NrContext*c){
 const State*s=nrView(c);const PromptAppearance*q=&s->promptAppearance;if(!q->weatherConfigured||!q->weatherStyle||!q->eventCount||!q->weatherIntensity)return;
 NrSourceWeatherOptions options;nrSourceWeatherDefaults(&options);options.lifeMs=q->weatherLifeMs;options.launchSpeed=q->weatherSpeed;if(s->reducedMotion){options.launchSpeed=1;options.brightness*=.5;}
 uint32_t wheel[360];for(int i=0;i<360;i++)wheel[i]=nrHueShift(0xf1ad80,(double)i);
 nrSourceWeatherPaintLayer(q->events,q->eventCount,(double)s->timeUs/1000,&options,q->weatherIntensity,1,0,wheel,s->width,s->height,(uint32_t*)c->cells);
}
void nrPromptAppearanceCursor(NrContext*c,const State*s,int x,int y){
 const PromptAppearance*q=&s->promptAppearance;if(!q->cursorConfigured||q->cursorShape<=1||x<0||y<0||x>=(int)s->width||y>=(int)s->height)return;
 double ms=(double)s->timeUs/1000;if(!s->reducedMotion&&q->blinkMs>0){double phase=ms-q->blinkMs*nrFloor(ms/q->blinkMs);if(phase>=q->blinkMs*q->duty)return;}
 uint32_t rgb=q->cursorColor;if(!s->reducedMotion&&q->colorMode){double phase=ms/q->colorPeriodMs;rgb=q->colorMode==1?nrMix(q->cursorColor,q->cursorColor2,.5-.5*nrCos(phase*2*NR_PI)):nrHueShift(q->cursorColor,phase*360);}
 static const uint32_t glyphs[]={32,32,0x2588,0x258c,0x2581,0x2502,0x2801,32};uint32_t glyph=q->cursorShape==7?q->cursorGlyph:glyphs[q->cursorShape];
 if(q->cursorShape==6&&!s->reducedMotion){static const uint32_t dots[]={0x2801,0x2808,0x2810,0x2820,0x2880,0x2840,0x2804,0x2802};glyph=dots[((uint64_t)ms/100)%8];}
 nrIndexedGlyph(c,x,y,glyph,rgb,1,NR_ID_PROMPT,(uint32_t)s->promptDocument.caret);
}

void nrPromptAppearanceApplication(NrContext*c,const State*s){
 if(!s->windowApplication.enabled||!s->promptAppearance.cursorConfigured)return;
 const Prompt*p=&s->promptDocument;int y=(int)s->height-4;
 if(y<0)return;
 /* An explicit caret override owns the application draft row as well. */
 for(int x=5;x<(int)s->width-4;x++){
  NrCell*cell=&c->cells[(size_t)y*s->width+x];cell->glyph=32;cell->foreground=cell->background;
 }
 int(*positions)[2]=(int(*)[2])s->dynamicPrompt.scratch;nrPromptCoordinates(s,positions);
 uint32_t owner=c->characterOwner;c->characterOwner=1u<<16;
 for(int i=0;i<p->count;i++){
  int x=positions[i][0];if(positions[i][1]!=y||x<5||x>=(int)s->width-4)continue;
  uint32_t glyph=p->glyphs[i];if(glyph==9||glyph==10||glyph==13)glyph=32;
  nrIndexedGlyph(c,x,y,glyph,0xe4dacc,1,NR_ID_PROMPT,(uint32_t)i);
 }
 nrPromptAppearanceCursor(c,s,positions[p->caret][0],positions[p->caret][1]);c->characterOwner=owner;
}
