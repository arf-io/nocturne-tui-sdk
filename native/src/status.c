#include "internal.h"
/* Status records stay recoverable until explicit purge. Queue dwell starts when
 * activated, not while waiting behind another message. No rendering side effects. */
void nrStatusTick(State*s) {
    for(int a=-1;a<NR_AREAS;a++) {
        Area fallback={.used=1,.id=0};
        Area*area=a<0?&fallback:&s->areas[a];if(!area->used)continue;
        if(area->layout!=1) {
            for(int i=0;i<NR_MESSAGES;i++) {
                Message*m=&s->messages[i];if(!m->used||m->area!=area->id||m->state>=2)continue;
                if(!m->state&&m->readyUs<=s->timeUs){m->state=1;m->startUs=m->readyUs;}
                if(m->state==1&&m->durationUs&&s->timeUs-m->startUs>=m->durationUs)m->state=2;
            }
            continue;
        }
        for(int pass=0;pass<NR_MESSAGES+1;pass++) {
            int active=-1;
            for(int i=0;i<NR_MESSAGES;i++)if(s->messages[i].used&&s->messages[i].area==area->id&&s->messages[i].state==1){active=i;break;}
            if(active>=0) {
                Message*m=&s->messages[active];
                if(!m->durationUs||s->timeUs<m->startUs+m->durationUs)break;
                area->availableUs=m->startUs+m->durationUs+area->gapUs;m->state=2;
            }
            uint64_t earliest=~(uint64_t)0;
            for(int i=0;i<NR_MESSAGES;i++) {
                const Message*m=&s->messages[i];
                if(m->used&&m->area==area->id&&m->state==0&&m->readyUs<earliest)earliest=m->readyUs;
            }
            if(earliest==~(uint64_t)0)break;
            uint64_t start=earliest>area->availableUs?earliest:area->availableUs;
            if(start>s->timeUs)break;
            int chosen=-1;
            for(int i=0;i<NR_MESSAGES;i++) {
                const Message*m=&s->messages[i];
                if(!m->used||m->area!=area->id||m->state||m->readyUs>start)continue;
                if(chosen<0||m->priority>s->messages[chosen].priority||
                  (m->priority==s->messages[chosen].priority&&m->sequence<s->messages[chosen].sequence))chosen=i;
            }
            if(chosen<0)break;
            s->messages[chosen].state=1;s->messages[chosen].startUs=start;
        }
    }
}
