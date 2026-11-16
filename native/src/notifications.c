#include "internal.h"
/* Notifications own records; actions create retained intentions. The host decides
 * what to execute, acknowledges the intention, and explicitly purges history. */
static int fail(NrContext *c,const char *message) {
    size_t length=strlen(message);if(length>255)length=255;
    memcpy(c->error,message,length);c->error[length]=0;return -1;
}
static int scalar(const Json*j,int at,const char*key,double*value,double low,double high) {
    int f=nrField(j,at,key);if(f<0)return 1;
    double x;if(!nrNumber(j,f,&x)||!(x>=low&&x<=high))return 0;
    *value=x;return 1;
}
static int whole(const Json*j,int at,const char*key,int*value,int low,int high) {
    double x=*value;if(!scalar(j,at,key,&x,low,high)||x!=(int)x)return 0;
    *value=(int)x;return 1;
}
static int flag(const Json*j,int at,const char*key,int*value) {
    int f=nrField(j,at,key);return f<0||nrBoolean(j,f,value);
}
static int millis(const Json*j,const char*key,uint64_t*value) {
    double x=*value/1000.0;if(!scalar(j,0,key,&x,0,86400000)||x!=(uint64_t)x)return 0;
    *value=(uint64_t)x*1000;return 1;
}
static int choose(const Json*j,const char*key,int*out,const char*const*names,int count) {
    int f=nrField(j,0,key);if(f<0)return 1;
    for(int i=0;i<count;i++)if(nrEqual(j,f,names[i])){*out=i;return 1;}
    return 0;
}
int nrEventPath(const char *path) {
    if(!path||path[0]!='/'||!path[1])return 0;
    int start=1;
    for(int i=1;;i++) {
        char ch=path[i];
        if(!ch||ch=='/') {
            if(i==start|| (i-start==1&&path[start]=='.') ||
               (i-start==2&&path[start]=='.'&&path[start+1]=='.'))return 0;
            if(!ch)return 1;start=i+1;
        } else if(!((ch>='a'&&ch<='z')||(ch>='A'&&ch<='Z')||
                    (ch>='0'&&ch<='9')||ch=='_'||ch=='-'||ch=='.'))return 0;
    }
}
static int decodeActions(const Json*j,Message*m) {
    int f=nrField(j,0,"actions");if(f<0)return 1;
    if(j->tokens[f].type!=J_ARRAY||j->tokens[f].count>NR_NOTIFICATION_ACTIONS)return 0;
    m->actionCount=j->tokens[f].count;int at=f+1;
    for(int i=0;i<m->actionCount;i++) {
        NotificationAction*a=&m->actions[i];
        if(!nrAllowed(j,at,"id label event value dismiss"))return 0;
        if(!whole(j,at,"id",&a->id,1,65535)||!a->id)return 0;
        int label=nrField(j,at,"label"),event=nrField(j,at,"event");
        if(label<0||(a->labelCount=nrDecode(j,label,a->label,NR_ACTION_LABEL))<=0)return 0;
        if(event<0||nrString(j,event,a->event,sizeof(a->event))<0||!nrEventPath(a->event))return 0;
        if(!scalar(j,at,"value",&a->value,-1000000,1000000)||!flag(j,at,"dismiss",&a->dismiss))return 0;
        for(int k=0;k<i;k++)if(a->id==m->actions[k].id)return 0;
        at=j->tokens[at].next;
    }
    return 1;
}
static int compatible(const Message*a,const Message*b) {
    if(a->count!=b->count||memcmp(a->text,b->text,(size_t)a->count*sizeof(uint32_t)))return 0;
    return a->mode==b->mode&&a->priority==b->priority&&a->important==b->important&&
        a->durationUs==b->durationUs&&a->x==b->x&&a->y==b->y&&
        a->actionCount==b->actionCount&&
        !memcmp(a->actions,b->actions,sizeof(a->actions));
}
int nrNotificationCommand(NrContext*c,State*s,const Json*j) {
    static const char*const modes[]={"static","horizontal","vertical","fade","pop","horizontal-fade","vertical-fade"};
    static const char*const policies[]={"none","count","replace-queued"};
    if(!nrAllowed(j,0,"op id area text durationMs mode priority startTimeUs x y key coalesce important actions dwellPerCharacterMs minDurationMs maxDurationMs"))return fail(c,"Unknown notification setting");
    Message candidate;memset(&candidate,0,sizeof(candidate));Message*m=&candidate;
    m->used=1;m->durationUs=6000000;m->readyUs=m->startUs=s->timeUs;m->occurrences=1;
    if(!whole(j,0,"id",&m->id,1,65535)||!whole(j,0,"area",&m->area,0,65535)||
       !whole(j,0,"priority",&m->priority,0,100)||!whole(j,0,"x",&m->x,0,NR_LAYOUT_MAX)||
       !whole(j,0,"y",&m->y,0,NR_LAYOUT_MAX)||!flag(j,0,"important",&m->important))return fail(c,"Notification bounds");
    int field=nrField(j,0,"text");if(field<0||(m->count=nrDecode(j,field,m->text,NR_MAX_TEXT))<0)return fail(c,"Notification text required, within capacity");
    if(m->area) {int found=0;for(int i=0;i<NR_AREAS;i++)found|=s->areas[i].used&&s->areas[i].id==m->area;
        if(!found)return fail(c,"Status area not found");}
    double start=(double)m->readyUs;
    if(!scalar(j,0,"startTimeUs",&start,0,86400000000.0)||start!=(uint64_t)start)return fail(c,"Notification start time");
    m->readyUs=m->startUs=(uint64_t)start;
    if(!millis(j,"durationMs",&m->durationUs)||!choose(j,"mode",&m->mode,modes,7)||!choose(j,"coalesce",&m->coalesce,policies,3))return fail(c,"Notification duration or policy");
    field=nrField(j,0,"key");if(field>=0&&nrString(j,field,m->key,sizeof(m->key))<0)return fail(c,"Notification key capacity");
    if(m->coalesce&&(!m->key[0]||m->important))return fail(c,"Coalescing requires a key and is forbidden for important messages");
    if(!decodeActions(j,m))return fail(c,"Notification action configuration");
    if(nrField(j,0,"dwellPerCharacterMs")>=0) {
        if(nrField(j,0,"durationMs")>=0)return fail(c,"Choose fixed or derived duration, not both");
        double per=0,low=1000,high=60000;
        if(!scalar(j,0,"dwellPerCharacterMs",&per,0,60000)||!scalar(j,0,"minDurationMs",&low,0,86400000)||
           !scalar(j,0,"maxDurationMs",&high,0,86400000)||low>high||per!=(uint64_t)per||low!=(uint64_t)low||high!=(uint64_t)high)return fail(c,"Derived dwell bounds");
        m->durationUs=(uint64_t)nrClamp(per*m->count,low,high)*1000;
    } else if(nrField(j,0,"minDurationMs")>=0||nrField(j,0,"maxDurationMs")>=0)return fail(c,"Derived dwell bounds need dwellPerCharacterMs");
    if(m->coalesce) {
        int chosen=-1;
        for(int i=0;i<NR_MESSAGES;i++) {
            Message*old=&s->messages[i];
            if(!old->used||old->area!=m->area||old->state>=2||strcmp(old->key,m->key)||
               (m->coalesce==2&&old->state!=0))continue;
            if(chosen<0||old->sequence<s->messages[chosen].sequence)chosen=i;
        }
        if(chosen>=0) {
            Message*old=&s->messages[chosen];
            if(old->important||old->coalesce!=m->coalesce)return fail(c,"Existing key has incompatible notification policy");
            if(m->coalesce==1) {
                if(!compatible(old,m)||old->occurrences==0xffffffffu)return fail(c,"Count coalescing requires identical content and available counter");
                old->occurrences++;return 0;
            }
            m->id=old->id;m->sequence=old->sequence;m->replacements=old->replacements+1;
            if(!m->replacements)return fail(c,"Replacement counter exhausted");
            *old=*m;nrStatusTick(s);return 0;
        }
    }
    if(!m->id) {
        for(;;) {
            if(s->nextMessageId>65535)return fail(c,"Notification identity capacity exhausted");
            m->id=(int)s->nextMessageId++;int found=0;
            for(int i=0;i<NR_MESSAGES;i++)found|=s->messages[i].used&&s->messages[i].id==m->id;
            if(!found)break;
        }
    }
    int slot=-1;
    for(int i=0;i<NR_MESSAGES;i++)if(s->messages[i].used&&s->messages[i].id==m->id){slot=i;break;}
    if(slot>=0&&s->messages[slot].important&&!s->messages[slot].acknowledged)return fail(c,"Acknowledge important record before replacement");
    if(slot<0)for(int i=0;i<NR_MESSAGES;i++)if(!s->messages[i].used){slot=i;break;}
    if(slot<0)return fail(c,"Notification history full; explicitly acknowledge/dismiss/purge records");
    m->sequence=++s->nextMessage;s->messages[slot]=*m;nrStatusTick(s);return 0;
}
int nrNotificationActivate(NrContext*c,State*s,int id,int actionId) {
    Message*m=0;for(int i=0;i<NR_MESSAGES;i++)if(s->messages[i].used&&s->messages[i].id==id){m=&s->messages[i];break;}
    if(!m||m->state!=1)return fail(c,"Notification is not active");
    int index=-1;for(int i=0;i<m->actionCount;i++)if(m->actions[i].id==actionId)index=i;
    if(index<0)return fail(c,"Notification action does not exist");
    if(m->actionMask&(1u<<index))return 0;
    int slot=-1;for(int i=0;i<NR_INTENTS;i++)if(!s->intents[i].used){slot=i;break;}
    if(slot<0||s->nextIntent>9007199254740991ull)return fail(c,"Intent capacity reached; acknowledge consumed intentions");
    NotificationAction*a=&m->actions[index];Intent*q=&s->intents[slot];memset(q,0,sizeof(*q));
    memset(&s->intentPayloads[slot],0,sizeof(IntentPayload));
    q->used=1;q->id=s->nextIntent++;q->messageId=m->id;q->actionId=a->id;q->messageSequence=m->sequence;
    q->atUs=s->timeUs;q->value=a->value;memcpy(q->event,a->event,sizeof(q->event));
    m->actionMask|=1u<<index;
    if(a->dismiss) {
        m->state=3;
        for(int i=0;i<NR_AREAS;i++)if(s->areas[i].used&&s->areas[i].id==m->area)s->areas[i].availableUs=s->timeUs+s->areas[i].gapUs;
        nrStatusTick(s);
    }
    return nrEvaluateValues(c,s)?0:fail(c,"Notification trigger target rejected; action retained");
}
