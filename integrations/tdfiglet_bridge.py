#!/usr/bin/env python3
"""Rasterize an installed TD Figlet fork once, then animate its cell art.

No bundled fonts, shell evaluation, per-frame subprocess, or terminal escape replay.
Verified CLI reference: a fork of tat3r/tdfiglet with classic TDF support, at commit
94e212569244229f78b23aade9053940e6dcb6fa. Actual binary execution is host-dependent.
"""
from __future__ import annotations
import argparse,json,os,re,selectors,subprocess,time
from pathlib import Path
ANSI=[0x000000,0xaa0000,0x00aa00,0xaa5500,0x0000aa,0xaa00aa,0x00aaaa,0xaaaaaa,0x555555,0xff5555,0x55ff55,0xffff55,0x5555ff,0xff55ff,0x55ffff,0xffffff]

def indexedColor(index):
    if not 0<=index<=255:raise ValueError('palette index')
    if index<16:return ANSI[index]
    if index>=232:g=8+(index-232)*10;return g*0x10101
    n=index-16;v=[0,95,135,175,215,255];return (v[n//36]<<16)|(v[n//6%6]<<8)|v[n%6]

def parseAnsi(source:str,maxWidth=None,maxHeight=None,maxCells=8*1024*1024):
    """Decode a bounded UTF-8 ANSI art string into {width,height,cells}.

    Supports SGR 16/256/truecolor, bold-bright ANSI, CR/LF. Discards OSC, DCS,
    all non-SGR CSI and other controls. Cursor positioning is NOT an art primitive.
    No implicit width/height ceiling; optional caller bounds remain available.
    maxCells bounds the padded rectangle before allocation, not either axis.
    Raises ValueError on resource/color limits. Example: parseAnsi('\\x1b[31mA').
    """
    if len(source.encode('utf-8'))>8*1024*1024:raise ValueError('ANSI payload too large')
    if not isinstance(maxCells,int) or isinstance(maxCells,bool) or maxCells<1:raise ValueError('Invalid cell budget')
    source=re.sub(r'\x1b\][^\x07\x1b]*(?:\x07|\x1b\\|$)','',source)
    source=re.sub(r'\x1b[P^_].*?(?:\x1b\\|$)','',source,flags=re.S)
    rows=[[]];fg=0xdddddd;bg=0;bold=False;ansiFg=None;pos=0
    for token in re.finditer(r'\x1b\[[0-?]*[ -/]*[@-~]|\x1b.|[^\x1b]',source,re.S):
        s=token.group()
        if s.startswith('\x1b['):
            if not s.endswith('m'):continue
            raw=s[2:-1]
            if ':' in raw:continue
            try:values=[int(v or '0') for v in raw.split(';')]
            except ValueError:continue
            i=0
            while i<len(values):
                v=values[i]
                if v==0:fg=0xdddddd;bg=0;bold=False;ansiFg=None
                elif v==1:bold=True
                elif v==22:bold=False
                elif 30<=v<=37:ansiFg=v-30;fg=ANSI[ansiFg+(8 if bold else 0)]
                elif 90<=v<=97:ansiFg=None;fg=ANSI[v-90+8]
                elif 40<=v<=47:bg=ANSI[v-40]
                elif 100<=v<=107:bg=ANSI[v-100+8]
                elif v==39:fg=0xdddddd;ansiFg=None
                elif v==49:bg=0
                elif v in (38,48) and i+1<len(values):
                    color=None
                    if values[i+1]==5 and i+2<len(values):color=indexedColor(values[i+2]);i+=2
                    elif values[i+1]==2 and i+4<len(values):
                        r,g,b=values[i+2:i+5]
                        if not all(0<=c<=255 for c in (r,g,b)):raise ValueError('RGB out of bounds')
                        color=(r<<16)|(g<<8)|b;i+=4
                    if color is not None:
                        if v==38:fg=color;ansiFg=None
                        else:bg=color
                if ansiFg is not None:fg=ANSI[ansiFg+(8 if bold else 0)]
                i+=1
            continue
        if s.startswith('\x1b'):continue
        if s=='\n':
            if maxHeight is not None and len(rows)>=maxHeight and source[token.end():].strip():raise ValueError('art too tall')
            rows.append([]);continue
        if s=='\r':continue
        if ord(s)<32 or 0x7f<=ord(s)<0xa0:continue
        if maxWidth is not None and len(rows[-1])>=maxWidth:raise ValueError('art too wide')
        rows[-1].append((ord(s),fg,bg,0))
    while len(rows)>1 and not rows[-1]:rows.pop()
    width=max((len(r) for r in rows),default=0)
    if not width:return {'width':1,'height':1,'cells':[0,0xdddddd,0,0]}
    if width*len(rows)>maxCells:raise ValueError('Art rectangle exceeds cell budget')
    cells=[]
    for row in rows:
        for cell in row+[(0,0xdddddd,0,0)]*(width-len(row)):cells.extend(cell)
    return dict(width=width,height=len(rows),cells=cells)

def commandFor(binary,font,subfont,text,width):
    """Build an argv vector; caller text is one positional argument, never shell code."""
    if not 0<=subfont<=65535 or not isinstance(width,int) or isinstance(width,bool) or not 1<=width<=2147483647 or len(text)>512 or '\x00' in text:raise ValueError('invalid CLI argument bounds')
    return [str(binary),'-f',str(font),'-n',str(subfont),'-j','l','-w',str(width),'-c','a','-e','u','--',text]

def renderFont(binary,font,subfont,text,width=100,timeout=5,maxBytes=8*1024*1024):
    """Run a local renderer with a timeout and combined output bound (POSIX).

    Returns parsed cell art with provenance. Raises ValueError/TimeoutError/OSError
    on invalid output/timeout/missing executable. No network access is performed.
    """
    argv=commandFor(binary,font,subfont,text,width)
    proc=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    selector=selectors.DefaultSelector();buffers={proc.stdout:bytearray(),proc.stderr:bytearray()}
    for stream in buffers:selector.register(stream,selectors.EVENT_READ)
    deadline=time.monotonic()+timeout;total=0
    try:
        while selector.get_map():
            if time.monotonic()>=deadline:raise TimeoutError('tdfiglet timeout')
            for key,_ in selector.select(min(.1,max(0,deadline-time.monotonic()))):
                chunk=os.read(key.fileobj.fileno(),65536)
                if not chunk:selector.unregister(key.fileobj);continue
                total+=len(chunk)
                if total>maxBytes:raise ValueError('tdfiglet output limit')
                buffers[key.fileobj].extend(chunk)
        code=proc.wait(timeout=max(.01,deadline-time.monotonic()))
        if code:raise ValueError(f'tdfiglet exited {code}: '+buffers[proc.stderr].decode('utf-8','replace')[:500])
        art=parseAnsi(buffers[proc.stdout].decode('utf-8','strict'),maxWidth=width)
        art['provenance']={'binary':str(binary),'fontPath':str(font),'subfont':subfont,'text':text,'adapterVersion':2}
        return art
    finally:
        if proc.poll() is None:proc.kill();proc.wait()
        selector.close();proc.stdout.close();proc.stderr.close()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--binary',default='tdfiglet');p.add_argument('--font',required=True);p.add_argument('--subfont',type=int,default=0);p.add_argument('--width',type=int,default=100);p.add_argument('--output',type=Path,required=True);p.add_argument('text');a=p.parse_args();art=renderFont(a.binary,a.font,a.subfont,a.text,a.width);a.output.write_text(json.dumps(art,indent=2)+'\n');print(f'{art["width"]} × {art["height"]} cells → {a.output}')
if __name__=='__main__':main()
