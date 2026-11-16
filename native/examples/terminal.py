#!/usr/bin/env python3
"""Standalone POSIX terminal demonstration of the direct native C API.

The host owns time, raw mode, signal cleanup and stdout. Draft input is never executed.
UI applications should copy the binding's owned cells into their own framework buffer.
"""
from __future__ import annotations
import argparse,codecs,fcntl,json,os,re,selectors,signal,struct,sys,termios,time,tty
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
sys.path.insert(0,str(ROOT/'hosts/python'))
from document_store import load_document,save_document
from unicode_document_view import UnicodeDocumentView

class Host:
 def __init__(self,args):
  self.args=args;self.scene=NativeScene(args.seed);self.recipes=json.loads((ROOT/'recipes.json').read_text());self.running=True;self.paused=args.paused;self.logical=0.;self.lastWall=time.monotonic();self.buffer=bytearray();self.previous=None;self.frameSize=None;self.current=0;self.decoder=codecs.getincrementaldecoder('utf-8')('strict');self.interrupted=False;self.pasting=False;self.clipboard=''
  self.load(args.scene)
 def size(self):
  size=os.get_terminal_size(sys.stdout.fileno());return max(1,size.columns),max(1,size.lines)
 def load(self,name):
  self.current=next((i for i,r in enumerate(self.recipes)if r['id']==name),0);preserve=getattr(self,'document_loaded',False)
  self.scene.command({'op':'reset','seed':self.args.seed,'preservePrompt':preserve})
  for command in self.recipes[self.current]['commands']:
   if preserve and command['op'] in ('prompt','draft','input','paste','key'):continue
   self.scene.command(command)
  self.document_loaded=True
  w,h=self.size();self.scene.command({'op':'resize','width':w,'height':h});self.scene.command({'op':'pause','paused':self.paused});self.logical=0.;self.lastWall=time.monotonic();self.previous=None
 def paint(self):
  frame=self.scene.render()
  if getattr(getattr(self,'args',None),'unicode_document',False):
   if not hasattr(self,'unicodeView'):self.unicodeView=UnicodeDocumentView()
   rendered=self.unicodeView.paint(self.scene,frame.width,frame.height)
   if rendered is not None:
    if rendered!=getattr(self,'unicodePrevious',None):sys.stdout.write(rendered);sys.stdout.flush()
    self.unicodePrevious=rendered;self.previous=None;self.frameSize=(frame.width,frame.height);return
   self.unicodePrevious=None
   sys.stdout.write('\x1b[?25l')
  words=frame.words();out=[];lastStyle=None
  for row in range(frame.height):
   start=row*frame.width*16;end=start+frame.width*16
   if self.previous is not None and self.previous[start:end]==frame.bytes[start:end]:continue
   out.append(f'\x1b[{row+1};1H')
   for g,fg,bg,_ in words[row*frame.width:(row+1)*frame.width]:
    style=(fg,bg)
    if style!=lastStyle:out.append(f'\x1b[38;2;{fg>>16&255};{fg>>8&255};{fg&255};48;2;{bg>>16&255};{bg>>8&255};{bg&255}m');lastStyle=style
    out.append(chr(g)if g>=32 and g!=127 and not 0xd800<=g<=0xdfff else ' ')
  if out:sys.stdout.write(''.join(out));sys.stdout.flush()
  self.previous=frame.bytes;self.frameSize=(frame.width,frame.height)
 def key(self,key,ctrl=False):
  if not ctrl and hasattr(self,'unicodeView') and self.unicodeView.move(self.scene,key):return
  self.scene.command({'op':'key','key':key,'ctrl':ctrl,'unit':'grapheme' if getattr(getattr(self,'args',None),'unicode_document',False) else 'scalar'})
 def clipboard_action(self,action):
  info=self.scene.info()
  if info.get('inputOwner')!='prompt':return
  p=info['prompt'];anchor=p['anchor'];caret=p['caret']
  if action=='paste':
   text=getattr(self,'clipboard','')
   if text:self.scene.command({'op':'paste','text':text})
   return
  if action=='cut' and (anchor<0 or anchor==caret):return
  text=p['text'] if anchor<0 else self.scene.selected_text()
  if text is None:return
  self.clipboard=text
  if action=='cut':self.scene.command({'op':'key','key':'Delete'})
 def input(self,data):
  self.buffer.extend(data)
  while self.buffer:
   if self.pasting:
    end=self.buffer.find(b'\x1b[201~')
    if end<0:return
    text=bytes(self.buffer[:end]).decode('utf-8','strict');del self.buffer[:end+6];self.pasting=False
    self.scene.command({'op':'paste','text':text});self.paint();continue
   if self.buffer.startswith(b'\x1b[200~'):
    del self.buffer[:6];self.pasting=True;continue
   b=self.buffer[0]
   if b==27:
    if self.buffer.startswith(b'\x1bw'):
     del self.buffer[:2];self.clipboard_action('copy');self.paint();continue
    shifted={b'\x1b[1;2A':'ArrowUp',b'\x1b[1;2B':'ArrowDown',b'\x1b[1;2C':'ArrowRight',b'\x1b[1;2D':'ArrowLeft',b'\x1b[1;2H':'Home',b'\x1b[1;2F':'End'}
    sequence=next((s for s in shifted if self.buffer.startswith(s)),None)
    if sequence:
     del self.buffer[:len(sequence)]
     if not (hasattr(self,'unicodeView') and self.unicodeView.move(self.scene,shifted[sequence],True)):self.scene.command({'op':'key','key':shifted[sequence],'shift':True})
     self.paint();continue
    if any(s.startswith(self.buffer) for s in shifted):return
    mouse=re.match(rb'\x1b\[<(\d+);(\d+);(\d+)([Mm])',self.buffer)
    if mouse:
     # Match groups reference the mutable bytearray. Copy the terminator
     # BEFORE removing bytes, including when multiple events share one read.
     code,x,y,terminator=int(mouse[1]),int(mouse[2])-1,int(mouse[3])-1,mouse[4];self.buffer[:mouse.end()]=b''
     if code&64:
      if not (hasattr(self,'unicodeView') and self.unicodeView.scroll_by(self.scene,3 if code&1 else -3)):self.scene.command({'op':'wheel','x':x,'y':y,'delta':-1 if code&1 else 1,'shift':bool(code&4)})
     elif hasattr(self,'unicodeView') and self.unicodeView.pointer(self.scene,'up' if terminator==b'm' else 'move' if code&32 else 'down',x,y,bool(code&4)):pass
     else:self.scene.command({'op':'pointer','phase':'up'if terminator==b'm'else'move'if code&32 else'down','x':x,'y':y,'button':code&3 if code&3<3 else 0,'shift':bool(code&4),'alt':bool(code&8)})
     self.paint();continue
    known={b'\x1b[A':'ArrowUp',b'\x1b[B':'ArrowDown',b'\x1b[C':'ArrowRight',b'\x1b[D':'ArrowLeft',b'\x1b[H':'Home',b'\x1b[F':'End',b'\x1bOP':'F1',b'\x1b[11~':'F1',b'\x1bOQ':'F2',b'\x1b[12~':'F2',b'\x1b[17~':'F6',b'\x1b[5~':'PageUp',b'\x1b[6~':'PageDown',b'\x1b[3~':'Delete'}
    seq=next((s for s in known if self.buffer.startswith(s)),None)
    if seq:
     del self.buffer[:len(seq)];key=known[seq]
     if key=='F2':self.load(self.recipes[(self.current+1)%len(self.recipes)]['id'])
     else:self.key(key)
     self.paint();continue
    if len(self.buffer)==1 or self.buffer.startswith(b'\x1b[<') or b'\x1b[200~'.startswith(self.buffer) or any(s.startswith(self.buffer)for s in known):return
    del self.buffer[0];self.key('Escape');self.paint();continue
   del self.buffer[0]
   if b in (3,17):self.running=False;return
   if b==16:self.paused=not self.paused;self.scene.command({'op':'pause','paused':self.paused});self.lastWall=time.monotonic()
   elif b in (23,25):self.clipboard_action('cut' if b==23 else 'paste')
   elif b in (1,5,26):self.key(chr(96+b),True)
   elif b in (8,127):self.key('Backspace')
   elif b in (10,13):self.key('Enter')
   elif b==9:
    for _ in range(4):self.key(' ')
   elif b>=32:
    text=self.decoder.decode(bytes([b]));
    if text:
     for char in text:self.key(char)
   self.paint()
 def run(self):
  fd=sys.stdin.fileno();before=termios.tcgetattr(fd);start=time.monotonic();nextFrame=start;lastInput=start;selector=selectors.DefaultSelector();selector.register(fd,selectors.EVENT_READ)
  savedSignals={}
  def stop(*_):self.running=False
  for sig in (signal.SIGTERM,signal.SIGHUP):savedSignals[sig]=signal.signal(sig,stop)
  try:
   tty.setraw(fd);sys.stdout.write('\x1b[?1049h\x1b[?25l\x1b[?7l\x1b[?1003h\x1b[?1006h\x1b[?2004h');sys.stdout.flush();self.paint()
   while self.running:
    now=time.monotonic()
    if self.args.max_seconds and now-start>=self.args.max_seconds:break
    events=selector.select(max(0,min(.05,nextFrame-now)))
    for _,_ in events:
     raw=os.read(fd,4096)
     if not raw:self.running=False;break
     self.input(raw);lastInput=time.monotonic()
    now=time.monotonic()
    if self.buffer==b'\x1b'and now-lastInput>.05:self.buffer.clear();self.key('Escape');self.paint()
    w,h=self.size()
    if (w,h)!=self.frameSize:self.scene.command({'op':'resize','width':w,'height':h});self.previous=None;self.paint()
    if now>=nextFrame:
     if not self.paused:
      self.logical+=(now-self.lastWall)*1e6;self.scene.command({'op':'time','timeUs':int(self.logical),'budget':240})
     self.lastWall=now;nextFrame=now+1/self.args.fps;self.paint()
  finally:
   selector.close();termios.tcsetattr(fd,termios.TCSANOW,before)
   sys.stdout.write('\x1b[0m\x1b[?1002l\x1b[?1003l\x1b[?1006l\x1b[?2004l\x1b[?7h\x1b[?25h\x1b[?1049l');sys.stdout.flush()
   for sig,handler in savedSignals.items():signal.signal(sig,handler)
   if self.args.info_on_exit:Path(self.args.info_on_exit).write_text(json.dumps({**self.scene.info(),'hostViewport':self.frameSize,'hostScene':self.recipes[self.current]['id']},indent=2)+'\n')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--scene',default='autumn');p.add_argument('--fps',type=int,default=60);p.add_argument('--seed',type=int,default=2030);p.add_argument('--paused',action='store_true');p.add_argument('--info-on-exit');p.add_argument('--max-seconds',type=float,default=0);p.add_argument('--load-document',type=Path);p.add_argument('--save-document',type=Path);p.add_argument('--unicode-document',action='store_true',help='Render the document using native wrapped bidi/grapheme layout');args=p.parse_args()
 if not 1<=args.fps<=120:p.error('fps: 1..120')
 if not sys.stdin.isatty()or not sys.stdout.isatty():p.error('A POSIX terminal is required.')
 host=Host(args)
 try:
  if args.load_document:load_document(host.scene,args.load_document)
  host.run()
  if args.save_document:save_document(host.scene,args.save_document)
 finally:
  host.scene.close()
if __name__=='__main__':main()
