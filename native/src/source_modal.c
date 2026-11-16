#include "internal.h"
#include <limits.h>
#include <float.h>
static const char*const kinds[]={"center","fullscreen","drawer-left","drawer-right","drawer-top","drawer-bottom","corner","toast","error","confirmation","dropdown"};
const char*nrModalKind(uint32_t k){return k<11?kinds[k]:"";}
static int valid(const NrContext*c){return c&&c->valid==NR_MAGIC&&c->capacity>=sizeof(*c);}
static int fail(NrContext*c,const char*m){memcpy(c->error,m,strlen(m)+1);return -1;}
uint64_t nrModalMemorySize(const NrContext*c){return valid(c)?c->modalRequiredBytes:0;}
uint64_t nrModalMemoryCapacity(const NrContext*c){return valid(c)?c->modalMemoryBytes:0;}
static int require(State*s,uint32_t n){NrContext*c=s->dynamicPrompt.owner;if(!valid(c))return 0;if(n<=c->modalCapacity)return 1;
 uint64_t cap=c->modalCapacity;while(cap<n){cap+=cap/2+1;if(cap>UINT32_MAX/4u){cap=UINT32_MAX/4u;break;}}
 uint64_t bytes=cap*12;if(cap<n||bytes>SIZE_MAX){fail(c,"Modal storage address representation exhausted");return 0;}
 c->modalRequestedCapacity=(uint32_t)cap;c->modalRequiredBytes=bytes;fail(c,"Modal storage required");return 0;
}
int nrSetModalMemory(NrContext*c,void*memory,uint64_t bytes){
 if(!valid(c)||!memory||((uintptr_t)memory&7u)||bytes>SIZE_MAX||bytes>UINTPTR_MAX-(uintptr_t)memory||bytes<c->modalRequiredBytes||!nrExternalOutput(c,memory,(size_t)bytes))return -1;
 uint32_t cap=c->modalRequestedCapacity;if(!cap||cap<c->modalCapacity||(uint64_t)cap*12>bytes)return -1;
 c->settled=0;
 uint32_t*base=memory,n=c->state.sourceModal.scalars;if(n)memcpy(base,c->state.modalScalars,(size_t)n*4);
 c->state.modalScalars=base;c->trial.modalScalars=base+cap;c->probe.modalScalars=base+2*(size_t)cap;
 if(n){memcpy(c->trial.modalScalars,base,(size_t)n*4);memcpy(c->probe.modalScalars,base,(size_t)n*4);}
 c->trial.sourceModal=c->state.sourceModal;c->probe.sourceModal=c->state.sourceModal;
 c->modalMemory=memory;c->modalMemoryBytes=bytes;c->modalCapacity=cap;c->modalRequiredBytes=(uint64_t)cap*12;return 0;
}
void nrModalCopyState(State*d,const State*s){if(s->sourceModal.scalars)memcpy(d->modalScalars,s->modalScalars,(size_t)s->sourceModal.scalars*4);}
static int spans(SourceModalState*q,SourceModalString**out){int n=0;out[n++]=&q->workspace;out[n++]=&q->context;out[n++]=&q->query;for(uint32_t i=0;i<q->depth;i++){SourceModalEntry*e=&q->entries[i];out[n++]=&e->title;out[n++]=&e->body;out[n++]=&e->context;out[n++]=&e->query;}return n;}
static void compact(State*s){SourceModalString*p[35];int n=spans(&s->sourceModal,p);for(int i=1;i<n;i++){SourceModalString*t=p[i];int j=i;while(j&&p[j-1]->offset>t->offset){p[j]=p[j-1];j--;}p[j]=t;}uint32_t at=0;for(int i=0;i<n;i++){SourceModalString*t=p[i];if(t->count){memmove(s->modalScalars+at,s->modalScalars+t->offset,(size_t)t->count*4);t->offset=at;at+=t->count;}else t->offset=0;}s->sourceModal.scalars=at;}
static int idValid(const char*id){int n=0;while(n<68&&id[n]){unsigned char c=id[n++];if(!((c>=97&&c<=122)||(c>=65&&c<=90)||(c>=48&&c<=57)||c==95||c==46||c==45))return 0;}if(n<1||n>64)return 0;for(;n<68;n++)if(id[n])return 0;return 1;}
static int equal(const State*s,SourceModalString q,const char*text){size_t n=strlen(text);if(n!=q.count)return 0;for(uint32_t i=0;i<q.count;i++)if(s->modalScalars[q.offset+i]!=(unsigned char)text[i])return 0;return 1;}
int nrModalBlocking(const State*s){const SourceModalState*q=&s->sourceModal;if(!q->depth)return 0;const SourceModalEntry*e=&q->entries[q->depth-1];return !(strcmp(e->id,"node")==0&&equal(s,e->context,"node")&&(equal(s,q->workspace,"dag")||equal(s,q->workspace,"graph-explorer")||equal(s,q->workspace,"git-history")||equal(s,q->workspace,"spatial-menu")));}
static void cancel(State*s){s->pointerActive=0;s->pressedHit=0;s->hoverHit=0;s->originalCamera.grabActive=0;if(!s->originalCamera.enabled)memset(&s->originalCamera,0,sizeof(s->originalCamera));}
static void invalidate(SourceModalState*q){q->association=0;q->activeCount=0;q->boxId=0;memset(q->activeIds,0,sizeof(q->activeIds));}
int nrModalDismiss(State*s){SourceModalState*q=&s->sourceModal;if(!q->depth||!q->entries[q->depth-1].dismissible)return 0;memset(&q->entries[--q->depth],0,sizeof(q->entries[0]));invalidate(q);if(q->revision<UINT64_MAX)q->revision++;compact(s);cancel(s);return 1;}
void nrModalForgetComponent(State*s,uint32_t id){SourceModalState*q=&s->sourceModal;uint32_t n=0;for(uint32_t i=0;i<q->ownedCount;i++)if(q->ownedIds[i]!=id)q->ownedIds[n++]=q->ownedIds[i];if(n!=q->ownedCount){memset(q->ownedIds+n,0,(q->ownedCount-n)*sizeof(*q->ownedIds));q->ownedCount=n;if(nrModalActiveComponent(s,id))invalidate(q);}}
int nrModalOwnsComponent(const State*s,uint32_t id){for(uint32_t i=0;i<s->sourceModal.ownedCount;i++)if(s->sourceModal.ownedIds[i]==id)return 1;return 0;}
int nrModalActiveComponent(const State*s,uint32_t id){const SourceModalState*q=&s->sourceModal;if(!q->depth||!q->association)return 0;for(uint32_t i=0;i<q->activeCount;i++)if(q->activeIds[i]==id)return 1;return 0;}
static const SourceStageComponentRecord*component(const State*s,uint32_t id){for(uint32_t i=0;i<s->sourceStage.count;i++)if(s->sourceStage.components[i].id==id&&s->sourceStage.components[i].used)return &s->sourceStage.components[i];return 0;}
int nrModalAssociationReady(const State*s){const SourceModalState*q=&s->sourceModal;if(!q->depth||!q->association)return 0;for(uint32_t i=0;i<q->activeCount;i++)if(!component(s,q->activeIds[i]))return 0;const SourceStageComponentRecord*r=component(s,q->boxId);return r&&r->node[0]==1&&(r->node[14]||r->node[15])&&r->node[4]>0&&r->node[5]>0;}
int nrModalPointerOwns(const State*s,double x,double y){if(nrModalBlocking(s))return 1;if(!s->sourceModal.depth||!nrModalAssociationReady(s))return 0;const int32_t*n=component(s,s->sourceModal.boxId)->node;return x>=n[2]&&y>=n[3]&&x<(double)n[2]+n[4]&&y<(double)n[3]+n[5];}
int nrValidSourceModal(const State*s){const SourceModalState*q=&s->sourceModal;const NrContext*c=s->dynamicPrompt.owner;
 if(s->schema<NR_STATE_SCHEMA_SOURCE_MODAL){SourceModalState z={0};return !memcmp(q,&z,sizeof(z));}
 if(!valid(c)||q->depth>8||q->scalars>c->modalCapacity||q->scalars>UINT32_MAX/4u||q->reserved||q->ownedCount>NR_SOURCE_STAGE_COMPONENT_CAPACITY||q->activeCount>NR_SOURCE_STAGE_COMPONENT_CAPACITY||q->association>1)return 0;
 SourceModalString*p[35];int n=spans((SourceModalState*)q,p);uint64_t total=0;
 for(int i=0;i<n;i++){SourceModalString a=*p[i];if(a.offset>q->scalars||a.count>q->scalars-a.offset||(!a.count&&a.offset))return 0;total+=a.count;for(int j=0;j<i;j++){SourceModalString b=*p[j];if(a.count&&b.count&&a.offset<b.offset+b.count&&b.offset<a.offset+a.count)return 0;}}
 if(total!=q->scalars)return 0;
 for(uint32_t i=0;i<q->scalars;i++){uint32_t x=s->modalScalars[i];if(x>0x10ffff||(x>=0xd800&&x<=0xdfff))return 0;}
 for(uint32_t i=0;i<8;i++){const SourceModalEntry*e=&q->entries[i];if(i>=q->depth){SourceModalEntry z={0};if(memcmp(e,&z,sizeof(z)))return 0;}else if(!idValid(e->id)||e->kind>=11||e->dismissible>1||e->reserved||e->reserved2||!(e->atMs>=0&&e->atMs<=DBL_MAX))return 0;}
 for(uint32_t i=0;i<NR_SOURCE_STAGE_COMPONENT_CAPACITY;i++){uint32_t id=q->ownedIds[i],active=q->activeIds[i];if(i>=q->ownedCount){if(id)return 0;}else {if(!id||id>65535)return 0;for(uint32_t j=0;j<i;j++)if(q->ownedIds[j]==id)return 0;}if(i>=q->activeCount){if(active)return 0;}else{if(!nrModalOwnsComponent(s,active))return 0;for(uint32_t j=0;j<i;j++)if(q->activeIds[j]==active)return 0;}}
 if(!q->association){if(q->activeCount||q->boxId)return 0;}else if(!q->depth||!q->activeCount||!nrModalActiveComponent(s,q->boxId))return 0;
 return 1;
}
int nrModalLoadPayload(State*s,const uint8_t*p,uint32_t bytes){uint32_t n=s->sourceModal.scalars;if((uint64_t)n*4!=bytes)return -1;for(uint32_t i=0;i<n;i++){uint32_t x;memcpy(&x,p+(size_t)i*4,4);if(x>0x10ffff||(x>=0xd800&&x<=0xdfff))return -1;}if(!require(s,n))return -1;if(bytes)memcpy(s->modalScalars,p,bytes);return 0;}
static int getText(NrContext*c,State*s,const Json*j,int obj,const char*key,SourceModalString*out,int required){int t=nrField(j,obj,key);if(t<0)return required?fail(c,"Missing modal text"):0;int n=nrDecode(j,t,0,0);if(n<0)return fail(c,"Invalid modal Unicode string");uint64_t end=(uint64_t)s->sourceModal.scalars+(uint32_t)n;if(end>UINT32_MAX/4u||!require(s,(uint32_t)end))return -1;SourceModalString q={n?s->sourceModal.scalars:0,(uint32_t)n};if(n&&nrDecode(j,t,s->modalScalars+q.offset,n)!=n)return fail(c,"Invalid modal Unicode string");s->sourceModal.scalars=(uint32_t)end;*out=q;return 0;}
int nrSourceModalCommand(NrContext*c,State*s,const Json*j){int t=nrField(j,0,"action");if(s->schema<NR_STATE_SCHEMA_SOURCE_MODAL||t<0)return fail(c,"Modal action required");SourceModalState*q=&s->sourceModal;
 if(nrEqual(j,t,"push")){
  if(!nrAllowed(j,0,"op action entry context workspace")||q->depth>=8)return fail(c,"Modal stack limit or unknown field");int e=nrField(j,0,"entry");if(e<0||j->tokens[e].type!=J_OBJECT||!nrAllowed(j,e,"id kind title body atMs dismissible"))return fail(c,"Invalid modal entry");SourceModalEntry z={0};int id=nrField(j,e,"id"),kind=nrField(j,e,"kind"),at=nrField(j,e,"atMs"),dismiss=nrField(j,e,"dismissible"),d;
  if(id<0||nrString(j,id,z.id,sizeof(z.id))<0||!idValid(z.id)||at<0||!nrNumber(j,at,&z.atMs)||!(z.atMs>=0&&z.atMs<=DBL_MAX)||dismiss<0||!nrBoolean(j,dismiss,&d))return fail(c,"Invalid modal entry domain");z.dismissible=(uint32_t)d;for(z.kind=0;z.kind<11;z.kind++)if(nrEqual(j,kind,kinds[z.kind]))break;if(z.kind==11)return fail(c,"Invalid modal kind");
  if(getText(c,s,j,e,"title",&z.title,1)||getText(c,s,j,e,"body",&z.body,1)||getText(c,s,j,0,"context",&z.context,1)||getText(c,s,j,0,"workspace",&q->workspace,0))return -1;q->entries[q->depth++]=z;invalidate(q);cancel(s);
 }else if(nrEqual(j,t,"edit")){
  if(!nrAllowed(j,0,"op action context query selected workspace"))return fail(c,"Unknown modal edit field");SourceModalEntry*e=q->depth?&q->entries[q->depth-1]:0;SourceModalString*context=e?&e->context:&q->context,*query=e?&e->query:&q->query;uint32_t*selected=e?&e->selected:&q->selected;
  if(getText(c,s,j,0,"context",context,0)||getText(c,s,j,0,"query",query,0)||getText(c,s,j,0,"workspace",&q->workspace,0))return -1;int v=nrField(j,0,"selected");if(v>=0){double n;if(!nrNumber(j,v,&n)||n<0||n>UINT32_MAX||n!=(uint32_t)n)return fail(c,"Invalid modal selection");*selected=(uint32_t)n;}invalidate(q);cancel(s);
 }else if(nrEqual(j,t,"dismiss")){if(!nrAllowed(j,0,"op action"))return fail(c,"Unknown modal dismiss field");nrModalDismiss(s);return 0;
 }else if(nrEqual(j,t,"clear")){if(!nrAllowed(j,0,"op action"))return fail(c,"Unknown modal clear field");q->depth=0;memset(q->entries,0,sizeof(q->entries));invalidate(q);cancel(s);
 }else if(nrEqual(j,t,"associate")){
  if(!q->depth||!nrAllowed(j,0,"op action componentIds boxId"))return fail(c,"Modal association needs active layer");int a=nrField(j,0,"componentIds"),b=nrField(j,0,"boxId");double box;if(a<0||j->tokens[a].type!=J_ARRAY||j->tokens[a].count<1||j->tokens[a].count>NR_SOURCE_STAGE_COMPONENT_CAPACITY||b<0||!nrNumber(j,b,&box)||box<1||box>65535||box!=(uint32_t)box)return fail(c,"Invalid modal association");invalidate(q);q->boxId=(uint32_t)box;
  for(int v=a+1;v<j->tokens[a].next;v=j->tokens[v].next){double d;if(!nrNumber(j,v,&d)||d<1||d>65535||d!=(uint32_t)d||!component(s,(uint32_t)d))return fail(c,"Modal component unavailable");uint32_t id=(uint32_t)d;for(uint32_t k=0;k<q->activeCount;k++)if(q->activeIds[k]==id)return fail(c,"Duplicate modal component");q->activeIds[q->activeCount++]=id;if(!nrModalOwnsComponent(s,id)){/* Discard removed owned components before retaining a new one. */if(q->ownedCount==NR_SOURCE_STAGE_COMPONENT_CAPACITY){uint32_t n=0;for(uint32_t k=0;k<q->ownedCount;k++)if(component(s,q->ownedIds[k]))q->ownedIds[n++]=q->ownedIds[k];memset(q->ownedIds+n,0,(q->ownedCount-n)*4);q->ownedCount=n;}if(q->ownedCount==NR_SOURCE_STAGE_COMPONENT_CAPACITY)return fail(c,"Modal component association exhausted");q->ownedIds[q->ownedCount++]=id;}}
  q->association=1;if(!nrModalAssociationReady(s)||!nrModalActiveComponent(s,q->boxId))return fail(c,"Modal box must be a visible current component");
 }else return fail(c,"Unknown modal action");
 if(q->revision==UINT64_MAX)return fail(c,"Modal revision representation exhausted");q->revision++;compact(s);return nrValidSourceModal(s)?0:fail(c,"Invalid modal state");
}
