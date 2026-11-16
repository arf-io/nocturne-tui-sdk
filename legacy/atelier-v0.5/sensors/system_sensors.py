#!/usr/bin/env python3
"""Read-only Linux sensor sampler emitting bounded NDJSON scalar events.

No root escalation, network requests, device writes, inferred missing values,
or summation of overlapping power domains. Each source has explicit units.
Usage: python3 sensors/system_sensors.py --interval 0.25
"""
from __future__ import annotations
import argparse,json,math,re,time,sys
from pathlib import Path

class SystemSampler:
    """Sample sysfs/procfs beneath root (fixture injection supported).

    poll(atMs) returns measured records. Network and energy rates need two
    monotonic samples. Missing, denied, reset, and malformed sources are omitted.
    No exception from an unreadable sensor poisons the remaining sources.
    """
    def __init__(self,root:Path|str='/'):
        self.root=Path(root);self.previous={};self.sequences={}
    def readNumber(self,path:Path):
        try:
            value=float(path.read_text().strip())
            return value if math.isfinite(value) else None
        except (OSError,ValueError):return None
    def sourceId(self,path:Path,suffix:str):
        rel=str(path.relative_to(self.root));name=re.sub(r'[^a-zA-Z0-9_.-]','_',rel)
        # Bound paths while preserving uniqueness for the normal sysfs layouts.
        if len(name)>48:
            import hashlib
            name=name[:37]+'_'+hashlib.sha256(name.encode()).hexdigest()[:10]
        return (name+'.'+suffix)[:64]
    def poll(self,atMs:int|float)->list[dict]:
        if not isinstance(atMs,(int,float)) or not math.isfinite(atMs) or atMs<0:raise ValueError('nonnegative finite monotonic milliseconds required')
        rows=[]
        def emit(source,value,unit):
            if value is None or not math.isfinite(value):return
            seq=self.sequences.get(source,0)+1;self.sequences[source]=seq
            rows.append(dict(source=source,value=value,atMs=atMs,seq=seq,unit=unit,quality='measured'))
        for directory in sorted((self.root/'sys/class/hwmon').glob('hwmon*'))[:64]:
            for kind,factor,unit,limit in [('temp',.001,'°C',(-273.15,500)),('power',.000001,'W',(0,1e7))]:
                for path in sorted(directory.glob(kind+'*_input'))[:32]:
                    v=self.readNumber(path)
                    if v is not None and limit[0]<=v*factor<=limit[1]:emit(self.sourceId(path,'value'),v*factor,unit)
        for directory in sorted((self.root/'sys/class/power_supply').glob('*'))[:32]:
            p=directory/'power_now';v=self.readNumber(p)
            if v is not None:emit(self.sourceId(p,'value'),v/1e6,'W')
        # Report each power domain separately. Parent/child domains overlap.
        powerRoot=self.root/'sys/class/powercap'
        paths=sorted(powerRoot.glob('*/energy_uj'))+sorted(powerRoot.glob('*/*/energy_uj'))
        seen=set()
        for path in paths[:128]:
            try:key=str(path.resolve())
            except OSError:continue
            if key in seen:continue
            seen.add(key);v=self.readNumber(path)
            if v is None:continue
            old=self.previous.get(key);self.previous[key]=(atMs,v)
            if old and atMs>old[0]:
                delta=v-old[1]
                if delta<0:
                    wrap=self.readNumber(path.parent/'max_energy_range_uj')
                    if wrap is not None:delta+=wrap
                if delta>=0:emit(self.sourceId(path,'watts'),delta/1e6/((atMs-old[0])/1000),'W')
        network=self.root/'proc/net/dev'
        try:lines=network.read_text().splitlines()
        except OSError:lines=[]
        for line in lines[:258]:
            if ':' not in line:continue
            name,data=line.split(':',1);name=name.strip()
            try:parts=data.split();rx,tx=int(parts[0]),int(parts[8])
            except (ValueError,IndexError):continue
            source='net.'+re.sub('[^a-zA-Z0-9_.-]','_',name)[:38];old=self.previous.get(source);self.previous[source]=(atMs,rx,tx)
            if old and atMs>old[0]:
                dt=(atMs-old[0])/1000
                for suffix,current,before in [('rx',rx,old[1]),('tx',tx,old[2])]:
                    if current>=before:emit(source+'.'+suffix,(current-before)*8/dt/1e6,'Mbit/s')
        for device in sorted((self.root/'sys/bus/iio/devices').glob('iio:device*'))[:32]:
            for axis in ['x','y','z']:
                p=device/f'in_accel_{axis}_raw';raw=self.readNumber(p);scale=self.readNumber(device/f'in_accel_{axis}_scale')
                if scale is None:scale=self.readNumber(device/'in_accel_scale')
                if raw is not None and scale is not None:
                    offset=self.readNumber(device/f'in_accel_{axis}_offset')
                    if offset is None:offset=self.readNumber(device/'in_accel_offset')
                    emit(self.sourceId(p,'accel'),(raw+(offset or 0))*scale,'m/s²')
        return rows[:512]

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--interval',type=float,default=.25);parser.add_argument('--once',action='store_true');parser.add_argument('--root',type=Path,default=Path('/'));args=parser.parse_args()
    if not .02<=args.interval<=60:parser.error('interval 0.02..60 seconds')
    sampler=SystemSampler(args.root)
    try:
        while True:
            rows=sampler.poll(time.monotonic_ns()/1e6)
            for row in rows:print(json.dumps(row,separators=(',',':')),flush=True)
            if args.once:break
            time.sleep(args.interval)
    except (BrokenPipeError,KeyboardInterrupt):pass
if __name__=='__main__':main()
