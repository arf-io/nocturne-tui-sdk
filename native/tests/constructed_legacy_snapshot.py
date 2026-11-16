"""Explicitly test-constructed old layouts, never historical provenance fixtures.

The retained original receipt files are untouched. Current32-window state stores
active pools after the historical prefix; truncating without this copy silently
constructs an empty-window old state. Compiler offsetof/sizeof maps actual fields.
"""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
from functools import lru_cache
from pathlib import Path
import json,os,struct,subprocess,tempfile,zlib
from native.tests.current_writer_contract import current_schema
ROOT=Path(__file__).resolve().parents[1]
@lru_cache(maxsize=1)
def layout():
 source=Path(os.environ.get('NOCTURNE_TEST_SOURCE_ROOT',ROOT))
 with tempfile.TemporaryDirectory(prefix='nr-legacy-layout-') as d:
  exe=Path(d)/'probe';run=subprocess.run(['cc','-std=c11','-I'+str(source/'include'),'-I'+str(source/'src'),str(ROOT/'tests/legacy_window_layout_probe.c'),'-o',str(exe)],capture_output=True,text=True)
  if run.returncode:raise RuntimeError(run.stderr)
  data=json.loads(subprocess.check_output([str(exe)]))
 if data['schema']!=current_schema():raise RuntimeError('Test source header differs from loaded runtime; set NOCTURNE_TEST_SOURCE_ROOT to its native directory')
 return data

def construct_legacy_snapshot(snapshot,schema,payload_bytes):
 q=layout();old=bytearray(snapshot[:24+payload_bytes])
 if len(old)!=24+payload_bytes:raise ValueError('Historical prefix not present')
 for index in range(12,q['maxWindows']):
  used=struct.unpack_from('<I',snapshot,24+q['windowOffset']+index*q['windowSize']+q['usedOffset'])[0]
  if used:raise ValueError('Current window beyond historical12-slot capacity')
 for destination,source,size in q['copies']:
  if destination>=payload_bytes:continue
  if destination+size>payload_bytes:raise ValueError('Historical prefix cuts a mapped field')
  old[24+destination:24+destination+size]=snapshot[24+source:24+source+size]
 for at,value in ((12,schema),(16,payload_bytes),(28,schema)):struct.pack_into('<I',old,at,value)
 struct.pack_into('<I',old,20,zlib.crc32(old[24:]));return bytes(old)
