"""Optional host reference models. No application actions, threads or terminal I/O.

These models complement the shared renderer. Other languages may retain their
framework's own focus, DAG layout, input decoder and scheduling implementations.
"""
from __future__ import annotations
import codecs,re
from collections import deque
from studio import tween,integer

class Dag:
    """Validated DAG preserving node identity and multiple parents.

    Inputs: unique hashable IDs and unique directed (parent,child) edges.
    Raises ValueError for duplicate IDs/edges, unknown endpoints or cycles.
    Example: Dag([1,2,3],[(1,3),(2,3)]).parents(3) returns [1,2].
    """
    def __init__(self,nodes,edges):
        self.nodes=list(nodes);self.edges=list(map(tuple,edges))
        if len(set(self.nodes))!=len(self.nodes) or len(set(self.edges))!=len(self.edges):raise ValueError('duplicate node/edge')
        known=set(self.nodes)
        if any(len(e)!=2 or e[0] not in known or e[1] not in known for e in self.edges):raise ValueError('unknown edge endpoint')
        self.levels()
    def parents(self,node):
        """Return direct parents in declared edge order; no synthetic duplicates."""
        if node not in self.nodes:raise KeyError(node)
        return [a for a,b in self.edges if b==node]
    def children(self,node):
        """Return direct children; a node may occur under several parents by reference."""
        if node not in self.nodes:raise KeyError(node)
        return [b for a,b in self.edges if a==node]
    def ancestors(self,node):
        """Return all transitive parents as an identity-preserving set."""
        seen=set();queue=deque(self.parents(node))
        while queue:
            item=queue.popleft()
            if item not in seen:seen.add(item);queue.extend(self.parents(item))
        return seen
    def levels(self):
        """Stable topological levels; raises ValueError for cycles."""
        degree={n:0 for n in self.nodes}
        for _,b in self.edges:degree[b]+=1
        result=[];done=set()
        while len(done)<len(self.nodes):
            layer=[n for n in self.nodes if n not in done and degree[n]==0]
            if not layer:raise ValueError('graph contains a cycle')
            result.append(layer);done.update(layer)
            for a,b in self.edges:
                if a in layer:degree[b]-=1
        return result

class FocusModel:
    """Keyboard focus independent of selection, with modal push/pop restoration."""
    def __init__(self,order,disabled=()):self.order=list(dict.fromkeys(order));self.disabled=set(disabled);self.current=None;self.stack=[]
    def move(self,direction):
        """Cycle enabled IDs. Positive moves forward; negative backward; empty -> None."""
        live=[x for x in self.order if x not in self.disabled]
        if not live:self.current=None;return None
        if self.current not in live:self.current=live[0 if direction>=0 else -1]
        else:self.current=live[(live.index(self.current)+(1 if direction>=0 else -1))%len(live)]
        return self.current
    def pushModal(self,order):
        """Trap focus to supplied IDs and save the former focus context."""
        self.stack.append((self.order,self.disabled,self.current));self.order=list(order);self.disabled=set();self.current=None
    def popModal(self):
        """Restore the previous focus context. Empty stack is a no-op."""
        if self.stack:self.order,self.disabled,self.current=self.stack.pop()

class KeyframeTrack:
    """Piecewise scalar keyframes using native integer interpolation.

    Inputs: at least one (timeMs,value) pair, strictly increasing timestamps,
    signed 32-bit values. Looping is explicit. Example: [(0,0),(600,1000)].
    """
    def __init__(self,frames,easing=1,loop=False):
        self.frames=[(integer(t,0,2**32-1,'keyframe time'),integer(v,-2147483648,2147483647,'keyframe value')) for t,v in frames]
        if not self.frames or any(a[0]>=b[0] for a,b in zip(self.frames,self.frames[1:])):raise ValueError('strictly increasing keyframes required')
        self.easing=integer(easing,0,3,'easing');self.loop=bool(loop)
    def sample(self,timeMs):
        """Return the deterministic scalar at explicit time, clamping outside range."""
        integer(timeMs,0,2**64-1,'time')
        if self.loop and self.frames[-1][0]:timeMs%=self.frames[-1][0]
        if timeMs<=self.frames[0][0]:return self.frames[0][1]
        for (a,av),(b,bv) in zip(self.frames,self.frames[1:]):
            if timeMs<=b:return tween(av,bv,timeMs-a,b-a,self.easing)
        return self.frames[-1][1]

class InputDecoder:
    """Incremental UTF-8, arrows and SGR mouse parser for the POSIX demo host.

    feed(bytes) returns normalized ('text',str), ('key',name), or
    ('mouse',(zeroBasedX,zeroBasedY,buttonBits)). Unknown CSI sequences are dropped.
    Bracketed paste emits text only; pasted controls cannot invoke UI actions.
    Bare Escape is resolved by flushEscape() after the host's short ambiguity timeout.
    """
    def __init__(self):self.pasting=False;self.buffer=bytearray();self.decoder=codecs.getincrementaldecoder('utf-8')('replace')
    def feed(self,data):
        self.buffer.extend(data);result=[]
        if len(self.buffer)>65536:self.buffer.clear();raise ValueError('input buffer capacity')
        controls={3:'quit',20:'palette',18:'nova',17:'quit',14:'next',16:'pause',15:'modal',6:'feed',12:'clear',9:'tab',13:'enter',10:'enter',127:'backspace',8:'backspace'}
        while self.buffer:
            if self.buffer[0]==27:
                if len(self.buffer)==1:break
                if self.buffer[1]!=91:
                    del self.buffer[0]
                    if not self.pasting:result.append(('key','escape'))
                    continue
                match=re.match(rb'\x1b\[([0-?]*)([ -/]*)([@-~])',self.buffer)
                if not match:break
                seq=bytes(self.buffer[:match.end()]);del self.buffer[:match.end()]
                if seq==b'\x1b[200~':self.pasting=True;continue
                if seq==b'\x1b[201~':self.pasting=False;continue
                if self.pasting:continue
                if seq in (b'\x1b[A',b'\x1b[B',b'\x1b[C',b'\x1b[D'):result.append(('key',{65:'up',66:'down',67:'right',68:'left'}[seq[-1]]))
                elif seq==b'\x1b[Z':result.append(('key','backtab'))
                else:
                    mouse=re.fullmatch(rb'\x1b\[<(\d{1,5});(\d{1,5});(\d{1,5})M',seq)
                    if mouse:
                        b,x,y=map(int,mouse.groups())
                        if 1<=x<=4096 and 1<=y<=4096:result.append(('mouse',(x-1,y-1,b)))
                continue
            byte=self.buffer.pop(0)
            if self.pasting and (byte<32 or byte==127):continue
            if byte in controls:result.append(('key',controls[byte]));continue
            if byte<32:continue
            text=self.decoder.decode(bytes([byte]))
            if text:result.append(('text',text))
        return result
    def flushEscape(self):
        """Emit bare Escape only when the host's escape ambiguity timeout expires."""
        if self.buffer==b'\x1b':
            self.buffer.clear()
            return [] if self.pasting else [('key','escape')]
        return []
