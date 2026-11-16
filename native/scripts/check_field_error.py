#!/usr/bin/env python3
"""Bound the current radial lookup optimization against the exact equations.

This is an independently compiled exact-equation test target, not a historical
runtime or production fallback. The test measures 8-bit channel quantization.
"""
from pathlib import Path
import sys,json,subprocess,math
from toolchain import discover
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene

def main():
 suffix='.dylib'if sys.platform=='darwin'else'.so';path=ROOT/'dist'/('reference-fields'+suffix)
 sources=sorted(str(p)for p in (ROOT/'src').glob('*.c')if p.name!='wasm_mem.c')
 subprocess.run([discover()['cc'],'-std=c11','-O2','-fPIC','-dynamiclib'if sys.platform=='darwin'else'-shared','-ffp-contract=off','-fno-fast-math','-fno-math-errno','-fno-strict-aliasing','-DNR_REFERENCE_FIELDS','-Iinclude','-Isrc',*sources,'-o',str(path)],cwd=ROOT,check=True)
 records=[]
 with NativeScene()as actual,NativeScene(library=path)as exact:
  for effect in ['surface-field/silk-tide','surface-field/satin-rings','surface-field/opal-fronts','surface-field/interference-tide']:
   for width in [.15,1.4,8]:
    for s in [actual,exact]:
     s.command({'op':'reset'});s.command({'op':'resize','width':100,'height':35});s.command({'op':'environment','stars':0,'style':'solid','sampling':'cell'});s.command({'op':'prompt','active':False});s.command({'op':'field','effect':effect,'x':43.2,'y':18.4,'width':width,'speed':8.5,'lifeMs':12000,'strength':.83})
    for t in [0,150000,800000,2200000]:
     for s in [actual,exact]:s.advance_to(t)
     aa,bb=actual.render().words(),exact.render().words();errors=[]
     for a,b in zip(aa,bb):
      assert a[0]==b[0]and a[3]==b[3], 'optimization changed glyph or hit ID'
      for color in [1,2]:
       for shift in [16,8,0]:errors.append(abs((a[color]>>shift&255)-(b[color]>>shift&255)))
     records.append({'effect':effect,'width':width,'timeUs':t,'maxChannelError':max(errors),'meanChannelError':sum(errors)/len(errors)})
 result={'scope':'48 cell-sampling frames against exact current radial equations; 8-bit RGB quantization, not historical optical acceptance.','cases':records,'passed':all(r['maxChannelError']<=2 for r in records)}
 (ROOT/'evidence/field-lookup-error.json').write_text(json.dumps(result,indent=2)+'\n');print('Field LUT',len(records),'cases; max channel error',max(r['maxChannelError']for r in records),'PASS'if result['passed']else'FAIL');return 0 if result['passed']else 2
if __name__=='__main__':raise SystemExit(main())
