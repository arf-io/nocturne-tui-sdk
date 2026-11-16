#!/usr/bin/env python3
"""Explicit opt-in PCM features for a native terminal host.

Uses a caller-selected PulseAudio/PipeWire-Pulse source through parec, or caller-
supplied mono float32le PCM on stdin. No audio files or network sinks are created.
A monitor source can supply output audio. This utility does not choose one for you.
"""
from __future__ import annotations
import argparse,array,json,math,shutil,subprocess,sys,time

def blockFeatures(data:bytes)->tuple[float,float,list[float]]:
    """Return RMS, peak, and 128 display samples from mono little-endian float32.

    Blocks must contain 2..16384 finite samples in +/-32 full-scale units.
    Invalid/malformed PCM raises ValueError; it is never replaced with silence.
    """
    if len(data)%4 or not 8<=len(data)<=65536:raise ValueError('PCM block length')
    values=array.array('f');values.frombytes(data)
    if sys.byteorder!='little':values.byteswap()
    if any(not math.isfinite(v) or abs(v)>32 for v in values):raise ValueError('invalid float32 PCM')
    rms=math.sqrt(sum(v*v for v in values)/len(values));peak=max(map(abs,values))
    return rms,peak,[float(values[min(len(values)-1,i*len(values)//128)]) for i in range(128)]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--device',help='Exact source name from pactl list short sources');p.add_argument('--kind',choices=['input','output'],required=True);p.add_argument('--stdin-pcm',action='store_true');p.add_argument('--rate',type=int,default=16000);p.add_argument('--block',type=int,default=512);a=p.parse_args()
    if not 8000<=a.rate<=192000 or not 64<=a.block<=16384:p.error('rate 8000..192000, block 64..16384')
    if not a.stdin_pcm and not a.device:p.error('--device is required for capture; source selection is explicit')
    child=None
    if a.stdin_pcm:stream=sys.stdin.buffer
    else:
        executable=shutil.which('parec')
        if not executable:p.error('parec is unavailable; use --stdin-pcm or install a Pulse-compatible recording client')
        child=subprocess.Popen([executable,'--raw','--format=float32le','--channels=1',f'--rate={a.rate}',f'--device={a.device}'],stdout=subprocess.PIPE,stderr=sys.stderr);stream=child.stdout
    seq=0;prefix='audio.'+a.kind;pending=b''
    def emit(row):print(json.dumps(row,separators=(',',':')),flush=True)
    try:
        while True:
            chunk=stream.read(a.block*4-len(pending))
            if not chunk:break
            pending+=chunk
            if len(pending)<a.block*4:continue
            rms,peak,wave=blockFeatures(pending);pending=b'';at=time.monotonic_ns()/1e6
            for suffix,value in [('rms',rms),('peak',peak)]:
                seq+=1;emit(dict(source=prefix+'.'+suffix,value=value,seq=seq,atMs=at,unit='FS',quality='measured' if child else 'external'))
            seq+=1;emit(dict(type='waveform',source=prefix,samples=wave,seq=seq,atMs=at,quality='measured' if child else 'external'))
    except (KeyboardInterrupt,BrokenPipeError):pass
    finally:
        if child:
            child.terminate()
            try:child.wait(timeout=1)
            except subprocess.TimeoutExpired:child.kill();child.wait()
if __name__=='__main__':main()
