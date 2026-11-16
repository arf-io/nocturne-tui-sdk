#!/usr/bin/env python3
"""Build the current C sources natively and to WASM. Never downloads dependencies."""
from pathlib import Path
import argparse, json, os, platform, shutil, subprocess, sys
from toolchain import discover
import build_switches
ROOT=Path(__file__).resolve().parents[1]
def run(argv):
    print('+',' '.join(map(str,argv)),flush=True)
    subprocess.run(list(map(str,argv)),check=True,cwd=ROOT)
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--native-only',action='store_true');parser.add_argument('--sanitize',action='store_true');args=parser.parse_args()
    # The record of the applied switches describes only a build that completed: remove the old one first,
    # so a refused or failed build leaves none (build_switches.py).
    out=ROOT/'dist';switchRecord=out/'build-switches.json';switchRecord.unlink(missing_ok=True)
    # Command-path switches (build_switches.py): refused before anything is discovered or compiled.
    try:switches=build_switches.parse(os.environ)
    except build_switches.BuildSwitchError as error:raise SystemExit('build.py: '+str(error))
    out.mkdir(exist_ok=True)
    sources=sorted(p for p in (ROOT/'src').glob('*.c') if p.name!='wasm_mem.c')
    tools=discover();cc=tools['cc'];clang=tools['wasmCC'];ld=tools['wasmLD'];print(json.dumps(tools),flush=True)
    if not cc: raise SystemExit('Native C compiler missing. Run the explicit installer.')
    # Preserve exact builtin arithmetic without libc errno fallbacks (no libm).
    common=['-std=c11','-O2','-ffp-contract=off','-fno-fast-math','-fno-math-errno','-fno-strict-aliasing','-Wall','-Wextra','-Wno-misleading-indentation','-Iinclude','-Isrc']
    if os.environ.get('NOCTURNE_COVERAGE')=='1':common.extend(['-fprofile-instr-generate','-fcoverage-mapping'])
    common.extend(switches['defines'])
    native=out/('libnocturne_native.dylib' if sys.platform=='darwin' else 'libnocturne_native.so')
    nativeLink=['-dynamiclib','-Wl,-install_name,@rpath/'+native.name] if sys.platform=='darwin' else ['-shared']
    run([cc,*common,'-fPIC',*nativeLink,*sources,'-o',native])
    if os.environ.get('NOCTURNE_COVERAGE')=='1':
        common=[flag for flag in common if flag not in {'-fprofile-instr-generate','-fcoverage-mapping'}]
        # Audit shipping dependencies without LLVM's file-writing runtime;
        # language tests continue executing the measured shared library.
        audit=out/'dependency-audit';audit.mkdir(exist_ok=True)
        run([cc,*common,'-fPIC',*nativeLink,*sources,'-o',audit/native.name])
    if not args.native_only:
        if not clang or not ld: raise SystemExit('WASM requires clang AND wasm-ld. macOS: brew install llvm lld; set WASM_CC/WASM_LD explicitly.')
        objects=[]
        # Bulk memory explicitly, not by toolchain default: src/wasm_mem.c lowers memcpy,
        # memmove and memset to memory.copy/memory.fill only when the feature is enabled.
        for source in [*sources,ROOT/'src/wasm_mem.c']:
            obj=out/(source.stem+'.wasm.o');run([clang,'--target=wasm32',*common,'-nostdlib','-ffreestanding','-fno-builtin','-mbulk-memory','-Ifreestanding','-c',source,'-o',obj]);objects.append(obj)
        run([ld,'--no-entry','--export-all','--stack-first','-z','stack-size=8388608','--initial-memory=16777216','--max-memory=4294967296',*objects,'-o',out/'nocturne_native.wasm'])
    if args.sanitize:
        test=ROOT/'tests/safety.c'
        run([cc,*common,'-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer',*sources,test,'-o',out/'native-safety'])
        run([out/'native-safety'])
    build_switches.write_record(switchRecord,build_switches.record(os.environ,wasm=not args.native_only))
    print('BUILT:',native,flush=True)
if __name__=='__main__':main()
