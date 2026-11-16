#!/usr/bin/env python3
"""Labeled synthetic NDJSON producer for the inherited-pipe integration example.
Writes to stdout only. No provider calls; Ctrl+C or a closed reader exits cleanly.
"""
import json,math,time
AGENTS=('coordinator','research')
seq={a:0 for a in AGENTS}
def emit(agentId,eventType,atMs,payload):
    seq[agentId]+=1
    print(json.dumps(dict(version=1,seq=seq[agentId],agentId=agentId,type=eventType,atMs=atMs,payload=payload)),flush=True)
try:
    for a in AGENTS:
        emit(a,'status',0,{'status':'running'})
        emit(a,'message.start',0,{'messageId':'source-note','role':'system','text':'External pipe connected to the SYNTHETIC example producer. No AI agents are connected.'})
    for tick in range(1000000):
        for i,a in enumerate(AGENTS):
            emit(a,'telemetry',tick*80,dict(tokenRate=round(60+35*math.sin(tick/12+i)),latencyMs=round(190+80*math.sin(tick/17+i)),contextPermille=400+i*170,queue=tick//30%7,tools=tick//10,progressPermille=tick%1000))
        time.sleep(.08)
except (BrokenPipeError,KeyboardInterrupt):
    pass
