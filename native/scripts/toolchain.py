"""Separate native compiler, LLVM WASM compiler and LLD discovery. No installation."""
import os,platform,shutil,subprocess
from pathlib import Path

def executable(value):return shutil.which(str(value)) if value else None

def discover():
    extras=[Path(p)for p in ['/opt/homebrew/opt/llvm/bin','/opt/homebrew/opt/lld/bin','/usr/local/opt/llvm/bin','/usr/local/opt/lld/bin']]
    brew=executable('brew')
    if brew:
        for package in ['llvm','lld']:
            r=subprocess.run([brew,'--prefix',package],capture_output=True,text=True,timeout=10)
            if r.returncode==0:extras.insert(0,Path(r.stdout.strip())/'bin')
    def resolve(env,names,extra=()):
        for key in env:
            if os.environ.get(key):
                result=executable(os.environ[key])
                if not result:raise RuntimeError(f'{key}: executable not found: {os.environ[key]}')
                return result
        for folder in extra:
            for name in names:
                if result:=executable(folder/name):return result
        for name in names:
            if result:=executable(name):return result
        return None
    return {'platform':platform.system(),'architecture':platform.machine(),
            'cc':resolve(['CC'],['cc','clang','gcc']),
            'wasmCC':resolve(['WASM_CC','WASM_CLANG'],['clang']+[f'clang-{i}'for i in range(22,13,-1)],extras),
            'wasmLD':resolve(['WASM_LD'],['wasm-ld']+[f'wasm-ld-{i}'for i in range(22,13,-1)],extras)}
