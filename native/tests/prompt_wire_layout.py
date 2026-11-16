"""Actual current prompt wire layout for hostile snapshot tests; no fabricated fixture."""
from functools import lru_cache
import os,re,struct,subprocess,tempfile,zlib
from pathlib import Path

@lru_cache(maxsize=1)
def layout():
 source=Path(os.environ.get('NOCTURNE_TEST_SOURCE_ROOT',Path(__file__).resolve().parents[1]))
 text=(source/'src/prompt_storage.c').read_text()
 matches=re.findall(r'typedef struct \{[^}]+\} PromptWire;',text)
 if len(matches)!=1:raise AssertionError('Exactly one actual PromptWire declaration required')
 with tempfile.TemporaryDirectory(prefix='nr-vim-wire-layout-') as d:
  p=Path(d);c=p/'probe.c';exe=p/'probe'
  c.write_text('#include "internal.h"\n#include <stddef.h>\n#include <stdio.h>\n'+matches[0]+'\nint main(void){printf("%u %zu %zu %zu %zu %u %u\\n",NR_STATE_SCHEMA,offsetof(State,dynamicPrompt),sizeof(PromptWire),offsetof(PromptWire,registers),offsetof(PromptWire,lengths),NR_PROMPT_WIRE_ARRAYS,NR_INLINE_PROMPT_CAPACITY);return 0;}\n')
  subprocess.run([os.environ.get('CC','cc'),'-std=c11','-I'+str(source/'include'),'-I'+str(source/'src'),str(c),'-o',str(exe)],check=True,capture_output=True,text=True)
  return dict(zip(['schema','fixed','wireBytes','registers','lengths','arrays','inlineCapacity'],map(int,subprocess.check_output([str(exe)],text=True).split())))

def prompt_wire(snapshot,scene):
 q=layout();data=bytes(snapshot);wire=24+q['fixed']
 if scene.info_complete()['contract']['snapshotSchema']!=q['schema'] or scene._lib.nrPromptWireSize()!=q['wireBytes']:
  raise AssertionError('Compiled wire does not match loaded runtime')
 if len(data)<wire+q['wireBytes'] or struct.unpack_from('<I',data,12)[0]!=q['schema'] or struct.unpack_from('<I',data,28)[0]!=q['schema']:
  raise AssertionError('Snapshot is not the current writer layout')
 if struct.unpack_from('<I',data,16)[0]!=len(data)-24 or struct.unpack_from('<I',data,20)[0]!=zlib.crc32(data[24:]):
  raise AssertionError('Writer length or checksum differs')
 lengths=struct.unpack_from('<'+'I'*q['arrays'],data,wire+q['lengths'])
 if wire+q['wireBytes']+4*sum(lengths)!=len(data):raise AssertionError('Wire scalar array lengths differ')
 return q,wire,lengths
