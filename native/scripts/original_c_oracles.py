#!/usr/bin/env python3
"""Build the named original-source differential helpers with their real probes.

Instrumentation is copied verbatim from test_scenic_art and
 test_scenic_source_raster; every original seam must still occur exactly once.
"""
from pathlib import Path
import argparse,json,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
NAMES=('original_world_frame_oracle','scenic_art_geometry_diff','scenic_source_raster_diff')
GEOMETRY_PROBES={'static void wTriangle ( WCanvas * c , WPoint a , WPoint b , WPoint d , uint32_t color , int32_t alpha ) {': 'nsOriginalPrimitiveTrace(0,a.x,a.y,a.z,b.x,b.y,b.z,d.x,d.y,d.z,color,alpha,0);',
 'static void wDot ( WCanvas * c , WPoint p , uint32_t color , int32_t alpha , int32_t radius ) {': 'nsOriginalPrimitiveTrace(2,p.x,p.y,p.z,0,0,0,0,0,0,color,alpha,radius);',
 'static void wLine ( WCanvas * c , WPoint a , WPoint b , uint32_t color , int32_t alpha ) {': 'nsOriginalPrimitiveTrace(1,a.x,a.y,a.z,b.x,b.y,b.z,0,0,0,color,alpha,0);'}
RASTER_PROBES={
 'int32_t z = ( int32_t ) ( ( e0 * ip + e1 * iq + e2 * ir ) / area ) ;\n        uint32_t i = ( uint32_t ) y * c -> width + x ;': 'int32_t z = ( int32_t ) ( ( e0 * ip + e1 * iq + e2 * ir ) / area ) ;\n        nsOriginalRasterCoverage(x,y,z,color,alpha,750);\n        uint32_t i = ( uint32_t ) y * c -> width + x ;',
 'if ( radius && ( ( x - cx ) * ( x - cx ) + ( y - cy ) * ( y - cy ) > radius * radius ) ) continue ;\n        uint32_t i = ( uint32_t ) y * c -> width + x ;': 'if ( radius && ( ( x - cx ) * ( x - cx ) + ( y - cy ) * ( y - cy ) > radius * radius ) ) continue ;\n        nsOriginalRasterCoverage(x,y,iz,color,alpha,950);\n        uint32_t i = ( uint32_t ) y * c -> width + x ;',
 'int32_t iz = ( int32_t ) ( ( ( int64_t ) wDepth ( c , u . z ) * ( n - k ) + ( int64_t ) wDepth ( c , v . z ) * k ) / n ) ;\n        uint32_t i = ( uint32_t ) y * c -> width + x ;': 'int32_t iz = ( int32_t ) ( ( ( int64_t ) wDepth ( c , u . z ) * ( n - k ) + ( int64_t ) wDepth ( c , v . z ) * k ) / n ) ;\n        nsOriginalRasterCoverage(x,y,iz,color,alpha,950);\n        uint32_t i = ( uint32_t ) y * c -> width + x ;',
}
PROJECT_WITNESS='\nint nsOriginalProjectWitness(const int32_t *values,int32_t outputWidth,int32_t outputHeight,\n    int32_t x,int32_t y,int32_t z,int32_t *cx,int32_t *cy,int32_t *cz,\n    int32_t *sx,int32_t *sy,int32_t *depth) {\n    NsWorldConfig config;memcpy(config.v,values,sizeof(config.v));\n    WCanvas c;c.config=&config;c.detail=0;\n    c.width=outputWidth*(values[NSW_SAMPLING]?2:1);\n    c.height=outputHeight*(values[NSW_SAMPLING]?4:2);\n    c.sy=wSin(values[NSW_YAW]);c.cy=wCos(values[NSW_YAW]);\n    c.sp=wSin(values[NSW_PITCH]);c.cp=wCos(values[NSW_PITCH]);\n    c.sr=wSin(values[NSW_ROLL]);c.cr=wCos(values[NSW_ROLL]);\n    c.focal=c.width*8*wCos(values[NSW_FOV]/2)/wSin(values[NSW_FOV]/2);\n    WPoint p=wCamera(&c,wP(x,y,z));if(p.z<384)return 0;\n    WScreen q=wProject(&c,p);*cx=p.x;*cy=p.y;*cz=p.z;\n    *sx=q.x;*sy=q.y;*depth=wDepth(&c,p.z);return 1;\n}\n'

def originalOracleInputs(root):
 root=Path(root);directory=root/'evidence/original-scenic-restoration-20261013'
 manifest=directory/'ORIGINAL-WORLD-FRAMES.json'
 paths=[manifest,directory/'ORIGINAL-WORLD-FRAMES.tsv',root/'evidence/original-observatory-overlay-20261015/sanitizer-commands.txt']
 if not manifest.is_file():return paths
 frames=json.loads(manifest.read_text())['frames']
 if len(frames)!=16:raise ValueError('Expected all16 original source scenarios')
 for frame in frames:
  name=frame['cellsFile']
  if Path(name).name!=name or not name.endswith('.cells'):raise ValueError('Noncanonical original cell fixture')
  paths.append(directory/name)
 return paths

def originalOracleJobs(root,cc,python,relative,executable,sources):
 root=Path(root);name=Path(relative).stem
 if relative=='tests/observatory_overlay_safety.c':
  flags=['-std=c11','-O1','-g','-ffp-contract=off','-fno-fast-math','-fno-math-errno','-fno-strict-aliasing','-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer','-Iinclude','-Isrc']
  return ([cc,*flags,*sources,relative,'-o',executable],[str(root/executable),str(root/'evidence/original-observatory-overlay-20261015/sanitizer-commands.txt')])
 if relative in {'tests/'+n+'.c'for n in NAMES}:
  return ([python,'scripts/original_c_oracles.py','--kind',name,'--cc',cc,'--output',executable],[str(root/executable),str(root/'evidence/original-scenic-restoration-20261013')])
 return None

def replaceOnce(text,needle,replacement):
 if text.count(needle)!=1:raise ValueError('Original instrumentation seam changed: '+needle)
 return text.replace(needle,replacement,1)

def buildOriginalOracle(root,kind,cc,output):
 root=Path(root);output=Path(output).resolve()
 if kind not in NAMES:raise ValueError('Unknown original oracle')
 with tempfile.TemporaryDirectory(prefix='nocturne-original-oracle-') as d:
  temporary=Path(d);original=root.parent/'src/nocturne.c';sources=[root/'tests'/(kind+'.c')]
  if kind!='original_world_frame_oracle':
   world=(root.parent/'src/world.inc').read_text()
   if kind=='scenic_art_geometry_diff':
    for needle,trace in GEOMETRY_PROBES.items():world=replaceOnce(world,needle,needle+'\n    '+trace)
    declaration='void nsOriginalPrimitiveTrace(int,int32_t,int32_t,int32_t,int32_t,int32_t,int32_t,int32_t,int32_t,int32_t,uint32_t,int32_t,int32_t);\n'
    source=replaceOnce(original.read_text(),'#include "world.inc"',declaration+'#include "'+str(temporary/'world.instrumented.inc')+'"')
   else:
    for needle,replacement in RASTER_PROBES.items():world=replaceOnce(world,needle,replacement)
    source='#include <stdint.h>\n#include <string.h>\nvoid nsOriginalRasterCoverage(int32_t,int32_t,int32_t,uint32_t,int32_t,int32_t);\n'+replaceOnce(original.read_text(),'#include "world.inc"','#include "'+str(temporary/'world.instrumented.inc')+'"')+PROJECT_WITNESS
   (temporary/'world.instrumented.inc').write_text(world);original=temporary/'nocturne.instrumented.c';original.write_text(source)
   sources.append(root/'src/scenic_art.c')
   if kind=='scenic_source_raster_diff':sources.append(root/'src/scenic_source_raster.c')
  sources.append(original)
  argv=[cc,'-std=c11','-O2','-Wall','-Wextra','-Werror','-I',str(root/'src'),'-I',str(root.parent/'include'),'-I',str(root.parent/'src'),*map(str,sources),'-o',str(output)]
  print(json.dumps({'helper':kind,'compileArgv':argv}),flush=True)
  subprocess.run(argv,cwd=root,check=True)

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--kind',choices=NAMES,required=True);parser.add_argument('--cc',required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
 buildOriginalOracle(ROOT,args.kind,args.cc,args.output)
 return 0
if __name__=='__main__':raise SystemExit(main())
