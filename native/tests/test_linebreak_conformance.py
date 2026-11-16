"""Unicode-17 UAX14-55 independent fixture oracle; deferred combined gate.

This contract precedes the native rule engine. Generated properties alone do
not satisfy it. Invalid Unicode scalar cases require native rejection.
"""
import ctypes as C
import hashlib,json,unittest
from pathlib import Path
from test_hull_immersion import NativeScene
DATA=Path(__file__).resolve().parents[1]/'unicode/17.0.0'

class LineBreakConformance(unittest.TestCase):
 def test_mandatory_breaks_distinguish_spaces_newlines_and_end(self):
  with NativeScene() as scene:
   before=scene.snapshot();source='A B\r\nC\u2028D';expected=[[2,0],[5,1],[7,1],[8,1]]
   owned=scene.line_break_details(source);self.assertEqual(owned,expected);owned[0][1]=999;self.assertEqual(scene.line_break_details(source),expected)
   self.assertEqual(scene.line_break_details(''),[[0,1]])
   self.assertEqual([row[0] for row in expected],scene.line_breaks(source));self.assertEqual(scene.snapshot(),before)
 def test_detail_row_capacity_probe_alias_and_atomicity(self):
  with NativeScene() as scene:
   query=scene._lib.nrLineBreakDetails;query.argtypes=[C.POINTER(C.c_uint32),C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32];query.restype=C.c_int
   source=(C.c_uint32*12)(*map(ord,'A B\r\nC\u2028D'));output=(C.c_uint32*12)(*([777]*12))
   self.assertEqual(query(source,8,None,0),4)
   self.assertEqual(query(source,8,output,3),-1);self.assertEqual(list(output),[777]*12)
   raw=(C.c_ubyte*49)(*([0xaa]*49));misaligned=C.cast(C.addressof(raw)+1,C.POINTER(C.c_uint32));before=bytes(raw)
   self.assertEqual(query(source,8,misaligned,4),-1);self.assertEqual(bytes(raw),before)
   source[7]=0xd800;self.assertEqual(query(source,8,output,4),-1);self.assertEqual(list(output),[777]*12)
   source[7]=ord('D');self.assertEqual(query(source,8,source,4),4);self.assertEqual(list(source[:8]),[2,0,5,1,7,1,8,1])
 def test_atomic_short_misaligned_and_alias_outputs(self):
  with NativeScene() as scene:
   query=scene._lib.nrLineBreaks;query.argtypes=[C.POINTER(C.c_uint32),C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32];query.restype=C.c_int
   source=(C.c_uint32*11)(*map(ord,'hello world'));output=(C.c_uint32*12)(*([777]*12))
   self.assertEqual(query(source,11,output,1),-1);self.assertEqual(list(output),[777]*12)
   raw=(C.c_ubyte*49)(*([0xaa]*49));misaligned=C.cast(C.addressof(raw)+1,C.POINTER(C.c_uint32));before=bytes(raw)
   self.assertEqual(query(source,11,misaligned,12),-1);self.assertEqual(bytes(raw),before)
   self.assertEqual(query(source,11,source,11),2);self.assertEqual(list(source[:2]),[6,11])
 def test_owned_binding_known_text_and_scalar_rejection(self):
  with NativeScene() as scene:
   before=scene.snapshot();owned=scene.line_breaks('hello world');self.assertEqual(owned,[6,11]);owned[0]=999;self.assertEqual(scene.line_breaks('hello world'),[6,11])
   self.assertEqual(scene.line_breaks('A\r\nB'),[3,4]);self.assertEqual(scene.line_breaks(''),[0])
   with self.assertRaises(ValueError):scene.line_breaks('\ud800')
   with self.assertRaises(ValueError):scene.line_breaks('A'*2049)
   self.assertEqual(scene.snapshot(),before)
 def test_pinned_official_break_opportunities(self):
  receipts={s['name']:s for s in json.loads((DATA/'SOURCES.json').read_text())['sources']};raw=(DATA/'LineBreakTest.txt').read_bytes()
  self.assertEqual(hashlib.sha256(raw).hexdigest(),receipts['LineBreakTest.txt']['sha256'])
  cases=0
  with NativeScene() as scene:
   query=scene._lib.nrLineBreaks;query.argtypes=[C.POINTER(C.c_uint32),C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32];query.restype=C.c_int
   before=scene.snapshot()
   for line_no,line in enumerate(raw.decode().splitlines(),1):
    tokens=line.split('#',1)[0].split()
    if not tokens:continue
    source=[];expected=[]
    for token in tokens:
     if token=='÷':expected.append(len(source))
     elif token!='×':source.append(int(token,16))
    values=(C.c_uint32*len(source))(*source);output=(C.c_uint32*(len(source)+1))(*([777]*(len(source)+1)));cases+=1
    if any(0xd800<=value<=0xdfff or value>0x10ffff for value in source):
     self.assertEqual(query(values,len(source),output,len(output)),-1,f'invalid scalar fixture line {line_no}');self.assertEqual(list(output),[777]*len(output));continue
    count=query(values,len(source),None,0);self.assertEqual(count,len(expected),f'probe fixture line {line_no}')
    count=query(values,len(source),output,len(output));self.assertEqual(list(output[:count]),expected,f'fixture line {line_no}')
   self.assertGreater(cases,19000);self.assertEqual(scene.snapshot(),before)
