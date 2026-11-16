/* Prompt material kernel with current document/state ownership. */
#include "internal.h"
#define nsDefaultConfig nrFirstSourceDefaults
#define nsValidateConfig nrFirstSourceValidate
#define nsRender nrFirstSourceRender
#define nsRowPeriod nrFirstSourceRowPeriod
#define nsRowSaturation nrFirstSourceRowSaturation
#define nsAbiVersion nrFirstSourceAbiVersion
#define nsConfigSize nrFirstSourceConfigSize
#define nsCellSize nrFirstSourceCellSize
#include "first_prompt_kernel.inc"
_Static_assert(sizeof(NsConfig)==448,"Prompt config layout");
_Static_assert(sizeof(NsCell)==sizeof(NrCell),"Prompt cell layout");
_Static_assert(sizeof(*((NrContext*)0)->plotColor)>=sizeof(NrCell),"A viewport row of prompt cells fits plot scratch");
_Static_assert(sizeof(*((NrContext*)0)->plotColor)>=2*sizeof(NrCell),"A layer rectangle and a protected row of cells fit plot scratch together");
static int fail(NrContext*c,const char*m){size_t n=strlen(m);if(n>=sizeof(c->error))n=sizeof(c->error)-1;memcpy(c->error,m,n);c->error[n]=0;return -1;}
static void config(const State*s,NsConfig*q){memcpy(q,s->firstPromptSource.values,sizeof(*q));q->values[NS_WIDTH]=(int32_t)s->width;q->values[NS_HEIGHT]=(int32_t)s->height;}
/* The layer rectangle in grid cells, resolved from current state (placement 0 is the whole viewport).
 * Returns 0 when nothing is placed: an inactive prompt, a removed widget or a rectangle off the grid. */
static int clipRect(const State*s,int64_t x,int64_t y,int64_t w,int64_t h,int*ox,int*oy,int*ow,int*oh){
 int64_t r=x+w,b=y+h;if(x<0)x=0;if(y<0)y=0;if(r>(int64_t)s->width)r=s->width;if(b>(int64_t)s->height)b=s->height;
 if(r<=x||b<=y)return 0;*ox=(int)x;*oy=(int)y;*ow=(int)(r-x);*oh=(int)(b-y);return 1;
}
int nrFirstPromptViewport(const State*s,int*x,int*y,int*w,int*h){
 const PromptSourceLayer*l=&s->promptSourceLayer;*x=*y=*w=*h=0;
 if(!s->firstPromptSource.enabled)return 0;
 if(l->placement==NR_PROMPT_SOURCE_CELLS)return clipRect(s,l->x,l->y,l->width,l->height,x,y,w,h);
 if(l->placement==NR_PROMPT_SOURCE_PROMPT){int px,py,pw,ph;return nrPromptFrameRect(s,&px,&py,&pw,&ph)&&clipRect(s,px,py,pw,ph,x,y,w,h);}
 if(l->placement==NR_PROMPT_SOURCE_WIDGET){for(int i=0;i<NR_WIDGETS;i++){const Widget*g=&s->widgets[i];if(g->used&&g->id==(int)l->widget)return clipRect(s,g->x,g->y,g->width,g->height,x,y,w,h);}return 0;}
 *w=(int)s->width;*h=(int)s->height;return 1;
}
static int layerConfig(const State*s,NsConfig*q,int*x,int*y,int*w,int*h){
 memcpy(q,s->firstPromptSource.values,sizeof(*q));int placed=nrFirstPromptViewport(s,x,y,w,h);
 q->values[NS_WIDTH]=*w;q->values[NS_HEIGHT]=*h;return placed;
}
/* The archived library declares a 512x256 extent (MAX_VALUES[0..1]) for its
 * standalone callers. Its equations evaluate cells as int32 Q10 samples up to
 * (extent-1)*1024+896 and index them as int32 y*width+x with an int32
 * width*height count, so those are the only limits on the current viewport.
 * Every other field keeps the original validator and its exact domains. */
#define NR_FIRST_PROMPT_EXTENT 2097152
static int32_t validateSource(const NsConfig*q){
 NsConfig domain=*q;domain.values[NS_WIDTH]=domain.values[NS_HEIGHT]=1;int32_t invalid=nrFirstSourceValidate(&domain);if(invalid)return invalid;
 int32_t w=q->values[NS_WIDTH],h=q->values[NS_HEIGHT];
 if(w<0||w>NR_FIRST_PROMPT_EXTENT)return NS_WIDTH+1;
 if(h<0||h>NR_FIRST_PROMPT_EXTENT||(int64_t)w*h>INT32_MAX)return NS_HEIGHT+1;
 return 0;
}
/* Archived nsRender frame loop for viewports beyond that extent, calling the
 * kernel's own static functions. Only its two range checks differ: validateSource
 * replaces the extent bound, and the caller's visible tail (at most width-4
 * scalars) replaces the 512-scalar NS_MAX_TEXT array bound. */
static int32_t extentRender(const NsConfig *config, uint64_t motionMs, const uint32_t *text, uint32_t textLength, NsCell *cells, uint32_t capacity)
{
  if (validateSource(config))
    return -1;
  uint32_t count = (uint32_t) (V(NS_WIDTH) * V(NS_HEIGHT));
  if ((capacity < count) || ((!cells) && count))
    return -2;
  if ((!text) && textLength)
    return -3;
  uint64_t timeMs = (V(NS_MOTION)) ? (motionMs) : (0);
  int32_t w = V(NS_WIDTH);
  int32_t h = V(NS_HEIGHT);
  for (int32_t y = 0; y < h; y++)
    for (int32_t x = 0; x < w; x++)
  {
    NsCell *cell = &cells[(y * w) + x];
    uint32_t bg = materialI(config, timeMs, x * 1024, y * 1024);
    cell->glyph = ' ';
    cell->fg = (uint32_t) V(NS_FOREGROUND_COLOR);
    cell->bg = bg;
    cell->flags = 0;
    switch (V(NS_PIXEL_MODE))
    {
      case 1:
        cell->glyph = 0x2580;
        cell->fg = materialI(config, timeMs, x * 1024, (y * 1024) + 256);
        cell->bg = materialI(config, timeMs, x * 1024, (y * 1024) + 768);
        break;

      case 2:
        cell->glyph = 0x258c;
        cell->fg = materialI(config, timeMs, (x * 1024) + 256, y * 1024);
        cell->bg = materialI(config, timeMs, (x * 1024) + 768, y * 1024);
        break;

      case 3:
        cell->glyph = (((x + y) % 3) == 0) ? (0x2591) : (0x2592);
        cell->fg = mixI(bg, (uint32_t) V(NS_FOREGROUND_COLOR), 130);
        break;

      case 4:
      {
        static const int32_t levels[4][2] = {{5, 41}, {57, 21}, {29, 61}, {45, 13}};
        static const uint32_t dots[4][2] = {{1, 8}, {2, 16}, {4, 32}, {64, 128}};
        uint32_t mask = 0;
        int32_t baseL = ((redI((uint32_t) V(NS_BASE_COLOR)) + greenI((uint32_t) V(NS_BASE_COLOR))) + blueI((uint32_t) V(NS_BASE_COLOR))) / 3;
        for (int32_t dy = 0; dy < 4; dy++)
          for (int32_t dx = 0; dx < 2; dx++)
        {
          uint32_t sample = materialI(config, timeMs, ((x * 1024) + (dx * 512)) + 256, ((y * 1024) + (dy * 256)) + 128);
          int32_t luminance = ((redI(sample) + greenI(sample)) + blueI(sample)) / 3;
          if ((luminance - baseL) > levels[dy][dx])
            mask |= dots[dy][dx];
        }


        cell->glyph = 0x2800 + mask;
        cell->fg = mixI(bg, (uint32_t) V(NS_FOREGROUND_COLOR), 250);
        break;
      }

      default:
        break;

    }

    if (V(NS_STARS))
      starI(config, timeMs, x, y, cell);
  }


  if (!count)
  {
    return 0;
  }
  static const uint32_t defaultText[] = {'M', 'a', 'k', 'e', ' ', 's', 'o', 'm', 'e', 't', 'h', 'i', 'n', 'g', ' ', 't', 'h', 'a', 't', ' ', 'f', 'e', 'e', 'l', 's', ' ', 'a', 'l', 'i', 'v', 'e', '.'};
  if (!text)
  {
    text = defaultText;
    textLength = (sizeof(defaultText)) / (sizeof(defaultText[0]));
  }
  switch (V(NS_LAYOUT))
  {
    case 1:
      promptI(config, cells, timeMs, text, textLength);
      break;

    case 2:
      controlsI(config, cells, timeMs, text, textLength);
      break;

    case 3:
      ribbonI(config, cells, timeMs, text, textLength);
      break;

    case 4:
      scopeI(config, cells, timeMs);
      break;

    default:
      break;

  }

  return (int32_t) count;
}
/* The archived entry point renders every frame its own ABI admits. */
static int32_t renderSource(const NsConfig*config,uint64_t motionMs,const uint32_t*text,uint32_t textLength,NsCell*cells,uint32_t capacity){
 if(!nrFirstSourceValidate(config)&&textLength<=NS_MAX_TEXT)return nrFirstSourceRender(config,motionMs,text,textLength,cells,capacity);
 return extentRender(config,motionMs,text,textLength,cells,capacity);
}
/* Canonical layer bytes: zero unless enabled at schema 98; z and order reserved (zero); alpha configured
 * in 0..1 or all-zero; only the fields of the chosen placement are set. */
static int validLayer(const State*s){
 const PromptSourceLayer*l=&s->promptSourceLayer;PromptSourceLayer empty;memset(&empty,0,sizeof(empty));
 if(!s->firstPromptSource.enabled||s->schema<NR_STATE_SCHEMA_PROMPT_SOURCE_REGION)return !memcmp(l,&empty,sizeof(empty));
 uint64_t fg,bg;memcpy(&fg,&l->alphaForeground,sizeof(fg));memcpy(&bg,&l->alphaBackground,sizeof(bg));
 if(l->placement>NR_PROMPT_SOURCE_WIDGET||l->frame>1||l->z||l->order||l->alphaConfigured>1)return 0;
 if(l->alphaConfigured?!(l->alphaForeground>=0&&l->alphaForeground<=1&&l->alphaBackground>=0&&l->alphaBackground<=1):(fg|bg)!=0)return 0;
 if(l->placement!=NR_PROMPT_SOURCE_WIDGET&&l->widget)return 0;
 if(l->placement==NR_PROMPT_SOURCE_WIDGET&&(l->widget<1||l->widget>65535))return 0;
 if(l->placement!=NR_PROMPT_SOURCE_CELLS)return !(l->x||l->y||l->width||l->height);
 return l->x>=0&&l->y>=0&&l->width>=1&&l->height>=1&&l->width<=NR_FIRST_PROMPT_EXTENT&&l->height<=NR_FIRST_PROMPT_EXTENT&&(int64_t)l->width*l->height<=INT32_MAX&&(int64_t)l->x+l->width<=INT32_MAX&&(int64_t)l->y+l->height<=INT32_MAX;
}
int nrValidFirstPrompt(const State*s){
 const FirstPromptSource*f=&s->firstPromptSource;
 if(!f->enabled){FirstPromptSource empty={0};return !memcmp(f,&empty,sizeof(empty))&&validLayer(s);}
 if(f->enabled!=1||f->reserved||s->schema<NR_STATE_SCHEMA_FIRST_PROMPT)return 0;
 NsConfig q;config(s,&q);if(s->promptSourceLayer.placement==NR_PROMPT_SOURCE_CELLS){q.values[NS_WIDTH]=s->promptSourceLayer.width;q.values[NS_HEIGHT]=s->promptSourceLayer.height;}
 if(q.values[NS_WIDTH]<1||q.values[NS_HEIGHT]<1||validateSource(&q))return 0;
 if(f->values[NS_WIDTH]||f->values[NS_HEIGHT])return 0;
 if(!validLayer(s))return 0;
 for(int i=49;i<64;i++)if(q.values[i])return 0;
 for(int i=0;i<8;i++)if(q.palette[i]>0xffffffu||q.starPalette[i]>0xffffffu)return 0;
 for(int i=0;i<32;i++)if(q.glyphs[i]>0x10ffffu||(q.glyphs[i]>=0xd800u&&q.glyphs[i]<=0xdfffu))return 0;
 return 1;
}
static int exactInt(const Json*j,int owner,const char*key,int64_t lo,int64_t hi,int64_t*out){
 int v=nrField(j,owner,key);double n;if(v<0||j->tokens[v].type!=J_NUMBER||!nrNumber(j,v,&n)||!(n>=(double)lo&&n<=(double)hi)||n!=(double)(int64_t)n)return 0;*out=(int64_t)n;return 1;
}
/* layer:{region,z,order,alpha,frame}. Omitted fields keep their value; layer:null restores the defaults. */
static int parseLayer(NrContext*c,const State*s,const Json*j,int t,PromptSourceLayer*l){
 if(j->tokens[t].type==J_NULL){memset(l,0,sizeof(*l));return 0;}
 if(j->tokens[t].type!=J_OBJECT||!nrAllowed(j,t,"region z order alpha frame"))return fail(c,"Unknown prompt source layer field");
 int r=nrField(j,t,"region");
 if(r>=0){
  PromptSourceLayer next=*l;next.placement=0;next.widget=0;next.x=next.y=next.width=next.height=0;
  if(j->tokens[r].type==J_NULL){}
  else if(j->tokens[r].type==J_STRING){if(!nrEqual(j,r,"prompt"))return fail(c,"Prompt source region must be {x,y,width,height}, \"prompt\", {widget} or null");next.placement=NR_PROMPT_SOURCE_PROMPT;}
  else if(j->tokens[r].type==J_OBJECT&&nrField(j,r,"widget")>=0){
   int64_t id;if(!nrAllowed(j,r,"widget")||!exactInt(j,r,"widget",1,65535,&id))return fail(c,"Prompt source region widget must be a widget id");
   int found=0;for(int i=0;i<NR_WIDGETS;i++)if(s->widgets[i].used&&s->widgets[i].id==(int)id)found=1;
   if(!found)return fail(c,"Prompt source region widget does not exist");
   next.placement=NR_PROMPT_SOURCE_WIDGET;next.widget=(uint32_t)id;
  }
  else if(j->tokens[r].type==J_OBJECT){
   int64_t x,y,w,h;if(!nrAllowed(j,r,"x y width height")||!exactInt(j,r,"x",INT32_MIN,INT32_MAX,&x)||!exactInt(j,r,"y",INT32_MIN,INT32_MAX,&y)||!exactInt(j,r,"width",INT32_MIN,INT32_MAX,&w)||!exactInt(j,r,"height",INT32_MIN,INT32_MAX,&h))return fail(c,"Prompt source region needs integer x, y, width and height");
   if(w<1||h<1)return fail(c,"Prompt source region is below the kernel's 1x1 minimum");
   if(x<0||y<0||x+w>(int64_t)s->width||y+h>(int64_t)s->height)return fail(c,"Prompt source region must lie inside the grid");
   next.placement=NR_PROMPT_SOURCE_CELLS;next.x=(int32_t)x;next.y=(int32_t)y;next.width=(int32_t)w;next.height=(int32_t)h;
  }
  else return fail(c,"Prompt source region must be {x,y,width,height}, \"prompt\", {widget} or null");
  *l=next;
 }
 int v=nrField(j,t,"z");if(v>=0){if(nrEqual(j,v,"above"))l->z=0;else if(nrEqual(j,v,"below"))return fail(c,"Prompt source layer z \"below\" requires the surface-layers design");else return fail(c,"Prompt source layer z must be \"above\"");}
 v=nrField(j,t,"order");if(v>=0){int64_t order;if(!exactInt(j,t,"order",INT32_MIN,INT32_MAX,&order))return fail(c,"Prompt source layer order must be an integer");if(order)return fail(c,"Prompt source layer order other than 0 requires the surface-layers design");}
 v=nrField(j,t,"alpha");if(v>=0){
  /* A number sets both channels; {fg,bg} sets each one given and keeps the other. */
  double fg=l->alphaConfigured?l->alphaForeground:1,bg=l->alphaConfigured?l->alphaBackground:1,a;
  if(j->tokens[v].type==J_NUMBER){if(!nrNumber(j,v,&a)||!(a>=0&&a<=1))return fail(c,"Prompt source layer alpha must be a number from 0 to 1 or {fg,bg}");fg=bg=a;}
  else if(j->tokens[v].type==J_OBJECT&&j->tokens[v].count>0&&nrAllowed(j,v,"fg bg")){
   const char*keys[2]={"fg","bg"};double*out[2]={&fg,&bg};
   for(int k=0;k<2;k++){int e=nrField(j,v,keys[k]);if(e<0)continue;if(j->tokens[e].type!=J_NUMBER||!nrNumber(j,e,&a)||!(a>=0&&a<=1))return fail(c,"Prompt source layer alpha must be a number from 0 to 1 or {fg,bg}");*out[k]=a;}
  }
  else return fail(c,"Prompt source layer alpha must be a number from 0 to 1 or {fg,bg}");
  l->alphaConfigured=1;l->alphaForeground=fg+0.0;l->alphaBackground=bg+0.0;
 }
 v=nrField(j,t,"frame");if(v>=0){if(nrEqual(j,v,"visible"))l->frame=1;else if(nrEqual(j,v,"invisible"))l->frame=0;else return fail(c,"Prompt source layer frame must be \"visible\" or \"invisible\"");}
 return 0;
}
int nrFirstPromptCommand(NrContext*c,State*s,const Json*j){
 if(s->schema<NR_STATE_SCHEMA_FIRST_PROMPT||!nrAllowed(j,0,"op enabled values palette starPalette glyphs layer"))return fail(c,"Invalid prompt command");
 if(nrField(j,0,"layer")>=0&&s->schema<NR_STATE_SCHEMA_PROMPT_SOURCE_REGION)return fail(c,"Prompt source layer requires schema98");
 FirstPromptSource f=s->firstPromptSource;int enabled=1,t=nrField(j,0,"enabled");if(t>=0&&!nrBoolean(j,t,&enabled))return fail(c,"Prompt enabled must be boolean");
 if(!enabled){if(nrField(j,0,"values")>=0||nrField(j,0,"palette")>=0||nrField(j,0,"starPalette")>=0||nrField(j,0,"glyphs")>=0||nrField(j,0,"layer")>=0)return fail(c,"Disable prompt without a config patch");memset(&s->firstPromptSource,0,sizeof(s->firstPromptSource));memset(&s->promptSourceLayer,0,sizeof(s->promptSourceLayer));return 0;}
 PromptSourceLayer layer;if(f.enabled)layer=s->promptSourceLayer;else memset(&layer,0,sizeof(layer));
 t=nrField(j,0,"layer");if(t>=0&&parseLayer(c,s,j,t,&layer)<0)return -1;
 NsConfig q;if(!f.enabled){nrFirstSourceDefaults(&q);q.values[NS_LAYOUT]=1;}else memcpy(&q,f.values,sizeof(q));
 q.values[NS_WIDTH]=(int)s->width;q.values[NS_HEIGHT]=(int)s->height;
 t=nrField(j,0,"values");if(t>=0){
  if(!nrAllowed(j,t,"effect layout seed stars densityPermille glyphSet starPeriodMinMs starPeriodRangeMs starDutyPermille starFloorPermille starPeakPermille gradientPeriodMs saturationPermille brightnessPermille focusRow neighborSpeedPermille neighborSaturationPermille neighborBrightnessPermille angleDegrees scaleCells hueStepDegrees hueDegreesPerSecond baseHueDegrees pixelMode originX originY valuePermille motion phaseDegrees grainPermille cursorMode borderStyle selection foregroundColor baseColor waveAmplitudePermille starAttackPermille paletteCount starPaletteCount glyphCount modalOpen hueSaturationPermille hueBrightnessPermille cellAspectPermille textScrimPermille promptBands colorMode"))return fail(c,"Unknown prompt value");
  static const struct {const char*name;int index;}fields[]={
 {"effect",2},
 {"layout",3},
 {"seed",4},
 {"stars",5},
 {"densityPermille",6},
 {"glyphSet",7},
 {"starPeriodMinMs",8},
 {"starPeriodRangeMs",9},
 {"starDutyPermille",10},
 {"starFloorPermille",11},
 {"starPeakPermille",12},
 {"gradientPeriodMs",13},
 {"saturationPermille",14},
 {"brightnessPermille",15},
 {"focusRow",16},
 {"neighborSpeedPermille",17},
 {"neighborSaturationPermille",18},
 {"neighborBrightnessPermille",19},
 {"angleDegrees",20},
 {"scaleCells",21},
 {"hueStepDegrees",22},
 {"hueDegreesPerSecond",23},
 {"baseHueDegrees",24},
 {"pixelMode",25},
 {"originX",26},
 {"originY",27},
 {"valuePermille",28},
 {"motion",29},
 {"phaseDegrees",30},
 {"grainPermille",31},
 {"cursorMode",32},
 {"borderStyle",33},
 {"selection",34},
 {"foregroundColor",35},
 {"baseColor",36},
 {"waveAmplitudePermille",37},
 {"starAttackPermille",38},
 {"paletteCount",39},
 {"starPaletteCount",40},
 {"glyphCount",41},
 {"modalOpen",42},
 {"hueSaturationPermille",43},
 {"hueBrightnessPermille",44},
 {"cellAspectPermille",45},
 {"textScrimPermille",46},
 {"promptBands",47},
 {"colorMode",48},
  };
  for(unsigned k=0;k<sizeof(fields)/sizeof(*fields);k++){int v=nrField(j,t,fields[k].name);if(v>=0){double n;if(!nrNumber(j,v,&n)||n<INT32_MIN||n>INT32_MAX||n!=(int32_t)n)return fail(c,"Prompt values must be exact int32");q.values[fields[k].index]=(int32_t)n;}}
 }
 const char*arrays[]={"palette","starPalette","glyphs"};uint32_t*dest[]={q.palette,q.starPalette,q.glyphs};const int cap[]={8,8,32};const int countKey[]={NS_PALETTE_COUNT,NS_STAR_PALETTE_COUNT,NS_GLYPH_COUNT};
 for(int k=0;k<3;k++){t=nrField(j,0,arrays[k]);if(t<0)continue;if(j->tokens[t].type!=J_ARRAY||j->tokens[t].count<1||j->tokens[t].count>cap[k])return fail(c,"Invalid prompt array length");memset(dest[k],0,(size_t)cap[k]*4);int a=t+1;for(int i=0;i<j->tokens[t].count;i++,a=j->tokens[a].next){double n;if(!nrNumber(j,a,&n)||n<0||n>(k==2?0x10ffff:0xffffff)||n!=(uint32_t)n||(k==2&&(n>=0xd800&&n<=0xdfff)))return fail(c,"Invalid prompt array value");dest[k][i]=(uint32_t)n;}q.values[countKey[k]]=j->tokens[t].count;}
 if(layer.placement==NR_PROMPT_SOURCE_CELLS){q.values[NS_WIDTH]=layer.width;q.values[NS_HEIGHT]=layer.height;}
 if(validateSource(&q))return fail(c,"Prompt config or viewport is outside source ABI");
 /* "prompt" needs a prompt frame now; later frames without one paint no source. */
 if(layer.placement==NR_PROMPT_SOURCE_PROMPT){int px,py,pw,ph,fx,fy,fw,fh;if(!nrPromptFrameRect(s,&px,&py,&pw,&ph)||!clipRect(s,px,py,pw,ph,&fx,&fy,&fw,&fh))return fail(c,"Prompt source region \"prompt\" needs a visible prompt");}
 q.values[NS_WIDTH]=q.values[NS_HEIGHT]=0;memset(&f,0,sizeof(f));f.enabled=1;memcpy(f.values,&q,sizeof(q));s->firstPromptSource=f;s->promptSourceLayer=layer;return 0;
}
/* Where the archived layout functions paint the input row in a w x h kernel viewport. promptI
 * (layout 1, and controlsI below 64x26) puts '>' at x=w>12?5:0 and the tail of at most w-x-4
 * scalars two cells right of it on the focus row; controlsI puts '>' at 5 and the tail of at most
 * w-12 scalars at 7 on row h-5; ribbonI centres at most w-4 scalars at (w-n)/2 on row h/2 with
 * no '>'; layouts 0 and 4 paint no input. Returns 1 when a '>' precedes the input, 2 for the
 * ribbon, 0 for none. */
static int place(const State*s,int w,int h,int*max,int*column,int*row){
 int layout=s->firstPromptSource.values[NS_LAYOUT];
 if(layout==2&&w>=64&&h>=26){*column=7;*row=h-5;*max=w-12;return 1;}
 if(layout==1||layout==2){int x=w>12?5:0;*column=x+2;*max=w-x-4;*row=s->firstPromptSource.values[NS_FOCUS_ROW];if(*row<0)*row=h/2;else if(*row>=h)*row=h-1;return 1;}
 if(layout==3){*column=0;*row=h/2;*max=w>4?w-4:0;return 2;}
 *column=*row=-1;*max=0;return 0;
}
/* Input geometry in grid cells: the first input column and the input row. The kernel lays the
 * prompt out in its own viewport (the layer rectangle; the whole grid by default); the result is
 * offset by that rectangle's origin. Unplaced: row -1. No input (layouts 0 and 4): column and
 * row -1 and an empty span at the caret. Returns place()'s kind. */
int nrFirstPromptGeometry(const State*s,int*start,int*end,int*x,int*y){
 int ox,oy,width,height,placed=nrFirstPromptViewport(s,&ox,&oy,&width,&height);
 if(!s->firstPromptSource.enabled){ox=oy=0;width=(int)s->width;height=(int)s->height;placed=1;}
 const Prompt*p=&s->promptDocument;int max,kind=place(s,width,height,&max,x,y);if(max<0)max=0;*end=nrGraphemeFloor(p->glyphs,p->count,p->caret);
 if(!kind){*start=*end;return 0;}
 if(kind==2){
  /* ribbonI keeps the head text[0..min(length,w-4)) of the text before the caret; inputI keeps its tail. */
  *start=0;if(*end>max)*end=nrGraphemeFloor(p->glyphs,p->count,max);*x=(width-*end)/2;
 }else{
  *start=*end>max?*end-max:0;
  int floor=nrGraphemeFloor(p->glyphs,p->count,*start);if(floor!=*start)*start=nrGraphemeAfter(p->glyphs,p->count,floor);if(*start>*end)*start=*end;
 }
 *x+=ox;*y=placed?*y+oy:-1;
 return kind;
}
int nrFirstPromptHit(const State*s,int x,int y){
 (void)y;int start,end,column,row;if(!nrFirstPromptGeometry(s,&start,&end,&column,&row))return nrGraphemeFloor(s->promptDocument.glyphs,s->promptDocument.count,s->promptDocument.caret);
 int index=start+x-column;if(index<start)index=start;if(index>end)index=end;return nrGraphemeFloor(s->promptDocument.glyphs,s->promptDocument.count,index);
}
void nrFirstPromptCoordinates(const State*s,int (*out)[2]){
 int start,end,x,y,kind=nrFirstPromptGeometry(s,&start,&end,&x,&y);for(int i=0;i<=s->promptDocument.count;i++){out[i][0]=kind?x+i-start:-1;out[i][1]=(kind&&i>=start&&i<=end)?y:-1;}
}
static void paintViewport(NrContext*c,const State*s){
 NsConfig q;config(s,&q);if(s->reducedMotion)q.values[NS_MOTION]=0;
 int start,end,x,y,kind=nrFirstPromptGeometry(s,&start,&end,&x,&y);
 if(renderSource(&q,s->timeUs/1000,s->promptDocument.glyphs+start,(uint32_t)(end-start),(NsCell*)c->cells,s->width*s->height)<0)return;
 /* The material kernel owns the canvas. Paint arrival weather after it,
  * preserving the document row and caret from that same frame. */
 if(s->promptAppearance.weatherConfigured&&s->promptAppearance.eventCount){
  /* The protected row spans up to the viewport width. Hold it in the
   * caller-owned plot scratch (two cells per viewport cell, write-before-read
   * per widget); weather paints only c->cells, so nothing reads it meanwhile. */
  NrCell*protected=(NrCell*)c->plotColor;int left=kind==1?x-2:x,right=x+end-start;
  if(left<0)left=0;if(right>=(int)s->width)right=(int)s->width-1;
  int count=kind&&right>=left&&y>=0&&y<(int)s->height?right-left+1:0;
  if(count)memcpy(protected,c->cells+(size_t)y*s->width+left,(size_t)count*sizeof(*protected));
  nrPromptAppearanceWeather(c);
  if(count)memcpy(c->cells+(size_t)y*s->width+left,protected,(size_t)count*sizeof(*protected));
 }
 if(kind&&s->promptAppearance.cursorConfigured){int xx=x+end-start;if(xx>=0&&xx<(int)s->width&&y>=0&&y<(int)s->height){NrCell*cell=&c->cells[(size_t)y*s->width+xx];cell->glyph=32;cell->foreground=cell->background;}}
 for(size_t i=0;i<(size_t)s->width*s->height;i++)c->cells[i].id=0;
 memset(c->characterIndices,0xff,(size_t)s->width*s->height*4);memset(c->characterOwners,0,(size_t)s->width*s->height*4);
 for(int i=start;kind&&i<=end;i++){int xx=x+i-start;if(xx<0||xx>=(int)s->width||y<0||y>=(int)s->height)continue;size_t at=(size_t)y*s->width+xx;c->cells[at].id=NR_ID_PROMPT;c->characterIndices[at]=(uint32_t)i;c->characterOwners[at]=1u<<16;if(s->promptDocument.anchor>=0&&i<end&&i>=(s->promptDocument.anchor<s->promptDocument.caret?s->promptDocument.anchor:s->promptDocument.caret)&&i<(s->promptDocument.anchor>s->promptDocument.caret?s->promptDocument.anchor:s->promptDocument.caret))nrCellBackground(c,xx,y,0x43637f,.8);}
 if(kind&&s->promptAppearance.cursorConfigured)nrPromptAppearanceCursor(c,s,x+end-start,y);
}
/* A bounded layer: the kernel renders the layer rectangle into the first half of plot scratch (at most
 * one cell per viewport cell) and is composited at its origin. Every step below touches only cells of the
 * rectangle, so the cost follows its area and the rest of the frame is the ordinary scene. */
static void paintLayer(NrContext*c,const State*s){
 NsConfig q;int ox,oy,w,h;if(!layerConfig(s,&q,&ox,&oy,&w,&h))return;if(s->reducedMotion)q.values[NS_MOTION]=0;
 int start,end,x,y,kind=nrFirstPromptGeometry(s,&start,&end,&x,&y);
 NsCell*source=(NsCell*)c->plotColor;size_t W=s->width;
 if(renderSource(&q,s->timeUs/1000,s->promptDocument.glyphs+start,(uint32_t)(end-start),source,(uint32_t)w*(uint32_t)h)<0)return;
 const double alphaFg=NR_PROMPT_SOURCE_ALPHA_FG(s),alphaBg=NR_PROMPT_SOURCE_ALPHA_BG(s);int blend=c->paintBlend;c->paintBlend=0;
 for(int r=0;r<h;r++){
  NrCell*row=c->cells+(size_t)(oy+r)*W+ox;const NsCell*k=source+(size_t)r*w;
  if(alphaFg>=1&&alphaBg>=1){memcpy(row,k,(size_t)w*sizeof(*row));continue;}
  /* Otherwise each channel blends with its own alpha. The source's paper mixes over the scene's background
   * and over the scene's ink, so a translucent band covers text as well as paper; the source's glyphs are
   * drawn over that with the foreground alpha. Under the source's blank cells the scene's glyphs remain. */
  for(int i=0;i<w;i++){
   NrCell*cell=&row[i];cell->background=nrMix(cell->background,k[i].bg,alphaBg);
   if(cell->glyph!=32)cell->foreground=nrMix(cell->foreground,k[i].bg,alphaBg);
   if(k[i].glyph!=32)nrIndexedGlyph(c,ox+i,oy+r,k[i].glyph,k[i].fg,alphaFg,0,UINT32_MAX);
  }
 }
 int left=kind==1?x-2:x,right=x+end-start;if(left<ox)left=ox;if(right>=ox+w)right=ox+w-1;
 int rowInside=kind&&y>=oy&&y<oy+h,count=rowInside&&right>=left?right-left+1:0;
 const PromptAppearance*a=&s->promptAppearance;
 if(a->weatherConfigured&&a->eventCount&&a->weatherStyle&&a->weatherIntensity){
  /* Weather over the layer, clipped to it, with the document row protected as in the full viewport. */
  NrCell*protected=(NrCell*)c->plotColor+W*s->height;
  if(count)memcpy(protected,c->cells+(size_t)y*W+left,(size_t)count*sizeof(*protected));
  NrSourceWeatherOptions options;nrSourceWeatherDefaults(&options);options.lifeMs=a->weatherLifeMs;options.launchSpeed=a->weatherSpeed;if(s->reducedMotion){options.launchSpeed=1;options.brightness*=.5;}
  uint32_t wheel[360];for(int i=0;i<360;i++)wheel[i]=nrHueShift(0xf1ad80,(double)i);
  nrSourceWeatherPaintLayerClipped(a->events,a->eventCount,(double)s->timeUs/1000,&options,a->weatherIntensity,1,0,wheel,s->width,s->height,(uint32_t*)c->cells,(uint32_t)ox,(uint32_t)oy,(uint32_t)w,(uint32_t)h);
  if(count)memcpy(c->cells+(size_t)y*W+left,protected,(size_t)count*sizeof(*protected));
 }
 int caret=x+end-start,caretInside=rowInside&&caret>=ox&&caret<ox+w;
 if(a->cursorConfigured&&caretInside){NrCell*cell=&c->cells[(size_t)y*W+caret];cell->glyph=32;cell->foreground=cell->background;}
 if(s->promptSourceLayer.frame&&w>=3&&h>=3){ClipRect previous=nrClip(c,ox,oy,w,h);nrBox(c,ox,oy,w,h,1,(uint32_t)q.values[NS_FOREGROUND_COLOR]&0xffffffu,.9,0);c->clip=previous;}
 for(int r=0;r<h;r++){size_t at=(size_t)(oy+r)*W+ox;for(int i=0;i<w;i++)c->cells[at+i].id=0;memset(c->characterIndices+at,0xff,(size_t)w*4);memset(c->characterOwners+at,0,(size_t)w*4);}
 const Prompt*p=&s->promptDocument;
 for(int i=start;i<=end;i++){int xx=x+i-start;if(!rowInside||xx<ox||xx>=ox+w)continue;size_t at=(size_t)y*W+xx;c->cells[at].id=NR_ID_PROMPT;c->characterIndices[at]=(uint32_t)i;c->characterOwners[at]=1u<<16;if(p->anchor>=0&&i<end&&i>=(p->anchor<p->caret?p->anchor:p->caret)&&i<(p->anchor>p->caret?p->anchor:p->caret))nrCellBackground(c,xx,y,0x43637f,.8);}
 if(a->cursorConfigured&&caretInside)nrPromptAppearanceCursor(c,s,caret,y);
 c->paintBlend=blend;
}
void nrFirstPromptPaint(NrContext*c,const State*s){
 if(s->promptSourceLayer.placement)paintLayer(c,s);else paintViewport(c,s);
}
