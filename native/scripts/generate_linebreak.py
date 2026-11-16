#!/usr/bin/env python3
"""Generate frozen Unicode-17 line-break properties; no rule execution."""
from pathlib import Path
import hashlib,json
from array import array
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'unicode/17.0.0'
def generate():
 sources={s['name']:s for s in json.loads((DATA/'SOURCES.json').read_text())['sources']}
 for name in ['LineBreak.txt','LineBreakTest.txt','UnicodeData.txt','EastAsianWidth.txt','emoji-data.txt']:
  data=(DATA/name).read_bytes();receipt=sources[name]
  if len(data)!=receipt['bytes'] or hashlib.sha256(data).hexdigest()!=receipt['sha256']:raise ValueError('Source digest mismatch: '+name)
 ranges=[]
 for line in (DATA/'LineBreak.txt').read_text().splitlines():
  line=line.split('#',1)[0].strip()
  if not line:continue
  bounds,kind=map(str.strip,line.split(';'));parts=bounds.split('..');ranges.append((int(parts[0],16),int(parts[-1],16),kind))
 classes=sorted({kind for _,_,kind in ranges}|{'XX'});identities={kind:index for index,kind in enumerate(classes)}
 previous=-1
 for a,b,kind in ranges:
  if a<=previous or a>b or b>0x10ffff:raise ValueError('Invalid line-break property ranges')
  previous=b
 output=['/* Generated Unicode 17.0.0 properties; source hashes in SOURCES.json. */',
  'enum {'+','.join('NR_LB_'+kind+'='+str(identities[kind]) for kind in classes)+'};',
  'static const struct {uint32_t first,last;uint8_t kind;} lineBreakRanges[]={']
 output.extend('{0x%x,0x%x,NR_LB_%s},'%(a,b,kind) for a,b,kind in ranges);output.extend(['};',''])
 # Auxiliary UAX14 predicates: Mn/Mc, Pi, Pf, Cn, EastAsian F/W/H and EP.
 flags=array('B',[8])*0x110000
 pending=None
 for line in (DATA/'UnicodeData.txt').read_text().splitlines():
  fields=line.split(';');point=int(fields[0],16);category=fields[2]
  if fields[1].endswith(', First>'):pending=(point,category);continue
  first=pending[0] if fields[1].endswith(', Last>') else point
  if fields[1].endswith(', Last>'):
   if pending is None or pending[1]!=category:raise ValueError('Invalid Unicode category range')
   pending=None
  value=1 if category in ('Mn','Mc') else 2 if category=='Pi' else 4 if category=='Pf' else 8 if category=='Cn' else 0
  flags[first:point+1]=array('B',[value])*(point-first+1)
 if pending is not None:raise ValueError('Unclosed Unicode category range')
 for name,accepted,bit in [('EastAsianWidth.txt',{'F','W','H'},16),('emoji-data.txt',{'Extended_Pictographic'},32)]:
  for line in (DATA/name).read_text().splitlines():
   line=line.split('#',1)[0].strip()
   if not line:continue
   bounds,kind=map(str.strip,line.split(';'))
   if kind not in accepted:continue
   parts=bounds.split('..');first,last=int(parts[0],16),int(parts[-1],16)
   for point in range(first,last+1):flags[point]|=bit
 output.append('static const struct {uint32_t first,last;uint8_t flags;} lineBreakAuxiliary[]={')
 first=0
 for point in range(1,len(flags)+1):
  if point==len(flags) or flags[point]!=flags[first]:
   if flags[first]:output.append('{0x%x,0x%x,%d},'%(first,point-1,flags[first]))
   first=point
 output.extend(['};',''])
 (ROOT/'src/unicode_linebreak.inc').write_text('\n'.join(output))
if __name__=='__main__':generate()
