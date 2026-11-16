#!/usr/bin/env python3
"""Interactive, dependency-free POSIX terminal gallery.

Run from the project root: python3 examples/terminal_demo.py --preset black-creme
Controls: Ctrl+N next study; Ctrl+P pause; Ctrl+O modal; Ctrl+F data feed;
Ctrl+L clear prompt; Ctrl+Q quit; arrows change selection; type to edit.
No shell commands or network requests are issued by the input field.
"""
from __future__ import annotations
import argparse
import codecs
import ctypes
import json
import math
import os
from pathlib import Path
import selectors
import shutil
import signal
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne import Surface,Cell
from terminal import AnsiWriter,MotionClock

PRESETS=json.loads((ROOT/'presets.json').read_text())


def main() -> int:
    """Own the terminal until exit, always restoring tty, cursor, and wrap modes."""
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--preset',default='black-creme',choices=[preset['id'] for preset in PRESETS])
    parser.add_argument('--fps',type=int,default=30,help='Decorative motion target; data is not gated by this clock.')
    parser.add_argument('--sync',action='store_true',help='Opt into CSI 2026 synchronized updates on a supporting terminal.')
    parser.add_argument('--feed',action='store_true',help='Enable the independent synthetic ~80 Hz data source.')
    parser.add_argument('--config',type=Path,help='Use a configuration JSON exported by Nocturne-Gallery.html.')
    parser.add_argument('--snapshot',type=int,metavar='MS',help='Emit one ANSI frame at this time without taking over the tty.')
    args=parser.parse_args()
    index=next(i for i,preset in enumerate(PRESETS) if preset['id']==args.preset)
    selectedPreset=PRESETS[index]
    surface=Surface(**selectedPreset['values'])
    if 'palette' in selectedPreset:surface.setPalette(selectedPreset['palette'])
    if 'starPalette' in selectedPreset:surface.setStarPalette(selectedPreset['starPalette'])
    if args.config:
        data=json.loads(args.config.read_text())
        if data.get('schemaVersion')!=1:raise ValueError('Unsupported config schemaVersion')
        surface.configure(**data['values']);surface.setPalette(data['palette']);surface.setStarPalette(data['starPalette'])
        if data.get('glyphs'):surface.setGlyphs(data['glyphs'])
    text=selectedPreset.get('text','Make something that feels alive.')
    if args.snapshot is not None:
        if args.snapshot<0:parser.error('--snapshot must be nonnegative')
        frame=surface.render(args.snapshot,text=text)
        sys.stdout.write(AnsiWriter(args.sync).encode(frame)+'\n')
        return 0
    if os.name!='posix':parser.error('Interactive Python demo uses POSIX tty APIs. Use the browser gallery on Windows.')
    if not (sys.stdin.isatty() and sys.stdout.isatty()):parser.error('Interactive mode needs a tty; use --snapshot MS for redirected output.')
    import termios
    import tty
    oldAttributes=termios.tcgetattr(sys.stdin.fileno())
    oldHandlers={}
    writer=AnsiWriter(args.sync)
    start=time.monotonic_ns()/1e6
    clock=MotionClock(fps=args.fps,epochMs=start)
    selector=selectors.DefaultSelector()
    selector.register(sys.stdin,selectors.EVENT_READ)
    decoder=codecs.getincrementaldecoder('utf-8')('replace')
    feed=args.feed
    nextData=start
    dataCommits=0
    motionSamples=0
    stop=False
    needsResize=True
    pendingEscape=''

    def onStop(_number,_frame):
        nonlocal stop
        stop=True

    def onResize(_number,_frame):
        nonlocal needsResize
        needsResize=True

    def dimensions():
        nonlocal needsResize
        size=shutil.get_terminal_size((84,30))
        surface.configure(width=max(1,min(512,size.columns)),height=max(1,min(256,size.lines-1)))
        writer.invalidate();needsResize=False
        sys.stdout.write('\x1b[2J')

    def renderNow():
        frame=surface.render(clock.lastMotionMs,text=text)
        output=writer.encode(frame)
        size=shutil.get_terminal_size((84,30))
        footer=(f' ^N study {index+1:02}/{len(PRESETS)}  ^P {"pause" if clock.playing else "resume"}  ^O modal  ^F data  ^Q quit'
                f' | motion {motionSamples} data {dataCommits}')[:size.columns]
        sys.stdout.write(output+f'\x1b[{size.lines};1H\x1b[0;38;2;148;140;127m\x1b[48;2;17;16;14m'+footer+'\x1b[K\x1b[0m')
        sys.stdout.flush()

    try:
        for sig in (signal.SIGINT,signal.SIGTERM,signal.SIGWINCH):
            oldHandlers[sig]=signal.getsignal(sig)
            signal.signal(sig,onResize if sig==signal.SIGWINCH else onStop)
        tty.setcbreak(sys.stdin.fileno())
        mode=termios.tcgetattr(sys.stdin.fileno())
        mode[0] &= ~(termios.IXON | termios.IXOFF)
        termios.tcsetattr(sys.stdin.fileno(),termios.TCSANOW,mode)
        sys.stdout.write('\x1b[?1049h\x1b[?25l\x1b[?7l')
        dimensions();clock.advance(start);renderNow()
        while not stop:
            now=time.monotonic_ns()/1e6
            timeoutMs=min(100,clock.untilNextMs(now))
            if feed:timeoutMs=min(timeoutMs,max(0,nextData-now))
            events=selector.select(timeoutMs/1000)
            if events:
                raw=os.read(sys.stdin.fileno(),4096)
                if not raw:break
                incoming=pendingEscape+decoder.decode(raw);pendingEscape=''
                i=0;dirty=False
                while i<len(incoming):
                    ch=incoming[i];i+=1
                    if ch=='\x1b':
                        suffix=incoming[i:]
                        if not suffix or suffix=='[':
                            pendingEscape='\x1b'+suffix;break
                        if suffix.startswith('[') and len(suffix)>=2:
                            code=suffix[1];i+=2
                            if code in 'AB':
                                current=surface.settings()['selection'];surface.configure(selection=(current+(1 if code=='B' else -1))%6,layout=2);dirty=True
                        continue
                    if ch in ('\x11','\x04'):
                        stop=True;break
                    if ch=='\x10':clock.setPlaying(not clock.playing,time.monotonic_ns()/1e6);dirty=True
                    elif ch=='\x0e':
                        index=(index+1)%len(PRESETS);selectedPreset=PRESETS[index]
                        surface=Surface(**selectedPreset['values'])
                        if 'palette' in selectedPreset:surface.setPalette(selectedPreset['palette'])
                        if 'starPalette' in selectedPreset:surface.setStarPalette(selectedPreset['starPalette'])
                        text=selectedPreset.get('text','Make something that feels alive.');dimensions();dirty=True
                    elif ch=='\x0f':surface.configure(layout=2,modalOpen=1-surface.settings()['modalOpen']);dirty=True
                    elif ch=='\x06':feed=not feed;nextData=time.monotonic_ns()/1e6;dirty=True
                    elif ch=='\x0c':text='';dirty=True
                    elif ch in ('\x7f','\x08'):text=text[:-1];dirty=True
                    elif ch in ('\r','\n'):dirty=True
                    elif ch.isprintable() and len(text)<512:text+=ch;dirty=True
                # This flush occurs before consulting the animation timer.
                if dirty and not stop:dataCommits+=1;renderNow()
            if needsResize:dimensions();dataCommits+=1;renderNow()
            now=time.monotonic_ns()/1e6
            if feed and now>=nextData:
                surface.configure(valuePermille=round(500+470*math.sin((now-start)/750)))
                nextData=now+12.5;dataCommits+=1;renderNow()
            if clock.advance(now):motionSamples+=1;renderNow()
    finally:
        selector.close()
        termios.tcsetattr(sys.stdin.fileno(),termios.TCSADRAIN,oldAttributes)
        for sig,handler in oldHandlers.items():signal.signal(sig,handler)
        sys.stdout.write('\x1b[?2026l\x1b[0m\x1b[?7h\x1b[?25h\x1b[?1049l')
        sys.stdout.flush()
    return 0

if __name__=='__main__':
    try:
        raise SystemExit(main())
    except (ValueError,OSError,RuntimeError) as error:
        print(f'Nocturne: {error}',file=sys.stderr)
        raise SystemExit(1)
