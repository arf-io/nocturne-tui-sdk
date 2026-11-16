"""The freestanding WASM memory routines: bulk-memory lowering and exact libc semantics.

Every native command copies the fixed 30.5 MB State twice (state.c nrCommand). With byte
loops in src/wasm_mem.c that copy dominated each gallery frame in browsers (2026-11-01
pacing report: 50-150 ms per command). The built module must lower memcpy, memmove and
memset to memory.copy / memory.fill without calling back into itself, and the exported
routines must keep the exact results of the byte loops they replace, including overlap
and the sign of memcmp. Runs against dist/nocturne_native.wasm (NOCTURNE_WASM overrides).
"""
import json, os, shutil, subprocess, unittest
from pathlib import Path
NATIVE = Path(__file__).resolve().parents[1]
WASM = Path(os.environ.get('NOCTURNE_WASM', NATIVE / 'dist/nocturne_native.wasm'))


def leb(data, at):
    value = shift = 0
    while True:
        byte = data[at]; at += 1
        value |= (byte & 0x7f) << shift; shift += 7
        if byte < 0x80:
            return value, at


def functions(data):
    """Function bodies by name from the code and name sections of an import-free module."""
    if data[:8] != b'\0asm\x01\0\0\0':
        raise AssertionError('not a WASM 1 module')
    at, bodies, names = 8, [], {}
    while at < len(data):
        section, (size, start) = data[at], leb(data, at + 1)
        end = start + size
        if section == 2:
            count, _ = leb(data, start)
            if count:
                raise AssertionError('the core module must have no imports')
        elif section == 10:
            count, p = leb(data, start)
            for _ in range(count):
                length, p = leb(data, p); bodies.append(data[p:p + length]); p += length
        elif section == 0:
            length, p = leb(data, start)
            if data[p:p + length] == b'name':
                p += length
                while p < end:
                    kind, (length, q) = data[p], leb(data, p + 1)
                    if kind == 1:
                        count, r = leb(data, q)
                        for _ in range(count):
                            index, r = leb(data, r); size_, r = leb(data, r)
                            names[data[r:r + size_].decode()] = index; r += size_
                    p = q + length
        at = end
    return {name: (index, bodies[index]) for name, index in names.items() if index < len(bodies)}


def call_bytes(index):
    out, value = bytearray([0x10]), index
    while True:
        byte = value & 0x7f; value >>= 7
        out.append(byte | (0x80 if value else 0))
        if not value:
            return bytes(out)


SEMANTICS = r"""
const {readFileSync}=await import('node:fs');
const {instance}=await WebAssembly.instantiate(readFileSync(process.argv[1]),{});
const x=instance.exports,size=1<<17,base=x.nrAlloc(size*2);if(!base)throw Error('allocation');
const heap=()=>new Uint8Array(x.memory.buffer,base,size*2);
let seed=2030;const random=()=>((seed=(Math.imul(seed,1103515245)+12345)>>>0)>>>16)&255;
const saved=new Uint8Array(size*2);for(let i=0;i<saved.length;i++)saved[i]=random();
const restore=()=>heap().set(saved);
// Each result must match the byte loops exactly inside the written range and leave a 64-byte margin untouched.
const expect=(label,lo,want)=>{const h=heap();for(let i=Math.max(0,lo-64);i<lo+want.length+64&&i<h.length;i++){const w=i>=lo&&i<lo+want.length?want[i-lo]:saved[i];if(h[i]!==w)return fail(`${label} at ${i}`);}};
const lengths=[0,1,2,3,4,5,7,8,9,15,16,17,31,32,33,63,64,65,127,255,256,257,4095,4096,4097,65537];
const offsets=[0,1,2,3,4,5,6,7,8,13];
const failures=[];let checks=0;const fail=text=>{if(failures.length<12)failures.push(text);};
for(const n of lengths)for(const d of offsets)for(const s of offsets){
 // memcpy between disjoint halves.
 restore();let r=x.memcpy(base+d,base+size+s,n);checks++;if(r!==base+d)fail('memcpy return');
 expect(`memcpy n=${n} d=${d} s=${s}`,d,saved.subarray(size+s,size+s+n));
 // memmove overlapping in both directions inside one half.
 for(const [dst,src] of [[d,s+11],[s+11,d]]){restore();r=x.memmove(base+dst,base+src,n);checks++;if(r!==base+dst)fail('memmove return');
  expect(`memmove n=${n} dst=${dst} src=${src}`,dst,saved.subarray(src,src+n));}
}
for(const n of lengths)for(const d of offsets)for(const v of [0,1,127,128,255,256,-1,-129,0x12345]){
 restore();const r=x.memset(base+d,v,n);checks++;if(r!==base+d)fail('memset return');
 expect(`memset n=${n} d=${d} v=${v}`,d,new Uint8Array(n).fill(v&255));
}
const sign=v=>v>0?1:v<0?-1:0;
for(const n of lengths)for(const a of offsets)for(const b of offsets){
 restore();let h=heap();h.copyWithin(size+b,a,a+n);checks++;
 if(x.memcmp(base+a,base+size+b,n)!==0)fail(`memcmp equal n=${n} a=${a} b=${b}`);
 for(const at of new Set([0,1,6,7,8,9,15,16,n>>1,n-9,n-8,n-1]))if(at>=0&&at<n){h=heap();const old=h[size+b+at];for(const value of [(old+1)&255,(old+255)&255]){h[size+b+at]=value;const want=h[a+at]-value,got=x.memcmp(base+a,base+size+b,n);checks++;if(got!==want)fail(`memcmp n=${n} a=${a} b=${b} at=${at}: ${got} != ${want}`);if(sign(got)!==sign(want))fail('memcmp sign');}h[size+b+at]=old;}
}
console.log(JSON.stringify({checks,failures}));
"""


class WasmMemoryRoutines(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not WASM.is_file():
            raise AssertionError(f'BLOCKED: build the WASM core first ({WASM})')
        cls.functions = functions(WASM.read_bytes())

    def test_copies_and_fills_lower_to_bulk_memory_without_recursion(self):
        for name, opcode in (('memcpy', b'\xfc\x0a'), ('memmove', b'\xfc\x0a'), ('memset', b'\xfc\x0b')):
            with self.subTest(routine=name):
                self.assertIn(name, self.functions, 'routine not in the name section')
                index, body = self.functions[name]
                self.assertIn(opcode, body, f'{name} is not memory.copy/memory.fill: {body.hex()[:120]}')
                self.assertNotIn(call_bytes(index), body, f'{name} calls itself')
                self.assertLess(len(body), 64, f'{name} still carries a loop body of {len(body)} bytes')
        index, body = self.functions['memcmp']
        self.assertNotIn(call_bytes(index), body, 'memcmp calls itself')

    def test_routines_keep_byte_loop_results(self):
        node = os.environ.get('NODE') or shutil.which('node')
        if not node:
            raise AssertionError('BLOCKED: Node is required to execute the WASM routines')
        result = subprocess.run([node, '--input-type=module', '-e', SEMANTICS, str(WASM)], capture_output=True, text=True, timeout=600)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['failures'], []); self.assertGreater(report['checks'], 20000)


if __name__ == '__main__':
    unittest.main()
