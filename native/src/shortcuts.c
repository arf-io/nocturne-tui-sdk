#include "internal.h"
/* Host-owned capability negotiation. No context, callbacks or retained input. */
typedef struct {
    uint32_t edge[64][8],counts[64];
    int order[64][256];
    int owner[256],selected[64];
    unsigned char visited[256];
    uint32_t hostCount;
} ShortcutGraph;
static int shortcutMatch(ShortcutGraph*g,int action){
    for(uint32_t i=0;i<g->counts[action];i++){
        uint32_t chord=(uint32_t)g->order[action][i];
        if(!(g->edge[action][chord>>5]&(1u<<(chord&31)))||g->visited[chord])continue;
        g->visited[chord]=1;
        if(g->owner[chord]<0||shortcutMatch(g,g->owner[chord])){
            g->owner[chord]=action;g->selected[action]=(int)chord;return 1;
        }
    }return 0;
}
static int shortcutWords(const uint32_t*p,uint32_t count){return !count||(p&&!((uintptr_t)p&3));}
static int shortcutKey(uint32_t key){return key&&key<=0x11ffff&&!(key>=0xd800&&key<=0xdfff);}
int nrNegotiateShortcuts(const uint32_t*actions,uint32_t actionCount,const uint32_t*candidates,uint32_t candidateCount,const uint32_t*host,uint32_t hostCount,uint32_t*out,uint32_t capacity){
    if(actionCount>64||candidateCount>256||hostCount>256||!shortcutWords(actions,actionCount)||!shortcutWords(candidates,candidateCount)||!shortcutWords(host,hostCount)||(!out&&capacity)||(out&&((uintptr_t)out&3)))return -1;
    ShortcutGraph g={.hostCount=hostCount};
    for(uint32_t i=0;i<actionCount;i++){
        if(!actions[i])return -1;g.selected[i]=-1;
        for(uint32_t j=0;j<i;j++)if(actions[i]==actions[j])return -1;
    }
    for(uint32_t i=0;i<hostCount;i++){
        const uint32_t*h=host+i*3;if(!shortcutKey(h[0])||h[1]>15||h[2]>1)return -1;g.owner[i]=-1;
        for(uint32_t j=0;j<i;j++)if(h[0]==host[j*3]&&h[1]==host[j*3+1])return -1;
    }
    /* Candidate order is preserved separately from the host's capability order. */
    for(uint32_t i=0;i<candidateCount;i++){
        const uint32_t*c=candidates+i*3;if(!shortcutKey(c[1])||c[2]>15)return -1;
        uint32_t a=0;while(a<actionCount&&actions[a]!=c[0])a++;if(a==actionCount)return -1;
        for(uint32_t h=0;h<hostCount;h++)if(!host[h*3+2]&&host[h*3]==c[1]&&host[h*3+1]==c[2]){
            uint32_t bit=1u<<(h&31);if(!(g.edge[a][h>>5]&bit)){g.edge[a][h>>5]|=bit;g.order[a][g.counts[a]++]=(int)h;}break;
        }
    }
    if(!out&&!capacity)return (int)actionCount;if(capacity<actionCount)return -1;
    /* Insert later actions first. Augmenting paths maximize assigned actions;
     * each search traverses application candidate order. This is deterministic,
     * but does not promise lexicographic optimality of all preferences. */
    for(int a=(int)actionCount-1;a>=0;a--){memset(g.visited,0,sizeof(g.visited));shortcutMatch(&g,a);}
    uint32_t rows[64*4];for(uint32_t a=0;a<actionCount;a++){
        int h=g.selected[a];rows[a*4]=actions[a];rows[a*4+1]=h<0?0:host[h*3];rows[a*4+2]=h<0?0:host[h*3+1];rows[a*4+3]=h>=0;
    }
    if(actionCount)memcpy(out,rows,actionCount*4*sizeof(uint32_t));return (int)actionCount;
}
