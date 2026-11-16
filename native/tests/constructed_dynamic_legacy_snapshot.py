"""Construct supported old layouts for tests; these are not historical writer fixtures."""
import ctypes as C
from functools import lru_cache
import json,os,struct,subprocess,sys,tempfile,zlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
ROOT=Path(__file__).resolve().parents[1]
SUPPORTED={0x20261077,0x20261078,0x20261079,0x20261081,0x20261083}
@lru_cache(maxsize=1)
def layout():
 """Compile actual layout offsets; cross-check the loaded runtime's wire contract."""
 source=Path(os.environ.get('NOCTURNE_TEST_SOURCE_ROOT',ROOT))
 with tempfile.TemporaryDirectory(prefix='nr-dynamic-legacy-layout-') as d:
  p=Path(d);probe=p/'layout.c';exe=p/'layout'
  fields=['atelierWindows','atelierApplicationParticles','sourceGraphLayout','sourceSky','firstPromptSource','sourceModel','sourceStageScene','observatoryOverlay','sourceModal','cameraControls','sceneArtClock','promptAppearance','occlusionControls','promptSourceLayer']
  statements=['printf("%u %zu %zu %zu %zu\\n",NR_STATE_SCHEMA,sizeof(State),offsetof(State,dynamicPrompt),offsetof(State,atelierWindows),offsetof(State,fieldControls));']
  statements.extend('printf("%zu %zu\\n",offsetof(State,'+name+'),sizeof(((State*)0)->'+name+'));' for name in fields)
  probe.write_text('#include "internal.h"\n#include <stddef.h>\n#include <stdio.h>\nint main(void){'+''.join(statements)+'return 0;}\n')
  subprocess.run([os.environ.get('CC','cc'),'-std=c11','-I'+str(source/'include'),'-I'+str(source/'src'),str(probe),'-o',str(exe)],check=True,capture_output=True,text=True)
  rows=subprocess.check_output([str(exe)],text=True).splitlines()
 q=dict(zip(['schema','stateSize','fixed','legacyFixed','schema45Fixed'],map(int,rows[0].split())))
 if len(rows)!=1+len(fields):raise AssertionError('Incomplete actual layout probe')
 q['appendFields']=[dict(zip(['offset','bytes'],map(int,row.split())),name=name) for name,row in zip(fields,rows[1:])]
 cursor=q['legacyFixed']
 for field in q['appendFields']:
  if field['offset']!=cursor or field['bytes']<=0:raise AssertionError('Unaccounted fixed-layout appendix or padding')
  cursor+=field['bytes']
 q['omittedBytes']=sum(field['bytes'] for field in q['appendFields'])
 q['windowsBytes']=q['appendFields'][0]['bytes'];q['particlesBytes']=q['appendFields'][1]['bytes']
 if q['legacyFixed']!=30478240 or cursor!=q['fixed'] or q['fixed']>=q['stateSize']:
  raise AssertionError('Unsupported actual dynamic state layout')
 with NativeScene() as scene:
  contract=scene.info_complete()['contract'];q['wireBytes']=scene._lib.nrPromptWireSize();snapshot=scene.snapshot();q['magic']=snapshot[:8].hex()
  if contract['snapshotSchema']!=q['schema'] or scene._lib.nrSnapshotSize()!=24+q['fixed']+q['wireBytes'] or len(snapshot)!=24+q['fixed']+q['wireBytes']:
   raise AssertionError('Compiled source layout disagrees with loaded native writer')
 return q

def construct_dynamic_legacy_snapshot(snapshot,schema):
 """Explicit test-constructed77/78/79/81/83 fixed prefix plus compatible prompt wire.

 Retain the full pointer-free prompt payload, including Unicode/history arrays;
 refuse to discard nonzero newer fields. Genuine archived fixtures are untouched.
 """
 if schema not in SUPPORTED:raise ValueError('Unsupported test-constructed legacy epoch')
 q=layout();data=bytes(snapshot)
 if len(data)<24+q['fixed']+q['wireBytes'] or data[:8].hex()!=q['magic'] or struct.unpack_from('<I',data,8)[0]!=1:
  raise ValueError('Invalid current snapshot identity or size')
 if struct.unpack_from('<I',data,12)[0]!=q['schema'] or struct.unpack_from('<I',data,28)[0]!=q['schema']:
  raise ValueError('Input is not the actual current writer epoch')
 if struct.unpack_from('<I',data,16)[0]!=len(data)-24 or struct.unpack_from('<I',data,20)[0]!=zlib.crc32(data[24:]):
  raise ValueError('Invalid current snapshot length or checksum')
 if any(data[24+q['legacyFixed']:24+q['fixed']]):raise ValueError('Cannot discard active newer fixed-layout fields')
 payload=data[24+q['fixed']:]
 with NativeScene() as scene:
  shape=scene._lib.nrPromptPayloadShape;shape.argtypes=[C.c_void_p,C.c_uint32,C.c_uint32];shape.restype=C.c_int
  buffer=C.create_string_buffer(payload)
  if shape(buffer,len(payload),q['schema'])!=1 or shape(buffer,len(payload),schema)!=1:
   raise ValueError('Prompt payload is not valid for both current and selected old wire layout')
 old=bytearray(data[:24+q['legacyFixed']]+payload)
 for offset,value in [(12,schema),(28,schema),(16,len(old)-24)]:struct.pack_into('<I',old,offset,value)
 struct.pack_into('<I',old,20,zlib.crc32(old[24:]));return bytes(old)
