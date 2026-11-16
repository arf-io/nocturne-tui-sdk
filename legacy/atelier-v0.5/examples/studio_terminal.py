#!/usr/bin/env python3
"""Interactive Nocturne Studio in a POSIX terminal or tmux pane.

Ctrl+Q quit; Ctrl+N next scene; Ctrl+T palette; Ctrl+P motion pause; Ctrl+O modal;
Ctrl+F independent mock feed; Ctrl+R nova; Ctrl+L clear prompt; Tab/arrows focus;
Enter inspect; Escape close modal; click inspect/ripple; shift-click nova.
Typed text is inert. No shell command is executed. --data-fd accepts bounded JSONL
on a pipe: {"type":"value","value":670}, {"type":"prompt","text":"hello"}.
"""
from __future__ import annotations
import argparse,json,os,selectors,shutil,signal,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from studio import Studio,Node,Impulse
from terminal import MotionClock,AnsiWriter
from interaction import InputDecoder,FocusModel

SCENES=json.loads((ROOT/'studio.scenes.json').read_text())['scenes']
PALETTES=json.loads((ROOT/'palettes.json').read_text())['palettes']

class Session:
    """Demo scene/controller. Scene data is explicitly synthetic; library is generic."""
    def __init__(self,sceneId,paletteId):
        self.index=next(i for i,s in enumerate(SCENES) if s['id']==sceneId);self.paletteIndex=next(i for i,p in enumerate(PALETTES) if p['id']==paletteId)
        self.studio=Studio();self.text='';self.value=670;self.events=[];self.selected=None;self.modal=False;self.details='Select a component';self.width=100;self.height=32;self.commits=0;self.frames=0;self.nodes=[];self.focus=FocusModel([]);self.timeMs=0;self.sceneAt=0;self.collapsed=set();self.configure()
    def configure(self):
        scene=SCENES[self.index];p=PALETTES[self.paletteIndex];self.studio=Studio(**scene['config']);self.studio.configure(width=self.width,height=self.height,palette=p['colors'],starPalette=p['colors'],baseColor=p['background'],inkColor=p['ink'])
        self.focus=FocusModel([n['id'] for n in scene['nodes'] if n.get('id') and n['id']!=100],{n['id'] for n in scene['nodes'] if n.get('id') and n.get('state')==3})
    def changeScene(self):
        self.index=(self.index+1)%len(SCENES);self.sceneAt=self.timeMs;self.modal=False;self.events=[];self.selected=None;self.configure()
    def ripple(self,x,y,nova=False):
        self.events.append(Impulse(x,y,kind=1 if nova else 0,atMs=self.timeMs,id=self.commits));self.events=self.events[-96:]
    def build(self,playing=True):
        records=json.loads(json.dumps(SCENES[self.index]['nodes']))
        if SCENES[self.index]['id']=='knowledge':records=[n for n in records if not (40 in self.collapsed and n.get('id') in (41,42)) and not (43 in self.collapsed and n.get('id') in (44,45))]
        for n in records:
            if n.get('id')==100:n['text']='› '+self.text
            if n['kind']=='progress':n['value']=self.value
            if n['kind']=='digits' and SCENES[self.index]['id']=='dashboard':n['text']=f'{round(self.value/10):03}'
            if n['kind'] in ('bars','pie','donut'):n.update(changedMs=self.sceneAt,durationMs=850 if playing else 0)
            if n.get('text','').startswith('67%'):n['text']=f'{self.value/10:.1f}% / data commit {self.commits}'
            if n.get('id') and n.get('state')!=3:
                if n['id']==self.selected:n.update(state=2,bgOpacity=max(n.get('bgOpacity',0),300))
                elif n['id']==self.focus.current:n.update(state=1,bgOpacity=max(n.get('bgOpacity',0),230))
            if SCENES[self.index]['id']=='logwatch' and n.get('id')==86:n['text']=f'LIVE   event {self.commits} / value {self.value}'
        if self.modal:
            records.extend([dict(kind='box',x=24,y=9,width=54,height=17,id=900,text='  GLASS / INSPECTOR  ',bg='#241c30',bgOpacity=680,colorAnimation=2),dict(kind='text',x=28,y=13,width=45,height=8,text=self.details),dict(kind='button',x=42,y=22,width=19,height=3,id=901,text='CLOSE',colorAnimation=2)])
        self.nodes=[]
        for n in records:
            # Demo-only proportional layout; apps should provide their own layout engine.
            n['x']=n['x']*self.width//100;n['y']=n['y']*self.height//32;n['width']=max(1,n['width']*self.width//100);n['height']=max(1,n['height']*self.height//32)
            self.nodes.append(Node(**n))
        self.nodes.append(Node('text',0,max(0,self.height-1),self.width,1,text=f' ^N scene  ^T palette  ^P pause  ^O glass  ^Q quit | {SCENES[self.index]["name"]} | data {self.commits}',bgOpacity=1000,fg='#a69cab'))
        return self.nodes
    def inspect(self,id,item=0):
        if id==901:self.modal=False;self.focus.popModal();return
        if id==60:self.toggleModal();return
        n=next((n for n in self.nodes if n.id==id),None)
        if not n:return
        self.selected=id;self.focus.current=id
        self.details=f'ID {id} / {n.kind}\n{n.text}\n'
        if n.data:self.details+=f'item {item}: '+str(n.data[item*2:item*2+2] if n.kind=='scatter' else n.data[item] if item<len(n.data) else None)+'\n'+str(n.data)
        for d in SCENES[self.index].get('dag',[]):
            if d['id']==id:self.details+='\nparents: '+str(d['parents'])
        if SCENES[self.index]['id']=='knowledge' and id in (40,43):
            if id in self.collapsed:self.collapsed.remove(id)
            else:self.collapsed.add(id)
        self.modal=True;self.focus.pushModal([901])
    def toggleModal(self):
        self.modal=not self.modal
        if self.modal:self.focus.pushModal([901])
        else:self.focus.popModal()
    def append(self,text):
        self.text=(self.text+text)[:80];self.commits+=1
        pn=next((n for n in self.build() if n.id==100),None)
        if pn:
            x=pn.values[2]+min(len(self.text)+1,max(0,pn.values[4]-1));y=pn.values[3];self.ripple(x,y);self.studio.configure(focusX=x*256,focusY=y*256)
    def data(self,record):
        if not isinstance(record,dict):raise ValueError('JSON object required')
        if record.get('type')=='value':
            v=record.get('value')
            if type(v)is not int or not 0<=v<=1000:raise ValueError('value 0..1000')
            self.value=v
        elif record.get('type')=='prompt':
            if not isinstance(record.get('text'),str) or len(record['text'])>80:raise ValueError('text <=80 scalars')
            self.text=record['text']
        elif record.get('type')=='ripple':self.ripple(int(record['x']),int(record['y']),bool(record.get('nova',False)))
        else:raise ValueError('unknown data event type')
        self.commits+=1

def main():
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter);p.add_argument('--scene',default='starwrite',choices=[s['id'] for s in SCENES]);p.add_argument('--palette',default='smart-dark',choices=[t['id'] for t in PALETTES]);p.add_argument('--fps',type=int,default=30);p.add_argument('--feed',action='store_true');p.add_argument('--no-mouse',action='store_true');p.add_argument('--snapshot-ms',type=int);p.add_argument('--width',type=int,default=100);p.add_argument('--height',type=int,default=32);p.add_argument('--data-fd',type=int);p.add_argument('--metrics',type=Path);a=p.parse_args()
    if not 1<=a.fps<=60 or not 1<=a.width<=512 or not 1<=a.height<=256:p.error('fps 1..60; width 1..512; height 1..256')
    s=Session(a.scene,a.palette);s.width=a.width;s.height=a.height;s.configure();writer=AnsiWriter()
    if a.snapshot_ms is not None:
        s.timeMs=a.snapshot_ms;print(writer.encode(s.studio.render(s.timeMs,nodes=s.build())),end='');return
    if os.name!='posix' or not sys.stdin.isatty() or not sys.stdout.isatty():p.error('interactive mode requires a POSIX tty; use --snapshot-ms for pipe output')
    import termios,tty
    fd=sys.stdin.fileno();old=termios.tcgetattr(fd);decoder=InputDecoder();sel=selectors.DefaultSelector();sel.register(fd,selectors.EVENT_READ,'input');dataBuffer=bytearray()
    if a.data_fd is not None:
        if a.data_fd==fd:p.error('data-fd must differ from keyboard fd')
        sel.register(a.data_fd,selectors.EVENT_READ,'data')
    epoch=time.monotonic()*1000;clock=MotionClock(fps=a.fps,epochMs=epoch);running=True;feed=a.feed;feedDeadline=epoch;lastEscape=epoch;lastSize=None
    handlers={}
    def stop(*_):
        nonlocal running
        running=False
    for sig in (signal.SIGINT,signal.SIGTERM,signal.SIGHUP):handlers[sig]=signal.signal(sig,stop)
    def present():
        s.timeMs=clock.lastMotionMs;frame=s.studio.render(s.timeMs,nodes=s.build(clock.playing),events=s.events);sys.stdout.write(writer.encode(frame));sys.stdout.flush();s.frames+=1
    try:
        tty.setraw(fd);sys.stdout.write('\x1b[?1049h\x1b[?25l\x1b[?7l\x1b[?2004h'+('' if a.no_mouse else '\x1b[?1000h\x1b[?1006h'));sys.stdout.flush()
        while running:
            now=time.monotonic()*1000
            size=shutil.get_terminal_size((a.width,a.height));dim=(max(1,min(512,size.columns)),max(1,min(256,size.lines)))
            if dim!=lastSize:s.width,s.height=dim;s.studio.configure(width=s.width,height=s.height);writer.invalidate();lastSize=dim;present()
            wait=min(.04,clock.untilNextMs(now)/1000)
            for key,_ in sel.select(max(0,wait)):
                raw=os.read(key.fd,16384)
                if not raw:
                    if key.data=='input':running=False
                    else:sel.unregister(key.fd)
                    continue
                if key.data=='data':
                    dataBuffer.extend(raw)
                    if len(dataBuffer)>65536:dataBuffer.clear();s.details='Data pipe exceeded 64 KiB buffer';continue
                    while b'\n' in dataBuffer:
                        line,_,rest=dataBuffer.partition(b'\n');dataBuffer=bytearray(rest)
                        try:s.data(json.loads(line));present()
                        except (ValueError,TypeError,KeyError) as e:s.details=f'Data event rejected: {e}'
                    continue
                # Extra control keys kept separate from character data.
                if raw==b'\x14':s.paletteIndex=(s.paletteIndex+1)%len(PALETTES);s.configure();present();continue
                if raw==b'\x12':s.ripple(s.width//2,s.height//2,True);present();continue
                actions=decoder.feed(raw);lastEscape=now
                for kind,event in actions:
                    if kind=='text':s.append(event)
                    elif kind=='mouse':
                        x,y,bits=event
                        if bits&64:continue
                        hit=s.studio.hit(s.nodes,x,y)
                        if s.modal:
                            if hit and hit[0]==901:s.inspect(901)
                        elif hit and hit[0]!=100:s.inspect(*hit)
                        else:s.ripple(x,y,bool(bits&4));s.studio.configure(focusX=x*256,focusY=y*256)
                    elif event=='quit':running=False
                    elif event=='next':s.changeScene()
                    elif event=='palette':s.paletteIndex=(s.paletteIndex+1)%len(PALETTES);s.configure()
                    elif event=='nova':s.ripple(s.width//2,s.height//2,True)
                    elif event=='pause':clock.setPlaying(not clock.playing,time.monotonic()*1000)
                    elif event=='modal':s.toggleModal()
                    elif event=='feed':feed=not feed
                    elif event=='clear':s.text='';s.commits+=1
                    elif event=='backspace':s.text=s.text[:-1];s.commits+=1
                    elif event in ('tab','down','right','backtab','up','left'):s.focus.move(-1 if event in ('backtab','up','left') else 1)
                    elif event=='enter' and s.focus.current:s.inspect(s.focus.current)
                    elif event=='escape' and s.modal:s.toggleModal()
                    present() # Input never waits for decorative clock.advance().
            now=time.monotonic()*1000
            if now-lastEscape>40 and decoder.flushEscape() and s.modal:s.toggleModal();present()
            if feed and now>=feedDeadline:s.value=(s.commits*37+431)%1001;s.commits+=1;feedDeadline=now+47;present()
            if clock.advance(now):present()
    finally:
        sys.stdout.write('\x1b[?1000l\x1b[?1006l\x1b[?2004l\x1b[?7h\x1b[0m\x1b[?25h\x1b[?1049l');sys.stdout.flush();termios.tcsetattr(fd,termios.TCSADRAIN,old);sel.close()
        for sig,handler in handlers.items():signal.signal(sig,handler)
        if a.metrics:a.metrics.write_text(json.dumps(dict(frames=s.frames,dataCommits=s.commits,timeMs=s.timeMs,playing=clock.playing,text=s.text,value=s.value),indent=2)+'\n')
if __name__=='__main__':main()
